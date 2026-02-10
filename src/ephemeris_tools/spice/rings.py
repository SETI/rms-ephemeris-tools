"""Ring geometry: opening angles, RA/Dec of ring points (rspk_ringopen, ringradec, ansaradec)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

import cspyce

from ephemeris_tools.constants import SUN_ID
from ephemeris_tools.spice.bodmat import bodmat as planet_bodmat
from ephemeris_tools.spice.common import get_state
from ephemeris_tools.spice.observer import observer_state

if TYPE_CHECKING:
    pass

TWOPI = 2.0 * math.pi


@dataclass
class RingGeometry:
    """Ring opening and lighting geometry."""

    obs_b: float
    sun_b: float
    sun_db: float
    is_dark: bool
    obs_long: float
    sun_long: float


def ring_opening(et: float) -> RingGeometry:
    """Observed ring opening angle, Sun geometry, and whether rings are dark."""
    state = get_state()
    obs_pv = observer_state(et)
    planet_dpv, dt = cspyce.spkapp(
        state.planet_id, et, "J2000", obs_pv[:6].tolist(), "CN"
    )
    planet_time = et - dt
    planet_pv = cspyce.spkssb(state.planet_id, planet_time, "J2000")
    sun_dpv, _ = cspyce.spkapp(
        SUN_ID, planet_time, "J2000", planet_pv[:6], "LT+S"
    )
    sun_radii = cspyce.bodvrd(str(SUN_ID), "RADII")
    sun_db = sun_radii[0] / cspyce.vnorm(sun_dpv[:3])
    rotmat = planet_bodmat(state.planet_id, planet_time)
    pole = [rotmat[2][0], rotmat[2][1], rotmat[2][2]]
    if state.planet_num == 7:
        pole = [-pole[0], -pole[1], -pole[2]]
    tempvec = [0.0, 0.0, 1.0]
    ascnode = cspyce.vcrss(tempvec, pole)
    rotmat = cspyce.twovec(pole, 3, ascnode, 1)
    obs_dp = [
        obs_pv[0] - planet_pv[0],
        obs_pv[1] - planet_pv[1],
        obs_pv[2] - planet_pv[2],
    ]
    norm_dp = cspyce.vhat(obs_dp)
    tempvec = cspyce.vlcom(
        1.0, norm_dp, -1.0 / cspyce.clight(), planet_pv[3:6]
    )
    tempvec = cspyce.mxv(rotmat, tempvec)
    n = cspyce.vnorm(tempvec)
    obs_b = math.asin(tempvec[2] / n)
    obs_long = math.atan2(tempvec[1], tempvec[0])
    if obs_long < 0:
        obs_long += TWOPI
    tempvec = cspyce.mxv(rotmat, sun_dpv[:3])
    n = cspyce.vnorm(tempvec)
    sun_b = math.asin(tempvec[2] / n)
    sun_long = math.atan2(tempvec[1], tempvec[0])
    if sun_long < 0:
        sun_long += TWOPI
    is_dark = (obs_b * sun_b < 0) and (abs(sun_b) > sun_db)
    return RingGeometry(
        obs_b=obs_b,
        sun_b=sun_b,
        sun_db=sun_db,
        is_dark=is_dark,
        obs_long=obs_long,
        sun_long=sun_long,
    )


def ring_radec(et: float, radius_km: float, lon_rad: float) -> tuple[float, float]:
    """J2000 RA and Dec (radians) of a point on the ring at given radius and longitude."""
    state = get_state()
    obs_pv = observer_state(et)
    planet_dpv, dt = cspyce.spkapp(
        state.planet_id, et, "J2000", obs_pv[:6].tolist(), "LT"
    )
    planet_time = et - dt
    bodmat_rot = planet_bodmat(state.planet_id, planet_time)
    pole = [bodmat_rot[2][0], bodmat_rot[2][1], bodmat_rot[2][2]]
    if state.planet_num == 7:
        pole = [-pole[0], -pole[1], -pole[2]]
    tempvec = [0.0, 0.0, 1.0]
    ascnode = cspyce.vcrss(tempvec, pole)
    rotmat = cspyce.twovec(pole, 3, planet_dpv[:3], 1)
    vec = [
        -radius_km * math.cos(lon_rad),
        -radius_km * math.sin(lon_rad),
        0.0,
    ]
    vec = cspyce.mxv(rotmat, vec)
    ring_dp = [
        planet_dpv[0] + vec[0],
        planet_dpv[1] + vec[1],
        planet_dpv[2] + vec[2],
    ]
    _, ra, dec = cspyce.recrad(ring_dp)
    return (ra, dec)


def ansa_radec(
    et: float, radius_km: float, is_right: bool
) -> tuple[float, float]:
    """J2000 RA and Dec (radians) of the right or left ring ansa."""
    from ephemeris_tools.spice.geometry import planet_ranges

    _, obs_dist = planet_ranges(et)
    geom = ring_opening(et)
    obs_dist_km = obs_dist
    offset = math.asin(
        radius_km / (obs_dist_km * math.cos(geom.obs_b))
    )
    if is_right:
        lon = 0.5 * math.pi - offset
    else:
        lon = 1.5 * math.pi + offset
    return ring_radec(et, radius_km, lon)
