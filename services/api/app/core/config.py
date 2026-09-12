import ipaddress
import os
from collections.abc import Mapping
from typing import Literal, Self
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, SecretStr, model_validator


class Settings(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)
    environment: Literal["development", "test", "production"] = "development"
    allowed_origins: tuple[str, ...] = ("http://localhost:3000",)
    formatter_provider: Literal["disabled", "openai"] = "disabled"
    formatter_model: str = ""
    formatter_api_key: SecretStr = SecretStr("")
    formatter_privacy_verified: bool = False
    formatter_timeout_seconds: float = Field(default=8, gt=0, le=8)
    total_request_timeout_seconds: float = Field(default=10, ge=1, le=30)
    max_raw_notes_chars: Literal[10000] = 10000
    max_request_bytes: Literal[65536] = 65536
    max_draft_chars: Literal[20000] = 20000
    max_draft_item_chars: Literal[10000] = 10000
    max_provider_response_bytes: int = Field(default=262144, ge=65536, le=262144)
    max_response_bytes: int = Field(default=1048576, ge=262144, le=1048576)
    rate_limit_per_minute: int = Field(default=10, ge=1, le=10000)
    max_provider_concurrency: int = Field(default=8, ge=1, le=64)
    max_queue_depth: int = Field(default=16, ge=0, le=128)
    circuit_breaker_failures: int = Field(default=5, ge=1, le=100)
    circuit_breaker_reset_seconds: float = Field(default=30, ge=0.01, le=300)
    trusted_proxy_count: int = Field(default=0, ge=0, le=8)
    trusted_proxy_cidrs: tuple[str, ...] = ()
    provider_monthly_budget_approved: bool = False
    deployment_limits_verified: bool = False
    log_level: Literal["INFO", "WARNING", "ERROR"] = "INFO"

    @property
    def provider_enabled(self) -> bool:
        return bool(
            self.formatter_provider == "openai"
            and self.formatter_model
            and self.formatter_api_key.get_secret_value()
            and self.formatter_privacy_verified
        )

    @model_validator(mode="after")
    def safe_configuration(self) -> Self:
        if not self.allowed_origins:
            raise ValueError("Explicit frontend origins are required.")
        for origin in self.allowed_origins:
            parsed = urlsplit(origin)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.hostname
                or parsed.path
                or parsed.query
                or parsed.fragment
                or parsed.username
                or parsed.password
                or "*" in origin
                or parsed.netloc.endswith(":")
            ):
                raise ValueError("Configure exact origins only.")
            try:
                _ = parsed.port
            except ValueError:
                raise ValueError("Invalid origin port.") from None
            if parsed.scheme != "https":
                if self.environment == "production" or parsed.hostname not in {
                    "localhost",
                    "127.0.0.1",
                    "::1",
                }:
                    raise ValueError("HTTPS is required outside loopback development.")
        if self.trusted_proxy_count and not self.trusted_proxy_cidrs:
            raise ValueError("Trusted proxy networks are required.")
        for network in self.trusted_proxy_cidrs:
            if ipaddress.ip_network(network).prefixlen == 0:
                raise ValueError("Unrestricted proxy trust is prohibited.")
        if self.environment == "production" and (
            not self.deployment_limits_verified or not self.provider_monthly_budget_approved
        ):
            raise ValueError(
                "Production capacity, topology, and budget require operator verification."
            )
        if self.total_request_timeout_seconds < self.formatter_timeout_seconds + 0.5:
            raise ValueError("Reserve time for fallback after the provider deadline.")
        return self

    @classmethod
    def from_env(cls, environ: Mapping[str, str] | None = None) -> Self:
        env = os.environ if environ is None else environ
        data: dict[str, object] = {}
        for name in cls.model_fields:
            key = name.upper()
            if key not in env:
                continue
            value = env[key]
            if name in {"allowed_origins", "trusted_proxy_cidrs"}:
                data[name] = tuple(part.strip() for part in value.split(",") if part.strip())
            elif name.startswith("max_") or name in {
                "rate_limit_per_minute",
                "circuit_breaker_failures",
                "trusted_proxy_count",
            }:
                data[name] = int(value)
            else:
                data[name] = value
        if env.get("ENVIRONMENT") == "production":
            required = {
                "ALLOWED_ORIGINS",
                "TRUSTED_PROXY_COUNT",
                "RATE_LIMIT_PER_MINUTE",
                "MAX_PROVIDER_CONCURRENCY",
                "MAX_QUEUE_DEPTH",
                "DEPLOYMENT_LIMITS_VERIFIED",
                "PROVIDER_MONTHLY_BUDGET_APPROVED",
            }
            if not required.issubset(env):
                raise ValueError("Production configuration is incomplete.")
        return cls.model_validate(data)
