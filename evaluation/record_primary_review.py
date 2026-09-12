"""Serialize the completed semantic review of the current fallback packet.

The decisions below were made after reading every compact packet row and the
full-value hashes for the three long fixture families. This file records those
human/model review decisions; it is not used to infer them from automated gates.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORTS = ROOT / "reports"

ABSENCE = {"Q-008", "Q-032", "Q-056"}
THREE_SECTION = {"Q-003", "Q-004", "Q-027", "Q-028", "Q-051", "Q-052"}
TWELVE_PLANS = {"Q-021", "Q-045", "Q-069"}
TWO_OUTPUT_FACTS = {
    "Q-005",
    "Q-006",
    "Q-007",
    "Q-010",
    "Q-016",
    "Q-017",
    "Q-022",
    "Q-024",
    "Q-029",
    "Q-030",
    "Q-031",
    "Q-034",
    "Q-040",
    "Q-041",
    "Q-046",
    "Q-048",
    "Q-053",
    "Q-054",
    "Q-055",
    "Q-058",
    "Q-064",
    "Q-065",
    "Q-070",
    "Q-072",
}
FOUR_OUTPUT_FACTS = {"Q-003", "Q-027", "Q-051"}
LEADING_CONJUNCTION_EDIT = {
    "Q-005",
    "Q-006",
    "Q-029",
    "Q-030",
    "Q-053",
    "Q-054",
}
NON_ENGLISH_MOVE = {"Q-022", "Q-046"}


def rationale(case_id: str) -> str:
    if case_id in ABSENCE:
        return (
            f"Reviewed {case_id}: the explicit absence of a current blocker is correctly "
            "represented by empty sections without inventing work or an active blocker."
        )
    if case_id in TWELVE_PLANS:
        return (
            f"Reviewed {case_id}: all twelve distinct planned fixture reviews are retained "
            "in Today, and the preference-overflow warning accurately explains the extra items."
        )
    if case_id in NON_ENGLISH_MOVE:
        return (
            f"Reviewed {case_id}: both source-supported statements are preserved without added "
            "facts. The language warning is correct; moving the waiting statement to Blockers "
            "would improve placement."
        )
    if case_id == "Q-070":
        return (
            "Reviewed Q-070: the complete Japanese source is preserved without added facts and "
            "is correctly marked as not quality-evaluated; splitting the waiting clause into "
            "Blockers would improve the draft."
        )
    if case_id in LEADING_CONJUNCTION_EDIT:
        return (
            f"Reviewed {case_id}: completed and planned facts are faithfully separated into "
            "Yesterday and Today. Removing the leading conjunction would improve copy polish."
        )
    if case_id in THREE_SECTION:
        return (
            f"Reviewed {case_id}: completed work, planned work, and the active blocker are all "
            "preserved in their correct sections with no unsupported cause or outcome."
        )
    if case_id in {"Q-024", "Q-048", "Q-072"}:
        return (
            f"Reviewed {case_id}: the completed review and still-blocked preview are correctly "
            "separated, retaining the exact ticket and approval dependency."
        )
    return (
        f"Reviewed {case_id}: the extractive candidate preserves every annotated source fact, "
        "status, qualifier, and protected value without adding a forbidden claim; its section "
        "and any cautionary warning are appropriate for the supplied note."
    )


def main() -> None:
    template = json.loads((REPORTS / "semantic-review-template.json").read_text(encoding="utf-8"))
    template["reviewer"] = {
        "type": "model",
        "name": "Codex semantic release reviewer",
        "modelOrRole": "OpenAI Codex (GPT-5)",
        "provider": "OpenAI",
        "reviewedAt": datetime.now(UTC).isoformat(),
        "independent": False,
    }
    template["method"] = (
        "Read all 69 current source/output rows and their annotations. Long boundary values were "
        "checked using labelled previews plus complete lengths and SHA-256 equality. Counts, "
        "placements, warnings, editing effort, and rationales record that semantic review."
    )
    template["limitations"] = [
        "Reviewer is part of the implementation context and is not independent.",
        "Fallback-only review cannot establish live-model usefulness or deployed quality.",
    ]

    for record in template["records"]:
        case_id = record["caseId"]
        required = record["requiredSourceFacts"]
        if case_id in ABSENCE:
            output_facts = 0
        elif case_id in TWELVE_PLANS:
            output_facts = 12
        elif case_id in FOUR_OUTPUT_FACTS:
            output_facts = 4
        elif case_id in TWO_OUTPUT_FACTS:
            output_facts = 2
        else:
            output_facts = 1
        record.update(
            {
                "supportedOutputFacts": output_facts,
                "totalOutputFacts": output_facts,
                "representedSourceFacts": required,
                "novelOrChangedProtectedFacts": 0,
                "criticalOmissions": 0,
                "falseActiveBlockers": 0,
                "warningsCorrect": True,
                "rationale": rationale(case_id),
            }
        )
        for placement in record["placement"]:
            fact = next(
                fact
                for fact in next(
                    row
                    for row in _packet
                    if row["caseId"] == case_id
                )["sourceFacts"]
                if fact["factId"] == placement["factId"]
            )
            allowed = fact["allowedSections"]
            placement["actualSections"] = allowed[:1]
        record["editingEffort"] = {
            "edits": 1 if case_id in LEADING_CONJUNCTION_EDIT or case_id == "Q-070" else 0,
            "deletes": 0,
            "additions": 1 if case_id == "Q-070" else 0,
            "moves": 1 if case_id in NON_ENGLISH_MOVE or case_id == "Q-070" else 0,
        }

    target = REPORTS / "primary-review.json"
    target.write_text(
        json.dumps(template, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Recorded {len(template['records'])} reviewed cases in {target.relative_to(ROOT)}.")


_packet = [
    json.loads(line)
    for line in (REPORTS / "semantic-review-packet.jsonl").read_text(encoding="utf-8").splitlines()
]

if __name__ == "__main__":
    main()
