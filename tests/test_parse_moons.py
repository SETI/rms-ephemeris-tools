"""Tests for moon selection parsing (names, NAIF IDs, and groups)."""

from __future__ import annotations

from ephemeris_tools.planets import parse_moon_spec


def test_parse_moons_accepts_naif_id() -> None:
    """NAIF IDs are accepted directly."""
    moons = parse_moon_spec(8, ['802'])
    assert moons == [802]


def test_parse_moons_accepts_name_case_insensitive() -> None:
    """Moon names are accepted case-insensitively."""
    moons = parse_moon_spec(8, ['TrItOn'])
    assert moons == [801]


def test_parse_moons_accepts_cli_index() -> None:
    """Legacy moon index values are converted to NAIF IDs."""
    moons = parse_moon_spec(8, ['1'])
    assert moons == [801]


def test_parse_moons_keyword_classical_jupiter() -> None:
    """Jupiter classical group maps to J1-J4."""
    moons = parse_moon_spec(5, ['classical'])
    assert moons == [501, 502, 503, 504]


def test_parse_moons_keyword_classical_saturn() -> None:
    """Saturn classical group maps to S1-S9."""
    moons = parse_moon_spec(6, ['classical'])
    assert moons == [601, 602, 603, 604, 605, 606, 607, 608, 609]


def test_parse_moons_keyword_classical_uranus() -> None:
    """Uranus classical group maps to U1-U5."""
    moons = parse_moon_spec(7, ['classical'])
    assert moons == [701, 702, 703, 704, 705]


def test_parse_moons_keyword_classical_neptune() -> None:
    """Neptune classical group maps to Triton and Nereid."""
    moons = parse_moon_spec(8, ['classical'])
    assert moons == [801, 802]


def test_parse_moons_keyword_classical_pluto() -> None:
    """Pluto classical group maps to Charon only."""
    moons = parse_moon_spec(9, ['classical'])
    assert moons == [901]


def test_parse_moons_keyword_all_neptune() -> None:
    """All group maps to every Neptune moon in config order."""
    moons = parse_moon_spec(8, ['all'])
    assert moons == [801, 802, 803, 804, 805, 806, 807, 808, 814]


def test_parse_moons_keyword_all_mars() -> None:
    """All group maps to both Mars moons."""
    moons = parse_moon_spec(4, ['all'])
    assert moons == [401, 402]


def test_parse_moons_mixed_tokens_deduplicates() -> None:
    """Mixed tokens return unique IDs in first-seen order."""
    moons = parse_moon_spec(8, ['classical', 'triton', '802', 'nereid'])
    assert moons == [801, 802]
