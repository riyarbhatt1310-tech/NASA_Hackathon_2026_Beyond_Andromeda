"""Tests for MultiParameterSimilarityEngine.

Validates:
1. 5-axis similarity scoring across Terrain, Mineralogy, Thermophysics, Volatiles, Geology.
2. Dynamic coverage masking: only mutually valid parameters contribute to composite score.
3. Invariant physical scaling and exponential decay distance functions.
4. Explainable 5-axis radar profile and natural-language rationale output.
5. Strict zero-imputation policy: unobserved parameters are never treated as zero.
"""

import pytest
from src.processing.similarity_engine import MultiParameterSimilarityEngine, DEFAULT_WEIGHTS


@pytest.fixture
def similarity_engine():
    return MultiParameterSimilarityEngine()


@pytest.fixture
def sample_moon_target():
    """Mock record for a lunar mare target (e.g. Apollo 11)."""
    return {
        "tile_id": "Moon_Mare_Tranquillitatis",
        "body": "moon",
        "terrain_valid": True,
        "terrain_mean_slope_deg": 4.5,
        "terrain_roughness_tri_m": 8.0,
        "terrain_local_relief_m": 120.0,
        "mineral_valid": True,
        "mineral_feo_wt_pct": 15.5,  # High FeO basalt
        "thermal_valid": True,
        "thermal_delta_t_k": 288.0,
        "thermal_inertia_tiu": 55.0,
        "volatile_valid": True,
        "volatile_weh_wt_pct": 0.04,  # Hyper-arid
        "volatile_psr_area_fraction": 0.0,
        "geology_valid": True,
        "geology_stratigraphic_unit": "Mare Basalt (Imbrian)",
        "crater_raw_count": 8,
        "crater_density_n1": 12.8,
    }


@pytest.fixture
def sample_mars_jezero_target():
    """Mock record for Mars Jezero Crater."""
    return {
        "tile_id": "Mars_Jezero_Crater",
        "body": "mars",
        "terrain_valid": True,
        "terrain_mean_slope_deg": 6.8,
        "terrain_roughness_tri_m": 18.0,
        "terrain_local_relief_m": 350.0,
        "mineral_valid": True,
        "thermal_valid": True,
        "thermal_delta_t_k": 72.0,
        "thermal_inertia_tiu": 360.0,
        "volatile_valid": True,
        "volatile_weh_wt_pct": 3.8,  # Equatorial Mars
        "mars_swim_ice_consistency_index": None,
        "geology_valid": True,
        "geology_stratigraphic_unit": "Noachian Crater Floor / Clastics",
        "crater_raw_count": 14,
        "crater_density_n1": 22.4,
    }


@pytest.fixture
def sample_earth_atacama_candidate():
    """Mock record for hyper-arid basaltic terrestrial analog (Atacama Desert)."""
    return {
        "tile_id": "Earth_Atacama_Basalt_Plain",
        "body": "earth",
        "terrain_valid": True,
        "terrain_mean_slope_deg": 5.0,
        "terrain_roughness_tri_m": 9.5,
        "terrain_local_relief_m": 140.0,
        "mineral_valid": True,
        "mineral_lithology_id": 8,  # Volcanic Basic (Basalt)
        "thermal_valid": True,
        "thermal_delta_t_k": 28.0,
        "thermal_inertia_tiu": None,
        "volatile_valid": True,
        "earth_high_occurrence_water_fraction": 0.0,  # 0% water
        "earth_glacier_area_fraction": 0.0,  # 0% ice
        "geology_valid": True,
        "earth_impact_structure_present": False,
        "earth_impact_structure_proximity_km": 150.0,
    }


@pytest.fixture
def sample_earth_sudbury_candidate():
    """Mock record for terrestrial impact crater analog (Sudbury Basin)."""
    return {
        "tile_id": "Earth_Sudbury_Basin",
        "body": "earth",
        "terrain_valid": True,
        "terrain_mean_slope_deg": 7.2,
        "terrain_roughness_tri_m": 22.0,
        "terrain_local_relief_m": 280.0,
        "mineral_valid": True,
        "mineral_lithology_id": 1,  # Sedimentary / Clastic
        "thermal_valid": True,
        "thermal_delta_t_k": 22.0,
        "volatile_valid": True,
        "earth_high_occurrence_water_fraction": 0.05,
        "earth_glacier_area_fraction": 0.0,
        "geology_valid": True,
        "earth_impact_structure_present": True,
        "earth_impact_structure_proximity_km": 5.0,
        "earth_impact_structure_names": ["Sudbury"],
    }


class TestMultiParameterSimilarityEngine:
    def test_weight_normalization(self):
        engine = MultiParameterSimilarityEngine(weights={"terrain": 2.0, "mineral": 2.0})
        assert pytest.approx(sum(engine.weights.values())) == 1.0
        assert engine.weights["terrain"] == 0.5
        assert engine.weights["mineral"] == 0.5

    def test_dynamic_coverage_masking(self, similarity_engine, sample_moon_target, sample_earth_atacama_candidate):
        # Invalidate thermal on candidate
        cand = sample_earth_atacama_candidate.copy()
        cand["thermal_valid"] = False

        res = similarity_engine.compute_similarity(sample_moon_target, cand)

        assert res["parameter_coverage"]["thermal"] is False
        assert res["parameter_coverage"]["terrain"] is True
        assert res["parameter_scores"]["thermal"] is None
        # Composite coverage ratio should be 1.0 - 0.20 = 0.80
        assert pytest.approx(res["composite_coverage_ratio"], abs=0.01) == 0.80
        assert res["meets_coverage_threshold"] is True
        assert res["composite_similarity_pct"] is not None

    def test_insufficient_coverage_threshold(self, similarity_engine, sample_moon_target):
        # Candidate with only 1 parameter valid (25% coverage < 60% threshold)
        sparse_cand = {
            "tile_id": "Sparse_Candidate",
            "body": "earth",
            "terrain_valid": True,
            "terrain_mean_slope_deg": 5.0,
            "mineral_valid": False,
            "thermal_valid": False,
            "volatile_valid": False,
            "geology_valid": False,
        }

        res = similarity_engine.compute_similarity(sample_moon_target, sparse_cand)
        assert res["composite_coverage_ratio"] == pytest.approx(0.25, abs=0.01)
        assert res["meets_coverage_threshold"] is False
        assert res["is_qualified_match"] is False
        assert res["coverage_status"] == "INSUFFICIENT_COVERAGE"
        assert res["valid_group_count"] == 1
        assert "1 of 5 parameter groups available" in res["valid_groups_summary"]
        assert res["radar_profile"]["values"][0] is not None
        assert res["radar_profile"]["values"][1] is None
        assert res["radar_profile"]["values"][2] is None
        assert res["radar_profile"]["values"][3] is None
        assert res["radar_profile"]["values"][4] is None

    def test_two_of_five_parameter_groups_available(self, similarity_engine, sample_mars_jezero_target):
        """Validates behavior when only Volatiles and Geology are mutually observed (e.g. Jezero -> Sudbury)."""
        two_group_cand = {
            "tile_id": "Earth_Two_Group_Analog",
            "body": "earth",
            "terrain_valid": False,  # Missing terrain
            "mineral_valid": False,  # Missing mineralogy
            "thermal_valid": False,  # Missing thermal
            "volatile_valid": True,  # Valid volatiles (hyper-arid)
            "earth_high_occurrence_water_fraction": 0.0,
            "earth_glacier_area_fraction": 0.0,
            "geology_valid": True,  # Valid geology (impact)
            "earth_impact_structure_present": True,
            "earth_impact_structure_proximity_km": 0.0,
            "earth_impact_structure_names": ["Sudbury"],
        }

        res = similarity_engine.compute_similarity(sample_mars_jezero_target, two_group_cand)

        # 1. Parameter counts & summary
        assert res["valid_group_count"] == 2
        assert res["total_group_count"] == 5
        assert res["valid_groups_summary"] == "2 of 5 parameter groups available"
        assert res["observed_groups"] == ["water", "geology"]
        assert res["unobserved_groups"] == ["terrain", "mineral", "thermal"]

        # 2. Coverage calculation (Water 15% + Geology 20% = 35%)
        assert pytest.approx(res["composite_coverage_pct"], abs=0.1) == 35.0
        assert res["meets_coverage_threshold"] is False
        assert res["is_qualified_match"] is False
        assert res["coverage_status"] == "INSUFFICIENT_COVERAGE"
        assert "Insufficient coverage" in res["status_message"]
        assert "2 of 5 parameter groups available" in res["status_message"]

        # 3. Missing values are None in radar profile, NOT zero
        profile = res["radar_profile"]
        assert profile["values"][0] is None  # Terrain
        assert profile["values"][1] is None  # Mineralogy
        assert profile["values"][2] is None  # Thermal
        assert profile["values"][3] is not None  # Water
        assert profile["values"][4] is not None  # Geology
        assert profile["valid"] == [False, False, False, True, True]

        # 4. Composite similarity is calculated ONLY from observed groups
        # Both water and geology have high scores (~95%), composite is ~95%, NOT diluted by missing groups
        assert res["composite_similarity_pct"] > 85.0

    def test_missing_values_never_treated_as_zero(self, similarity_engine):
        """Ensures unobserved parameters do not drag composite similarity down to zero."""
        target = {
            "body": "mars",
            "terrain_valid": False,
            "mineral_valid": False,
            "thermal_valid": False,
            "volatile_valid": True,
            "volatile_weh_wt_pct": 2.0,
            "geology_valid": True,
            "crater_density_n1": 20.0,
            "crater_raw_count": 10,
        }
        cand = {
            "body": "earth",
            "terrain_valid": False,
            "mineral_valid": False,
            "thermal_valid": False,
            "volatile_valid": True,
            "earth_high_occurrence_water_fraction": 0.0,
            "geology_valid": True,
            "earth_impact_structure_present": True,
            "earth_impact_structure_proximity_km": 0.0,
        }

        res = similarity_engine.compute_similarity(target, cand)
        # If unobserved groups were treated as 0.0, composite would be ~30%.
        # With dynamic coverage masking, composite reflects only valid groups (> 80%).
        assert res["composite_similarity_pct"] is not None
        assert res["composite_similarity_pct"] > 75.0
        # Radar profile must have None for unobserved groups
        for idx in [0, 1, 2]:
            assert res["radar_profile"]["values"][idx] is None

    def test_safeguard_zero_coverage_not_allowed(self):
        """Ensures min_composite_coverage cannot be silently set to 0 to bypass safeguards."""
        engine_zero = MultiParameterSimilarityEngine(min_composite_coverage=0.0)
        assert engine_zero.min_composite_coverage >= 0.20

        engine_negative = MultiParameterSimilarityEngine(min_composite_coverage=-0.5)
        assert engine_negative.min_composite_coverage >= 0.20

    def test_weight_tuning_updates_ranking_and_radar(self, sample_mars_jezero_target):
        """Verifies that changing weights updates composite scores and radar profiles."""
        cand_water = {
            "tile_id": "Water_Heavy",
            "body": "earth",
            "terrain_valid": True,
            "terrain_mean_slope_deg": 25.0,  # poor slope match
            "terrain_roughness_tri_m": 80.0,
            "terrain_local_relief_m": 900.0,
            "mineral_valid": False,
            "thermal_valid": False,
            "volatile_valid": True,
            "earth_high_occurrence_water_fraction": 0.0,  # excellent water match
            "earth_glacier_area_fraction": 0.0,
            "geology_valid": False,
        }
        cand_terrain = {
            "tile_id": "Terrain_Heavy",
            "body": "earth",
            "terrain_valid": True,
            "terrain_mean_slope_deg": 6.8,  # identical slope match
            "terrain_roughness_tri_m": 18.0,
            "terrain_local_relief_m": 350.0,
            "mineral_valid": False,
            "thermal_valid": False,
            "volatile_valid": True,
            "earth_high_occurrence_water_fraction": 0.90,  # poor water match
            "earth_glacier_area_fraction": 0.0,
            "geology_valid": False,
        }

        # Weighting terrain heavily
        eng_terrain = MultiParameterSimilarityEngine(weights={"terrain": 90.0, "water": 10.0}, min_composite_coverage=0.2)
        r_terrain = eng_terrain.rank_candidates(sample_mars_jezero_target, [cand_water, cand_terrain])
        assert r_terrain[0]["candidate_tile"]["tile_id"] == "Terrain_Heavy"

        # Weighting water heavily
        eng_water = MultiParameterSimilarityEngine(weights={"terrain": 10.0, "water": 90.0}, min_composite_coverage=0.2)
        r_water = eng_water.rank_candidates(sample_mars_jezero_target, [cand_water, cand_terrain])
        assert r_water[0]["candidate_tile"]["tile_id"] == "Water_Heavy"

    def test_hyperarid_volatile_matching(self, similarity_engine, sample_moon_target, sample_earth_atacama_candidate):
        res = similarity_engine.compute_similarity(sample_moon_target, sample_earth_atacama_candidate)
        assert res["parameter_coverage"]["water"] is True
        # Both Moon and Atacama have virtually zero water -> high volatile similarity
        assert res["parameter_scores"]["water"] is not None
        assert res["parameter_scores"]["water"] > 90.0

    def test_impact_geology_matching(self, similarity_engine, sample_mars_jezero_target, sample_earth_sudbury_candidate):
        res = similarity_engine.compute_similarity(sample_mars_jezero_target, sample_earth_sudbury_candidate)
        assert res["parameter_coverage"]["geology"] is True
        # Sudbury is a confirmed hypervelocity impact structure -> high geology similarity
        assert res["parameter_scores"]["geology"] is not None
        assert res["parameter_scores"]["geology"] >= 90.0

    def test_radar_profile_and_rationale(self, similarity_engine, sample_mars_jezero_target, sample_earth_sudbury_candidate):
        res = similarity_engine.compute_similarity(sample_mars_jezero_target, sample_earth_sudbury_candidate)

        profile = res["radar_profile"]
        assert len(profile["axes"]) == 5
        assert len(profile["values"]) == 5
        assert all(v >= 0.0 for v in profile["values"])
        assert "Sudbury" in res["scientific_rationale"] or "impact" in res["scientific_rationale"]

    def test_candidate_ranking(self, similarity_engine, sample_mars_jezero_target, sample_earth_sudbury_candidate, sample_earth_atacama_candidate):
        ranked = similarity_engine.rank_candidates(
            target_tile=sample_mars_jezero_target,
            candidate_tiles=[sample_earth_sudbury_candidate, sample_earth_atacama_candidate],
            top_k=5,
        )
        assert len(ranked) == 2
        # Verify descending sort order
        assert ranked[0]["similarity"]["composite_similarity_pct"] >= ranked[1]["similarity"]["composite_similarity_pct"]
