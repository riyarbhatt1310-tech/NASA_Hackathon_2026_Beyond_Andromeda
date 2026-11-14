"""FastAPI Backend Integration and Functional Tests.

Tests:
1. GET /api/health returns 200 with service status and catalog counts.
2. GET /api/targets returns curated scientific reference sites for Moon and Mars.
3. POST /api/extract extracts full 5-group tile records for Moon, Mars, and Earth.
4. POST /api/match ranks top-K global Earth analogs with 5-axis scores and radar profiles.
5. GET / serves the single-page dashboard HTML.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestTerraTwinAPI:
    def test_health_endpoint(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "planetary_bodies" in data
        assert "moon" in data["planetary_bodies"]
        assert "mars" in data["planetary_bodies"]
        assert "earth" in data["planetary_bodies"]
        assert data["earth_catalog_tiles"] > 0
        assert "disclaimer" in data

    def test_targets_endpoint(self):
        # All targets
        resp_all = client.get("/api/targets")
        assert resp_all.status_code == 200
        data_all = resp_all.json()
        assert data_all["count"] >= 8
        assert any(t["id"] == "moon_apollo11" for t in data_all["targets"])
        assert any(t["id"] == "mars_jezero" for t in data_all["targets"])

        # Filter by body
        resp_moon = client.get("/api/targets?body=moon")
        assert resp_moon.status_code == 200
        data_moon = resp_moon.json()
        assert all(t["body"] == "moon" for t in data_moon["targets"])

        resp_mars = client.get("/api/targets?body=mars")
        assert resp_mars.status_code == 200
        data_mars = resp_mars.json()
        assert all(t["body"] == "mars" for t in data_mars["targets"])

    def test_extract_endpoint(self):
        # Moon Apollo 11
        resp_moon = client.post("/api/extract", json={"body": "moon", "lat": 0.67, "lon": 23.47})
        assert resp_moon.status_code == 200
        tile_moon = resp_moon.json()["tile"]
        assert tile_moon["body"] == "moon"
        assert tile_moon["terrain_valid"] is True
        assert tile_moon["volatile_valid"] is True
        assert tile_moon["geology_valid"] is True

        # Mars Jezero
        resp_mars = client.post("/api/extract", json={"body": "mars", "lat": 18.38, "lon": 77.58})
        assert resp_mars.status_code == 200
        tile_mars = resp_mars.json()["tile"]
        assert tile_mars["body"] == "mars"
        assert tile_mars["terrain_valid"] is True
        assert tile_mars["volatile_valid"] is True

        # Earth Sudbury
        resp_earth = client.post("/api/extract", json={"body": "earth", "lat": 46.60, "lon": -81.18})
        assert resp_earth.status_code == 200
        tile_earth = resp_earth.json()["tile"]
        assert tile_earth["body"] == "earth"
        assert tile_earth["earth_impact_structure_present"] is True

        # Invalid body
        resp_invalid = client.post("/api/extract", json={"body": "jupiter", "lat": 0.0, "lon": 0.0})
        assert resp_invalid.status_code == 400

    def test_match_endpoint_moon(self):
        req = {
            "body": "moon",
            "lat": 0.67,
            "lon": 23.47,
            "weights": {
                "terrain": 25.0,
                "mineral": 20.0,
                "thermal": 20.0,
                "water": 15.0,
                "geology": 20.0
            },
            "top_k": 3,
            "min_coverage": 0.30
        }
        resp = client.post("/api/match", json=req)
        assert resp.status_code == 200
        data = resp.json()

        assert "target" in data
        assert data["target"]["body"] == "moon"
        assert "ranked_analogs" in data
        assert len(data["ranked_analogs"]) == 3

        top = data["ranked_analogs"][0]
        assert top["rank"] == 1
        assert 0.0 <= top["composite_similarity_pct"] <= 100.0
        assert "is_qualified_match" in top
        assert "coverage_status" in top
        assert "valid_groups_summary" in top
        assert "composite_coverage_pct" in top
        assert "radar_profile" in top
        assert len(top["radar_profile"]["axes"]) == 5
        assert len(top["radar_profile"]["values"]) == 5
        assert "scientific_rationale" in top
        assert "effective_resolutions_km" in top
        assert "disclaimer" in data
        assert "effective_weights_pct" in data["query_parameters"]

    def test_match_endpoint_safeguards_and_coverage(self):
        # 1. Reject invalid min_coverage (< 0.20) via validation error
        resp_invalid_cov = client.post("/api/match", json={
            "body": "mars",
            "lat": 18.38,
            "lon": 77.58,
            "min_coverage": 0.05  # below 0.20 safeguard
        })
        assert resp_invalid_cov.status_code == 422

        # 2. Check Jezero matching transparency with default 60% threshold
        resp_jezero = client.post("/api/match", json={
            "body": "mars",
            "lat": 18.38,
            "lon": 77.58,
            "top_k": 3,
            "min_coverage": 0.60
        })
        assert resp_jezero.status_code == 200
        data_jezero = resp_jezero.json()
        assert len(data_jezero["ranked_analogs"]) > 0
        top = data_jezero["ranked_analogs"][0]
        assert "valid_groups_summary" in top
        assert "composite_coverage_pct" in top
        # Radar profile must have None for unobserved groups, never 0.0
        assert None in top["radar_profile"]["values"]

    def test_match_endpoint_mars(self):
        req = {
            "body": "mars",
            "lat": 18.38,
            "lon": 77.58,
            "top_k": 5,
            "min_coverage": 0.50
        }
        resp = client.post("/api/match", json=req)
        assert resp.status_code == 200
        data = resp.json()

        assert data["target"]["body"] == "mars"
        assert len(data["ranked_analogs"]) > 0

        # Check descending similarity ordering
        scores = [a["composite_similarity_pct"] for a in data["ranked_analogs"]]
        assert scores == sorted(scores, reverse=True)

    def test_dashboard_html_served(self):
        resp = client.get("/")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "TerraTwin" in resp.text
        assert "NASA Space Apps 2026" in resp.text
