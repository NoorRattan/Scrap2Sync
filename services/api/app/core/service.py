import asyncio
import time
from uuid import UUID

from pydantic import ValidationError

from app.core.circuit_breaker import CircuitBreaker
from app.core.config import Settings
from app.core.errors import APIError
from app.core.logging import log_result
from app.formatters.fragmenter import prepare_request
from app.formatters.rules_fallback_v1 import FALLBACK_MESSAGE, format_fallback, warning
from app.formatters.validator import UnsafeDraft, validate_result
from app.models.generation import EngineVersion, GenerateRequest, GenerateResponse
from app.models.source_fragment import FormatResult
from app.providers.formatter_provider import FormatterProvider, OpenAIProvider, ProviderFailure
from app.routers.health import PrimaryState


class GenerationService:
    def __init__(self, settings: Settings, provider: FormatterProvider | None = None) -> None:
        self.settings = settings
        self.provider = provider or OpenAIProvider(settings)
        self.circuit = CircuitBreaker(
            settings.circuit_breaker_failures, settings.circuit_breaker_reset_seconds
        )
        self.slots = asyncio.Semaphore(settings.max_provider_concurrency)
        self.waiting = 0
        self.active_ids: set[UUID] = set()
        self.primary_state: PrimaryState = (
            "configured" if settings.provider_enabled else "unconfigured"
        )

    @property
    def readiness(self) -> PrimaryState:
        return "circuit_open" if self.circuit.is_open else self.primary_state

    async def generate(
        self,
        body: GenerateRequest,
        request_id: UUID,
        deadline: float | None = None,
    ) -> GenerateResponse:
        started = time.monotonic()
        deadline = deadline or started + self.settings.total_request_timeout_seconds
        if body.client_request_id in self.active_ids:
            raise APIError(409, "REQUEST_IN_PROGRESS")
        self.active_ids.add(body.client_request_id)
        try:
            fragments = prepare_request(body.raw_notes)
            result: FormatResult | None = None
            engine: EngineVersion = "rules-fallback-v1"
            if self.settings.provider_enabled and self.circuit.allow():
                acquired = False
                try:
                    if self.slots.locked() and self.waiting >= self.settings.max_queue_depth:
                        raise APIError(429, "RATE_LIMITED", retry_after=1)
                    self.waiting += 1
                    try:
                        async with asyncio.timeout(max(0, deadline - time.monotonic() - 0.5)):
                            await self.slots.acquire()
                            acquired = True
                    finally:
                        self.waiting -= 1
                    timeout = min(
                        self.settings.formatter_timeout_seconds,
                        max(0, deadline - time.monotonic() - 0.5),
                    )
                    async with asyncio.timeout(timeout):
                        draft = await self.provider.generate(fragments, body.style_profile)
                    self.circuit.success()
                    result = validate_result(FormatResult(draft, []), fragments, body.style_profile)
                    self.primary_state = "available"
                    engine = "structured-llm-v1"
                except (TimeoutError, ProviderFailure) as failure:
                    self.primary_state = "degraded"
                    if isinstance(failure, TimeoutError) or failure.infrastructure:
                        self.circuit.failure()
                    else:
                        self.circuit.cancel_probe()
                except UnsafeDraft, ValidationError:
                    self.primary_state = "degraded"
                except asyncio.CancelledError:
                    self.circuit.cancel_probe()
                    raise
                except APIError:
                    self.circuit.cancel_probe()
                    raise
                finally:
                    if acquired:
                        self.slots.release()
            if result is None:
                try:
                    result = validate_result(
                        format_fallback(fragments, body.style_profile),
                        fragments,
                        body.style_profile,
                    )
                    if any(entry.code == "POSSIBLE_FACT_OMISSION" for entry in result.warnings):
                        raise UnsafeDraft("Fallback must preserve all content.")
                    result.warnings.append(
                        warning(len(result.warnings) + 1, "FALLBACK_USED", FALLBACK_MESSAGE)
                    )
                except UnsafeDraft, ValidationError:
                    raise APIError(503, "SERVICE_UNAVAILABLE") from None
            duration = max(0, int((time.monotonic() - started) * 1000))
            response = GenerateResponse(
                draft=result.draft,
                engineVersion=engine,
                warnings=result.warnings,
                durationMs=duration,
                requestId=request_id,
                clientRequestId=body.client_request_id,
            )
            log_result(request_id, engine, duration, [entry.code for entry in result.warnings])
            return response
        finally:
            self.active_ids.discard(body.client_request_id)
