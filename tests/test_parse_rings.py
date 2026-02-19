"""Tests for viewer ring-name parsing."""

from __future__ import annotations

from ephemeris_tools.params import parse_viewer_rings


def test_parse_viewer_rings_saturn_named_rings() -> None:
    """Saturn named rings normalize with canonical casing."""
    rings = parse_viewer_rings(6, ['a', 'b', 'c', 'f'])
    assert rings == ['A', 'B', 'C', 'F']


def test_parse_viewer_rings_uranus_named_rings() -> None:
    """Uranus named rings normalize with canonical casing."""
    rings = parse_viewer_rings(7, ['alpha', 'beta', 'epsilon'])
    assert rings == ['Alpha', 'Beta', 'Epsilon']


def test_parse_viewer_rings_neptune_named_rings() -> None:
    """Neptune ring names normalize to canonical names."""
    rings = parse_viewer_rings(8, ['leverrier', 'adams'])
    assert rings == ['LeVerrier', 'Adams']


def test_parse_viewer_rings_mars_named_rings() -> None:
    """Mars accepts moon-ring names."""
    rings = parse_viewer_rings(4, ['phobos', 'deimos'])
    assert rings == ['Phobos', 'Deimos']


def test_parse_viewer_rings_all_keyword() -> None:
    """All keyword expands to all names for the selected planet."""
    rings = parse_viewer_rings(8, ['all'])
    assert rings == ['Galle', 'LeVerrier', 'Arago', 'Adams']


def test_parse_viewer_rings_none_keyword() -> None:
    """None keyword disables all ring names."""
    rings = parse_viewer_rings(8, ['none'])
    assert rings == []


def test_parse_viewer_rings_deduplicates() -> None:
    """Duplicate names collapse to first-seen unique list."""
    rings = parse_viewer_rings(8, ['adams', 'Adams'])
    assert rings == ['Adams']
