"""Execute the frozen benchmark and preserve automated and reviewer evidence separately.

No network provider calls are made by this tool. The local backend adapter must
explicitly disable provider processing. Run with the API project's environment.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import platform
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
REPOSITORY = ROOT.parent
SECTIONS = ("yesterday", "today", "blockers")
RESPONSE_KEYS = {
    "draft",
    "engineVersion",
    "warnings",
    "durationMs",
    "requestId",
    "clientRequestId",
}
ITEM_KEYS = {"itemId", "text", "sourceFragmentIds"}
WARNING_KEYS = {
    "warningId",
    "code",
    "message",
    "section",
    "itemId",
    "sourceFragmentIds",
}
WARNING_CODES = {
    "FALLBACK_USED",
    "UNCERTAIN_SECTION",
    "POSSIBLE_FACT_OMISSION",
    "PROFILE_LIMIT_EXCEEDED",
    "LANGUAGE_NOT_EVALUATED",
}
SEMANTIC_FIELDS = (
    "supportedOutputFacts",
    "totalOutputFacts",
    "representedSourceFacts",
    "requiredSourceFacts",
    "novelOrChangedProtectedFacts",
    "criticalOmissions",
    "falseActiveBlockers",
)


def now() -> str:
    return datetime.now(UTC).isoformat()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
            for row in rows
        ),
        encoding="utf-8",
        newline="\n",
    )


def archive_previous_run(reports: Path) -> None:
    """Keep failed and superseded execution evidence visible after a repair run."""
    metadata_path = reports / "execution-metadata.json"
    if not metadata_path.exists():
        return
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    old_hash = metadata.get("caseResultsSha256")
    if not isinstance(old_hash, str) or not re.fullmatch(r"[a-f0-9]{64}", old_hash):
        raise ValueError("Cannot archive an execution without its case-result hash.")
    destination = reports / "runs" / old_hash[:20]
    if not destination.resolve().is_relative_to(ROOT):
        raise ValueError("Evaluation archive must remain within evaluation/.")
    destination.mkdir(parents=True, exist_ok=True)
    for name in (
        "case-results.jsonl",
        "execution-metadata.json",
        "semantic-review-packet.jsonl",
        "semantic-review-template.json",
        "release-report.json",
    ):
        source, target = reports / name, destination / name
        if source.exists() and not target.exists():
            shutil.copyfile(source, target)


def load_frozen() -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    from freeze_benchmark import validate

    manifest = json.loads((ROOT / "freeze-manifest.json").read_text(encoding="utf-8"))
    dataset_path = ROOT / "dataset" / "benchmark.jsonl"
    rubric_path = ROOT / "rubric.json"
    if sha256(dataset_path) != manifest["datasetSha256"]:
        raise ValueError("Frozen dataset hash mismatch; evaluation refused.")
    if sha256(rubric_path) != manifest["rubricSha256"]:
        raise ValueError("Frozen rubric hash mismatch; evaluation refused.")
    if (ROOT / "benchmark.sha256").read_text().split()[0] != manifest["datasetSha256"]:
        raise ValueError("Dataset hash record does not match manifest.")
    if (ROOT / "rubric.sha256").read_text().split()[0] != manifest["rubricSha256"]:
        raise ValueError("Rubric hash record does not match manifest.")
    cases = [
        json.loads(line)
        for line in dataset_path.read_text(encoding="utf-8").splitlines()
    ]
    validate(cases)
    return cases, json.loads(rubric_path.read_text(encoding="utf-8")), manifest


def normalized_span(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().rstrip(".!?;").casefold()


def public_schema_errors(payload: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict) or set(payload) != RESPONSE_KEYS:
        return ["response-field-set"]
    if not isinstance(payload["engineVersion"], str) or payload[
        "engineVersion"
    ] not in {"rules-fallback-v1", "structured-llm-v1"}:
        errors.append("engine-enum")
    if type(payload["durationMs"]) is not int or payload["durationMs"] < 0:
        errors.append("duration-type-or-range")
    from uuid import UUID

    for name in ("requestId", "clientRequestId"):
        try:
            UUID(payload[name])
        except (ValueError, TypeError, AttributeError):
            errors.append(name + "-uuid")
    draft = payload["draft"]
    if not isinstance(draft, dict) or set(draft) != set(SECTIONS):
        return errors + ["draft-section-field-set"]
    item_ids: list[str] = []
    total = 0
    for section in SECTIONS:
        items = draft[section]
        if not isinstance(items, list):
            errors.append(section + "-not-array")
            continue
        for item in items:
            if not isinstance(item, dict) or set(item) != ITEM_KEYS:
                errors.append("item-field-set")
                continue
            if not isinstance(item["itemId"], str) or not item["itemId"]:
                errors.append("item-id-type")
            else:
                item_ids.append(item["itemId"])
            text = item["text"]
            if not isinstance(text, str):
                errors.append("item-text-type")
            else:
                total += len(text)
                if not 1 <= len(text) <= 10000 or text != text.strip():
                    errors.append("item-text-size-or-trim")
                if text in {"Not specified.", "No blockers stated."}:
                    errors.append("placeholder-item")
            ids = item["sourceFragmentIds"]
            if (
                not isinstance(ids, list)
                or not ids
                or not all(isinstance(i, str) for i in ids)
            ):
                errors.append("item-source-reference-type")
    if total > 20000:
        errors.append("total-text-limit")
    if len(item_ids) != len(set(item_ids)):
        errors.append("duplicate-item-id")
    warnings = payload["warnings"]
    if not isinstance(warnings, list):
        return errors + ["warnings-not-array"]
    warning_ids: list[str] = []
    for warning in warnings:
        if not isinstance(warning, dict) or set(warning) != WARNING_KEYS:
            errors.append("warning-field-set")
            continue
        if not isinstance(warning["warningId"], str) or not warning["warningId"]:
            errors.append("warning-id-type")
        else:
            warning_ids.append(warning["warningId"])
        if not isinstance(warning["code"], str) or warning["code"] not in WARNING_CODES:
            errors.append("warning-code")
        if warning["section"] is not None and warning["section"] not in SECTIONS:
            errors.append("warning-section")
        if warning["itemId"] is not None and warning["itemId"] not in item_ids:
            errors.append("warning-item-reference")
        if not isinstance(warning["message"], str):
            errors.append("warning-message-type")
        if not isinstance(warning["sourceFragmentIds"], list) or not all(
            isinstance(i, str) for i in warning["sourceFragmentIds"]
        ):
            errors.append("warning-source-reference-type")
    if len(warning_ids) != len(set(warning_ids)):
        errors.append("duplicate-warning-id")
    return errors


def score_automated(case: dict[str, Any], execution: dict[str, Any]) -> dict[str, Any]:
    invalid = "empty-invalid" in case["coverageTags"]
    status = execution["statusCode"]
    body = execution["response"]
    checks: dict[str, Any] = {}
    if invalid:
        error = body.get("error", {}) if isinstance(body, dict) else {}
        checks["invalidInputRejected"] = (
            status == 422
            and error.get("code") == "VALIDATION_ERROR"
            and "rawNotes" in error.get("fieldErrors", {})
        )
        checks["formatterNotInvoked"] = execution.get("formatterInvoked") is False
        return {
            "checks": checks,
            "failures": [name for name, passed in checks.items() if not passed],
            "expectedInvalid": True,
            "schemaErrors": [],
            "protected": {"required": 0, "preserved": 0},
            "placementProxy": [],
            "semanticScores": "requires-review",
        }

    errors = public_schema_errors(body) if status == 200 else [f"http-status-{status}"]
    checks["successfulResponse"] = status == 200
    checks["strictResponseSchema"] = (
        not errors and execution.get("backendSchemaValid") is True
    )
    checks["fallbackEngine"] = (
        isinstance(body, dict) and body.get("engineVersion") == "rules-fallback-v1"
    )
    draft = body.get("draft", {}) if isinstance(body, dict) else {}
    if not isinstance(draft, dict):
        draft = {}
    items = [
        (section, item)
        for section in SECTIONS
        for item in (draft.get(section) or [])
        if isinstance(item, dict) and isinstance(item.get("text"), str)
    ]
    output = "\n".join(item["text"] for _, item in items)
    tokens = Counter(
        token
        for source_fact in case["sourceFacts"]
        for token in source_fact["protectedTokens"]
    )
    protected_total = sum(tokens.values())
    protected_kept = sum(
        min(output.count(token), count) for token, count in tokens.items()
    )
    checks["exactAnnotatedProtectedTokens"] = protected_kept == protected_total
    checks["commonProtectedFactValidation"] = (
        execution.get("commonValidationPassed") is True
    )
    fragments = execution.get("sourceFragments", [])
    normalized_source = (
        case.get("rawNotes", "").replace("\r\n", "\n").replace("\r", "\n").strip()
    )
    if normalized_source:
        covered_positions: set[int] = set()
        spans_exact = True
        for fragment in fragments:
            start, end = fragment.get("sourceStart"), fragment.get("sourceEnd")
            if (
                type(start) is not int
                or type(end) is not int
                or not 0 <= start < end <= len(normalized_source)
            ):
                spans_exact = False
                continue
            spans_exact = spans_exact and normalized_source[start:end] == fragment.get(
                "text"
            )
            covered_positions.update(range(start, end))
        checks["sourcePreparationExactSpans"] = spans_exact
        checks["sourcePreparationNoDroppedText"] = all(
            offset in covered_positions or character.isspace()
            for offset, character in enumerate(normalized_source)
        )
    fragment_ids = {fragment["fragmentId"] for fragment in fragments}
    exempt = {
        fragment["fragmentId"]
        for fragment in fragments
        if fragment.get("exemptFromOutput", False)
    }
    mapped = {
        fragment_id
        for _, item in items
        for fragment_id in item.get("sourceFragmentIds", [])
    }
    warnings = body.get("warnings", []) if isinstance(body, dict) else []
    warnings = (
        [warning for warning in warnings if isinstance(warning, dict)]
        if isinstance(warnings, list)
        else []
    )
    warned = {
        fragment_id
        for warning in warnings
        if warning.get("code") == "POSSIBLE_FACT_OMISSION"
        for fragment_id in warning.get("sourceFragmentIds", [])
    }
    checks["validSourceReferences"] = bool(fragments) and mapped <= fragment_ids
    if not fragments and execution.get("absenceOnly") is True:
        checks["validSourceReferences"] = not items
    checks["meaningfulFragmentCoverage"] = (fragment_ids - exempt) <= (mapped | warned)
    checks["fallbackNoOmittedFragments"] = (fragment_ids - exempt) <= mapped
    checks["validWarningFragmentReferences"] = all(
        set(warning.get("sourceFragmentIds", [])) <= fragment_ids
        for warning in warnings
    )
    checks["fallbackWarning"] = any(
        warning.get("code") == "FALLBACK_USED" for warning in warnings
    )
    if "non-english" in case["coverageTags"]:
        checks["languageWarning"] = any(
            warning.get("code") == "LANGUAGE_NOT_EVALUATED" for warning in warnings
        )
    if (
        "negated-blocker" in case["coverageTags"]
        or "resolved-blocker" in case["coverageTags"]
    ):
        checks["noFalseActiveBlocker"] = not draft.get("blockers", [])
    if "negated-blocker" in case["coverageTags"]:
        checks["absenceOnlyEmptyDraft"] = not items
    placement = []
    exact_spans = []
    for source_fact in case["sourceFacts"]:
        expected = source_fact["allowedSections"]
        found = [
            section
            for section, item in items
            if normalized_span(source_fact["sourceText"])
            in normalized_span(item["text"])
        ]
        placement.append(
            {
                "factId": source_fact["factId"],
                "expected": expected,
                "matchedSections": found,
                "unambiguous": len(expected) == 1 and not source_fact["uncertain"],
                "method": "normalized-span-match; requires separate semantic review",
            }
        )
        exact_spans.append(
            {
                "factId": source_fact["factId"],
                "matched": bool(found) if expected else not items,
            }
        )
    return {
        "checks": checks,
        "failures": [name for name, passed in checks.items() if not passed],
        "expectedInvalid": False,
        "schemaErrors": errors,
        "protected": {
            "required": protected_total,
            "preserved": protected_kept,
            "missing": [
                token for token, count in tokens.items() if output.count(token) < count
            ],
        },
        "fragments": {
            "total": len(fragment_ids),
            "exempt": len(exempt),
            "mapped": len(mapped),
            "warned": len(warned),
            "uncovered": sorted(fragment_ids - exempt - mapped - warned),
        },
        "exactSourceSpanProxy": exact_spans,
        "placementProxy": placement,
        "semanticScores": "requires-review",
    }


def review_packet(case: dict[str, Any], execution: dict[str, Any]) -> dict[str, Any]:
    body = execution["response"]
    draft = body.get("draft", {}) if isinstance(body, dict) else {}
    if not isinstance(draft, dict):
        draft = {}
    return {
        "caseId": case["caseId"],
        "sourceNotes": case["rawNotes"],
        "sourceFacts": case["sourceFacts"],
        "forbiddenClaims": case["forbiddenClaims"],
        "acceptableVariations": case["acceptableVariations"],
        "coverageTags": case["coverageTags"],
        "outputA": {
            section: [item["text"] for item in draft.get(section, [])]
            for section in SECTIONS
        },
        "warningsForReview": [
            warning
            for warning in body.get("warnings", [])
            if warning.get("code") != "FALLBACK_USED"
        ]
        if isinstance(body, dict)
        else [],
        "blindingLimitation": "Single-output factuality review; no pairwise usefulness score. Engine-identifying request-wide notices removed.",
    }


def review_template(
    cases: list[dict[str, Any]], manifest: dict[str, Any], packet_hash: str
) -> dict[str, Any]:
    return {
        "datasetSha256": manifest["datasetSha256"],
        "rubricSha256": manifest["rubricSha256"],
        "reviewPacketSha256": packet_hash,
        "reviewer": {
            "type": "model",
            "name": None,
            "modelOrRole": None,
            "provider": None,
            "reviewedAt": None,
            "independent": False,
        },
        "method": "Read source notes, annotated facts, rubric, and anonymized output. Complete scores only after actual review.",
        "records": [
            {
                "caseId": case["caseId"],
                "supportedOutputFacts": None,
                "totalOutputFacts": None,
                "representedSourceFacts": None,
                "requiredSourceFacts": len(case["sourceFacts"]),
                "novelOrChangedProtectedFacts": None,
                "criticalOmissions": None,
                "falseActiveBlockers": None,
                "warningsCorrect": None,
                "placement": [
                    {"factId": fact["factId"], "actualSections": None}
                    for fact in case["sourceFacts"]
                ],
                "editingEffort": {
                    "edits": None,
                    "deletes": None,
                    "additions": None,
                    "moves": None,
                },
                "rationale": None,
            }
            for case in cases
            if "empty-invalid" not in case["coverageTags"]
        ],
    }


def compact_review_packet(packet: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Preview long repetitive fixtures without concealing where text was omitted."""

    def preview(text: str) -> dict[str, Any]:
        shortened = len(text) > 900
        return {
            "text": text
            if not shortened
            else text[:350]
            + "\n[PREVIEW: middle omitted; inspect full packet]\n"
            + text[-180:],
            "characters": len(text),
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "complete": not shortened,
        }

    return [
        {
            "caseId": row["caseId"],
            "source": preview(row["sourceNotes"]),
            "sourceFacts": [
                {
                    "factId": fact["factId"],
                    "sourceText": preview(fact["sourceText"]),
                    "allowedSections": fact["allowedSections"],
                    "uncertain": fact["uncertain"],
                }
                for fact in row["sourceFacts"]
            ],
            "candidateA": {
                section: [
                    {
                        **preview(text),
                        "exactSourceSubstring": text in row["sourceNotes"],
                    }
                    for text in row["outputA"][section]
                ]
                for section in SECTIONS
            },
            "warnings": [
                {
                    "code": warning["code"],
                    "section": warning["section"],
                    "itemId": warning["itemId"],
                    "sourceFragmentIds": warning["sourceFragmentIds"],
                }
                for warning in row["warningsForReview"]
            ],
            "forbiddenClaims": row["forbiddenClaims"],
            "acceptableVariations": row["acceptableVariations"],
            "reviewLimitation": "Exact-substring indicators are automated aids, not semantic scores. Full unabridged source/output remains in semantic-review-packet.jsonl.",
        }
        for row in packet
    ]


def ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def gate(
    value: Any,
    passed: bool | None,
    failures: list[str] | None = None,
    limitation: str | None = None,
) -> dict[str, Any]:
    return {
        "value": value,
        "verdict": "not_run" if passed is None else "pass" if passed else "fail",
        "failureCaseIds": failures or [],
        "limitation": limitation,
    }


def load_reviews(
    paths: list[Path], manifest: dict[str, Any], packet_hash: str
) -> list[dict[str, Any]]:
    reviews = []
    for path in paths:
        review = json.loads(path.read_text(encoding="utf-8"))
        if (
            review["datasetSha256"] != manifest["datasetSha256"]
            or review["rubricSha256"] != manifest["rubricSha256"]
        ):
            raise ValueError(f"Review freeze mismatch: {path.name}")
        if review.get("reviewPacketSha256") != packet_hash:
            raise ValueError(f"Review output has changed since scoring: {path.name}")
        reviewer = review["reviewer"]
        if not all(
            reviewer.get(name) for name in ("name", "modelOrRole", "reviewedAt")
        ):
            raise ValueError(f"Missing reviewer provenance: {path.name}")
        ids = [row["caseId"] for row in review["records"]]
        if len(ids) != len(set(ids)):
            raise ValueError(f"Duplicate review case ID: {path.name}")
        for row in review["records"]:
            for name in SEMANTIC_FIELDS:
                if type(row.get(name)) is not int or row[name] < 0:
                    raise ValueError(
                        f"Unscored semantic field {name} in {row['caseId']}"
                    )
            if not row.get("rationale") or not isinstance(
                row.get("warningsCorrect"), bool
            ):
                raise ValueError(
                    f"Incomplete rationale/warning review: {row['caseId']}"
                )
            if (
                row["supportedOutputFacts"] > row["totalOutputFacts"]
                or row["representedSourceFacts"] > row["requiredSourceFacts"]
            ):
                raise ValueError(f"Invalid semantic fraction: {row['caseId']}")
            if any(
                not isinstance(item["actualSections"], list)
                or not set(item["actualSections"]) <= set(SECTIONS)
                for item in row["placement"]
            ):
                raise ValueError(f"Unscored placement: {row['caseId']}")
            effort = row.get("editingEffort", {})
            if set(effort) != {"edits", "deletes", "additions", "moves"} or any(
                type(count) is not int or count < 0 for count in effort.values()
            ):
                raise ValueError(f"Unscored editing effort: {row['caseId']}")
        review["evidencePath"] = path.resolve().relative_to(REPOSITORY).as_posix()
        reviews.append(review)
    return reviews


def semantic_metrics(
    cases: list[dict[str, Any]], reviews: list[dict[str, Any]], gates: dict[str, Any]
) -> dict[str, Any]:
    valid = [case for case in cases if "empty-invalid" not in case["coverageTags"]]
    primary = {row["caseId"]: row for row in reviews[0]["records"]} if reviews else {}
    missing = [case["caseId"] for case in valid if case["caseId"] not in primary]
    if missing:
        reason = "Separate semantic review incomplete; automated checks are not semantic reviewer scores."
        return {
            name: gate(None, None, missing, reason)
            for name in (
                "semanticFactPrecision",
                "semanticFactRecall",
                "criticalOmissions",
                "sectionPlacementMacroF1",
                "semanticNovelOrChangedProtectedFacts",
                "semanticFalseActiveBlockers",
                "warningCorrectness",
            )
        }
    totals = Counter(
        {name: sum(row[name] for row in primary.values()) for name in SEMANTIC_FIELDS}
    )
    precision = ratio(totals["supportedOutputFacts"], totals["totalOutputFacts"])
    recall = ratio(totals["representedSourceFacts"], totals["requiredSourceFacts"])
    confusion = {section: Counter(tp=0, fp=0, fn=0) for section in SECTIONS}
    placement_failures = set()
    for case in valid:
        actual_by_fact = {
            fact["factId"]: fact["actualSections"]
            for fact in primary[case["caseId"]]["placement"]
        }
        for fact in case["sourceFacts"]:
            if fact["uncertain"] or len(fact["allowedSections"]) != 1:
                continue
            expected = fact["allowedSections"][0]
            actual = set(actual_by_fact.get(fact["factId"], []))
            if actual != {expected}:
                placement_failures.add(case["caseId"])
            for section in SECTIONS:
                confusion[section]["tp"] += int(
                    section == expected and section in actual
                )
                confusion[section]["fn"] += int(
                    section == expected and section not in actual
                )
                confusion[section]["fp"] += int(
                    section != expected and section in actual
                )
    by_section = {}
    for section, counts in confusion.items():
        p = ratio(counts["tp"], counts["tp"] + counts["fp"]) or 0.0
        r = ratio(counts["tp"], counts["tp"] + counts["fn"]) or 0.0
        by_section[section] = {
            **dict(counts),
            "precision": p,
            "recall": r,
            "f1": 2 * p * r / (p + r) if p + r else 0.0,
        }
    macro = sum(values["f1"] for values in by_section.values()) / 3
    return {
        "semanticFactPrecision": gate(
            {
                "numerator": totals["supportedOutputFacts"],
                "denominator": totals["totalOutputFacts"],
                "rate": precision,
            },
            precision is not None
            and precision >= gates["semanticFactPrecisionMinimum"],
            [
                key
                for key, row in primary.items()
                if row["supportedOutputFacts"] < row["totalOutputFacts"]
            ],
        ),
        "semanticFactRecall": gate(
            {
                "numerator": totals["representedSourceFacts"],
                "denominator": totals["requiredSourceFacts"],
                "rate": recall,
            },
            recall is not None and recall >= gates["semanticFactRecallMinimum"],
            [
                key
                for key, row in primary.items()
                if row["representedSourceFacts"] < row["requiredSourceFacts"]
            ],
        ),
        "criticalOmissions": gate(
            totals["criticalOmissions"],
            totals["criticalOmissions"] == 0,
            [key for key, row in primary.items() if row["criticalOmissions"]],
        ),
        "sectionPlacementMacroF1": gate(
            {"macroF1": macro, "sections": by_section},
            macro >= gates["unambiguousMacroSectionF1Minimum"],
            sorted(placement_failures),
        ),
        "semanticNovelOrChangedProtectedFacts": gate(
            totals["novelOrChangedProtectedFacts"],
            totals["novelOrChangedProtectedFacts"] == 0,
            [
                key
                for key, row in primary.items()
                if row["novelOrChangedProtectedFacts"]
            ],
        ),
        "semanticFalseActiveBlockers": gate(
            totals["falseActiveBlockers"],
            totals["falseActiveBlockers"] == 0,
            [key for key, row in primary.items() if row["falseActiveBlockers"]],
        ),
        "warningCorrectness": gate(
            sum(row["warningsCorrect"] for row in primary.values()),
            all(row["warningsCorrect"] for row in primary.values()),
            [key for key, row in primary.items() if not row["warningsCorrect"]],
        ),
    }


def review_agreement(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    if len(reviews) < 2:
        return {
            "status": "not_run",
            "reason": "Only one or no semantic reviewer supplied; no agreement claim.",
        }
    first = {row["caseId"]: row for row in reviews[0]["records"]}
    second = {row["caseId"]: row for row in reviews[1]["records"]}
    overlap = sorted(set(first) & set(second))
    criteria = (*SEMANTIC_FIELDS, "warningsCorrect", "placement")
    disagreement = {
        key: [
            case_id
            for case_id in overlap
            if first[case_id][key] != second[case_id][key]
        ]
        for key in criteria
    }
    return {
        "status": "measured"
        if len(overlap) >= 20
        else "insufficient-double-score-count",
        "doubleScoredCaseCount": len(overlap),
        "caseIds": overlap,
        "agreementByCriterion": {
            key: ratio(len(overlap) - len(ids), len(overlap))
            for key, ids in disagreement.items()
        },
        "disagreements": disagreement,
        "adjudication": "not_needed"
        if not any(disagreement.values())
        else "required; retain both original reviews and add documented adjudication",
        "independence": "Shared model/team context; not independent external validation.",
    }


def make_report(
    cases: list[dict[str, Any]],
    records: list[dict[str, Any]],
    rubric: dict[str, Any],
    manifest: dict[str, Any],
    metadata: dict[str, Any],
    reviews: list[dict[str, Any]],
) -> dict[str, Any]:
    valid_records = [row for row in records if not row["automated"]["expectedInvalid"]]
    invalid_records = [row for row in records if row["automated"]["expectedInvalid"]]
    checks = (
        "strictResponseSchema",
        "commonProtectedFactValidation",
        "meaningfulFragmentCoverage",
        "fallbackNoOmittedFragments",
        "noFalseActiveBlocker",
        "exactAnnotatedProtectedTokens",
    )
    metrics = {}
    for check in checks:
        applicable = [
            row for row in valid_records if check in row["automated"]["checks"]
        ]
        failures = [
            row["caseId"] for row in applicable if not row["automated"]["checks"][check]
        ]
        metrics[check] = gate(
            {
                "passed": len(applicable) - len(failures),
                "total": len(applicable),
                "rate": ratio(len(applicable) - len(failures), len(applicable)),
            },
            not failures if applicable else None,
            failures,
        )
    protected_required = sum(
        row["automated"]["protected"]["required"] for row in valid_records
    )
    protected_preserved = sum(
        row["automated"]["protected"]["preserved"] for row in valid_records
    )
    metrics["protectedTokenPreservation"] = gate(
        {
            "preserved": protected_preserved,
            "required": protected_required,
            "rate": ratio(protected_preserved, protected_required),
        },
        protected_required == protected_preserved,
        [
            row["caseId"]
            for row in valid_records
            if row["automated"]["protected"]["missing"]
        ],
    )
    metrics.update(semantic_metrics(cases, reviews, rubric["releaseGates"]))
    metrics["pairwiseUsefulness"] = gate(
        None,
        None,
        limitation="Live primary provider not run; stub output cannot establish usefulness preference.",
    )
    failures = [row["caseId"] for row in records if row["automated"]["failures"]]
    all_failure_ids = sorted(
        set(failures)
        | {
            case_id
            for metric in metrics.values()
            if metric["verdict"] == "fail"
            for case_id in metric["failureCaseIds"]
        }
    )
    tags = Counter(tag for case in cases for tag in set(case["coverageTags"]))
    per_slice = {}
    for tag in sorted(tags):
        rows = [row for row in records if tag in row["coverageTags"]]
        per_slice[tag] = {
            "cases": len(rows),
            "automatedPassed": sum(not row["automated"]["failures"] for row in rows),
            "failureCaseIds": [
                row["caseId"] for row in rows if row["automated"]["failures"]
            ],
        }
    try:
        git_state = subprocess.run(
            ["git", "status", "--short"],
            cwd=REPOSITORY,
            capture_output=True,
            text=True,
            check=True,
        ).stdout.splitlines()
        head = (
            subprocess.run(
                ["git", "rev-parse", "--verify", "HEAD"],
                cwd=REPOSITORY,
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
            or "no commits"
        )
    except (OSError, subprocess.CalledProcessError):
        git_state, head = ["unavailable"], "unavailable"
    factuality_gates = [
        metric for name, metric in metrics.items() if name != "pairwiseUsefulness"
    ]
    conclusion = (
        "blocked"
        if failures or any(metric["verdict"] == "fail" for metric in factuality_gates)
        else (
            "demonstrated"
            if all(metric["verdict"] == "pass" for metric in factuality_gates)
            else "not demonstrated"
        )
    )
    return {
        "specificationRevision": "REV-002",
        "timestamp": now(),
        "repository": {"commit": head, "state": git_state},
        "dataset": {
            "path": "evaluation/dataset/benchmark.jsonl",
            "sha256": manifest["datasetSha256"],
            "frozenAt": manifest["frozenAt"],
            "caseCount": len(cases),
            "validCaseCount": len(valid_records),
            "invalidCaseCount": len(invalid_records),
            "coverageTagCounts": dict(sorted(tags.items())),
        },
        "rubric": {"version": rubric["version"], "sha256": manifest["rubricSha256"]},
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            **metadata,
        },
        "engines": {
            "rules-fallback-v1": {
                "execution": "run",
                "formatterRevision": metadata["formatterRevision"],
                "metrics": metrics,
                "slices": per_slice,
                "failureCaseIds": all_failure_ids,
                "automatedFailureCaseIds": failures,
                "caseResults": "evaluation/reports/case-results.jsonl",
                "conclusion": conclusion,
            },
            "structured-llm-v1": {
                "execution": "not_run",
                "model": "not_run",
                "settings": "not_run",
                "metrics": {
                    name: gate(
                        None, None, limitation="No authorized live provider run."
                    )
                    for name in metrics
                },
                "failureCaseIds": [],
                "conclusion": "not demonstrated",
                "limitation": "Adapter stubs verify integration correctness only; no live primary quality, latency, retention or cost claim.",
            },
        },
        "invalidInput": {
            "count": len(invalid_records),
            "passed": sum(not row["automated"]["failures"] for row in invalid_records),
            "failureCaseIds": [
                row["caseId"] for row in invalid_records if row["automated"]["failures"]
            ],
        },
        "review": {
            "reviewerCount": len(reviews),
            "provenance": [review["reviewer"] for review in reviews],
            "evidencePaths": [review["evidencePath"] for review in reviews],
            "agreement": review_agreement(reviews),
            "limitations": [
                "RISK-005: model-authored fictional benchmark; shared model/team context.",
                "Automated span/placement matches are proxies and remain separate from semantic reviewer scores.",
                "Single-output review is not blinded pairwise usefulness evidence.",
            ],
        },
        "editingEffort": {
            "status": "reviewed",
            "counts": {
                kind: sum(row["editingEffort"][kind] for row in reviews[0]["records"])
                for kind in ("edits", "deletes", "additions", "moves")
            },
            "reviewedCases": len(reviews[0]["records"]),
        }
        if reviews
        else {
            "status": "not_run",
            "reason": "Requires actual reviewer simulation; not inferred from exact matching.",
        },
        "latency": {
            "status": "not_run",
            "reason": "Case timings measure direct service calls only, not client-visible output paint; browser profile is separate.",
        },
        "cost": "not_measured",
        "providerIntegrationEvidence": {
            "status": "not_run",
            "reason": "Separate stubbed adapter tests supply this evidence.",
        },
        "previousRunEvidence": [
            path.relative_to(REPOSITORY).as_posix()
            for path in sorted(
                (ROOT / "reports" / "runs").glob("*/execution-metadata.json")
            )
        ],
        "conclusionScope": "Local frozen fallback benchmark only; excludes live primary quality, pairwise improvement and deployed latency.",
        "conclusion": conclusion,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--adapter",
        default="backend_adapter",
        help="Local-only adapter module exposing metadata() and run_case().",
    )
    parser.add_argument(
        "--review",
        action="append",
        type=Path,
        default=[],
        help="Completed semantic review JSON; first file is primary.",
    )
    parser.add_argument(
        "--reuse-results",
        action="store_true",
        help="Regenerate reports from existing case-level results without rerunning formatter.",
    )
    parser.add_argument(
        "--require-semantic-pass",
        action="store_true",
        help="Fail unless completed semantic factuality gates also pass.",
    )
    parser.add_argument(
        "--latency-report",
        type=Path,
        help="Attach separately measured client-visible latency evidence without inventing measurements.",
    )
    parser.add_argument(
        "--provider-integration-report",
        type=Path,
        help="Attach deterministic adapter-test evidence; this never changes live primary quality status.",
    )
    args = parser.parse_args()
    cases, rubric, manifest = load_frozen()
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    if args.reuse_results:
        records = [
            json.loads(line)
            for line in (reports / "case-results.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        metadata = json.loads(
            (reports / "execution-metadata.json").read_text(encoding="utf-8")
        )
        if {row["caseId"] for row in records} != {case["caseId"] for case in cases}:
            raise ValueError("Stored results do not cover exactly the frozen cases.")
        if (
            metadata.get("datasetSha256") != manifest["datasetSha256"]
            or metadata.get("rubricSha256") != manifest["rubricSha256"]
        ):
            raise ValueError("Stored execution used a different benchmark or rubric.")
        if metadata.get("caseResultsSha256") != sha256(reports / "case-results.jsonl"):
            raise ValueError("Case-level result hash mismatch.")
        if metadata.get("reviewPacketSha256") != sha256(
            reports / "semantic-review-packet.jsonl"
        ):
            raise ValueError("Semantic review packet hash mismatch.")
    else:
        adapter = importlib.import_module(args.adapter)
        metadata = adapter.metadata()
        if metadata.get("providerEnabled") is not False:
            raise ValueError(
                "Evaluation requires an explicitly disabled provider; refusing possible paid calls."
            )
        if not metadata.get("formatterRevision"):
            raise ValueError("Adapter must supply an immutable formatter revision.")
        archive_previous_run(reports)
        records = []
        packet = []
        for case in cases:
            started = time.perf_counter()
            execution = adapter.run_case(case)
            elapsed = round((time.perf_counter() - started) * 1000, 3)
            automated = score_automated(case, execution)
            records.append(
                {
                    "caseId": case["caseId"],
                    "coverageTags": case["coverageTags"],
                    "executedAt": now(),
                    "serviceCallElapsedMs": elapsed,
                    "formatterRevision": metadata["formatterRevision"],
                    "statusCode": execution["statusCode"],
                    "response": execution["response"],
                    "sourceFragments": execution.get("sourceFragments", []),
                    "automated": automated,
                }
            )
            if not automated["expectedInvalid"]:
                packet.append(review_packet(case, execution))
            print(
                f"{case['caseId']}: {'FAIL ' + ','.join(automated['failures']) if automated['failures'] else 'automated checks pass'}"
            )
        after_metadata = adapter.metadata()
        if after_metadata["formatterRevision"] != metadata["formatterRevision"]:
            raise ValueError(
                "Backend source changed during benchmark execution; rerun once the source is stable."
            )
        write_jsonl(reports / "case-results.jsonl", records)
        write_jsonl(reports / "semantic-review-packet.jsonl", packet)
        write_jsonl(
            reports / "semantic-review-compact.jsonl", compact_review_packet(packet)
        )
        metadata.update(
            {
                "datasetSha256": manifest["datasetSha256"],
                "rubricSha256": manifest["rubricSha256"],
                "caseResultsSha256": sha256(reports / "case-results.jsonl"),
                "reviewPacketSha256": sha256(reports / "semantic-review-packet.jsonl"),
            }
        )
        write_json(reports / "execution-metadata.json", metadata)
        write_json(
            reports / "semantic-review-template.json",
            review_template(cases, manifest, metadata["reviewPacketSha256"]),
        )
    reviews = load_reviews(args.review, manifest, metadata["reviewPacketSha256"])
    report = make_report(cases, records, rubric, manifest, metadata, reviews)
    for argument, key in (
        (args.latency_report, "latency"),
        (args.provider_integration_report, "providerIntegrationEvidence"),
    ):
        if argument is not None:
            evidence_path = argument.resolve()
            if not evidence_path.is_relative_to(REPOSITORY):
                raise ValueError(
                    "Attached evidence must be a project artifact inside the repository."
                )
            report[key] = {
                "evidencePath": evidence_path.relative_to(REPOSITORY).as_posix(),
                "sha256": sha256(evidence_path),
                "evidence": json.loads(evidence_path.read_text(encoding="utf-8")),
            }
    write_json(reports / "release-report.json", report)
    automated_failures = report["engines"]["rules-fallback-v1"][
        "automatedFailureCaseIds"
    ]
    print(
        json.dumps(
            {
                "cases": len(cases),
                "automatedFailureCaseIds": automated_failures,
                "semanticReviewers": len(reviews),
                "conclusion": report["conclusion"],
                "report": "evaluation/reports/release-report.json",
            },
            indent=2,
        )
    )
    if automated_failures or (
        args.require_semantic_pass and report["conclusion"] != "demonstrated"
    ):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
