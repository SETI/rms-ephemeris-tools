"""Tests for parsing viewer --fov token lists."""

from __future__ import annotations

import pytest

from ephemeris_tools.params import parse_fov


def test_parse_fov_degrees_short() -> None:
    """Short degree unit parses to canonical degrees."""
    value, unit = parse_fov(['1.5', 'deg'])
    assert value == 1.5
    assert unit == 'degrees'


def test_parse_fov_arcmin_alias() -> None:
    """Arcminute aliases normalize to minutes of arc."""
    value, unit = parse_fov(['2', 'arcmin'])
    assert value == 2.0
    assert unit == 'minutes of arc'


def test_parse_fov_arcsec_alias() -> None:
    """Arcsecond aliases normalize to seconds of arc."""
    value, unit = parse_fov(['0.5', 'arcsec'])
    assert value == 0.5
    assert unit == 'seconds of arc'


def test_parse_fov_milliradian_alias() -> None:
    """mrad alias normalizes to milliradians."""
    value, unit = parse_fov(['3', 'mrad'])
    assert value == 3.0
    assert unit == 'milliradians'


def test_parse_fov_microradian_alias() -> None:
    """urad alias normalizes to microradians."""
    value, unit = parse_fov(['600', 'urad'])
    assert value == 600.0
    assert unit == 'microradians'


def test_parse_fov_kilometers_alias() -> None:
    """km alias normalizes to kilometers."""
    value, unit = parse_fov(['1000', 'km'])
    assert value == 1000.0
    assert unit == 'kilometers'


def test_parse_fov_planet_radii() -> None:
    """Planet radii units normalize planet name capitalization."""
    value, unit = parse_fov(['10', 'neptune', 'radii'])
    assert value == 10.0
    assert unit == 'Neptune radii'


def test_parse_fov_instrument_prefix_match() -> None:
    """Instrument abbreviations normalize to canonical unit strings."""
    value, unit = parse_fov(['3', 'Cassini', 'ISS', 'narrow'])
    assert value == 3.0
    assert unit == 'Cassini ISS narrow angle FOVs'


def test_parse_fov_voyager_wide() -> None:
    """Voyager wide-angle abbreviation is accepted."""
    value, unit = parse_fov(['1', 'voyager', 'iss', 'wide'])
    assert value == 1.0
    assert unit == 'Voyager ISS wide angle FOVs'


def test_parse_fov_galileo_ssi() -> None:
    """Galileo SSI abbreviation is accepted."""
    value, unit = parse_fov(['2', 'galileo', 'ssi'])
    assert value == 2.0
    assert unit == 'Galileo SSI FOVs'


def test_parse_fov_lorri() -> None:
    """LORRI abbreviation is accepted."""
    value, unit = parse_fov(['1', 'lorri'])
    assert value == 1.0
    assert unit == 'LORRI FOVs'


def test_parse_fov_requires_value() -> None:
    """Empty token list raises a clear ValueError."""
    with pytest.raises(ValueError, match='at least one token'):
        parse_fov([])


def test_parse_fov_requires_numeric_value() -> None:
    """First token must be numeric."""
    with pytest.raises(ValueError, match='first token must be numeric'):
        parse_fov(['degrees'])


def test_parse_fov_unknown_unit() -> None:
    """Unknown unit strings raise a clear ValueError."""
    with pytest.raises(ValueError, match='Unknown FOV unit'):
        parse_fov(['1', 'furlongs'])
