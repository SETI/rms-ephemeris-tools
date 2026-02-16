"""Tests for julian time utility initialization behavior."""

from __future__ import annotations

from ephemeris_tools import time_utils


def test_ensure_leapsecs_sets_spice_ut_model(monkeypatch) -> None:
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

