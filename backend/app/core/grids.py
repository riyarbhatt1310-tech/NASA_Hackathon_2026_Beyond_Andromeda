"""
Planetary Spatial Grid Generator for TerraTwin.

Constructs equal-physical-area analysis tiles (~25 km x 25 km, ~625 km^2)
accounting for each planetary body's true radius and latitude-dependent
metric longitudinal scaling (R * cos(phi) * dLambda).
"""

import math
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass

from src.core.constants import (
    EARTH_VOLUMETRIC_RADIUS_M,
    MOON_REFERENCE_RADIUS_M,
    MARS_REFERENCE_RADIUS_M,
    ANALYSIS_TILE_SIZE_KM,
)


@dataclass
class PlanetaryTile:
    """Represents a discrete physical analysis tile on a planetary body."""
    tile_id: str
    body: str
    lat_center: float
    lon_center: float
    lat_min: float
    lat_max: float
    lon_min: float
    lon_max: float
    target_area_km2: float
    actual_area_km2: float
    effective_resolution_km: float


class PlanetaryGrid:
    """
    Generates and queries a common physical-area grid across planetary bodies.
    """

    RADIUS_MAP_KM = {
        "earth": EARTH_VOLUMETRIC_RADIUS_M / 1000.0,
        "moon": MOON_REFERENCE_RADIUS_M / 1000.0,
        "mars": MARS_REFERENCE_RADIUS_M / 1000.0,
    }

    # Sensor native resolution in km at the equator
    NATIVE_RESOLUTION_MAP_KM = {
        "earth": 0.030,   # Copernicus GLO-30 (~30 m)
        "moon": 1.8952,   # LOLA LDEM_16 (~1.9 km)
        "mars": 3.7045,   # MOLA MEGDR (~3.7 km)
    }

    def __init__(self, body: str, target_tile_size_km: float = ANALYSIS_TILE_SIZE_KM):
        body_lower = body.lower()
        if body_lower not in self.RADIUS_MAP_KM:
            raise ValueError(f"Unknown planetary body: '{body}'. Must be one of {list(self.RADIUS_MAP_KM.keys())}")

        self.body = body_lower
        self.radius_km = self.RADIUS_MAP_KM[body_lower]
        self.target_tile_size_km = target_tile_size_km
        self.target_area_km2 = target_tile_size_km * target_tile_size_km
        self.native_res_km = self.NATIVE_RESOLUTION_MAP_KM[body_lower]

        # Calculate latitudinal strip height in degrees
        # Arc length s = R * theta (radians) -> theta = s / R
        delta_lat_rad = self.target_tile_size_km / self.radius_km
        delta_lat_deg = math.degrees(delta_lat_rad)
        self.num_lat_bands = max(2, int(round(180.0 / delta_lat_deg)))
        self.actual_delta_lat_deg = 180.0 / self.num_lat_bands

    def compute_spherical_tile_area_km2(
        self, lat_min_deg: float, lat_max_deg: float, lon_width_deg: float
    ) -> float:
        """
        Calculates the true physical area on a spherical body between two latitudes:
        Area = R^2 * (sin(lat2) - sin(lat1)) * delta_lon_radians
        """
        phi1 = math.radians(lat_min_deg)
        phi2 = math.radians(lat_max_deg)
        d_lambda = math.radians(lon_width_deg)
        area = (self.radius_km ** 2) * abs(math.sin(phi2) - math.sin(phi1)) * d_lambda
        return area

    def get_tile_for_coord(self, lat: float, lon: float) -> PlanetaryTile:
        """
        Finds the exact discrete physical analysis tile bounding (lat, lon).
        """
        if not -90.0 <= lat <= 90.0:
            raise ValueError(f"Latitude must be between -90 and +90, got {lat}")

        lon_norm = lon % 360.0

        # Lat band index (0 at +90 deg N, down to num_lat_bands - 1 at -90 deg S)
        lat_from_north = 90.0 - lat
        band_idx = int(lat_from_north / self.actual_delta_lat_deg)
        band_idx = min(band_idx, self.num_lat_bands - 1)

        lat_max = min(90.0, 90.0 - band_idx * self.actual_delta_lat_deg)
        lat_min = max(-90.0, lat_max - self.actual_delta_lat_deg)
        if band_idx == self.num_lat_bands - 1:
            lat_min = -90.0
        lat_center = (lat_min + lat_max) / 2.0

        # Total physical area of this spherical latitude band:
        # A_band = 2 * pi * R^2 * |sin(lat_max) - sin(lat_min)|
        phi_min_rad = math.radians(lat_min)
        phi_max_rad = math.radians(lat_max)
        band_area_km2 = 2.0 * math.pi * (self.radius_km ** 2) * abs(math.sin(phi_max_rad) - math.sin(phi_min_rad))

        # Optimal integer number of cells to achieve target_area_km2 (625 km^2)
        num_lon_cells = max(1, int(round(band_area_km2 / self.target_area_km2)))
        actual_delta_lon_deg = 360.0 / num_lon_cells

        lon_idx = int(lon_norm / actual_delta_lon_deg)
        lon_idx = min(lon_idx, num_lon_cells - 1)

        lon_min = lon_idx * actual_delta_lon_deg
        lon_max = lon_min + actual_delta_lon_deg
        lon_center = (lon_min + lon_max) / 2.0

        actual_area = self.compute_spherical_tile_area_km2(lat_min, lat_max, actual_delta_lon_deg)
        tile_id = f"{self.body}_{lat_center:+.2f}_{lon_center:.2f}"

        return PlanetaryTile(
            tile_id=tile_id,
            body=self.body,
            lat_center=lat_center,
            lon_center=lon_center,
            lat_min=lat_min,
            lat_max=lat_max,
            lon_min=lon_min,
            lon_max=lon_max,
            target_area_km2=self.target_area_km2,
            actual_area_km2=actual_area,
            effective_resolution_km=self.native_res_km,
        )

    def generate_sample_tiles(self, count_per_band: int = 4) -> List[PlanetaryTile]:
        """Generates representative spatial tiles across equatorial, mid-latitude, and polar bands."""
        tiles = []
        sample_lats = [0.0, 30.0, -30.0, 60.0, -60.0, 85.0, -85.0]
        for lat in sample_lats:
            for i in range(count_per_band):
                lon = (360.0 / count_per_band) * i
                tiles.append(self.get_tile_for_coord(lat, lon))
        return tiles
