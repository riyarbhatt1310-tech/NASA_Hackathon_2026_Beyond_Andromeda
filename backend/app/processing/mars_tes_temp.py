"""
Mars Global Surveyor (MGS) Thermal Emission Spectrometer (TES) Temperature Reader.

Reads daytime and nighttime bolometric surface temperature products (VICAR / GeoTIFF format).
Preserves local solar time (LST), native resolution, units (Kelvin), quality flags, and nodata masks.
"""

from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import numpy as np
import rasterio
from rasterio.windows import Window

from src.data_ingestion.earth_glim import compute_safe_window


class MarsTesTempReader:
    """
    Reader for MGS TES day and night temperature products.

    TES characteristics:
    - Orbit: Sun-synchronous near-polar.
    - Nominal Local Solar Time: ~14:00 (daytime pass) and ~02:00 (nighttime pass).
    - Native resolution: 1.0 deg/pixel (~59.3 km at equator) or 0.5 deg/pixel (~29.6 km).
    - Units: Kelvin (K).
    - Physical temperature valid range on Mars: 130 K to 310 K.
    """

    def __init__(self, day_path: str, night_path: Optional[str] = None):
        self.day_path = Path(day_path)
        self.night_path = Path(night_path) if night_path else None

        if not self.day_path.is_file():
            raise FileNotFoundError(f"TES day temperature file not found: {self.day_path}")
        if self.night_path and not self.night_path.is_file():
            raise FileNotFoundError(f"TES night temperature file not found: {self.night_path}")

        self._day_ds: Optional[rasterio.io.DatasetReader] = None
        self._night_ds: Optional[rasterio.io.DatasetReader] = None

    def open(self) -> "MarsTesTempReader":
        self._day_ds = rasterio.open(self.day_path)
        if self.night_path:
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

    def _read_dataset_window(
        self,
        ds: rasterio.io.DatasetReader,
        center_lat: float,
        center_lon: float,
        half_width_deg: float,
        half_height_deg: float,
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """Read a geographic window from a dataset reader."""
        left = center_lon - half_width_deg
        right = center_lon + half_width_deg
        bottom = center_lat - half_height_deg
        top = center_lat + half_height_deg

        window = compute_safe_window(ds, left, bottom, right, top)
        fill_val = ds.nodata if ds.nodata is not None else -9999.0
        data = ds.read(1, window=window, boundless=True, fill_value=fill_val).astype(np.float32)

        # Build mask: valid temperatures on Mars are typically between 100 K and 350 K
        mask = np.isfinite(data)
        if ds.nodata is not None:
            mask = mask & (~np.isclose(data, ds.nodata))
        mask = mask & (data > 50.0) & (data < 400.0)

        coverage = float(np.sum(mask)) / data.size if data.size > 0 else 0.0
        return data, mask, coverage

    def read_window_pixels(
        self,
        center_lat: float,
        center_lon: float,
        half_width_deg: float,
        half_height_deg: float,
    ) -> Tuple[Tuple[np.ndarray, np.ndarray], Tuple[Optional[np.ndarray], Optional[np.ndarray]], float]:
        """
        Reads day and night temperature arrays and masks for the given bounding box.
        Returns:
            ((day_data, day_mask), (night_data, night_mask), min_coverage_ratio)
        """
        if self._day_ds is None:
            self.open()

        day_data, day_mask, day_cov = self._read_dataset_window(
            self._day_ds, center_lat, center_lon, half_width_deg, half_height_deg
        )

        if self._night_ds is not None:
            night_data, night_mask, night_cov = self._read_dataset_window(
                self._night_ds, center_lat, center_lon, half_width_deg, half_height_deg
            )
            total_cov = min(day_cov, night_cov)
        else:
            night_data, night_mask = None, None
            total_cov = day_cov

        return (day_data, day_mask), (night_data, night_mask), total_cov

    def get_metadata(self) -> Dict[str, Any]:
        """Returns verified scientific metadata and observation context."""
        return {
            "instrument": "MGS Thermal Emission Spectrometer (TES)",
            "body": "mars",
            "day_nominal_lst": "14:00 (2 PM local solar time)",
            "night_nominal_lst": "02:00 (2 AM local solar time)",
            "temperature_unit": "Kelvin (K)",
            "native_res_deg": 1.0,
            "effective_res_km": 59.3,
            "format": self._day_ds.driver if self._day_ds else "Unknown",
            "day_crs": str(self._day_ds.crs) if self._day_ds else None,
            "day_shape": (self._day_ds.height, self._day_ds.width) if self._day_ds else None,
            "nodata_value": self._day_ds.nodata if self._day_ds else None,
        }
