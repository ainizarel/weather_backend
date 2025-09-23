from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .schemas import AverageWeatherResponse
from .weather import compute_average_temperature
from .cache import Cache
from .settings import settings

app = FastAPI(
    title="Weather Average API",
    version="0.1.0",
    description="Returns average temperature (°C) for the last X days for a given city."
)

# If you ever set CORS_ORIGINS="*", you can't use allow_credentials=True.
cors_kwargs = dict(allow_methods=["*"], allow_headers=["*"])
if settings.cors_origins == ["*"]:
    # Wildcard cannot be used with credentials
    app.add_middleware(CORSMiddleware, allow_origin_regex=".*", allow_credentials=False, **cors_kwargs)
else:
    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True, **cors_kwargs)


cache = Cache(settings.redis_url, default_ttl=120)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get("/weather/average", ...)
async def get_average_weather(city: str, days: int = Query(..., ge=1), country: str | None = None):
    end_iso = (date.today() - timedelta(days=1)).isoformat()  # the window end your code uses
    key = f"avg:v1:{city.strip().lower()}:{country or ''}:{days}:end={end_iso}"

    if cached := await cache.aget(key):
        return AverageWeatherResponse(**cached)

    canonical, avg = await compute_average_temperature(city, days, country)
    payload = AverageWeatherResponse(city=canonical, days=days, average_temperature_c=avg).model_dump()

    # cache until tomorrow 02:00 UTC (or any window you like)
    await cache.aset(key, payload, ttl=60 * 30)  # 30 min example
    return payload

async def get_average_weather(
    city: str = Query(..., description="City name"),
    days: int = Query(..., ge=1, description="Past days (>=1; capped by server config)")
):
    # Enforce configurable cap (0 disables)
    if settings.max_days and settings.max_days > 0 and days > settings.max_days:
        raise HTTPException(status_code=422, detail=f"For 'days': must be ≤ {settings.max_days}.")

    key = f"avg:{city.lower()}:{days}"
    cached = await cache.aget(key)
    if cached:
        return AverageWeatherResponse(**cached)

    try:
        canonical, avg = await compute_average_temperature(city, days)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception:
        raise HTTPException(status_code=502, detail="Upstream weather provider error")

    payload = AverageWeatherResponse(city=canonical, days=days, average_temperature_c=avg).model_dump()
    await cache.aset(key, payload, ttl=120)
    return payload
