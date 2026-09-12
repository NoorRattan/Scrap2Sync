import asyncio
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from starlette.datastructures import Headers

from app.core.config import Settings
from app.core.errors import APIError
from app.core.rate_limit import RateLimiter
from app.core.security import SecurityMiddleware, client_address
from app.main import create_app
from app.models.style_profile import builtin_profile


def payload(text="fixed MOCK-802"):
    return {
        "rawNotes": text,
        "styleProfile": builtin_profile().model_dump(),
        "clientRequestId": str(uuid4()),
    }


def test_http_fallback_headers_and_no_content_logs(caplog):
    marker = "confidential-fictional-MOCK-802"
    app = create_app(Settings())
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/generate", json=payload(marker), headers={"Origin": "http://localhost:3000"}
        )
    assert response.status_code == 200
    assert response.json()["engineVersion"] == "rules-fallback-v1"
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
    assert "access-control-allow-credentials" not in response.headers
    assert marker not in caplog.text and "clientRequestId" not in caplog.text


@pytest.mark.parametrize(
    "data,headers,status,code",
    [
        (b"{}", {}, 415, "UNSUPPORTED_MEDIA_TYPE"),
        (b"{", {"Content-Type": "application/json"}, 400, "MALFORMED_JSON"),
        (b'{"x":1,"x":2}', {"Content-Type": "application/json"}, 400, "MALFORMED_JSON"),
        (b'{"x":NaN}', {"Content-Type": "application/json"}, 400, "MALFORMED_JSON"),
        (
            b"{}",
            {"Content-Type": "application/json", "Content-Length": "65537"},
            413,
            "PAYLOAD_TOO_LARGE",
        ),
        (
            b"{}",
            {"Content-Type": "application/json", "Origin": "https://evil.test"},
            422,
            "VALIDATION_ERROR",
        ),
        (
            b"{}",
            {"Content-Type": "application/json", "Content-Encoding": "gzip"},
            415,
            "UNSUPPORTED_MEDIA_TYPE",
        ),
    ],
)
def test_negative_envelopes(data, headers, status, code):
    with TestClient(create_app(Settings())) as client:
        response = client.post("/api/v1/generate", content=data, headers=headers)
    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    assert response.json()["error"]["requestId"] == response.headers["x-request-id"]
    if "evil" in headers.get("Origin", ""):
        assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize(
    "mutation,field",
    [
        ({"rawNotes": " "}, "rawNotes"),
        ({"raw_notes": "snake"}, "body"),
        ({"rawNotes": "secret\x00"}, "rawNotes"),
        ({"clientRequestId": "invalid-secret"}, "clientRequestId"),
    ],
)
def test_validation_fields_are_canonical_and_content_safe(mutation, field):
    request = payload()
    request.update(mutation)
    with TestClient(create_app(Settings())) as client:
        response = client.post("/api/v1/generate", json=request)
    assert response.status_code == 422
    assert field in response.json()["error"]["fieldErrors"]
    assert "secret" not in response.text


def test_preflight_exact_allowlist_and_rate_retry_after():
    with TestClient(create_app(Settings(rate_limit_per_minute=1))) as client:
        response = client.options(
            "/api/v1/generate",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            },
        )
        assert response.status_code == 204
        bad = client.options(
            "/api/v1/generate",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "authorization",
            },
        )
        assert bad.status_code == 422
        assert client.post("/api/v1/generate", json=payload()).status_code == 200
        response = client.post("/api/v1/generate", json=payload())
        assert response.status_code == 429 and int(response.headers["retry-after"]) >= 1


async def test_streamed_request_ceiling_without_content_length():
    async def content():
        for _ in range(9):
            yield b" " * 8192

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=create_app(Settings())), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/v1/generate", content=content(), headers={"Content-Type": "application/json"}
        )
    assert response.status_code == 413


def test_proxy_topology_and_spoofing():
    scope = {"client": ("127.0.0.1", 123), "scheme": "http"}
    assert client_address(scope, Headers({"x-forwarded-for": "1.2.3.4"}), Settings()) == "127.0.0.1"
    settings = Settings(trusted_proxy_count=1, trusted_proxy_cidrs=("127.0.0.0/8",))
    assert client_address(scope, Headers({"x-forwarded-for": "192.0.2.7"}), settings) == "192.0.2.7"
    with pytest.raises(APIError):
        client_address(scope, Headers({"x-forwarded-for": "192.0.2.7, 10.0.0.5"}), settings)
    with pytest.raises(APIError):
        client_address(
            {"client": ("192.0.2.9", 1)}, Headers({"x-forwarded-for": "192.0.2.7"}), settings
        )


def test_rate_memory_bounded_ephemeral_and_expiry():
    limiter = RateLimiter(1, max_keys=1)
    limiter.check("192.0.2.7", now=0)
    with pytest.raises(APIError):
        limiter.check("192.0.2.8", now=1)
    assert b"192.0.2.7" not in limiter.buckets
    limiter.check("192.0.2.8", now=61)
    assert len(limiter.buckets) == 1


async def test_total_deadline_and_global_admission_bound():
    settings = Settings(
        formatter_timeout_seconds=0.1,
        total_request_timeout_seconds=1,
        max_provider_concurrency=1,
        max_queue_depth=0,
    )
    events = []

    async def inner(scope, receive, send):
        raise AssertionError("Slow body must not reach app.")

    middleware = SecurityMiddleware(inner, settings)

    async def receive():
        await asyncio.sleep(5)
        return {"type": "http.request", "body": b"{}"}

    async def send(event):
        events.append(event)

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/generate",
        "headers": [(b"content-type", b"application/json")],
        "client": ("127.0.0.1", 1),
    }
    task = asyncio.create_task(middleware(scope, receive, send))
    await asyncio.sleep(0)
    second_events = []

    async def second_send(event):
        second_events.append(event)

    await middleware({**scope, "state": {}}, receive, second_send)
    assert second_events[0]["status"] == 429
    await task
    assert events[0]["status"] == 503 and middleware.in_flight == 0
