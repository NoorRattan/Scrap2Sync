from typing import Literal

from fastapi import APIRouter, Request
from pydantic import Field

from app.models.base import PublicModel

router = APIRouter(prefix="/api/v1/health", tags=["health"])
type PrimaryState = Literal["configured", "unconfigured", "available", "degraded", "circuit_open"]


class Liveness(PublicModel):
    status: Literal["ok"] = "ok"


class Readiness(PublicModel):
    status: Literal["ready"] = "ready"
    primary_formatter: PrimaryState = Field(alias="primaryFormatter")


@router.get("/live", response_model=Liveness)
async def live() -> Liveness:
    return Liveness()


@router.get("/ready", response_model=Readiness)
async def ready(request: Request) -> Readiness:
    from app.core.service import GenerationService

    service: GenerationService = request.app.state.service
    return Readiness(primaryFormatter=service.readiness)
