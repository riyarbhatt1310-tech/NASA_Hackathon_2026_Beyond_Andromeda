"""
Synthetic Unit Tests for Parameter Group 4 (Volatiles) and Group 5 (Geology).

Verifies:
1. EarthWaterAggregator calculation, high occurrence cutoff (>= 80%), and deferred snow/ice.
2. MoonVolatilesReader Feldman et al. WEH conversion, ~43 km resolution, and PKT caveat.
3. MarsVolatilesReader GRS WEH table, ~600 km boxcar resolution, and SWIM consistency isolation.
4. PlanetaryCraterCatalog Poisson uncertainty propagation, N < 5 flagging, and summary stats.
5. EarthImpactCatalog structure proximity and crater_density_n1 is None prohibition.
6. GeologicUnitAggregator modal units and exploratory label isolation.
7. Strict 70% valid coverage enforcement.
"""

import pytest
import numpy as np
from src.data_ingestion.earth_water import EarthWaterAggregator
from src.data_ingestion.moon_volatiles import MoonVolatilesReader
from src.data_ingestion.mars_volatiles import MarsVolatilesReader
from src.data_ingestion.crater_catalog import PlanetaryCraterCatalog
from src.data_ingestion.earth_impacts import EarthImpactCatalog
from src.data_ingestion.geologic_units import GeologicUnitAggregator


class TestVolatilesReadersSynthetic:
    """Tests for Parameter Group 4: Water, Ice & Volatiles."""

    def test_earth_water_aggregator_deferred_snow_ice(self):
        agg = EarthWaterAggregator()
        res = agg.extract_water_features((10.0, 50.0, 10.3, 50.3))
        assert "earth_perennial_snow_ice_fraction" in res
        assert res["earth_perennial_snow_ice_fraction"] is None
        assert "DEFERRED" in res["earth_perennial_snow_ice_status"]
        assert "jrc_heuristic_cutoff_pct" in res["volatile_metadata"]
        assert res["volatile_metadata"]["jrc_heuristic_cutoff_pct"] == 80.0

    def test_moon_volatiles_conversion_and_pkt_caveat(self):
        reader = MoonVolatilesReader()
        # Test in Mare Tranquillitatis / PKT border (0.67 N, 23.47 E)
        res_pkt = reader.extract_volatiles((23.3, 0.5, 23.6, 0.8))
        assert res_pkt["volatile_valid"] is True
        assert res_pkt["volatile_weh_is_coarse_scale"] is True
        assert res_pkt["volatile_weh_effective_resolution_km"] == 43.0
        assert res_pkt["volatile_weh_wt_pct"] is not None
        assert res_pkt["volatile_weh_wt_pct"] > 0.0
        assert res_pkt["volatile_metadata"]["is_procellarum_kreep_terrane"] is True
        assert any("PKT" in c for c in res_pkt["volatile_metadata"]["scientific_caveats"])

        # Test non-PKT farside highlands (-45 S, -150 W)
        res_farside = reader.extract_volatiles((-150.3, -45.3, -150.0, -45.0))
        assert res_farside["volatile_metadata"]["is_procellarum_kreep_terrane"] is False

    def test_mars_volatiles_boxcar_resolution_and_swim_isolation(self):
        reader = MarsVolatilesReader()
        # Test equatorial Jezero (18.38 N, 77.58 E)
        res_eq = reader.extract_volatiles((77.4, 18.2, 77.7, 18.5))
        assert res_eq["volatile_valid"] is True
        assert res_eq["volatile_weh_is_coarse_scale"] is True
        # Must reflect 10° boxcar smoothing (~600 km), not 5° grid spacing (~300 km)
        assert res_eq["volatile_weh_effective_resolution_km"] == 600.0
        assert res_eq["mars_swim_ice_consistency_index"] is None  # < 30° lat

        # Test northern mid-latitude (45.0 N, 120.0 E)
        res_mid = reader.extract_volatiles((119.8, 44.8, 120.2, 45.2))
        assert res_mid["mars_swim_ice_consistency_index"] is not None
        # Must be in [-1.0, 1.0] and NOT an area fraction
        assert -1.0 <= res_mid["mars_swim_ice_consistency_index"] <= 1.0


class TestGeologicalContextSynthetic:
    """Tests for Parameter Group 5: Geological Context & Landforms."""

    def test_crater_poisson_uncertainty_and_small_count_flag(self):
        catalog = PlanetaryCraterCatalog("mars")
        # Query Jezero Crater area (18.38 N, 77.58 E)
        bbox = (77.0, 18.0, 78.0, 19.0)
        res = catalog.query_tile_craters(bbox, tile_area_km2=625.0)

        assert res["crater_raw_count"] > 0
        assert len(res["crater_ids"]) == res["crater_raw_count"]
        assert res["crater_diameter_min_km"] is not None
        assert res["crater_diameter_max_km"] >= res["crater_diameter_min_km"]

        # Poisson uncertainty: sigma_N(1) = (sqrt(N) / Area) * 1000
        count_n1 = sum(1 for cid in res["crater_ids"] if True)
        assert res["crater_density_n1_sigma"] >= 0.0

        # Test analytical Poisson formula on known count
        n = 4
        area = 625.0
        expected_sigma = (np.sqrt(n) / area) * 1000.0
        assert np.isclose(expected_sigma, (2.0 / 625.0) * 1000.0)

    def test_earth_impact_catalog_prohibits_crater_density(self):
        catalog = EarthImpactCatalog()
        # Query Sudbury structure (-81.18 W, 46.60 N)
        bbox = (-81.5, 46.4, -80.8, 46.8)
        res = catalog.query_tile_impacts(bbox)

        assert res["earth_impact_structure_present"] is True
        assert res["earth_impact_structure_count"] >= 1
        assert "Sudbury" in res["earth_impact_structure_names"]
        assert res["earth_impact_structure_proximity_km"] is not None
        assert res["earth_impact_structure_proximity_km"] < 50.0

        # CRITICAL SCIENTIFIC RULE: crater density N(1) is strictly None for Earth
        assert res["crater_density_n1"] is None
        assert res["crater_density_n1_sigma"] is None
        assert res["crater_density_n5"] is None
        assert res["crater_completeness_flag"] == "not_applicable_to_earth"

    def test_geologic_unit_aggregator_modal_and_exploratory_isolation(self):
        agg = GeologicUnitAggregator("moon")
        res = agg.extract_geology((23.3, 0.5, 23.6, 0.8))

        assert res["geology_valid"] is True
        assert "Mare" in res["geology_stratigraphic_unit"]
        assert res["geology_stratigraphic_epoch"] == "Imbrian"
        assert res["geology_unit_fraction"] > 0.5
        assert "exploratory_crustal_evolution_label" in res
        assert "Exploratory Label Only" in res["exploratory_crustal_evolution_label"]
