"""
Planetary constants, datums, and physical scales for TerraTwin.

All values are based on IAU/IAG working group standards and NASA PDS datasets.
"""

from typing import Final, Dict, Any

# Earth Physical & Geodetic Constants (WGS 84 / EGM2008)
EARTH_VOLUMETRIC_RADIUS_M: Final[float] = 6_371_008.8
EARTH_EQUATORIAL_RADIUS_M: Final[float] = 6_378_137.0
EARTH_POLAR_RADIUS_M: Final[float] = 6_356_752.3
EARTH_EQUATORIAL_CIRCUMFERENCE_KM: Final[float] = 40_075.017
EARTH_NODATA_VALUE: Final[float] = -9999.0

# Moon Physical & Geodetic Constants (NASA LOLA ME Reference Frame)
MOON_REFERENCE_RADIUS_M: Final[float] = 1_737_400.0  # 1737.4 km standard sphere
MOON_EQUATORIAL_CIRCUMFERENCE_KM: Final[float] = 10_920.707
MOON_RASTER_LINES: Final[int] = 2880
MOON_RASTER_SAMPLES: Final[int] = 5760
MOON_PIXELS_PER_DEGREE: Final[float] = 16.0
MOON_EQUATORIAL_KM_PER_PIXEL: Final[float] = 1.8952136
MOON_NODATA_THRESHOLD: Final[float] = -3.0e38

# Mars Physical & Geodetic Constants (MGS MOLA Areoid / IAU 2000)
MARS_REFERENCE_RADIUS_M: Final[float] = 3_396_190.0  # 3396.19 km areoid
MARS_POLAR_RADIUS_M: Final[float] = 3_376_200.0
MARS_EQUATORIAL_CIRCUMFERENCE_KM: Final[float] = 21_343.834
MARS_RASTER_LINES: Final[int] = 2880
MARS_RASTER_SAMPLES: Final[int] = 5760
MARS_PIXELS_PER_DEGREE: Final[float] = 16.0
MARS_EQUATORIAL_KM_PER_PIXEL: Final[float] = 3.7044616
MARS_NODATA_VALUE: Final[int] = -32768  # 0x8000 in SignedMSB2

# Analysis Scale
ANALYSIS_TILE_SIZE_KM: Final[float] = 25.0
MIN_VALID_COVERAGE_RATIO: Final[float] = 0.70

# Body Metadata Registry
PLANETARY_METADATA: Final[Dict[str, Dict[str, Any]]] = {
    "earth": {
        "name": "Earth",
        "radius_m": EARTH_VOLUMETRIC_RADIUS_M,
        "datum": "EGM2008 / WGS 84",
        "nodata": EARTH_NODATA_VALUE,
        "elevation_description": "Elevation in meters relative to mean sea level (EGM2008 geoid)",
    },
    "moon": {
        "name": "Moon",
        "radius_m": MOON_REFERENCE_RADIUS_M,
        "datum": "Mean Earth / Polar Axis (ME) 1737.4 km sphere",
        "nodata_threshold": MOON_NODATA_THRESHOLD,
        "elevation_description": "Elevation in meters relative to the 1737.4 km reference sphere",
        "lines": MOON_RASTER_LINES,
        "samples": MOON_RASTER_SAMPLES,
        "pixels_per_degree": MOON_PIXELS_PER_DEGREE,
    },
    "mars": {
        "name": "Mars",
        "radius_m": MARS_REFERENCE_RADIUS_M,
        "datum": "MOLA Areoid (IAU 2000)",
        "nodata": MARS_NODATA_VALUE,
        "elevation_description": "Elevation in meters relative to the MOLA zero areoid",
        "lines": MARS_RASTER_LINES,
        "samples": MARS_RASTER_SAMPLES,
        "pixels_per_degree": MARS_PIXELS_PER_DEGREE,
    },
}
