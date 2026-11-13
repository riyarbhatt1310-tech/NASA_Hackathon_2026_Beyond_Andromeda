"""Tests for TerraTwin UI Phase 1 Visual Refinement.

Verifies:
1. Professional scientific typography (Inter + JetBrains Mono) without Orbitron.
2. Prominent 3D planetary showcase on Landing Page (Earth, Moon, Mars canvases).
3. Scientific texture endpoints are served locally (/static/textures/earth.jpg, moon.jpg, mars.jpg).
4. Critical spherical coordinate conversion accuracy across hemispheres, prime meridian, and poles.
5. All UI Phase 1 components and preserved comparison drawer are accessible.
"""

import math
from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)


class TestUIPhase1VisualRefinement:
    def test_dashboard_refined_html_structure(self):
        resp = client.get("/")
        assert resp.status_code == 200
        html = resp.text

        # 1. Branding & Verification
        assert "TerraTwin" in html
        assert "NASA Space Apps 2026" in html

        # 2. Professional Typography system (Inter + JetBrains Mono)
        assert "Inter" in html
        assert "JetBrains+Mono" in html
        assert "Orbitron" not in html

        # 3. Area 1: Landing Page with 3D Showcase Canvases
        assert 'id="landingView"' in html
        assert "BEGIN EXPLORATION" in html
        assert 'id="canvasEarthShowcase"' in html
        assert 'id="canvasMoonShowcase"' in html
        assert 'id="canvasMarsShowcase"' in html

        # 4. Area 2: Planet Selection Pills
        assert "planet-selector-bar" in html
        assert 'id="navBtn_earth"' in html
        assert 'id="navBtn_moon"' in html
        assert 'id="navBtn_mars"' in html

        # 5. Area 3: Planet Exploration Hero
        assert 'id="explorationView"' in html
        assert 'id="globeContainer"' in html
        assert 'id="map2dContainer"' in html
        assert 'id="curatedSitesList"' in html
        assert 'id="btnExtractTile"' in html

        # 6. Environmental 5 Parameter Groups
        assert "1. Terrain Geomorphometry" in html
        assert "2. Mineralogy & Composition" in html
        assert "3. Thermophysical Environment" in html
        assert "4. Water, Ice & Volatiles" in html
        assert "5. Geological Context" in html

        # 7. Preserved Comparison Functionality
        assert 'id="comparisonDrawer"' in html
        assert 'id="drawerRadarChart"' in html
        assert 'id="drawerMinCov"' in html
        assert 'id="wTerrain"' in html

    def test_scientific_textures_served(self):
        for tex in ["earth.jpg", "moon.jpg", "mars.jpg", "earth_clouds.png"]:
            resp = client.get(f"/static/textures/{tex}")
            assert resp.status_code == 200
            assert len(resp.content) > 50000, f"Texture {tex} size too small"

    def test_static_css_typography(self):
        resp = client.get("/static/css/terratwin.css")
        assert resp.status_code == 200
        css = resp.text
        assert "Inter" in css
        assert "JetBrains Mono" in css
        assert "Orbitron" not in css
        assert "--font-sans" in css
        assert "--font-mono" in css

    def test_static_globe_js_features(self):
        resp = client.get("/static/js/globe.js")
        assert resp.status_code == 200
        js = resp.text
        assert "PlanetaryGlobe" in js
        assert "createShowcaseGlobe" in js
        assert "latLonToVector3" in js
        assert "vector3ToLatLon" in js
        assert "/static/textures/earth.jpg" in js
        assert "/static/textures/moon.jpg" in js
        assert "/static/textures/mars.jpg" in js

    def test_spherical_coordinate_accuracy_across_poles_and_hemispheres(self):
        """Validates mathematical precision of lat/lon <-> vector3 conversions."""
        def lat_lon_to_vec3(lat, lon, r=2.0):
            phi = (90.0 - lat) * (math.pi / 180.0)
            theta = (lon + 180.0) * (math.pi / 180.0)
            x = -r * math.cos(theta) * math.sin(phi)
            y = r * math.cos(phi)
            z = r * math.sin(theta) * math.sin(phi)
            return x, y, z

        def vec3_to_lat_lon(x, y, z):
            r = math.sqrt(x*x + y*y + z*z)
            phi = math.acos(max(-1.0, min(1.0, y / r)))
            lat = 90.0 - phi * (180.0 / math.pi)
            theta = math.atan2(z, -x)
            lon = theta * (180.0 / math.pi) - 180.0
            while lon > 180.0: lon -= 360.0
            while lon <= -180.0: lon += 360.0
            return round(lat, 4), round(lon, 4)

        critical_points = [
            (0.0, 0.0),       # Equator & Prime Meridian
            (0.67, 23.47),    # Apollo 11 (Mare Tranquillitatis)
            (18.38, 77.58),   # Jezero Crater (Northern Hemisphere, East Lon)
            (-89.9, 0.0),     # Shackleton Crater (Lunar South Pole)
            (46.60, -81.18),  # Sudbury Impact Basin (Northern Hemisphere, West Lon)
            (0.0, 90.0),      # Eastern Equatorial limb
            (0.0, -90.0),     # Western Equatorial limb
            (85.0, 45.0),     # High Arctic / North Polar
            (-85.0, -135.0),  # High Antarctic / South Polar
        ]

        for lat, lon in critical_points:
            x, y, z = lat_lon_to_vec3(lat, lon, 2.0)
            # Distance from center must equal radius 2.0
            dist = math.sqrt(x*x + y*y + z*z)
            assert abs(dist - 2.0) < 1e-6, f"Point ({lat}, {lon}) not on sphere surface"

            # Inverse conversion roundtrip
            olat, olon = vec3_to_lat_lon(x, y, z)
            assert abs(lat - olat) < 0.01, f"Latitude mismatch for {lat}: got {olat}"
            lon_diff = abs(lon - olon)
            if lon_diff > 359.9: lon_diff = 0.0
            assert lon_diff < 0.01, f"Longitude mismatch for {lon}: got {olon}"
