import re
import unicodedata

from app.formatters.fragmenter import DATA_CONTEXT
from app.models.generation import DraftItem, GenerationWarning, StandupDraft, WarningCode
from app.models.source_fragment import FormatResult, SourceFragment
from app.models.style_profile import SECTIONS, Section, StyleProfile

FORMATTER_REVISION = "rules-2026-09-12.2"
FALLBACK_MESSAGE = (
    "The AI formatter is unavailable. This draft uses conservative rules and preserves your "
    "original wording. Review the sections before copying."
)
RESOLVED = re.compile(r"\b(?:resolved|fixed|unblocked|no longer blocked|now working)\b", re.I)
NEGATED_BLOCK = re.compile(
    r"\b(?:no (?:current )?blockers?|not blocked|no longer blocked|unblocked|"
    r"(?:is|are|was|were) not (?:failing|blocked)|not failing)\b",
    re.I,
)
ACTIVE = re.compile(
    r"\b(?:still blocked|blocked|waiting (?:on|for)|cannot|can't|unable to|"
    r"(?:tests? (?:are |still )?)?failing|blocked by|need(?:s)? access|"
    r"awaiting|dependency unavailable)\b",
    re.I,
)
COMPLETED = re.compile(
    r"\b(?:fixed|finished|completed|shipped|merged|delivered|released|resolved|"
    r"implemented|added|updated|removed|wrote|reviewed|tested|deployed|closed|"
    r"worked on|investigated|debugged|documented|refactored|verified|built|"
    r"paired|landed|unblocked|measured|benchmarked|profiled)\b",
    re.I,
)
FUTURE = re.compile(
    r"\b(?:will|plan(?:ning)?|going to|intend|continue|continuing|working on|"
    r"today|next|tomorrow|in progress|starting|start|investigating|need to|"
    r"to do|todo|follow up)\b",
    re.I,
)
UNCERTAIN = re.compile(
    r"\b(?:maybe|might|perhaps|unsure|unclear|possibly|unknown|not sure)\b", re.I
)
NOT_COMPLETED = re.compile(
    r"\b(?:not|never|didn't|did not|haven't|have not)\s+(?:yet\s+)?"
    r"(?:fix|finish|complete|merge|ship|deploy)",
    re.I,
)


def classify(fragment: SourceFragment) -> tuple[Section, bool]:
    text = fragment.text
    if DATA_CONTEXT.search(text):
        return fragment.heading or "today", True
    cleaned = NEGATED_BLOCK.sub("", text)
    resolved = bool(RESOLVED.search(text))
    active = bool(ACTIVE.search(cleaned)) and not (
        resolved and not re.search(r"\b(?:still|but|waiting|cannot|can't)\b", cleaned, re.I)
    )
    completed = bool(COMPLETED.search(text)) and not NOT_COMPLETED.search(text)
    future = bool(FUTURE.search(text))
    uncertain = bool(UNCERTAIN.search(text) or NOT_COMPLETED.search(text))
    inferred: Section = "blockers" if active else "yesterday" if completed else "today"
    if fragment.heading:
        contradiction = (
            (fragment.heading == "yesterday" and (active or future and not completed))
            or (fragment.heading == "blockers" and resolved and not active)
            or (fragment.heading == "today" and completed and not future)
        )
        return fragment.heading if not contradiction else inferred, bool(contradiction or uncertain)
    return inferred, uncertain or not (active or completed or future)


def warning(
    index: int,
    code: WarningCode,
    message: str,
    *,
    section: Section | None = None,
    item_id: str | None = None,
    fragments: list[str] | None = None,
) -> GenerationWarning:
    return GenerationWarning(
        warningId=f"W{index:03}",
        code=code,
        message=message,
        section=section,
        itemId=item_id,
        sourceFragmentIds=fragments or [],
    )


def language_not_evaluated(text: str) -> bool:
    words = re.findall(r"[^\W\d_]+", text.lower())
    letters = [letter for letter in text if letter.isalpha()]
    non_latin = sum("LATIN" not in unicodedata.name(letter, "") for letter in letters)
    signals = {
        "ayer",
        "hoy",
        "mañana",
        "bloqueado",
        "demain",
        "aujourd",
        "terminé",
        "bloqué",
        "gestern",
        "heute",
        "morgen",
        "blockiert",
        "ontem",
        "hoje",
        "amanhã",
    }
    foreign_words = {
        "el",
        "la",
        "los",
        "las",
        "para",
        "pero",
        "estoy",
        "necesito",
        "revisar",
        "le",
        "les",
        "des",
        "une",
        "pour",
        "avec",
        "sans",
        "attends",
        "travaille",
        "terminé",
        "corrigé",
        "bloqué",
        "bloqueado",
        "esperando",
        "en",
        "de",
        "je",
    }
    return len(letters) >= 4 and (
        non_latin > len(letters) * 0.5
        or len(set(words) & signals) >= 2
        or (
            len(set(words) & foreign_words) >= 2
            and bool(
                set(words) & (signals | {"estoy", "necesito", "attends", "travaille", "corrigé"})
            )
        )
    )


def format_fallback(fragments: list[SourceFragment], profile: StyleProfile) -> FormatResult:
    sections: dict[Section, list[DraftItem]] = {section: [] for section in SECTIONS}
    warnings: list[GenerationWarning] = []
    for fragment in fragments:
        if not fragment.meaningful:
            continue
        section, uncertain = classify(fragment)
        previous = next(
            (
                item
                for entries in sections.values()
                for item in entries
                if item.text == fragment.text
            ),
            None,
        )
        if previous is not None:
            previous.source_fragment_ids.append(fragment.fragment_id)
            prior_section = next(key for key, entries in sections.items() if previous in entries)
            if prior_section != section:
                warnings.append(
                    warning(
                        len(warnings) + 1,
                        "UNCERTAIN_SECTION",
                        "Repeated wording appeared in different sections. Check its placement.",
                        section=prior_section,
                        item_id=previous.item_id,
                        fragments=list(previous.source_fragment_ids),
                    )
                )
            continue
        item = DraftItem(
            itemId=f"D{sum(map(len, sections.values())) + 1:03}",
            text=fragment.text,
            sourceFragmentIds=[fragment.fragment_id],
        )
        sections[section].append(item)
        if uncertain:
            warnings.append(
                warning(
                    len(warnings) + 1,
                    "UNCERTAIN_SECTION",
                    "This section is a best guess. Check it against your original note.",
                    section=section,
                    item_id=item.item_id,
                    fragments=[fragment.fragment_id],
                )
            )
    for section in SECTIONS:
        if len(sections[section]) > profile.preferred_max_items_per_section:
            warnings.append(
                warning(
                    len(warnings) + 1,
                    "PROFILE_LIMIT_EXCEEDED",
                    "This section exceeds your preferred item count to preserve the source facts.",
                    section=section,
                    fragments=[
                        fid for item in sections[section] for fid in item.source_fragment_ids
                    ],
                )
            )
    if language_not_evaluated(" ".join(fragment.text for fragment in fragments)):
        warnings.append(
            warning(
                len(warnings) + 1,
                "LANGUAGE_NOT_EVALUATED",
                "This language is not quality-evaluated. Original wording is preserved.",
            )
        )
    return FormatResult(StandupDraft(**sections), warnings)
