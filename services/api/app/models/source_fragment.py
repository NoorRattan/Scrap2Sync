from dataclasses import dataclass

from app.models.generation import GenerationWarning, StandupDraft
from app.models.style_profile import Section


@dataclass(frozen=True, slots=True)
class SourceFragment:
    fragment_id: str
    source_start: int
    source_end: int
    text: str
    heading: Section | None = None
    meaningful: bool = True


@dataclass(frozen=True, slots=True)
class FormatResult:
    draft: StandupDraft
    warnings: list[GenerationWarning]
