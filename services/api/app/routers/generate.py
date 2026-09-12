import asyncio

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.errors import APIError
from app.models.generation import ErrorResponse, GenerateRequest, GenerateResponse

router = APIRouter(prefix="/api/v1", tags=["drafts"])


@router.post(
    "/generate",
    response_model=GenerateResponse,
    responses={code: {"model": ErrorResponse} for code in (400, 409, 413, 415, 422, 429, 500, 503)},
)
async def generate(body: GenerateRequest, request: Request) -> JSONResponse:
    from app.core.service import GenerationService

    service: GenerationService = request.app.state.service
    task = asyncio.create_task(
        service.generate(body, request.state.request_id, request.state.deadline)
    )

    async def disconnected() -> None:
        while True:
            event = await request.receive()
            if event["type"] == "http.disconnect":
                return

    watcher = asyncio.create_task(disconnected())
    try:
        done, _ = await asyncio.wait({task, watcher}, return_when=asyncio.FIRST_COMPLETED)
        if watcher in done and task not in done:
            task.cancel()
            raise asyncio.CancelledError
        result = await task
        if len(result.model_dump_json().encode("utf-8")) > service.settings.max_response_bytes:
            raise APIError(503, "SERVICE_UNAVAILABLE")
        return JSONResponse(result.model_dump(mode="json"))
    finally:
        for pending in (task, watcher):
            pending.cancel()
        await asyncio.gather(task, watcher, return_exceptions=True)
