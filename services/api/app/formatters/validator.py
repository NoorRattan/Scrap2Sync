import re

from app.formatters.rules_fallback_v1 import warning
from app.models.generation import StandupDraft
from app.models.source_fragment import FormatResult, SourceFragment
from app.models.style_profile import SECTIONS, StyleProfile

PROTECTED_FACTS = re.compile(
    r'https?://[^\s<>"`]+|`[^`]+`|"[^"\n]+"|\b[A-Z][A-Z0-9]+-\d+\b|'
    r"\bv?\d+(?:\.\d+){1,3}(?:[-+][\w.]+)?\b|\b\d+(?:[.,:/-]\d+)*(?:%|ms|s|MB|GB)?|"
    r"\b[A-Z][a-z]+(?:[ -][A-Z][a-z]+)+\b|\b[A-Z]{2,}\b"
)
POLARITY = re.compile(
    r"\b(?:not|never|no|cannot|can't|didn't|maybe|might|perhaps|possibly|unknown)\b", re.I
)
GRAMMAR_WORDS = {
    "a",
    "an",
    "the",
    "i",
    "we",
    "and",
    "but",
    "then",
    "to",
    "of",
    "on",
    "in",
    "for",
    "with",
    "is",
    "are",
    "was",
    "were",
    "have",
    "has",
    "had",
    "it",
}
COMMON_CAPITALS = {word.capitalize() for word in GRAMMAR_WORDS} | {
    "Fixed",
    "Finished",
    "Completed",
    "Today",
    "Yesterday",
    "Blockers",
    "Next",
    "No",
    "Not",
    "Plan",
    "Planning",
    "Continue",
    "Continuing",
    "Waiting",
    "Still",
    "Worked",
    "Reviewed",
}


def content_words(text: str) -> set[str]:
    return set(re.findall(r"\w+", text.casefold())) - GRAMMAR_WORDS


class UnsafeDraft(ValueError):
    """The response cannot safely be returned; the message never carries source data."""


def protected_tokens(text: str) -> set[str]:
    names = set(re.findall(r"\b[A-Z][a-z]+\b", text)) - COMMON_CAPITALS
    return {match[0] for match in PROTECTED_FACTS.finditer(text)} | names


def validate_result(
    result: FormatResult,
    fragments: list[SourceFragment],
    profile: StyleProfile,
) -> FormatResult:
    draft = StandupDraft.model_validate(result.draft.model_dump())
    source = {fragment.fragment_id: fragment for fragment in fragments}
    items = {item.item_id: item for section in SECTIONS for item in getattr(draft, section)}
    covered: set[str] = set()
    rendered: dict[str, str] = {}
    mapped_text: dict[str, list[str]] = {}
    for section in SECTIONS:
        for item in getattr(draft, section):
            if len(set(item.source_fragment_ids)) != len(item.source_fragment_ids):
                raise UnsafeDraft("Repeated source reference.")
            if any(
                fid not in source or not source[fid].meaningful for fid in item.source_fragment_ids
            ):
                raise UnsafeDraft("Unknown or non-content source reference.")
            normalized = " ".join(item.text.casefold().split())
            if normalized in rendered and rendered[normalized] != section:
                raise UnsafeDraft("Repeated rendered fact.")
            rendered[normalized] = section
            supporting = " ".join(source[fid].text for fid in item.source_fragment_ids)
            if content_words(item.text) - content_words(supporting):
                raise UnsafeDraft("Novel source content.")
            if protected_tokens(item.text) - protected_tokens(supporting):
                raise UnsafeDraft("Novel protected fact.")
            if set(POLARITY.findall(supporting.lower())) - set(POLARITY.findall(item.text.lower())):
                raise UnsafeDraft("Source uncertainty or negation changed.")
            covered.update(item.source_fragment_ids)
            for fid in item.source_fragment_ids:
                mapped_text.setdefault(fid, []).append(item.text)
    for fragment in fragments:
        if not fragment.meaningful:
            continue
        joined = " ".join(mapped_text.get(fragment.fragment_id, []))
        if protected_tokens(fragment.text) - protected_tokens(joined):
            raise UnsafeDraft("Protected source fact omitted.")
        if fragment.fragment_id in covered and content_words(fragment.text) - content_words(joined):
            raise UnsafeDraft("Mapped source content omitted.")
    warnings = list(result.warnings)
    if len({entry.warning_id for entry in warnings}) != len(warnings):
        raise UnsafeDraft("Repeated warning identifier.")
    for entry in warnings:
        if any(fid not in source for fid in entry.source_fragment_ids):
            raise UnsafeDraft("Unknown warning source reference.")
        if entry.item_id is not None:
            if entry.item_id not in items:
                raise UnsafeDraft("Unknown warning item.")
            if entry.section and items[entry.item_id] not in getattr(draft, entry.section):
                raise UnsafeDraft("Warning section does not match its item.")
        if entry.code == "POSSIBLE_FACT_OMISSION" and (
            not entry.source_fragment_ids
            or any(fid in covered for fid in entry.source_fragment_ids)
        ):
            raise UnsafeDraft("Incorrect omission warning.")
    already_warned = {
        fid
        for entry in warnings
        if entry.code == "POSSIBLE_FACT_OMISSION"
        for fid in entry.source_fragment_ids
    }
    missing = [
        fragment.fragment_id
        for fragment in fragments
        if fragment.meaningful and fragment.fragment_id not in covered | already_warned
    ]
    if missing:
        warnings.append(
            warning(
                len(warnings) + 1,
                "POSSIBLE_FACT_OMISSION",
                "Some source content may be missing. Review the original notes.",
                fragments=missing,
            )
        )
    for section in SECTIONS:
        if len(getattr(draft, section)) > profile.preferred_max_items_per_section and not any(
            entry.code == "PROFILE_LIMIT_EXCEEDED" and entry.section == section
            for entry in warnings
        ):
            warnings.append(
                warning(
                    len(warnings) + 1,
                    "PROFILE_LIMIT_EXCEEDED",
                    "This section exceeds your preferred item count to preserve facts.",
                    section=section,
                )
            )
    return FormatResult(draft, warnings)
