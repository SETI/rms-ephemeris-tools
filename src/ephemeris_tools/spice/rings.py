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
    """Ring opening and lighting geometry (output of ring_opening, port of RSPK_RingOpen)."""

    obs_b: float
    sun_b: float
    sun_db: float
    is_dark: bool
    obs_long: float
    sun_long: float


def ring_opening(et: float) -> RingGeometry:
    """Return observed ring opening and lighting geometry (port of RSPK_RingOpen).

    Returns opening angle, sub-observer/sub-solar longitudes, and whether the
    visible ring side is lit. Longitudes are from the equatorial plane J2000
    ascending node. Both sides are treated as lit while Sun crosses ring plane.

    Parameters:
        et: Ephemeris time of the observation (e.g. from cspyce.utc2et).

    Returns:
        RingGeometry with obs_b, sun_b, sun_db, is_dark, obs_long, sun_long.
    """
    state = get_state()
    obs_pv = observer_state(et)
    _planet_dpv, dt = cspyce.spkapp(state.planet_id, et, 'J2000', obs_pv[:6].tolist(), 'CN')
    planet_time = et - dt
    planet_pv = cspyce.spkssb(state.planet_id, planet_time, 'J2000')
    sun_dpv, _ = cspyce.spkapp(SUN_ID, planet_time, 'J2000', planet_pv[:6], 'LT+S')
    sun_radii = cspyce.bodvrd(str(SUN_ID), 'RADII')
    sun_db = sun_radii[0] / cspyce.vnorm(sun_dpv[:3])
    bodmat_rot = planet_bodmat(state.planet_id, planet_time)
    pole = [bodmat_rot[2][0], bodmat_rot[2][1], bodmat_rot[2][2]]
    if state.planet_num == 7:
        pole = [-pole[0], -pole[1], -pole[2]]
    axis_z = [0.0, 0.0, 1.0]
    ascnode = cspyce.vcrss(axis_z, pole)
    pole_rot_raw = cspyce.twovec(pole, 3, ascnode, 1)
    pole_rot = [list(row) for row in pole_rot_raw]
    # Match FORTRAN RSPK_RingOpen quirk:
    # "This fixes a bug in TWOVEC(): rotmat(3,1)=pole(1)".
    pole_rot[2][0] = pole[0]
    obs_dp = [
        obs_pv[0] - planet_pv[0],
        obs_pv[1] - planet_pv[1],
        obs_pv[2] - planet_pv[2],
    ]
    norm_dp = cspyce.vhat(obs_dp)
    obs_dir = cspyce.vlcom(1.0, norm_dp, -1.0 / cspyce.clight(), planet_pv[3:6])
    tempvec = cspyce.mxv(pole_rot, obs_dir)
    n = cspyce.vnorm(tempvec)
    obs_b = math.asin(tempvec[2] / n)
    obs_long = math.atan2(tempvec[1], tempvec[0])
    if obs_long < 0:
        obs_long += TWOPI
    tempvec = cspyce.mxv(pole_rot, sun_dpv[:3])
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
    """Return observed J2000 RA and Dec of a point on the ring (port of RSPK_RingRaDec).

    Applies to Earth center or observatory per set_observer_*. Coordinates are
    not corrected for stellar aberration (correct relative to star catalogs).

    Parameters:
        et: Ephemeris time of the observation (e.g. from cspyce.utc2et).
        radius_km: Ring radius in km.
        lon_rad: Longitude on ring in radians; positive = ring rotation direction.

    Returns:
        Tuple of (ra, dec) in radians.
    """
    state = get_state()
    obs_pv = observer_state(et)
    planet_dpv, dt = cspyce.spkapp(state.planet_id, et, 'J2000', obs_pv[:6].tolist(), 'LT')
    planet_time = et - dt
    bodmat_rot = planet_bodmat(state.planet_id, planet_time)
    pole = [bodmat_rot[2][0], bodmat_rot[2][1], bodmat_rot[2][2]]
    if state.planet_num == 7:
        pole = [-pole[0], -pole[1], -pole[2]]
    # Match FORTRAN RSPK_RingRaDec exactly:
    # TWOVEC(pole,3,planet_dpv,1) defines J2000->planet frame and MTXV maps
    # from that planet frame back into J2000.
    pole_rot = cspyce.twovec(pole, 3, planet_dpv[:3], 1)
    vec_in = [
        -radius_km * math.cos(lon_rad),
        -radius_km * math.sin(lon_rad),
        0.0,
    ]
    vec_j2000 = cspyce.mtxv(pole_rot, vec_in)
    ring_dp = [
        planet_dpv[0] + vec_j2000[0],
        planet_dpv[1] + vec_j2000[1],
        planet_dpv[2] + vec_j2000[2],
    ]
    _, ra, dec = cspyce.recrad(ring_dp)
    return (ra, dec)


_EPS_ANSA = 1e-12


def ansa_radec(et: float, radius_km: float, is_right: bool) -> tuple[float, float]:
    """Return observed J2000 RA and Dec of a ring ansa (port of RSPK_AnsaRaDec).

    Right ansa is near 90 deg longitude; left ansa near 270 deg. Coordinates
    apply to Earth center or observatory; not corrected for stellar aberration.

    Parameters:
        et: Ephemeris time of the observation (e.g. from cspyce.utc2et).
        radius_km: Ring radius in km.
        is_right: True for right ansa, False for left ansa.

    Returns:
        Tuple of (ra, dec) in radians.

    Raises:
        ValueError: If geometry is edge-on (denom ~ 0).
    """
    from ephemeris_tools.spice.geometry import planet_ranges

    _, obs_dist = planet_ranges(et)
    geom = ring_opening(et)
    denom = obs_dist * math.cos(geom.obs_b)
    if abs(denom) < _EPS_ANSA:
        raise ValueError(
            f'Ring ansa calculation undefined for edge-on geometry: obs_dist*cos(obs_b)={denom!r}'
        )
    ratio = radius_km / denom
    ratio = max(-1.0, min(1.0, ratio))
    offset = math.asin(ratio)
    if is_right:
        lon = 0.5 * math.pi - offset
    else:
        lon = 1.5 * math.pi + offset
    return ring_radec(et, radius_km, lon)
