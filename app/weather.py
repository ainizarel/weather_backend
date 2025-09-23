from __future__ import annotations
import datetime as dt
from typing import Any
from .settings import settings
import httpx   # make sure this import is here!

OPEN_METEO_GEOCODE = "https://geocoding-api.open-meteo.com/v1/search"
OPEN_METEO_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"


async def geocode_city(client: httpx.AsyncClient, city: str) -> tuple[float, float, str]:
    params = {"name": city, "count": 1}
    r = await client.get(OPEN_METEO_GEOCODE, params=params, timeout=20)
    r.raise_for_status()
    data = r.json()
    results = data.get("results") or []
    if not results:
        raise ValueError("City not found")
    top = results[0]
    return float(top["latitude"]), float(top["longitude"]), top.get("name", city)


async def fetch_daily_means(client: httpx.AsyncClient, lat: float, lon: float, days: int) -> list[float]:
    end = dt.date.today() - dt.timedelta(days=1)  # avoid partial current day
    start = end - dt.timedelta(days=days - 1)
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start.isoformat(),
        "end_date": end.isoformat(),
        # ask for all three so we can fall back if mean is null
        "daily": ["temperature_2m_mean", "temperature_2m_max", "temperature_2m_min"],
        "timezone": "auto",
    }
    r = await client.get(OPEN_METEO_ARCHIVE, params=params, timeout=30)
    r.raise_for_status()
    data: dict[str, Any] = r.json()
    daily = data.get("daily") or {}

    means = (daily.get("temperature_2m_mean") or []) or []
    tmax  = (daily.get("temperature_2m_max")  or []) or []
    tmin  = (daily.get("temperature_2m_min")  or []) or []

    temps: list[float] = []
    for i in range(max(len(means), len(tmax), len(tmin))):
        m = means[i] if i < len(means) else None
        hi = tmax[i] if i < len(tmax) else None
        lo = tmin[i] if i < len(tmin) else None

        if m is not None:
            temps.append(float(m))
        elif hi is not None and lo is not None:
            temps.append((float(hi) + float(lo)) / 2.0)
        # else: skip day (all null)

    if not temps:
        raise ValueError("No temperature data available for the given range")

    return temps


async def compute_average_temperature(city: str, days: int) -> tuple[str, float]:
    if days < 1:
        raise ValueError("days must be ≥ 1")
    if settings.max_days and settings.max_days > 0 and days > settings.max_days:
        raise ValueError(f"days must be ≤ {settings.max_days}")

    async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
        lat, lon, canonical = await geocode_city(client, city)
        temps = await fetch_daily_means(client, lat, lon, days)
    avg = sum(temps) / len(temps)
    return canonical, round(avg, 2)
