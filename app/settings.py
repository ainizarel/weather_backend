import os
from typing import List
from pydantic import BaseModel

def parse_origins(raw: str) -> List[str]:
    # supports: "*" OR comma-separated list
    raw = (raw or "").strip()
    if raw == "*" or raw == "":
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]

class Settings(BaseModel):
    cors_origins: List[str] = parse_origins(os.getenv("CORS_ORIGINS", "http://localhost:3000"))
    api_port: int = int(os.getenv("API_PORT", 8000))
    redis_url: str | None = os.getenv("REDIS_URL")
    # NEW: configurable cap (0 disables the cap)
    max_days: int = int(os.getenv("WEATHER_MAX_DAYS", 0))

settings = Settings()
