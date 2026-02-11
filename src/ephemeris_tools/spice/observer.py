"""Observer setup and state (ported from rspk_setobs.f)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import cspyce

from ephemeris_tools.constants import EARTH_ID
from ephemeris_tools.spice.common import get_state

if TYPE_CHECKING:
    import numpy as np

# GRS 80 (FORTRAN parameters)
EARTH_RAD_KM = 6378.137
EARTH_FLAT = 1.0 / 298.257222


def set_observer_id(body_id: int) -> None:
    """Set observer to a SPICE body (e.g. spacecraft). Use 0 for Earth center."""
    state = get_state()
    state.obs_id = EARTH_ID if body_id == 0 else body_id
    state.obs_is_set = False


def set_observer_location(lat_deg: float, lon_deg: float, alt_m: float) -> None:
    """Set observer to geodetic location on Earth. |lat| > 90 disables (Earth center)."""
    state = get_state()
    state.obs_id = EARTH_ID
    state.obs_lat = math.radians(lat_deg)
    state.obs_lon = math.radians(lon_deg)
    state.obs_alt = alt_m / 1000.0
    state.obs_is_set = abs(lat_deg) <= 90.0


# Earth rotation rate (rad/s) in body-fixed frame for surface velocity
_EARTH_ROT_RATE_RAD_S = 2.0 * math.pi / 86400.0


def observer_state(et: float) -> np.ndarray:
    """Return observer state (6) in J2000: position (3) and velocity (3) in km, km/s."""
    import numpy as np

    state = get_state()
    obs_pv = list(cspyce.spkssb(state.obs_id, et, 'J2000'))
    if not state.obs_is_set:
        return np.array(obs_pv, dtype=np.float64)
    obs_dp = cspyce.georec(state.obs_lon, state.obs_lat, state.obs_alt, EARTH_RAD_KM, EARTH_FLAT)
    frame = f'IAU_{cspyce.bodc2n(EARTH_ID).upper()}'
    earth_mat = cspyce.pxform(frame, 'J2000', et)
    rotated = cspyce.mtxv(earth_mat, obs_dp)
    obs_pv[0] += rotated[0]
    obs_pv[1] += rotated[1]
    obs_pv[2] += rotated[2]
    # Add surface rotational velocity: omega x obs_dp in body frame, then transform to J2000
    vel_body = [
        -_EARTH_ROT_RATE_RAD_S * obs_dp[1],
        _EARTH_ROT_RATE_RAD_S * obs_dp[0],
        0.0,
    ]
    vel_j2000 = cspyce.mtxv(earth_mat, vel_body)
    obs_pv[3] += vel_j2000[0]
    obs_pv[4] += vel_j2000[1]
    obs_pv[5] += vel_j2000[2]
    return np.array(obs_pv, dtype=np.float64)
