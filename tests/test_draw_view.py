"""Tests for planet viewer PostScript rendering."""

from __future__ import annotations

from io import StringIO

import pytest

from ephemeris_tools.rendering.draw_view import draw_planetary_view


def test_draw_planetary_view_produces_diagram_not_stub() -> None:
    """draw_planetary_view emits real PostScript (planet disk, labels), not a stub."""
    out = StringIO()
    bodies = [
        (0.0, 0.0, "Saturn", True),
        (50.0, 30.0, "TITAN", False),
    ]
    draw_planetary_view(
        out,
        planet_name="Saturn",
        limb_radius_plot=40.0,
        bodies_plot=bodies,
        title="Saturn  2025-01-01 12:00",
    )
    s = out.getvalue()
    assert "Planet view (stub)" not in s
    assert "Saturn" in s
    assert "TITAN" in s
    assert "arc" in s
    assert "%%Creator: ephemeris_tools" in s
    assert "showpage" in s


def test_draw_planetary_view_with_grid_draws_limb_and_lineto() -> None:
    """With planet_grid_segments, planet is drawn with limb + lat/lon lines (no fill)."""
    out = StringIO()
    bodies = [(0.0, 0.0, "Saturn", True)]
    grid_segments: list[tuple[list[tuple[float, float]], str]] = [
        ([(10.0, 0.0), (-10.0, 0.0)], "lit"),
        ([(0.0, 10.0), (0.0, -10.0)], "dark"),
    ]
    draw_planetary_view(
        out,
        planet_name="Saturn",
        limb_radius_plot=40.0,
        bodies_plot=bodies,
        title="Saturn",
        planet_grid_segments=grid_segments,
    )
    s = out.getvalue()
    assert "lineto" in s
    assert "stroke" in s
    assert "0 setgray" in s
    assert "0.85 setgray" in s
    assert "%%Creator: ephemeris_tools" in s
