"""
Earth Global Digital Elevation Model (DEM) Reader & Validator.

Dataset: NOAA NCEI ETOPO 2022 Global Relief Model (60 Arc-Second Surface Elevation)
DOI: 10.25921/fd45-gt74
Citation: NOAA National Centers for Environmental Information. 2022:
          ETOPO 2022 60 Arc-Second Global Relief Model. NOAA National Centers
          for Environmental Information.
Dimensions: 10800 lines x 21600 samples
Native Resolution: 60 arc-seconds (1/60 deg, ~1.853 km at equator)
Vertical Datum: Orthometric height in meters relative to EGM2008 geoid
CRS: EPSG:9518 (WGS 84 3D / Geographic 2D + Gravity-related height)
Integrated Sources: Copernicus DEM GLO-30 (global land), USGS 3DEP, ArcticDEM,
                    REMA (Antarctica), and multi-beam bathymetry.
"""

import math
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np
import rasterio
from rasterio.windows import from_bounds

from src.core.constants import EARTH_VOLUMETRIC_RADIUS_M


class EarthDemMetadata:
    """Scientific metadata and provenance for NOAA ETOPO 2022 Global Relief Model."""

    def __init__(
        self,
        name: str = "NOAA ETOPO 2022 Global Relief Model (60s)",
        doi: str = "10.25921/fd45-gt74",
        citation: str = "NOAA NCEI. 2022: ETOPO 2022 60 Arc-Second Global Relief Model.",
        native_res_arcsec: float = 60.0,
        native_res_km: float = 1.853,
        elevation_unit: str = "METERS",
        vertical_datum: str = "EGM2008 geoid",
        nodata_value: float = -99999.0,
        crs: str = "EPSG:9518",
        lines: int = 10800,
        samples: int = 21600,
    ):
        self.name = name
        self.doi = doi
        self.citation = citation
        self.native_res_arcsec = native_res_arcsec
        self.native_res_km = native_res_km
        self.elevation_unit = elevation_unit
        self.vertical_datum = vertical_datum
        self.nodata_value = nodata_value
        self.crs = crs
        self.lines = lines
        self.samples = samples

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "doi": self.doi,
            "citation": self.citation,
            "native_res_arcsec": self.native_res_arcsec,
            "native_res_km": self.native_res_km,
            "elevation_unit": self.elevation_unit,
            "vertical_datum": self.vertical_datum,
            "nodata_value": self.nodata_value,
            "crs": self.crs,
            "dimensions": {"lines": self.lines, "samples": self.samples},
        }


class EarthDemReader:
    """
    High-performance, memory-efficient windowed reader for global Earth DEM rasters.
    
    Reads geographic windows directly without loading the entire global raster into memory,
    handles longitude normalization (0-360 to -180..+180), antimeridian wrapping,
    polar boundary clamping, and nodata quality masking.
    """

    def __init__(self, dem_path: Optional[Path] = None):
        if dem_path is None:
            base_dir = Path(__file__).resolve().parent.parent.parent
            dem_path = base_dir / "data" / "raw" / "earth" / "dem" / "ETOPO_2022_v1_60s_N90W180_surface.tif"
        self.dem_path = Path(dem_path)
        self.metadata = EarthDemMetadata()
        self._dataset: Optional[rasterio.io.DatasetReader] = None

    def open(self) -> "EarthDemReader":
        """Opens the GeoTIFF raster for windowed reads."""
        if not self.dem_path.is_file():
            raise FileNotFoundError(
                f"Earth DEM raster file not found at: {self.dem_path}. "
                f"Please ensure ETOPO_2022_v1_60s_N90W180_surface.tif is present."
            )
        if self._dataset is None or self._dataset.closed:
            self._dataset = rasterio.open(self.dem_path)
        return self

    def close(self) -> None:
        """Closes the underlying raster dataset."""
        if self._dataset is not None and not self._dataset.closed:
            self._dataset.close()
            self._dataset = None

    def __enter__(self) -> "EarthDemReader":
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()

    def read_window_pixels(
        self,
        center_lat: float,
        center_lon: float,
        half_width_deg: float,
        half_height_deg: float,
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Reads a window around (center_lat, center_lon) and returns:
        - elevation_m: 2D array of elevation in meters with nodata as NaN
        - valid_mask: 2D boolean array (True where valid physical elevation)
        - valid_ratio: fraction of valid pixels in window [0.0, 1.0]

        Strictly handles:
        - Coordinate normalization: supports both [-180, 180] and [0, 360] longitude formats.
        - Antimeridian wrapping: if window crosses 180° / -180°, reads both sides and joins.
        - Polar clamping: restricts latitude to [-90, 90].
        - Memory safety: uses windowed IO directly from disk.
        """
        if self._dataset is None or self._dataset.closed:
            self.open()

        ds = self._dataset

        # Normalize center_lon to [-180, 180]
        norm_lon = ((center_lon + 180.0) % 360.0) - 180.0

        min_lat = max(-90.0, float(center_lat - half_height_deg))
        max_lat = min(90.0, float(center_lat + half_height_deg))
        min_lon = float(norm_lon - half_width_deg)
        max_lon = float(norm_lon + half_width_deg)

        nodata_val = ds.nodata if ds.nodata is not None else self.metadata.nodata_value

        # Check for antimeridian crossing
        if min_lon < -180.0:
            w1 = from_bounds(min_lon + 360.0, min_lat, 180.0, max_lat, ds.transform)
            w2 = from_bounds(-180.0, min_lat, max_lon, max_lat, ds.transform)
            d1 = ds.read(1, window=w1, boundless=True, fill_value=nodata_val)
            d2 = ds.read(1, window=w2, boundless=True, fill_value=nodata_val)
            raw = np.concatenate([d1, d2], axis=1)
        elif max_lon > 180.0:
            w1 = from_bounds(min_lon, min_lat, 180.0, max_lat, ds.transform)
            w2 = from_bounds(-180.0, min_lat, max_lon - 360.0, max_lat, ds.transform)
            d1 = ds.read(1, window=w1, boundless=True, fill_value=nodata_val)
            d2 = ds.read(1, window=w2, boundless=True, fill_value=nodata_val)
            raw = np.concatenate([d1, d2], axis=1)
        else:
            w = from_bounds(min_lon, min_lat, max_lon, max_lat, ds.transform)
            raw = ds.read(1, window=w, boundless=True, fill_value=nodata_val)

        # Quality mask: filter out nodata and non-finite values
        valid_mask = np.isfinite(raw) & (raw != nodata_val)
        elev_m = np.where(valid_mask, raw.astype(np.float32), np.nan)

        total_pixels = raw.size
        valid_pixels = int(np.sum(valid_mask))
        valid_ratio = float(valid_pixels / total_pixels) if total_pixels > 0 else 0.0

        return elev_m, valid_mask, valid_ratio

    def get_metadata(self) -> Dict[str, Any]:
        """Returns verified scientific metadata for the Earth DEM."""
        return self.metadata.to_dict()
