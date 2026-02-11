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

# Case-insensitive planet name -> planet number for --planet
PLANET_NAME_TO_NUM: dict[str, int] = {
    'mars': 4,
    'jupiter': 5,
    'saturn': 6,
    'uranus': 7,
    'neptune': 8,
    'pluto': 9,
}


def parse_planet(value: str) -> int:
    """Parse a planet specifier: integer 4-9 or name (mars..pluto).

    Raises ValueError if unrecognised.
    """
    v = value.strip()
    try:
        num = int(v)
        if 4 <= num <= 9:
            return num
        raise ValueError(f'planet number must be 4-9, got {num}')
    except ValueError:
        pass
    key = v.lower()
    if key in PLANET_NAME_TO_NUM:
        return PLANET_NAME_TO_NUM[key]
    raise ValueError(
        f'Unknown planet {value!r}; use 4-9 or a name: ' + ', '.join(PLANET_NAME_TO_NUM)
    )


# Case-insensitive name -> column ID for --columns (CLI and env)
COL_NAME_TO_ID: dict[str, int] = {
    'mjd': COL_MJD,
    'ymdhm': COL_YMDHM,
    'ymdhms': COL_YMDHMS,
    'ydhm': COL_YDHM,
    'ydhms': COL_YDHMS,
    'obsdist': COL_OBSDIST,
    'sundist': COL_SUNDIST,
    'phase': COL_PHASE,
    'obsopen': COL_OBSOPEN,
    'sunopen': COL_SUNOPEN,
    'obslon': COL_OBSLON,
    'sunlon': COL_SUNLON,
    'subobs': COL_SUBOBS,
    'subsol': COL_SUBSOL,
    'radec': COL_RADEC,
    'earthrd': COL_EARTHRD,
    'sunrd': COL_SUNRD,
    'radius': COL_RADIUS,
    'raddeg': COL_RADDEG,
    'lphase': COL_LPHASE,
    'sunsep': COL_SUNSEP,
    'lsep': COL_LSEP,
}

# Case-insensitive name -> moon column ID for --mooncols
MCOL_NAME_TO_ID: dict[str, int] = {
    'obsdist': MCOL_OBSDIST,
    'phase': MCOL_PHASE,
    'subobs': MCOL_SUBOBS,
    'subsol': MCOL_SUBSOL,
    'radec': MCOL_RADEC,
    'offset': MCOL_OFFSET,
    'offdeg': MCOL_OFFDEG,
    'orblon': MCOL_ORBLON,
    'orbopen': MCOL_ORBOPEN,
}


def parse_column_spec(tokens: list[str]) -> list[int]:
    """Convert list of column tokens (int strings or names) to column IDs.

    Each token may be a decimal column ID or a case-insensitive column name
    (e.g. ymdhms, radec, obslon). Invalid tokens are skipped with a log message.
    """
    out: list[int] = []
    for s in tokens:
        s = s.strip()
        if not s:
            continue
        try:
            out.append(int(s))
            continue
        except ValueError:
            pass
        key = s.lower()
        if key in COL_NAME_TO_ID:
            out.append(COL_NAME_TO_ID[key])
        else:
            logger.warning('Unknown column name %r; use an ID (1-22) or a known name', s)
    return out


def parse_mooncol_spec(tokens: list[str]) -> list[int]:
    """Convert list of moon column tokens (int strings or names) to moon column IDs.

    Each token may be a decimal ID or a case-insensitive name (e.g. radec, offset).
    Invalid tokens are skipped with a log message.
    """
    out: list[int] = []
    for s in tokens:
        s = s.strip()
        if not s:
            continue
        try:
            out.append(int(s))
            continue
        except ValueError:
            pass
        key = s.lower()
        if key in MCOL_NAME_TO_ID:
            out.append(MCOL_NAME_TO_ID[key])
        else:
            logger.warning('Unknown moon column name %r; use an ID (1-9) or a known name', s)
    return out


# Ring option codes: planet number -> (lowercase name -> code).
# These are the CGI ring option codes consumed by _ring_options_to_flags in tracker.py.
RING_NAME_TO_CODE: dict[int, dict[str, int]] = {
    5: {
        'main': 51,
        'gossamer': 52,
    },
    6: {
        'main': 61,
        'ge': 62,
        'outer': 63,
    },
    7: {
        'epsilon': 71,
    },
    8: {
        'rings': 81,
    },
}


def parse_ring_spec(planet_num: int, tokens: list[str]) -> list[int]:
    """Convert ring tokens (int strings or names) to ring option codes.

    Each token may be a decimal ring option code (e.g. 61) or a
    case-insensitive ring name (e.g. ``main``, ``gossamer``).
    The set of valid names depends on the planet. Unknown tokens are
    skipped with a log message.

    Parameters:
        planet_num: Planet number (4-9).
        tokens: List of string tokens from the CLI.

    Returns:
        List of integer ring option codes.
    """
    name_map = RING_NAME_TO_CODE.get(planet_num, {})
    out: list[int] = []
    for s in tokens:
        s = s.strip()
        if not s:
            continue
        try:
            out.append(int(s))
            continue
        except ValueError:
            pass
        key = s.lower()
        if key in name_map:
            out.append(name_map[key])
        else:
            valid = ', '.join(name_map) if name_map else '(none for this planet)'
            logger.warning(
                'Unknown ring name %r for planet %d; valid names: %s',
                s,
                planet_num,
                valid,
            )
    return out


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
    try:
        lat = float(lat_s) if lat_s else None
    except ValueError:
        logger.error('Invalid latitude %r: must be numeric', lat_s)
        lat = None
    try:
        lon = float(lon_s) if lon_s else None
    except ValueError:
        logger.error('Invalid longitude %r: must be numeric', lon_s)
        lon = None
    try:
        alt = float(alt_s) if alt_s else None
    except ValueError:
        logger.error('Invalid altitude %r: must be numeric', alt_s)
        alt = None
    if lon is not None and lon_dir.lower() == 'west':
        lon = -lon

    sc_traj_s = _get_env('sc_trajectory', '0')
    try:
        sc_trajectory = int(sc_traj_s[:4] or '0')
    except ValueError as e:
        logger.error('Invalid sc_trajectory %r: %s; using 0', sc_traj_s, e)
        sc_trajectory = 0

    column_strs = _get_keys_env('columns')
    columns = parse_column_spec(column_strs) if column_strs else []

    mooncol_strs = _get_keys_env('mooncols')
    mooncols = parse_mooncol_spec(mooncol_strs) if mooncol_strs else []

    moon_strs = _get_keys_env('moons')
    from ephemeris_tools.planets import parse_moon_spec

    moon_parsed = parse_moon_spec(nplanet, moon_strs) if moon_strs else []
    moon_ids = [v if v >= 100 else 100 * nplanet + v for v in moon_parsed]

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
