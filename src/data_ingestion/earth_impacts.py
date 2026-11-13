"""Earth Impact Database Catalog for TerraTwin.

Queries Planetary and Space Science Centre (PASSC) Earth Impact Database (EID).
Features:
1. Impact structure presence and count in tile.
2. Distance to nearest confirmed hypervelocity impact structure (km).
3. Names of intersecting impact structures.
4. Strictly sets crater_density_n1 to None (cumulative crater chronometry is scientifically invalid on Earth).
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import json
import numpy as np


class EarthImpactCatalog:
    """Queries confirmed terrestrial impact structures from PASSC EID."""

    def __init__(self, geojson_path: Optional[str] = None):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.geojson_file = Path(geojson_path) if geojson_path else (
            base_dir / "data" / "raw" / "earth" / "geology" / "earth_impact_database.geojson"
        )
        self.structures = []
        self._load_structures()

    def _load_structures(self) -> None:
        """Load structures from GeoJSON."""
        if not self.geojson_file.exists():
            return

        try:
            with open(self.geojson_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for feat in data.get("features", []):
                    geom = feat.get("geometry", {})
                    props = feat.get("properties", {})
                    coords = geom.get("coordinates", [])
                    if len(coords) >= 2:
                        self.structures.append({
                            "name": props.get("name", "Unknown"),
                            "lon": coords[0],
                            "lat": coords[1],
                            "diameter_km": props.get("diameter_km", 0.0),
                            "age_myr": props.get("age_myr", 0.0)
                        })
        except Exception:
            self.structures = []

    def query_tile_impacts(
        self,
        bbox: Tuple[float, float, float, float]
    ) -> Dict[str, Any]:
        """Query terrestrial impact structures for a 25 km tile."""
        min_lon, min_lat, max_lon, max_lat = bbox
        center_lat = (min_lat + max_lat) / 2.0
        center_lon = (min_lon + max_lon) / 2.0

        # Standardize longitudes to [-180, 180]
        if min_lon > 180.0:
            min_lon -= 360.0
        if max_lon > 180.0:
            max_lon -= 360.0
        if center_lon > 180.0:
            center_lon -= 360.0
        if min_lon > max_lon:
            min_lon, max_lon = min(min_lon, max_lon), max(min_lon, max_lon)

        if not self.structures:
            return {
                "earth_impact_structure_present": False,
                "earth_impact_structure_count": 0,
                "earth_impact_structure_proximity_km": None,
                "earth_impact_structure_names": [],
                "crater_density_n1": None,
                "crater_density_n1_sigma": None,
                "crater_density_n5": None,
                "crater_density_n5_sigma": None,
                "crater_raw_count": 0,
                "crater_ids": [],
                "crater_local_completeness_km": None,
                "crater_completeness_flag": "not_applicable_to_earth",
                "low_count_uncertainty": None
            }

        in_tile_names = []
        min_dist_km = float("inf")

        # Earth mean radius for haversine distance
        R_EARTH = 6371.0

        for s in self.structures:
            s_lat = s["lat"]
            s_lon = s["lon"]
            if s_lon > 180.0:
                s_lon -= 360.0

            # Bounding box check
            if min_lat <= s_lat <= max_lat and min_lon <= s_lon <= max_lon:
                in_tile_names.append(s["name"])

            # Great circle distance
            dlat = np.radians(s_lat - center_lat)
            dlon_deg = (s_lon - center_lon + 180.0) % 360.0 - 180.0
            dlon = np.radians(dlon_deg)
            a = (np.sin(dlat / 2.0)**2 +
                 np.cos(np.radians(center_lat)) * np.cos(np.radians(s_lat)) * np.sin(dlon / 2.0)**2)
            c = 2.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a))
            dist_km = R_EARTH * c

            if dist_km < min_dist_km:
                min_dist_km = dist_km

        present = len(in_tile_names) > 0
        proximity = float(min_dist_km) if min_dist_km < float("inf") else None

        return {
            "earth_impact_structure_present": present,
            "earth_impact_structure_count": len(in_tile_names),
            "earth_impact_structure_proximity_km": round(proximity, 2) if proximity is not None else None,
            "earth_impact_structure_names": in_tile_names,
            "crater_density_n1": None,  # Strictly None for Earth
            "crater_density_n1_sigma": None,
            "crater_density_n5": None,
            "crater_density_n5_sigma": None,
            "crater_raw_count": len(in_tile_names),
            "crater_ids": in_tile_names,
            "crater_local_completeness_km": None,
            "crater_completeness_flag": "not_applicable_to_earth",
            "low_count_uncertainty": None
        }
