import logging
from pydantic_settings import BaseSettings, SettingsConfigDict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

class Settings(BaseSettings):
    BOT_TOKEN: str
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    RUN_TELEGRAM: bool = True
    RUN_API: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
