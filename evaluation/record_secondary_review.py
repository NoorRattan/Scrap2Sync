"""Serialize decisions actually made by the secondary model reviewer after reading.

This is a record of a completed review, not an automated semantic classifier.
The initial observations remain tied to their original output packet forever.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
INITIAL_PACKET_HASH = "8ebe7818eda06807c9efc33fb55a2488313f11efa5a057991ab4456652d65cf8"

# Each tuple is: supported/total output facts, required/represented source facts,
# actual source-fact sections in annotation order, item edits, moves, rationale.
DECISIONS = {
    "Q-001": (
        1,
        1,
        [["yesterday"]],
        0,
        0,
        "Completed cache cleanup is retained as completed work with no invented speed or deployment claim.",
    ),
    "Q-002": (
        1,
        1,
        [["today"]],
        0,
        0,
        "An inspection plan remains a plan; no completed inspection or diagnosed retry cause is asserted.",
    ),
    "Q-003": (
        4,
        3,
        [["yesterday"], ["today"], ["today", "blockers"]],
        0,
        1,
        "Cleanup, review intention, blocked access and unknown cause are all supported. The cause qualifier is detached into Today; move it beside the blocker to preserve context.",
    ),
    "Q-004": (
        3,
        3,
        [["yesterday"], ["today"], ["blockers"]],
        0,
        0,
        "All three explicitly headed facts retain the correct status; no sample approval or export resolution is invented.",
    ),
    "Q-005": (
        2,
        2,
        [["yesterday"], ["today"]],
        1,
        0,
        "Completed review and future proposal are distinguished correctly. Remove the leading conjunction from the planned item for copy polish.",
    ),
    "Q-006": (
        2,
        2,
        [["yesterday"], ["today"]],
        1,
        0,
        "Review performed and continued review are both preserved. The continuing item would read better without its initial conjunction; no claim of full cancellation coverage appears.",
    ),
    "Q-007": (
        2,
        1,
        [["today", "blockers"]],
        0,
        1,
        "The active upload blocker, exact diagnostic and unknown cause are supported. The uncertainty qualifier belongs with the blocker rather than in Today.",
    ),
    "Q-008": (
        0,
        1,
        [[]],
        0,
        0,
        "Empty sections correctly represent the explicit absence of blockers. No user-visible work facts are invented; the absence assertion counts as represented source context.",
    ),
    "Q-009": (
        1,
        1,
        [["yesterday"]],
        0,
        0,
        "The previously blocked fetch is explicitly resolved and remains completed context, with no active blocker or invented cause.",
    ),
    "Q-010": (
        2,
        1,
        [["today"]],
        0,
        0,
        "Tentative cache attention and uncertain timing remain tentative. Both exact clauses stay in Today with targeted uncertainty warnings, without a commitment or diagnosis.",
    ),
    "Q-011": (
        1,
        1,
        [["yesterday"]],
        0,
        0,
        "Ticket and version remain exact, and only completed checks are asserted; deployment is not inferred.",
    ),
    "Q-012": (
        1,
        1,
        [["today"]],
        0,
        1,
        "Date, count and percentage are unchanged and no causal claim appears. The past-tense measurement is completed work, so its Today placement needs correction despite the visible uncertainty notice.",
    ),
    "Q-013": (
        1,
        1,
        [["today"]],
        0,
        0,
        "The complete maximal-length URL is preserved, with no claim it was visited or deployed. Its temporal status is unstated and conservative Today placement is visibly warned.",
    ),
    "Q-014": (
        1,
        1,
        [["today"]],
        0,
        0,
        "The complete quoted diagnostic remains exact. No cause, fix or presently active incident is inferred; the warned Today placement is acceptable for uncertain status.",
    ),
    "Q-015": (
        1,
        1,
        [["yesterday"]],
        0,
        0,
        "The maximal repeated archive-review description remains verbatim completed work, with no deletion or deployment claim. Repetition is source content, not an added fact.",
    ),
    "Q-016": (
        2,
        1,
        [["yesterday", "today"]],
        0,
        1,
        "The named review and exact casing constraint are supported, but separating the constraint into Today detaches it from the completed-review context; move it alongside that context.",
    ),
    "Q-017": (
        2,
        2,
        [["yesterday"], ["today"]],
        0,
        0,
        "The completed cleanup and intended documentation review are correctly separated; informal wording and emoji remain source-supported.",
    ),
    "Q-018": (
        1,
        1,
        [["today"]],
        0,
        0,
        "The plan and disabled-widget markup are preserved literally, without converting markup to execution or claiming the review is complete.",
    ),
    "Q-019": (
        1,
        1,
        [["today"]],
        0,
        0,
        "The JSON fixture is retained as data, including its false boolean and numeric value, and the instruction not to change it remains a source-supported plan.",
    ),
    "Q-021": (
        12,
        12,
        [["today"]] * 12,
        0,
        0,
        "All twelve distinct ticketed review plans are present in Today. The preference-overflow warning identifies all affected fragments; no fixture is silently removed.",
    ),
}


def initial_review() -> dict:
    manifest = json.loads((ROOT / "freeze-manifest.json").read_text(encoding="utf-8"))
    records = []
    for case_id, decision in DECISIONS.items():
        output_count, source_count, sections, edits, moves, rationale = decision
        records.append(
            {
                "caseId": case_id,
                "supportedOutputFacts": output_count,
                "totalOutputFacts": output_count,
                "representedSourceFacts": source_count,
                "requiredSourceFacts": source_count,
                "novelOrChangedProtectedFacts": 0,
                "criticalOmissions": 0,
                "falseActiveBlockers": 0,
                "warningsCorrect": True,
                "placement": [
                    {"factId": f"FACT-{index:02d}", "actualSections": actual}
                    for index, actual in enumerate(sections, 1)
                ],
                "editingEffort": {
                    "edits": edits,
                    "deletes": 0,
                    "additions": 0,
                    "moves": moves,
                },
                "rationale": rationale,
            }
        )
    return {
        "datasetSha256": manifest["datasetSha256"],
        "rubricSha256": manifest["rubricSha256"],
        "reviewPacketSha256": INITIAL_PACKET_HASH,
        "reviewer": {
            "type": "model",
            "name": "Codex evaluation secondary reviewer",
            "modelOrRole": "OpenAI GPT-6 / Codex sub-agent",
            "provider": "OpenAI",
            "reviewedAt": "2026-09-12T10:33:28Z",
            "independent": False,
        },
        "method": "Actual source/output/rubric reading of Q-001 through Q-019 and Q-021. Long repetitive boundary fields were read via labelled beginning/end previews and checked against complete-value lengths, hashes and exact preservation evidence. Counts and rationales were authored after reading, not produced by span-matching automation.",
        "limitations": [
            "Shared model and implementation-team context; not independent external validation.",
            "Single-output factuality review; no pairwise usefulness claim.",
            "This initial review preserves pre-repair findings and must not be applied to a changed output packet.",
        ],
        "records": records,
    }


if __name__ == "__main__":
    target = ROOT / "reports" / "secondary-review-initial.json"
    payload = json.dumps(initial_review(), ensure_ascii=False, indent=2) + "\n"
    if target.exists() and target.read_text(encoding="utf-8") != payload:
        raise ValueError("Refusing to overwrite a different completed initial review.")
    target.write_text(payload, encoding="utf-8", newline="\n")
    print(
        f"Recorded {len(DECISIONS)} actually reviewed cases with original packet hash."
    )
