"""
Lunar Mineral Extraction: Inversion of TiO2 from Clementine UVVIS observations.
"""

import rasterio
import numpy as np
from pathlib import Path
from typing import Tuple, Optional

from src.processing.ti_calibration import tio2_lucey2000, tio2_legacy_linear


class MoonTiO2Extractor:
    """
    Derive TiO2 weight-percent from Clementine UVVIS color ratios.

    Uses the peer-reviewed Lucey et al. (2000) calibration:
        theta_Ti = arctan(((R415 / R750) - 0.42) / (R750 - 0.00))
        TiO2 (wt%) = 3.708 * (theta_Ti ** 5.979)

    If only pre-computed 750/415 ratio bands are available, falls back to
    calibrated inversion with quality flagging.
    """

    def __init__(self, mosaic_path: str, use_lucey2000: bool = True):
        self.mosaic_path = Path(mosaic_path)
        if not self.mosaic_path.is_file():
            raise FileNotFoundError(f"UVVIS mosaic not found at {self.mosaic_path}")
        self.dataset = rasterio.open(self.mosaic_path)
        self.use_lucey2000 = use_lucey2000
        self.nodata = self.dataset.nodatavals[0] if self.dataset.nodatavals else None

    def compute_tio2(self, window=None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute TiO2 weight-percent for the full raster or a window.
        Returns:
            tio2 : 2-D array of TiO2 wt% values
            mask : boolean mask of valid pixels
        """
        # In the Clementine UVVIS ratio product:
        # Band 1: 750/415 ratio
        # Band 2: 750/1000 ratio
        # Band 3: 415/750 ratio (or 750 nm reflectance in 3-band products)
        if self.dataset.count >= 3 and self.use_lucey2000:
            b1 = self.dataset.read(1, window=window).astype(np.float32)
            b3 = self.dataset.read(3, window=window).astype(np.float32)

            # R415/R750 is inverse of R750/R415 (Band 1), or directly Band 3 if Blue is 415/750
            # For 750 reflectance, typical physical lunar values are 0.03 - 0.40
            r415_r750 = np.where(b1 > 0, 1.0 / b1, np.nan)
            r750 = b3

            # Check if r750 is within physical lunar reflectance range (0.01 to 0.80)
            valid_refl = np.isfinite(r750) & (r750 >= 0.01) & (r750 <= 0.80)
            if np.any(valid_refl):
                tio2 = tio2_lucey2000(r415=r415_r750 * r750, r750=r750)
                mask = ~np.isnan(tio2) & np.isfinite(tio2) & valid_refl
                if self.nodata is not None:
                    mask = mask & (b1 != self.nodata)
            else:
                # Incompatible or non-reflectance values: mark unavailable rather than uncalibrated estimates
                tio2 = np.full_like(b1, np.nan)
                mask = np.zeros_like(b1, dtype=bool)
        else:
            # Calibrated inputs (R750 absolute reflectance and R415/R750) are unavailable.
            # Per scientific integrity guidelines: mark TiO2 as unavailable rather than
            # generating unverified values with legacy linear shortcuts.
            shape = self.dataset.read(1, window=window).shape
            tio2 = np.full(shape, np.nan, dtype=np.float32)
            mask = np.zeros(shape, dtype=bool)

        return tio2, mask

    def close(self):
        if self.dataset and not self.dataset.closed:
            self.dataset.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
