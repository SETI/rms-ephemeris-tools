"""Enhanced BODMAT with time-shift and tidally-locked moon fallback (rspk_bodmat.f)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import cspyce

from ephemeris_tools.spice.common import get_state
from ephemeris_tools.spice.observer import observer_state

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    import numpy as np


def _is_moon(body_id: int) -> bool:
    return 300 < body_id < 999 and (body_id % 100) != 99


def _body_fixed_frame(body_id: int) -> str:
    """Return IAU body-fixed frame name for body ID (e.g. IAU_SATURN)."""
    try:
        name = cspyce.bodc2n(body_id)
    except Exception as e:
        raise ValueError(f'invalid body_id {body_id}: {e}') from e
    return f'IAU_{name.upper()}'


def bodmat(body_id: int, et: float) -> np.ndarray:
    """Rotation matrix J2000 -> body-fixed, with time-shift and moon fallback.

    Uses cspyce.tipbod (equivalent to FORTRAN BODMAT) which computes
    the matrix from PCK pole data directly — no frame kernel needed.
    Falls back to orbit-derived orientation for moons without PCK data.
    """
    import numpy as np

    state = get_state()
    for i in range(state.nshifts):
        if state.shift_id[i] == body_id:
            try:
                rot = cspyce.tipbod('J2000', body_id, et + state.shift_dt[i])
                return np.array(rot, dtype=np.float64)
            except Exception as e:
                logger.debug('time-shifted tipbod failed: %s', e, exc_info=True)
            break
    mat: np.ndarray
    try:
        rot = cspyce.tipbod('J2000', body_id, et)
        mat = np.array(rot, dtype=np.float64)
    except Exception as e:
        msg = str(e)
        if _is_moon(body_id):
            logger.debug(
                'cspyce.tipbod no PCK for moon body_id=%s, using orbit fallback: %s',
                body_id,
                msg[:80],
            )
        else:
            logger.error(
                'cspyce.tipbod failed for body_id=%s et=%s: %s',
                body_id,
                et,
                e,
                exc_info=True,
            )
        mat = np.zeros((3, 3), dtype=np.float64)
    if not _is_moon(body_id):
        if not np.any(mat != 0):
            logger.warning(
                'Failed to compute rotation matrix for body_id=%s; returning identity',
                body_id,
            )
            return np.eye(3, dtype=np.float64)
        return mat
    if np.any(mat != 0):
        return mat
    return bodmat_from_orbit(body_id, et)


def _spkez_state(state_planet: object) -> list[float]:
    """Return 6-element state [x,y,z,vx,vy,vz] from cspyce.spkez return (handles tuple or array)."""
    import numpy as np

    arr = np.asarray(state_planet, dtype=np.float64)
    flat = arr.flatten()
    return [float(flat[i]) for i in range(min(6, len(flat)))]


def bodmat_from_orbit(body_id: int, et: float) -> np.ndarray:
    """Rotation matrix for tidally-locked moon from orbit geometry (X toward planet, Z = pole)."""
    import numpy as np

    state = get_state()
    obs_pv = observer_state(et)
    _body_dpv, lt = cspyce.spkapp(body_id, et, 'J2000', obs_pv[:6].tolist(), 'LT')
    body_time = et - lt
    spkez_result = cspyce.spkez(state.planet_id, body_time, 'J2000', 'NONE', body_id)
    state_planet = (
        spkez_result[0]
        if isinstance(spkez_result, (tuple, list)) and len(spkez_result) >= 1
        else spkez_result
    )
    state_vec = _spkez_state(state_planet)
    if len(state_vec) < 6:
        return _identity_rotmat()
    pos = state_vec[:3]
    vel = state_vec[3:6]
    if state.planet_num == 7:
        vel = [-vel[0], -vel[1], -vel[2]]

    pos_norm = cspyce.vnorm(pos)
    if pos_norm < 1e-10:
        return _identity_rotmat()

    orbit_normal = list(cspyce.ucrss(pos, vel))
    if float(cspyce.vnorm(orbit_normal)) < 1e-10:
        return _bodmat_from_orbit_fallback(body_id, et, pos, pos_norm)

    try:
        rotmat = cspyce.twovec(pos, 1, vel, 2)
        return np.array(rotmat, dtype=np.float64)
    except Exception:
        return _bodmat_from_orbit_fallback(body_id, et, pos, pos_norm)


def _identity_rotmat() -> np.ndarray:
    import numpy as np

    return np.eye(3, dtype=np.float64)


def _bodmat_from_orbit_fallback(
    body_id: int, et: float, pos: list[float], pos_norm: float
) -> np.ndarray:
    """Fallback when twovec fails (parallel pos/vel): Z = planet pole, X = pos."""
    import numpy as np

    state = get_state()
    planet_frame = _body_fixed_frame(state.planet_id)
    planet_mat = cspyce.pxform(planet_frame, 'J2000', et)
    z = [float(planet_mat[2][i]) for i in range(3)]
    if state.planet_num == 7:
        z = [-z[0], -z[1], -z[2]]
    x = [pos[i] / pos_norm for i in range(3)]
    y = list(cspyce.ucrss(z, x))
    yn = float(cspyce.vnorm(y))
    if yn < 1e-10:
        y = list(cspyce.ucrss(x, [0, 0, 1] if abs(x[2]) < 0.9 else [0, 1, 0]))
        yn = float(cspyce.vnorm(y))
    y = [float(y[i]) / yn for i in range(3)]
    z = list(cspyce.ucrss(x, y))
    zn = float(cspyce.vnorm(z))
    z = [float(z[i]) / zn for i in range(3)]
    return np.array([x, y, z], dtype=np.float64).T
