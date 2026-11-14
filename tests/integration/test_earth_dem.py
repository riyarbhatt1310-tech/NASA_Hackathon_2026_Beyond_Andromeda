"""
Tests for Milestone 8A: Global Earth DEM Ingestion.

Validates:
- EarthDemReader windowed reading and metadata integrity.
- Coordinate normalization and antimeridian wrapping.
- Scale harmonization and physical terrain geomorphometry extraction.
- Non-destruction of non-terrain catalog fields.
- Scientific safeguards (no NaNs converted to zero, minimum coverage thresholds).
"""

import json
from pathlib import Path
import numpy as np
import pytest

from src.core.constants import EARTH_VOLUMETRIC_RADIUS_M
from src.core.metrics import compute_tile_geomorphometry
from src.data_ingestion.earth_dem import EarthDemReader, EarthDemMetadata
from src.processing.earth_catalog import EarthCatalogManager
from src.processing.tile_extractor import PlanetaryTileExtractor


DEM_PATH = Path("data/raw/earth/dem/ETOPO_2022_v1_60s_N90W180_surface.tif")


@pytest.mark.skipif(not DEM_PATH.is_file(), reason="Earth DEM file not available")
class TestEarthDemReader:
    """Tests for EarthDemReader."""

    def test_metadata(self):
        reader = EarthDemReader(DEM_PATH)
        meta = reader.get_metadata()
        assert meta["doi"] == "10.25921/fd45-gt74"
        assert meta["native_res_arcsec"] == 60.0
        assert meta["native_res_km"] == pytest.approx(1.853, rel=1e-2)
        assert meta["elevation_unit"] == "METERS"
        assert meta["vertical_datum"] == "EGM2008 geoid"
        assert meta["dimensions"]["lines"] == 10800
        assert meta["dimensions"]["samples"] == 21600

    def test_windowed_read_death_valley(self):
        """Tests reading a known depression (Death Valley, CA)."""
        reader = EarthDemReader(DEM_PATH)
        with reader:
            elev_m, mask, vr = reader.read_window_pixels(
                center_lat=36.53,
                center_lon=-116.93,
                half_width_deg=0.15,
                half_height_deg=0.15,
            )
            assert vr == 1.0
            assert elev_m.shape[0] > 0 and elev_m.shape[1] > 0
            # Lowest point in Death Valley is below sea level
            assert np.nanmin(elev_m) < 0.0

    def test_longitude_normalization_wrap(self):
        """Tests that -116.93° and 242.94° (360 - 116.93 ≈ 243.07) return the same region."""
        reader = EarthDemReader(DEM_PATH)
        with reader:
            elev_neg, _, _ = reader.read_window_pixels(36.53, -116.93, 0.1, 0.1)
            elev_pos, _, _ = reader.read_window_pixels(36.53, 243.07, 0.1, 0.1)
            assert elev_neg.shape == elev_pos.shape
            # Coordinates represent the same physical area on Earth
            assert np.nanmean(elev_neg) == pytest.approx(np.nanmean(elev_pos), abs=10.0)

    def test_antimeridian_crossing(self):
        """Tests window that crosses the 180° antimeridian."""
        reader = EarthDemReader(DEM_PATH)
        with reader:
            elev_m, mask, vr = reader.read_window_pixels(
                center_lat=65.0,
                center_lon=180.0,
                half_width_deg=0.2,
                half_height_deg=0.2,
            )
            assert vr == 1.0
            assert elev_m.shape[1] > 0
            assert not np.isnan(np.nanmean(elev_m))

    def test_geomorphometry_flat_vs_mountain(self):
        """Verifies discrimination between flat playa (Salar de Uyuni) and mountains (Everest)."""
        reader = EarthDemReader(DEM_PATH)
        with reader:
            # Flat: Salar de Uyuni (-20.13, -67.49)
            elev_flat, _, _ = reader.read_window_pixels(-20.13, -67.49, 0.11, 0.11)
            metrics_flat = compute_tile_geomorphometry(
                elev_m=elev_flat,
                lat_center=-20.13,
                radius_m=EARTH_VOLUMETRIC_RADIUS_M,
                pixel_res_deg=1.0 / 60.0,
                native_res_km=1.853,
                min_valid_ratio=0.70,
            )

            # Mountain: Mt Everest (27.99, 86.93)
            elev_mtn, _, _ = reader.read_window_pixels(27.99, 86.93, 0.11, 0.11)
            metrics_mtn = compute_tile_geomorphometry(
                elev_m=elev_mtn,
                lat_center=27.99,
                radius_m=EARTH_VOLUMETRIC_RADIUS_M,
                pixel_res_deg=1.0 / 60.0,
                native_res_km=1.853,
                min_valid_ratio=0.70,
            )

            assert metrics_flat["is_valid_coverage"] is True
            assert metrics_mtn["is_valid_coverage"] is True

            # Salar de Uyuni relief is near 0; Everest relief is huge (>3000 m)
            assert metrics_flat["local_relief_m"] < 50.0
            assert metrics_flat["mean_slope_deg"] < 1.0
            assert metrics_mtn["local_relief_m"] > 2500.0
            assert metrics_mtn["mean_slope_deg"] > 10.0


@pytest.mark.skipif(not DEM_PATH.is_file(), reason="Earth DEM file not available")
class TestEarthCatalogDEMIngestion:
    """Validates Earth candidate catalog DEM ingestion."""

    def test_catalog_terrain_coverage(self):
        mgr = EarthCatalogManager()
        tiles = mgr.get_all_tiles()
        assert len(tiles) == 128

        # All tiles must now have valid terrain
        valid_count = sum(1 for t in tiles if t.get("terrain_valid"))
        assert valid_count == 128

        # Check mean coverage
        mean_cov = sum(t.get("terrain_coverage_pct", 0.0) for t in tiles) / len(tiles)
        assert mean_cov == pytest.approx(100.0, abs=1.0)

    def test_preservation_of_unrelated_fields(self):
        """Verifies that non-terrain fields are preserved accurately."""
        mgr = EarthCatalogManager()
        tiles = mgr.get_all_tiles()
        sudbury = next(t for t in tiles if "Sudbury" in t.get("tile_id", ""))

        assert sudbury["geology_valid"] is True
        assert sudbury["earth_impact_structure_present"] is True
        assert sudbury["mineral_valid"] is True
        assert sudbury["volatile_valid"] is True
        assert sudbury["terrain_valid"] is True
        assert sudbury["terrain_mean_elevation_m"] is not None
        assert sudbury["terrain_mean_slope_deg"] is not None
        assert sudbury["terrain_roughness_index_m"] is not None
        assert sudbury["effective_res_km"] == pytest.approx(1.853, abs=0.01)

    def test_tile_extractor_with_dem_reader(self):
        """Tests extracting an individual Earth tile using PlanetaryTileExtractor with EarthDemReader."""
        reader = EarthDemReader(DEM_PATH)
        extractor = PlanetaryTileExtractor(earth_dem_reader=reader)

        rec = extractor.extract_earth_tile(lat=35.03, lon=-111.02)  # Meteor Crater
        assert rec["body"] == "earth"
        assert rec["terrain_valid"] is True
        assert rec["terrain_coverage_pct"] > 70.0
        assert rec["terrain_mean_elevation_m"] is not None
        assert rec["terrain_roughness_index_m"] is not None
        assert rec["effective_res_km"] == pytest.approx(1.853, abs=0.01)
