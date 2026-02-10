"""Body geometry: RA/Dec, phase, ranges, lat/lon (ported from rspk_* body routines)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import cspyce

from ephemeris_tools.constants import SUN_ID
from ephemeris_tools.spice.bodmat import bodmat
from ephemeris_tools.spice.common import get_state
from ephemeris_tools.spice.observer import observer_state
from ephemeris_tools.spice.shifts import spkapp_shifted

if TYPE_CHECKING:
    import numpy as np

TWOPI = 2.0 * math.pi


def body_radec(et: float, body_id: int) -> tuple[float, float]:
    """Observed J2000 RA and Dec of body (radians)."""
    obs_pv = observer_state(et)
    body_dpv, _ = spkapp_shifted(body_id, et, "J2000", obs_pv, "LT")
    range_, ra, dec = cspyce.recrad(body_dpv[:3])
    return (ra, dec)


def body_phase(et: float, body_id: int) -> float:
    """Solar phase angle of body as seen from observer (radians)."""
    obs_pv = observer_state(et)
    body_dpv, _ = spkapp_shifted(body_id, et, "J2000", obs_pv, "LT")
    body_time = et  # approximation; exact would use lt
    body_pv = cspyce.spkssb(body_id, body_time, "J2000")
    sun_dpv, _ = cspyce.spkapp(
        SUN_ID, body_time, "J2000", body_pv[:6], "LT"
    )
    obs_dp = [
        obs_pv[0] - body_dpv[0],
        obs_pv[1] - body_dpv[1],
        obs_pv[2] - body_dpv[2],
    ]
    return cspyce.vsep(sun_dpv[:3], obs_dp)


def body_ranges(et: float, body_id: int) -> tuple[float, float]:
    """Sun-body and observer-body distances (km)."""
    obs_pv = observer_state(et)
    body_dpv, dt = spkapp_shifted(body_id, et, "J2000", obs_pv, "LT")
    body_time = et - dt
    body_pv = cspyce.spkssb(body_id, body_time, "J2000")
    sun_dpv, _ = cspyce.spkapp(
        SUN_ID, body_time, "J2000", body_pv[:6], "LT+S"
    )
    return (cspyce.vnorm(sun_dpv[:3]), cspyce.vnorm(body_dpv[:3]))


def planet_phase(et: float) -> float:
    """Solar phase angle of planet as seen from observer (radians)."""
    state = get_state()
    obs_pv = observer_state(et)
    planet_dpv, dt = cspyce.spkapp(
        state.planet_id, et, "J2000", obs_pv[:6].tolist(), "LT"
    )
    planet_time = et - dt
    planet_pv = cspyce.spkssb(state.planet_id, planet_time, "J2000")
    sun_dpv, _ = cspyce.spkapp(
        SUN_ID, planet_time, "J2000", planet_pv[:6], "LT"
    )
    obs_dp = [
        obs_pv[0] - planet_dpv[0],
        obs_pv[1] - planet_dpv[1],
        obs_pv[2] - planet_dpv[2],
    ]
    return cspyce.vsep(sun_dpv[:3], obs_dp)


def planet_ranges(et: float) -> tuple[float, float]:
    """Sun-planet and observer-planet distances (km)."""
    state = get_state()
    obs_pv = observer_state(et)
    planet_dpv, dt = cspyce.spkapp(
        state.planet_id, et, "J2000", obs_pv[:6].tolist(), "LT"
    )
    planet_time = et - dt
    planet_pv = cspyce.spkssb(state.planet_id, planet_time, "J2000")
    sun_dpv, _ = cspyce.spkapp(
        SUN_ID, planet_time, "J2000", planet_pv[:6], "LT+S"
    )
    return (cspyce.vnorm(sun_dpv[:3]), cspyce.vnorm(planet_dpv[:3]))


def limb_radius(et: float) -> tuple[float, float]:
    """Planet radius (km) and projected angular radius (radians)."""
    state = get_state()
    obs_pv = observer_state(et)
    planet_dpv, _ = cspyce.spkapp(
        state.planet_id, et, "J2000", obs_pv[:6].tolist(), "LT"
    )
    radii = cspyce.bodvrd(str(state.planet_id), "RADII")
    rkm = radii[0]
    rradians = rkm / cspyce.vnorm(planet_dpv[:3])
    return (rkm, rradians)


def conjunction_angle(et: float, body1_id: int, body2_id: int) -> float:
    """Angular separation between two bodies as seen from observer (radians)."""
    obs_pv = observer_state(et)
    b1_dpv, _ = spkapp_shifted(body1_id, et, "J2000", obs_pv, "LT+S")
    b2_dpv, _ = spkapp_shifted(body2_id, et, "J2000", obs_pv, "LT+S")
    return cspyce.vsep(b1_dpv[:3], b2_dpv[:3])


def anti_sun(et: float, body_id: int) -> tuple[float, float]:
    """Anti-Sun direction as RA, Dec (radians) for the body's system."""
    state = get_state()
    obs_pv = observer_state(et)
    planet_dpv, dt = cspyce.spkapp(
        state.planet_id, et, "J2000", obs_pv[:6].tolist(), "LT"
    )
    planet_time = et - dt
    planet_pv = cspyce.spkssb(state.planet_id, planet_time, "J2000")
    sun_dpv, _ = cspyce.spkapp(
        SUN_ID, planet_time, "J2000", planet_pv[:6], "LT+S"
    )
    anti = [-sun_dpv[0], -sun_dpv[1], -sun_dpv[2]]
    _, ra, dec = cspyce.recrad(anti)
    return (ra, dec)


def body_latlon(
    et: float, body_id: int
) -> tuple[float, float, float, float]:
    """Sub-observer and sub-solar lat/long (radians). Returns (subobs_lat, subsol_lat, subobs_long, subsol_long)."""
    state = get_state()
    obs_pv = observer_state(et)
    body_dpv, dt = spkapp_shifted(body_id, et, "J2000", obs_pv, "LT")
    body_time = et - dt
    body_pv = cspyce.spkssb(body_id, body_time, "J2000")
    sun_dpv, _ = cspyce.spkapp(
        SUN_ID, body_time, "J2000", body_pv[:6], "LT+S"
    )
    rotmat = bodmat(body_id, body_time)
    obs_dp = [
        obs_pv[0] - body_pv[0],
        obs_pv[1] - body_pv[1],
        obs_pv[2] - body_pv[2],
    ]
    norm_dp = cspyce.vhat(obs_dp)
    tempvec = cspyce.vlcom(1.0, norm_dp, -1.0 / cspyce.clight(), body_pv[3:6])
    tempvec = cspyce.mxv(rotmat, tempvec)
    n = cspyce.vnorm(tempvec)
    subobs_lat = math.asin(tempvec[2] / n)
    subobs_long = -math.atan2(tempvec[1], tempvec[0])
    if subobs_long < 0:
        subobs_long += TWOPI
    tempvec = cspyce.mxv(rotmat, sun_dpv[:3])
    n = cspyce.vnorm(tempvec)
    subsol_lat = math.asin(tempvec[2] / n)
    subsol_long = -math.atan2(tempvec[1], tempvec[0])
    if subsol_long < 0:
        subsol_long += TWOPI
    if state.planet_num == 7:
        if subobs_long > 0:
            subobs_long = TWOPI - subobs_long
        if subsol_long > 0:
            subsol_long = TWOPI - subsol_long
    return (subobs_lat, subsol_lat, subobs_long, subsol_long)


def body_lonlat(
    et: float, body_id: int
) -> tuple[float, float, float, float]:
    """Sub-observer and sub-solar lon/lat (radians). Returns (subobs_lon, subobs_lat, subsol_lon, subsol_lat)."""
    subobs_lat, subsol_lat, subobs_long, subsol_long = body_latlon(et, body_id)
    return (subobs_long, subobs_lat, subsol_long, subsol_lat)


def moon_tracker_offsets(et: float, moon_ids: list[int]) -> tuple[list[float], float]:
    """East-west angular offsets of moons from planet and limb radius (radians).

    Port of RSPK_MoonDist. Positive offset = morning ansa (higher RA). Returns
    (offsets per moon in radians, limb angular radius in radians).
    """
    state = get_state()
    obs_pv = observer_state(et)
    planet_dpv, dt = cspyce.spkapp(
        state.planet_id, et, "J2000", obs_pv[:6], "LT"
    )
    planet_time = et - dt
    rotmat = bodmat(state.planet_id, planet_time)
    pole = [rotmat[2][0], rotmat[2][1], rotmat[2][2]]
    if state.planet_num == 7:
        pole = [-p for p in pole]
    x = cspyce.vhat(planet_dpv[:3])
    dot_xp = x[0] * pole[0] + x[1] * pole[1] + x[2] * pole[2]
    z = [pole[i] - dot_xp * x[i] for i in range(3)]
    zn = cspyce.vnorm(z)
    if zn < 1e-12:
        z = [0.0, 0.0, 1.0] if abs(x[2]) < 0.9 else [0.0, 1.0, 0.0]
        z = cspyce.vhat(cspyce.ucrss(x, z))
    else:
        z = [z[i] / zn for i in range(3)]
    y = cspyce.ucrss(z, x)
    offsets = []
    for mid in moon_ids:
        moon_dpv, _ = spkapp_shifted(mid, et, "J2000", obs_pv, "LT")
        vec = cspyce.mxv([x, y, z], moon_dpv[:3])
        offsets.append(math.atan2(vec[1], vec[0]))
    radii = cspyce.bodvrd(str(state.planet_id), "RADII")
    rkm = radii[0]
    limb_rad = math.asin(min(1.0, rkm / cspyce.vnorm(planet_dpv[:3])))
    return (offsets, limb_rad)
