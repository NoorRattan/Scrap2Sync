from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app.core.config import Settings
from app.core.errors import APIError, api_error_handler, error_response
from app.core.logging import configure_logging
from app.core.security import SecurityMiddleware
from app.core.service import GenerationService
from app.providers.formatter_provider import FormatterProvider
from app.routers import generate, health

PUBLIC_FIELDS = {
    "rawNotes",
    "styleProfile",
    "clientRequestId",
    "id",
    "label",
    "layout",
    "verbosity",
    "tone",
    "headers",
    "yesterday",
    "today",
    "blockers",
    "preferredMaxItemsPerSection",
}


async def validation_handler(request: Request, error: Exception) -> JSONResponse:
    fields: dict[str, list[str]] = {}
    if isinstance(error, RequestValidationError):
        for detail in error.errors():
            path = [part for part in detail["loc"] if part != "body"]
            name = (
                ".".join(path) if path and all(part in PUBLIC_FIELDS for part in path) else "body"
            )
            message = "Check this field's value and try again."
            if name == "rawNotes":
                message = "Enter 1–10,000 characters without unsupported control characters."
            fields.setdefault(name, []).append(message)
    return error_response(
        APIError(422, "VALIDATION_ERROR", fields),
        request.state.request_id,
        getattr(request.state, "client_request_id", None),
    )


async def http_error_handler(request: Request, error: Exception) -> JSONResponse:
    status = error.status_code if isinstance(error, HTTPException) else 500
    return error_response(APIError(status, "VALIDATION_ERROR"), request.state.request_id)


def create_app(
    settings: Settings | None = None, provider: FormatterProvider | None = None
) -> FastAPI:
    resolved = settings or Settings.from_env()
    configure_logging(resolved.log_level)
    instance = FastAPI(
        title="Scrap2Sync API", version="0.1.0", docs_url=None, redoc_url=None, openapi_url=None
    )
    instance.state.settings = resolved
    instance.state.service = GenerationService(resolved, provider)
    instance.add_middleware(SecurityMiddleware, settings=resolved)
    instance.add_exception_handler(APIError, api_error_handler)
    instance.add_exception_handler(RequestValidationError, validation_handler)
    instance.add_exception_handler(HTTPException, http_error_handler)
    instance.include_router(generate.router)
    instance.include_router(health.router)
    return instance


app = create_app()
