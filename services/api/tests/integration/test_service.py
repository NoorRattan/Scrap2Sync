import asyncio
import json
from uuid import uuid4

import httpx
import pytest
from pydantic import SecretStr

from app.core.config import Settings
from app.core.errors import APIError
from app.core.service import GenerationService
from app.formatters.fragmenter import prepare_request
from app.formatters.rules_fallback_v1 import format_fallback
from app.models.generation import GenerateRequest, StandupDraft
from app.models.style_profile import builtin_profile
from app.providers.formatter_provider import OpenAIProvider, ProviderFailure


def enabled(**kwargs):
    return Settings(
        formatter_provider="openai",
        formatter_model="fictional-exact-model",
        formatter_api_key=SecretStr("fictional-provider-key"),
        formatter_privacy_verified=True,
        **kwargs,
    )


def body(text="fixed TEST-701"):
    return GenerateRequest.model_validate(
        {
            "rawNotes": text,
            "styleProfile": builtin_profile().model_dump(),
            "clientRequestId": str(uuid4()),
        }
    )


class Stub:
    def __init__(self, mode="ok"):
        self.mode = mode
        self.calls = 0
        self.cancelled = False
        self.started = asyncio.Event()
        self.release = asyncio.Event()

    async def generate(self, fragments, profile):
        self.calls += 1
        self.started.set()
        if self.mode == "network":
            raise ProviderFailure()
        if self.mode == "slow":
            try:
                await self.release.wait()
            except asyncio.CancelledError:
                self.cancelled = True
                raise
        draft = format_fallback(fragments, profile).draft
        if self.mode == "novel":
            data = draft.model_dump()
            data["yesterday"][0]["text"] = "fixed TEST-999"
            return StandupDraft.model_validate(data)
        if self.mode == "omitted":
            return StandupDraft(yesterday=[], today=[], blockers=[])
        return draft


@pytest.mark.parametrize("mode", ["ok", "network", "novel", "omitted", "slow"])
async def test_provider_results_validated_once_and_fallback(mode):
    stub = Stub(mode)
    service = GenerationService(enabled(formatter_timeout_seconds=0.03), stub)
    result = await service.generate(body(), uuid4())
    assert result.engine_version == ("structured-llm-v1" if mode == "ok" else "rules-fallback-v1")
    assert result.draft.yesterday[0].text == "fixed TEST-701"
    assert stub.calls == 1
    assert not service.active_ids
    if mode == "slow":
        assert stub.cancelled


async def test_disabled_missing_key_unverified_privacy_never_call_provider():
    for settings in [
        Settings(),
        Settings(formatter_provider="openai", formatter_model="fictional"),
        enabled().model_copy(update={"formatter_privacy_verified": False}),
    ]:
        stub = Stub()
        response = await GenerationService(settings, stub).generate(body(), uuid4())
        assert response.engine_version == "rules-fallback-v1"
        assert any(entry.code == "FALLBACK_USED" for entry in response.warnings)
        assert stub.calls == 0


async def test_active_duplicate_queue_bounds_and_cancellation_cleanup():
    stub = Stub("slow")
    service = GenerationService(enabled(max_provider_concurrency=1, max_queue_depth=0), stub)
    request = body()
    first = asyncio.create_task(service.generate(request, uuid4()))
    await stub.started.wait()
    with pytest.raises(APIError) as duplicate:
        await service.generate(request, uuid4())
    assert duplicate.value.status == 409
    with pytest.raises(APIError) as full:
        await service.generate(body(), uuid4())
    assert full.value.status == 429
    first.cancel()
    with pytest.raises(asyncio.CancelledError):
        await first
    assert not service.active_ids and not service.slots.locked() and service.waiting == 0
    assert stub.cancelled


async def test_circuit_open_skips_calls_and_reset_allows_only_one_probe():
    stub = Stub("network")
    service = GenerationService(enabled(circuit_breaker_failures=2), stub)
    for _ in range(4):
        await service.generate(body(), uuid4())
    assert stub.calls == 2 and service.readiness == "circuit_open"
    service.circuit.opened_at -= 31
    assert service.circuit.allow()
    assert not service.circuit.allow()
    service.circuit.success()
    assert service.circuit.allow() and not service.circuit.is_open


def wire_response(text="fixed TEST-701"):
    draft = {
        "yesterday": [{"itemId": "D001", "text": text, "sourceFragmentIds": ["F001"]}],
        "today": [],
        "blockers": [],
    }
    return {
        "status": "completed",
        "output": [
            {"type": "message", "content": [{"type": "output_text", "text": json.dumps(draft)}]}
        ],
    }


async def test_openai_wire_contract_strict_schema_store_false_and_no_tools():
    calls = []

    async def handler(request):
        calls.append(request)
        payload = json.loads(request.content)
        assert payload["store"] is False and payload["tools"] == []
        assert payload["text"]["format"]["strict"] is True
        assert payload["text"]["format"]["schema"]["additionalProperties"] is False
        assert str(request.url) == "https://api.openai.com/v1/responses"
        assert "fixed TEST-701" not in payload["instructions"]
        assert request.headers["accept-encoding"] == "identity"
        return httpx.Response(200, json=wire_response())

    provider = OpenAIProvider(enabled(), httpx.MockTransport(handler))
    result = await provider.generate(prepare_request("fixed TEST-701"), builtin_profile())
    assert result.yesterday[0].text == "fixed TEST-701" and len(calls) == 1


@pytest.mark.parametrize(
    "case",
    ["network", "tls", "redirect", "oversize", "malformed", "refusal", "schema", "incomplete"],
)
async def test_openai_failure_paths_are_safe(case):
    calls = 0

    async def handler(request):
        nonlocal calls
        calls += 1
        if case in {"network", "tls"}:
            raise httpx.ConnectError("fictional-secret-leak", request=request)
        if case == "redirect":
            return httpx.Response(302, headers={"location": "https://example.test/"})
        if case == "oversize":
            return httpx.Response(200, content=b"x" * 262145)
        if case == "malformed":
            return httpx.Response(200, content=b"not json")
        if case == "refusal":
            return httpx.Response(
                200,
                json={
                    "status": "completed",
                    "output": [{"type": "message", "content": [{"type": "refusal"}]}],
                },
            )
        if case == "incomplete":
            return httpx.Response(200, json={"status": "incomplete", "output": []})
        data = wire_response()
        data["output"][0]["content"][0]["text"] = (
            '{"yesterday":[],"today":[],"blockers":[],"extra":true}'
        )
        return httpx.Response(200, json=data)

    provider = OpenAIProvider(enabled(), httpx.MockTransport(handler))
    with pytest.raises(ProviderFailure) as failure:
        await provider.generate(prepare_request("fixed TEST-701"), builtin_profile())
    assert "fictional-secret-leak" not in str(failure.value)
    assert calls == 1
