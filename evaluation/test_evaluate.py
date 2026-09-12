"""Evidence-tool checks: detect regressions without changing the frozen dataset."""

from __future__ import annotations

import copy
import unittest
from uuid import uuid4

from evaluate import (
    load_frozen,
    public_schema_errors,
    score_automated,
    semantic_metrics,
)


def sample_response(text: str) -> dict:
    return {
        "draft": {
            "yesterday": [],
            "today": [{"itemId": "D001", "text": text, "sourceFragmentIds": ["F001"]}],
            "blockers": [],
        },
        "engineVersion": "rules-fallback-v1",
        "warnings": [
            {
                "warningId": "W001",
                "code": "FALLBACK_USED",
                "message": "Fallback used.",
                "section": None,
                "itemId": None,
                "sourceFragmentIds": [],
            }
        ],
        "durationMs": 0,
        "requestId": str(uuid4()),
        "clientRequestId": str(uuid4()),
    }


class EvidenceToolTests(unittest.TestCase):
    def test_frozen_hashes_and_case_membership(self) -> None:
        cases, rubric, manifest = load_frozen()
        self.assertEqual(len(cases), 72)
        self.assertEqual(
            sum("empty-invalid" in case["coverageTags"] for case in cases), 3
        )
        self.assertEqual(rubric["releaseGates"]["semanticFactPrecisionMinimum"], 1)
        self.assertEqual(
            manifest["datasetSha256"],
            "7f2125f0b686678adba7eaa1d48c86304ba6f873065ba93a73e9400d393b6951",
        )

    def test_full_length_protected_token_cannot_be_silently_shortened(self) -> None:
        token = "https://example.invalid/" + "a" * (
            10000 - len("https://example.invalid/")
        )
        case = {
            "coverageTags": ["boundary-length"],
            "sourceFacts": [
                {
                    "factId": "FACT-01",
                    "sourceText": token,
                    "allowedSections": ["today"],
                    "protectedTokens": [token],
                    "uncertain": True,
                }
            ],
        }
        execution = {
            "statusCode": 200,
            "response": sample_response(token),
            "backendSchemaValid": True,
            "commonValidationPassed": True,
            "sourceFragments": [{"fragmentId": "F001", "text": token}],
        }
        self.assertEqual(public_schema_errors(execution["response"]), [])
        self.assertEqual(score_automated(case, execution)["failures"], [])
        damaged = copy.deepcopy(execution)
        damaged["response"]["draft"]["today"][0]["text"] = token[:-1]
        result = score_automated(case, damaged)
        self.assertIn("exactAnnotatedProtectedTokens", result["failures"])
        self.assertEqual(result["protected"]["preserved"], 0)

    def test_unknown_output_properties_and_target_errors_fail(self) -> None:
        response = sample_response("Fictional source text")
        response["providerPayload"] = "must not appear"
        self.assertIn("response-field-set", public_schema_errors(response))
        del response["providerPayload"]
        response["warnings"][0]["itemId"] = "D999"
        self.assertIn("warning-item-reference", public_schema_errors(response))

    def test_automated_scores_never_fill_unperformed_semantic_review(self) -> None:
        cases, rubric, _ = load_frozen()
        results = semantic_metrics(cases, [], rubric["releaseGates"])
        self.assertTrue(
            all(metric["verdict"] == "not_run" for metric in results.values())
        )
        self.assertTrue(
            all(len(metric["failureCaseIds"]) == 69 for metric in results.values())
        )

    def test_invalid_request_requires_real_field_error_and_no_formatter(self) -> None:
        case = {"coverageTags": ["empty-invalid"]}
        execution = {
            "statusCode": 422,
            "response": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "fieldErrors": {"rawNotes": ["Enter notes."]},
                }
            },
            "formatterInvoked": False,
        }
        self.assertEqual(score_automated(case, execution)["failures"], [])
        execution["formatterInvoked"] = True
        self.assertIn(
            "formatterNotInvoked", score_automated(case, execution)["failures"]
        )


if __name__ == "__main__":
    unittest.main()
