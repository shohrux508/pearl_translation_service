"""
Единая конфигурация приложения (Pydantic Settings).

Все значения читаются из .env файла.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Telegram ──────────────────────────────────────────────────────
    BOT_TOKEN: str
    ADMIN_IDS: list[int] = []

    # ── AI / Gemini ───────────────────────────────────────────────────
    GEMINI_API_KEY: str = ""
    GEMINI_API_KEY2: str = ""

    # ── API ───────────────────────────────────────────────────────────
    API_HOST: str = "0.0.0.0"
    PORT: int = 8000
    RUN_TELEGRAM: bool = True
    RUN_API: bool = True

    # ── Webapp ────────────────────────────────────────────────────────
    RUN_WEBAPP: bool = False
    WEBAPP_PORT: int = 8001

    # ── Логирование ───────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str | None = None
    LOG_JSON: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
