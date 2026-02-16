"""Tests for tracker backend parameter adaptation."""

from __future__ import annotations

from io import StringIO
from types import SimpleNamespace

import cspyce
import pytest

from ephemeris_tools.params import Observer, TrackerParams
from ephemeris_tools.tracker import (
    _tracker_call_kwargs_from_params,
    run_tracker,
)


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


def test_tracker_matches_fortran_time_grid_split(monkeypatch) -> None:
    """Tracker samples geometry on stretched grid but labels fixed interval times."""

    sampled_ets: list[float] = []
    first_et: float | None = None
    plot_dts: list[float] = []

    monkeypatch.setattr(
        'ephemeris_tools.spice.load.load_spice_files',
        lambda planet_num, ephem_version: (True, ''),
    )
    monkeypatch.setattr('ephemeris_tools.spice.observer.set_observer_id', lambda obs_id: None)
    monkeypatch.setattr(
        'ephemeris_tools.viewer.get_planet_config',
        lambda planet_num: SimpleNamespace(
            moons=[
                SimpleNamespace(id=599, name='Jupiter'),
                SimpleNamespace(id=501, name='Io'),
            ]
        ),
    )
    monkeypatch.setattr(
        'ephemeris_tools.tracker.get_state',
        lambda: SimpleNamespace(planet_id=599),
    )
    monkeypatch.setattr(cspyce, 'bodvrd', lambda body, item: [71492.0, 0.0, 0.0])
    monkeypatch.setattr('ephemeris_tools.time_utils.tdb_from_tai', lambda tai: tai)

    def _fake_moon_tracker_offsets(et: float, moon_ids: list[int]) -> tuple[list[float], float]:
        del moon_ids
        nonlocal first_et
        if first_et is None:
            first_et = et
        sampled_ets.append(et)
        return ([(et - first_et) / 1000.0], 0.0)

    monkeypatch.setattr(
        'ephemeris_tools.spice.geometry.moon_tracker_offsets',
        _fake_moon_tracker_offsets,
    )
    monkeypatch.setattr(
        'ephemeris_tools.rendering.draw_tracker.draw_moon_tracks',
        lambda *args, **kwargs: plot_dts.append(float(kwargs['dt'])),
    )

    out = StringIO()
    out_ps = StringIO()
    run_tracker(
        planet_num=5,
        start_time='January 7 2015 00:00:00',
        stop_time='January 10 2015 00:00:00',
        interval=10,
        time_unit='hours',
        viewpoint="Earth's center",
        moon_ids=[501],
        output_ps=out_ps,
        output_txt=out,
    )

    assert len(sampled_ets) == 8
    assert sampled_ets[1] - sampled_ets[0] == pytest.approx(37028.57142857143)
    assert sampled_ets[-1] - sampled_ets[0] == pytest.approx(259200.0)
    assert plot_dts == [37028.57142857143]

    rows = out.getvalue().splitlines()
    second = rows[2]
    assert ' 10  0 ' in second
    assert second.rstrip().endswith('7637691.111')


def test_tracker_preserves_user_arcsec_xrange_below_ten(monkeypatch) -> None:
    """Tracker should keep explicit small arcsec ranges from CGI/CLI inputs."""

    captured_xranges: list[float] = []

    monkeypatch.setattr(
        'ephemeris_tools.spice.load.load_spice_files',
        lambda planet_num, ephem_version: (True, ''),
    )
    monkeypatch.setattr('ephemeris_tools.spice.observer.set_observer_id', lambda obs_id: None)
    monkeypatch.setattr(
        'ephemeris_tools.viewer.get_planet_config',
        lambda planet_num: SimpleNamespace(
            moons=[
                SimpleNamespace(id=899, name='Neptune'),
                SimpleNamespace(id=803, name='Naiad'),
            ]
        ),
    )
    monkeypatch.setattr(
        'ephemeris_tools.tracker.get_state',
        lambda: SimpleNamespace(planet_id=899),
    )
    monkeypatch.setattr(cspyce, 'bodvrd', lambda body, item: [24764.0, 0.0, 0.0])
    monkeypatch.setattr('ephemeris_tools.time_utils.tdb_from_tai', lambda tai: tai)
    monkeypatch.setattr(
        'ephemeris_tools.spice.geometry.moon_tracker_offsets',
        lambda et, moon_ids: ([0.00001], 0.0),
    )
    monkeypatch.setattr(
        'ephemeris_tools.rendering.draw_tracker.draw_moon_tracks',
        lambda *args, **kwargs: captured_xranges.append(float(kwargs['xrange'])),
    )

    run_tracker(
        planet_num=8,
        start_time='2030-01-23',
        stop_time='2030-01-25',
        interval=1.0,
        time_unit='hours',
        viewpoint='observatory',
        moon_ids=[803],
        xrange=5.0,
        xscaled=False,
        output_ps=StringIO(),
        output_txt=StringIO(),
    )

    assert captured_xranges == [5.0]


