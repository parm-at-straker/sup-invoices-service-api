from pydantic import Field, SecretStr, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from straker_utils.domain import StrakerDomains
from straker_utils.environment import Environment
import os


domains = StrakerDomains.from_environment()


class StrakerConfig(BaseSettings):
    """The configuration for this app. Use this class to define settings that
    are different depending on the environment variables (keys, passwords,
    URLs, etc.) or running environment (local, uat, production, etc.).
    """

    model_config = SettingsConfigDict(frozen=True)

    # Environment variables.
    environment: Environment
    health_check_password: SecretStr = SecretStr("")
    elastic_apm_server_url: str = ""

    # CORS Configuration
    cors_origins_raw: str = Field(default="", validation_alias="CORS_ORIGINS")

    # Derived settings.
    buglog_listener_url: str = ""

    @field_validator("health_check_password", mode="after")
    def validate_health_check_password(cls, v, info: ValidationInfo):
        if info.data["environment"] == Environment.production:
            if not v:
                raise ValueError("The health check password must be set in production")
        return v

    @field_validator("buglog_listener_url", mode="before")
    def default_buglog_listener_url(cls, v):
        return f"{domains.buglog}/bugLog/listeners/bugLogListenerREST.cfm"

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from raw string or use defaults."""
        if self.cors_origins_raw:
            # Parse comma-separated string, strip whitespace and quotes
            return [
                origin.strip().strip('"').strip("'")
                for origin in self.cors_origins_raw.split(",")
                if origin.strip()
            ]

        # Default origins for local development
        return [
            "http://localhost:13001",  # Verify Hub UI dev
            "http://localhost:3000",  # Alternate dev port
            "https://franchise.strakergroup.com",  # Production
            "https://franchise-staging.strakergroup.com",  # Staging
        ]


config = StrakerConfig()  # type: ignore
