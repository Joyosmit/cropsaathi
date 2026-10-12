"""CropBima Express settings."""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./cropbima.db")
    MOCK_MODE: bool = os.getenv("MOCK_MODE", "true").lower() in ("1", "true", "yes")
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "./uploads")
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "15"))

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

def use_mock() -> bool:
    if settings.MOCK_MODE:
        return True
    return not bool(settings.SARVAM_API_KEY and "your_" not in settings.SARVAM_API_KEY)
