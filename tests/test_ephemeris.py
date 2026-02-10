"""Tests for ephemeris generator (no SPICE kernels required for param/record logic)."""

from __future__ import annotations

import io

import pytest

from ephemeris_tools.params import (
    COL_MJD,
    COL_PHASE,
    COL_RADEC,
    EphemerisParams,
    ephemeris_params_from_env,
)
from ephemeris_tools.record import Record


def test_record_append_and_write() -> None:
    """Record first field has no leading space; later fields get one blank."""
    r = Record()
    r.init()
    r.append("a")
    r.append("b")
    r.append("c")
    line = r.get_line()
    assert line == "a b c"
    buf = io.StringIO()
    r.write(buf)
    assert buf.getvalue() == "a b c\n"
    assert r.get_line() == ""


def test_ephemeris_params_defaults() -> None:
    """EphemerisParams has sensible defaults."""
    p = EphemerisParams(
        planet_num=6,
        start_time="2025-01-01 00:00",
        stop_time="2025-01-01 02:00",
    )
    assert p.planet_num == 6
    assert p.interval == 1.0
    assert p.time_unit == "hour"


def test_interval_seconds() -> None:
    """Interval conversion via time_utils.interval_seconds (ephemeris default)."""
    from ephemeris_tools.time_utils import interval_seconds

    assert interval_seconds(1, "hour") == 3600.0
    assert interval_seconds(1, "day") == 86400.0
    assert interval_seconds(5, "min") == 300.0
    assert interval_seconds(0.5, "sec") == 1.0  # min_seconds=1 default
    assert interval_seconds(1, "min", min_seconds=60.0, round_to_minutes=True) == 60.0
    assert interval_seconds(90, "sec", min_seconds=60.0, round_to_minutes=True) == 120.0
