"""CropBima Express settings (deploy-safe: /tmp uploads, portable sqlite path)."""
import os
import tempfile
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

def _default_upload_dir() -> str:
    # Serverless (Vercel/Lambda): only /tmp is writable
    if os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return os.path.join(tempfile.gettempdir(), "cropbima-uploads")
    return os.getenv("UPLOAD_DIR", "./uploads")

class Settings(BaseSettings):
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./cropbima.db")
    MOCK_MODE: bool = os.getenv("MOCK_MODE", "true").lower() in ("1", "true", "yes")
    UPLOAD_DIR: str = _default_upload_dir()
    MAX_UPLOAD_MB: int = int(os.getenv("MAX_UPLOAD_MB", "15"))

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

def use_mock() -> bool:
    if settings.MOCK_MODE:
        return True
    return not bool(settings.SARVAM_API_KEY and "your_" not in settings.SARVAM_API_KEY)

