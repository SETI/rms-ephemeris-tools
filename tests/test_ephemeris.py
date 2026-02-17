"""Tests for ephemeris generator (no SPICE kernels required for param/record logic)."""

from __future__ import annotations

import io

from ephemeris_tools.params import (
    EphemerisParams,
)
from ephemeris_tools.record import Record


def test_record_append_and_write() -> None:
    """Record first field has no leading space; later fields get one blank."""
    r = Record()
    r.init()
    r.append('a')
    r.append('b')
    r.append('c')
    line = r.get_line()
    assert line == 'a b c'
    buf = io.StringIO()
    r.write(buf)
    assert buf.getvalue() == 'a b c\n'
    assert r.get_line() == ''


def test_ephemeris_params_defaults() -> None:
    """EphemerisParams has sensible defaults."""
    p = EphemerisParams(
        planet_num=6,
        start_time='2025-01-01 00:00',
        stop_time='2025-01-01 02:00',
    )
    assert p.planet_num == 6
    assert p.interval == 1.0
    assert p.time_unit == 'hour'


def test_interval_seconds() -> None:
    """Interval conversion via time_utils.interval_seconds (ephemeris default)."""
    from ephemeris_tools.time_utils import interval_seconds

    assert interval_seconds(1, 'hour') == 3600.0
    assert interval_seconds(1, 'day') == 86400.0
    assert interval_seconds(5, 'min') == 300.0
    assert interval_seconds(0.5, 'sec') == 1.0  # min_seconds=1 default
    assert interval_seconds(1, 'min', min_seconds=60.0, round_to_minutes=True) == 60.0
    assert interval_seconds(90, 'sec', min_seconds=60.0, round_to_minutes=True) == 120.0


def test_start_second_normalization_rounds_to_minutes_for_all_units() -> None:
    """Ephemeris start boundary seconds always round to minute precision."""
    from ephemeris_tools.ephemeris import _normalized_start_sec

    assert _normalized_start_sec(8.0, 'sec') == 0.0
    assert _normalized_start_sec(8.0, 'min') == 0.0
    assert _normalized_start_sec(8.0, 'hour') == 0.0
    assert _normalized_start_sec(8.0, 'day') == 0.0
    assert _normalized_start_sec(30.0, 'sec') == 60.0


def test_set_observer_from_params_parses_observatory_coordinates(monkeypatch) -> None:
    """Observatory strings with embedded coordinates set topocentric observer."""
    from ephemeris_tools.ephemeris import _set_observer_from_params

    called: dict[str, tuple[float, float, float]] = {}

    def _fake_set_observer_location(lat: float, lon: float, alt: float) -> None:
        called['coords'] = (lat, lon, alt)

    monkeypatch.setattr('ephemeris_tools.ephemeris.set_observer_location', _fake_set_observer_location)
    monkeypatch.setattr('ephemeris_tools.ephemeris.set_observer_id', lambda _obs_id: None)

    params = EphemerisParams(
        planet_num=5,
        start_time='2000-01-01 00:00:00',
        stop_time='2000-01-01 01:00:00',
        observatory='Apache Point Observatory (32.780361, -105.820417, 2674.)',
    )

    _set_observer_from_params(params)

    assert called['coords'] == (32.780361, -105.820417, 2674.0)
