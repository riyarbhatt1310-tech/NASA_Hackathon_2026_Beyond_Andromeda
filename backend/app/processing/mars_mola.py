"""
MGS MOLA MEGDR megt90n000eb Binary Reader & Validator.

Dataset: Mars Global Surveyor (MGS) MOLA MEGDR Topography (megt90n000eb)
Dimensions: 2880 lines x 5760 samples
Data Type: SignedMSB2 (signed 16-bit integer, big-endian, >i2)
Resolution: 16 pixels per degree (~3.70446 km/pixel at equator)
Elevation Unit: Meters relative to MOLA areoid (0 m datum)
Offset: 0
Scale: 1.0
NoData Value: -32768 (0x8000)
"""

import math
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np

from src.core.constants import (
    MARS_REFERENCE_RADIUS_M,
    MARS_RASTER_LINES,
    MARS_RASTER_SAMPLES,
    MARS_PIXELS_PER_DEGREE,
    MARS_NODATA_VALUE,
)


class MarsMolaMetadata:
    """Parses and holds metadata for MOLA MEGDR (from XML or defaults)."""

    def __init__(
        self,
        lines: int = MARS_RASTER_LINES,
        samples: int = MARS_RASTER_SAMPLES,
        sample_bits: int = 16,
        data_type: str = "SignedMSB2",
        scaling_factor: float = 1.0,
        offset: float = 0.0,
        unit: str = "METERS",
        nodata_value: int = MARS_NODATA_VALUE,
    ):
        self.lines = lines
        self.samples = samples
        self.sample_bits = sample_bits
        self.data_type = data_type
        self.scaling_factor = scaling_factor
        self.offset = offset
        self.unit = unit.upper()
        self.nodata_value = nodata_value

    @classmethod
    def from_metadata_file(cls, meta_path: Path) -> "MarsMolaMetadata":
        """Parses an XML or PDS label file for MOLA MEGDR."""
        if not meta_path.is_file():
            return cls()

        with open(meta_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        def extract_val(pattern: str, default: Any, cast_fn=str):
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                try:
                    return cast_fn(m.group(1).strip().strip('"').strip("'"))
                except (ValueError, TypeError):
                    return default
            return default

        # Try PDS4 XML tags or PDS3 tags
        lines = extract_val(r"<(?:records|lines)>(\d+)</(?:records|lines)>", None, int)
        if lines is None:
            lines = extract_val(r"LINES\s*=\s*(\d+)", MARS_RASTER_LINES, int)

        samples = extract_val(r"<(?:fields|samples|line_samples)>(\d+)</(?:fields|samples|line_samples)>", None, int)
        if samples is None:
            samples = extract_val(r"LINE_SAMPLES\s*=\s*(\d+)", MARS_RASTER_SAMPLES, int)

        scaling_factor = extract_val(r"<scaling_factor>([\d\.\+\-eE]+)</scaling_factor>", None, float)
        if scaling_factor is None:
            scaling_factor = extract_val(r"SCALING_FACTOR\s*=\s*([\d\.\+\-eE]+)", 1.0, float)

        offset = extract_val(r"<value_offset>([\d\.\+\-eE]+)</value_offset>", None, float)
        if offset is None:
            offset = extract_val(r"OFFSET\s*=\s*([\d\.\+\-eE]+)", 0.0, float)

        nodata = extract_val(r"<special_constant>([-\d]+)</special_constant>", None, int)
        if nodata is None:
            nodata = extract_val(r"(?:MISSING_CONSTANT|NULL_VALUE)\s*=\s*([-\d]+)", MARS_NODATA_VALUE, int)

        return cls(
            lines=lines,
            samples=samples,
            scaling_factor=scaling_factor,
            offset=offset,
            nodata_value=nodata,
        )


class MarsMolaReader:
    """
    High-performance memory-mapped reader for the global MGS MOLA MEGDR raster.
    Interprets big-endian signed 16-bit integers (SignedMSB2).
    """

    EXPECTED_BYTES = MARS_RASTER_LINES * MARS_RASTER_SAMPLES * 2  # 33,177,600 bytes

    def __init__(self, raster_path: Optional[Path] = None, metadata_path: Optional[Path] = None):
        if raster_path is None:
            from src.core.config import Config
            raster_path = Config.load().get_mars_raster_path()
        self.raster_path = Path(raster_path)
        self.metadata_path = (
            Path(metadata_path) if metadata_path else self.raster_path.with_suffix(".xml")
        )
        self.metadata = MarsMolaMetadata.from_metadata_file(self.metadata_path)
        self._data: Optional[np.ndarray] = None
        self._is_mmap = False

    def open(self) -> "MarsMolaReader":
        """Opens and memory-maps the SignedMSB2 raster."""
        if not self.raster_path.is_file():
            raise FileNotFoundError(
                f"Mars MOLA raster file not found at: {self.raster_path}. "
                f"Please update config.yaml with the path to megt90n000eb.img."
            )

        file_size = self.raster_path.stat().st_size
        if file_size < self.EXPECTED_BYTES:
            raise ValueError(
                f"Invalid file size for {self.raster_path}: got {file_size} bytes, "
                f"expected at least {self.EXPECTED_BYTES} bytes."
            )

        # Big-endian signed 16-bit integer (>i2)
        self._data = np.memmap(
            self.raster_path,
            dtype=">i2",
            mode="r",
            shape=(self.metadata.lines, self.metadata.samples),
        )
        self._is_mmap = True
        return self

    def close(self):
        """Closes memory map."""
        self._data = None
        self._is_mmap = False

    def __enter__(self):
        return self.open()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @property
    def data(self) -> np.ndarray:
        if self._data is None:
            self.open()
        return self._data

    @staticmethod
    def lat_lon_to_row_col(lat: float, lon: float) -> Tuple[int, int]:
        """
        Converts Mars latitude [-90, +90] and longitude [0, 360] or [-180, +180]
        to 0-indexed raster row and column at 16 pixels/deg.
        """
        if not -90.0 <= lat <= 90.0:
            raise ValueError(f"Latitude must be between -90 and +90, got {lat}")

        # Normalise longitude to [0, 360) East
        lon_norm = lon % 360.0

        # Row 0 is +90 deg (North Pole), Row 2879 is -90 deg (South Pole)
        row = int((90.0 - lat) * MARS_PIXELS_PER_DEGREE)
        row = min(max(row, 0), MARS_RASTER_LINES - 1)

        # Col 0 is 0 deg E, Col 5759 is (360 - 1/16) deg E
        col = int(lon_norm * MARS_PIXELS_PER_DEGREE)
        col = min(max(col, 0), MARS_RASTER_SAMPLES - 1)

        return row, col

    @staticmethod
    def row_col_to_lat_lon(row: int, col: int) -> Tuple[float, float]:
        """
        Converts 0-indexed raster row and column to pixel-center Martian latitude and longitude.
        """
        lat = 90.0 - (row + 0.5) / MARS_PIXELS_PER_DEGREE
        lon = (col + 0.5) / MARS_PIXELS_PER_DEGREE
        return lat, lon

    def get_elevation_at(self, lat: float, lon: float) -> Optional[float]:
        """
        Returns the elevation in meters at the given Martian coordinates.
        Returns None if pixel is nodata (-32768).
        """
        row, col = self.lat_lon_to_row_col(lat, lon)
        raw_val = int(self.data[row, col])

        if raw_val == self.metadata.nodata_value:
            return None

        # Apply scaling and offset (standard MOLA MEGDR is scale 1.0, offset 0.0)
        elev = (float(raw_val) * self.metadata.scaling_factor) + self.metadata.offset
        return elev

    def read_window_pixels(
        self,
        center_lat: float,
        center_lon: float,
        half_width_deg: float,
        half_height_deg: float,
    ) -> Tuple[np.ndarray, np.ndarray, float]:
        """
        Reads a window around (center_lat, center_lon) and returns:
        - elevation_m: 2D array of elevation in meters (float32) with nodata as NaN
        - valid_mask: 2D boolean array (True where valid)
        - valid_ratio: fraction of valid pixels in window [0.0, 1.0]
        """
        min_lat = max(-90.0, center_lat - half_height_deg)
        max_lat = min(90.0, center_lat + half_height_deg)

        r_start, _ = self.lat_lon_to_row_col(max_lat, center_lon)
        r_end, _ = self.lat_lon_to_row_col(min_lat, center_lon)
        row_slice = slice(min(r_start, r_end), max(r_start, r_end) + 1)

        lon_w = (center_lon - half_width_deg) % 360.0
        lon_e = (center_lon + half_width_deg) % 360.0
        _, c_start = self.lat_lon_to_row_col(center_lat, lon_w)
        _, c_end = self.lat_lon_to_row_col(center_lat, lon_e)

        if c_start <= c_end:
            raw_sub = np.array(self.data[row_slice, c_start : c_end + 1], dtype=np.int16)
        else:
            # Handle prime meridian / antimeridian wrap
            sub1 = self.data[row_slice, c_start:MARS_RASTER_SAMPLES]
            sub2 = self.data[row_slice, 0 : c_end + 1]
            raw_sub = np.concatenate([sub1, sub2], axis=1).astype(np.int16)

        valid_mask = raw_sub != self.metadata.nodata_value

        elev = raw_sub.astype(np.float32)
        elev = (elev * self.metadata.scaling_factor) + self.metadata.offset
        elev[~valid_mask] = np.nan

        valid_ratio = float(np.sum(valid_mask)) / float(elev.size) if elev.size > 0 else 0.0
        return elev, valid_mask, valid_ratio
