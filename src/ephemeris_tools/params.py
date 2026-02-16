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

_PLANET_NUM_TO_NAME: dict[int, str] = {v: k.capitalize() for k, v in PLANET_NAME_TO_NUM.items()}

_FOV_ALIASES: dict[str, str] = {
    'deg': 'degrees',
    'degree': 'degrees',
    'degrees': 'degrees',
    'arcmin': 'minutes of arc',
    'minute of arc': 'minutes of arc',
    'minutes of arc': 'minutes of arc',
    'arcsec': 'seconds of arc',
    'second of arc': 'seconds of arc',
    'seconds of arc': 'seconds of arc',
    'mrad': 'milliradians',
    'milliradian': 'milliradians',
    'milliradians': 'milliradians',
    'urad': 'microradians',
    'microradian': 'microradians',
    'microradians': 'microradians',
    'km': 'kilometers',
    'kilometer': 'kilometers',
    'kilometers': 'kilometers',
}

_FOV_INSTRUMENT_PREFIXES: dict[str, str] = {
    'voyager iss narrow': 'Voyager ISS narrow angle FOVs',
    'voyager iss wide': 'Voyager ISS wide angle FOVs',
    'cassini iss narrow': 'Cassini ISS narrow angle FOVs',
    'cassini iss wide': 'Cassini ISS wide angle FOVs',
    'galileo ssi': 'Galileo SSI FOVs',
    'cassini vims': 'Cassini VIMS 64x64 FOVs',
    'cassini uvis': 'Cassini UVIS slit FOVs',
    'lorri': 'LORRI FOVs',
}

_CENTER_ANSA_NAME_MAP: dict[int, dict[str, str]] = {
    4: {
        'phobos ring': 'Phobos Ring',
        'deimos ring': 'Deimos Ring',
    },
    5: {
        'main ring': 'Main Ring',
        'thebe ring': 'Thebe Ring',
        'amalthea ring': 'Amalthea Ring',
        'halo': 'Halo',
    },
    6: {
        'a ring': 'A Ring',
        'b ring': 'B Ring',
        'c ring': 'C Ring',
        'f ring': 'F Ring',
        'g ring': 'G Ring',
        'e ring': 'E Ring',
    },
    7: {
        '6 ring': '6 Ring',
        '5 ring': '5 Ring',
        '4 ring': '4 Ring',
        'alpha ring': 'Alpha Ring',
        'beta ring': 'Beta Ring',
        'eta ring': 'Eta Ring',
        'gamma ring': 'Gamma Ring',
        'delta ring': 'Delta Ring',
        'epsilon ring': 'Epsilon Ring',
        'nu ring': 'Nu Ring',
        'mu ring': 'Mu Ring',
    },
    8: {
        'galle ring': 'Galle Ring',
        'galle': 'Galle Ring',
        'leverrier ring': 'LeVerrier Ring',
        'leverrier': 'LeVerrier Ring',
        'arago ring': 'Arago Ring',
        'arago': 'Arago Ring',
        'adams ring': 'Adams Ring',
        'adams': 'Adams Ring',
    },
    9: {
        'charon': 'Charon',
        'styx': 'Styx',
        'nix': 'Nix',
        'kerberos': 'Kerberos',
        'hydra': 'Hydra',
    },
}

_VIEWER_RING_NAME_MAP: dict[int, dict[str, str]] = {
    4: {'phobos': 'Phobos', 'deimos': 'Deimos'},
    5: {'main': 'Main', 'gossamer': 'Gossamer'},
    6: {
        'a': 'A',
        'b': 'B',
        'c': 'C',
        'f': 'F',
        'g': 'G',
        'e': 'E',
    },
    7: {
        '6': '6',
        '5': '5',
        '4': '4',
        'alpha': 'Alpha',
        'beta': 'Beta',
        'eta': 'Eta',
        'gamma': 'Gamma',
        'delta': 'Delta',
        'epsilon': 'Epsilon',
        'nu': 'Nu',
        'mu': 'Mu',
    },
    8: {
        'galle': 'Galle',
        'leverrier': 'LeVerrier',
        'arago': 'Arago',
        'adams': 'Adams',
    },
    9: {
        'charon': 'Charon',
        'styx': 'Styx',
        'nix': 'Nix',
        'kerberos': 'Kerberos',
        'hydra': 'Hydra',
    },
}


def parse_planet(value: str) -> int:
    """Parse planet specifier: integer 4-9 or name (mars..pluto).

    Parameters:
        value: Planet number string or name (case-insensitive).

    Returns:
        Planet number (4-9).

    Raises:
        ValueError: If value is not a valid planet.
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


def parse_fov(tokens: list[str]) -> tuple[float, str]:
    """Parse CLI ``--fov`` tokens into numeric value and canonical unit string.

    Parameters:
        tokens: Tokenized FOV value from CLI, where the first token is numeric and
            remaining tokens form the unit string.

    Returns:
        Tuple ``(value, unit)`` where ``value`` is the parsed float and ``unit`` is
        the canonical unit string.

    Raises:
        ValueError: If no tokens are provided, numeric value cannot be parsed, or the
            unit is unknown.
    """
    if len(tokens) == 0:
        raise ValueError('FOV requires at least one token')
    first = tokens[0].strip()
    try:
        value = float(first)
    except ValueError as e:
        raise ValueError('FOV first token must be numeric') from e
    if len(tokens) == 1:
        return (value, 'degrees')

    unit_raw = ' '.join(part.strip() for part in tokens[1:] if part.strip()).lower()
    if unit_raw in _FOV_ALIASES:
        return (value, _FOV_ALIASES[unit_raw])

    sorted_prefixes = sorted(
        _FOV_INSTRUMENT_PREFIXES.items(),
        key=lambda item: -len(item[0]),
    )
    for prefix, canonical in sorted_prefixes:
        if unit_raw.startswith(prefix):
            return (value, canonical)

    if unit_raw.endswith(' radii'):
        planet_name = unit_raw[:-6].strip()
        if planet_name in PLANET_NAME_TO_NUM:
            return (value, f'{planet_name.capitalize()} radii')

    raise ValueError(f'Unknown FOV unit: {unit_raw!r}')


def _parse_ra_token_degrees(token: str) -> float:
    """Parse RA token as degrees, supporting ``h`` suffix for hours."""
    raw = token.strip().lower()
    if raw.endswith('h'):
        return float(raw[:-1]) * 15.0
    return float(raw)


def parse_center(planet_num: int, tokens: list[str]) -> ViewerCenter:
    """Parse CLI ``--center`` tokens into a structured viewer center definition.

    Parameters:
        planet_num: Planet number (4-9) for body/ring lookups.
        tokens: Tokenized center specification from CLI.

    Returns:
        Parsed center as a ``ViewerCenter`` object.
    """
    from ephemeris_tools.planets import (
        JUPITER_CONFIG,
        MARS_CONFIG,
        NEPTUNE_CONFIG,
        PLUTO_CONFIG,
        SATURN_CONFIG,
        URANUS_CONFIG,
    )

    cfg_map = {
        4: MARS_CONFIG,
        5: JUPITER_CONFIG,
        6: SATURN_CONFIG,
        7: URANUS_CONFIG,
        8: NEPTUNE_CONFIG,
        9: PLUTO_CONFIG,
    }
    cfg = cfg_map.get(planet_num)
    planet_name = _PLANET_NUM_TO_NAME.get(planet_num, str(planet_num))
    if cfg is None:
        return ViewerCenter(mode='body', body_name=planet_name)
    if len(tokens) == 0:
        return ViewerCenter(mode='body', body_name=planet_name)

    normalized = [tok.strip() for tok in tokens if tok.strip()]
    if len(normalized) == 0:
        return ViewerCenter(mode='body', body_name=planet_name)

    # J2000 coordinate pair: <ra> <dec>, with optional hour suffix for RA.
    if len(normalized) == 2:
        try:
            ra_deg = _parse_ra_token_degrees(normalized[0])
            dec_deg = float(normalized[1])
            return ViewerCenter(mode='J2000', ra_deg=ra_deg, dec_deg=dec_deg)
        except ValueError:
            pass

    # Ring ansa name with optional east/west.
    ew = 'east'
    ansa_tokens = normalized
    if normalized[-1].lower() in ('east', 'west'):
        ew = normalized[-1].lower()
        ansa_tokens = normalized[:-1]
    ansa_candidate = ' '.join(ansa_tokens).lower()
    ring_name_map = {
        ring.name.lower(): ring.name
        for ring in cfg.rings
        if ring.name is not None and ring.name.strip()
    }
    ring_name_map.update(_CENTER_ANSA_NAME_MAP.get(planet_num, {}))
    if ansa_candidate.endswith(' ring'):
        no_suffix = ansa_candidate[:-5].strip()
        if no_suffix in ring_name_map:
            return ViewerCenter(mode='ansa', ansa_name=ring_name_map[no_suffix], ansa_ew=ew)
    if ansa_candidate in ring_name_map:
        return ViewerCenter(mode='ansa', ansa_name=ring_name_map[ansa_candidate], ansa_ew=ew)

    # Body lookup by planet name or moon names.
    body_candidate = ' '.join(normalized).lower()
    if body_candidate == cfg.planet_name.lower():
        return ViewerCenter(mode='body', body_name=cfg.planet_name)
    moon_name_map = {
        moon.name.lower(): moon.name
        for moon in cfg.moons
        if moon.name is not None and moon.name.strip() and moon.id != cfg.planet_id
    }
    if body_candidate in moon_name_map:
        return ViewerCenter(mode='body', body_name=moon_name_map[body_candidate])

    # Fallback: star name.
    return ViewerCenter(mode='star', star_name=' '.join(normalized))


def parse_viewer_rings(planet_num: int, tokens: list[str]) -> list[str]:
    """Parse viewer ring tokens into canonical ring names.

    Parameters:
        planet_num: Planet number (4-9).
        tokens: Ring name tokens from CLI.

    Returns:
        Canonical ring names in first-seen order. Supports ``all`` and ``none``.
    """
    mapping = _VIEWER_RING_NAME_MAP.get(planet_num, {})
    if len(tokens) == 0:
        return []

    out: list[str] = []
    seen: set[str] = set()

    def _append_unique(name: str) -> None:
        if name in seen:
            return
        seen.add(name)
        out.append(name)

    for token in tokens:
        key = token.strip().lower()
        if not key:
            continue
        if key == 'none':
            return []
        if key == 'all':
            for canonical in mapping.values():
                _append_unique(canonical)
            continue
        if key in mapping:
            _append_unique(mapping[key])
    return out


def parse_observer(tokens: list[str]) -> Observer:
    """Parse CLI observer tokens into a structured observer definition.

    Parameters:
        tokens: Observer tokens from CLI. Either a named observer/observatory or a
            numeric ``latitude longitude altitude`` triplet.

    Returns:
        Parsed observer object.

    Raises:
        ValueError: If the input looks numeric but is not a valid triplet.
    """
    if len(tokens) == 0:
        return Observer(name="Earth's Center")

    normalized = [tok.strip() for tok in tokens if tok.strip()]
    if len(normalized) == 0:
        return Observer(name="Earth's Center")

    if len(normalized) == 3:
        try:
            latitude = float(normalized[0])
            longitude = float(normalized[1])
            altitude = float(normalized[2])
            return Observer(latitude_deg=latitude, longitude_deg=longitude, altitude_m=altitude)
        except ValueError:
            pass

    if len(normalized) in (1, 2):
        all_numeric = True
        for token in normalized:
            try:
                float(token)
            except ValueError:
                all_numeric = False
                break
        if all_numeric:
            raise ValueError('Observer numeric form requires three numeric tokens: lat lon alt')

    name = ' '.join(normalized)
    if name.lower() in {'earth', "earth's center", 'earths center'}:
        name = "Earth's Center"
    return Observer(name=name)


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
    """Convert column tokens to column IDs (ephem3_xxx.f COL_*).

    Parameters:
        tokens: List of decimal IDs or case-insensitive names (e.g. ymdhms, radec).

    Returns:
        List of column IDs; invalid tokens are skipped (logged).
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
    """Convert moon column tokens to moon column IDs (MCOL_*).

    Parameters:
        tokens: List of decimal IDs or case-insensitive names (e.g. radec, offset).

    Returns:
        List of moon column IDs; invalid tokens are skipped (logged).
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
        'alpha': 71,
        'beta': 71,
        'eta': 71,
        'gamma': 71,
        'delta': 71,
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
class Observer:
    """Observer location and trajectory selection shared by all tools.

    Parameters:
        name: Named observer, observatory, or spacecraft identifier.
        latitude_deg: Observer latitude in degrees.
        longitude_deg: Observer longitude in degrees; east-positive.
        altitude_m: Observer altitude in meters.
        sc_trajectory: Optional spacecraft trajectory selector.
    """

    name: str | None = None
    latitude_deg: float | None = None
    longitude_deg: float | None = None
    altitude_m: float | None = None
    sc_trajectory: int = 0


@dataclass
class ViewerCenter:
    """Viewer center specification.

    Parameters:
        mode: One of ``body``, ``ansa``, ``J2000``, or ``star``.
        body_name: Center body name when mode is ``body``.
        ansa_name: Ring ansa name when mode is ``ansa``.
        ansa_ew: Ring ansa side (``east`` or ``west``) when mode is ``ansa``.
        ra_deg: Right ascension in degrees when mode is ``J2000``.
        dec_deg: Declination in degrees when mode is ``J2000``.
        star_name: Star name when mode is ``star``.
    """

    mode: str = 'body'
    body_name: str | None = None
    ansa_name: str | None = None
    ansa_ew: str | None = None
    ra_deg: float | None = None
    dec_deg: float | None = None
    star_name: str | None = None


@dataclass
class ExtraStar:
    """Optional extra star marker for viewer plots.

    Parameters:
        name: Display name.
        ra_deg: Right ascension in degrees.
        dec_deg: Declination in degrees.
    """

    name: str = ''
    ra_deg: float = 0.0
    dec_deg: float = 0.0


@dataclass
class ViewerDisplayInfo:
    """Display-only strings preserved from CGI inputs.

    Parameters:
        ephem_display: Ephemeris display string.
        moons_display: Moon selection display string.
        rings_display: Ring selection display string.
    """

    ephem_display: str | None = None
    moons_display: str | None = None
    rings_display: str | None = None


@dataclass
class ViewerParams:
    """Structured inputs for viewer backend execution."""

    planet_num: int
    time_str: str
    fov_value: float = 1.0
    fov_unit: str = 'degrees'
    center: ViewerCenter = field(default_factory=ViewerCenter)
    observer: Observer = field(default_factory=Observer)
    ephem_version: int = 0
    moon_ids: list[int] | None = None
    ring_names: list[str] | None = None
    blank_disks: bool = False
    opacity: str = 'Transparent'
    labels: str = 'Small (6 points)'
    moonpts: float = 0.0
    peris: str = 'None'
    peripts: float = 4.0
    meridians: bool = False
    arcmodel: str | None = None
    arcpts: float = 4.0
    show_standard_stars: bool = False
    extra_star: ExtraStar | None = None
    other_bodies: list[str] | None = None
    torus: bool = False
    torus_inc: float = 6.8
    torus_rad: float = 422000.0
    title: str = ''
    display: ViewerDisplayInfo | None = None
    output_ps: TextIO | None = None
    output_txt: TextIO | None = None


@dataclass
class TrackerParams:
    """Structured inputs for tracker backend execution."""

    planet_num: int
    start_time: str
    stop_time: str
    interval: float = 1.0
    time_unit: str = 'hours'
    observer: Observer = field(default_factory=Observer)
    ephem_version: int = 0
    moon_ids: list[int] = field(default_factory=list)
    ring_names: list[str] | None = None
    xrange: float | None = None
    xunit: str = 'arcsec'
    title: str = ''
    output_ps: TextIO | None = None
    output_txt: TextIO | None = None


@dataclass
class EphemerisParams:
    """Parameters for ephemeris table generation (ephem3_xxx.f request summary)."""

    planet_num: int
    start_time: str
    stop_time: str
    interval: float = 1.0
    time_unit: str = 'hour'
    ephem_version: int = 0
    observer: Observer = field(default_factory=Observer)
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
    """Get environment variable, stripped.

    Parameters:
        key: Environment variable name.
        default: Value if key missing.

    Returns:
        Stripped string.
    """
    return os.environ.get(key, default).strip()


def _get_keys_env(key: str) -> list[str]:
    """Get repeated env keys (e.g. columns#1, columns#2). Perl/CGI convention.

    Parameters:
        key: Base name (e.g. 'columns').

    Returns:
        List of values from key, key#1, key#2, ... or comma/split of single value.
    """
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
    """Build EphemerisParams from CGI-style environment variables.

    Reads NPLANET, start, stop, interval, viewpoint, columns, etc. from env.

    Returns:
        EphemerisParams or None if required keys are missing/invalid.
    """
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


def viewer_params_from_env() -> ViewerParams | None:
    """Build ``ViewerParams`` from CGI-style environment variables."""
    nplanet_s = _get_env('NPLANET')
    if not nplanet_s:
        return None
    try:
        planet_num = int(nplanet_s)
    except ValueError:
        return None
    time_str = _get_env('time')
    if not time_str:
        return None
    fov_s = _get_env('fov', '1')
    try:
        fov_value = float(fov_s)
    except ValueError:
        fov_value = 1.0
    fov_unit = _get_env('fov_unit', 'degrees')

    center_mode = _get_env('center', 'body')
    if center_mode == 'J2000':
        try:
            ra_deg = float(_get_env('center_ra', '0'))
        except ValueError:
            ra_deg = 0.0
        try:
            dec_deg = float(_get_env('center_dec', '0'))
        except ValueError:
            dec_deg = 0.0
        center = ViewerCenter(mode='J2000', ra_deg=ra_deg, dec_deg=dec_deg)
    elif center_mode == 'ansa':
        center = ViewerCenter(
            mode='ansa',
            ansa_name=_get_env('center_ansa') or None,
            ansa_ew=_get_env('center_ew', 'east'),
        )
    elif center_mode == 'star':
        center = ViewerCenter(mode='star', star_name=_get_env('center_star') or None)
    else:
        center = ViewerCenter(mode='body', body_name=_get_env('center_body') or None)

    viewpoint = _get_env('viewpoint', 'observatory')
    observer = Observer(name="Earth's Center")
    if viewpoint == 'latlon':
        lat_s = _get_env('latitude')
        lon_s = _get_env('longitude')
        alt_s = _get_env('altitude')
        try:
            lat = float(lat_s) if lat_s else None
        except ValueError:
            lat = None
        try:
            lon = float(lon_s) if lon_s else None
        except ValueError:
            lon = None
        try:
            alt = float(alt_s) if alt_s else None
        except ValueError:
            alt = None
        observer = Observer(latitude_deg=lat, longitude_deg=lon, altitude_m=alt)
    elif viewpoint == 'observatory':
        observer = Observer(name=_get_env('observatory', "Earth's Center"))
    elif viewpoint:
        observer = Observer(name=viewpoint)

    moon_tokens = _get_keys_env('moons')
    from ephemeris_tools.planets import parse_moon_spec

    moon_ids = parse_moon_spec(planet_num, moon_tokens) if moon_tokens else None
    rings_raw = _get_env('rings')
    ring_names = [r.strip() for r in rings_raw.split(',') if r.strip()] if rings_raw else None
    blank_flag = _get_env('blank', '').lower()
    blank_disks = blank_flag in {'yes', 'y', 'true', '1'}
    ephem_s = _get_env('ephem', '0')
    ephem_value = ephem_s.split()[0] if ephem_s else '0'
    try:
        ephem_version = int(ephem_value)
    except ValueError:
        ephem_version = 0

    display = ViewerDisplayInfo(
        ephem_display=_get_env('ephem') or None,
        moons_display=_get_env('moons') or None,
        rings_display=_get_env('rings') or None,
    )
    return ViewerParams(
        planet_num=planet_num,
        time_str=time_str,
        fov_value=fov_value,
        fov_unit=fov_unit,
        center=center,
        observer=observer,
        ephem_version=ephem_version,
        moon_ids=moon_ids,
        ring_names=ring_names,
        blank_disks=blank_disks,
        display=display,
    )


def tracker_params_from_env() -> TrackerParams | None:
    """Build ``TrackerParams`` from CGI-style environment variables."""
    nplanet_s = _get_env('NPLANET')
    if not nplanet_s:
        return None
    try:
        planet_num = int(nplanet_s)
    except ValueError:
        return None
    start_time = _get_env('start')
    stop_time = _get_env('stop')
    if not start_time or not stop_time:
        return None
    interval_s = _get_env('interval', '1')
    try:
        interval = float(interval_s)
    except ValueError:
        interval = 1.0
    time_unit = _get_env('time_unit', 'hour')
    viewpoint = _get_env('viewpoint', 'observatory')
    observer = Observer(name="Earth's Center")
    if viewpoint == 'observatory':
        observer = Observer(name=_get_env('observatory', "Earth's Center"))
    elif viewpoint:
        observer = Observer(name=viewpoint)
    moon_tokens = _get_keys_env('moons')
    from ephemeris_tools.planets import parse_moon_spec

    moon_ids = parse_moon_spec(planet_num, moon_tokens) if moon_tokens else []
    rings_raw = _get_keys_env('rings')
    ring_names = [r.strip() for r in rings_raw if r.strip()] if rings_raw else None
    xrange_s = _get_env('xrange')
    try:
        xrange = float(xrange_s) if xrange_s else None
    except ValueError:
        xrange = None
    xunit = _get_env('xunit', 'arcsec')
    title = _get_env('title')
    ephem_s = _get_env('ephem', '0')
    ephem_value = ephem_s.split()[0] if ephem_s else '0'
    try:
        ephem_version = int(ephem_value)
    except ValueError:
        ephem_version = 0
    return TrackerParams(
        planet_num=planet_num,
        start_time=start_time,
        stop_time=stop_time,
        interval=interval,
        time_unit=time_unit,
        observer=observer,
        ephem_version=ephem_version,
        moon_ids=moon_ids,
        ring_names=ring_names,
        xrange=xrange,
        xunit=xunit,
        title=title,
    )
