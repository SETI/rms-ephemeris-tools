"""Tests for viewer FOV unit conversion."""

from __future__ import annotations

import math

import pytest

from ephemeris_tools.planets import NEPTUNE_CONFIG
from ephemeris_tools.viewer import _fov_deg_from_unit


def test_fov_deg_from_planet_radii(monkeypatch: pytest.MonkeyPatch) -> None:
    """Planet-radii units use observer range and equatorial radius (angular size)."""
    monkeypatch.setattr(
        'ephemeris_tools.spice.geometry.planet_ranges',
        lambda _et: (0.0, 1_000_000.0),
    )
    result = _fov_deg_from_unit(10.0, 'Neptune radii', et=0.0, cfg=NEPTUNE_CONFIG)
    # Formula: fov * asin(equatorial_radius_km / obs_dist_km) * 180/pi
    expected = 10.0 * math.asin(NEPTUNE_CONFIG.equatorial_radius_km / 1_000_000.0) * 180.0 / math.pi
    assert result == pytest.approx(expected)


def test_fov_deg_from_kilometers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Kilometer units convert by observer range geometry."""
    monkeypatch.setattr(
        'ephemeris_tools.spice.geometry.planet_ranges',
        lambda _et: (0.0, 1_000_000.0),
    )
    result = _fov_deg_from_unit(1000.0, 'kilometers', et=0.0, cfg=NEPTUNE_CONFIG)
    expected = 2.0 * math.atan((1000.0 / 2.0) / 1_000_000.0) * 180.0 / math.pi
    assert result == pytest.approx(expected)
