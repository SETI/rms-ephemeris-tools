"""Tests for viewer FOV unit conversion."""

from __future__ import annotations

import math

from ephemeris_tools.planets import NEPTUNE_CONFIG
from ephemeris_tools.viewer import _fov_deg_from_unit


def test_fov_deg_from_planet_radii(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Planet-radii units use angular limb radius conversion."""
    monkeypatch.setattr('ephemeris_tools.spice.geometry.limb_radius', lambda _et: (1.0, 0.01))
    result = _fov_deg_from_unit(10.0, 'Neptune radii', et=0.0, cfg=NEPTUNE_CONFIG)
    expected = 10.0 * (0.01 * 180.0 / math.pi)
    assert result == expected


def test_fov_deg_from_kilometers(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Kilometer units convert by observer range geometry."""
    monkeypatch.setattr(
        'ephemeris_tools.spice.geometry.planet_ranges',
        lambda _et: (0.0, 1_000_000.0),
    )
    result = _fov_deg_from_unit(1000.0, 'kilometers', et=0.0, cfg=NEPTUNE_CONFIG)
    expected = 2.0 * math.atan((1000.0 / 2.0) / 1_000_000.0) * 180.0 / math.pi
    assert result == expected
