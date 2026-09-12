from typing import Literal, Self

from pydantic import Field, field_validator, model_validator

from app.models.base import PublicModel, safe_text

type ProfileId = Literal["concise-bullets", "standard-update", "async-detail", "custom"]
type Section = Literal["yesterday", "today", "blockers"]
SECTIONS: tuple[Section, ...] = ("yesterday", "today", "blockers")


def label_text(value: str) -> str:
    safe_text(value, multiline=False)
    if value != value.strip() or not value or any(x in value for x in ("<", ">", "{{", "}}", "${")):
        raise ValueError("Use trimmed plain text.")
    return value


class SectionHeaders(PublicModel):
    yesterday: str = Field(min_length=1, max_length=30)
    today: str = Field(min_length=1, max_length=30)
    blockers: str = Field(min_length=1, max_length=30)

    @field_validator("yesterday", "today", "blockers")
    @classmethod
    def validate_label(cls, value: str) -> str:
        return label_text(value)


class StyleProfile(PublicModel):
    id: ProfileId
    label: str = Field(min_length=1, max_length=40)
    layout: Literal["bullets", "paragraphs"]
    verbosity: Literal["brief", "standard"]
    tone: Literal["direct", "neutral-professional"]
    headers: SectionHeaders
    preferred_max_items_per_section: int = Field(alias="preferredMaxItemsPerSection", ge=1, le=10)

    @field_validator("label")
    @classmethod
    def validate_label(cls, value: str) -> str:
        return label_text(value)

    @model_validator(mode="after")
    def exact_builtin(self) -> Self:
        if self.id != "custom" and self.model_dump() != BUILTIN_PROFILES[self.id]:
            raise ValueError("Built-in profiles must match their defined values.")
        return self


BUILTIN_PROFILES: dict[str, dict[str, object]] = {
    "concise-bullets": {
        "id": "concise-bullets",
        "label": "Concise bullets",
        "layout": "bullets",
        "verbosity": "brief",
        "tone": "direct",
        "headers": {"yesterday": "Yesterday", "today": "Today", "blockers": "Blockers"},
        "preferredMaxItemsPerSection": 5,
    },
    "standard-update": {
        "id": "standard-update",
        "label": "Standard update",
        "layout": "bullets",
        "verbosity": "standard",
        "tone": "neutral-professional",
        "headers": {"yesterday": "Yesterday", "today": "Today", "blockers": "Blockers"},
        "preferredMaxItemsPerSection": 8,
    },
    "async-detail": {
        "id": "async-detail",
        "label": "Async detail",
        "layout": "paragraphs",
        "verbosity": "standard",
        "tone": "neutral-professional",
        "headers": {"yesterday": "Completed", "today": "Next", "blockers": "Blockers"},
        "preferredMaxItemsPerSection": 8,
    },
}


def builtin_profile(profile_id: str = "concise-bullets") -> StyleProfile:
    return StyleProfile.model_validate(BUILTIN_PROFILES[profile_id])
