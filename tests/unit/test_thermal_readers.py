"""
Unit tests for Thermal Data Readers and Aggregators.

Uses isolated synthetic GeoTIFF fixtures to test:
1. MoonDivinerReader (day/night Kelvin, masks, metadata)
2. MarsThermisReader (thermal inertia tiu, masks, metadata)
3. MarsTesTempReader (TES bolometric day/night, valid range, metadata)
4. ModisLSTReader (scale factor 0.02, QC masks, day/night, metadata)
5. EarthGLiMAggregator (categorical mode and fraction)
"""

import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin
from pathlib import Path

from src.data_ingestion.moon_diviner import MoonDivinerReader
from src.data_ingestion.mars_thermis import MarsThermisReader
from src.data_ingestion.mars_tes_temp import MarsTesTempReader
from src.data_ingestion.earth_modis import ModisLSTReader
from src.data_ingestion.earth_glim import EarthGLiMAggregator


def create_synthetic_geotiff(
    path: Path,
    data: np.ndarray,
    nodata: float = -9999.0,
    dtype: str = "float32",
    top_lat: float = 10.0,
    left_lon: float = 0.0,
    res_deg: float = 1.0,
) -> Path:
    """Helper to create a small georeferenced GeoTIFF fixture."""
    transform = from_origin(left_lon, top_lat, res_deg, res_deg)
    height, width = data.shape
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=1,
        dtype=dtype,
        crs="EPSG:4326",
        transform=transform,
        nodata=nodata,
    ) as dst:
        dst.write(data.astype(dtype), 1)
    return path


class TestThermalReaders:
    def test_moon_diviner_reader_synthetic(self, tmp_path):
        """Tests MoonDivinerReader with synthetic day/night GeoTIFFs."""
        day_grid = np.array([
            [380.0, 385.0, 390.0],
            [375.0, 380.0, -9999.0],  # 1 nodata
            [370.0, 375.0, 380.0],
        ], dtype=np.float32)

        night_grid = np.array([
            [95.0, 96.0, 98.0],
            [92.0, 94.0, 95.0],
            [90.0, 91.0, 93.0],
        ], dtype=np.float32)

        day_file = create_synthetic_geotiff(tmp_path / "diviner_day.tif", day_grid)
        night_file = create_synthetic_geotiff(tmp_path / "diviner_night.tif", night_grid)

        with MoonDivinerReader(str(day_file), str(night_file)) as reader:
            (day_d, day_m), (night_d, night_m), cov = reader.read_window_pixels(
                center_lat=8.5, center_lon=1.5, half_width_deg=1.0, half_height_deg=1.0
            )
            meta = reader.get_metadata()

            assert meta["instrument"] == "LRO Diviner Lunar Radiometer Experiment"
            assert meta["temperature_unit"] == "Kelvin (K)"
            assert cov > 0.70
            assert np.nanmean(day_d[day_m]) > 350.0
            assert np.nanmean(night_d[night_m]) < 110.0

    def test_mars_thermis_reader_synthetic(self, tmp_path):
        """Tests MarsThermisReader with synthetic thermal inertia GeoTIFF."""
        tiu_grid = np.array([
            [250.0, 300.0, 350.0],
            [280.0, 310.0, 320.0],
            [260.0, 290.0, -9999.0],
        ], dtype=np.float32)

        ti_file = create_synthetic_geotiff(tmp_path / "themis_ti.tif", tiu_grid)

        with MarsThermisReader(str(ti_file)) as reader:
            data, mask, cov = reader.read_window_pixels(
                center_lat=8.5, center_lon=1.5, half_width_deg=1.0, half_height_deg=1.0
            )
            meta = reader.get_metadata()

            assert meta["parameter"] == "Thermal Inertia"
            assert meta["unit"] == "J m^-2 K^-1 s^-1/2 (tiu)"
            assert cov >= 0.70
            assert 250.0 <= np.mean(data[mask]) <= 350.0

    def test_mars_tes_reader_synthetic(self, tmp_path):
        """Tests MarsTesTempReader with synthetic day/night temperature files."""
        day_grid = np.array([
            [240.0, 245.0, 250.0],
            [235.0, 240.0, 245.0],
            [230.0, 235.0, 240.0],
        ], dtype=np.float32)

        night_grid = np.array([
            [170.0, 175.0, 180.0],
            [165.0, 170.0, 175.0],
            [160.0, 165.0, 170.0],
        ], dtype=np.float32)

        day_file = create_synthetic_geotiff(tmp_path / "tes_day.tif", day_grid)
        night_file = create_synthetic_geotiff(tmp_path / "tes_night.tif", night_grid)

        with MarsTesTempReader(str(day_file), str(night_file)) as reader:
            (d_data, d_mask), (n_data, n_mask), cov = reader.read_window_pixels(
                center_lat=8.5, center_lon=1.5, half_width_deg=1.0, half_height_deg=1.0
            )
            meta = reader.get_metadata()

            assert meta["instrument"] == "MGS Thermal Emission Spectrometer (TES)"
            assert meta["day_nominal_lst"] == "14:00 (2 PM local solar time)"
            assert cov == 1.0
            assert 230.0 <= np.mean(d_data[d_mask]) <= 250.0
            assert 160.0 <= np.mean(n_data[n_mask]) <= 180.0

    def test_earth_modis_reader_synthetic(self, tmp_path):
        """Tests ModisLSTReader with DN scale factor 0.02 and QC mask."""
        # 300 K / 0.02 = 15000 DN
        day_dn = np.array([
            [15000, 15100, 15200],
            [14900, 15000, 0],      # 0 is nodata
            [14800, 15000, 15100],
        ], dtype=np.uint16)

        night_dn = np.array([
            [14000, 14050, 14100],
            [13950, 14000, 14050],
            [13900, 13950, 14000],
        ], dtype=np.uint16)

        day_file = create_synthetic_geotiff(tmp_path / "modis_day.tif", day_dn, nodata=0, dtype="uint16")
        night_file = create_synthetic_geotiff(tmp_path / "modis_night.tif", night_dn, nodata=0, dtype="uint16")

        with ModisLSTReader(str(day_file), str(night_file), is_scaled_dn=True) as reader:
            (d_data, d_mask), (n_data, n_mask), cov = reader.read_window_pixels(
                center_lat=8.5, center_lon=1.5, half_width_deg=1.0, half_height_deg=1.0
            )
            meta = reader.get_metadata()

            assert meta["instrument"] == "MODIS Terra"
            assert meta["scale_factor"] == 0.02
            assert cov > 0.70
            mean_day_k = float(np.mean(d_data[d_mask]))
            mean_night_k = float(np.mean(n_data[n_mask]))
            # 15000 * 0.02 = 300.0 K
            assert pytest.approx(mean_day_k, abs=5.0) == 300.0
            # 14000 * 0.02 = 280.0 K
            assert pytest.approx(mean_night_k, abs=5.0) == 280.0
            assert mean_day_k > mean_night_k

    def test_earth_glim_aggregator_synthetic(self, tmp_path):
        """Tests EarthGLiMAggregator categorical mode and fraction."""
        # 1: Siliciclastic (6 pixels), 2: Carbonate (2 pixels), -9999: nodata (1 pixel)
        glim_grid = np.array([
            [1, 1, 1],
            [1, 1, 2],
            [1, 2, -9999],
        ], dtype=np.int16)

        glim_file = create_synthetic_geotiff(tmp_path / "glim.tif", glim_grid, nodata=-9999, dtype="int16")

        with EarthGLiMAggregator(str(glim_file)) as aggregator:
            mode_id, fraction = aggregator.aggregate_mode(
                center_lat=8.5, center_lon=1.5, half_width_deg=1.5, half_height_deg=1.5
            )
            assert mode_id == 1
            # 6 valid pixels of class 1 out of 8 non-nodata pixels = 6/8 = 0.75
            assert fraction == pytest.approx(0.75, abs=0.01)
