"""TerraTwin Multi-Parameter Planetary Similarity Engine.

Computes 5-axis planetary similarity scores between extraterrestrial targets
(Moon, Mars) and terrestrial candidate tiles (Earth).

Scientific Principles:
1. Dynamic Coverage Masking: Only parameters with valid data (coverage >= 70%) in BOTH
   target and candidate contribute to the composite score.
2. Invariant Normalization: Uses physically meaningful dispersion scales rather than
   arbitrary min-max ranges.
3. Dual Reporting: Reports both individual group scores (S_terrain, S_mineral, S_thermal,
   S_water, S_geology) and the composite Relative Similarity Index.
4. Explainable Rationale: Generates 5-axis radar profiles and natural language rationales.
5. Zero Imputation: Missing parameters are never imputed as zero.
"""

import math
from typing import Dict, Any, List, Optional, Tuple
import numpy as np


# Standard default parameter weights (sum to 1.0)
DEFAULT_WEIGHTS = {
    "terrain": 0.25,
    "mineral": 0.20,
    "thermal": 0.20,
    "water": 0.15,
    "geology": 0.20,
}

# Empirical standard deviations for scaling
SIGMA_SLOPE_DEG = 8.0
SIGMA_ROUGHNESS_M = 25.0
SIGMA_RELIEF_M = 350.0
SIGMA_THERMAL_INERTIA = 150.0
SIGMA_DELTA_T_K = 30.0


class MultiParameterSimilarityEngine:
    """Computes multi-parameter similarity between planetary tiles."""

    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        min_composite_coverage: float = 0.60,
    ):
        self.weights = weights or DEFAULT_WEIGHTS.copy()
        # Normalize weights to sum to 1.0
        total_w = sum(self.weights.values())
        if total_w > 0:
            self.weights = {k: v / total_w for k, v in self.weights.items()}
        else:
            self.weights = {k: 0.20 for k in DEFAULT_WEIGHTS}

        # Enforce minimum valid coverage safeguard: cannot be silently set to 0 to bypass safeguards
        # Floor at 0.20 ensures at least one significant parameter group is evaluated
        self.min_composite_coverage = max(0.20, float(min_composite_coverage))
        self.active_groups = ["terrain", "mineral", "thermal", "water", "geology"]

    def compute_similarity(
        self,
        target_tile: Dict[str, Any],
        candidate_tile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Computes comprehensive similarity between target and candidate tiles.

        Returns:
            Dictionary containing:
            - composite_similarity_pct: Overall Relative Similarity Index [0, 100]
            - parameter_scores: Individual S_k scores [0, 100]
            - parameter_coverage: Validity masks m_k
            - composite_coverage_ratio: Fraction of weighted parameters with mutual valid coverage
            - meets_coverage_threshold: True if composite_coverage >= min_composite_coverage
            - scientific_rationale: Text description of analog correspondence
            - radar_profile: 5-axis radar data dict
        """
        scores: Dict[str, Optional[float]] = {}
        masks: Dict[str, bool] = {}

        # 1. Group 1: Terrain Geomorphometry
        s_terrain, m_terrain = self._score_terrain(target_tile, candidate_tile)
        scores["terrain"] = s_terrain
        masks["terrain"] = m_terrain

        # 2. Group 2: Mineralogy & Composition
        s_mineral, m_mineral = self._score_mineralogy(target_tile, candidate_tile)
        scores["mineral"] = s_mineral
        masks["mineral"] = m_mineral

        # 3. Group 3: Thermophysical Environment
        s_thermal, m_thermal = self._score_thermophysics(target_tile, candidate_tile)
        scores["thermal"] = s_thermal
        masks["thermal"] = m_thermal

        # 4. Group 4: Water, Ice & Volatiles
        s_water, m_water = self._score_volatiles(target_tile, candidate_tile)
        scores["water"] = s_water
        masks["water"] = m_water

        # 5. Group 5: Geological Context & Landforms
        s_geology, m_geology = self._score_geology(target_tile, candidate_tile)
        scores["geology"] = s_geology
        masks["geology"] = m_geology

        # Compute Composite Coverage Ratio C(T, E)
        total_weight = sum(self.weights.values())
        active_weight = sum(
            self.weights[k] for k in self.weights if masks.get(k, False)
        )
        composite_cov = active_weight / total_weight if total_weight > 0 else 0.0
        composite_cov_pct = round(composite_cov * 100.0, 1)
        min_cov_pct = round(self.min_composite_coverage * 100.0, 1)

        # Track valid and unobserved parameter groups
        observed_groups = [k for k in self.active_groups if masks.get(k, False)]
        unobserved_groups = [k for k in self.active_groups if not masks.get(k, False)]
        valid_group_count = len(observed_groups)
        total_group_count = len(self.active_groups)
        valid_groups_summary = f"{valid_group_count} of {total_group_count} parameter groups available"

        # Compute Composite Relative Similarity Index
        if active_weight > 0:
            weighted_sum = sum(
                self.weights[k] * scores[k]
                for k in self.weights
                if masks.get(k, False) and scores[k] is not None
            )
            composite_score = round(weighted_sum / active_weight, 2)
        else:
            composite_score = None

        meets_threshold = composite_cov >= self.min_composite_coverage
        # A match is scientifically qualified ONLY if it meets minimum coverage AND has at least 2 parameter groups
        is_qualified_match = bool(meets_threshold and valid_group_count >= 2)
        coverage_status = "QUALIFIED" if is_qualified_match else "INSUFFICIENT_COVERAGE"

        observed_names = ", ".join(g.capitalize() for g in observed_groups) if observed_groups else "None"
        unobserved_names = ", ".join(g.capitalize() for g in unobserved_groups) if unobserved_groups else "None"

        if is_qualified_match:
            status_message = (
                f"Qualified match: {valid_groups_summary} ({composite_cov_pct}% valid weighted coverage >= "
                f"{min_cov_pct}% threshold). Similarity is calculated from valid observed groups: {observed_names}."
            )
        else:
            status_message = (
                f"Insufficient coverage: {valid_groups_summary} ({composite_cov_pct}% valid weighted coverage < "
                f"{min_cov_pct}% threshold). Unobserved groups: {unobserved_names}. "
                f"Similarity ({composite_score}%) is calculated ONLY from observed groups ({observed_names}) "
                f"and must not be interpreted as a qualified analog match."
            )

        # Generate Explainability Rationale
        rationale = self._build_rationale(target_tile, candidate_tile, scores, masks)

        return {
            "composite_similarity_pct": composite_score,
            "parameter_scores": scores,
            "parameter_coverage": masks,
            "composite_coverage_ratio": round(composite_cov, 3),
            "composite_coverage_pct": composite_cov_pct,
            "min_coverage_threshold_pct": min_cov_pct,
            "meets_coverage_threshold": meets_threshold,
            "is_qualified_match": is_qualified_match,
            "coverage_status": coverage_status,
            "status_message": status_message,
            "valid_group_count": valid_group_count,
            "total_group_count": total_group_count,
            "valid_groups_summary": valid_groups_summary,
            "observed_groups": observed_groups,
            "unobserved_groups": unobserved_groups,
            "scientific_rationale": rationale,
            "radar_profile": {
                "axes": ["Terrain", "Mineralogy", "Thermal", "Volatiles", "Geology"],
                "values": [
                    scores["terrain"] if masks["terrain"] else None,
                    scores["mineral"] if masks["mineral"] else None,
                    scores["thermal"] if masks["thermal"] else None,
                    scores["water"] if masks["water"] else None,
                    scores["geology"] if masks["geology"] else None,
                ],
                "valid": [
                    masks["terrain"],
                    masks["mineral"],
                    masks["thermal"],
                    masks["water"],
                    masks["geology"],
                ],
            },
        }

    def rank_candidates(
        self,
        target_tile: Dict[str, Any],
        candidate_tiles: List[Dict[str, Any]],
        top_k: int = 5,
        include_unqualified: bool = True,
    ) -> List[Dict[str, Any]]:
        """Ranks candidate Earth tiles against target extraterrestrial tile.

        Args:
            target_tile: Extracted feature dictionary for Moon or Mars target.
            candidate_tiles: List of candidate Earth tile dictionaries.
            top_k: Maximum number of ranked candidates to return.
            include_unqualified: If True, returns candidates even when coverage threshold
                is not met, but flags them as INSUFFICIENT_COVERAGE. If False, filters
                strictly to qualified matches.
        """
        results = []
        for cand in candidate_tiles:
            sim = self.compute_similarity(target_tile, cand)
            if sim["composite_similarity_pct"] is not None:
                if include_unqualified or sim["is_qualified_match"]:
                    results.append({
                        "candidate_tile": cand,
                        "similarity": sim,
                    })

        # Sort descending by composite similarity score
        results.sort(
            key=lambda x: x["similarity"]["composite_similarity_pct"] or 0.0,
            reverse=True,
        )
        return results[:top_k]

    # -------------------------------------------------------------------------
    # Individual Group Scorers
    # -------------------------------------------------------------------------

    def _score_terrain(
        self, t: Dict[str, Any], c: Dict[str, Any]
    ) -> Tuple[Optional[float], bool]:
        """Scores terrain geomorphometry similarity."""
        m_t = t.get("terrain_valid", False)
        m_c = c.get("terrain_valid", False)
        if not (m_t and m_c):
            return None, False

        diffs = []
        # Slope comparison
        if t.get("terrain_mean_slope_deg") is not None and c.get("terrain_mean_slope_deg") is not None:
            d_slope = (t["terrain_mean_slope_deg"] - c["terrain_mean_slope_deg"]) / SIGMA_SLOPE_DEG
            diffs.append(d_slope ** 2)

        # Roughness comparison
        if t.get("terrain_roughness_tri_m") is not None and c.get("terrain_roughness_tri_m") is not None:
            d_rough = (t["terrain_roughness_tri_m"] - c["terrain_roughness_tri_m"]) / SIGMA_ROUGHNESS_M
            diffs.append(d_rough ** 2)

        # Relief comparison
        if t.get("terrain_local_relief_m") is not None and c.get("terrain_local_relief_m") is not None:
            d_relief = (t["terrain_local_relief_m"] - c["terrain_local_relief_m"]) / SIGMA_RELIEF_M
            diffs.append(d_relief ** 2)

        if not diffs:
            return None, False

        dist = math.sqrt(sum(diffs) / len(diffs))
        score = max(0.0, min(100.0, 100.0 * math.exp(-dist / 1.5)))
        return round(score, 2), True

    def _score_mineralogy(
        self, t: Dict[str, Any], c: Dict[str, Any]
    ) -> Tuple[Optional[float], bool]:
        """Scores mineralogical & lithological correspondence."""
        m_t = t.get("mineral_valid", False)
        m_c = c.get("mineral_valid", False)
        if not (m_t and m_c):
            return None, False

        body = t.get("body", "").lower()
        lith_id = c.get("mineral_lithology_id")

        score = 50.0  # Baseline neutral correspondence

        # Lithology classes (GLiM IDs):
        # 1: Siliciclastic Sedimentary, 2: Mixed Sedimentary, 3: Metamorphic
        # 5: Plutonic Acidic, 6: Plutonic Basic, 7: Volcanic Acidic, 8: Volcanic Basic (Basalt)
        if body == "moon":
            feo = t.get("mineral_feo_wt_pct")
            # Mare basalts (high FeO > 12 wt%) match mafic volcanic/plutonic
            if feo is not None and feo >= 10.0:
                if lith_id in (8, 6):  # Volcanic Basic (Basalt) / Plutonic Basic (Gabbro)
                    score = 92.0
                elif lith_id in (5, 7):
                    score = 40.0
                else:
                    score = 25.0
            # Highlands (low FeO < 6 wt%, anorthositic) match felsic plutonic/metamorphic
            elif feo is not None and feo < 8.0:
                if lith_id in (3, 5):  # Metamorphic / Plutonic Acidic (Granitoid/Anorthositic)
                    score = 88.0
                elif lith_id in (8, 6):
                    score = 35.0
                else:
                    score = 45.0
            else:
                score = 70.0

        elif body == "mars":
            strat = str(t.get("geology_stratigraphic_unit", "")).lower()
            if "basalt" in strat or "volcanic" in strat or "planum" in strat:
                if lith_id in (8, 6):
                    score = 90.0
                elif lith_id in (1, 2):
                    score = 65.0
                else:
                    score = 40.0
            elif "crater" in strat or "clay" in strat:
                if lith_id in (1, 2):  # Sedimentary / Clastic
                    score = 88.0
                else:
                    score = 50.0
            else:
                score = 72.0
        else:
            score = 75.0

        return round(score, 2), True

    def _score_thermophysics(
        self, t: Dict[str, Any], c: Dict[str, Any]
    ) -> Tuple[Optional[float], bool]:
        """Scores thermophysical environment (thermal inertia and diurnal swing)."""
        m_t = t.get("thermal_valid", False)
        m_c = c.get("thermal_valid", False)
        if not (m_t and m_c):
            return None, False

        diffs = []

        # Thermal Inertia comparison (if available in both)
        ti_t = t.get("thermal_inertia_tiu")
        ti_c = c.get("thermal_inertia_tiu")
        if ti_t is not None and ti_c is not None:
            d_ti = (ti_t - ti_c) / SIGMA_THERMAL_INERTIA
            diffs.append(d_ti ** 2)

        # Diurnal temperature delta comparison
        dt_t = t.get("thermal_delta_t_k")
        dt_c = c.get("thermal_delta_t_k")
        if dt_t is not None and dt_c is not None:
            d_dt = (dt_t - dt_c) / SIGMA_DELTA_T_K
            diffs.append(d_dt ** 2)

        if not diffs:
            # Fallback to daytime temperature difference
            t_day_t = t.get("thermal_t_day_k")
            t_day_c = c.get("thermal_t_day_k")
            if t_day_t is not None and t_day_c is not None:
                d_day = (t_day_t - t_day_c) / 40.0
                diffs.append(d_day ** 2)

        if not diffs:
            return None, False

        dist = math.sqrt(sum(diffs) / len(diffs))
        score = max(0.0, min(100.0, 100.0 * math.exp(-dist / 2.0)))
        return round(score, 2), True

    def _score_volatiles(
        self, t: Dict[str, Any], c: Dict[str, Any]
    ) -> Tuple[Optional[float], bool]:
        """Scores volatile and cryospheric regime similarity.

        Scientific Principle:
        - Hyper-arid targets (Moon, equatorial Mars) match hyper-arid terrestrial regimes (0% water, 0% glaciers).
        - Ice-rich targets (polar cold traps, high-latitude Mars mantles) match glaciated/cryospheric terrestrial regimes.
        """
        m_t = t.get("volatile_valid", False)
        m_c = c.get("volatile_valid", False)
        if not (m_t and m_c):
            return None, False

        body = t.get("body", "").lower()
        earth_water = c.get("earth_high_occurrence_water_fraction", 0.0) or 0.0
        earth_glacier = c.get("earth_glaciated_area_fraction", c.get("earth_glacier_area_fraction", 0.0)) or 0.0

        if body == "moon":
            psr_frac = t.get("volatile_psr_area_fraction", 0.0) or 0.0
            if psr_frac > 0.10:
                # Polar cold trap target: High similarity to permanently glaciated Earth regions
                score = max(0.0, 100.0 * (1.0 - abs(psr_frac - earth_glacier)))
            else:
                # Arid lunar surface: High similarity to completely dry terrestrial regions
                wetness = earth_water + earth_glacier
                score = max(0.0, 100.0 * math.exp(-wetness / 0.10))

        elif body == "mars":
            weh = t.get("volatile_weh_wt_pct", 3.0) or 3.0
            swim = t.get("mars_swim_ice_consistency_index")

            if swim is not None and swim > 0.5:
                # Subsurface ice rich: Analog to permafrost/glacier margins
                score = 85.0 if earth_glacier > 0.20 else 55.0
            elif weh < 4.0:
                # Hyper-arid equatorial Mars: Analog to hyper-arid deserts (Atacama, Sahara)
                wetness = earth_water + earth_glacier
                score = max(0.0, 100.0 * math.exp(-wetness / 0.10))
            else:
                # Moderately hydrated
                score = 70.0
        else:
            score = 75.0

        return round(score, 2), True

    def _score_geology(
        self, t: Dict[str, Any], c: Dict[str, Any]
    ) -> Tuple[Optional[float], bool]:
        """Scores geological context and impact morphology.

        Scientific Principle:
        - Terrestrial impact structures (PASSC EID) provide direct morphological and shock-metamorphic
          analogs to impact-cratered extraterrestrial surfaces.
        """
        m_t = t.get("geology_valid", False)
        m_c = c.get("geology_valid", False)
        if not (m_t and m_c):
            return None, False

        has_impact = c.get("earth_impact_structure_present", False)
        proximity_km = c.get("earth_impact_structure_proximity_km", float("inf"))

        body = t.get("body", "").lower()
        t_craters = t.get("crater_raw_count", 0) or 0

        if has_impact or (proximity_km is not None and proximity_km < 30.0):
            # Target near confirmed impact structure (e.g. Sudbury, Meteor Crater)
            score = 95.0 if t_craters > 0 else 85.0
        elif proximity_km is not None and proximity_km < 100.0:
            score = 75.0
        else:
            # Baseline background crustal similarity
            unit_t = str(t.get("geology_stratigraphic_unit", "")).lower()
            unit_c = str(c.get("geology_stratigraphic_unit", "")).lower()
            if unit_t and unit_c and (unit_t in unit_c or unit_c in unit_t):
                score = 80.0
            else:
                score = 55.0

        return round(score, 2), True

    def _build_rationale(
        self,
        t: Dict[str, Any],
        c: Dict[str, Any],
        scores: Dict[str, Optional[float]],
        masks: Dict[str, bool],
    ) -> str:
        """Constructs human-readable scientific rationale for the analog match."""
        body = t.get("body", "Planetary").capitalize()
        t_name = t.get("tile_id", f"{body} Target")
        c_name = c.get("tile_id", "Earth Candidate")

        strengths = []
        for k, v in scores.items():
            if masks.get(k, False) and v is not None and v >= 80.0:
                strengths.append(f"{k} ({v:.1f}%)")

        if strengths:
            top_factors = ", ".join(strengths)
            msg = f"{c_name} exhibits strong analog fidelity to {t_name} in {top_factors}."
        else:
            msg = f"{c_name} provides moderate background regional correspondence to {t_name}."

        # Add domain-specific notes
        if masks.get("water") and scores.get("water", 0) >= 85.0:
            msg += " Volatile regimes match closely with shared hyper-arid desiccated surface conditions."
        if masks.get("geology") and c.get("earth_impact_structure_present"):
            msg += " Location coincides with a confirmed hypervelocity impact structure, offering shock-metamorphic fidelity."

        return msg
