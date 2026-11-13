"""
Isolated Unit Tests for TerraTwin Planetary Binary Readers and Configuration.

Ensures:
- Exact dimensions (2880 x 5760)
- Correct byte orders (Moon: float32 LE, Mars: int16 SignedMSB2 BE)
- Strict nodata masking (never treated as 0.0)
- Coordinate transformations (lat/lon to row/col)
- Configurable file paths and environment variable overrides
"""

import os
import struct
from pathlib import Path
import pytest
import numpy as np

from src.core.constants import (
    MOON_RASTER_LINES,
    MOON_RASTER_SAMPLES,
    MARS_RASTER_LINES,
    MARS_RASTER_SAMPLES,
    MOON_NODATA_THRESHOLD,
    MARS_NODATA_VALUE,
    MOON_REFERENCE_RADIUS_M,
    MARS_REFERENCE_RADIUS_M,
)
from src.core.config import Config
from src.data_ingestion.moon_lola import MoonLolaReader, MoonLolaMetadata
from src.data_ingestion.mars_mola import MarsMolaReader, MarsMolaMetadata


# ---------------------------------------------------------------------------
# Fixtures for isolated synthetic test rasters (strictly within tmp_path)
# ---------------------------------------------------------------------------

@pytest.fixture
def isolated_moon_raster(tmp_path):
    """
    Creates an isolated minimal Moon binary fixture for unit testing.
    Uses memmap to create the exact (2880, 5760) shape without RAM overhead.
    """
    raster_file = tmp_path / "test_LDEM_16_FLOAT.IMG"
    label_file = tmp_path / "test_LDEM_16_FLOAT.LBL"

    # Write PDS3 label
    label_content = f"""
    PDS_VERSION_ID = PDS3
    RECORD_TYPE = FIXED_LENGTH
    RECORD_BYTES = 23040
    FILE_RECORDS = 2880
    OBJECT = IMAGE
      LINES = {MOON_RASTER_LINES}
      LINE_SAMPLES = {MOON_RASTER_SAMPLES}
      SAMPLE_BITS = 32
      SAMPLE_TYPE = PC_REAL
      SCALING_FACTOR = 1.0
      OFFSET = 0.0
      UNIT = "METERS"
      MISSING_CONSTANT = -3.40282265e+38
    END_OBJECT = IMAGE
    END
    """
    label_file.write_text(label_content, encoding="utf-8")

    # Allocate exact file size on disk using memmap
    m = np.memmap(raster_file, dtype="<f4", mode="w+", shape=(MOON_RASTER_LINES, MOON_RASTER_SAMPLES))
    # Fill with known elevation values
    m[:] = 500.0  # 500 m elevation
    # Set a specific known pixel (Equator, 0 deg lon)
    eq_row, eq_col = 1440, 0
    m[eq_row, eq_col] = 1250.5
    # Set a nodata pixel
    m[100, 100] = -3.40282265e38
    m.flush()
    del m

    return raster_file, label_file


@pytest.fixture
def isolated_mars_raster(tmp_path):
    """
    Creates an isolated minimal Mars binary fixture for unit testing.
    Uses big-endian int16 (>i2) matching MOLA MEGDR SignedMSB2.
    """
    raster_file = tmp_path / "test_megt90n000eb.img"
    xml_file = tmp_path / "test_megt90n000eb.xml"

    # Write minimal XML metadata
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Product_Observational>
      <File_Area_Observational>
        <Array_2D_Image>
          <lines>{MARS_RASTER_LINES}</lines>
          <fields>{MARS_RASTER_SAMPLES}</fields>
          <scaling_factor>1.0</scaling_factor>
          <value_offset>0.0</value_offset>
          <special_constant>{MARS_NODATA_VALUE}</special_constant>
        </Array_2D_Image>
      </File_Area_Observational>
    </Product_Observational>
    """
    xml_file.write_text(xml_content, encoding="utf-8")

    # Allocate exact file size on disk (2880 x 5760 x 2 = 33,177,600 bytes)
    m = np.memmap(raster_file, dtype=">i2", mode="w+", shape=(MARS_RASTER_LINES, MARS_RASTER_SAMPLES))
    m[:] = -1500  # -1500 m elevation
    # Known pixel: Olympus Mons high point (18.65 N, 226.2 E)
    m[1141, 3619] = 21229
    # Known nodata pixel
    m[50, 50] = MARS_NODATA_VALUE  # -32768
    m.flush()
    del m

    return raster_file, xml_file


# ---------------------------------------------------------------------------
# Moon LOLA Reader Tests
# ---------------------------------------------------------------------------

class TestMoonLolaReader:
    def test_moon_reader_dimensions_and_dtype(self, isolated_moon_raster):
        raster_path, label_path = isolated_moon_raster
        with MoonLolaReader(raster_path, label_path) as reader:
            assert reader.data.shape == (2880, 5760)
            assert reader.data.dtype == np.dtype("<f4")
            assert reader.metadata.lines == 2880
            assert reader.metadata.samples == 5760
            assert reader.metadata.scaling_factor == 1.0

    def test_moon_coordinate_mapping(self):
        # North Pole (+90 deg) -> Row 0
        r_np, c_np = MoonLolaReader.lat_lon_to_row_col(90.0, 0.0)
        assert r_np == 0 and c_np == 0

        # South Pole (-90 deg) -> Row 2879
        r_sp, c_sp = MoonLolaReader.lat_lon_to_row_col(-90.0, 0.0)
        assert r_sp == 2879 and c_sp == 0

        # Equator (0 deg) -> Row 1440
        r_eq, c_eq = MoonLolaReader.lat_lon_to_row_col(0.0, 180.0)
        assert r_eq == 1440 and c_eq == 2880

        # Longitude normalization: -90 deg lon -> 270 deg E
        _, c_neg = MoonLolaReader.lat_lon_to_row_col(0.0, -90.0)
        assert c_neg == int(270.0 * 16.0)

        # Reverse coordinate mapping round-trip
        lat, lon = MoonLolaReader.row_col_to_lat_lon(1440, 2880)
        assert pytest.approx(lat, abs=0.1) == 0.0
        assert pytest.approx(lon, abs=0.1) == 180.0

    def test_moon_elevation_and_nodata(self, isolated_moon_raster):
        raster_path, label_path = isolated_moon_raster
        with MoonLolaReader(raster_path, label_path) as reader:
            # Equator, 0 deg lon: set to 1250.5 m
            elev = reader.get_elevation_at(0.0, 0.0)
            assert elev is not None
            assert pytest.approx(elev, abs=0.01) == 1250.5

            # Test nodata pixel at row 100, col 100
            lat_nd, lon_nd = MoonLolaReader.row_col_to_lat_lon(100, 100)
            elev_nd = reader.get_elevation_at(lat_nd, lon_nd)
            assert elev_nd is None, "Nodata must return None, not 0.0 or corrupted value!"

    def test_moon_window_extraction(self, isolated_moon_raster):
        raster_path, label_path = isolated_moon_raster
        with MoonLolaReader(raster_path, label_path) as reader:
            # Extract 1-deg box around (0, 0)
            sub_elev, valid_mask, valid_ratio = reader.read_window_pixels(
                center_lat=0.0, center_lon=0.0, half_width_deg=0.5, half_height_deg=0.5
            )
            assert sub_elev.shape[0] > 0 and sub_elev.shape[1] > 0
            assert valid_ratio > 0.99
            assert np.nanmean(sub_elev) > 0

    def test_moon_file_not_found(self, tmp_path):
        missing_path = tmp_path / "non_existent_moon.img"
        reader = MoonLolaReader(missing_path)
        with pytest.raises(FileNotFoundError, match="Moon LOLA raster file not found"):
            reader.open()


# ---------------------------------------------------------------------------
# Mars MOLA Reader Tests
# ---------------------------------------------------------------------------

class TestMarsMolaReader:
    def test_mars_reader_dimensions_and_endianness(self, isolated_mars_raster):
        raster_path, xml_path = isolated_mars_raster
        with MarsMolaReader(raster_path, xml_path) as reader:
            assert reader.data.shape == (2880, 5760)
            # Must be big-endian signed 16-bit integer (>i2)
            assert reader.data.dtype == np.dtype(">i2")
            assert reader.metadata.lines == 2880
            assert reader.metadata.samples == 5760

    def test_mars_coordinate_mapping(self):
        # North Pole (+90 deg) -> Row 0
        r_np, _ = MarsMolaReader.lat_lon_to_row_col(90.0, 0.0)
        assert r_np == 0

        # South Pole (-90 deg) -> Row 2879
        r_sp, _ = MarsMolaReader.lat_lon_to_row_col(-90.0, 0.0)
        assert r_sp == 2879

        # Olympus Mons: ~18.65 N, ~226.2 E
        r_om, c_om = MarsMolaReader.lat_lon_to_row_col(18.65, 226.2)
        assert r_om == 1141 and c_om == 3619

    def test_mars_elevation_and_nodata(self, isolated_mars_raster):
        raster_path, xml_path = isolated_mars_raster
        with MarsMolaReader(raster_path, xml_path) as reader:
            # Check Olympus Mons peak elevation (written as 21229)
            elev = reader.get_elevation_at(18.65, 226.2)
            assert elev is not None
            assert elev == 21229.0

            # Check nodata pixel at row 50, col 50 (written as -32768)
            lat_nd, lon_nd = MarsMolaReader.row_col_to_lat_lon(50, 50)
            elev_nd = reader.get_elevation_at(lat_nd, lon_nd)
            assert elev_nd is None, "Nodata (-32768) must be masked as None, not treated as valid elevation!"

    def test_mars_window_extraction(self, isolated_mars_raster):
        raster_path, xml_path = isolated_mars_raster
        with MarsMolaReader(raster_path, xml_path) as reader:
            elev_window, valid_mask, valid_ratio = reader.read_window_pixels(
                center_lat=18.65, center_lon=226.2, half_width_deg=0.5, half_height_deg=0.5
            )
            assert elev_window.shape[0] > 0
            assert valid_ratio > 0.95
            assert np.nanmax(elev_window) == 21229.0

    def test_mars_file_not_found(self, tmp_path):
        missing_path = tmp_path / "non_existent_mars.img"
        reader = MarsMolaReader(missing_path)
        with pytest.raises(FileNotFoundError, match="Mars MOLA raster file not found"):
            reader.open()


# ---------------------------------------------------------------------------
# Configuration Loader & Override Tests
# ---------------------------------------------------------------------------

class TestConfigLoader:
    def test_load_default_config(self):
        cfg = Config.load()
        assert cfg.project["name"] == "TerraTwin"
        assert cfg.moon["pixels_per_degree"] == 16.0
        assert cfg.mars["pixels_per_degree"] == 16.0
        assert cfg.analysis["tile_size_km"] == 25.0
        assert cfg.analysis["min_valid_pixel_ratio"] == 0.70

    def test_env_override(self, monkeypatch, tmp_path):
        custom_moon = str(tmp_path / "my_custom_moon.img")
        monkeypatch.setenv("TERRATWIN_MOON_RASTER", custom_moon)
        cfg = Config.load()
        assert str(cfg.get_moon_raster_path()) == str(Path(custom_moon).resolve())

    def test_path_resolution(self):
        cfg = Config.load()
        resolved_moon = cfg.get_moon_raster_path()
        assert isinstance(resolved_moon, Path)
        assert resolved_moon.name == "LDEM_16_FLOAT.IMG"
