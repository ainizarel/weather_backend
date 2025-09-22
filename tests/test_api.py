
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"

def test_days_validation():
    r = client.get("/weather/average", params={"city": "Tokyo", "days": 0})
    assert r.status_code == 422  # FastAPI validation enforces ge=1

