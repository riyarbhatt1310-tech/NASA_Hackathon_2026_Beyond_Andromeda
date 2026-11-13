"""
Earth Global Lithological Map (GLiM v1.0) Aggregator.

Extracts modal lithology ID and area fraction for analysis tiles.
Preserves categorical nature of lithological classes (never averages class IDs).
"""

from pathlib import Path
from typing import Tuple, Optional
import os
import numpy as np
import rasterio
from rasterio.windows import Window
from rasterio.warp import transform_bounds

# Ensure PROJ permits transformations between planetary bodies (e.g. Mars/Moon and Earth EPSG:4326)
os.environ["PROJ_IGNORE_CELESTIAL_BODY"] = "YES"


def compute_safe_window(
    ds: rasterio.io.DatasetReader,
    left: float,
    bottom: float,
    right: float,
    top: float,
) -> Window:
    """
    Computes a pixel window from geographic bounds, handling coordinate wrapping,
    reprojection for projected CRS (e.g. MODIS Sinusoidal), and ensuring at least
    a 1x1 pixel window is sampled even for coarse rasters.
    """
    if ds.crs and ds.crs.is_projected:
        try:
            left, bottom, right, top = transform_bounds(
                "EPSG:4326", ds.crs, left, bottom, right, top
            )
        except Exception:
            pass
    else:
        # Normalize longitude if dataset is [-180, 180] and query is [0, 360]
        b = ds.bounds
        if b.left >= -180.5 and b.right <= 180.5:
            if left > 180.0:
                left -= 360.0
                right -= 360.0
        elif b.left >= -0.5 and b.right >= 359.0:
            if left < 0.0:
                left += 360.0
                right += 360.0

    c1, r1 = ~ds.transform @ (left, top)
    c2, r2 = ~ds.transform @ (right, bottom)

    row_min = int(np.floor(min(r1, r2)))
    row_max = int(np.ceil(max(r1, r2)))
    col_min = int(np.floor(min(c1, c2)))
    col_max = int(np.ceil(max(c1, c2)))

    if row_max <= row_min:
        row_max = row_min + 1
    if col_max <= col_min:
        col_max = col_min + 1

    return Window(col_min, row_min, col_max - col_min, row_max - row_min)


class EarthGLiMAggregator:
    """Aggregator for GLiM lithology raster.
    Returns the modal lithology ID and its fraction within the requested window.
    """

    def __init__(self, raster_path: str):
        self.path = Path(raster_path)
        if not self.path.is_file():
            raise FileNotFoundError(f"GLiM raster not found: {self.path}")
        self._ds: Optional[rasterio.io.DatasetReader] = None

    def open(self) -> "EarthGLiMAggregator":
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
    ) -> np.ndarray:
        left = center_lon - half_width_deg
        right = center_lon + half_width_deg
        bottom = center_lat - half_height_deg
        top = center_lat + half_height_deg

        window = compute_safe_window(self._ds, left, bottom, right, top)
        fill_val = self._ds.nodata if self._ds.nodata is not None else -9999
        data = self._ds.read(1, window=window, boundless=True, fill_value=fill_val)
        return data

    def aggregate_mode(
        self,
        center_lat: float,
        center_lon: float,
        half_width_deg: float,
        half_height_deg: float,
    ) -> Tuple[int, float]:
        """
        Computes the modal categorical lithology ID and the fraction of valid pixels.
        """
        if self._ds is None:
            self.open()

        data = self._read_window(center_lat, center_lon, half_width_deg, half_height_deg)
        mask = data != self._ds.nodata
        valid = data[mask]
        if valid.size == 0:
            return (0, 0.0)

        values, counts = np.unique(valid, return_counts=True)
        mode_idx = np.argmax(counts)
        mode_id = int(values[mode_idx])
        fraction = float(counts[mode_idx]) / valid.size
        return mode_id, fraction
