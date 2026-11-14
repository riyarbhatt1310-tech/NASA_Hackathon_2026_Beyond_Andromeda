"""
Integration and validation tests against REAL downloaded planetary thermal datasets.

Bodies tested:
1. Moon: LRO Diviner bolometric surface temperatures (Williams et al. 2017).
2. Mars: 2001 Mars Odyssey THEMIS 100m quantitative thermal inertia (USGS Astropedia)
         and MGS TES daytime/nighttime thermal inertia (Putzig et al. 2007).
3. Earth: NASA MODIS Aqua Level-3 (MYD11A1.061) day and night LST (Planetary Computer).
"""

from pathlib import Path
import pytest
import numpy as np

from src.data_ingestion.moon_diviner import MoonDivinerReader
from src.data_ingestion.mars_thermis import MarsThermisReader
from src.data_ingestion.mars_tes_temp import MarsTesTempReader
from src.data_ingestion.earth_modis import ModisLSTReader
from src.processing.tile_extractor import PlanetaryTileExtractor

RAW_DIR = (
    Path(__file__).resolve().parents[2] / "data" / "raw"
    if len(Path(__file__).resolve().parents) > 2 and (Path(__file__).resolve().parents[2] / "data").exists()
    else Path(__file__).resolve().parent.parent / "data" / "raw"
)

# Real file paths
MOON_DIVINER_DAY = RAW_DIR / "moon" / "thermal" / "diviner_day.tif"
MOON_DIVINER_NIGHT = RAW_DIR / "moon" / "thermal" / "diviner_night.tif"
MOON_DIVINER_GHRM = RAW_DIR / "moon" / "thermal" / "diviner_night_ghrm_apollo11.tif"

MARS_THEMIS_TIF = RAW_DIR / "mars" / "thermal" / "themis_ti_jezero_100m.tif"
MARS_TES_DAY_LBL = RAW_DIR / "mars" / "thermal" / "global_ti_day_2007.lbl"
MARS_TES_NIGHT_LBL = RAW_DIR / "mars" / "thermal" / "global_ti_night_2007.lbl"

EARTH_MODIS_DAY = RAW_DIR / "earth" / "thermal" / "modis_lst_day.tif"
EARTH_MODIS_NIGHT = RAW_DIR / "earth" / "thermal" / "modis_lst_night.tif"
EARTH_MODIS_QC_DAY = RAW_DIR / "earth" / "thermal" / "modis_qc_day.tif"
EARTH_MODIS_QC_NIGHT = RAW_DIR / "earth" / "thermal" / "modis_qc_night.tif"


# =============================================================================
# 1. Moon Real Diviner Tests
# =============================================================================

@pytest.mark.skipif(not (MOON_DIVINER_DAY.exists() and MOON_DIVINER_NIGHT.exists()), reason="Real Moon Diviner data not downloaded")
class TestMoonRealThermal:
    def test_moon_diviner_reader_real(self):
        reader = MoonDivinerReader(str(MOON_DIVINER_DAY), str(MOON_DIVINER_NIGHT))
        with reader:
            meta = reader.get_metadata()
            assert meta["instrument"] == "LRO Diviner Lunar Radiometer Experiment"
            assert meta["body"] == "moon"
            assert meta["temperature_unit"] == "Kelvin (K)"

            # Query tile at Lat 5.0 N, Lon 23.47 E
            (d_data, d_mask), (n_data, n_mask), cov = reader.read_window_pixels(
                center_lat=5.0, center_lon=23.47, half_width_deg=0.5, half_height_deg=0.5
            )
            assert cov >= 0.70, f"Expected >= 70% valid coverage, got {cov*100:.1f}%"
            assert np.any(d_mask) and np.any(n_mask)

            t_day = float(np.mean(d_data[d_mask]))
            t_night = float(np.mean(n_data[n_mask]))
            assert 370.0 <= t_day <= 405.0, f"Unphysical Moon daytime temp: {t_day} K"
            assert 90.0 <= t_night <= 115.0, f"Unphysical Moon nighttime temp: {t_night} K"
            assert (t_day - t_night) > 260.0, "Diurnal range on Moon equator should exceed 260 K"

    def test_moon_tile_extractor_real_thermal(self):
        extractor = PlanetaryTileExtractor(
            moon_diviner_reader=MoonDivinerReader(str(MOON_DIVINER_DAY), str(MOON_DIVINER_NIGHT))
        )
        record = extractor.extract_moon_tile(lat=5.0, lon=23.47)
        assert record["body"] == "moon"
        assert record["thermal_valid"] is True
        assert record["thermal_coverage_pct"] >= 70.0
        assert 370.0 <= record["thermal_t_day_k"] <= 405.0
        assert 90.0 <= record["thermal_t_night_k"] <= 115.0
        assert record["thermal_delta_t_k"] > 260.0


# =============================================================================
# 2. Mars Real THEMIS & TES Tests
# =============================================================================

@pytest.mark.skipif(not (MARS_THEMIS_TIF.exists() and MARS_TES_DAY_LBL.exists()), reason="Real Mars thermal data not downloaded")
class TestMarsRealThermal:
    def test_themis_reader_jezero_real(self):
        reader = MarsThermisReader(str(MARS_THEMIS_TIF))
        with reader:
            meta = reader.get_metadata()
            assert meta["instrument"] == "2001 Mars Odyssey THEMIS"
            assert meta["body"] == "mars"
            assert meta["parameter"] == "Thermal Inertia"

            # Query Jezero Crater at 18.38 N, 77.58 E
            data, mask, cov = reader.read_window_pixels(18.38, 77.58, 0.05, 0.05)
            assert cov == 1.0, f"Expected 100% valid coverage over Jezero crop, got {cov*100:.1f}%"
            ti_mean = float(np.mean(data[mask]))
            assert 250.0 <= ti_mean <= 450.0, f"Unexpected Jezero TI mean: {ti_mean} tiu"

    def test_tes_reader_real_pds(self):
        reader = MarsTesTempReader(str(MARS_TES_DAY_LBL), str(MARS_TES_NIGHT_LBL))
        with reader:
            meta = reader.get_metadata()
            assert "TES" in meta["instrument"]
            assert meta["format"] == "PDS"

            # Query Jezero region
            (d_data, d_mask), (n_data, n_mask), cov = reader.read_window_pixels(18.38, 77.58, 0.5, 0.5)
            assert cov >= 0.70
            assert np.any(d_mask) and np.any(n_mask)

    def test_mars_tile_extractor_real_themis_and_tes(self):
        extractor = PlanetaryTileExtractor(
            mars_thermis_reader=MarsThermisReader(str(MARS_THEMIS_TIF)),
            mars_tes_reader=MarsTesTempReader(str(MARS_TES_DAY_LBL), str(MARS_TES_NIGHT_LBL)),
        )
        record = extractor.extract_mars_tile(lat=18.38, lon=77.58)
        assert record["body"] == "mars"
        assert record["thermal_valid"] is True
        assert record["thermal_coverage_pct"] >= 70.0
        assert 250.0 <= record["thermal_inertia_tiu"] <= 450.0
        assert record["thermal_t_day_k"] is not None
        assert record["thermal_t_night_k"] is not None
        assert "themis" in record["thermal_metadata"]
        assert "tes" in record["thermal_metadata"]


# =============================================================================
# 3. Earth Real MODIS LST Tests
# =============================================================================

@pytest.mark.skipif(not (EARTH_MODIS_DAY.exists() and EARTH_MODIS_NIGHT.exists()), reason="Real Earth MODIS data not downloaded")
class TestEarthRealThermal:
    def test_modis_lst_reader_real(self):
        reader = ModisLSTReader(
            day_path=str(EARTH_MODIS_DAY),
            night_path=str(EARTH_MODIS_NIGHT),
            qc_day_path=str(EARTH_MODIS_QC_DAY),
            qc_night_path=str(EARTH_MODIS_QC_NIGHT),
            satellite="Aqua",
        )
        with reader:
            meta = reader.get_metadata()
            assert meta["instrument"] == "MODIS Aqua"
            assert meta["body"] == "earth"
            assert meta["scale_factor"] == 0.02
            assert meta["native_res_km"] == 1.0

            # Query Death Valley at Lat 36.5 N, Lon -116.9 W
            (d_data, d_mask), (n_data, n_mask), cov = reader.read_window_pixels(
                center_lat=36.5, center_lon=-116.9, half_width_deg=0.1, half_height_deg=0.1
            )
            assert cov >= 0.70, f"Expected >= 70% valid coverage, got {cov*100:.1f}%"
            t_day = float(np.mean(d_data[d_mask]))
            t_night = float(np.mean(n_data[n_mask]))
            delta_t = t_day - t_night

            assert 315.0 <= t_day <= 345.0, f"Unphysical Mojave summer day LST: {t_day} K"
            assert 290.0 <= t_night <= 315.0, f"Unphysical Mojave night LST: {t_night} K"
            assert delta_t > 15.0, f"Diurnal swing too small for desert: {delta_t} K"

    def test_earth_tile_extractor_real_modis(self):
        modis = ModisLSTReader(
            day_path=str(EARTH_MODIS_DAY),
            night_path=str(EARTH_MODIS_NIGHT),
            qc_day_path=str(EARTH_MODIS_QC_DAY),
            qc_night_path=str(EARTH_MODIS_QC_NIGHT),
            satellite="Aqua",
        )
        extractor = PlanetaryTileExtractor(earth_modis_reader=modis)
        record = extractor.extract_earth_tile(lat=36.5, lon=-116.9)
        assert record["body"] == "earth"
        assert record["thermal_valid"] is True
        assert record["thermal_coverage_pct"] >= 70.0
        assert 315.0 <= record["thermal_t_day_k"] <= 345.0
        assert 290.0 <= record["thermal_t_night_k"] <= 315.0
        assert record["thermal_delta_t_k"] > 15.0
        assert record["thermal_inertia_tiu"] is None  # Earth record does not fabricate thermal inertia
