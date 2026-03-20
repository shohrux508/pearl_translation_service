import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

class Settings(BaseSettings):
    BOT_TOKEN: str
    GEMINI_API_KEY: str = "" # Ключ не сделан обязательным, чтобы не ломать старый код
    API_HOST: str = "0.0.0.0"
    PORT: int = 8000
    RUN_TELEGRAM: bool = True
    RUN_API: bool = True
    ADMIN_IDS: str = "" # Comma-separated list of admin user IDs

    @property
    def parsed_admin_ids(self) -> list[int]:
        if not self.ADMIN_IDS:
            return []
        return [int(x.strip()) for x in self.ADMIN_IDS.split(",") if x.strip().isdigit()]

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
