"""Tests for spacecraft kernel loading observer behavior."""

from __future__ import annotations

from pathlib import Path

from ephemeris_tools.spice.common import get_state
from ephemeris_tools.spice.load import load_spacecraft


def test_load_spacecraft_sets_body_observer_without_geodetic_flag(
    monkeypatch, tmp_path: Path
) -> None:
    """Spacecraft observer should not enable geodetic observatory correction.

    FORTRAN `RSPK_SetObsId` clears `obs_is_set` for body observers. If this flag
    stays True, geometry code incorrectly applies Earth surface offset math to a
    spacecraft observer.
    """

    spice_dir = tmp_path / 'spice'
    spice_dir.mkdir()
    config = spice_dir / 'SPICE_spacecraft.txt'
    kernel = spice_dir / 'hst_test.bsp'
    kernel.touch()
    config.write_text('"HST",5,1,399001,"hst_test.bsp"\n', encoding='utf-8')

    monkeypatch.setattr('ephemeris_tools.spice.load.get_spice_path', lambda: str(spice_dir))
    monkeypatch.setattr('cspyce.furnsh', lambda path: None)

    state = get_state()
    state.planet_num = 0
    state.planet_id = 0
    state.pool_loaded = False
    state.obs_id = 0
    state.obs_is_set = False
    state.obs_lat = 0.0
    state.obs_lon = 0.0
    state.obs_alt = 0.0

    ok = load_spacecraft(sc_id='HST', planet=5, version=1, set_obs=True)

    assert ok is True
    assert state.obs_id == 399001
    assert state.obs_is_set is False
