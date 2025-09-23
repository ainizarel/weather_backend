import os
from typing import List, Optional
from pydantic import BaseModel

def parse_origins(raw: str) -> List[str]:
    raw = (raw or "").strip()
    if raw in ("", "*"):
        return ["*"]
    return [o.strip() for o in raw.split(",") if o.strip()]

class Settings(BaseModel):
    cors_origins: List[str] = parse_origins(
        os.getenv("CORS_ORIGINS", "http://localhost:3000")
    )
    api_port: int = int(os.getenv("API_PORT", 8000))
    redis_url: Optional[str] = os.getenv("REDIS_URL")

settings = Settings()
