"""
Unit Tests for TerraTwin Geomorphometry, Spatial Grids, and Planetary Tile Extractor.

Tests:
1. PlanetaryGrid equal-physical-area logic and latitude-dependent scaling.
2. Horn spherical slope metric calculations and analytical invariance.
3. Terrain Roughness Index (TRI), local relief, hypsometric integral, and skewness.
4. End-to-end tile extraction on the REAL downloaded Moon LOLA and Mars MOLA datasets!
"""

import math
import pytest
import numpy as np

from src.core.constants import (
    MOON_REFERENCE_RADIUS_M,
    MARS_REFERENCE_RADIUS_M,
    EARTH_VOLUMETRIC_RADIUS_M,
    ANALYSIS_TILE_SIZE_KM,
)
from src.core.config import Config
from src.core.grids import PlanetaryGrid, PlanetaryTile
from src.core.metrics import (
    compute_spherical_slope_horn,
    compute_terrain_roughness_index,
    compute_tile_geomorphometry,
)
from src.data_ingestion.moon_lola import MoonLolaReader
from src.data_ingestion.mars_mola import MarsMolaReader
from src.processing.tile_extractor import PlanetaryTileExtractor


# ---------------------------------------------------------------------------
# 1. Planetary Grid Tests
# ---------------------------------------------------------------------------

class TestPlanetaryGrid:
    def test_grid_initialization_all_bodies(self):
        grid_earth = PlanetaryGrid("earth", target_tile_size_km=25.0)
        grid_moon = PlanetaryGrid("moon", target_tile_size_km=25.0)
        grid_mars = PlanetaryGrid("mars", target_tile_size_km=25.0)

        assert grid_earth.radius_km == pytest.approx(6371.0, abs=1.0)
        assert grid_moon.radius_km == pytest.approx(1737.4, abs=1.0)
        assert grid_mars.radius_km == pytest.approx(3396.2, abs=1.0)

    def test_tile_area_conservation(self):
        """Verify that analysis tiles on Moon, Mars, and Earth maintain ~625 km^2 physical area."""
        for body in ["moon", "mars", "earth"]:
            grid = PlanetaryGrid(body, target_tile_size_km=25.0)
            target_area = 25.0 * 25.0  # 625 km^2

            # Test equatorial and mid-latitude tiles
            for test_lat in [0.0, 30.0, -45.0, 70.0]:
                tile = grid.get_tile_for_coord(lat=test_lat, lon=45.0)
                # Physical area should be within 25% of target 625 km^2 despite discrete rounding
                assert pytest.approx(tile.actual_area_km2, rel=0.30) == target_area

    def test_polar_latitude_bounds(self):
        """Verify safe handling at extreme poles without zero-division."""
        grid = PlanetaryGrid("moon", target_tile_size_km=25.0)
        tile_np = grid.get_tile_for_coord(lat=89.9, lon=0.0)
        tile_sp = grid.get_tile_for_coord(lat=-89.9, lon=180.0)

        assert tile_np.lat_max == 90.0
        assert tile_sp.lat_min == -90.0
        assert tile_np.actual_area_km2 > 0


# ---------------------------------------------------------------------------
# 2. Geomorphometric Derivative Tests
# ---------------------------------------------------------------------------

class TestGeomorphometryMetrics:
    def test_flat_plane_slope_and_roughness(self):
        """A flat horizontal surface must have 0.0 deg slope and 0.0 m roughness."""
        flat = np.full((15, 15), 1000.0, dtype=np.float32)
        slope = compute_spherical_slope_horn(
            elev_grid=flat,
            lat_deg=0.0,
            radius_m=MOON_REFERENCE_RADIUS_M,
            pixel_dlat_deg=1.0 / 16.0,
            pixel_dlon_deg=1.0 / 16.0,
        )
        tri = compute_terrain_roughness_index(flat)

        assert np.nanmean(slope) == pytest.approx(0.0, abs=1e-5)
        assert np.nanmean(tri) == pytest.approx(0.0, abs=1e-5)

    def test_tilted_plane_analytical_slope(self):
        """
        Creates an analytical ramp with known physical slope:
        dz = 100 m per pixel.
        Physical pixel size dy = R * dphi.
        Analytical slope = arctan(dz / dy).
        """
        R = 1_737_400.0  # Moon radius in meters
        dlat_deg = 1.0 / 16.0
        dy = R * math.radians(dlat_deg)  # ~1895.2 m

        # Ramp increasing along latitude (rows)
        ramp = np.zeros((21, 21), dtype=np.float32)
        target_slope_deg = 10.0  # 10 degrees slope
        dz_per_pixel = dy * math.tan(math.radians(target_slope_deg))

        for r in range(21):
            ramp[r, :] = r * dz_per_pixel

        calculated_slope = compute_spherical_slope_horn(
            elev_grid=ramp,
            lat_deg=0.0,
            radius_m=R,
            pixel_dlat_deg=dlat_deg,
            pixel_dlon_deg=dlat_deg,
        )

        interior_slope = calculated_slope[2:-2, 2:-2]
        assert np.nanmean(interior_slope) == pytest.approx(target_slope_deg, abs=0.1)

    def test_latitude_metric_slope_scaling(self):
        """
        On a sphere, longitudinal physical distance shrinks with cos(lat).
        Therefore, an identical longitudinal elevation difference produces
        a STEEPER physical slope at high latitude (e.g. 60 deg) than at equator (0 deg).
        """
        R = 3_396_190.0  # Mars radius
        dlon_deg = 1.0 / 16.0

        # Ramp along columns (longitude)
        ramp_lon = np.zeros((15, 15), dtype=np.float32)
        for c in range(15):
            ramp_lon[:, c] = c * 50.0  # 50 m per pixel

        slope_eq = compute_spherical_slope_horn(
            elev_grid=ramp_lon, lat_deg=0.0, radius_m=R,
            pixel_dlat_deg=dlon_deg, pixel_dlon_deg=dlon_deg,
        )
        slope_60 = compute_spherical_slope_horn(
            elev_grid=ramp_lon, lat_deg=60.0, radius_m=R,
            pixel_dlat_deg=dlon_deg, pixel_dlon_deg=dlon_deg,
        )

        mean_slope_eq = np.nanmean(slope_eq[2:-2, 2:-2])
        mean_slope_60 = np.nanmean(slope_60[2:-2, 2:-2])

        # At 60 deg, cos(60) = 0.5, dx is half as wide, so slope must be roughly double
        assert mean_slope_60 > mean_slope_eq
        assert pytest.approx(math.tan(math.radians(mean_slope_60)), rel=0.1) == 2.0 * math.tan(math.radians(mean_slope_eq))

    def test_tile_geomorphometry_statistical_metrics(self):
        """Tests relief, standard deviation, and hypsometric integral."""
        grid = np.array([
            [100, 110, 120, 130],
            [105, 115, 125, 135],
            [110, 120, 130, 140],
            [115, 125, 135, 150],
        ], dtype=np.float32)

        res = compute_tile_geomorphometry(
            elev_m=grid,
            lat_center=0.0,
            radius_m=MOON_REFERENCE_RADIUS_M,
            min_valid_ratio=0.70,
        )

        assert res["local_relief_m"] == 50.0  # 150 - 100
        assert res["mean_elevation_m"] == pytest.approx(np.mean(grid), abs=0.1)
        assert 0.0 <= res["hypsometric_integral"] <= 1.0


# ---------------------------------------------------------------------------
# 3. Real Planetary Datasets Tile Extraction Tests (Real Moon & Mars Data!)
# ---------------------------------------------------------------------------

class TestRealPlanetaryTileExtraction:
    @pytest.fixture(scope="class")
    def extractor(self):
        cfg = Config.load()
        moon_r = MoonLolaReader(cfg.get_moon_raster_path(), cfg.get_moon_label_path()).open()
        mars_r = MarsMolaReader(cfg.get_mars_raster_path(), cfg.get_mars_metadata_path()).open()
        extractor = PlanetaryTileExtractor(moon_reader=moon_r, mars_reader=mars_r)
        yield extractor
        moon_r.close()
        mars_r.close()

    def test_real_moon_south_pole_shackleton(self, extractor):
        """
        Tests extraction at Moon South Pole near Shackleton crater (-89.9° N, 0.0° E).
        Should show rugged terrain, high relief, and valid coverage.
        """
        record = extractor.extract_moon_tile(lat=-89.5, lon=0.0)
        assert record["body"] == "moon"
        assert record["terrain_valid"] is True
        assert record["terrain_coverage_pct"] >= 70.0
        assert record["terrain_local_relief_m"] > 500.0  # Rugged polar crater walls
        assert record["terrain_mean_slope_deg"] > 3.0
        assert record["sample_count"] > 10
        assert record["effective_res_km"] == pytest.approx(1.895, abs=0.01)

    def test_real_moon_oceanus_procellarum(self, extractor):
        """
        Tests extraction at Oceanus Procellarum basaltic mare (20.0° N, 300.0° E).
        Should show smoother terrain with lower slopes than the polar highlands.
        """
        record = extractor.extract_moon_tile(lat=20.0, lon=300.0)
        assert record["body"] == "moon"
        assert record["terrain_valid"] is True
        assert record["terrain_mean_slope_deg"] < 10.0  # Basaltic plain is relatively smooth

    def test_real_mars_olympus_mons(self, extractor):
        """
        Tests extraction at Olympus Mons (18.65° N, 226.2° E).
        Highest volcano in Solar System: elevation should exceed 15,000 m.
        """
        record = extractor.extract_mars_tile(lat=18.65, lon=226.2)
        assert record["body"] == "mars"
        assert record["terrain_valid"] is True
        assert record["terrain_mean_elevation_m"] > 15_000.0  # Gigantic volcano
        assert record["terrain_local_relief_m"] > 500.0
        assert record["effective_res_km"] == pytest.approx(3.704, abs=0.01)

    def test_real_mars_jezero_crater(self, extractor):
        """
        Tests extraction at Jezero crater (18.38° N, 77.58° E, Perseverance landing site).
        Should have valid coverage and realistic Martian elevation.
        """
        record = extractor.extract_mars_tile(lat=18.38, lon=77.58)
        assert record["body"] == "mars"
        assert record["terrain_valid"] is True
        assert -4000.0 < record["terrain_mean_elevation_m"] < 0.0  # Isidis basin rim/floor
        assert record["terrain_local_relief_m"] > 100.0

    def test_real_mars_hellas_basin(self, extractor):
        """
        Tests extraction at Hellas Planitia (-42.4° N, 70.5° E).
        Deepest impact basin on Mars: elevation should be well below -5000 m.
        """
        record = extractor.extract_mars_tile(lat=-42.4, lon=70.5)
        assert record["body"] == "mars"
        assert record["terrain_valid"] is True
        assert record["terrain_mean_elevation_m"] < -5_000.0
