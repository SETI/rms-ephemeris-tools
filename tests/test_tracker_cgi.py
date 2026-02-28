"""Tests for tracker CGI environment parsing."""

from __future__ import annotations

import pytest

from ephemeris_tools.params import tracker_params_from_env


def test_tracker_params_from_env_basic(monkeypatch: pytest.MonkeyPatch) -> None:
    """Tracker CGI env parses into TrackerParams."""
    monkeypatch.setenv('NPLANET', '6')
    monkeypatch.setenv('start', '2025-01-01 00:00')
    monkeypatch.setenv('stop', '2025-01-02 00:00')
    monkeypatch.setenv('interval', '1')
    monkeypatch.setenv('time_unit', 'hours')
    monkeypatch.setenv('viewpoint', 'observatory')
    monkeypatch.setenv('observatory', "Earth's center")
    monkeypatch.setenv('moons', '001 Mimas (S1)')
    monkeypatch.setenv('rings', '061 Main Rings')
    monkeypatch.setenv('xrange', '180')
    monkeypatch.setenv('xunit', 'arcsec')
    params = tracker_params_from_env()
    assert params is not None
    assert params.planet_num == 6
    assert params.start_time == '2025-01-01 00:00'
    assert params.observer.name == "Earth's center"
    assert params.stop_time == '2025-01-02 00:00'
    assert params.moon_ids == [601]
    assert params.ring_names == ['061 Main Rings']
    assert params.xrange == 180.0
    assert params.xunit == 'arcsec'


def test_tracker_params_from_env_observatory_with_coordinates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Named observatory with embedded coordinates sets observer geodetic fields."""

    monkeypatch.setenv('NPLANET', '5')
    monkeypatch.setenv('start', '2025-01-01 00:00')
    monkeypatch.setenv('stop', '2025-01-02 00:00')
    monkeypatch.setenv('interval', '1')
    monkeypatch.setenv('time_unit', 'hours')
    monkeypatch.setenv('viewpoint', 'observatory')
    monkeypatch.setenv(
        'observatory',
        'Apache Point Observatory (32.780361, -105.820417, 2674.)',
    )
    monkeypatch.setenv('moons', '001 Io (J1)')

    params = tracker_params_from_env()

    assert params is not None
    assert params.observer.name == 'Apache Point Observatory (32.780361, -105.820417, 2674.)'
    assert params.observer.latitude_deg == 32.780361
    assert params.observer.longitude_deg == -105.820417
    assert params.observer.altitude_m == 2674.0
