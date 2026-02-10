"""Time shift support for moon orbits (ported from rspk_setshift.f and rspk_spkapp.f)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import cspyce

from ephemeris_tools.spice.common import MAXSHIFTS, get_state
from ephemeris_tools.spice.observer import observer_state

if TYPE_CHECKING:
    import numpy as np


def set_shift(body_id: int, dt: float) -> None:
    """Apply a fixed time shift (seconds) to a moon's orbit. Positive = lead ephemeris."""
    state = get_state()
    for i in range(state.nshifts):
        if state.shift_id[i] == body_id:
            state.shift_dt[i] = dt
            return
    if state.nshifts >= MAXSHIFTS:
        raise RuntimeError(
            "Number of moon orbit time shifts exceeded in set_shift()"
        )
    state.shift_id[state.nshifts] = body_id
    state.shift_dt[state.nshifts] = dt
    state.nshifts += 1


def spkapp_shifted(
    body_id: int,
    et: float,
    ref: str,
    obs_pv: "np.ndarray",
    aberr: str,
) -> tuple["np.ndarray", float]:
    """Like cspyce.spkapp but with time-shift support. Returns (body_dpv, lt)."""
    import numpy as np

    state = get_state()
    obs = obs_pv if hasattr(obs_pv, "__len__") else np.array(obs_pv)
    for i in range(state.nshifts):
        if state.shift_id[i] != body_id:
            continue
        dt_shift = state.shift_dt[i]
        if dt_shift == 0.0:
            break
        planet_dpv, planet_lt = cspyce.spkapp(
            state.planet_id, et + dt_shift, ref, obs, aberr
        )
        body_dpv, body_lt = cspyce.spkapp(
            body_id, et + dt_shift, ref, obs, aberr
        )
        temp_pos = [
            body_dpv[0] - planet_dpv[0],
            body_dpv[1] - planet_dpv[1],
            body_dpv[2] - planet_dpv[2],
        ]
        temp_vel = [
            body_dpv[3] - planet_dpv[3],
            body_dpv[4] - planet_dpv[4],
            body_dpv[5] - planet_dpv[5],
        ]
        planet_dpv_at_et, planet_lt_at_et = cspyce.spkapp(
            state.planet_id, et, ref, obs, aberr
        )
        out_pos = [
            temp_pos[0] + planet_dpv_at_et[0],
            temp_pos[1] + planet_dpv_at_et[1],
            temp_pos[2] + planet_dpv_at_et[2],
        ]
        out_vel = [
            temp_vel[0] + planet_dpv_at_et[3],
            temp_vel[1] + planet_dpv_at_et[4],
            temp_vel[2] + planet_dpv_at_et[5],
        ]
        return (
            np.array(out_pos + out_vel, dtype=np.float64),
            body_lt - planet_lt + planet_lt_at_et,
        )
    body_dpv, lt = cspyce.spkapp(body_id, et, ref, obs, aberr)
    return (np.array(body_dpv, dtype=np.float64), lt)
