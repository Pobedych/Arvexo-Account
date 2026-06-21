from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    public_site_url: str = "http://localhost:9101"
    public_api_url: str = "http://localhost:8032"
    frontend_url: str = "http://localhost:9101"
    database_url: str = "postgresql+psycopg://arvexo:arvexo@postgres:5432/arvexo_account"
    redis_url: str = "redis://redis:6379/0"
    jwt_secret: str = Field(default="change_me_change_me", min_length=12)
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 30
    cookie_domain: str | None = None
    cookie_secure: bool = False
    cookie_samesite: str = "lax"

    # Google OAuth (disabled until credentials are set)
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8032/auth/google/callback"

    # Yandex OAuth
    yandex_client_id: str = ""
    yandex_client_secret: str = ""
    yandex_redirect_uri: str = "http://localhost:8032/auth/yandex/callback"

    # Telegram OIDC (Client ID и Secret берутся из BotFather → Login Widget → OpenID Connect)
    telegram_client_id: str = ""
    telegram_client_secret: str = ""
    telegram_bot_token: str = ""   # нужен только для проверки is_configured
    telegram_redirect_uri: str = "http://localhost:8032/auth/telegram/callback"

    # SSO seed — Arvexo Study
    seed_arvexo_study_client: bool = True
    arvexo_study_client_id: str = "arvexo-study"
    arvexo_study_client_secret: str = "dev_secret"
    arvexo_study_redirect_uri: str = "http://localhost:9101/auth/callback"

    # SSO seed — Arvexo Consulting
    seed_arvexo_consulting_client: bool = True
    arvexo_consulting_client_id: str = "arvexo-consulting"
    arvexo_consulting_client_secret: str = "dev_consulting_secret"
    arvexo_consulting_redirect_uri: str = "http://localhost:8000/api/auth/callback"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("cookie_domain", mode="before")
    @classmethod
    def normalize_cookie_domain(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = str(value).strip()
        return stripped or None

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() == "production"

    @property
    def cors_origins(self) -> list[str]:
        origins = {self.frontend_url, self.public_site_url}
        if not self.is_production:
            origins.update({"http://localhost", "http://localhost:3000", "http://127.0.0.1:3000"})
        return sorted(origin.rstrip("/") for origin in origins if origin)

    @property
    def oauth_enabled(self) -> dict:
        return {
            "google": bool(self.google_client_id and self.google_client_secret),
            "yandex": bool(self.yandex_client_id and self.yandex_client_secret),
            "telegram": bool(self.telegram_client_id and self.telegram_client_secret),
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
