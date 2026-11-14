"""
Scientific Geomorphometry & Terrain Derivatives Engine for TerraTwin.

Calculates scale-invariant physical terrain metrics on a spherical body:
- Horn's spherical physical slope (degrees)
- Terrain Roughness Index (TRI, meters)
- Local Relief (max - min, meters)
- Elevation Standard Deviation (meters)
- Hypsometric Integral & Skewness
- Effective resolution and data quality accounting
"""

import math
from typing import Dict, Any, Optional, Tuple
import numpy as np
from scipy import stats, ndimage


def scale_harmonize_dem(
    elev_grid: np.ndarray,
    native_res_m: float,
    target_res_m: float = 2000.0,
) -> Tuple[np.ndarray, float]:
    """
    Spatially filters high-resolution elevation data (e.g. Earth 30m DEM)
    to match the planetary baseline physical scale (~2 km).

    Prevents micro-topographic bias (e.g. 30m gullies) when comparing against
    coarser planetary sensors (e.g. Moon LOLA ~1.9 km, Mars MOLA ~3.7 km).

    Returns:
    - filtered_elev: spatially aggregated/smoothed elevation grid
    - effective_res_m: resulting effective physical scale in meters
    """
    if target_res_m <= native_res_m:
        return elev_grid, native_res_m

    # Filter sigma in pixels
    sigma_pixels = (target_res_m / native_res_m) / 2.0

    # Mask NaNs before filtering, then restore
    valid_mask = ~np.isnan(elev_grid)
    if not np.any(valid_mask):
        return elev_grid, target_res_m

    filled = np.where(valid_mask, elev_grid, 0.0)
    # Normalized convolution to handle boundaries and NaNs
    weights = np.where(valid_mask, 1.0, 0.0)

    smoothed_data = ndimage.gaussian_filter(filled, sigma=sigma_pixels, mode='nearest')
    smoothed_weights = ndimage.gaussian_filter(weights, sigma=sigma_pixels, mode='nearest')

    with np.errstate(divide='ignore', invalid='ignore'):
        filtered = np.where(smoothed_weights > 0.1, smoothed_data / smoothed_weights, np.nan)

    filtered[~valid_mask] = np.nan
    return filtered.astype(np.float32), float(target_res_m)


def compute_spherical_slope_horn(
    elev_grid: np.ndarray,
    lat_deg: float,
    radius_m: float,
    pixel_dlat_deg: float,
    pixel_dlon_deg: float,
) -> np.ndarray:
    """
    Computes physical terrain slope in degrees using Horn's 3x3 algorithm on the sphere.

    Accounting for metric physical distances:
    dy = radius_m * radians(pixel_dlat_deg)
    dx = radius_m * cos(radians(lat_deg)) * radians(pixel_dlon_deg)
    """
    rows, cols = elev_grid.shape
    if rows < 3 or cols < 3:
        return np.full_like(elev_grid, np.nan, dtype=np.float32)

    lat_rad = math.radians(lat_deg)
    cos_lat = max(0.01, math.cos(lat_rad))

    dy = radius_m * math.radians(pixel_dlat_deg)
    dx = radius_m * cos_lat * math.radians(pixel_dlon_deg)

    # 3x3 neighborhoods
    z = elev_grid
    z_top_left = z[0:-2, 0:-2]
    z_top = z[0:-2, 1:-1]
    z_top_right = z[0:-2, 2:]

    z_left = z[1:-1, 0:-2]
    z_right = z[1:-1, 2:]

    z_bot_left = z[2:, 0:-2]
    z_bot = z[2:, 1:-1]
    z_bot_right = z[2:, 2:]

    # Horn finite differences
    # dz/dx = ((z_top_right + 2*z_right + z_bot_right) - (z_top_left + 2*z_left + z_bot_left)) / (8 * dx)
    dz_dx = ((z_top_right + 2.0 * z_right + z_bot_right) - (z_top_left + 2.0 * z_left + z_bot_left)) / (8.0 * dx)

    # dz/dy = ((z_top_left + 2*z_top + z_top_right) - (z_bot_left + 2*z_bot + z_bot_right)) / (8 * dy)
    dz_dy = ((z_top_left + 2.0 * z_top + z_top_right) - (z_bot_left + 2.0 * z_bot + z_bot_right)) / (8.0 * dy)

    grad = np.sqrt(dz_dx**2 + dz_dy**2)
    slope_rad = np.arctan(grad)
    slope_deg = np.degrees(slope_rad)

    # Pad back to original grid size with NaN borders
    padded_slope = np.full_like(elev_grid, np.nan, dtype=np.float32)
    padded_slope[1:-1, 1:-1] = slope_deg
    return padded_slope


def compute_terrain_roughness_index(elev_grid: np.ndarray) -> np.ndarray:
    """
    Computes Riley et al. Terrain Roughness Index (TRI) in meters:
    Mean absolute difference between central pixel and its 8 neighbors.
    """
    rows, cols = elev_grid.shape
    if rows < 3 or cols < 3:
        return np.full_like(elev_grid, np.nan, dtype=np.float32)

    center = elev_grid[1:-1, 1:-1]
    diffs = []
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            neighbor = elev_grid[1 + dr : rows - 1 + dr, 1 + dc : cols - 1 + dc]
            diffs.append(np.abs(neighbor - center))

    tri_interior = np.mean(np.array(diffs), axis=0)
    padded_tri = np.full_like(elev_grid, np.nan, dtype=np.float32)
    padded_tri[1:-1, 1:-1] = tri_interior
    return padded_tri


def compute_tile_geomorphometry(
    elev_m: np.ndarray,
    lat_center: float,
    radius_m: float,
    pixel_res_deg: float = 1.0 / 16.0,
    native_res_km: float = 2.0,
    min_valid_ratio: float = 0.70,
) -> Dict[str, Any]:
    """
    Extracts complete statistical and derivative geomorphometry for an analysis tile.

    Returns dictionary of scale-invariant terrain metrics, quality ratio,
    and effective resolution tracking.
    """
    total_pixels = elev_m.size
    valid_mask = ~np.isnan(elev_m)
    valid_count = int(np.sum(valid_mask))
    valid_ratio = valid_count / total_pixels if total_pixels > 0 else 0.0

    result = {
        "valid_count": valid_count,
        "total_pixels": total_pixels,
        "valid_ratio": float(valid_ratio),
        "native_res_km": float(native_res_km),
        "effective_res_km": float(native_res_km),
        "is_valid_coverage": valid_ratio >= min_valid_ratio,
        "mean_elevation_m": np.nan,
        "std_elevation_m": np.nan,
        "local_relief_m": np.nan,
        "mean_slope_deg": np.nan,
        "max_slope_deg": np.nan,
        "terrain_roughness_index_m": np.nan,
        "hypsometric_integral": np.nan,
        "hypsometric_skewness": np.nan,
    }

    if not result["is_valid_coverage"] or valid_count < 9:
        return result

    valid_vals = elev_m[valid_mask]
    min_elev = float(np.min(valid_vals))
    max_elev = float(np.max(valid_vals))
    mean_elev = float(np.mean(valid_vals))
    std_elev = float(np.std(valid_vals))
    relief = max_elev - min_elev

    result["mean_elevation_m"] = mean_elev
    result["std_elevation_m"] = std_elev
    result["local_relief_m"] = relief

    # Hypsometric Integral (HI) = (mean - min) / (max - min)
    if relief > 1e-3:
        result["hypsometric_integral"] = float((mean_elev - min_elev) / relief)
    else:
        result["hypsometric_integral"] = 0.5

    # Hypsometric distribution skewness
    if len(valid_vals) >= 3 and std_elev > 1e-4:
        result["hypsometric_skewness"] = float(stats.skew(valid_vals))
    else:
        result["hypsometric_skewness"] = 0.0

    # Physical slope & roughness calculations
    slope_grid = compute_spherical_slope_horn(
        elev_grid=elev_m,
        lat_deg=lat_center,
        radius_m=radius_m,
        pixel_dlat_deg=pixel_res_deg,
        pixel_dlon_deg=pixel_res_deg,
    )
    valid_slopes = slope_grid[~np.isnan(slope_grid)]
    if len(valid_slopes) > 0:
        result["mean_slope_deg"] = float(np.mean(valid_slopes))
        result["max_slope_deg"] = float(np.percentile(valid_slopes, 95))

    tri_grid = compute_terrain_roughness_index(elev_m)
    valid_tri = tri_grid[~np.isnan(tri_grid)]
    if len(valid_tri) > 0:
        result["terrain_roughness_index_m"] = float(np.mean(valid_tri))

    return result
