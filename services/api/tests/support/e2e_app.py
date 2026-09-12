import asyncio
import os

from pydantic import SecretStr

from app.core.config import Settings
from app.formatters.rules_fallback_v1 import format_fallback
from app.main import create_app as production_app
from app.models.generation import StandupDraft
from app.models.source_fragment import SourceFragment
from app.models.style_profile import StyleProfile
from app.providers.formatter_provider import ProviderFailure


class LocalScenarioProvider:
    async def generate(
        self, fragments: list[SourceFragment], profile: StyleProfile
    ) -> StandupDraft:
        scenario = os.environ.get("E2E_PROVIDER_SCENARIO", "success")
        if scenario == "timeout":
            await asyncio.sleep(2)
        if scenario == "malformed":
            raise ProviderFailure(infrastructure=False)
        draft = format_fallback(fragments, profile).draft
        if scenario == "novel":
            for items in (draft.yesterday, draft.today, draft.blockers):
                if items:
                    items[0].text += " fabricated TEST-999999"
                    break
        return draft


def create_app():
    settings = Settings(
        environment="test",
        formatter_provider="openai",
        formatter_model="local-stub",
        formatter_api_key=SecretStr("fictional-local-only-key"),
        formatter_privacy_verified=True,
        formatter_timeout_seconds=0.05,
        rate_limit_per_minute=10000,
        allowed_origins=("http://localhost:3000", "http://localhost:3100", "http://127.0.0.1:3000"),
    )
    return production_app(settings, LocalScenarioProvider())
