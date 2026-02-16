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
    """Set the observation point to a SPICE body (e.g. spacecraft).

    Port of RSPK_SetObsId. Subsequent geometry calls use this observer.
    Use 0 to reset to Earth's center.

    Parameters:
        body_id: SPICE body ID of the observer, or 0 for Earth center.
    """
    state = get_state()
    state.obs_id = EARTH_ID if body_id == 0 else body_id
    state.obs_is_set = False


def set_observer_location(lat_deg: float, lon_deg: float, alt_m: float) -> None:
    """Set observer to a geodetic location on Earth.

    Port of RSPK_SetObs. Subsequent geometry calls are corrected for the
    observatory's offset from Earth's center. If latitude is outside
    [-90, 90], the observatory offset is disabled (Earth's center used).

    Parameters:
        lat_deg: Geodetic latitude in degrees. Outside [-90, 90] disables
            observatory offset.
        lon_deg: East longitude in degrees.
        alt_m: Altitude in meters (relative to GRS 80 reference spheroid).
    """
    state = get_state()
    state.obs_id = EARTH_ID
    state.obs_lat = math.radians(lat_deg)
    state.obs_lon = math.radians(lon_deg)
    state.obs_alt = alt_m / 1000.0
    state.obs_is_set = abs(lat_deg) <= 90.0


# Earth rotation rate (rad/s) in body-fixed frame for surface velocity
_EARTH_ROT_RATE_RAD_S = 2.0 * math.pi / 86400.0


def observer_state(et: float) -> np.ndarray:
    """Return observer state (position and velocity) in J2000 at ephemeris time.

    Port of RSPK_ObsLoc. Uses coordinates from set_observer_location or
    set_observer_id. Position is in km; velocity in km/s. For an Earth
    observatory, velocity includes Earth rotation.

    Parameters:
        et: Ephemeris time (e.g. from cspyce.utc2et).

    Returns:
        Length-6 array: position (3) and velocity (3) in km and km/s.
    """
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
