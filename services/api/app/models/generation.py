from typing import Literal, Self
from uuid import UUID

from pydantic import Field, field_validator, model_validator

from app.models.base import PublicModel, safe_text
from app.models.style_profile import Section, StyleProfile

MAX_RAW_NOTES_CHARS = 10_000
MAX_DRAFT_ITEM_CHARS = 10_000
MAX_DRAFT_CHARS = 20_000
MAX_REQUEST_BYTES = 65_536
type EngineVersion = Literal["structured-llm-v1", "rules-fallback-v1"]
type WarningCode = Literal[
    "FALLBACK_USED",
    "UNCERTAIN_SECTION",
    "POSSIBLE_FACT_OMISSION",
    "PROFILE_LIMIT_EXCEEDED",
    "LANGUAGE_NOT_EVALUATED",
]
type ErrorCode = Literal[
    "MALFORMED_JSON",
    "REQUEST_IN_PROGRESS",
    "PAYLOAD_TOO_LARGE",
    "UNSUPPORTED_MEDIA_TYPE",
    "VALIDATION_ERROR",
    "RATE_LIMITED",
    "SERVICE_UNAVAILABLE",
    "INTERNAL_ERROR",
]


class GenerateRequest(PublicModel):
    raw_notes: str = Field(alias="rawNotes", min_length=1, max_length=MAX_RAW_NOTES_CHARS)
    style_profile: StyleProfile = Field(alias="styleProfile")
    client_request_id: UUID = Field(alias="clientRequestId")

    @field_validator("raw_notes", mode="before")
    @classmethod
    def normalize_notes(cls, value: object) -> object:
        if isinstance(value, str):
            return safe_text(value.replace("\r\n", "\n").replace("\r", "\n")).strip()
        return value

    @field_validator("client_request_id", mode="before")
    @classmethod
    def parse_client_id(cls, value: object) -> object:
        return UUID(value) if isinstance(value, str) else value


class DraftItem(PublicModel):
    item_id: str = Field(alias="itemId", pattern=r"^D[0-9]{3,6}$")
    text: str = Field(min_length=1, max_length=MAX_DRAFT_ITEM_CHARS)
    source_fragment_ids: list[str] = Field(alias="sourceFragmentIds", min_length=1, max_length=256)

    @field_validator("text")
    @classmethod
    def validate_text(cls, value: str) -> str:
        safe_text(value)
        if value != value.strip() or value in {"Not specified.", "No blockers stated."}:
            raise ValueError("Use source-supported, trimmed item text.")
        return value


class StandupDraft(PublicModel):
    yesterday: list[DraftItem] = Field(max_length=256)
    today: list[DraftItem] = Field(max_length=256)
    blockers: list[DraftItem] = Field(max_length=256)

    @model_validator(mode="after")
    def bounded_unique_items(self) -> Self:
        items = self.yesterday + self.today + self.blockers
        if sum(len(item.text) for item in items) > MAX_DRAFT_CHARS:
            raise ValueError("Draft text exceeds its limit.")
        if len({item.item_id for item in items}) != len(items):
            raise ValueError("Item identifiers must be unique.")
        return self


class GenerationWarning(PublicModel):
    warning_id: str = Field(alias="warningId", pattern=r"^W[0-9]{3,6}$")
    code: WarningCode
    message: str = Field(min_length=1, max_length=300)
    section: Section | None
    item_id: str | None = Field(alias="itemId")
    source_fragment_ids: list[str] = Field(alias="sourceFragmentIds", max_length=256)


class GenerateResponse(PublicModel):
    draft: StandupDraft
    engine_version: EngineVersion = Field(alias="engineVersion")
    warnings: list[GenerationWarning] = Field(max_length=512)
    duration_ms: int = Field(alias="durationMs", ge=0)
    request_id: UUID = Field(alias="requestId")
    client_request_id: UUID = Field(alias="clientRequestId")


class ErrorDetail(PublicModel):
    code: ErrorCode
    message: str
    request_id: UUID = Field(alias="requestId")
    client_request_id: UUID | None = Field(alias="clientRequestId")
    field_errors: dict[str, list[str]] = Field(alias="fieldErrors")


class ErrorResponse(PublicModel):
    error: ErrorDetail
