"""
Real Dataset Tests for Parameter Group 4 (Volatiles) and Group 5 (Geology).

Validates actual downloaded scientific data files:
1. Mars Odyssey GRS table: data/raw/mars/volatiles/h2o_sr_5x5.tab
2. Moon LP-NS table: data/raw/moon/volatiles/hydrogenlow.txt
3. Earth Impact Database: data/raw/earth/geology/earth_impact_database.geojson
4. Global Glaciated Areas: data/raw/earth/volatiles/glaciers/ne_10m_glaciated_areas.shp
"""

import pytest
from pathlib import Path
from src.data_ingestion.mars_volatiles import MarsVolatilesReader
from src.data_ingestion.moon_volatiles import MoonVolatilesReader
from src.data_ingestion.earth_water import EarthWaterAggregator
from src.data_ingestion.earth_impacts import EarthImpactCatalog
from src.data_ingestion.crater_catalog import PlanetaryCraterCatalog


class TestRealVolatilesGeologyData:
    """Validates readers against actual local downloaded files."""

    def test_real_mars_odyssey_grs_table(self):
        reader = MarsVolatilesReader()
        assert len(reader._grs_data) > 0, "GRS data table should be loaded"

        # Check dry region (Noachis Terra: -37.5 N, -52.5 E / 307.5 E) vs elevated WEH region (Medusae Fossae: -7.5 N, 177.5 E)
        res_dry = reader.extract_volatiles((-52.7, -37.7, -52.3, -37.3))
        res_wet = reader.extract_volatiles((177.3, -7.7, 177.7, -7.3))

        assert res_dry["volatile_valid"] is True
        assert res_wet["volatile_valid"] is True

        weh_dry = res_dry["volatile_weh_wt_pct"]
        weh_wet = res_wet["volatile_weh_wt_pct"]

        assert weh_dry is not None and weh_wet is not None
        # In Mars Odyssey GRS H2O_SR_5X5, Noachis Terra WEH is ~1.7 wt%, while Medusae Fossae reaches > 7.0 wt%
        assert weh_wet > weh_dry
        assert weh_dry < 3.0
        assert weh_wet > 6.0
        assert res_dry["volatile_weh_effective_resolution_km"] == 600.0

    def test_real_moon_lp_ns_table(self):
        reader = MoonVolatilesReader()
        assert reader._grid_data is not None and len(reader._grid_data) > 0

        # Check equatorial region (0 N, 0 E) vs South Pole (-89 S, 0 E)
        res_eq = reader.extract_volatiles((-0.2, -0.2, 0.2, 0.2))
        res_pole = reader.extract_volatiles((-0.2, -89.2, 0.2, -88.8))

        assert res_eq["volatile_valid"] is True
        assert res_pole["volatile_valid"] is True

        weh_eq = res_eq["volatile_weh_wt_pct"]
        weh_pole = res_pole["volatile_weh_wt_pct"]

        assert weh_eq is not None and weh_pole is not None
        # Lunar poles exhibit marked epithermal hydrogen enhancement (suppressed neutron counts = higher ppm H)
        assert weh_pole > weh_eq
        assert res_eq["volatile_weh_effective_resolution_km"] == 43.0

    def test_real_earth_impact_database(self):
        catalog = EarthImpactCatalog()
        assert len(catalog.structures) > 0

        # Barringer Meteor Crater, Arizona (35.03 N, -111.02 W)
        res_barringer = catalog.query_tile_impacts((-111.1, 34.95, -110.95, 35.1))
        assert res_barringer["earth_impact_structure_present"] is True
        assert "Barringer" in res_barringer["earth_impact_structure_names"]
        assert res_barringer["earth_impact_structure_proximity_km"] < 10.0
        assert res_barringer["crater_density_n1"] is None

        # Non-impact location (e.g. Central Pacific ocean)
        res_pacific = catalog.query_tile_impacts((-160.0, 0.0, -159.8, 0.2))
        assert res_pacific["earth_impact_structure_present"] is False
        assert res_pacific["earth_impact_structure_count"] == 0
        assert res_pacific["earth_impact_structure_proximity_km"] > 1000.0

    def test_real_earth_glaciers_shapefile(self):
        agg = EarthWaterAggregator()
        # Test in glaciated Alaska / St. Elias region (60.0 N, -141.0 W)
        res_glacier = agg.extract_water_features((-141.2, 59.9, -140.8, 60.1))
        assert res_glacier["volatile_valid"] is True
        assert res_glacier["earth_glaciated_area_fraction"] is not None
        assert res_glacier["earth_glaciated_area_fraction"] > 0.0
        assert res_glacier["earth_glacier_area_fraction"] > 0.0

        # Test in non-glaciated Sahara Desert (25.0 N, 10.0 E)
        res_desert = agg.extract_water_features((9.9, 24.9, 10.1, 25.1))
        assert res_desert["earth_glaciated_area_fraction"] == 0.0
        assert res_desert["earth_glacier_area_fraction"] == 0.0
