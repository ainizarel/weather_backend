# tests/test_api.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_days_min_validation():
    # ge=1 triggers 422 for 0 or negatives
    r = client.get("/weather/average", params={"city": "Tokyo", "days": 0})
    assert r.status_code == 422

def test_days_78_is_ok_when_no_cap():
    r = client.get("/weather/average", params={"city": "Tokyo", "days": 78})
    assert r.status_code == 200
