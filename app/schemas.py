from pydantic import BaseModel, Field

class AverageWeatherResponse(BaseModel):
    city: str = Field(..., description="Canonical city name")
    days: int = Field(..., ge=1, le=30, description="Past days (1–30)")
    average_temperature_c: float
