"""
Scientific Calibration and Validation for Lunar TiO2 from Clementine UVVIS.

References:
1. Lucey, P. G., Blewett, D. T., & Jolliff, B. L. (2000).
   "Lunar iron and titanium abundance algorithms based on final processing of Clementine
   ultraviolet-visible images." Journal of Geophysical Research: Planets, 105(E8), 20297-20305.
2. Gillis, J. J., Lucey, P. G., & Blewett, D. T. (2003).
   "A new calibration for Lunar Prospector and Clementine optical data."
   Journal of Geophysical Research: Planets.

Original Publication Formulation (Lucey et al. 2000):
   Origin coordinates: x0_Ti = 0.00, y0_Ti = 0.42
   Angle: theta_Ti = arctan(((R415 / R750) - y0_Ti) / (R750 - x0_Ti)) [in radians]
   Abundance: wt% TiO2 = 3.708 * (theta_Ti ** 5.979)
"""

import numpy as np
from typing import Tuple, Dict, Any, Optional

# Lucey et al. (2000) Ground-Truth Calibration Parameters
X0_LUCEY2000 = 0.00
Y0_LUCEY2000 = 0.42
COEFF_A_LUCEY2000 = 3.708
EXPONENT_B_LUCEY2000 = 5.979

# Heuristic / Trial Polynomial parameters previously suggested in discussions:
# x0 = 0.23, y0 = 0.05, a0 = -0.0135, a1 = 1.03, a2 = 0.0
X0_TRIAL = 0.23
Y0_TRIAL = 0.05
A0_TRIAL = -0.0135
A1_TRIAL = 1.03
A2_TRIAL = 0.0


def compute_theta_lucey2000(r415: np.ndarray, r750: np.ndarray) -> np.ndarray:
    """
    Compute the titanium spectral parameter theta_Ti per Lucey et al. (2000).
    theta_Ti = arctan(((R415 / R750) - 0.42) / (R750 - 0.00))
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = np.where(r750 > 0, r415 / r750, np.nan)
        theta = np.arctan((ratio - Y0_LUCEY2000) / (r750 - X0_LUCEY2000))
    return theta


def tio2_lucey2000(r415: np.ndarray, r750: np.ndarray) -> np.ndarray:
    """
    Compute wt% TiO2 using the peer-reviewed Lucey et al. (2000) power-law formulation:
    TiO2 (wt%) = 3.708 * (theta_Ti ** 5.979)
    Clipped to physical lunar basalt bounds: [0.0, 20.0] wt%.
    """
    theta = compute_theta_lucey2000(r415, r750)
    with np.errstate(invalid='ignore'):
        # theta must be positive for fractional power
        theta_pos = np.clip(theta, 0.0, None)
        tio2 = COEFF_A_LUCEY2000 * (theta_pos ** EXPONENT_B_LUCEY2000)
        # Any negative theta or invalid inputs are clipped to 0
        tio2 = np.nan_to_num(tio2, nan=np.nan)
    return np.clip(tio2, 0.0, 20.0)


def tio2_trial_polynomial(r415: np.ndarray, r750: np.ndarray) -> np.ndarray:
    """
    Compute TiO2 using the trial polynomial:
    theta = arctan(((R415 / R750) - 0.05) / (R750 - 0.23))
    TiO2 = a0 + a1 * theta + a2 * theta**2
    """
    with np.errstate(divide='ignore', invalid='ignore'):
        ratio = np.where(r750 > 0, r415 / r750, np.nan)
        theta = np.arctan((ratio - Y0_TRIAL) / (r750 - X0_TRIAL))
        tio2 = A0_TRIAL + A1_TRIAL * theta + A2_TRIAL * (theta ** 2)
    return np.clip(tio2, 0.0, 20.0)


def tio2_legacy_linear(r_band1: np.ndarray, a: float = 30.0, b: float = -5.0) -> np.ndarray:
    """
    Legacy linear shortcut previously implemented in mineral_extraction.py:
    TiO2 = a * R + b
    """
    tio2 = a * r_band1 + b
    return np.clip(tio2, 0.0, 30.0)


def validate_tio2_calibration(
    r415: np.ndarray,
    r750: np.ndarray,
    legacy_red: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """
    Validates calibration models on actual or representative reflectance values.
    Compares the legacy linear shortcut against the published Lucey et al. (2000) equation.
    Returns RMSE, max absolute difference, and scientific validity verdict.
    """
    valid_mask = (r750 > 0.01) & (r415 > 0.01) & np.isfinite(r750) & np.isfinite(r415)
    if not np.any(valid_mask):
        return {
            "valid": False,
            "error": "No valid pixels for calibration comparison",
            "rmse": None,
            "max_abs_diff": None,
            "status": "UNAVAILABLE",
        }

    r415_v = r415[valid_mask]
    r750_v = r750[valid_mask]

    # Published ground-truth model
    tio2_pub = tio2_lucey2000(r415_v, r750_v)

    # Legacy model
    if legacy_red is not None:
        red_v = legacy_red[valid_mask]
    else:
        red_v = r750_v / r415_v  # Red channel was documented as 750/415 ratio
    tio2_lin = tio2_legacy_linear(red_v)

    diff = tio2_lin - tio2_pub
    rmse = float(np.sqrt(np.mean(diff ** 2)))
    max_diff = float(np.max(np.abs(diff)))

    # Lucey trial polynomial comparison
    tio2_trial = tio2_trial_polynomial(r415_v, r750_v)
    trial_diff = tio2_trial - tio2_pub
    trial_rmse = float(np.sqrt(np.mean(trial_diff ** 2)))

    is_legacy_acceptable = rmse < 5.0

    return {
        "valid": True,
        "sample_count": int(np.sum(valid_mask)),
        "published_mean_wt_pct": float(np.nanmean(tio2_pub)),
        "published_max_wt_pct": float(np.nanmax(tio2_pub)),
        "legacy_mean_wt_pct": float(np.nanmean(tio2_lin)),
        "rmse_legacy_vs_published": rmse,
        "max_abs_diff_legacy_vs_published": max_diff,
        "trial_poly_rmse_vs_published": trial_rmse,
        "legacy_linear_acceptable": is_legacy_acceptable,
        "scientific_verdict": (
            "Legacy linear approximation deviates substantially (>5 wt%) from published Lucey 2000 calibration."
            if not is_legacy_acceptable else
            "Legacy linear approximation within tolerance."
        ),
        "recommendation": "Use peer-reviewed Lucey et al. (2000) power-law or USGS Clementine TiO2 product directly."
    }
