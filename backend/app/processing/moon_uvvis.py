import rasterio
import numpy as np
from pathlib import Path

class MoonUVVisReader:
    """Reader for the Moon UVVIS 200 m mosaic.
    Provides access to the three bands (R750, R415, R1000) as separate arrays.
    """

    def __init__(self, uvvis_path: str):
        self.path = Path(uvvis_path)
        if not self.path.is_file():
            raise FileNotFoundError(f"UVVIS file not found: {self.path}")
        self.dataset = rasterio.open(self.path)
        # Expected 3 bands: 1‑R750, 2‑R415, 3‑R1000 (order from USGS documentation)
        if self.dataset.count != 3:
            raise ValueError(f"UVVIS mosaic must have 3 bands, found {self.dataset.count}")
        self.nodata = self.dataset.nodatavals[0]
        self.crs = self.dataset.crs
        self.transform = self.dataset.transform

    def read_window_pixels(self, center_lat: float, center_lon: float, half_width_deg: float, half_height_deg: float):
        """Return three arrays (R750, R415, R1000) and a mask.
        The window is defined in geographic degrees (lat/lon) and converted via the dataset transform.
        """
        # Convert geographic bounds to raster coordinates
        left = center_lon - half_width_deg
        right = center_lon + half_width_deg
        bottom = center_lat - half_height_deg
        top = center_lat + half_height_deg
        row_start, col_start = ~self.transform @ (left, top)
        row_stop, col_stop = ~self.transform @ (right, bottom)
        row_start, col_start = int(np.floor(row_start)), int(np.floor(col_start))
        row_stop, col_stop = int(np.ceil(row_stop)), int(np.ceil(col_stop))
        window = rasterio.windows.Window(col_start, row_start, col_stop - col_start, row_stop - row_start)
        bands = []
        for b in range(1, 4):
            data = self.dataset.read(b, window=window)
            bands.append(data)
        # Build mask where any band equals nodata
        mask = np.logical_not(np.isclose(bands[0], self.nodata) | np.isclose(bands[1], self.nodata) | np.isclose(bands[2], self.nodata))
        return tuple(bands), mask
