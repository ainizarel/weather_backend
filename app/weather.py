# app/main.py
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import datetime as dt

from .schemas import AverageWeatherResponse
from .weather import compute_average_temperature
from .cache import Cache
from .settings import settings

app = FastAPI(title="Weather Average API", version="0.1.0",
              description="Returns average temperature (°C) for the last X days for a given city.")

cors_kwargs = dict(allow_methods=["*"], allow_headers=["*"])
if settings.cors_origins == ["*"]:
    app.add_middleware(CORSMiddleware, allow_origin_regex=".*", allow_credentials=False, **cors_kwargs)
else:
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, **cors_kwargs)

cache = Cache(settings.redis_url, default_ttl=120)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/weather/average", response_model=AverageWeatherResponse,
         summary="Average temperature (°C) for last X days")
async def get_average_weather(
    city: str = Query(..., description="City name"),
    days: int = Query(..., ge=1, description="Past days (≥1)"),
    country: str | None = Query(None, min_length=2, max_length=2, description="ISO-2 country code"),
):
    # cache key includes the day your window ends (yesterday) to avoid drift
    end_iso = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    key = f"avg:v1:{(country or '').upper()}:{city.strip().lower()}:{days}:end={end_iso}"

    if cached := await cache.aget(key):
        return AverageWeatherResponse(**cached)

    try:
        canonical, avg = await compute_average_temperature(city, days, country=country)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        raise HTTPException(status_code=502, detail="Upstream weather provider error")

    payload = AverageWeatherResponse(city=canonical, days=days, average_temperature_c=avg).model_dump()
    await cache.aset(key, payload, ttl=60 * 30)  # e.g., 30 min
    return payload
