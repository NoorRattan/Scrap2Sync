import logging
from uuid import UUID

from app.models.generation import EngineVersion, WarningCode

logger = logging.getLogger("scrap2sync")


def configure_logging(level: str) -> None:
    logger.setLevel(level)
    for name in ("httpx", "httpcore", "uvicorn.access"):
        logging.getLogger(name).disabled = True


def log_result(
    request_id: UUID, engine: EngineVersion, duration_ms: int, warnings: list[WarningCode]
) -> None:
    logger.info(
        "request=%s route=generate status=2xx engine=%s duration_bucket=%s warnings=%s",
        request_id,
        engine,
        min(duration_ms // 250, 120),
        ",".join(sorted(set(warnings))),
    )
