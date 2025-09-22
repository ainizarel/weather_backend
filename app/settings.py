import os
from pydantic import BaseModel

class Settings(BaseModel):
    cors_origins: str = os.getenv("CORS_ORIGINS", "http://localhost:5173")
    api_port: int = int(os.getenv("API_PORT", 8000))
    redis_url: str | None = os.getenv("REDIS_URL")

settings = Settings()
