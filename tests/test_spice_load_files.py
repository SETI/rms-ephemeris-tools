"""Tests for SPICE planetary kernel loading behavior."""

from __future__ import annotations

from pathlib import Path

import pytest

from ephemeris_tools.constants import EARTH_ID
from ephemeris_tools.spice.common import get_state
from ephemeris_tools.spice.load import load_spice_files


def test_load_spice_files_resets_observer_to_earth_center(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Planet load resets observer state like FORTRAN RSPK_LoadFiles."""

    spice_dir = tmp_path / 'spice'
    spice_dir.mkdir()
    (spice_dir / 'planet_test.bsp').touch()
    (spice_dir / 'SPICE_planets.txt').write_text(
        '5,1,"planet_test.bsp"\n',
        encoding='utf-8',
    )

    monkeypatch.setattr('ephemeris_tools.spice.load.get_spice_path', lambda: str(spice_dir))
    monkeypatch.setattr('cspyce.furnsh', lambda path: None)

    state = get_state()
    state.planet_num = 0
    state.planet_id = 0
    state.pool_loaded = False
    state.obs_id = -82
    state.obs_is_set = True
    state.obs_lat = 0.1
    state.obs_lon = 0.2
    state.obs_alt = 1.0

    ok, reason = load_spice_files(planet=5, version=1)

    assert ok is True
    assert reason is None
    assert state.obs_id == EARTH_ID
    assert state.obs_is_set is False
