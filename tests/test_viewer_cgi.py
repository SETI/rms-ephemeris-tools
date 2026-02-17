"""Tests for viewer CGI environment parsing."""

from __future__ import annotations

import pytest

from ephemeris_tools.params import viewer_params_from_env


def test_viewer_params_from_env_basic(monkeypatch: pytest.MonkeyPatch) -> None:
    """Viewer CGI env parses into ViewerParams."""
    monkeypatch.setenv('NPLANET', '8')
    monkeypatch.setenv('time', '2025-01-01 12:00')
    monkeypatch.setenv('fov', '3')
    monkeypatch.setenv('fov_unit', 'Neptune radii')
    monkeypatch.setenv('center', 'body')
    monkeypatch.setenv('center_body', 'Neptune')
    monkeypatch.setenv('viewpoint', 'observatory')
    monkeypatch.setenv('observatory', "Earth's Center")
    monkeypatch.setenv('moons', '802 Triton & Nereid')
    monkeypatch.setenv('rings', 'LeVerrier, Adams')
    params = viewer_params_from_env()
    assert params is not None
    assert params.planet_num == 8
    assert params.time_str == '2025-01-01 12:00'
    assert params.fov_value == 3.0
    assert params.fov_unit == 'Neptune radii'
    assert params.center.mode == 'body'
    assert params.center.body_name == 'Neptune'
    assert params.moon_ids == [801, 802]
    assert params.ring_names == ['LeVerrier', 'Adams']


def test_viewer_params_from_env_observatory_with_embedded_coords(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Observatory display strings with coords populate observer lat/lon/alt."""
    monkeypatch.setenv('NPLANET', '4')
    monkeypatch.setenv('time', '2001-01-01 00:00')
    monkeypatch.setenv('viewpoint', 'observatory')
    monkeypatch.setenv(
        'observatory',
        'Apache Point Observatory (32.780361, -105.820417, 2674.)',
    )
    params = viewer_params_from_env()
    assert params is not None
    assert params.observer.name is not None
    assert params.observer.latitude_deg == 32.780361
    assert params.observer.longitude_deg == -105.820417
    assert params.observer.altitude_m == 2674.0


def test_viewer_params_from_env_meridians_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    """Meridians yes/no parses into ViewerParams.meridians."""
    monkeypatch.setenv('NPLANET', '4')
    monkeypatch.setenv('time', '2001-01-01 00:00')
    monkeypatch.setenv('meridians', 'Yes')
    params = viewer_params_from_env()
    assert params is not None
    assert params.meridians is True


def test_viewer_params_from_env_title_labels_and_moonpts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Viewer CGI title/labels/moonpts are preserved in parsed params."""
    monkeypatch.setenv('NPLANET', '4')
    monkeypatch.setenv('time', '2001-01-01 00:00')
    monkeypatch.setenv('title', "Hubble's Closest View of Mars")
    monkeypatch.setenv('labels', 'Large (12 points)')
    monkeypatch.setenv('moonpts', '2.5')
    params = viewer_params_from_env()
    assert params is not None
    assert params.title == "Hubble's Closest View of Mars"
    assert params.labels == 'Large (12 points)'
    assert params.moonpts == 2.5


def test_viewer_params_from_env_j2000_sexagesimal(monkeypatch: pytest.MonkeyPatch) -> None:
    """J2000 CGI center supports sexagesimal RA/Dec parsing."""
    monkeypatch.setenv('NPLANET', '9')
    monkeypatch.setenv('time', '2018-08-15 05:32:32')
    monkeypatch.setenv('center', 'J2000')
    monkeypatch.setenv('center_ra', '19 22 10.4687')
    monkeypatch.setenv('center_ra_type', 'hours')
    monkeypatch.setenv('center_dec', '-21 58 49.020')
    params = viewer_params_from_env()
    assert params is not None
    assert params.center.mode == 'J2000'
    assert params.center.ra_deg is not None
    assert params.center.dec_deg is not None
    assert abs(params.center.ra_deg - 290.5436195833333) < 1e-9
    assert abs(params.center.dec_deg - (-21.980283333333334)) < 1e-9


def test_viewer_params_from_env_additional_extra_star(monkeypatch: pytest.MonkeyPatch) -> None:
    """CGI additional star fields parse into ViewerParams.extra_star."""
    monkeypatch.setenv('NPLANET', '9')
    monkeypatch.setenv('time', '2018-08-15 05:32:32')
    monkeypatch.setenv('additional', 'Yes')
    monkeypatch.setenv('extra_ra', '19 22 10.4687')
    monkeypatch.setenv('extra_ra_type', 'hours')
    monkeypatch.setenv('extra_dec', '-21 58 49.020')
    monkeypatch.setenv('extra_name', 'Occulted Star')
    params = viewer_params_from_env()
    assert params is not None
    assert params.show_standard_stars is True
    assert params.extra_star is not None
    assert params.extra_star.name == 'Occulted Star'
    assert abs(params.extra_star.ra_deg - 290.5436195833333) < 1e-9
    assert abs(params.extra_star.dec_deg - (-21.980283333333334)) < 1e-9


def test_viewer_params_from_env_other_bodies(monkeypatch: pytest.MonkeyPatch) -> None:
    """CGI other-body selections are captured for background stars."""
    monkeypatch.setenv('NPLANET', '7')
    monkeypatch.setenv('time', '1986-01-24 21:00:00')
    monkeypatch.setenv('other', 'Sun')
    params = viewer_params_from_env()
    assert params is not None
    assert params.other_bodies == ['Sun']


def test_viewer_params_from_env_latlon_viewpoint_display_precision(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Lat/lon viewpoint caption preserves CGI precision."""
    monkeypatch.setenv('NPLANET', '9')
    monkeypatch.setenv('time', '2018-08-15 05:32:32')
    monkeypatch.setenv('viewpoint', 'latlon')
    monkeypatch.setenv('latitude', '33.2319835')
    monkeypatch.setenv('longitude', '-116.7600221')
    monkeypatch.setenv('lon_dir', 'east')
    monkeypatch.setenv('altitude', '844')
    params = viewer_params_from_env()
    assert params is not None
    assert params.display is not None
    assert params.display.viewpoint_display == '(33.2319835, -116.7600221 east, 844)'


def test_viewer_params_from_env_latlon_west_longitude(monkeypatch: pytest.MonkeyPatch) -> None:
    """Lat/lon viewpoint applies lon_dir west sign convention."""
    monkeypatch.setenv('NPLANET', '7')
    monkeypatch.setenv('time', '2001-01-21 00:17:00')
    monkeypatch.setenv('viewpoint', 'latlon')
    monkeypatch.setenv('latitude', '33.3563')
    monkeypatch.setenv('longitude', '116.8650')
    monkeypatch.setenv('lon_dir', 'west')
    monkeypatch.setenv('altitude', '1712')
    params = viewer_params_from_env()
    assert params is not None
    assert params.observer.latitude_deg == 33.3563
    assert params.observer.longitude_deg == -116.865
    assert params.observer.lon_dir == 'west'
    assert params.observer.altitude_m == 1712.0
