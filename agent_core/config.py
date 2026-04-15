from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent



class Settings(BaseSettings):
    PROJECT_NAME: str = "IT Support Agent"
    DATABASE_URL: str
    DEBUG: bool = False
    GEMINI_API_KEY: str
    GEMINI_MODEL: str

    model_config = SettingsConfigDict(env_file = BASE_DIR / ".env")


settings = Settings()