"""Local formatter adapter. Provider work is disabled and never invoked."""

from __future__ import annotations

import asyncio
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

API_ROOT = Path(__file__).resolve().parents[1] / "services" / "api"
sys.path.insert(0, str(API_ROOT))
# This process is dedicated to no-provider evaluation, including import-time app setup.
os.environ["FORMATTER_PROVIDER"] = "disabled"
os.environ["ENVIRONMENT"] = "test"


def source_fingerprint() -> tuple[str, dict[str, str]]:
    digest = hashlib.sha256()
    files: dict[str, str] = {}
    for path in sorted((API_ROOT / "app").rglob("*.py")):
        relative = path.relative_to(API_ROOT).as_posix()
        content = path.read_bytes()
        files[relative] = hashlib.sha256(content).hexdigest()
        digest.update(relative.encode("utf-8") + b"\0" + content + b"\0")
    return digest.hexdigest(), files


def metadata() -> dict[str, Any]:
    from app.core.config import Settings
    from app.formatters.rules_fallback_v1 import FORMATTER_REVISION

    settings = Settings(environment="test", formatter_provider="disabled")
    fingerprint, files = source_fingerprint()
    return {
        "providerEnabled": settings.provider_enabled,
        "formatterRevision": f"{FORMATTER_REVISION}+sha256:{fingerprint}",
        "formatterFamilyRevision": FORMATTER_REVISION,
        "backendSourceSha256": fingerprint,
        "backendSourceFiles": files,
        "executionMethod": "Complete no-provider GenerationService response plus independent common-validator recheck for valid cases; actual in-process FastAPI validation requests for invalid cases.",
        "providerCalls": 0,
        "network": "No external requests; TestClient is in-process.",
    }


def run_case(case: dict[str, Any]) -> dict[str, Any]:
    from app.core.config import Settings
    from app.core.errors import APIError
    from app.core.service import GenerationService
    from app.formatters.fragmenter import prepare_request
    from app.formatters.validator import UnsafeDraft, validate_result
    from app.models.generation import GenerateRequest, GenerateResponse
    from app.models.source_fragment import FormatResult
    from app.models.style_profile import builtin_profile
    from pydantic import ValidationError

    payload = {
        "rawNotes": case["rawNotes"],
        "styleProfile": builtin_profile(case["styleProfileId"]).model_dump(mode="json"),
        "clientRequestId": str(uuid4()),
    }
    try:
        request = GenerateRequest.model_validate(payload)
    except ValidationError:
        from app.main import create_app
        from fastapi.testclient import TestClient

        with TestClient(
            create_app(Settings(environment="test", formatter_provider="disabled"))
        ) as client:
            response = client.post("/api/v1/generate", json=payload)
        return {
            "statusCode": response.status_code,
            "response": response.json(),
            "formatterInvoked": False,
            "backendSchemaValid": False,
            "commonValidationPassed": False,
            "sourceFragments": [],
        }

    fragments = prepare_request(request.raw_notes)
    exposed_fragments = [
        {
            "fragmentId": fragment.fragment_id,
            "sourceStart": fragment.source_start,
            "sourceEnd": fragment.source_end,
            "text": fragment.text,
            "exemptFromOutput": not fragment.meaningful,
        }
        for fragment in fragments
    ]
    try:
        service = GenerationService(
            Settings(environment="test", formatter_provider="disabled")
        )
        response_model = asyncio.run(service.generate(request, uuid4()))
        validate_result(
            FormatResult(response_model.draft, response_model.warnings),
            fragments,
            request.style_profile,
        )
        response = response_model.model_dump(mode="json")
        GenerateResponse.model_validate_json(json.dumps(response))
    except (APIError, UnsafeDraft, ValidationError) as error:
        return {
            "statusCode": 503,
            "response": {
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "Local formatter validation failed.",
                    "requestId": str(uuid4()),
                    "clientRequestId": payload["clientRequestId"],
                    "fieldErrors": {},
                }
            },
            "formatterInvoked": True,
            "backendSchemaValid": False,
            "commonValidationPassed": False,
            "sourceFragments": exposed_fragments,
            "diagnosticType": type(error).__name__,
        }
    return {
        "statusCode": 200,
        "response": response,
        "formatterInvoked": True,
        "backendSchemaValid": True,
        "commonValidationPassed": True,
        "sourceFragments": exposed_fragments,
        "absenceOnly": not any(fragment.meaningful for fragment in fragments),
    }
