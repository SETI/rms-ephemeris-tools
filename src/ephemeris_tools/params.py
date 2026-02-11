"""Unified parameter parsing for ephemeris, tracker, and viewer (env, CLI, API)."""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import TextIO

logger = logging.getLogger(__name__)

# General column IDs (ephem3_xxx.f COL_*)
COL_MJD = 1
COL_YMDHM = 2
COL_YMDHMS = 3
COL_YDHM = 4
COL_YDHMS = 5
COL_OBSDIST = 6
COL_SUNDIST = 7
COL_PHASE = 8
COL_OBSOPEN = 9
COL_SUNOPEN = 10
COL_OBSLON = 11
COL_SUNLON = 12
COL_SUBOBS = 13
COL_SUBSOL = 14
COL_RADEC = 15
COL_EARTHRD = 16
COL_SUNRD = 17
COL_RADIUS = 18
COL_RADDEG = 19
COL_LPHASE = 20
COL_SUNSEP = 21
COL_LSEP = 22

# Moon column IDs (MCOL_*)
MCOL_OBSDIST = 1
MCOL_PHASE = 2
MCOL_SUBOBS = 3
MCOL_SUBSOL = 4
MCOL_RADEC = 5
MCOL_OFFSET = 6
MCOL_OFFDEG = 7
MCOL_ORBLON = 8
MCOL_ORBOPEN = 9


@dataclass
class EphemerisParams:
    """Parameters for ephemeris table generation."""

    planet_num: int
    start_time: str
    stop_time: str
    interval: float = 1.0
    time_unit: str = 'hour'
    ephem_version: int = 0
    viewpoint: str = 'Earth'
    observatory: str = "Earth's Center"
    latitude_deg: float | None = None
    longitude_deg: float | None = None
    lon_dir: str = 'east'
    altitude_m: float | None = None
    sc_trajectory: int = 0
    columns: list[int] = field(default_factory=list)
    mooncols: list[int] = field(default_factory=list)
    moon_ids: list[int] = field(default_factory=list)
    output: TextIO | None = None


def _get_env(key: str, default: str = '') -> str:
    """Get environment variable, stripped."""
    return os.environ.get(key, default).strip()


def _get_keys_env(key: str) -> list[str]:
    """Get repeated env keys (e.g. columns#1, columns#2). Perl/CGI convention."""
    out: list[str] = []
    i = 1
    while True:
        v = os.environ.get(f'{key}#{i}', '').strip()
        if not v:
            v = os.environ.get(key if i == 1 else '', '').strip()
        if not v:
            break
        if '#' in v:
            v = v.split('#')[0].strip()
        out.append(v)
        i += 1
    if not out and key:
        single = os.environ.get(key, '').strip()
        if single:
            for part in single.replace(',', ' ').split():
                out.append(part)
    return out


def ephemeris_params_from_env() -> EphemerisParams | None:
    """Build EphemerisParams from CGI-style environment variables. Returns None if invalid."""
    nplanet_s = _get_env('NPLANET')
    if not nplanet_s:
        return None
    try:
        nplanet = int(nplanet_s.strip())
    except ValueError as e:
        logger.error('Invalid NPLANET %r (must be integer 4-9): %s', nplanet_s, e)
        return None
    if nplanet < 4 or nplanet > 9:
        logger.error('NPLANET %d out of range (must be 4-9)', nplanet)
        return None

    start = _get_env('start') or _get_env('START_TIME')
    stop = _get_env('stop') or _get_env('STOP_TIME')
    if not start or not stop:
        return None

    interval_s = _get_env('interval', '1')
    try:
        interval = float(interval_s)
    except ValueError as e:
        logger.error('Invalid interval %r (must be number): %s; using 1.0', interval_s, e)
        interval = 1.0
    time_unit = _get_env('time_unit', 'hour')
    if time_unit.lower()[:3] not in ('sec', 'min', 'hou', 'day'):
        time_unit = 'hour'

    ephem_s = _get_env('ephem', '0')
    try:
        ephem_version = int(ephem_s.split()[0])
    except (ValueError, IndexError) as e:
        logger.error('Invalid ephem %r (must be integer): %s; using 0 (latest)', ephem_s, e)
        ephem_version = 0

    viewpoint = _get_env('viewpoint', 'observatory')
    observatory = _get_env('observatory', "Earth's Center")
    lat_s = _get_env('latitude')
    lon_s = _get_env('longitude')
    alt_s = _get_env('altitude')
    lon_dir = _get_env('lon_dir', 'east')
    lat = float(lat_s) if lat_s else None
    lon = float(lon_s) if lon_s else None
    alt = float(alt_s) if alt_s else None
    if lat is not None and lon_dir.lower() == 'west':
        lon = -lon if lon is not None else None

    sc_traj_s = _get_env('sc_trajectory', '0')
    try:
        sc_trajectory = int(sc_traj_s[:4] or '0')
    except ValueError as e:
        logger.error('Invalid sc_trajectory %r: %s; using 0', sc_traj_s, e)
        sc_trajectory = 0

    column_strs = _get_keys_env('columns')
    columns: list[int] = []
    for s in column_strs:
        try:
            columns.append(int(s.strip()))
        except ValueError as e:
            logger.error('Invalid column value %r (must be integer): %s', s, e)

    mooncol_strs = _get_keys_env('mooncols')
    mooncols: list[int] = []
    for s in mooncol_strs:
        try:
            mooncols.append(int(s.strip()))
        except ValueError as e:
            logger.error('Invalid mooncol value %r (must be integer): %s', s, e)

    moon_strs = _get_keys_env('moons')
    moon_ids: list[int] = []
    for s in moon_strs:
        s = s.strip()
        if not s:
            continue
        try:
            idx = int(s.split()[0].split('(')[0])
            moon_ids.append(100 * nplanet + idx)
        except (ValueError, IndexError) as e:
            logger.error("Invalid moon value %r (expected index or 'N (Name)'): %s", s, e)
    if not moon_ids and moon_strs:
        for s in moon_strs:
            try:
                moon_ids.append(int(s) if int(s) > 100 else 100 * nplanet + int(s))
            except ValueError as e:
                logger.error('Invalid moon ID value %r: %s', s, e)

    return EphemerisParams(
        planet_num=nplanet,
        start_time=start,
        stop_time=stop,
        interval=interval,
        time_unit=time_unit,
        ephem_version=ephem_version,
        viewpoint=viewpoint,
        observatory=observatory,
        latitude_deg=lat,
        longitude_deg=lon,
        lon_dir=lon_dir,
        altitude_m=alt,
        sc_trajectory=sc_trajectory,
        columns=columns if columns else [COL_MJD, COL_YMDHMS, COL_RADEC, COL_PHASE],
        mooncols=mooncols if mooncols else [MCOL_RADEC, MCOL_OFFSET, MCOL_ORBLON, MCOL_ORBOPEN],
        moon_ids=moon_ids,
    )
