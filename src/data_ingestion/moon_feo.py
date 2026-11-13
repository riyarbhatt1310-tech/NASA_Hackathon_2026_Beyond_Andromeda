import rasterio
import numpy as np
from pathlib import Path

class MoonFeOReader:
    """Reader for Moon Clementine UVVIS FeO GeoTIFF.

    The GeoTIFF stores FeO weight percent as a float raster.
    This class provides a simple interface to read a window of data
    aligned with the planetary grid.
    """

    def __init__(self, raster_path: str):
        self.raster_path = Path(raster_path)
        if not self.raster_path.is_file():
            raise FileNotFoundError(f"FeO raster not found at {self.raster_path}")
        self.dataset = rasterio.open(self.raster_path)
        self.unit = self.dataset.tags().get('UNIT', '%')

    def read_window_pixels(self, window):
        """Return a NumPy array of FeO weight percent for the given rasterio window.

        Parameters
        ----------
        window : rasterio.windows.Window
            Pixel window specifying (col_off, row_off, width, height).
        Returns
        -------
        data : np.ndarray
            2‑D array of FeO weight percent values.
        mask : np.ndarray of bool
            True where data is valid (not nodata).
        """
        data = self.dataset.read(1, window=window)
        nodata = self.dataset.nodata
        if nodata is not None:
            mask = data != nodata
        else:
            mask = np.ones_like(data, dtype=bool)
        return data, mask

    def close(self):
        self.dataset.close()
