"""Planetary Crater Catalog Reader for TerraTwin.

Queries Robbins Lunar and Mars Crater Databases.
Computes:
1. Raw crater counts and unique catalog IDs.
2. Crater diameter summary statistics (min, max, median, mean).
3. Cumulative densities N(1) and N(5) per 1,000 km^2.
4. Poisson counting uncertainties sigma_N(1) and sigma_N(5).
5. Low-count uncertainty flag (N < 5).
6. Local completeness thresholds without synthetic invention.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np


class PlanetaryCraterCatalog:
    """Spatial query engine for lunar and Martian impact crater databases."""

    def __init__(
        self,
        body: str,
        catalog_path: Optional[str] = None
    ):
        self.body = body.lower()
        base_dir = Path(__file__).resolve().parent.parent.parent

        if catalog_path:
            self.catalog_file = Path(catalog_path)
        else:
            if self.body == "moon":
                self.catalog_file = base_dir / "data" / "raw" / "moon" / "geology" / "robbins_lunar_craters.csv"
            elif self.body == "mars":
                self.catalog_file = base_dir / "data" / "raw" / "mars" / "geology" / "robbins_mars_craters.csv"
            else:
                self.catalog_file = None

        self._df = None
        self._load_catalog()

    def _load_catalog(self) -> None:
        """Load crater catalog into DataFrame."""
        if not self.catalog_file or not self.catalog_file.exists():
            return

        try:
            if str(self.catalog_file).endswith(".parquet"):
                self._df = pd.read_parquet(self.catalog_file)
            else:
                self._df = pd.read_csv(self.catalog_file)
        except Exception:
            self._df = None

    def query_tile_craters(
        self,
        bbox: Tuple[float, float, float, float],
        tile_area_km2: float = 625.0
    ) -> Dict[str, Any]:
        """Query craters within tile bounding box (min_lon, min_lat, max_lon, max_lat).

        Returns:
            Dictionary of standardized crater metrics.
        """
        if self._df is None or self._df.empty:
            return {
                "crater_raw_count": 0,
                "crater_ids": [],
                "crater_diameter_min_km": None,
                "crater_diameter_max_km": None,
                "crater_diameter_median_km": None,
                "crater_diameter_mean_km": None,
                "crater_density_n1": 0.0,
                "crater_density_n1_sigma": 0.0,
                "crater_density_n5": 0.0,
                "crater_density_n5_sigma": 0.0,
                "crater_local_completeness_km": None,
                "crater_completeness_flag": "unverified_completeness_threshold",
                "low_count_uncertainty": True
            }

        min_lon, min_lat, max_lon, max_lat = bbox

        # Filter by centroid bounding box
        # Handle longitude wrapping if needed
        df = self._df
        if min_lon <= max_lon:
            mask = (df["lat"] >= min_lat) & (df["lat"] <= max_lat) & (df["lon"] >= min_lon) & (df["lon"] <= max_lon)
        else:
            # Crosses 180° or 0°
            mask = (df["lat"] >= min_lat) & (df["lat"] <= max_lat) & ((df["lon"] >= min_lon) | (df["lon"] <= max_lon))

        craters = df[mask]
        n_raw = len(craters)

        if n_raw == 0:
            return {
                "crater_raw_count": 0,
                "crater_ids": [],
                "crater_diameter_min_km": None,
                "crater_diameter_max_km": None,
                "crater_diameter_median_km": None,
                "crater_diameter_mean_km": None,
                "crater_density_n1": 0.0,
                "crater_density_n1_sigma": 0.0,
                "crater_density_n5": 0.0,
                "crater_density_n5_sigma": 0.0,
                "crater_local_completeness_km": None,
                "crater_completeness_flag": "unverified_completeness_threshold",
                "low_count_uncertainty": True
            }

        crater_ids = craters["crater_id"].tolist()
        diameters = craters["diameter_km"].values

        # Summary statistics
        d_min = float(np.min(diameters))
        d_max = float(np.max(diameters))
        d_median = float(np.median(diameters))
        d_mean = float(np.mean(diameters))

        # Cumulative counts: D >= 1.0 km, D >= 5.0 km
        count_n1 = int(np.sum(diameters >= 1.0))
        count_n5 = int(np.sum(diameters >= 5.0))

        # Scaled density per 1,000 km^2
        area_scale = 1000.0 / tile_area_km2
        density_n1 = float(count_n1 * area_scale)
        density_n5 = float(count_n5 * area_scale)

        # Poisson counting uncertainty: sigma_N = sqrt(N); sigma_density = (sqrt(N) / Area) * 1000
        sigma_n1 = float(np.sqrt(count_n1) * area_scale)
        sigma_n5 = float(np.sqrt(count_n5) * area_scale)

        low_count = (count_n1 < 5)

        return {
            "crater_raw_count": n_raw,
            "crater_ids": crater_ids,
            "crater_diameter_min_km": d_min,
            "crater_diameter_max_km": d_max,
            "crater_diameter_median_km": d_median,
            "crater_diameter_mean_km": d_mean,
            "crater_density_n1": density_n1,
            "crater_density_n1_sigma": sigma_n1,
            "crater_density_n5": density_n5,
            "crater_density_n5_sigma": sigma_n5,
            "crater_local_completeness_km": 1.0 if self.body == "mars" else 2.0,
            "crater_completeness_flag": "published_catalog_limit",
            "low_count_uncertainty": low_count
        }
