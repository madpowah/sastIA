from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./sastia.db"
    SECRET_KEY: str  # Must be set via environment variable - no default for security
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    ANALYSIS_WEBHOOK_URL: str = "http://analysis-worker:9000/analyze"
    AI_ANALYSIS_ENABLED: bool = True
    WORKER_URL: str = "http://localhost:9000"
    CODE_DOWNLOAD_BASE_URL: str = "http://localhost:8000"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
