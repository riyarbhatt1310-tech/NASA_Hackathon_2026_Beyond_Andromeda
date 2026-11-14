"""
Multi-Parameter Planetary Tile Feature Extractor for TerraTwin.

Connects the physical analysis grid, memory-mapped raster readers,
the geomorphometry metric engine, mineralogy extractors, thermal readers,
volatiles & cryosphere aggregators, and geological context / crater catalogs.
Implements unified 5-parameter-group records with resolution and quality tracking.
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple
import numpy as np

from src.core.constants import (
    MOON_REFERENCE_RADIUS_M,
    MARS_REFERENCE_RADIUS_M,
    EARTH_VOLUMETRIC_RADIUS_M,
    ANALYSIS_TILE_SIZE_KM,
    MIN_VALID_COVERAGE_RATIO,
)
from src.core.grids import PlanetaryGrid, PlanetaryTile
from src.core.metrics import compute_tile_geomorphometry
from src.data_ingestion.moon_lola import MoonLolaReader
from src.data_ingestion.mars_mola import MarsMolaReader
from src.data_ingestion.moon_diviner import MoonDivinerReader
from src.data_ingestion.mars_thermis import MarsThermisReader
from src.data_ingestion.mars_tes_temp import MarsTesTempReader
from src.data_ingestion.earth_glim import EarthGLiMAggregator
from src.data_ingestion.earth_dem import EarthDemReader
from src.data_ingestion.earth_modis import ModisLSTReader
from src.data_ingestion.earth_water import EarthWaterAggregator
from src.data_ingestion.moon_volatiles import MoonVolatilesReader
from src.data_ingestion.mars_volatiles import MarsVolatilesReader
from src.data_ingestion.crater_catalog import PlanetaryCraterCatalog
from src.data_ingestion.earth_impacts import EarthImpactCatalog
from src.data_ingestion.geologic_units import GeologicUnitAggregator


class PlanetaryTileExtractor:
    """
    Extracts multi-parameter features for spatial analysis tiles.
    Processes real Moon, Mars, and Earth datasets across all 5 parameter groups:
    - Group 1: Terrain Geomorphometry
    - Group 2: Mineralogy & Composition
    - Group 3: Thermophysics
    - Group 4: Water, Ice & Volatiles
    - Group 5: Geological Context & Landforms
    """

    def __init__(
        self,
        moon_reader: Optional[MoonLolaReader] = None,
        mars_reader: Optional[MarsMolaReader] = None,
        moon_diviner_reader: Optional[MoonDivinerReader] = None,
        mars_thermis_reader: Optional[MarsThermisReader] = None,
        mars_tes_reader: Optional[MarsTesTempReader] = None,
        earth_dem_reader: Optional[EarthDemReader] = None,
        earth_glim_aggregator: Optional[EarthGLiMAggregator] = None,
        earth_modis_reader: Optional[ModisLSTReader] = None,
        earth_water_aggregator: Optional[EarthWaterAggregator] = None,
        moon_volatiles_reader: Optional[MoonVolatilesReader] = None,
        mars_volatiles_reader: Optional[MarsVolatilesReader] = None,
        moon_crater_catalog: Optional[PlanetaryCraterCatalog] = None,
        mars_crater_catalog: Optional[PlanetaryCraterCatalog] = None,
        earth_impact_catalog: Optional[EarthImpactCatalog] = None,
        moon_geology_aggregator: Optional[GeologicUnitAggregator] = None,
        mars_geology_aggregator: Optional[GeologicUnitAggregator] = None,
        earth_geology_aggregator: Optional[GeologicUnitAggregator] = None,
        target_tile_size_km: float = ANALYSIS_TILE_SIZE_KM,
        min_valid_coverage: float = MIN_VALID_COVERAGE_RATIO,
    ):
        self.moon_reader = moon_reader
        self.mars_reader = mars_reader
        self.moon_diviner_reader = moon_diviner_reader
        self.mars_thermis_reader = mars_thermis_reader
        self.mars_tes_reader = mars_tes_reader
        self.earth_dem_reader = earth_dem_reader
        self.earth_glim_aggregator = earth_glim_aggregator
        self.earth_modis_reader = earth_modis_reader

        # Group 4: Volatiles readers
        self.earth_water_aggregator = earth_water_aggregator or EarthWaterAggregator()
        self.moon_volatiles_reader = moon_volatiles_reader or MoonVolatilesReader()
        self.mars_volatiles_reader = mars_volatiles_reader or MarsVolatilesReader()

        # Group 5: Crater & Geological Context
        self.moon_crater_catalog = moon_crater_catalog or PlanetaryCraterCatalog("moon")
        self.mars_crater_catalog = mars_crater_catalog or PlanetaryCraterCatalog("mars")
        self.earth_impact_catalog = earth_impact_catalog or EarthImpactCatalog()
        self.moon_geology_aggregator = moon_geology_aggregator or GeologicUnitAggregator("moon")
        self.mars_geology_aggregator = mars_geology_aggregator or GeologicUnitAggregator("mars")
        self.earth_geology_aggregator = earth_geology_aggregator or GeologicUnitAggregator("earth")

        self.target_tile_size_km = target_tile_size_km
        self.min_valid_coverage = min_valid_coverage

        self.grids = {
            "moon": PlanetaryGrid("moon", target_tile_size_km),
            "mars": PlanetaryGrid("mars", target_tile_size_km),
            "earth": PlanetaryGrid("earth", target_tile_size_km),
        }

    # -------------------------------------------------------------------------
    # Moon Extraction
    # -------------------------------------------------------------------------

    def extract_moon_tile(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Extracts multi-parameter record for a ~25 km Moon tile centered at (lat, lon).
        """
        tile: PlanetaryTile = self.grids["moon"].get_tile_for_coord(lat, lon)
        half_height = (tile.lat_max - tile.lat_min) / 2.0
        half_width = (tile.lon_max - tile.lon_min) / 2.0
        bbox = (tile.lon_min, tile.lat_min, tile.lon_max, tile.lat_max)

        # Group 1: Real Moon LOLA Terrain
        if self.moon_reader is not None:
            elev_m, valid_mask, valid_ratio = self.moon_reader.read_window_pixels(
                center_lat=tile.lat_center,
                center_lon=tile.lon_center,
                half_width_deg=half_width,
                half_height_deg=half_height,
            )
            geo_metrics = compute_tile_geomorphometry(
                elev_m=elev_m,
                lat_center=tile.lat_center,
                radius_m=MOON_REFERENCE_RADIUS_M,
                pixel_res_deg=1.0 / 16.0,
                native_res_km=1.8952,
                min_valid_ratio=self.min_valid_coverage,
            )
        else:
            geo_metrics = {
                "valid_ratio": 0.0,
                "coverage_pct": 0.0,
                "elevation_mean_m": None,
                "elevation_std_m": None,
                "elevation_min_m": None,
                "elevation_max_m": None,
                "elevation_relief_m": None,
                "slope_mean_deg": None,
                "slope_max_deg": None,
                "aspect_mean_deg": None,
                "roughness_mean_m": None,
                "tpi_mean_m": None,
                "tri_mean_m": None,
            }

        # Group 3: Moon Diviner Thermal
        thermal_metrics = self._load_moon_thermal(tile, half_width, half_height)

        # Group 4: Moon Volatiles (LP-NS WEH & optional LOLA GDRPSR)
        volatile_metrics = self.moon_volatiles_reader.extract_volatiles(bbox)

        # Group 5: Moon Geological Context & Craters
        geology_unit_metrics = self.moon_geology_aggregator.extract_geology(bbox)
        crater_metrics = self.moon_crater_catalog.query_tile_craters(bbox, tile.actual_area_km2)
        geology_metrics = {**geology_unit_metrics, **crater_metrics}

        record = self._build_multi_parameter_record(
            tile=tile,
            terrain_metrics=geo_metrics,
            thermal_metrics=thermal_metrics,
            volatile_metrics=volatile_metrics,
            geology_metrics=geology_metrics,
            body="moon",
        )
        return record

    def _load_moon_thermal(
        self,
        tile: PlanetaryTile,
        half_width: float,
        half_height: float,
    ) -> Dict[str, Any]:
        """Loads and processes Diviner thermal layers for a Moon tile."""
        if self.moon_diviner_reader is None:
            return {"thermal_valid": False, "thermal_coverage_pct": 0.0}

        try:
            (day_data, day_mask), (night_data, night_mask), cov = self.moon_diviner_reader.read_window_pixels(
                center_lat=tile.lat_center,
                center_lon=tile.lon_center,
                half_width_deg=half_width,
                half_height_deg=half_height,
            )
            cov_pct = round(cov * 100.0, 1)
            is_valid = cov >= self.min_valid_coverage

            if is_valid and np.any(day_mask) and np.any(night_mask):
                t_day = float(np.mean(day_data[day_mask]))
                t_night = float(np.mean(night_data[night_mask]))
                delta_t = t_day - t_night
                meta = getattr(self.moon_diviner_reader, "get_metadata", lambda: {})()
                return {
                    "thermal_valid": True,
                    "thermal_coverage_pct": cov_pct,
                    "thermal_t_day_k": round(t_day, 2),
                    "thermal_t_night_k": round(t_night, 2),
                    "thermal_delta_t_k": round(delta_t, 2),
                    "thermal_inertia_tiu": None,
                    "thermal_metadata": meta,
                }
            else:
                return {
                    "thermal_valid": False,
                    "thermal_coverage_pct": cov_pct,
                    "thermal_t_day_k": None,
                    "thermal_t_night_k": None,
                    "thermal_delta_t_k": None,
                    "thermal_inertia_tiu": None,
                }
        except Exception as e:
            return {"thermal_valid": False, "thermal_coverage_pct": 0.0, "thermal_error": str(e)}

    # -------------------------------------------------------------------------
    # Mars Extraction
    # -------------------------------------------------------------------------

    def extract_mars_tile(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Extracts multi-parameter record for a ~25 km Mars tile centered at (lat, lon).
        """
        tile: PlanetaryTile = self.grids["mars"].get_tile_for_coord(lat, lon)
        half_height = (tile.lat_max - tile.lat_min) / 2.0
        half_width = (tile.lon_max - tile.lon_min) / 2.0
        bbox = (tile.lon_min, tile.lat_min, tile.lon_max, tile.lat_max)

        # Group 1: Real Mars MOLA Terrain
        if self.mars_reader is not None:
            elev_m, valid_mask, valid_ratio = self.mars_reader.read_window_pixels(
                center_lat=tile.lat_center,
                center_lon=tile.lon_center,
                half_width_deg=half_width,
                half_height_deg=half_height,
            )
            geo_metrics = compute_tile_geomorphometry(
                elev_m=elev_m,
                lat_center=tile.lat_center,
                radius_m=MARS_REFERENCE_RADIUS_M,
                pixel_res_deg=1.0 / 16.0,
                native_res_km=3.7045,
                min_valid_ratio=self.min_valid_coverage,
            )
        else:
            geo_metrics = {
                "valid_ratio": 0.0,
                "coverage_pct": 0.0,
                "elevation_mean_m": None,
                "elevation_std_m": None,
                "elevation_min_m": None,
                "elevation_max_m": None,
                "elevation_relief_m": None,
                "slope_mean_deg": None,
                "slope_max_deg": None,
                "aspect_mean_deg": None,
                "roughness_mean_m": None,
                "tpi_mean_m": None,
                "tri_mean_m": None,
            }

        # Group 3: Mars Thermal (THEMIS thermal inertia + TES day/night)
        thermal_metrics = self._load_mars_thermal(tile, half_width, half_height)

        # Group 4: Mars Volatiles (Odyssey GRS WEH + SWIM consistency)
        volatile_metrics = self.mars_volatiles_reader.extract_volatiles(bbox)

        # Group 5: Mars Geological Context & Craters
        geology_unit_metrics = self.mars_geology_aggregator.extract_geology(bbox)
        crater_metrics = self.mars_crater_catalog.query_tile_craters(bbox, tile.actual_area_km2)
        geology_metrics = {**geology_unit_metrics, **crater_metrics}

        record = self._build_multi_parameter_record(
            tile=tile,
            terrain_metrics=geo_metrics,
            thermal_metrics=thermal_metrics,
            volatile_metrics=volatile_metrics,
            geology_metrics=geology_metrics,
            body="mars",
        )
        return record

    def _load_mars_thermal(
        self,
        tile: PlanetaryTile,
        half_width: float,
        half_height: float,
    ) -> Dict[str, Any]:
        """Loads and processes THEMIS thermal inertia and TES temperature for Mars."""
        res: Dict[str, Any] = {
            "thermal_valid": False,
            "thermal_coverage_pct": 0.0,
            "thermal_t_day_k": None,
            "thermal_t_night_k": None,
            "thermal_delta_t_k": None,
            "thermal_inertia_tiu": None,
            "thermal_metadata": {},
        }
        active_covs = []

        # 1. THEMIS Thermal Inertia
        if self.mars_thermis_reader is not None:
            try:
                tiu_data, tiu_mask, tiu_cov = self.mars_thermis_reader.read_window_pixels(
                    center_lat=tile.lat_center,
                    center_lon=tile.lon_center,
                    half_width_deg=half_width,
                    half_height_deg=half_height,
                )
                active_covs.append(tiu_cov)
                if tiu_cov >= self.min_valid_coverage and np.any(tiu_mask):
                    res["thermal_inertia_tiu"] = round(float(np.mean(tiu_data[tiu_mask])), 1)
                meta_tiu = getattr(self.mars_thermis_reader, "get_metadata", lambda: {})()
                res["thermal_metadata"]["themis"] = meta_tiu
            except Exception as e:
                res["thermal_metadata"]["themis_error"] = str(e)

        # 2. MGS TES Day/Night Temperature
        if self.mars_tes_reader is not None:
            try:
                (day_d, day_m), (night_d, night_m), tes_cov = self.mars_tes_reader.read_window_pixels(
                    center_lat=tile.lat_center,
                    center_lon=tile.lon_center,
                    half_width_deg=half_width,
                    half_height_deg=half_height,
                )
                active_covs.append(tes_cov)
                if tes_cov >= self.min_valid_coverage:
                    if day_m is not None and np.any(day_m):
                        res["thermal_t_day_k"] = round(float(np.mean(day_d[day_m])), 2)
                    if night_m is not None and np.any(night_m):
                        res["thermal_t_night_k"] = round(float(np.mean(night_d[night_m])), 2)
                    if res["thermal_t_day_k"] is not None and res["thermal_t_night_k"] is not None:
                        res["thermal_delta_t_k"] = round(res["thermal_t_day_k"] - res["thermal_t_night_k"], 2)
                meta_tes = getattr(self.mars_tes_reader, "get_metadata", lambda: {})()
                res["thermal_metadata"]["tes"] = meta_tes
            except Exception as e:
                res["thermal_metadata"]["tes_error"] = str(e)

        if active_covs:
            mean_cov = float(np.mean(active_covs))
            res["thermal_coverage_pct"] = round(mean_cov * 100.0, 1)
            res["thermal_valid"] = (mean_cov >= self.min_valid_coverage) and (
                res["thermal_inertia_tiu"] is not None or res["thermal_t_day_k"] is not None
            )

        return res

    # -------------------------------------------------------------------------
    # Earth Extraction
    # -------------------------------------------------------------------------

    def extract_earth_tile(self, lat: float, lon: float) -> Dict[str, Any]:
        """
        Extracts multi-parameter record for a ~25 km Earth tile centered at (lat, lon).
        Processes GLiM lithology, MODIS LST, JRC surface water, and PASSC impact structures.
        """
        tile: PlanetaryTile = self.grids["earth"].get_tile_for_coord(lat, lon)
        half_height = (tile.lat_max - tile.lat_min) / 2.0
        half_width = (tile.lon_max - tile.lon_min) / 2.0
        bbox = (tile.lon_min, tile.lat_min, tile.lon_max, tile.lat_max)

        # Group 2: Earth GLiM Lithology
        mineral_metrics = self._load_earth_glim(tile, half_width, half_height)

        # Group 3: Earth MODIS Day/Night Thermal
        thermal_metrics = self._load_earth_thermal(tile, half_width, half_height)

        # Group 4: Earth Water & Cryosphere
        volatile_metrics = self.earth_water_aggregator.extract_water_features(bbox)

        # Group 5: Earth Geological Context & Impact Structures
        geology_unit_metrics = self.earth_geology_aggregator.extract_geology(bbox)
        impact_metrics = self.earth_impact_catalog.query_tile_impacts(bbox)
        geology_metrics = {**geology_unit_metrics, **impact_metrics}

        # Group 1: Real Earth DEM Terrain
        if self.earth_dem_reader is not None:
            try:
                elev_m, valid_mask, valid_ratio = self.earth_dem_reader.read_window_pixels(
                    center_lat=tile.lat_center,
                    center_lon=tile.lon_center,
                    half_width_deg=half_width,
                    half_height_deg=half_height,
                )
                geo_metrics = compute_tile_geomorphometry(
                    elev_m=elev_m,
                    lat_center=tile.lat_center,
                    radius_m=EARTH_VOLUMETRIC_RADIUS_M,
                    pixel_res_deg=1.0 / 60.0,
                    native_res_km=1.853,
                    min_valid_ratio=self.min_valid_coverage,
                )
            except Exception:
                geo_metrics = {
                    "valid_ratio": 0.0,
                    "coverage_pct": 0.0,
                    "native_res_km": 1.853,
                    "effective_res_km": 1.853,
                    "valid_count": 0,
                    "is_valid_coverage": False,
                }
        else:
            geo_metrics = {
                "valid_ratio": 0.0,
                "coverage_pct": 0.0,
                "native_res_km": 1.853,
                "effective_res_km": 1.853,
                "valid_count": 0,
                "is_valid_coverage": False,
            }

        record = self._build_multi_parameter_record(
            tile=tile,
            terrain_metrics=geo_metrics,
            mineral_metrics=mineral_metrics,
            thermal_metrics=thermal_metrics,
            volatile_metrics=volatile_metrics,
            geology_metrics=geology_metrics,
            body="earth",
        )
        return record

    def _load_earth_glim(
        self,
        tile: PlanetaryTile,
        half_width: float,
        half_height: float,
    ) -> Dict[str, Any]:
        """Loads and computes modal lithology and area fraction from GLiM."""
        if self.earth_glim_aggregator is None:
            return {"mineral_valid": False, "mineral_coverage_pct": 0.0}

        try:
            mode_id, fraction = self.earth_glim_aggregator.aggregate_mode(
                center_lat=tile.lat_center,
                center_lon=tile.lon_center,
                half_width_deg=half_width,
                half_height_deg=half_height,
            )
            cov_pct = round(fraction * 100.0, 1)
            is_valid = (mode_id > 0) and (fraction >= 0.10)
            return {
                "mineral_valid": is_valid,
                "mineral_coverage_pct": cov_pct,
                "mineral_lithology_id": mode_id if is_valid else None,
                "mineral_lithology_fraction": round(fraction, 4) if is_valid else None,
            }
        except Exception as e:
            return {"mineral_valid": False, "mineral_coverage_pct": 0.0, "mineral_error": str(e)}

    def _load_earth_thermal(
        self,
        tile: PlanetaryTile,
        half_width: float,
        half_height: float,
    ) -> Dict[str, Any]:
        """Loads MODIS Day/Night LST observations for an Earth tile."""
        if self.earth_modis_reader is None:
            return {"thermal_valid": False, "thermal_coverage_pct": 0.0}

        try:
            (day_d, day_m), (night_d, night_m), cov = self.earth_modis_reader.read_window_pixels(
                center_lat=tile.lat_center,
                center_lon=tile.lon_center,
                half_width_deg=half_width,
                half_height_deg=half_height,
            )
            cov_pct = round(cov * 100.0, 1)
            is_valid = cov >= self.min_valid_coverage

            if is_valid and day_m is not None and np.any(day_m):
                t_day = float(np.mean(day_d[day_m]))
                t_night = float(np.mean(night_d[night_m])) if (night_m is not None and np.any(night_m)) else None
                delta_t = round(t_day - t_night, 2) if t_night is not None else None
                meta = getattr(self.earth_modis_reader, "get_metadata", lambda: {})()
                return {
                    "thermal_valid": True,
                    "thermal_coverage_pct": cov_pct,
                    "thermal_t_day_k": round(t_day, 2),
                    "thermal_t_night_k": round(t_night, 2) if t_night is not None else None,
                    "thermal_delta_t_k": delta_t,
                    "thermal_inertia_tiu": None,
                    "thermal_metadata": meta,
                }
            else:
                return {
                    "thermal_valid": False,
                    "thermal_coverage_pct": cov_pct,
                    "thermal_t_day_k": None,
                    "thermal_t_night_k": None,
                    "thermal_delta_t_k": None,
                    "thermal_inertia_tiu": None,
                }
        except Exception as e:
            return {"thermal_valid": False, "thermal_coverage_pct": 0.0, "thermal_error": str(e)}

    # -------------------------------------------------------------------------
    # Unified Multi-Parameter Record Builder
    # -------------------------------------------------------------------------

    def _build_multi_parameter_record(
        self,
        tile: PlanetaryTile,
        terrain_metrics: Dict[str, Any],
        thermal_metrics: Optional[Dict[str, Any]] = None,
        mineral_metrics: Optional[Dict[str, Any]] = None,
        volatile_metrics: Optional[Dict[str, Any]] = None,
        geology_metrics: Optional[Dict[str, Any]] = None,
        body: str = "moon",
    ) -> Dict[str, Any]:
        """
        Assembles unified multi-parameter dictionary across all 5 groups.
        Strictly obeys the rule: missing data is NEVER treated as zero.
        """
        terrain_cov = terrain_metrics.get("valid_ratio", 0.0)
        thermal_m = thermal_metrics or {}
        mineral_m = mineral_metrics or {}
        volatile_m = volatile_metrics or {}
        geology_m = geology_metrics or {}

        # Calculate composite coverage across active evaluated groups
        active_covs = [terrain_cov * 100.0]
        if "thermal_coverage_pct" in thermal_m:
            active_covs.append(thermal_m["thermal_coverage_pct"])
        if "mineral_coverage_pct" in mineral_m:
            active_covs.append(mineral_m["mineral_coverage_pct"])
        if "volatile_coverage_pct" in volatile_m:
            active_covs.append(volatile_m["volatile_coverage_pct"])
        if "geology_coverage_pct" in geology_m:
            active_covs.append(geology_m["geology_coverage_pct"])

        comp_cov = round(float(np.mean(active_covs)), 1) if active_covs else round(terrain_cov * 100.0, 1)

        record = {
            # Identification & Spatial Geodesy
            "tile_id": tile.tile_id,
            "body": body,
            "lat_center": round(tile.lat_center, 4),
            "lon_center": round(tile.lon_center, 4),
            "lat_min": round(tile.lat_min, 4),
            "lat_max": round(tile.lat_max, 4),
            "lon_min": round(tile.lon_min, 4),
            "lon_max": round(tile.lon_max, 4),
            "actual_area_km2": round(tile.actual_area_km2, 2),
            "native_res_km": terrain_metrics.get("native_res_km", tile.effective_resolution_km),
            "effective_res_km": terrain_metrics.get("effective_res_km", tile.effective_resolution_km),
            "sample_count": terrain_metrics.get("valid_count", 0),

            # Parameter Group 1: Terrain Geomorphometry
            "terrain_valid": terrain_metrics.get("is_valid_coverage", False),
            "terrain_coverage_pct": round(terrain_cov * 100.0, 1),
            "terrain_mean_elevation_m": terrain_metrics.get("mean_elevation_m"),
            "terrain_std_elevation_m": terrain_metrics.get("std_elevation_m"),
            "terrain_local_relief_m": terrain_metrics.get("local_relief_m"),
            "terrain_mean_slope_deg": terrain_metrics.get("mean_slope_deg"),
            "terrain_max_slope_deg": terrain_metrics.get("max_slope_deg"),
            "terrain_roughness_index_m": terrain_metrics.get("terrain_roughness_index_m"),
            "terrain_hypsometric_integral": terrain_metrics.get("hypsometric_integral"),
            "terrain_hypsometric_skewness": terrain_metrics.get("hypsometric_skewness"),

            # Parameter Group 2: Mineralogy & Composition
            "mineral_valid": mineral_m.get("mineral_valid", False),
            "mineral_coverage_pct": mineral_m.get("mineral_coverage_pct", 0.0),
            "mineral_fe_wt_pct": mineral_m.get("mineral_fe_wt_pct"),
            "mineral_ti_wt_pct": mineral_m.get("mineral_ti_wt_pct"),
            "mineral_pyroxene_pct": mineral_m.get("mineral_pyroxene_pct"),
            "mineral_olivine_pct": mineral_m.get("mineral_olivine_pct"),
            "mineral_plagioclase_pct": mineral_m.get("mineral_plagioclase_pct"),
            "mineral_mafic_affinity_index": mineral_m.get("mineral_mafic_affinity_index"),
            "mineral_lithology_id": mineral_m.get("mineral_lithology_id"),
            "mineral_lithology_fraction": mineral_m.get("mineral_lithology_fraction"),

            # Parameter Group 3: Thermophysics
            "thermal_valid": thermal_m.get("thermal_valid", False),
            "thermal_coverage_pct": thermal_m.get("thermal_coverage_pct", 0.0),
            "thermal_t_day_k": thermal_m.get("thermal_t_day_k"),
            "thermal_t_night_k": thermal_m.get("thermal_t_night_k"),
            "thermal_delta_t_k": thermal_m.get("thermal_delta_t_k"),
            "thermal_inertia_tiu": thermal_m.get("thermal_inertia_tiu"),
            "thermal_metadata": thermal_m.get("thermal_metadata", {}),

            # Parameter Group 4: Water, Ice & Volatiles
            "volatile_valid": volatile_m.get("volatile_valid", False),
            "volatile_coverage_pct": volatile_m.get("volatile_coverage_pct", 0.0),
            "volatile_weh_wt_pct": volatile_m.get("volatile_weh_wt_pct"),
            "volatile_weh_is_coarse_scale": volatile_m.get("volatile_weh_is_coarse_scale", False),
            "volatile_weh_effective_resolution_km": volatile_m.get("volatile_weh_effective_resolution_km"),
            "volatile_psr_area_fraction": volatile_m.get("volatile_psr_area_fraction"),
            "mars_swim_ice_consistency_index": volatile_m.get("mars_swim_ice_consistency_index"),
            "volatile_proxy_type": volatile_m.get("volatile_proxy_type", "unspecified"),
            "earth_water_occurrence_pct": volatile_m.get("earth_water_occurrence_pct"),
            "earth_high_occurrence_water_fraction": volatile_m.get("earth_high_occurrence_water_fraction"),
            "earth_glaciated_area_fraction": volatile_m.get("earth_glaciated_area_fraction", volatile_m.get("earth_glacier_area_fraction")),
            "earth_glacier_area_fraction": volatile_m.get("earth_glacier_area_fraction"),
            "earth_perennial_snow_ice_fraction": volatile_m.get("earth_perennial_snow_ice_fraction"),
            "earth_perennial_snow_ice_status": volatile_m.get("earth_perennial_snow_ice_status"),
            "volatile_metadata": volatile_m.get("volatile_metadata", {}),

            # Parameter Group 5: Geological Context & Landforms
            "geology_valid": geology_m.get("geology_valid", False),
            "geology_coverage_pct": geology_m.get("geology_coverage_pct", 0.0),
            "geology_stratigraphic_unit": geology_m.get("geology_stratigraphic_unit"),
            "geology_unit_fraction": geology_m.get("geology_unit_fraction"),
            "geology_stratigraphic_epoch": geology_m.get("geology_stratigraphic_epoch"),
            "crater_raw_count": geology_m.get("crater_raw_count"),
            "crater_ids": geology_m.get("crater_ids"),
            "crater_diameter_min_km": geology_m.get("crater_diameter_min_km"),
            "crater_diameter_max_km": geology_m.get("crater_diameter_max_km"),
            "crater_diameter_median_km": geology_m.get("crater_diameter_median_km"),
            "crater_diameter_mean_km": geology_m.get("crater_diameter_mean_km"),
            "crater_density_n1": geology_m.get("crater_density_n1"),
            "crater_density_n1_sigma": geology_m.get("crater_density_n1_sigma"),
            "crater_density_n5": geology_m.get("crater_density_n5"),
            "crater_density_n5_sigma": geology_m.get("crater_density_n5_sigma"),
            "crater_local_completeness_km": geology_m.get("crater_local_completeness_km"),
            "crater_completeness_flag": geology_m.get("crater_completeness_flag", "unverified_completeness_threshold"),
            "low_count_uncertainty": geology_m.get("low_count_uncertainty"),
            "earth_impact_structure_present": geology_m.get("earth_impact_structure_present"),
            "earth_impact_structure_count": geology_m.get("earth_impact_structure_count"),
            "earth_impact_structure_proximity_km": geology_m.get("earth_impact_structure_proximity_km"),
            "earth_impact_structure_names": geology_m.get("earth_impact_structure_names"),
            "exploratory_crustal_evolution_label": geology_m.get("exploratory_crustal_evolution_label"),
            "geology_metadata": geology_m.get("geology_metadata", {}),

            # Composite Coverage Accounting across active evaluated groups
            "composite_coverage_pct": comp_cov,
        }
        return record
