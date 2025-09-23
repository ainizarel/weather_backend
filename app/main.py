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

# Build CORS config
cors_common = dict(allow_methods=["*"], allow_headers=["*"])
allow_all = settings.cors_origins == ["*"] or "*" in settings.cors_origins

if allow_all:
    # If you allow everyone, credentials MUST be False
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=".*",
        allow_credentials=False,
        **cors_common,
    )
else:
    # Exact origins from env + any *.vercel.app preview
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_origin_regex=r"https://.*\.vercel\.app$",
        allow_credentials=True,
        **cors_common,
    )

cache = Cache(settings.redis_url, default_ttl=120)

@app.get("/healthz")
async def healthz():
    return {"status": "ok"}

@app.get(
    "/weather/average",
    response_model=AverageWeatherResponse,
    summary="Average temperature (°C) for last X days"
)
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
