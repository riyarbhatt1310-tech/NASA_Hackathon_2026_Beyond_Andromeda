"""
Integration tests for Multi-Parameter Tile Extraction with Thermal & Mineral Data.

Validates:
1. Moon tile extraction combining LOLA DEM + Diviner Thermal.
2. Mars tile extraction combining MOLA DEM + THEMIS TIU + TES Temperature.
3. Earth tile extraction combining GLiM lithology + MODIS LST.
4. Strict enforcement of the 70% valid-coverage rule (coverage >= 0.70 -> valid; < 0.70 -> None).
5. Never treating missing measurements as zero (missing -> None).
6. Scientific metadata preservation.
"""

import pytest
import numpy as np
from pathlib import Path
from rasterio.transform import from_origin
import rasterio

from src.processing.tile_extractor import PlanetaryTileExtractor
from src.data_ingestion.moon_lola import MoonLolaReader
from src.data_ingestion.mars_mola import MarsMolaReader
from src.data_ingestion.moon_diviner import MoonDivinerReader
from src.data_ingestion.mars_thermis import MarsThermisReader
from src.data_ingestion.mars_tes_temp import MarsTesTempReader
from src.data_ingestion.earth_modis import ModisLSTReader
from src.data_ingestion.earth_glim import EarthGLiMAggregator
from src.core.config import Config


def write_test_geotiff(
    path: Path,
    data: np.ndarray,
    nodata: float = -9999.0,
    dtype: str = "float32",
    top_lat: float = 90.0,
    left_lon: float = -180.0,
    res_deg: float = 1.0,
) -> Path:
    transform = from_origin(left_lon, top_lat, res_deg, res_deg)
    h, w = data.shape
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=h,
        width=w,
        count=1,
        dtype=dtype,
        crs="EPSG:4326",
        transform=transform,
        nodata=nodata,
    ) as dst:
        dst.write(data.astype(dtype), 1)
    return path


class TestTileExtractorThermalIntegration:
    @pytest.fixture
    def real_dem_readers(self):
        """Loads real DEM readers from verified project config."""
        cfg = Config.load()
        moon_r = MoonLolaReader(cfg.get_moon_raster_path(), cfg.get_moon_label_path()).open()
        mars_r = MarsMolaReader(cfg.get_mars_raster_path(), cfg.get_mars_metadata_path()).open()
        yield moon_r, mars_r
        moon_r.close()
        mars_r.close()

    def test_moon_tile_with_valid_diviner_thermal(self, real_dem_readers, tmp_path):
        """Tests Moon tile extraction when Diviner thermal coverage exceeds 70%."""
        moon_r, mars_r = real_dem_readers

        # Global grid with valid lunar temperatures: Day ~380 K, Night ~95 K
        day_grid = np.full((180, 360), 380.0, dtype=np.float32)
        night_grid = np.full((180, 360), 95.0, dtype=np.float32)
        day_f = write_test_geotiff(tmp_path / "diviner_day.tif", day_grid)
        night_f = write_test_geotiff(tmp_path / "diviner_night.tif", night_grid)

        with MoonDivinerReader(str(day_f), str(night_f)) as diviner_r:
            extractor = PlanetaryTileExtractor(
                moon_reader=moon_r,
                mars_reader=mars_r,
                moon_diviner_reader=diviner_r,
                min_valid_coverage=0.70,
            )

            record = extractor.extract_moon_tile(lat=0.0, lon=0.0)

            # Terrain checks
            assert record["body"] == "moon"
            assert record["terrain_valid"] is True
            assert record["terrain_coverage_pct"] >= 70.0

            # Thermal checks
            assert record["thermal_valid"] is True
            assert record["thermal_coverage_pct"] >= 70.0
            assert record["thermal_t_day_k"] == pytest.approx(380.0, abs=1.0)
            assert record["thermal_t_night_k"] == pytest.approx(95.0, abs=1.0)
            assert record["thermal_delta_t_k"] == pytest.approx(285.0, abs=1.0)
            assert record["thermal_metadata"]["instrument"] == "LRO Diviner Lunar Radiometer Experiment"

    def test_moon_tile_with_insufficient_thermal_coverage_rule(self, real_dem_readers, tmp_path):
        """
        Tests strict 70% coverage rule:
        When Diviner coverage is below 70%, thermal_valid must be False,
        and temperature values must be None (NEVER 0.0!).
        """
        moon_r, mars_r = real_dem_readers

        # 80% nodata in the tile region -> only 20% valid (< 70%)
        day_grid = np.full((180, 360), -9999.0, dtype=np.float32)
        day_grid[80:100, 170:175] = 380.0  # tiny valid spot
        night_grid = day_grid.copy()

        day_f = write_test_geotiff(tmp_path / "sparse_day.tif", day_grid)
        night_f = write_test_geotiff(tmp_path / "sparse_night.tif", night_grid)

        with MoonDivinerReader(str(day_f), str(night_f)) as diviner_r:
            extractor = PlanetaryTileExtractor(
                moon_reader=moon_r,
                mars_reader=mars_r,
                moon_diviner_reader=diviner_r,
                min_valid_coverage=0.70,
            )

            record = extractor.extract_moon_tile(lat=0.0, lon=0.0)

            # Thermal must be invalid
            assert record["thermal_valid"] is False
            assert record["thermal_coverage_pct"] < 70.0
            # Zero-imputation strictly forbidden: values MUST be None
            assert record["thermal_t_day_k"] is None
            assert record["thermal_t_night_k"] is None
            assert record["thermal_delta_t_k"] is None

    def test_mars_tile_with_themis_and_tes(self, real_dem_readers, tmp_path):
        """Tests Mars tile extraction with real MOLA DEM + THEMIS TIU + TES temperatures."""
        moon_r, mars_r = real_dem_readers

        # Synthetic THEMIS TIU (300 tiu) and TES (Day 240 K, Night 175 K)
        ti_grid = np.full((180, 360), 300.0, dtype=np.float32)
        tes_d_grid = np.full((180, 360), 240.0, dtype=np.float32)
        tes_n_grid = np.full((180, 360), 175.0, dtype=np.float32)

        ti_f = write_test_geotiff(tmp_path / "themis_ti.tif", ti_grid)
        tes_d_f = write_test_geotiff(tmp_path / "tes_day.tif", tes_d_grid)
        tes_n_f = write_test_geotiff(tmp_path / "tes_night.tif", tes_n_grid)

        with MarsThermisReader(str(ti_f)) as themis_r, MarsTesTempReader(str(tes_d_f), str(tes_n_f)) as tes_r:
            extractor = PlanetaryTileExtractor(
                moon_reader=moon_r,
                mars_reader=mars_r,
                mars_thermis_reader=themis_r,
                mars_tes_reader=tes_r,
                min_valid_coverage=0.70,
            )

            record = extractor.extract_mars_tile(lat=18.65, lon=226.2)  # Olympus Mons

            assert record["body"] == "mars"
            assert record["terrain_valid"] is True
            assert record["terrain_mean_elevation_m"] > 15_000.0
            assert record["thermal_valid"] is True
            assert record["thermal_inertia_tiu"] == pytest.approx(300.0, abs=1.0)
            assert record["thermal_t_day_k"] == pytest.approx(240.0, abs=1.0)
            assert record["thermal_t_night_k"] == pytest.approx(175.0, abs=1.0)
            assert record["thermal_delta_t_k"] == pytest.approx(65.0, abs=1.0)
            assert "themis" in record["thermal_metadata"]
            assert "tes" in record["thermal_metadata"]

    def test_earth_tile_extraction(self, tmp_path):
        """Tests Earth tile extraction with GLiM lithology + MODIS LST."""
        # GLiM: 1 (Siliciclastic)
        glim_grid = np.full((180, 360), 1, dtype=np.int16)
        glim_f = write_test_geotiff(tmp_path / "glim.tif", glim_grid, nodata=-9999, dtype="int16")

        # MODIS: 14500 DN * 0.02 = 290.0 K (Day), 13500 DN * 0.02 = 270.0 K (Night)
        modis_d_grid = np.full((180, 360), 14500, dtype=np.uint16)
        modis_n_grid = np.full((180, 360), 13500, dtype=np.uint16)
        modis_d_f = write_test_geotiff(tmp_path / "modis_day.tif", modis_d_grid, nodata=0, dtype="uint16")
        modis_n_f = write_test_geotiff(tmp_path / "modis_night.tif", modis_n_grid, nodata=0, dtype="uint16")

        with EarthGLiMAggregator(str(glim_f)) as glim_r, ModisLSTReader(str(modis_d_f), str(modis_n_f)) as modis_r:
            extractor = PlanetaryTileExtractor(
                earth_glim_aggregator=glim_r,
                earth_modis_reader=modis_r,
                min_valid_coverage=0.70,
            )

            record = extractor.extract_earth_tile(lat=25.0, lon=30.0)  # Sahara desert

            assert record["body"] == "earth"
            # Mineral (GLiM)
            assert record["mineral_valid"] is True
            assert record["mineral_lithology_id"] == 1
            assert record["mineral_lithology_fraction"] == pytest.approx(1.0, abs=0.01)

            # Thermal (MODIS)
            assert record["thermal_valid"] is True
            assert record["thermal_t_day_k"] == pytest.approx(290.0, abs=1.0)
            assert record["thermal_t_night_k"] == pytest.approx(270.0, abs=1.0)
            assert record["thermal_delta_t_k"] == pytest.approx(20.0, abs=1.0)
            assert record["thermal_metadata"]["instrument"] == "MODIS Terra"
