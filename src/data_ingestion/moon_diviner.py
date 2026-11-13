"""
LRO Diviner Lunar Radiometer Experiment Thermal Reader.

Reads daytime and nighttime bolometric temperature products.
Preserves native resolution, units (Kelvin), valid masks, and quality metrics.
"""

from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import numpy as np
import rasterio
from rasterio.windows import Window

from src.data_ingestion.earth_glim import compute_safe_window


class MoonDivinerReader:
    """Reader for LRO Diviner global daytime and nighttime temperature GeoTIFFs.
    Expects two GeoTIFF files (day and night) located in the configured thermal directory.
    Returns temperature in Kelvin and a validity mask.
    """

    def __init__(self, day_path: str, night_path: str):
        self.day_path = Path(day_path)
        self.night_path = Path(night_path)
        if not self.day_path.is_file():
            raise FileNotFoundError(f"Diviner day temperature file not found: {self.day_path}")
        if not self.night_path.is_file():
            raise FileNotFoundError(f"Diviner night temperature file not found: {self.night_path}")
        self._day_ds: Optional[rasterio.io.DatasetReader] = None
        self._night_ds: Optional[rasterio.io.DatasetReader] = None

    def open(self) -> "MoonDivinerReader":
        self._day_ds = rasterio.open(self.day_path)
        self._night_ds = rasterio.open(self.night_path)
        return self

    def close(self) -> None:
        if self._day_ds and not self._day_ds.closed:
            self._day_ds.close()
        if self._night_ds and not self._night_ds.closed:
            self._night_ds.close()
        self._day_ds = None
        self._night_ds = None

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _read_window(
        self,
        ds: rasterio.io.DatasetReader,
        center_lat: float,
        center_lon: float,
        half_width_deg: float,
        half_height_deg: float,
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        left = center_lon - half_width_deg
        right = center_lon + half_width_deg
        bottom = center_lat - half_height_deg
        top = center_lat + half_height_deg

        window = compute_safe_window(ds, left, bottom, right, top)
        fill_val = ds.nodata if ds.nodata is not None else -9999.0
        data = ds.read(1, window=window, boundless=True, fill_value=fill_val).astype(np.float32)

        mask = np.isfinite(data)
        if ds.nodata is not None:
            mask = mask & (~np.isclose(data, ds.nodata))
        mask = mask & (data > 10.0) & (data < 450.0)

        coverage = float(np.sum(mask)) / data.size if data.size > 0 else 0.0
        return data, mask, coverage

    def read_window_pixels(
        self,
        center_lat: float,
        center_lon: float,
        half_width_deg: float,
        half_height_deg: float,
    ) -> Tuple[Tuple[np.ndarray, np.ndarray], Tuple[np.ndarray, np.ndarray], float]:
        """Return day and night temperature arrays and masks.
        Output format: ((day_data, day_mask), (night_data, night_mask), coverage_ratio)
        """
        if self._day_ds is None or self._night_ds is None:
            self.open()
        day_data, day_mask, day_cov = self._read_window(
            self._day_ds, center_lat, center_lon, half_width_deg, half_height_deg
        )
        night_data, night_mask, night_cov = self._read_window(
            self._night_ds, center_lat, center_lon, half_width_deg, half_height_deg
        )
        coverage = min(day_cov, night_cov)
        return (day_data, day_mask), (night_data, night_mask), coverage

    def get_metadata(self) -> Dict[str, Any]:
        """Returns verified scientific metadata and observation context."""
        return {
            "instrument": "LRO Diviner Lunar Radiometer Experiment",
            "body": "moon",
            "day_nominal_lst": "Diurnal Maximum Bolometric (local noon)",
            "night_nominal_lst": "Diurnal Minimum Bolometric (local midnight)",
            "temperature_unit": "Kelvin (K)",
            "native_res_km": 15.0,
            "format": self._day_ds.driver if self._day_ds else "Unknown",
            "crs": str(self._day_ds.crs) if self._day_ds else None,
            "shape": (self._day_ds.height, self._day_ds.width) if self._day_ds else None,
            "nodata_value": self._day_ds.nodata if self._day_ds else None,
        }
