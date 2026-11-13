"""
Unit tests for Lunar TiO2 Calibration and Scientific Validation.

Tests:
1. Lucey et al. (2000) power-law formulation and spectral angle computation.
2. Comparison with legacy linear approximation (30 * R - 5).
3. Edge cases: zero reflectance, nodata, out-of-range reflectance.
4. Validation reporting and deviation (>5 wt% threshold).
"""

import pytest
import numpy as np

from src.processing.ti_calibration import (
    compute_theta_lucey2000,
    tio2_lucey2000,
    tio2_trial_polynomial,
    tio2_legacy_linear,
    validate_tio2_calibration,
    X0_LUCEY2000,
    Y0_LUCEY2000,
)


class TestLunarTiCalibration:
    def test_spectral_angle_lucey2000_origin(self):
        """At origin point (x0=0.00, y0=0.42), ratio=y0 gives numerator 0 -> theta=0."""
        r750 = np.array([0.10], dtype=np.float32)
        r415 = np.array([0.042], dtype=np.float32)  # ratio = 0.42
        theta = compute_theta_lucey2000(r415, r750)
        assert pytest.approx(float(theta[0]), abs=1e-5) == 0.0

    def test_tio2_lucey2000_typical_mare(self):
        """
        Typical high-Ti lunar mare (e.g. Apollo 11 / Mare Tranquillitatis):
        R750 ~ 0.09, R415 ~ 0.06 (R415/R750 ~ 0.67).
        Calculates positive theta and plausible TiO2 abundance (5 - 12 wt%).
        """
        r750 = np.array([0.09], dtype=np.float32)
        r415 = np.array([0.06], dtype=np.float32)
        tio2 = tio2_lucey2000(r415, r750)
        assert 3.0 <= float(tio2[0]) <= 15.0

    def test_tio2_lucey2000_typical_highlands(self):
        """
        Typical anorthositic highlands (e.g. Apollo 16):
        R750 ~ 0.22, R415 ~ 0.12 (R415/R750 ~ 0.55).
        Low TiO2 abundance (< 1.5 wt%).
        """
        r750 = np.array([0.22], dtype=np.float32)
        r415 = np.array([0.12], dtype=np.float32)
        tio2 = tio2_lucey2000(r415, r750)
        assert float(tio2[0]) < 2.0

    def test_tio2_bounds_clipping(self):
        """Abundance must be strictly clipped to [0.0, 20.0] wt%."""
        r750 = np.array([0.01, 0.50], dtype=np.float32)
        r415 = np.array([0.05, 0.10], dtype=np.float32)
        tio2 = tio2_lucey2000(r415, r750)
        assert np.all(tio2 >= 0.0)
        assert np.all(tio2 <= 20.0)

    def test_zero_and_negative_reflectance_handling(self):
        """Zero reflectance should not raise unhandled exception."""
        r750 = np.array([0.0, -1.0], dtype=np.float32)
        r415 = np.array([0.0, 0.0], dtype=np.float32)
        tio2 = tio2_lucey2000(r415, r750)
        assert tio2.shape == (2,)
        assert np.all(np.nan_to_num(tio2) >= 0.0)

    def test_validation_detects_legacy_linear_discrepancy(self):
        """
        Validates that legacy linear shortcut (30 * R - 5) produces large
        deviation (>5 wt% RMSE) compared to peer-reviewed Lucey et al. (2000).
        """
        # Synthetic grid covering typical lunar mare to highlands range
        np.random.seed(42)
        r750 = np.random.uniform(0.08, 0.25, size=(50, 50)).astype(np.float32)
        r415 = r750 * np.random.uniform(0.50, 0.70, size=(50, 50)).astype(np.float32)

        report = validate_tio2_calibration(r415, r750)
        assert report["valid"] is True
        assert report["sample_count"] == 2500
        # The legacy linear formula diverges significantly
        assert report["rmse_legacy_vs_published"] > 5.0
        assert report["legacy_linear_acceptable"] is False
        assert "Lucey" in report["recommendation"]

    def test_unavailable_when_r750_incompatible_or_missing(self):
        """
        Per scientific integrity rules, if R750 absolute reflectance is unavailable
        or outside physical reflectance bounds, TiO2 must be reported as unavailable
        rather than fabricating values with uncalibrated linear shortcuts.
        """
        # Non-physical R750 (e.g. all <= 0 or invalid)
        r750_bad = np.array([-9999.0, 0.0, -1.0], dtype=np.float32)
        r415 = np.array([0.05, 0.05, 0.05], dtype=np.float32)
        report = validate_tio2_calibration(r415, r750_bad)
        assert report["valid"] is False
        assert report["status"] == "UNAVAILABLE"
        assert report["rmse"] is None
