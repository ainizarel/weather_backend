# schemas.py
from pydantic import BaseModel, Field
from .settings import settings  # to mention the cap in docs (optional)

_cap = (
    f"; capped at {settings.max_days}"
    if settings.max_days and settings.max_days > 0
    else "; server-configurable"
)

class AverageWeatherResponse(BaseModel):
    city: str = Field(..., description="Canonical city name")
    # remove le=30 — keep only ge=1, and document the configurable cap
    days: int = Field(..., ge=1, description=f"Past days (≥1{_cap})")
    average_temperature_c: float
