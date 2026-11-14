"""
2001 Mars Odyssey THEMIS Global Thermal Inertia Reader.

Reads thermal inertia GeoTIFFs (units: J m^-2 K^-1 s^-1/2, tiu).
Preserves resolution, coordinate systems, quality masks, and valid data bounds.
"""

from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import numpy as np
import rasterio
from rasterio.windows import Window

from src.data_ingestion.earth_glim import compute_safe_window


class MarsThermisReader:
    """Reader for THEMIS global thermal inertia GeoTIFF.
    Returns thermal inertia (TIU) array, validity mask, and coverage ratio.
    """

    def __init__(self, raster_path: str):
        self.path = Path(raster_path)
        if not self.path.is_file():
            raise FileNotFoundError(f"THEMIS thermal inertia file not found: {self.path}")
        self._ds: Optional[rasterio.io.DatasetReader] = None

    def open(self) -> "MarsThermisReader":
        self._ds = rasterio.open(self.path)
        return self

    def close(self) -> None:
        if self._ds and not self._ds.closed:
            self._ds.close()
        self._ds = None

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _read_window(
        self,
        center_lat: float,
        center_lon: float,
        half_width_deg: float,
        half_height_deg: float,
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        left = center_lon - half_width_deg
        right = center_lon + half_width_deg
        bottom = center_lat - half_height_deg
        top = center_lat + half_height_deg

        window = compute_safe_window(self._ds, left, bottom, right, top)
        fill_val = self._ds.nodata if self._ds.nodata is not None else -9999.0
        data = self._ds.read(1, window=window, boundless=True, fill_value=fill_val).astype(np.float32)

        mask = np.isfinite(data)
        if self._ds.nodata is not None:
            mask = mask & (~np.isclose(data, self._ds.nodata))
        # Valid thermal inertia on Mars is typically 10 to 2000 tiu
        mask = mask & (data > 0.0) & (data < 2500.0)

        coverage = float(np.sum(mask)) / data.size if data.size > 0 else 0.0
        return data, mask, coverage

    def read_window_pixels(
        self,
        center_lat: float,
        center_lon: float,
        half_width_deg: float,
        half_height_deg: float,
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """Return thermal inertia array, mask, and coverage ratio."""
        if self._ds is None:
            self.open()
        return self._read_window(center_lat, center_lon, half_width_deg, half_height_deg)

    def get_metadata(self) -> Dict[str, Any]:
        """Returns verified scientific metadata and observation context."""
        return {
            "instrument": "2001 Mars Odyssey THEMIS",
            "body": "mars",
            "parameter": "Thermal Inertia",
            "unit": "J m^-2 K^-1 s^-1/2 (tiu)",
            "native_res_m": 100.0,
            "effective_res_km": 7.4,
            "format": self._ds.driver if self._ds else "Unknown",
            "crs": str(self._ds.crs) if self._ds else None,
            "shape": (self._ds.height, self._ds.width) if self._ds else None,
            "nodata_value": self._ds.nodata if self._ds else None,
        }
