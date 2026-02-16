"""Tests for tracker backend parameter adaptation."""

from __future__ import annotations

from ephemeris_tools.params import Observer, TrackerParams
from ephemeris_tools.tracker import _tracker_call_kwargs_from_params


def test_tracker_call_kwargs_from_params_maps_fields() -> None:
    """TrackerParams maps to legacy kwargs consistently."""
    params = TrackerParams(
        planet_num=6,
        start_time='2025-01-01 00:00',
        stop_time='2025-01-02 00:00',
        interval=2.0,
        time_unit='hours',
        observer=Observer(name='JWST'),
        ephem_version=0,
        moon_ids=[601, 602],
        xrange=10.0,
        xunit='arcsec',
        title='Test',
    )
    kwargs = _tracker_call_kwargs_from_params(params)
    assert kwargs['planet_num'] == 6
    assert kwargs['start_time'] == '2025-01-01 00:00'
    assert kwargs['stop_time'] == '2025-01-02 00:00'
    assert kwargs['interval'] == 2.0
    assert kwargs['time_unit'] == 'hours'
    assert kwargs['viewpoint'] == 'JWST'
    assert kwargs['moon_ids'] == [601, 602]
    assert kwargs['xrange'] == 10.0
    assert kwargs['xscaled'] is False
    assert kwargs['title'] == 'Test'


def test_tracker_call_kwargs_from_params_radii_unit_sets_scaled() -> None:
    """Radii xunit sets xscaled=True in legacy kwargs."""
    params = TrackerParams(
        planet_num=6,
        start_time='2025-01-01 00:00',
        stop_time='2025-01-02 00:00',
        observer=Observer(name=None),
        xunit='saturn radii',
    )
    kwargs = _tracker_call_kwargs_from_params(params)
    assert kwargs['xscaled'] is True
    assert kwargs['viewpoint'] == 'Earth'
