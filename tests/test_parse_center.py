"""Tests for parsing viewer --center token lists."""

from __future__ import annotations

from ephemeris_tools.params import parse_center


def test_parse_center_defaults_to_planet_body() -> None:
    """Empty center tokens default to selected planet body center."""
    center = parse_center(8, [])
    assert center.mode == 'body'
    assert center.body_name == 'Neptune'
    assert center.ansa_name is None
    assert center.ansa_ew is None
    assert center.ra_deg is None
    assert center.dec_deg is None
    assert center.star_name is None


def test_parse_center_body_planet_name() -> None:
    """Planet name maps to body mode."""
    center = parse_center(8, ['neptune'])
    assert center.mode == 'body'
    assert center.body_name == 'Neptune'


def test_parse_center_body_moon_name() -> None:
    """Moon name maps to body mode."""
    center = parse_center(8, ['triton'])
    assert center.mode == 'body'
    assert center.body_name == 'Triton'


def test_parse_center_ansa_with_direction() -> None:
    """Ring ansa name with direction maps to ansa mode."""
    center = parse_center(8, ['leverrier', 'ring', 'west'])
    assert center.mode == 'ansa'
    assert center.ansa_name == 'LeVerrier Ring'
    assert center.ansa_ew == 'west'


def test_parse_center_ansa_defaults_east() -> None:
    """Ring ansa name without direction defaults to east."""
    center = parse_center(8, ['adams', 'ring'])
    assert center.mode == 'ansa'
    assert center.ansa_name == 'Adams Ring'
    assert center.ansa_ew == 'east'


def test_parse_center_j2000_numeric_pair() -> None:
    """Two numeric tokens map to J2000 center in degrees."""
    center = parse_center(8, ['12.5', '-30.2'])
    assert center.mode == 'J2000'
    assert center.ra_deg == 12.5
    assert center.dec_deg == -30.2


def test_parse_center_j2000_ra_hours_suffix() -> None:
    """RA token with hour suffix converts to degrees."""
    center = parse_center(8, ['1.5h', '-30.0'])
    assert center.mode == 'J2000'
    assert center.ra_deg == 22.5
    assert center.dec_deg == -30.0


def test_parse_center_star_name_fallback() -> None:
    """Unknown text falls back to star mode."""
    center = parse_center(8, ['sirius'])
    assert center.mode == 'star'
    assert center.star_name == 'sirius'
