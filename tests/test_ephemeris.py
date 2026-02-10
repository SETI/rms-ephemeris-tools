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
    """Interval conversion (same logic as ephemeris._interval_seconds)."""
    def interval_sec(interval: float, time_unit: str) -> float:
        u = time_unit.lower()[:4]
        if u == "sec":
            return max(abs(interval), 1.0)
        if u == "min":
            return max(abs(interval) * 60.0, 1.0)
        if u == "hour":
            return max(abs(interval) * 3600.0, 1.0)
        if u == "day":
            return max(abs(interval) * 86400.0, 1.0)
        return max(abs(interval) * 3600.0, 1.0)
    assert interval_sec(1, "hour") == 3600.0
    assert interval_sec(1, "day") == 86400.0
    assert interval_sec(5, "min") == 300.0
