"""Ephemeris table generator (ported from ephem3_xxx.f)."""

from __future__ import annotations

import math
from typing import TextIO

from ephemeris_tools.constants import (
    EARTH_ID,
    MOON_ID,
    SUN_ID,
    spacecraft_code_to_id,
    spacecraft_name_to_code,
)
from ephemeris_tools.params import (
    COL_EARTHRD,
    COL_LPHASE,
    COL_LSEP,
    COL_MJD,
    COL_OBSOPEN,
    COL_OBSDIST,
    COL_OBSLON,
    COL_RADEC,
    COL_RADDEG,
    COL_RADIUS,
    COL_SUBOBS,
    COL_SUBSOL,
    COL_SUNDIST,
    COL_SUNOPEN,
    COL_SUNRD,
    COL_SUNLON,
    COL_SUNSEP,
    COL_PHASE,
    COL_YDHM,
    COL_YDHMS,
    COL_YMDHM,
    COL_YMDHMS,
    EphemerisParams,
    MCOL_OFFDEG,
    MCOL_OFFSET,
    MCOL_ORBLON,
    MCOL_ORBOPEN,
    MCOL_PHASE,
    MCOL_RADEC,
    MCOL_SUBOBS,
    MCOL_SUBSOL,
    MCOL_OBSDIST,
)
from ephemeris_tools.constants import PLANET_NUM_TO_ID
from ephemeris_tools.record import Record
from ephemeris_tools.spice.geometry import (
    body_latlon,
    body_phase,
    body_radec,
    body_ranges,
    conjunction_angle,
    limb_radius,
    planet_phase,
    planet_ranges,
)
from ephemeris_tools.spice.load import load_spacecraft, load_spice_files
from ephemeris_tools.spice.observer import set_observer_id, set_observer_location
from ephemeris_tools.spice.orbits import orbit_opening
from ephemeris_tools.spice.rings import ring_opening
from ephemeris_tools.time_utils import (
    day_sec_from_tai,
    mjd_from_tai,
    parse_datetime,
    tai_from_day_sec,
    tdb_from_tai,
    yd_from_day,
    ymd_from_day,
    hms_from_sec,
)

DPR = 180.0 / math.pi
HPR = DPR / 15.0
SPR = DPR * 3600.0
MAXSECS = 360.0 * 60.0 * 60.0


def _interval_seconds(interval: float, time_unit: str) -> float:
    """Convert interval and time_unit to seconds."""
    u = time_unit.lower()[:4]
    if u == "sec":
        return max(abs(interval), 1.0)
    if u == "min":
        return max(abs(interval) * 60.0, 1.0)
    if u == "hour":
        return max(abs(interval) * 3600.0, 1.0)
    if u == "day":
        return max(abs(interval) * 86400.0, 1.0)
    return max(abs(interval) * 3600.0, 1.0)


def _set_observer_from_params(params: EphemerisParams) -> None:
    """Set SPICE observer from params (viewpoint, observatory, or latlon)."""
    if params.viewpoint == "latlon" and params.latitude_deg is not None and params.longitude_deg is not None:
        alt = params.altitude_m if params.altitude_m is not None else 0.0
        set_observer_location(params.latitude_deg, params.longitude_deg, alt)
        return
    if params.observatory and params.observatory != "Earth's Center":
        code = spacecraft_name_to_code(params.observatory)
        if code is not None:
            sc_id = spacecraft_code_to_id(code)
            if sc_id:
                load_spacecraft(
                    sc_id,
                    params.planet_num,
                    params.sc_trajectory,
                    set_obs=True,
                )
                return
        if "Earth" in params.observatory or not params.observatory.strip():
            set_observer_id(EARTH_ID)
            return
    set_observer_id(EARTH_ID)


def _round_sec_to_min(sec: float) -> float:
    """Round seconds to nearest minute (60 * nint(sec/60))."""
    return 60.0 * round(sec / 60.0)


def _round_sec_to_sec(sec: float) -> float:
    """Round to nearest second."""
    return round(sec)


def generate_ephemeris(params: EphemerisParams, output: TextIO | None = None) -> None:
    """Generate ephemeris table and write to output stream.

    If output is None, uses params.output. If both are None, no output is written.
    """
    out = output or params.output
    if out is None:
        return

    start_parsed = parse_datetime(params.start_time)
    stop_parsed = parse_datetime(params.stop_time)
    if start_parsed is None or stop_parsed is None:
        raise ValueError("Invalid start or stop time")
    day1, sec1 = start_parsed
    day2, sec2 = stop_parsed
    tai1 = tai_from_day_sec(day1, _round_sec_to_min(sec1) if params.time_unit.startswith("min") else sec1)
    tai2 = tai_from_day_sec(day2, _round_sec_to_min(sec2) if params.time_unit.startswith("min") else sec2)
    dsec = _interval_seconds(params.interval, params.time_unit)
    ntimes = int((tai2 - tai1) / dsec) + 1
    if ntimes < 2:
        raise ValueError("Time range too short or interval too large")
    if ntimes > 100000:
        raise ValueError("Number of time steps exceeds limit of 100000")

    ok, reason = load_spice_files(params.planet_num, params.ephem_version)
    if not ok:
        raise RuntimeError(f"Failed to load SPICE kernels: {reason}")
    _set_observer_from_params(params)

    rec = Record()
    columns = params.columns or [COL_MJD, COL_YMDHMS, COL_RADEC, COL_PHASE]
    mooncols = params.mooncols or []
    moon_ids = list(params.moon_ids)
    planet_id = PLANET_NUM_TO_ID.get(params.planet_num, 100 * params.planet_num + 99)

    for irec in range(ntimes + 1):
        if irec == 0:
            tai = tai1 - dsec
        else:
            tai = tai1 + (irec - 1) * dsec
        et = tdb_from_tai(tai) if irec > 0 else 0.0

        if irec > 0:
            planet_ra, planet_dec = body_radec(et, planet_id)
            cosdec = math.cos(planet_dec)
        else:
            planet_ra = planet_dec = cosdec = 0.0

        ring_geom = None
        if irec > 0 and any(c in columns for c in (COL_OBSOPEN, COL_SUNOPEN, COL_OBSLON, COL_SUNLON)):
            ring_geom = ring_opening(et)

        subobs_lat = subobs_lon = subsol_lat = subsol_lon = 0.0
        if irec > 0 and any(c in columns for c in (COL_SUBOBS, COL_SUBSOL)):
            subobs_lat, subsol_lat, subobs_lon, subsol_lon = body_latlon(et, planet_id)

        sun_dist = obs_dist = 0.0
        if irec > 0 and any(c in columns for c in (COL_OBSDIST, COL_SUNDIST)):
            sun_dist, obs_dist = planet_ranges(et)

        rec.init()
        for col in columns:
            if col == COL_MJD:
                if irec == 0:
                    rec.append(" mjd        ")
                else:
                    rec.append(f"{mjd_from_tai(tai):12.5f}")
            elif col == COL_YMDHM:
                if irec == 0:
                    rec.append("year mo dy hr mi")
                else:
                    d, s = day_sec_from_tai(tai)
                    s = _round_sec_to_min(s)
                    if s >= 86400.0:
                        d += 1
                        s = 0.0
                    year, month, day = ymd_from_day(d)
                    hour, minute, _ = hms_from_sec(s)
                    rec.append(f"{year:4d}{month:3d}{day:3d}{hour:3d}{minute:3d}")
            elif col == COL_YMDHMS:
                if irec == 0:
                    rec.append("year mo dy hr mi sc")
                else:
                    d, s = day_sec_from_tai(tai)
                    s = _round_sec_to_sec(s)
                    if s >= 86400.0:
                        d += 1
                        s = 0.0
                    year, month, day = ymd_from_day(d)
                    hour, minute, sec = hms_from_sec(s)
                    rec.append(f"{year:4d}{month:3d}{day:3d}{hour:3d}{minute:3d}{int(sec):3d}")
            elif col == COL_YDHM:
                if irec == 0:
                    rec.append("year doy hr mi")
                else:
                    d, s = day_sec_from_tai(tai)
                    s = _round_sec_to_min(s)
                    if s >= 86400.0:
                        d += 1
                        s = 0.0
                    year, doy = yd_from_day(d)
                    hour, minute, _ = hms_from_sec(s)
                    rec.append(f"{year:4d}{doy:4d}{hour:3d}{minute:3d}")
            elif col == COL_YDHMS:
                if irec == 0:
                    rec.append("year doy hr mi sc")
                else:
                    d, s = day_sec_from_tai(tai)
                    s = _round_sec_to_sec(s)
                    if s >= 86400.0:
                        d += 1
                        s = 0.0
                    year, doy = yd_from_day(d)
                    hour, minute, sec = hms_from_sec(s)
                    rec.append(f"{year:4d}{doy:4d}{hour:3d}{minute:3d}{int(sec):3d}")
            elif col == COL_OBSDIST:
                if irec == 0:
                    rec.append("  obs_dist")
                else:
                    s = f"{obs_dist:10.0f}"
                    if len(s) > 10 or s.strip().startswith("*"):
                        s = f"{obs_dist:10.4e}"
                    rec.append(s[:10])
            elif col == COL_SUNDIST:
                if irec == 0:
                    rec.append("  sun_dist")
                else:
                    rec.append(f"{sun_dist:10.4e}")
            elif col == COL_PHASE:
                if irec == 0:
                    rec.append("    phase")
                else:
                    phase = planet_phase(et)
                    rec.append(f"{phase * DPR:9.5f}")
            elif col == COL_OBSOPEN:
                if irec == 0:
                    rec.append(" obs_open")
                else:
                    rec.append(f"{(ring_geom or ring_opening(et)).obs_b * DPR:9.5f}")
            elif col == COL_SUNOPEN:
                if irec == 0:
                    rec.append(" sun_open")
                else:
                    rec.append(f"{(ring_geom or ring_opening(et)).sun_b * DPR:9.5f}")
            elif col == COL_OBSLON:
                if irec == 0:
                    rec.append("  obs_lon")
                else:
                    rec.append(f"{(ring_geom or ring_opening(et)).obs_long * DPR:9.5f}")
            elif col == COL_SUNLON:
                if irec == 0:
                    rec.append("  sun_lon")
                else:
                    rec.append(f"{(ring_geom or ring_opening(et)).sun_long * DPR:9.5f}")
            elif col == COL_SUBOBS:
                if irec == 0:
                    rec.append("subobslat subobslon")
                else:
                    rec.append(f"{subobs_lat * DPR:9.5f}{subobs_lon * DPR:10.5f}")
            elif col == COL_SUBSOL:
                if irec == 0:
                    rec.append("subsollat subsollon")
                else:
                    rec.append(f"{subsol_lat * DPR:9.5f}{subsol_lon * DPR:10.5f}")
            elif col == COL_RADEC:
                if irec == 0:
                    rec.append("planet_ra planet_dec")
                else:
                    rec.append(f"{planet_ra * HPR:9.6f}{planet_dec * DPR:11.5f}")
            elif col == COL_EARTHRD:
                if irec == 0:
                    rec.append(" earth_ra earth_dec")
                else:
                    ra, dec = body_radec(et, EARTH_ID)
                    rec.append(f"{ra * HPR:9.6f}{dec * DPR:10.5f}")
            elif col == COL_SUNRD:
                if irec == 0:
                    rec.append("   sun_ra   sun_dec")
                else:
                    ra, dec = body_radec(et, SUN_ID)
                    rec.append(f"{ra * HPR:9.6f}{dec * DPR:10.5f}")
            elif col == COL_RADIUS:
                if irec == 0:
                    rec.append("  radius")
                else:
                    _, rrad = limb_radius(et)
                    rec.append(f"{rrad * SPR:8.3f}")
            elif col == COL_RADDEG:
                if irec == 0:
                    rec.append("  r_deg")
                else:
                    _, rrad = limb_radius(et)
                    rec.append(f"{rrad * DPR:7.3f}")
            elif col == COL_LPHASE:
                if irec == 0:
                    rec.append("lun_phase")
                else:
                    mp = body_phase(et, MOON_ID)
                    rec.append(f"{mp * DPR:9.5f}")
            elif col == COL_SUNSEP:
                if irec == 0:
                    rec.append("  sun_sep")
                else:
                    sep = conjunction_angle(et, planet_id, SUN_ID)
                    rec.append(f"{sep * DPR:9.5f}")
            elif col == COL_LSEP:
                if irec == 0:
                    rec.append(" moon_sep")
                else:
                    sep = conjunction_angle(et, planet_id, MOON_ID)
                    rec.append(f"{sep * DPR:9.5f}")

        for mid in moon_ids:
            prefix = _moon_prefix(mid, params.planet_num)
            for mcol in mooncols:
                if mcol == MCOL_OBSDIST:
                    if irec == 0:
                        rec.append(prefix + "dist")
                    else:
                        _, obs_d = body_ranges(et, mid)
                        s = f"{obs_d:10.0f}"
                        if len(s) > 10:
                            s = f"{obs_d:10.4e}"
                        rec.append(s[:10])
                elif mcol == MCOL_PHASE:
                    if irec == 0:
                        rec.append(prefix + "phase")
                    else:
                        ph = body_phase(et, mid)
                        rec.append(f"{ph * DPR:10.5f}")
                elif mcol == MCOL_SUBOBS:
                    if irec == 0:
                        rec.append(prefix + "olat " + prefix + "olon")
                    else:
                        subobs_lat_m, _, subobs_lon_m, _ = body_latlon(et, mid)
                        rec.append(f"{subobs_lat_m * DPR:9.5f}{subobs_lon_m * DPR:10.5f}")
                elif mcol == MCOL_SUBSOL:
                    if irec == 0:
                        rec.append(prefix + "slat " + prefix + "slon")
                    else:
                        _, subsol_lat_m, _, subsol_lon_m = body_latlon(et, mid)
                        rec.append(f"{subsol_lat_m * DPR:9.5f}{subsol_lon_m * DPR:10.5f}")
                elif mcol == MCOL_RADEC:
                    if irec == 0:
                        rec.append("  " + prefix + "ra  " + prefix + "dec")
                    else:
                        ra, dec = body_radec(et, mid)
                        rec.append(f"{ra * HPR:9.6f}{dec * DPR:10.5f}")
                elif mcol == MCOL_OFFSET:
                    if irec == 0:
                        rec.append(" " + prefix + "dra " + prefix + "ddec")
                    else:
                        ra, dec = body_radec(et, mid)
                        ddec = SPR * (dec - planet_dec)
                        dra = SPR * (ra - planet_ra)
                        if dra < -0.5 * MAXSECS:
                            dra += MAXSECS
                        if dra > 0.5 * MAXSECS:
                            dra -= MAXSECS
                        dra *= cosdec
                        rec.append(f"{dra:9.3f}{ddec:10.3f}")
                elif mcol == MCOL_OFFDEG:
                    if irec == 0:
                        rec.append(" " + prefix + "dra " + prefix + "ddec")
                    else:
                        ra, dec = body_radec(et, mid)
                        ddec = DPR * (dec - planet_dec)
                        dra = DPR * (ra - planet_ra)
                        if dra < -180.0:
                            dra += 360.0
                        if dra > 180.0:
                            dra -= 360.0
                        dra *= cosdec
                        rec.append(f"{dra:9.5f}{ddec:10.5f}")
                elif mcol == MCOL_ORBLON:
                    if irec == 0:
                        rec.append(prefix + "orbit")
                    else:
                        _, obs_lon = orbit_opening(et, mid)
                        rec.append(f"{obs_lon * DPR:10.5f}")
                elif mcol == MCOL_ORBOPEN:
                    if irec == 0:
                        rec.append(prefix + "open")
                    else:
                        obs_b, _ = orbit_opening(et, mid)
                        rec.append(f"{obs_b * DPR:9.5f}")

        rec.write(out)


def _moon_prefix(moon_id: int, planet_num: int) -> str:
    """Short prefix for moon column labels (e.g. 'Mima_')."""
    from ephemeris_tools.planets import (
        JUPITER_CONFIG,
        MARS_CONFIG,
        NEPTUNE_CONFIG,
        PLUTO_CONFIG,
        SATURN_CONFIG,
        URANUS_CONFIG,
    )
    configs = {
        4: MARS_CONFIG, 5: JUPITER_CONFIG, 6: SATURN_CONFIG,
        7: URANUS_CONFIG, 8: NEPTUNE_CONFIG, 9: PLUTO_CONFIG,
    }
    cfg = configs.get(planet_num)
    if cfg:
        m = cfg.moon_by_id(moon_id)
        if m:
            name = m.name[:4] if len(m.name) >= 4 else m.name + "_" * (4 - len(m.name))
            return name + "_"
    return "moon_"
