import os
from pydantic import BaseModel
from typing import List

def parse_csv_origins(raw: str | None, default: list[str]) -> list[str]:
    if not raw:
        return default
    # split, trim, and remove trailing slashes
    out = []
    for item in raw.split(","):
        s = item.strip().rstrip("/")
        if s:
            out.append(s)
    return out or default

class Settings(BaseModel):
    cors_origins: List[str] = parse_csv_origins(
        os.getenv("CORS_ORIGINS"),
        ["http://localhost:3000", "http://localhost:5173"],
    )
    api_port: int = int(os.getenv("API_PORT", 8000))
    redis_url: str | None = os.getenv("REDIS_URL")
    # 0 or empty disables the cap
    max_days: int | None = int(os.getenv("WEATHER_MAX_DAYS", "0") or "0")

settings = Settings()

