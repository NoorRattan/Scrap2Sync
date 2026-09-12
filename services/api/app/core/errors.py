from uuid import UUID, uuid4

from fastapi import Request
from fastapi.responses import JSONResponse

from app.models.generation import ErrorCode, ErrorDetail, ErrorResponse

MESSAGES: dict[ErrorCode, str] = {
    "MALFORMED_JSON": "Send a valid JSON request.",
    "REQUEST_IN_PROGRESS": "This request is already being processed.",
    "PAYLOAD_TOO_LARGE": "These notes exceed the request size limit.",
    "UNSUPPORTED_MEDIA_TYPE": "Send the request as JSON.",
    "VALIDATION_ERROR": "Check the highlighted fields and try again.",
    "RATE_LIMITED": "Too many requests. Wait briefly before trying again.",
    "SERVICE_UNAVAILABLE": "A safe draft could not be produced. Please try again.",
    "INTERNAL_ERROR": "Something went wrong. Please try again.",
}


class APIError(Exception):
    def __init__(
        self,
        status: int,
        code: ErrorCode,
        field_errors: dict[str, list[str]] | None = None,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(code)
        self.status = status
        self.code = code
        self.field_errors = field_errors or {}
        self.retry_after = retry_after


def error_response(
    error: APIError,
    request_id: UUID,
    client_request_id: UUID | None = None,
) -> JSONResponse:
    body = ErrorResponse(
        error=ErrorDetail(
            code=error.code,
            message=MESSAGES[error.code],
            requestId=request_id,
            clientRequestId=client_request_id,
            fieldErrors=error.field_errors,
        )
    )
    headers = {"Cache-Control": "no-store", "X-Request-ID": str(request_id)}
    if error.retry_after is not None:
        headers["Retry-After"] = str(error.retry_after)
    return JSONResponse(body.model_dump(mode="json"), status_code=error.status, headers=headers)


async def api_error_handler(request: Request, error: Exception) -> JSONResponse:
    failure = error if isinstance(error, APIError) else APIError(500, "INTERNAL_ERROR")
    return error_response(
        failure,
        getattr(request.state, "request_id", uuid4()),
        getattr(request.state, "client_request_id", None),
    )
