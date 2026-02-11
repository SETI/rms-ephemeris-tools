"""Moon orbit geometry: orbit opening, moon angular offsets (rspk_orbitopen, rspk_moondist)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import cspyce

from ephemeris_tools.spice.bodmat import bodmat as planet_bodmat
from ephemeris_tools.spice.common import get_state
from ephemeris_tools.spice.observer import observer_state
from ephemeris_tools.spice.shifts import spkapp_shifted

if TYPE_CHECKING:
    import numpy as np

TWOPI = 2.0 * math.pi


def orbit_opening(et: float, moon_id: int) -> tuple[float, float]:
    """Observed opening angle of moon orbit and observer longitude (radians)."""
    state = get_state()
    obs_pv = observer_state(et)
    _planet_dpv, dt = cspyce.spkapp(state.planet_id, et, 'J2000', obs_pv[:6].tolist(), 'CN')
    planet_time = et - dt
    planet_pv = cspyce.spkssb(state.planet_id, planet_time, 'J2000')
    moon_dpv, _ = cspyce.spkez(moon_id, et, 'J2000', 'NONE', state.planet_id)
    rotmat = cspyce.twovec(moon_dpv[:3], 1, moon_dpv[3:6], 2)
    obs_dp = [
        obs_pv[0] - planet_pv[0],
        obs_pv[1] - planet_pv[1],
        obs_pv[2] - planet_pv[2],
    ]
    norm_dp = cspyce.vhat(obs_dp)
    tempvec = cspyce.vlcom(1.0, norm_dp, -1.0 / cspyce.clight(), planet_pv[3:6])
    tempvec = cspyce.mxv(rotmat, tempvec)
    n = cspyce.vnorm(tempvec)
    if n < 1e-12:
        obs_b = 0.0
    else:
        ratio = max(-1.0, min(1.0, tempvec[2] / n))
        obs_b = math.asin(ratio)
    obs_long = math.atan2(-tempvec[1], tempvec[0])
    if obs_long < 0:
        obs_long += TWOPI
    return (obs_b, obs_long)


def moon_distances(et: float, moon_ids: list[int]) -> tuple[np.ndarray, float]:
    """Projected angular offsets of moons from planet axis (radians), and limb angle."""
    import numpy as np

    state = get_state()
    obs_pv = observer_state(et)
    planet_dpv, dt = cspyce.spkapp(state.planet_id, et, 'J2000', obs_pv[:6].tolist(), 'LT')
    planet_time = et - dt
    bodmat_rot = planet_bodmat(state.planet_id, planet_time)
    pole = [bodmat_rot[2][0], bodmat_rot[2][1], bodmat_rot[2][2]]
    if state.planet_num == 7:
        pole = [-pole[0], -pole[1], -pole[2]]
    rotmat = cspyce.twovec(planet_dpv[:3], 1, pole, 3)
    offsets = np.zeros(len(moon_ids), dtype=np.float64)
    for i, mid in enumerate(moon_ids):
        moon_dpv, _ = spkapp_shifted(mid, et, 'J2000', obs_pv, 'LT')
        vector = cspyce.mxv(rotmat, moon_dpv[:3])
        offsets[i] = math.atan2(vector[1], vector[0])
    radii = cspyce.bodvrd(str(state.planet_id), 'RADII')
    r_eq = radii[0]
    eps_limb = 1e-12
    vnorm = cspyce.vnorm(planet_dpv[:3])
    limb = math.asin(min(1.0, r_eq / max(vnorm, eps_limb)))
    return (offsets, limb)
