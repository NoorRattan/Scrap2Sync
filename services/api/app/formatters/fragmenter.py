import re

from app.models.source_fragment import SourceFragment
from app.models.style_profile import Section

HEADING = re.compile(
    r"^\s*(?:#{1,4}\s*)?(Yesterday|Completed|Today|Next|Blockers)(?:\s*:|\s*$)", re.I
)
HEADINGS: dict[str, Section] = {
    "yesterday": "yesterday",
    "completed": "yesterday",
    "today": "today",
    "next": "today",
    "blockers": "blockers",
}
ABSENCE = re.compile(
    r"^(?:(?:and\s+)?(?:no (?:current )?blockers(?: stated)?|not blocked|unblocked|"
    r"no longer blocked|nothing (?:is )?blocking(?: me)?|not specified))[.!;\s]*$",
    re.I,
)
PROTECTED_SPAN = re.compile(r'```[\s\S]*?```|`[^`]*`|"[^"\n]*"|https?://[^\s<>"`]+')
DATA_CONTEXT = re.compile(
    r"\b(?:test[- ](?:string|input|payload)|literal|prompt|instruction|"
    r"ignore (?:all |previous )?instructions)\b",
    re.I,
)
CLAUSE = re.compile(
    r"\s+(?:and|but|then)\s+(?=(?:I\s+)?(?:will|plan|going|continue|still|waiting|"
    r"cannot|can't|tests?\b|fixed|finished|completed|no longer|no blockers|worked))",
    re.I,
)
DEPENDENT = re.compile(
    r"^\s*(?:(?:the )?cause (?:is )?unknown|(?:because|which|whose)\b|"
    r"(?:keep|preserve|retain)\b[^;\n]{0,120}\b(?:casing|spelling|spacing|case)\b)",
    re.I,
)
CONTRAST = re.compile(
    r"\s+but\s+(?=[^;\n]{0,160}\b(?:still blocked|waiting on|cannot|will|planned|continuing)\b)",
    re.I,
)


def prepare_request(raw_notes: str) -> list[SourceFragment]:
    """Keep exact spans, with headings and absence declarations explicitly represented."""
    fragments: list[SourceFragment] = []
    heading: Section | None = None

    def append(start: int, end: int, meaningful: bool = True) -> None:
        while start < end and raw_notes[start].isspace():
            start += 1
        while end > start and raw_notes[end - 1].isspace():
            end -= 1
        if start < end:
            text = raw_notes[start:end]
            fragments.append(
                SourceFragment(
                    f"F{len(fragments) + 1:03}",
                    start,
                    end,
                    text,
                    heading,
                    meaningful and not bool(ABSENCE.fullmatch(text)),
                )
            )

    protected = [(match.start(), match.end()) for match in PROTECTED_SPAN.finditer(raw_notes)]
    for line in re.finditer(r"[^\n]+", raw_notes):
        if DATA_CONTEXT.search(line[0]):
            protected.append((line.start(), line.end()))

    def inside(offset: int) -> bool:
        return any(start <= offset < end for start, end in protected)

    boundaries = {0, len(raw_notes)}
    for match in re.finditer(r"[;\n]", raw_notes):
        if not inside(match.start()) and not DEPENDENT.match(raw_notes[match.end() :]):
            boundaries.add(match.end())
    for match in CLAUSE.finditer(raw_notes):
        if not inside(match.start()):
            boundaries.add(match.start())
    for match in CONTRAST.finditer(raw_notes):
        if not inside(match.start()):
            boundaries.add(match.start())
    points = sorted(boundaries)
    for start, end in zip(points, points[1:], strict=False):
        span = raw_notes[start:end]
        heading_match = HEADING.match(span)
        if heading_match and not inside(start):
            heading = HEADINGS[heading_match[1].lower()]
            append(start, start + heading_match.end(), meaningful=False)
            start += heading_match.end()
        append(start, end)
    if len(fragments) > 256:
        tail = fragments[255:]
        fragments = fragments[:255] + [
            SourceFragment(
                "F256",
                tail[0].source_start,
                tail[-1].source_end,
                raw_notes[tail[0].source_start : tail[-1].source_end],
                None,
                True,
            )
        ]
    return fragments
