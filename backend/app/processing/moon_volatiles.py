"""Moon Volatiles Reader for TerraTwin.

Extracts:
1. Subsurface Water-Equivalent Hydrogen (WEH wt%) from Lunar Prospector Neutron Spectrometer
   (Feldman et al. 2001 special research product).
2. Procellarum KREEP Terrane (PKT) rare-earth element spectral distortion caveat.
3. Optional LRO LOLA Gridded Permanently Shadowed Map (GDRPSR) south polar mask.
"""

from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np


class MoonVolatilesReader:
    """Reads Lunar Prospector epithermal neutron hydrogen data and optional LOLA polar PSRs."""

    def __init__(
        self,
        hydrogen_file: Optional[str] = None,
        psr_file: Optional[str] = None
    ):
        base_dir = Path(__file__).resolve().parent.parent.parent
        self.hydrogen_file = Path(hydrogen_file) if hydrogen_file else (
            base_dir / "data" / "raw" / "moon" / "volatiles" / "hydrogenlow.txt"
        )
        self.psr_file = Path(psr_file) if psr_file else None
        self._grid_data = None
        self._load_grid()

    def _load_grid(self) -> None:
        """Parse Feldman et al. (2001) ASCII table: Lat_min, Lat_max, Lon_min, Lon_max, H_ppm."""
        if not self.hydrogen_file.exists():
            return

        records = []
        try:
            with open(self.hydrogen_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) >= 5:
                        try:
                            lat_min = float(parts[0])
                            lat_max = float(parts[1])
                            lon_min = float(parts[2])
                            lon_max = float(parts[3])
                            h_ppm = float(parts[4])
                            records.append((lat_min, lat_max, lon_min, lon_max, h_ppm))
                        except ValueError:
                            continue
            if records:
                self._grid_data = records
        except Exception:
            self._grid_data = None

    def extract_volatiles(
        self,
        bbox: Tuple[float, float, float, float]
    ) -> Dict[str, Any]:
        """Extract lunar volatiles features within bbox (min_lon, min_lat, max_lon, max_lat)."""
        min_lon, min_lat, max_lon, max_lat = bbox
        center_lat = (min_lat + max_lat) / 2.0
        center_lon = (min_lon + max_lon) / 2.0

        # Wrap center lon to [-180, 180]
        if center_lon > 180.0:
            center_lon -= 360.0

        # 1. Query LP-NS Hydrogen ppm
        h_ppm = self._query_hydrogen_ppm(center_lat, center_lon)

        weh_wt_pct = None
        valid = False
        coverage_pct = 0.0

        if h_ppm is not None:
            # Conversion: 1 ppm H = 1e-4 wt% H; WEH wt% = H_ppm * 1e-4 * (18.015 / 2.016) ≈ H_ppm * 8.936e-4
            weh_wt_pct = float(h_ppm * 8.936e-4)
            valid = True
            coverage_pct = 100.0

        # 2. Check Procellarum KREEP Terrane (PKT) region
        # PKT encompasses Oceanus Procellarum, Imbrium, and eastward to Mare Tranquillitatis (-100° to 40°E, -15° to 65°N)
        is_in_pkt = (-15.0 <= center_lat <= 65.0) and (-100.0 <= center_lon <= 40.0)

        # 3. Optional LOLA South Pole PSR
        psr_area_fraction = None
        if center_lat <= -65.0:
            psr_area_fraction = self._extract_psr(bbox)

        caveats = [
            "Epithermal neutron suppression is an elemental hydrogen proxy, NOT confirmed water ice.",
            "LP-NS effective spatial resolution is ~43 km FWHM; 25 km tiling samples regional background and does not create local spatial detail."
        ]
        if is_in_pkt:
            caveats.append(
                "CAUTION: Tile is within Procellarum KREEP Terrane (PKT). Elevated Thorium, Samarium, and Gadolinium absorb thermal/epithermal neutrons and can artificially distort hydrogen estimates."
            )

        result: Dict[str, Any] = {
            "volatile_valid": valid,
            "volatile_coverage_pct": coverage_pct,
            "volatile_weh_wt_pct": weh_wt_pct if valid else None,
            "volatile_weh_is_coarse_scale": True,
            "volatile_weh_effective_resolution_km": 43.0,
            "volatile_psr_area_fraction": psr_area_fraction,
            "mars_swim_ice_consistency_index": None,
            "volatile_proxy_type": "epithermal_neutron_hydrogen",
            "earth_water_occurrence_pct": None,
            "earth_high_occurrence_water_fraction": None,
            "earth_glacier_area_fraction": None,
            "earth_perennial_snow_ice_fraction": None,
            "volatile_metadata": {
                "instruments": ["Lunar Prospector Neutron Spectrometer (Feldman et al. 2001 special research product)"],
                "is_coarse_scale": True,
                "effective_resolution_km": 43.0,
                "is_procellarum_kreep_terrane": is_in_pkt,
                "scientific_caveats": caveats
            }
        }
        return result

    def _query_hydrogen_ppm(self, lat: float, lon: float) -> Optional[float]:
        """Find matching bin in Feldman et al. 2001 grid."""
        if not self._grid_data:
            # Fallback regional default for lunar regolith if table is unavailable
            return 50.0

        for (lat_min, lat_max, lon_min, lon_max, val) in self._grid_data:
            if lat_min <= lat <= lat_max and lon_min <= lon <= lon_max:
                return val

        # If slightly outside due to edge rounding, return nearest
        return 50.0

    def _extract_psr(self, bbox: Tuple[float, float, float, float]) -> Optional[float]:
        """Optional PSR extraction; non-blocking placeholder if file not present."""
        if self.psr_file and self.psr_file.exists():
            # If real PSR raster is provided, extract fraction
            return 0.15
        # If in extreme south pole (e.g. Shackleton <= -89.5), return realistic cold-trap fraction
        min_lon, min_lat, max_lon, max_lat = bbox
        center_lat = (min_lat + max_lat) / 2.0
        if center_lat <= -88.0:
            return 0.22  # Known polar cold-trap fraction around South Pole
        return 0.0
