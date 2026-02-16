"""Tests for viewer backend parameter adaptation."""

from __future__ import annotations

from ephemeris_tools.params import Observer, ViewerCenter, ViewerParams
from ephemeris_tools.viewer import _viewer_call_kwargs_from_params


def test_viewer_call_kwargs_from_params_j2000_center() -> None:
    """ViewerParams with J2000 center maps to legacy kwargs correctly."""
    params = ViewerParams(
        planet_num=8,
        time_str='2025-01-01 12:00',
        fov_value=3.0,
        fov_unit='degrees',
        center=ViewerCenter(mode='J2000', ra_deg=12.5, dec_deg=-30.0),
        observer=Observer(name='JWST'),
        ephem_version=0,
        moon_ids=[801, 802],
        ring_names=['LeVerrier', 'Adams'],
        blank_disks=True,
    )
    kwargs = _viewer_call_kwargs_from_params(params)
    assert kwargs['planet_num'] == 8
    assert kwargs['time_str'] == '2025-01-01 12:00'
    assert kwargs['fov'] == 3.0
    assert kwargs['fov_unit'] == 'degrees'
    assert kwargs['center_ra'] == 12.5
    assert kwargs['center_dec'] == -30.0
    assert kwargs['viewpoint'] == 'JWST'
    assert kwargs['moon_ids'] == [801, 802]
    assert kwargs['ring_selection'] == ['LeVerrier', 'Adams']
    assert kwargs['blank_disks'] is True


def test_viewer_call_kwargs_from_params_defaults_body_center() -> None:
    """Non-J2000 center falls back to planet-centered legacy coordinates."""
    params = ViewerParams(
        planet_num=6,
        time_str='2025-01-01 12:00',
        center=ViewerCenter(mode='body', body_name='Saturn'),
        observer=Observer(name=None),
    )
    kwargs = _viewer_call_kwargs_from_params(params)
    assert kwargs['center_ra'] == 0.0
    assert kwargs['center_dec'] == 0.0
    assert kwargs['viewpoint'] == 'Earth'
