"""
Earth MODIS Land Surface Temperature (LST) Reader.

Supports MODIS Terra (MOD11A1 / MOD11A2) and Aqua (MYD11A1 / MYD11A2) products.
Preserves day/night observations, observation dates, local solar times, quality flags (QC),
native resolution (1 km), and scale factor calibration (DN * 0.02 -> Kelvin).
"""

from pathlib import Path
from typing import Tuple, Dict, Any, Optional
import numpy as np
import rasterio
from rasterio.windows import Window

from src.data_ingestion.earth_glim import compute_safe_window


class ModisLSTReader:
    """
    Reader for MODIS Land Surface Temperature products (MOD11A1 Terra, MYD11A1 Aqua).

    Sensor Characteristics:
    - Terra: Equatorial crossing ~10:30 (Day) and ~22:30 (Night).
    - Aqua: Equatorial crossing ~13:30 (Day) and ~01:30 (Night).
    - Native Resolution: 1 km (approx. 0.00833 deg).
    - Scale Factor: 0.02 (for raw 16-bit unsigned integer products).
    - Valid Earth LST Range: 200.0 K (-73.15 C) to 345.0 K (+71.85 C).
    - Missing/Cloud: Nodata value 0 in raw uint16 DN or NaN in float.
    """

    def __init__(
        self,
        day_path: str,
        night_path: Optional[str] = None,
        qc_day_path: Optional[str] = None,
        qc_night_path: Optional[str] = None,
        satellite: str = "Terra",
        is_scaled_dn: bool = True,
    ):
        self.day_path = Path(day_path)
        self.night_path = Path(night_path) if night_path else None
        self.qc_day_path = Path(qc_day_path) if qc_day_path else None
        self.qc_night_path = Path(qc_night_path) if qc_night_path else None
        self.satellite = satellite
        self.is_scaled_dn = is_scaled_dn

        if not self.day_path.is_file():
            raise FileNotFoundError(f"MODIS day LST file not found: {self.day_path}")
        if self.night_path and not self.night_path.is_file():
            raise FileNotFoundError(f"MODIS night LST file not found: {self.night_path}")

        self._day_ds: Optional[rasterio.io.DatasetReader] = None
        self._night_ds: Optional[rasterio.io.DatasetReader] = None
        self._qc_day_ds: Optional[rasterio.io.DatasetReader] = None
        self._qc_night_ds: Optional[rasterio.io.DatasetReader] = None

    def open(self) -> "ModisLSTReader":
        self._day_ds = rasterio.open(self.day_path)
        if self.night_path:
            self._night_ds = rasterio.open(self.night_path)
        if self.qc_day_path and self.qc_day_path.is_file():
            self._qc_day_ds = rasterio.open(self.qc_day_path)
        if self.qc_night_path and self.qc_night_path.is_file():
            self._qc_night_ds = rasterio.open(self.qc_night_path)
        return self

    def close(self) -> None:
        for ds in [self._day_ds, self._night_ds, self._qc_day_ds, self._qc_night_ds]:
            if ds and not ds.closed:
                ds.close()
        self._day_ds = None
        self._night_ds = None
        self._qc_day_ds = None
        self._qc_night_ds = None

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _read_window_raw(
        self,
        ds: rasterio.io.DatasetReader,
        center_lat: float,
        center_lon: float,
        half_width_deg: float,
        half_height_deg: float,
        qc_ds: Optional[rasterio.io.DatasetReader] = None,
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """Reads a geographic window, applies scale factor, QC flags, and validity mask."""
        left = center_lon - half_width_deg
        right = center_lon + half_width_deg
        bottom = center_lat - half_height_deg
        top = center_lat + half_height_deg

        window = compute_safe_window(ds, left, bottom, right, top)
        raw = ds.read(1, window=window, boundless=True, fill_value=ds.nodata or 0)

        # Convert DN to Kelvin using MODIS 0.02 scale factor if raw uint16
        if self.is_scaled_dn and np.issubdtype(raw.dtype, np.integer):
            valid_dn = (raw > 0)
            data = np.where(valid_dn, raw.astype(np.float32) * 0.02, np.nan)
        else:
            data = raw.astype(np.float32)

        # Basic physical validity mask for Earth surface temperature (200 K to 345 K)
        mask = np.isfinite(data) & (data >= 200.0) & (data <= 345.0)

        # Check QC mask if provided (MODIS QC bits 0-1: 0 = LST produced, good quality)
        if qc_ds is not None:
            qc_window = compute_safe_window(qc_ds, left, bottom, right, top)
            qc_raw = qc_ds.read(1, window=qc_window, boundless=True, fill_value=255)
            qc_valid = (qc_raw & 0b11) <= 1
            mask = mask & qc_valid

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
        Reads day and night temperature arrays and masks for the bounding box.
        Returns:
            ((day_data, day_mask), (night_data, night_mask), min_coverage_ratio)
        """
        if self._day_ds is None:
            self.open()

        day_data, day_mask, day_cov = self._read_window_raw(
            self._day_ds, center_lat, center_lon, half_width_deg, half_height_deg, self._qc_day_ds
        )

        if self._night_ds is not None:
            night_data, night_mask, night_cov = self._read_window_raw(
                self._night_ds, center_lat, center_lon, half_width_deg, half_height_deg, self._qc_night_ds
            )
            total_cov = min(day_cov, night_cov)
        else:
            night_data, night_mask = None, None
            total_cov = day_cov

        return (day_data, day_mask), (night_data, night_mask), total_cov

    def get_metadata(self) -> Dict[str, Any]:
        """Returns verified scientific metadata and observation context."""
        nominal_lst_day = "10:30 LST" if self.satellite.lower() == "terra" else "13:30 LST"
        nominal_lst_night = "22:30 LST" if self.satellite.lower() == "terra" else "01:30 LST"
        return {
            "instrument": f"MODIS {self.satellite}",
            "body": "earth",
            "day_nominal_lst": nominal_lst_day,
            "night_nominal_lst": nominal_lst_night,
            "temperature_unit": "Kelvin (K)",
            "native_res_km": 1.0,
            "scale_factor": 0.02 if self.is_scaled_dn else 1.0,
            "format": self._day_ds.driver if self._day_ds else "Unknown",
            "crs": str(self._day_ds.crs) if self._day_ds else None,
            "shape": (self._day_ds.height, self._day_ds.width) if self._day_ds else None,
            "nodata_value": self._day_ds.nodata if self._day_ds else None,
        }
