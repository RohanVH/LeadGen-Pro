"""Lightweight API smoke tests (no external API keys required for core paths)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json().get("status") == "ok"


def test_locations_autocomplete_returns_place_ids() -> None:
    client = TestClient(app)
    response = client.get("/locations/autocomplete", params={"q": "Mel", "country": "Australia"})
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert len(data["suggestions"]) >= 1
    for item in data["suggestions"]:
        assert "placeId" in item and item["placeId"]


def test_locations_popular_returns_suggestions() -> None:
    client = TestClient(app)
    response = client.get("/locations/popular", params={"country": "Australia"})
    assert response.status_code == 200
    data = response.json()
    assert "suggestions" in data
    assert len(data["suggestions"]) >= 1
    assert data["suggestions"][0]["secondaryText"] == "Australia"


def test_locations_details_supports_seed_place_ids() -> None:
    client = TestClient(app)
    response = client.get("/locations/details", params={"placeId": "seed:Australia:Melbourne"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["city"] == "Melbourne"
    assert payload["country"] == "Australia"
    assert payload["placeId"]
    assert "displayName" in payload


def test_lead_analyze_schema_accepts_camel_case() -> None:
    client = TestClient(app)
    body = {
        "name": "Smoke Test Co",
        "businessType": "cafe",
        "reviews": [],
    }
    response = client.post("/v1/lead/analyze", json=body)
    assert response.status_code == 200
    payload = response.json()
    assert "overview" in payload
    assert "whatToSell" in payload
