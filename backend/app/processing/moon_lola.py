"""
NASA LOLA LDEM_16_FLOAT Binary Reader & Validator.

Dataset: NASA Lunar Reconnaissance Orbiter (LRO) LOLA Global DEM (LDEM_16_FLOAT)
Dimensions: 2880 lines x 5760 samples
Data Type: 32-bit floating-point, little-endian (IEEE 754, <f4)
Resolution: 16 pixels per degree (~1.89521 km/pixel at equator)
Reference Radius: 1737.4 km (1,737,400.0 m)
"""

import math
import os
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import numpy as np

from src.core.constants import (
    MOON_REFERENCE_RADIUS_M,
    MOON_RASTER_LINES,
    MOON_RASTER_SAMPLES,
    MOON_PIXELS_PER_DEGREE,
    MOON_NODATA_THRESHOLD,
)


class MoonLolaMetadata:
    """Parses and holds PDS3 label metadata for NASA LOLA LDEM_16_FLOAT."""

    def __init__(
        self,
        lines: int = MOON_RASTER_LINES,
        samples: int = MOON_RASTER_SAMPLES,
        sample_bits: int = 32,
        sample_type: str = "PC_REAL",
        scaling_factor: float = 1.0,
        offset: float = 0.0,
        unit: str = "METERS",
        missing_constant: float = -3.40282265e38,
    ):
        self.lines = lines
        self.samples = samples
        self.sample_bits = sample_bits
        self.sample_type = sample_type
        self.scaling_factor = scaling_factor
        self.offset = offset
        self.unit = unit.upper()
        self.missing_constant = missing_constant

    @classmethod
    def from_label_file(cls, label_path: Path) -> "MoonLolaMetadata":
        """Parses a PDS3 .LBL file for LOLA DEM."""
        if not label_path.is_file():
            return cls()

        with open(label_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        def extract_val(pattern: str, default: Any, cast_fn=str):
            m = re.search(pattern, text, re.IGNORECASE)
            if m:
                try:
                    return cast_fn(m.group(1).strip().strip('"').strip("'"))
                except (ValueError, TypeError):
                    return default
            return default

        lines = extract_val(r"LINES\s*=\s*(\d+)", MOON_RASTER_LINES, int)
        samples = extract_val(r"LINE_SAMPLES\s*=\s*(\d+)", MOON_RASTER_SAMPLES, int)
        sample_bits = extract_val(r"SAMPLE_BITS\s*=\s*(\d+)", 32, int)
        sample_type = extract_val(r"SAMPLE_TYPE\s*=\s*([A-Za-z0-9_]+)", "PC_REAL", str)
        scaling_factor = extract_val(r"SCALING_FACTOR\s*=\s*([\d\.\+\-eE]+)", 1.0, float)
        offset = extract_val(r"OFFSET\s*=\s*([\d\.\+\-eE]+)", 0.0, float)
        # Parse unit (handles KILOMETER, KILOMETERS, KM, METERS)
        unit = extract_val(r"UNIT\s*=\s*\"?([A-Za-z]+)\"?", "METERS", str).upper()
        # In LOLA PDS labels, OFFSET is 1737.4 km (the reference sphere radius).
        # Topographic height relative to the sphere is DN * SCALING_FACTOR.
        # We store reference_radius_km = offset if offset > 1000, and keep elevation offset as 0.0.
        raw_offset = extract_val(r"OFFSET\s*=\s*([\d\.\+\-eE]+)", 0.0, float)
        elev_offset = 0.0 if raw_offset >= 1000.0 else raw_offset

        missing_constant = extract_val(
            r"MISSING_CONSTANT\s*=\s*([\d\.\+\-eE]+)", -3.40282265e38, float
        )

        return cls(
            lines=lines,
            samples=samples,
            sample_bits=sample_bits,
            sample_type=sample_type,
            scaling_factor=scaling_factor,
            offset=elev_offset,
            unit=unit,
            missing_constant=missing_constant,
        )

    def to_meters(self, raw_val: float) -> float:
        """Converts raw DN value to elevation in meters relative to reference sphere."""
        val = (raw_val * self.scaling_factor) + self.offset
        if "KILOMETER" in self.unit or self.unit == "KM":
            val *= 1000.0
        return val


class MoonLolaReader:
    """
    High-performance memory-mapped reader for the global NASA LOLA LDEM_16_FLOAT raster.
    """

    EXPECTED_BYTES = MOON_RASTER_LINES * MOON_RASTER_SAMPLES * 4  # 66,355,200 bytes

    def __init__(self, raster_path: Optional[Path] = None, label_path: Optional[Path] = None):
        if raster_path is None:
            from src.core.config import Config
            raster_path = Config.load().get_moon_raster_path()
        self.raster_path = Path(raster_path)
        self.label_path = Path(label_path) if label_path else self.raster_path.with_suffix(".LBL")
        self.metadata = MoonLolaMetadata.from_label_file(self.label_path)
        self._data: Optional[np.ndarray] = None
        self._is_mmap = False

    def open(self) -> "MoonLolaReader":
        """Opens and memory-maps the binary raster file."""
        if not self.raster_path.is_file():
            raise FileNotFoundError(
                f"Moon LOLA raster file not found at: {self.raster_path}. "
                f"Please update config.yaml with the path to LDEM_16_FLOAT.IMG."
            )

        file_size = self.raster_path.stat().st_size
        if file_size < self.EXPECTED_BYTES:
            raise ValueError(
                f"Invalid file size for {self.raster_path}: got {file_size} bytes, "
                f"expected at least {self.EXPECTED_BYTES} bytes."
            )

        # Memory map the 32-bit float array (little-endian: <f4)
        self._data = np.memmap(
            self.raster_path,
            dtype="<f4",
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
        Converts Lunar latitude [-90, +90] and longitude [0, 360] or [-180, +180]
        to 0-indexed raster row and column at 16 pixels/deg.
        """
        if not -90.0 <= lat <= 90.0:
            raise ValueError(f"Latitude must be between -90 and +90, got {lat}")

        # Normalise longitude to [0, 360)
        lon_norm = lon % 360.0

        # Row 0 is +90 deg (North Pole), Row 2879 is -90 deg (South Pole)
        row = int((90.0 - lat) * MOON_PIXELS_PER_DEGREE)
        row = min(max(row, 0), MOON_RASTER_LINES - 1)

        # Col 0 is 0 deg E, Col 5759 is (360 - 1/16) deg E
        col = int(lon_norm * MOON_PIXELS_PER_DEGREE)
        col = min(max(col, 0), MOON_RASTER_SAMPLES - 1)

        return row, col

    @staticmethod
    def row_col_to_lat_lon(row: int, col: int) -> Tuple[float, float]:
        """
        Converts 0-indexed raster row and column to pixel-center Lunar latitude and longitude.
        """
        lat = 90.0 - (row + 0.5) / MOON_PIXELS_PER_DEGREE
        lon = (col + 0.5) / MOON_PIXELS_PER_DEGREE
        return lat, lon

    def get_elevation_at(self, lat: float, lon: float) -> Optional[float]:
        """
        Returns the elevation in meters at the given lunar coordinates.
        Returns None if pixel is nodata.
        """
        row, col = self.lat_lon_to_row_col(lat, lon)
        raw_val = float(self.data[row, col])

        if np.isnan(raw_val) or raw_val <= MOON_NODATA_THRESHOLD:
            return None

        # Apply metadata scaling and unit conversion
        elev = self.metadata.to_meters(raw_val)
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
        - elevation_m: 2D array of elevation in meters with invalid data as NaN
        - valid_mask: 2D boolean array (True where valid)
        - valid_ratio: fraction of valid pixels in window [0.0, 1.0]
        """
        min_lat = max(-90.0, center_lat - half_height_deg)
        max_lat = min(90.0, center_lat + half_height_deg)

        r_start, _ = self.lat_lon_to_row_col(max_lat, center_lon)
        r_end, _ = self.lat_lon_to_row_col(min_lat, center_lon)
        # Ensure slice indices are ordered
        row_slice = slice(min(r_start, r_end), max(r_start, r_end) + 1)

        lon_w = (center_lon - half_width_deg) % 360.0
        lon_e = (center_lon + half_width_deg) % 360.0
        _, c_start = self.lat_lon_to_row_col(center_lat, lon_w)
        _, c_end = self.lat_lon_to_row_col(center_lat, lon_e)

        if c_start <= c_end:
            raw_sub = np.array(self.data[row_slice, c_start : c_end + 1], dtype=np.float32)
        else:
            # Handles antimeridian / 0-deg wrap
            sub1 = self.data[row_slice, c_start:MOON_RASTER_SAMPLES]
            sub2 = self.data[row_slice, 0 : c_end + 1]
            raw_sub = np.concatenate([sub1, sub2], axis=1).astype(np.float32)

        # Apply metadata scaling and conversion to meters
        scaled = (raw_sub * self.metadata.scaling_factor) + self.metadata.offset
        if "KILOMETER" in self.metadata.unit or self.metadata.unit == "KM":
            scaled *= 1000.0

        # Mask nodata values
        valid_mask = (~np.isnan(raw_sub)) & (raw_sub > MOON_NODATA_THRESHOLD)
        scaled[~valid_mask] = np.nan

        valid_ratio = float(np.sum(valid_mask)) / float(scaled.size) if scaled.size > 0 else 0.0
        return scaled, valid_mask, valid_ratio
