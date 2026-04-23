from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent



class Settings(BaseSettings):
    PROJECT_NAME: str = "IT Support Agent"
    DATABASE_URL: str
    DEBUG: bool = False
    GEMINI_API_KEY: str = None
    GEMINI_MODEL: str = None
    OLLAMA_MODEL: str = None
    TELEGRAM_BOT_TOKEN: str = None

    model_config = SettingsConfigDict(env_file = BASE_DIR / ".env")


settings = Settings()