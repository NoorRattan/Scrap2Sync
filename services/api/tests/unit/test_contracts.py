import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.main import create_app
from app.models.generation import DraftItem, GenerateRequest
from app.models.style_profile import BUILTIN_PROFILES, builtin_profile


def request_data(notes="finished a fictional check"):
    return {
        "rawNotes": notes,
        "styleProfile": builtin_profile().model_dump(),
        "clientRequestId": "6d4ce98e-4f6f-4eb7-81f8-09a89a073734",
    }


def test_alias_only_and_json_roundtrip():
    data = request_data(" A\r\nB\rC ")
    body = GenerateRequest.model_validate(data)
    assert body.raw_notes == "A\nB\nC"
    assert set(body.model_dump()) == {"rawNotes", "styleProfile", "clientRequestId"}
    data["raw_notes"] = data.pop("rawNotes")
    with pytest.raises(ValidationError):
        GenerateRequest.model_validate(data)


@pytest.mark.parametrize(
    "notes",
    ["", "  ", "x" * 10001, "secret\x00", "\ud800"],
    ids=["empty", "blank", "oversize", "control", "surrogate"],
)
def test_invalid_notes(notes):
    with pytest.raises(ValidationError):
        GenerateRequest.model_validate(request_data(notes))


@pytest.mark.parametrize(
    "notes",
    ["🙂" * 10000, "https://example.test/" + "a" * 9979, "<Button disabled>"],
    ids=["emoji", "long-url", "markup"],
)
def test_valid_unicode_and_long_item(notes):
    body = GenerateRequest.model_validate(request_data(notes))
    item = DraftItem(itemId="D001", text=body.raw_notes, sourceFragmentIds=["F001"])
    assert item.text == notes


@pytest.mark.parametrize("profile_id", list(BUILTIN_PROFILES))
def test_exact_builtins(profile_id):
    data = request_data()
    data["styleProfile"] = builtin_profile(profile_id).model_dump()
    GenerateRequest.model_validate(data)
    data["styleProfile"]["label"] = "changed"
    with pytest.raises(ValidationError):
        GenerateRequest.model_validate(data)


def test_health_and_contract():
    app = create_app(Settings())
    with TestClient(app) as client:
        assert client.get("/api/v1/health/live").json() == {"status": "ok"}
        response = client.get("/api/v1/health/ready")
        assert response.json() == {"status": "ready", "primaryFormatter": "unconfigured"}
        assert response.headers["cache-control"] == "no-store"
        assert response.headers["x-request-id"]
    schema = app.openapi()["components"]["schemas"]
    assert "rawNotes" in schema["GenerateRequest"]["properties"]
    assert schema["DraftItem"]["properties"]["text"]["maxLength"] == 10000


@pytest.mark.parametrize(
    "values",
    [
        {"ALLOWED_ORIGINS": "*"},
        {"ALLOWED_ORIGINS": "http://example.test"},
        {"ALLOWED_ORIGINS": "https://example.test/path"},
        {"ENVIRONMENT": "production"},
        {"MAX_DRAFT_ITEM_CHARS": "4000"},
        {"TRUSTED_PROXY_COUNT": "1"},
    ],
)
def test_unsafe_configuration(values):
    with pytest.raises(ValueError):
        Settings.from_env(values)


def test_privacy_gate_and_secret_redaction():
    settings = Settings(
        formatter_provider="openai",
        formatter_model="operator-exact-model",
        formatter_api_key="fictional-marker",
    )
    assert not settings.provider_enabled
    assert "fictional-marker" not in repr(settings)
