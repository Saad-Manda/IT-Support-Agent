from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent



class Settings(BaseSettings):
    PROJECT_NAME: str = "IT Support Agent"
    DATABASE_URL: str
    DEBUG: bool = False

    model_config = SettingsConfigDict(env_file = BASE_DIR / ".env")


settings = Settings()