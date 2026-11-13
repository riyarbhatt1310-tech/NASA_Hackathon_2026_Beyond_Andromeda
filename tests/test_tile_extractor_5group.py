"""
End-to-End 5-Parameter-Group Tile Extractor Integration Tests.

Validates that PlanetaryTileExtractor extracts all 5 foundational science groups:
- Group 1: Terrain Geomorphometry
- Group 2: Mineralogy & Composition
- Group 3: Thermophysics
- Group 4: Water, Ice & Volatiles
- Group 5: Geological Context & Landforms
Across real target sites on Earth, Moon, and Mars.
"""

from pathlib import Path
import pytest
from src.processing.tile_extractor import PlanetaryTileExtractor
from src.data_ingestion.moon_lola import MoonLolaReader
from src.data_ingestion.mars_mola import MarsMolaReader
from src.data_ingestion.moon_diviner import MoonDivinerReader
from src.data_ingestion.mars_thermis import MarsThermisReader
from src.data_ingestion.mars_tes_temp import MarsTesTempReader
from src.data_ingestion.earth_glim import EarthGLiMAggregator
from src.data_ingestion.earth_modis import ModisLSTReader
from src.data_ingestion.earth_water import EarthWaterAggregator
from src.data_ingestion.moon_volatiles import MoonVolatilesReader
from src.data_ingestion.mars_volatiles import MarsVolatilesReader
from src.data_ingestion.crater_catalog import PlanetaryCraterCatalog
from src.data_ingestion.earth_impacts import EarthImpactCatalog
from src.data_ingestion.geologic_units import GeologicUnitAggregator

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"


@pytest.fixture(scope="module")
def full_extractor():
    """Builds extractor with operational readers."""
    diviner_day = RAW_DIR / "moon" / "thermal" / "diviner_day.tif"
    diviner_night = RAW_DIR / "moon" / "thermal" / "diviner_night.tif"
    moon_diviner = MoonDivinerReader(str(diviner_day), str(diviner_night)) if diviner_day.exists() else None

    themis_tif = RAW_DIR / "mars" / "thermal" / "themis_ti_jezero_100m.tif"
    mars_themis = MarsThermisReader(str(themis_tif)) if themis_tif.exists() else None

    tes_day = RAW_DIR / "mars" / "thermal" / "global_ti_day_2007.lbl"
    tes_night = RAW_DIR / "mars" / "thermal" / "global_ti_night_2007.lbl"
    mars_tes = MarsTesTempReader(str(tes_day), str(tes_night)) if tes_day.exists() else None

    modis_day = RAW_DIR / "earth" / "thermal" / "modis_lst_day.tif"
    modis_night = RAW_DIR / "earth" / "thermal" / "modis_lst_night.tif"
    modis_qc_day = RAW_DIR / "earth" / "thermal" / "modis_qc_day.tif"
    modis_qc_night = RAW_DIR / "earth" / "thermal" / "modis_qc_night.tif"
    earth_modis = ModisLSTReader(str(modis_day), str(modis_night), str(modis_qc_day), str(modis_qc_night)) if modis_day.exists() else None

    glim_tif = RAW_DIR / "earth" / "mineralogy" / "glim_global.tif"
    earth_glim = EarthGLiMAggregator(str(glim_tif)) if glim_tif.exists() else None

    return PlanetaryTileExtractor(
        moon_reader=MoonLolaReader(),
        mars_reader=MarsMolaReader(),
        moon_diviner_reader=moon_diviner,
        mars_thermis_reader=mars_themis,
        mars_tes_reader=mars_tes,
        earth_glim_aggregator=earth_glim,
        earth_modis_reader=earth_modis,
        earth_water_aggregator=EarthWaterAggregator(),
        moon_volatiles_reader=MoonVolatilesReader(),
        mars_volatiles_reader=MarsVolatilesReader(),
        moon_crater_catalog=PlanetaryCraterCatalog("moon"),
        mars_crater_catalog=PlanetaryCraterCatalog("mars"),
        earth_impact_catalog=EarthImpactCatalog(),
        moon_geology_aggregator=GeologicUnitAggregator("moon"),
        mars_geology_aggregator=GeologicUnitAggregator("mars"),
        earth_geology_aggregator=GeologicUnitAggregator("earth"),
    )


class TestTileExtractor5Group:
    """End-to-end integration tests for 5-group tile records."""

    def test_moon_apollo11_5group_extraction(self, full_extractor):
        rec = full_extractor.extract_moon_tile(0.67, 23.47)

        # Identification
        assert rec["body"] == "moon"
        assert rec["actual_area_km2"] > 500.0

        # Group 1: Terrain
        assert rec["terrain_valid"] is True
        assert rec["terrain_mean_elevation_m"] is not None
        assert rec["terrain_mean_slope_deg"] is not None

        # Group 3: Thermal
        assert "thermal_valid" in rec

        # Group 4: Volatiles
        assert rec["volatile_valid"] is True
        assert rec["volatile_weh_wt_pct"] is not None
        assert rec["volatile_weh_is_coarse_scale"] is True
        assert rec["volatile_weh_effective_resolution_km"] == 43.0
        assert rec["earth_water_occurrence_pct"] is None  # Earth only

        # Group 5: Geology & Craters
        assert rec["geology_valid"] is True
        assert "Mare" in rec["geology_stratigraphic_unit"]
        assert rec["geology_stratigraphic_epoch"] == "Imbrian"
        assert rec["crater_raw_count"] is not None
        assert rec["crater_density_n1"] is not None
        assert rec["earth_impact_structure_present"] is None  # Earth only

    def test_moon_south_pole_psr_handling(self, full_extractor):
        rec = full_extractor.extract_moon_tile(-89.9, 0.0)

        assert rec["body"] == "moon"
        assert rec["terrain_valid"] is True
        # Cold trap fraction around South Pole
        assert rec["volatile_valid"] is True
        assert rec["volatile_psr_area_fraction"] is not None
        assert rec["volatile_psr_area_fraction"] > 0.0
        assert "Pre-Nectarian" in rec["geology_stratigraphic_unit"]

    def test_mars_jezero_5group_extraction(self, full_extractor):
        rec = full_extractor.extract_mars_tile(18.38, 77.58)

        # Identification
        assert rec["body"] == "mars"

        # Group 1: Terrain
        assert rec["terrain_valid"] is True
        assert rec["terrain_mean_elevation_m"] is not None

        # Group 3: Thermal
        assert rec["thermal_valid"] is True
        assert rec["thermal_inertia_tiu"] is not None

        # Group 4: Volatiles
        assert rec["volatile_valid"] is True
        assert rec["volatile_weh_wt_pct"] is not None
        assert rec["volatile_weh_effective_resolution_km"] == 600.0

        # Group 5: Geology & Craters
        assert rec["geology_valid"] is True
        assert "Noachian" in rec["geology_stratigraphic_unit"]
        assert rec["crater_raw_count"] > 0
        assert "01-000001" in rec["crater_ids"]  # Jezero crater ID
        assert rec["crater_density_n1"] is not None
        assert rec["crater_density_n1_sigma"] is not None

    def test_earth_sudbury_5group_extraction(self, full_extractor):
        # Sudbury Basin (-81.18 W, 46.60 N)
        rec = full_extractor.extract_earth_tile(46.60, -81.18)

        assert rec["body"] == "earth"

        # Group 2: Mineralogy (GLiM)
        assert rec["mineral_valid"] is True
        assert rec["mineral_lithology_id"] is not None

        # Group 3: Thermal (MODIS)
        assert "thermal_valid" in rec

        # Group 4: Volatiles (JRC & Glaciers)
        assert rec["volatile_valid"] is True
        assert rec["earth_glacier_area_fraction"] is not None
        assert rec["earth_perennial_snow_ice_fraction"] is None  # Deferred

        # Group 5: Geology & Impacts (PASSC)
        assert rec["geology_valid"] is True
        assert rec["earth_impact_structure_present"] is True
        assert "Sudbury" in rec["earth_impact_structure_names"]
        assert rec["earth_impact_structure_proximity_km"] < 25.0
        # Crater density N(1) must be strictly None
        assert rec["crater_density_n1"] is None
        assert rec["crater_density_n1_sigma"] is None
