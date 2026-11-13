"""Tests for TerraTwin Phase 2: Planetary Visibility Fix & Comparison Dashboard Redesign.

Verifies:
1. Part A: Planetary visibility lighting configuration (HemisphereLight, ACES tone mapping exposure, fill lighting).
2. Part B: Redesigned 3-Column Comparison Research Console DOM structure and elements.
3. Verification of all 5 parameter groups and missing-data preservation in comparison console.
4. Preserved endpoints, safeguards, and weight controls.
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestPhase2Implementation:
    def test_globe_visibility_lighting_configuration(self):
        resp = client.get("/static/js/globe.js")
        assert resp.status_code == 200
        js = resp.text

        # Verify Part A lighting improvements
        assert "HemisphereLight" in js
        assert "toneMappingExposure = 1.35" in js
        assert "THREE.sRGBEncoding" in js
        assert "sunLight" in js
        assert "fillLight" in js
        assert "createShowcaseGlobe" in js
        assert "1.45" in js  # Showcase exposure

    def test_comparison_research_console_structure(self):
        resp = client.get("/")
        assert resp.status_code == 200
        html = resp.text

        # 1. Branding & Navigation
        assert "TerraTwin" in html
        assert "NASA Space Apps 2026" in html
        assert "btnHeaderCompare" in html

        # 2. Part B: Comparison Console Layout
        assert 'id="comparisonDrawer"' in html
        assert "console-top-bar" in html
        assert 'id="consoleTargetBodyBadge"' in html
        assert 'id="consoleTargetName"' in html
        assert 'id="consoleTargetCoords"' in html
        assert 'id="consoleTargetResolutions"' in html

        # 3. 3-Column Grid Elements
        assert "console-workspace-grid" in html
        assert "console-col-config" in html
        assert "console-col-rankings" in html
        assert "console-col-inspection" in html

        # 4. Target Coverage & Controls
        assert 'id="consoleObsCount"' in html
        assert 'id="consoleTargetGroupPills"' in html
        assert 'id="wTerrain"' in html
        assert 'id="wMineral"' in html
        assert 'id="wThermal"' in html
        assert 'id="wWater"' in html
        assert 'id="wGeology"' in html
        assert 'id="drawerMinCov"' in html
        assert 'id="btnRunMatchInDrawer"' in html

        # 5. Rankings & Candidate Deep Inspection
        assert 'id="drawerAnalogsList"' in html
        assert 'id="drawerRadarChart"' in html
        assert 'id="drawerRadarPills"' in html
        assert 'id="candidateGroupsMatrix"' in html
        assert 'id="earthMap"' in html

    def test_comparison_api_integration_and_qualification(self):
        # Match Apollo 11 against Earth catalog
        req = {
            "body": "moon",
            "lat": 0.67,
            "lon": 23.47,
            "weights": {"terrain": 25, "mineral": 20, "thermal": 20, "water": 15, "geology": 20},
            "top_k": 5,
            "min_coverage": 0.60
        }
        resp = client.post("/api/match", json=req)
        assert resp.status_code == 200
        data = resp.json()

        assert "ranked_analogs" in data
        assert len(data["ranked_analogs"]) == 5

        # Check qualification status and missing data handling
        top = data["ranked_analogs"][0]
        assert "is_qualified_match" in top
        assert "composite_coverage_pct" in top
        assert "valid_groups_summary" in top
        assert "parameter_scores" in top
        assert "radar_profile" in top

        # Unobserved groups must have None in values, never 0.0
        assert None in top["radar_profile"]["values"]
        assert len(top["radar_profile"]["axes"]) == 5
