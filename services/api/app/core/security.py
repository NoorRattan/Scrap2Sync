import asyncio
import ipaddress
import json
import time
from uuid import UUID, uuid4

from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.config import Settings
from app.core.errors import APIError, error_response
from app.core.rate_limit import RateLimiter


def client_address(scope: Scope, headers: Headers, settings: Settings) -> str:
    peer = scope.get("client")
    address = peer[0] if peer else "unknown"
    if settings.trusted_proxy_count == 0:
        if settings.environment == "production" and scope.get("scheme") != "https":
            raise APIError(422, "VALIDATION_ERROR")
        return str(address)
    try:
        networks = [ipaddress.ip_network(network) for network in settings.trusted_proxy_cidrs]

        def trusted(value: str) -> bool:
            return any(ipaddress.ip_address(value) in network for network in networks)

        if not trusted(address):
            raise ValueError("Untrusted peer.")
        forwarded = [part.strip() for part in headers.get("x-forwarded-for", "").split(",")]
        if len(forwarded) != settings.trusted_proxy_count or not all(
            trusted(part) for part in forwarded[1:]
        ):
            raise ValueError("Invalid proxy chain.")
        result = str(ipaddress.ip_address(forwarded[0]))
        if settings.environment == "production" and headers.get("x-forwarded-proto") != "https":
            raise ValueError("HTTPS required.")
        return result
    except ValueError:
        raise APIError(422, "VALIDATION_ERROR") from None


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON property.")
        result[key] = value
    return result


def invalid_constant(value: str) -> object:
    raise ValueError("Non-JSON number.")


class SecurityMiddleware:
    def __init__(self, app: ASGIApp, settings: Settings) -> None:
        self.app = app
        self.settings = settings
        self.limiter = RateLimiter(settings.rate_limit_per_minute)
        self.in_flight = 0

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        state = scope.setdefault("state", {})
        state["request_id"] = uuid4()
        state["client_request_id"] = None
        state["deadline"] = time.monotonic() + self.settings.total_request_timeout_seconds
        headers = Headers(scope=scope)
        origin = headers.get("origin")
        admitted = False
        sent = False

        async def safe_send(message: Message) -> None:
            nonlocal sent
            if message["type"] == "http.response.start":
                target = MutableHeaders(scope=message)
                target["Cache-Control"] = "no-store"
                target["X-Request-ID"] = str(state["request_id"])
                target["X-Content-Type-Options"] = "nosniff"
                target["Referrer-Policy"] = "strict-origin-when-cross-origin"
                target["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
                if origin in self.settings.allowed_origins:
                    target["Access-Control-Allow-Origin"] = origin
                    target["Vary"] = "Origin"
                    target["Access-Control-Expose-Headers"] = "X-Request-ID, Retry-After"
                if self.settings.environment == "production":
                    target["Strict-Transport-Security"] = "max-age=31536000"
                sent = True
            await send(message)

        async def respond(error: APIError) -> None:
            if not sent:
                await error_response(error, state["request_id"], state["client_request_id"])(
                    scope, receive, safe_send
                )

        try:
            async with asyncio.timeout_at(state["deadline"]):
                if origin is not None and origin not in self.settings.allowed_origins:
                    raise APIError(422, "VALIDATION_ERROR")
                address = client_address(scope, headers, self.settings)
                if scope["method"] == "OPTIONS":
                    requested = {
                        part.strip().lower()
                        for part in headers.get("access-control-request-headers", "").split(",")
                        if part.strip()
                    }
                    if (
                        origin is None
                        or headers.get("access-control-request-method") != "POST"
                        or not requested.issubset({"content-type"})
                        or scope["path"] != "/api/v1/generate"
                    ):
                        raise APIError(422, "VALIDATION_ERROR")
                    await safe_send(
                        {
                            "type": "http.response.start",
                            "status": 204,
                            "headers": [
                                (b"access-control-allow-methods", b"POST"),
                                (b"access-control-allow-headers", b"Content-Type"),
                                (b"access-control-max-age", b"600"),
                            ],
                        }
                    )
                    await safe_send({"type": "http.response.body", "body": b""})
                    return
                if scope["path"] == "/api/v1/generate" and scope["method"] == "POST":
                    self.limiter.check(address)
                    if (
                        self.in_flight
                        >= self.settings.max_provider_concurrency + self.settings.max_queue_depth
                    ):
                        raise APIError(429, "RATE_LIMITED", retry_after=1)
                    self.in_flight += 1
                    admitted = True
                    if (
                        headers.get("content-type", "").split(";", 1)[0].strip().lower()
                        != "application/json"
                    ):
                        raise APIError(415, "UNSUPPORTED_MEDIA_TYPE")
                    if headers.get("content-encoding", "identity") != "identity":
                        raise APIError(415, "UNSUPPORTED_MEDIA_TYPE")
                    try:
                        length = int(headers.get("content-length", "0"))
                    except ValueError:
                        raise APIError(400, "MALFORMED_JSON") from None
                    if length < 0:
                        raise APIError(400, "MALFORMED_JSON")
                    if length > self.settings.max_request_bytes:
                        raise APIError(413, "PAYLOAD_TOO_LARGE")
                    raw = bytearray()
                    while True:
                        event = await receive()
                        if event["type"] == "http.disconnect":
                            return
                        chunk = event.get("body", b"")
                        if len(raw) + len(chunk) > self.settings.max_request_bytes:
                            raise APIError(413, "PAYLOAD_TOO_LARGE")
                        raw.extend(chunk)
                        if not event.get("more_body", False):
                            break
                    try:
                        body = json.loads(
                            raw.decode("utf-8"),
                            object_pairs_hook=unique_object,
                            parse_constant=invalid_constant,
                        )
                    except ValueError, UnicodeError, RecursionError:
                        raise APIError(400, "MALFORMED_JSON") from None
                    if isinstance(body, dict) and isinstance(body.get("clientRequestId"), str):
                        try:
                            state["client_request_id"] = UUID(body["clientRequestId"])
                        except ValueError:
                            pass
                    consumed = False

                    async def replay() -> Message:
                        nonlocal consumed
                        if not consumed:
                            consumed = True
                            return {"type": "http.request", "body": bytes(raw), "more_body": False}
                        return await receive()

                    await self.app(scope, replay, safe_send)
                else:
                    await self.app(scope, receive, safe_send)
        except APIError as error:
            await respond(error)
        except TimeoutError:
            await respond(APIError(503, "SERVICE_UNAVAILABLE"))
        except Exception:
            await respond(APIError(500, "INTERNAL_ERROR"))
        finally:
            if admitted:
                self.in_flight -= 1
