import secrets

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../../.env", extra="ignore")
    database_url: str = "sqlite:///./finsphere.db"
    jwt_secret: str = Field(default_factory=lambda: secrets.token_urlsafe(48), min_length=32)
    jwt_expires_minutes: int = 30
    web_origin: str = "http://localhost:3000"
    web_origins: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""
    openai_api_key: str = ""
    openai_model: str = "gpt-6-astra"
    openai_timeout_seconds: float = Field(default=20, gt=0, le=90)
    mfa_encryption_key: str = ""

    @property
    def allowed_web_origins(self) -> list[str]:
        if self.web_origins.strip():
            return [origin.strip() for origin in self.web_origins.split(",") if origin.strip()]
        origins = [self.web_origin]
        if self.web_origin == "http://localhost:3000":
            origins.append("http://localhost:3001")
        return origins


settings = Settings()
