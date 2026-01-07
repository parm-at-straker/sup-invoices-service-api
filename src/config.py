from pydantic import SecretStr, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from straker_utils.domain import StrakerDomains
from straker_utils.environment import Environment


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


config = StrakerConfig()  # type: ignore
