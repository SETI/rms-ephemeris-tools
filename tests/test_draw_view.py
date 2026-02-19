"""Tests for planet viewer PostScript rendering."""

from __future__ import annotations

from io import StringIO

import pytest

from ephemeris_tools.rendering.draw_view import (
    DrawPlanetaryViewOptions,
    _rspk_write_label,
    draw_planetary_view,
)
from ephemeris_tools.rendering.escher import EscherState


def test_draw_planetary_view_produces_diagram_not_stub() -> None:
    """draw_planetary_view emits real PostScript (Escher/Euclid preamble), not a stub."""
    out = StringIO()
    try:
        options = DrawPlanetaryViewOptions(
            obs_time=0.0,
            fov=0.01,
            center_ra=0.0,
            center_dec=0.0,
            planet_name='Saturn',
            title='Saturn  2025-01-01 12:00',
        )
        draw_planetary_view(out, options)
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
        options = DrawPlanetaryViewOptions(
            obs_time=0.0,
            fov=0.01,
            center_ra=0.0,
            center_dec=0.0,
            planet_name='Saturn',
            title='Saturn',
        )
        draw_planetary_view(out, options)
    except (OSError, RuntimeError) as e:
        if 'SPICE' in str(e) or 'NOLOADEDFILES' in str(e):
            pytest.skip('SPICE kernels not loaded')
        raise
    s = out.getvalue()
    assert '/L {lineto} def' in s or 'lineto' in s
    assert 'stroke' in s or 'S\n' in s
    assert '%%Creator:' in s


def test_rspk_write_label_negative_left_has_no_space_after_minus() -> None:
    """Negative declination labels should be like '-11 20 31.9', not '- 11 ...'."""
    out = StringIO()
    state = EscherState()
    state.outuni = out
    _rspk_write_label(-11.0 * 3600.0, 'L', state)
    s = out.getvalue()
    assert '(-11' in s
    assert '(- 11' not in s


def test_rspk_write_label_bottom_omits_fraction_when_whole_second() -> None:
    """Bottom-axis labels should omit trailing .000 for whole-second values."""
    out = StringIO()
    state = EscherState()
    state.outuni = out
    _rspk_write_label(3.0 * 3600.0 + 44.0 * 60.0, 'B', state)
    s = out.getvalue()
    assert '(3 44 00) LabelBelow' in s
    assert '(3 44 00.000) LabelBelow' not in s


def test_rspk_write_label_left_keeps_millisecond_precision() -> None:
    """Left-axis labels keep 3 decimal places like FORTRAN."""
    out = StringIO()
    state = EscherState()
    state.outuni = out
    _rspk_write_label(-(21 * 3600 + 58 * 60 + 49.001), 'L', state)
    s = out.getvalue()
    assert '(-21 58 49.001) LabelLeft' in s
