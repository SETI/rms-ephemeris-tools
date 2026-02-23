"""Tests for observer state behavior in SPICE observer utilities."""

from __future__ import annotations

import numpy as np
import pytest

from ephemeris_tools.constants import EARTH_ID
from ephemeris_tools.spice.common import get_state
from ephemeris_tools.spice.observer import observer_state, set_observer_location


def test_observer_state_geodetic_keeps_ssb_velocity(monkeypatch: pytest.MonkeyPatch) -> None:
    """Geodetic observer adjusts position only; velocity remains Earth SSB velocity."""

    monkeypatch.setattr(
        'cspyce.spkssb',
        lambda body_id, et, frame: [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
    )
    monkeypatch.setattr('cspyce.georec', lambda lon, lat, alt, rad, flat: [10.0, 20.0, 30.0])

    def _tipbod(frm: str, body: int, et: float) -> np.ndarray:
        assert frm == 'J2000'
        assert body == EARTH_ID
        assert et == 0.0
        return np.eye(3)

    monkeypatch.setattr('cspyce.tipbod', _tipbod)
    monkeypatch.setattr('cspyce.mtxv', lambda mat, vec: vec)

    state = get_state()
    monkeypatch.setattr(state, 'obs_id', EARTH_ID)
    monkeypatch.setattr(state, 'obs_is_set', False)
    monkeypatch.setattr(state, 'obs_lat', 0.0)
    monkeypatch.setattr(state, 'obs_lon', 0.0)
    monkeypatch.setattr(state, 'obs_alt', 0.0)

    set_observer_location(30.0, -100.0, 1000.0)
    out = observer_state(0.0)

    assert out[0] == 11.0
    assert out[1] == 22.0
    assert out[2] == 33.0
    assert out[3] == 4.0
    assert out[4] == 5.0
    assert out[5] == 6.0
