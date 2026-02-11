"""Body geometry: RA/Dec, phase, ranges, lat/lon (ported from rspk_* body routines)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import cspyce

from ephemeris_tools.constants import EARTH_ID, SUN_ID
from ephemeris_tools.spice.bodmat import bodmat
from ephemeris_tools.spice.common import get_state
from ephemeris_tools.spice.observer import observer_state
from ephemeris_tools.spice.shifts import spkapp_shifted

if TYPE_CHECKING:
    pass

TWOPI = 2.0 * math.pi


def body_radec(et: float, body_id: int) -> tuple[float, float]:
    """Observed J2000 RA and Dec of body (radians)."""
    obs_pv = observer_state(et)
    body_dpv, _ = spkapp_shifted(body_id, et, 'J2000', obs_pv, 'LT')
    _, ra, dec = cspyce.recrad(body_dpv[:3])
    return (ra, dec)


def body_phase(et: float, body_id: int) -> float:
    """Solar phase angle of body as seen from observer (radians).

    Port of RSPK_BodyPhase: uses standard SPKAPP with 'LT', not shifted.
    """
    obs_pv = observer_state(et)
    body_dpv, dt = cspyce.spkapp(body_id, et, 'J2000', obs_pv[:6], 'LT')
    body_time = et - dt
    body_pv = cspyce.spkssb(body_id, body_time, 'J2000')
    sun_dpv, _ = cspyce.spkapp(SUN_ID, body_time, 'J2000', body_pv[:6], 'LT')
    obs_dp = cspyce.vminus(body_dpv[:3])
    return cspyce.vsep(sun_dpv[:3], obs_dp)


def body_ranges(et: float, body_id: int) -> tuple[float, float]:
    """Sun-body and observer-body distances (km)."""
    obs_pv = observer_state(et)
    body_dpv, dt = spkapp_shifted(body_id, et, 'J2000', obs_pv, 'LT')
    body_time = et - dt
    body_pv = cspyce.spkssb(body_id, body_time, 'J2000')
    sun_dpv, _ = cspyce.spkapp(SUN_ID, body_time, 'J2000', body_pv[:6], 'LT+S')
    return (cspyce.vnorm(sun_dpv[:3]), cspyce.vnorm(body_dpv[:3]))


def planet_phase(et: float) -> float:
    """Solar phase angle of planet as seen from observer (radians).

    Port of RSPK_Phase: VMINUS(planet_dpv) gives direction from planet
    to observer, then VSEP with sun direction gives the phase angle.
    """
    state = get_state()
    obs_pv = observer_state(et)
    planet_dpv, dt = cspyce.spkapp(state.planet_id, et, 'J2000', obs_pv[:6].tolist(), 'LT')
    planet_time = et - dt
    planet_pv = cspyce.spkssb(state.planet_id, planet_time, 'J2000')
    sun_dpv, _ = cspyce.spkapp(SUN_ID, planet_time, 'J2000', planet_pv[:6], 'LT')
    obs_dp = cspyce.vminus(planet_dpv[:3])
    return cspyce.vsep(sun_dpv[:3], obs_dp)


def planet_ranges(et: float) -> tuple[float, float]:
    """Sun-planet and observer-planet distances (km)."""
    state = get_state()
    obs_pv = observer_state(et)
    planet_dpv, dt = cspyce.spkapp(state.planet_id, et, 'J2000', obs_pv[:6].tolist(), 'LT')
    planet_time = et - dt
    planet_pv = cspyce.spkssb(state.planet_id, planet_time, 'J2000')
    sun_dpv, _ = cspyce.spkapp(SUN_ID, planet_time, 'J2000', planet_pv[:6], 'LT+S')
    return (cspyce.vnorm(sun_dpv[:3]), cspyce.vnorm(planet_dpv[:3]))


def limb_radius(et: float) -> tuple[float, float]:
    """Planet radius (km) and projected angular radius (radians)."""
    state = get_state()
    obs_pv = observer_state(et)
    planet_dpv, _ = cspyce.spkapp(state.planet_id, et, 'J2000', obs_pv[:6].tolist(), 'LT')
    radii = cspyce.bodvrd(str(state.planet_id), 'RADII')
    rkm = radii[0]
    rradians = rkm / cspyce.vnorm(planet_dpv[:3])
    return (rkm, rradians)


def conjunction_angle(et: float, body1_id: int, body2_id: int) -> float:
    """Angular separation between two bodies as seen from observer (radians)."""
    obs_pv = observer_state(et)
    b1_dpv, _ = spkapp_shifted(body1_id, et, 'J2000', obs_pv, 'LT+S')
    b2_dpv, _ = spkapp_shifted(body2_id, et, 'J2000', obs_pv, 'LT+S')
    return cspyce.vsep(b1_dpv[:3], b2_dpv[:3])


def anti_sun(et: float, body_id: int) -> tuple[float, float]:
    """Anti-Sun direction as RA, Dec (radians) for the body's system."""
    obs_pv = observer_state(et)
    _planet_dpv, dt = cspyce.spkapp(body_id, et, 'J2000', obs_pv[:6].tolist(), 'LT')
    planet_time = et - dt
    planet_pv = cspyce.spkssb(body_id, planet_time, 'J2000')
    sun_dpv, _ = cspyce.spkapp(SUN_ID, planet_time, 'J2000', planet_pv[:6], 'LT+S')
    anti = [-sun_dpv[0], -sun_dpv[1], -sun_dpv[2]]
    _, ra, dec = cspyce.recrad(anti)
    return (ra, dec)


def body_latlon(et: float, body_id: int) -> tuple[float, float, float, float]:
    """Sub-observer and sub-solar lat/long (radians).

    Returns (subobs_lat, subsol_lat, subobs_long, subsol_long).
    Matches rspk_bodylonlat.f: body with CN, Sun with CN+S, observer with XCN+S;
    body_time adjusted by + r_eq/clight for observer direction.
    """
    state = get_state()
    obs_pv = observer_state(et)
    radii = cspyce.bodvrd(str(body_id), 'RADII')
    r_eq = radii[0]
    _body_dpv, dt = spkapp_shifted(body_id, et, 'J2000', obs_pv, 'CN')
    body_time = et - dt + r_eq / cspyce.clight()
    body_pv = cspyce.spkssb(body_id, body_time, 'J2000')
    sun_dpv, _ = cspyce.spkapp(SUN_ID, body_time, 'J2000', body_pv, 'CN+S')
    obs_id = state.obs_id if state.obs_id != 0 else EARTH_ID
    obs_dpv, _ = cspyce.spkapp(obs_id, body_time, 'J2000', body_pv, 'XCN+S')
    rotmat = bodmat(body_id, body_time)
    obs_dp_in_body = cspyce.mxv(rotmat, obs_dpv[:3])
    n = cspyce.vnorm(obs_dp_in_body)
    if n < 1e-12:
        raise ValueError(
            'Observer direction in body frame has zero length; cannot compute sub-observer lat/lon'
        )
    subobs_lat = math.asin(max(-1.0, min(1.0, obs_dp_in_body[2] / n)))
    subobs_long = math.atan2(obs_dp_in_body[1], obs_dp_in_body[0])
    if subobs_long < 0:
        subobs_long += TWOPI
    subobs_long = TWOPI - subobs_long
    sun_dp_in_body = cspyce.mxv(rotmat, sun_dpv[:3])
    n = cspyce.vnorm(sun_dp_in_body)
    if n < 1e-12:
        raise ValueError(
            'Sun direction in body frame has zero length; cannot compute sub-solar lat/lon'
        )
    subsol_lat = math.asin(max(-1.0, min(1.0, sun_dp_in_body[2] / n)))
    subsol_long = math.atan2(sun_dp_in_body[1], sun_dp_in_body[0])
    if subsol_long < 0:
        subsol_long += TWOPI
    subsol_long = TWOPI - subsol_long
    if state.planet_num == 7:
        if subobs_long > 0:
            subobs_long = TWOPI - subobs_long
        if subsol_long > 0:
            subsol_long = TWOPI - subsol_long
    return (subobs_lat, subsol_lat, subobs_long, subsol_long)


def body_lonlat(et: float, body_id: int) -> tuple[float, float, float, float]:
    """Sub-observer and sub-solar lon/lat (radians).

    Returns (subobs_lon, subobs_lat, subsol_lon, subsol_lat).
    """
    subobs_lat, subsol_lat, subobs_long, subsol_long = body_latlon(et, body_id)
    return (subobs_long, subobs_lat, subsol_long, subsol_lat)


def moon_tracker_offsets(et: float, moon_ids: list[int]) -> tuple[list[float], float]:
    """East-west angular offsets of moons from planet and limb radius (radians).

    Delegates to orbits.moon_distances (FORTRAN RSPK_MoonDist). Positive offset
    = morning ansa (higher RA). Returns (offsets per moon in radians, limb rad).
    """
    from ephemeris_tools.spice.orbits import moon_distances

    offsets, limb = moon_distances(et, moon_ids)
    return (list(offsets), float(limb))
