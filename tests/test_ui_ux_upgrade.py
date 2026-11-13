"""Tests for TerraTwin Complete UI/UX Upgrade.

Verifies:
1. Cinematic Opening Intro Screen with 3D Earth Horizon canvas, brand tagline, and real telemetry elements.
2. Mode Switcher (Explore Mode vs Compare Mode) and Quick Location Search in Top Nav.
3. Two Primary Option Cards (Option 1: Explore, Option 2: Compare & Discover Analogs) on Landing View.
4. Location Overview Header Banner in Exploration Workspace with coordinates, region, and elevation.
5. All 6 Scientific Parameter Groups (including Atmospheric & Space Environment) with provenance tags.
6. JavaScript engine functions (createIntroEarthHorizon, initIntroScreen, openExploreMode, openCompareMode).
"""

from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestUIUXUpgrade:
    def test_opening_intro_screen_structure(self):
        resp = client.get("/")
        assert resp.status_code == 200
        html = resp.text

        # Intro Screen & Canvas
        assert 'id="introScreen"' in html
        assert 'id="introEarthCanvas"' in html

        # Branding & Taglines
        assert "Explore Worlds. Discover Earth's Planetary Connections." in html
        assert "NASA Space Apps 2026 // Planetary Science Initiative" in html

        # System Initialization Telemetry & Real Progress Elements
        assert 'id="introStatusPct"' in html
        assert 'id="introProgressBar"' in html
        assert 'id="introTelemWebGL"' in html
        assert 'id="introTelemTextures"' in html
        assert 'id="introTelemCatalog"' in html
        assert 'id="introTelemAPI"' in html

        # Actions
        assert 'id="btnEnterPlatform"' in html
        assert 'id="btnSkipIntro"' in html
        assert "ENTER PLATFORM // SELECT MODE" in html

    def test_top_nav_mode_switcher_and_search(self):
        resp = client.get("/")
        assert resp.status_code == 200
        html = resp.text

        # Mode Switcher
        assert "nav-mode-switcher" in html
        assert 'id="navModeExplore"' in html
        assert 'id="navModeCompare"' in html
        assert "Explore Mode" in html
        assert "Compare Analogs" in html

        # Location Search
        assert "nav-search-wrap" in html
        assert 'id="locationSearchInput"' in html
        assert 'id="locationSearchDropdown"' in html

    def test_two_primary_option_cards_on_landing_page(self):
        resp = client.get("/")
        assert resp.status_code == 200
        html = resp.text

        assert "primary-modes-container" in html
        assert "primary-modes-grid" in html

        # Option 1: Explore
        assert "mode-explore-card" in html
        assert "Planetary Explorer" in html
        assert "Discover the environmental and geological characteristics of planetary locations." in html
        assert "btn-launch-explore" in html
        assert "Launch Planetary Explorer" in html

        # Option 2: Compare & Discover Analogs
        assert "mode-compare-card" in html
        assert "Compare & Find Analogs" in html
        assert "Find places on Earth that share similar geological and environmental characteristics with locations on other worlds." in html
        assert "btn-launch-compare" in html
        assert "Launch Analog Discovery" in html

    def test_location_overview_banner_and_parameter_groups(self):
        resp = client.get("/")
        assert resp.status_code == 200
        html = resp.text

        # Location Overview Banner
        assert 'id="locationOverviewBanner"' in html
        assert 'id="overviewBodyBadge"' in html
        assert 'id="overviewLocationCoords"' in html
        assert 'id="overviewLocationRegion"' in html
        assert 'id="overviewLocationElevation"' in html
        assert 'id="btnOverviewFindAnalogs"' in html

        # 6 Parameter Groups
        assert "1. Terrain Geomorphometry" in html
        assert "2. Mineralogy & Composition" in html
        assert "3. Thermophysical Environment" in html
        assert "4. Water, Ice & Volatiles" in html
        assert "5. Geological Context" in html
        assert "6. Atmospheric & Space Environment" in html

        # Group 6 elements
        assert 'id="badgeAtmo"' in html
        assert 'id="metricAtmPressure"' in html
        assert 'id="metricAtmGas"' in html
        assert 'id="metricSolarFlux"' in html
        assert 'id="metricRadiation"' in html

    def test_globe_js_intro_earth_horizon_export(self):
        resp = client.get("/static/js/globe.js")
        assert resp.status_code == 200
        js = resp.text
        assert "createIntroEarthHorizon" in js
        assert "window.createIntroEarthHorizon" in js
        assert "earthRadius = 14.0" in js

    def test_app_js_ux_controllers(self):
        resp = client.get("/static/js/app.js")
        assert resp.status_code == 200
        js = resp.text
        assert "initIntroScreen" in js
        assert "dismissIntroScreen" in js
        assert "openExploreMode" in js
        assert "openCompareMode" in js
        assert "initLocationSearch" in js
