"""Tests for observer token parsing."""

from __future__ import annotations

import pytest

from ephemeris_tools.params import parse_observer


def test_parse_observer_earth_keyword() -> None:
    """Earth keyword normalizes to canonical Earth observer."""
    observer = parse_observer(['earth'])
    assert observer.name == "Earth's center"
    assert observer.latitude_deg is None
    assert observer.longitude_deg is None
    assert observer.altitude_m is None


def test_parse_observer_spacecraft_keyword() -> None:
    """Spacecraft-like names are preserved."""
    observer = parse_observer(['cassini'])
    assert observer.name == 'cassini'


def test_parse_observer_lat_lon_alt_triplet() -> None:
    """Three numeric tokens map to explicit lat/lon/alt observer."""
    observer = parse_observer(['19.827', '-155.472', '4215'])
    assert observer.name is None
    assert observer.latitude_deg == 19.827
    assert observer.longitude_deg == -155.472
    assert observer.altitude_m == 4215.0


def test_parse_observer_named_observatory_phrase() -> None:
    """Named observatories preserve the phrase."""
    observer = parse_observer(['Mauna', 'Kea', 'Observatory'])
    assert observer.name == 'Mauna Kea Observatory'


def test_parse_observer_defaults_to_earth() -> None:
    """Empty observer token list defaults to Earth center."""
    observer = parse_observer([])
    expected = parse_observer(['earth'])
    assert observer.name == "Earth's center"
    assert observer.latitude_deg == expected.latitude_deg
    assert observer.longitude_deg == expected.longitude_deg
    assert observer.altitude_m == expected.altitude_m


def test_parse_observer_invalid_numeric_arity() -> None:
    """Two numeric tokens are rejected because altitude is required."""
    with pytest.raises(ValueError, match='three numeric tokens'):
        parse_observer(['10', '20'])
