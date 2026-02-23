"""Tests for julian time utility initialization behavior."""

from __future__ import annotations

import pytest

from ephemeris_tools import time_utils


def test_ensure_leapsecs_sets_spice_ut_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """Leap-second init uses SPICE-compatible UT model for FORTRAN parity."""

    calls: list[tuple[str, tuple[object, ...], dict[str, object]]] = []

    def _set_ut_model(model: str, future: object = None) -> None:
        del future
        calls.append(('set_ut_model', (model,), {}))

    def _load_lsk(path: str | None = None) -> None:
        del path
        calls.append(('load_lsk', (), {}))

    monkeypatch.setattr('julian.set_ut_model', _set_ut_model)
    monkeypatch.setattr('julian.load_lsk', _load_lsk)
    monkeypatch.setattr('ephemeris_tools.time_utils.get_leapsecs_path', lambda: 'dummy.tls')
    monkeypatch.setattr(time_utils, '_leapsecs_loaded', False)

    time_utils._ensure_leapsecs()

    assert calls[0][0] == 'set_ut_model'
    assert calls[0][1] == ('SPICE',)


def test_parse_datetime_accepts_iso_z_suffix() -> None:
    """ISO-8601 trailing Z parses as UTC like the same timestamp without Z."""

    with_z = time_utils.parse_datetime('2022-08-18T00:01:47Z')
    without_z = time_utils.parse_datetime('2022-08-18T00:01:47')

    assert with_z is not None
    assert without_z is not None
    assert with_z == without_z


def test_parse_datetime_accepts_year_hms_form() -> None:
    """FORTRAN-style 'YYYY HH:MM:SS' parses as Jan 1 at the given time."""

    compact = time_utils.parse_datetime('1700 01:01:01')
    explicit = time_utils.parse_datetime('1700-01-01 01:01:01')

    assert compact is not None
    assert explicit is not None
    assert compact == explicit
