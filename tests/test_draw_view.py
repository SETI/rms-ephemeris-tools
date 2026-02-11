"""Tests for planet viewer PostScript rendering."""

from __future__ import annotations

from io import StringIO

import pytest

from ephemeris_tools.rendering.draw_view import draw_planetary_view


def test_draw_planetary_view_produces_diagram_not_stub() -> None:
    """draw_planetary_view emits real PostScript (Escher/Euclid preamble), not a stub."""
    out = StringIO()
    try:
        draw_planetary_view(
            out,
            obs_time=0.0,
            fov=0.01,
            center_ra=0.0,
            center_dec=0.0,
            planet_name='Saturn',
            title='Saturn  2025-01-01 12:00',
        )
    except (OSError, RuntimeError) as e:
        if 'SPICE' in str(e) or 'NOLOADEDFILES' in str(e):
            pytest.skip('SPICE kernels not loaded')
        raise
    s = out.getvalue()
    assert 'Planet view (stub)' not in s
    assert 'Saturn' in s
    assert '%%Creator:' in s
    assert 'PDS Ring-Moon Systems Node' in s
    assert 'showpage' in s
    assert '0.1 0.1 scale' in s
    assert '%Draw box...' in s or 'N\n' in s


def test_draw_planetary_view_with_grid_draws_limb_and_lineto() -> None:
    """draw_planetary_view emits PostScript with lineto/stroke (Escher/Euclid drawing)."""
    out = StringIO()
    try:
        draw_planetary_view(
            out,
            obs_time=0.0,
            fov=0.01,
            center_ra=0.0,
            center_dec=0.0,
            planet_name='Saturn',
            title='Saturn',
        )
    except (OSError, RuntimeError) as e:
        if 'SPICE' in str(e) or 'NOLOADEDFILES' in str(e):
            pytest.skip('SPICE kernels not loaded')
        raise
    s = out.getvalue()
    assert '/L {lineto} def' in s or 'lineto' in s
    assert 'stroke' in s or 'S\n' in s
    assert '%%Creator:' in s
