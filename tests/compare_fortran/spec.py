"""Run specification: tool type and parameters (CLI/env compatible)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote

from ephemeris_tools.planets import (
    JUPITER_CONFIG,
    MARS_CONFIG,
    NEPTUNE_CONFIG,
    PLUTO_CONFIG,
    SATURN_CONFIG,
    URANUS_CONFIG,
)
from ephemeris_tools.planets.base import PlanetConfig

# Maps Python CLI values → FORTRAN CGI form values.
# The FORTRAN parses these with string comparisons like
#   string .eq. 'degrees'   or   string(1:3) .eq. 'sec'
# so the values must match what the HTML <option> sends.
_FOV_UNIT_TO_FORTRAN: dict[str, str] = {
    'deg': 'degrees',
    'arcsec': 'seconds of arc',
    'arcmin': 'degrees',  # no arcmin in FORTRAN; handled via value conversion
    'millirad': 'milliradians',
    'microrad': 'microradians',
    'radii': 'radii',
    'km': 'kilometers',
}

_OBSERVATORY_TO_FORTRAN: dict[str, str] = {
    "Earth's Center": "Earth's center",  # FORTRAN checks first 5 chars only
}

# Planet number → PlanetConfig for building moon CGI maps.
_PLANET_CONFIGS: dict[int, PlanetConfig] = {
    4: MARS_CONFIG,
    5: JUPITER_CONFIG,
    6: SATURN_CONFIG,
    7: URANUS_CONFIG,
    8: NEPTUNE_CONFIG,
    9: PLUTO_CONFIG,
}

# Planet number → letter used in moon CGI format "(Xn)".
_PLANET_LETTER: dict[int, str] = {
    4: 'M',
    5: 'J',
    6: 'S',
    7: 'U',
    8: 'N',
    9: 'P',
}

# Valid FORTRAN viewer RING_SELECTION form values per planet (from VIEWER3_FORM_*.shtml).
# Uranus viewer rejects any other value (goto 9999); others accept any string but only
# these match the HTML radio options and set ring flags correctly.
VIEWER_VALID_RING_FORMS: dict[int, frozenset[str]] = {
    4: frozenset({'None', 'Phobos, Deimos'}),
    5: frozenset({'None', 'Main', 'Main & Gossamer'}),
    6: frozenset({'A,B,C', 'A,B,C,F', 'A,B,C,F,E', 'A,B,C,F,G,E'}),
    7: frozenset(
        {
            'Alpha, Beta, Eta, Gamma, Delta, Epsilon',
            'Nine major rings',
            'All inner rings',
            'All rings',
        }
    ),
    8: frozenset(
        {
            'LeVerrier, Adams',
            'LeVerrier, Arago, Adams',
            'Galle, LeVerrier, Arago, Adams',
        }
    ),
    9: frozenset(
        {
            'None',
            'Charon',
            'Charon, Nix, Hydra',
            'Charon, Styx, Nix, Kerberos, Hydra',
            'Nix, Hydra',
            'Styx, Nix, Kerberos, Hydra',
        }
    ),
}

# Planet number → default viewer ring selection (FORM form "checked" value).
# FORTRAN viewer requires a non-empty RING_SELECTION; use these when user omits --rings.
VIEWER_DEFAULT_RINGS: dict[int, str] = {
    4: 'Phobos, Deimos',
    5: 'Main',
    6: 'A,B,C',
    7: 'Nine major rings',
    8: 'LeVerrier, Adams',
    9: 'None',
}

# Planet number → (ring option code → viewer form value).
# Python --rings accepts names/codes (params.RING_NAME_TO_CODE); viewer FORTRAN expects
# form strings. This maps parse_ring_spec() output to a valid VIEWER_VALID_RING_FORMS value.
VIEWER_RING_CODE_TO_FORM: dict[int, dict[int, str]] = {
    5: {51: 'Main', 52: 'Main & Gossamer'},
    6: {61: 'A,B,C', 62: 'A,B,C,F,E', 63: 'A,B,C,F,G,E'},
    7: {71: 'Alpha, Beta, Eta, Gamma, Delta, Epsilon'},
    8: {81: 'LeVerrier, Adams'},
}


def _build_moon_cgi_map(planet_num: int) -> dict[int, str]:
    """Build moon index → CGI form value for a planet. Format: "NNN Name (Xn)"."""
    cfg = _PLANET_CONFIGS.get(planet_num)
    if cfg is None:
        return {}
    letter = _PLANET_LETTER.get(planet_num, '?')
    out: dict[int, str] = {}
    for moon in cfg.moons:
        if moon.id == cfg.planet_id:
            continue
        idx = moon.id % 100
        out[idx] = f'{idx:03d} {moon.name} ({letter}{idx})'
    return out


# Moon index → CGI form value per planet (FORTRAN tracker/ephemeris HTML form format).
_MOON_CGI_BY_PLANET: dict[int, dict[int, str]] = {p: _build_moon_cgi_map(p) for p in range(4, 10)}

# Column ID → CGI description template; use {planet} for planet-specific columns.
_COLUMN_CGI_TEMPLATES: dict[int, str] = {
    1: '001 Modified Julian Date',
    2: '002 Year, Month, Day, Hour, Minute',
    3: '003 Year, Month, Day, Hour, Minute, Second',
    4: '004 Year, DOY, Hour, Minute',
    5: '005 Year, DOY, Hour, Minute, Second',
    6: '006 Observer-{planet} distance',
    7: '007 Sun-{planet} distance',
    8: '008 {planet} phase angle',
    9: '009 Ring plane opening angle to observer',
    10: '010 Ring plane opening angle to Sun',
    11: '011 Sub-observer inertial longitude',
    12: '012 Sub-solar inertial longitude',
    13: '013 Sub-observer latitude & rotating longitude',
    14: '014 Sub-solar latitude & rotating longitude',
    15: '015 {planet} RA & Dec',
    16: '016 Earth RA & Dec',
    17: '017 Sun RA & Dec',
    18: '018 {planet} projected equatorial radius',
    19: '019 {planet} projected equatorial radius',
    20: '020 Lunar phase angle',
    21: '021 Sun-{planet} sky separation angle',
    22: '022 Lunar-{planet} sky separation angle',
}

# Moon column ID → CGI form value (ephemeris HTML form).
_MOONCOL_CGI: dict[int, str] = {
    1: '001 Observer-moon distance',
    2: '002 Moon phase angle',
    3: '003 Sub-observer latitude & rotating longitude',
    4: '004 Sub-solar latitude & rotating longitude',
    5: '005 RA & Dec',
    6: '006 Offset RA & Dec from the moon',
    7: '007 Offset RA & Dec from the moon',
    8: '008 Orbital longitude relative to observer',
    9: '009 Orbit plane opening angle to observer',
}

# Tracker ring option code → CGI form value (TRACKER3_FORM.shtml).
_TRACKER_RING_CGI: dict[int, str] = {
    51: '051 Main Ring',
    52: '052 Gossamer Rings',
    61: '061 Main Rings',
    62: '062 G Ring',
    63: '063 E Ring',
    71: '071 Epsilon Ring',
    81: '081 Adams Ring',
}


def _column_cgi_value(col_id: int, planet_name: str) -> str:
    """Return CGI form value for a column ID; substitute planet name where needed."""
    tpl = _COLUMN_CGI_TEMPLATES.get(col_id)
    if tpl is None:
        return str(col_id)
    return tpl.format(planet=planet_name)


# Default tracker moons (8 classical Saturn moons).
DEFAULT_TRACKER_MOONS_SATURN: list[int] = [1, 2, 3, 4, 5, 6, 7, 8]

# Planet number → name used by viewer FORTRAN binaries (PLANET_NAME parameter).
PLANET_NAMES: dict[int, str] = {
    4: 'Mars',
    5: 'Jupiter',
    6: 'Saturn',
    7: 'Uranus',
    8: 'Neptune',
    9: 'Pluto',
}

# Planet number → ephemeris kernel description (chars 5+ of web "ephem" value).
# FORTRAN reads first 3 chars as integer, prints string(5:) in "Ephemeris:" header.
# Values match web/tools/EPHEMERIS_INFO.shtml hidden inputs.
EPHEM_DESCRIPTIONS_BY_PLANET: dict[int, str] = {
    4: 'MAR097 + DE440',
    5: 'JUP365 + DE440',
    6: 'SAT415 + SAT441 + DE440',
    7: 'URA111 + URA115 + DE440',
    8: 'NEP095 + NEP097 + NEP101 + DE440',
    9: 'PLU058 + DE440',
}


def _fortran_fov(fov: float, fov_unit: str) -> tuple[str, str]:
    """Return (fov_value, fov_unit) translated for FORTRAN QUERY_STRING.

    For arcmin we convert to degrees since FORTRAN has no arcmin option.
    """
    if fov_unit == 'arcmin':
        return (str(fov / 60.0), 'degrees')
    return (str(fov), _FOV_UNIT_TO_FORTRAN.get(fov_unit, fov_unit))


def _query_pairs(p: dict[str, Any], tool: str) -> list[tuple[str, str]]:
    """Build (name, value) pairs for QUERY_STRING (CGI GET).

    FORTRAN reads form params from QUERY_STRING via getcgivars(), not
    from individual env vars. Values are translated to match what the
    original HTML forms submit.
    """
    pairs: list[tuple[str, str]] = []

    # Time range (ephemeris / tracker only; viewer uses single 'time' param)
    if tool in ('ephemeris', 'tracker'):
        if p.get('start'):
            pairs.append(('start', str(p['start'])))
        if p.get('stop'):
            pairs.append(('stop', str(p['stop'])))
        if 'interval' in p:
            pairs.append(('interval', str(p['interval'])))
        if 'time_unit' in p:
            pairs.append(('time_unit', str(p['time_unit'])))

    # Ephemeris selection: web format "NNN DESCRIPTION" (FORTRAN (i3) + header string(5:)).
    if 'ephem' in p:
        version = int(p['ephem'])
        planet = int(p.get('planet', 6))
        desc = EPHEM_DESCRIPTIONS_BY_PLANET.get(planet, 'DE440')
        pairs.append(('ephem', f'{version:03d} {desc}'))

    # Viewpoint / observatory
    if 'viewpoint' in p:
        pairs.append(('viewpoint', str(p['viewpoint'])))
    if 'observatory' in p:
        obs = str(p['observatory'])
        obs = _OBSERVATORY_TO_FORTRAN.get(obs, obs)
        pairs.append(('observatory', obs))
    if 'latitude' in p and p['latitude'] is not None:
        pairs.append(('latitude', str(p['latitude'])))
    if 'longitude' in p and p['longitude'] is not None:
        pairs.append(('longitude', str(p['longitude'])))
    if 'lon_dir' in p:
        pairs.append(('lon_dir', str(p['lon_dir'])))
    if 'altitude' in p and p['altitude'] is not None:
        pairs.append(('altitude', str(p['altitude'])))
    if 'sc_trajectory' in p:
        pairs.append(('sc_trajectory', str(p['sc_trajectory'])))

    # Multi-value params: use CGI format "NNN Description" for FORTRAN header output.
    planet_num = int(p.get('planet', 6))
    planet_name = PLANET_NAMES.get(planet_num, 'Saturn')
    for col in p.get('columns') or []:
        col_int = int(col)
        pairs.append(('columns', _column_cgi_value(col_int, planet_name)))
    for col in p.get('mooncols') or []:
        col_int = int(col)
        pairs.append(('mooncols', _MOONCOL_CGI.get(col_int, str(col_int))))
    # FORTRAN moons: CGI "NNN Name (Xn)". Viewer = single cutoff; tracker/ephemeris = list.
    moon_list = p.get('moons') or []
    moon_cgi = _MOON_CGI_BY_PLANET.get(planet_num, {})
    if tool == 'viewer' and moon_list:
        # Viewer: single moons= entry with highest moon index as cutoff.
        cutoff = max(int(m) for m in moon_list)
        cgi_val = moon_cgi.get(cutoff, f'{cutoff:03d}')
        pairs.append(('moons', cgi_val))
    else:
        for moon in moon_list:
            moon_int = int(moon)
            cgi_val = moon_cgi.get(moon_int, str(moon_int))
            pairs.append(('moons', cgi_val))

    # Tracker-specific params
    if tool == 'tracker':
        if 'xrange' in p and p['xrange'] is not None:
            pairs.append(('xrange', str(p['xrange'])))
        else:
            # Default xrange: 180 arcsec for Saturn
            pairs.append(('xrange', '180'))
        if p.get('xunit'):
            pairs.append(('xunit', str(p['xunit'])))
        else:
            pairs.append(('xunit', 'arcsec'))
        # Tracker rings: CGI format "NNN Description" per option.
        if p.get('rings'):
            for r in p['rings'] if isinstance(p['rings'], list) else [p['rings']]:
                r_int = int(r)
                pairs.append(('rings', _TRACKER_RING_CGI.get(r_int, str(r_int))))
        if p.get('title'):
            pairs.append(('title', str(p['title'])))

    # Viewer-specific params
    if tool == 'viewer':
        if p.get('time'):
            pairs.append(('time', str(p['time'])))

        # FOV: translate unit to match FORTRAN CGI form values
        raw_fov = float(p['fov']) if 'fov' in p else 1.0
        raw_unit = str(p.get('fov_unit', 'degrees'))
        fov_val, fov_unit = _fortran_fov(raw_fov, raw_unit)
        pairs.append(('fov', fov_val))
        pairs.append(('fov_unit', fov_unit))

        # Center: default center_body to planet name when center=body
        center = str(p.get('center', 'body'))
        pairs.append(('center', center))
        if center == 'body':
            cb = str(p.get('center_body', ''))
            if not cb:
                planet_num = int(p.get('planet', 6))
                cb = PLANET_NAMES.get(planet_num, 'Saturn')
            pairs.append(('center_body', cb))
        if p.get('center_ansa'):
            pairs.append(('center_ansa', str(p['center_ansa'])))
        if p.get('center_ew'):
            pairs.append(('center_ew', str(p['center_ew'])))
        if 'center_ra' in p and p['center_ra'] not in (None, ''):
            pairs.append(('center_ra', str(p['center_ra'])))
        if p.get('center_ra_type'):
            pairs.append(('center_ra_type', str(p['center_ra_type'])))
        if 'center_dec' in p and p['center_dec'] not in (None, ''):
            pairs.append(('center_dec', str(p['center_dec'])))
        if p.get('center_star'):
            pairs.append(('center_star', str(p['center_star'])))

        # Rings: FORTRAN expects form value strings (e.g. "Nine major rings"), not option codes.
        planet_num = int(p.get('planet', 6))
        if 'rings' in p and p['rings'] is not None:
            r = p['rings']
            if isinstance(r, list) and r and all(isinstance(x, int) for x in r):
                code_to_form = VIEWER_RING_CODE_TO_FORM.get(planet_num, {})
                form_vals = [code_to_form.get(c) for c in r]
                if all(form_vals) and len(set(form_vals)) == 1:
                    rings_str = form_vals[0] or VIEWER_DEFAULT_RINGS.get(planet_num, 'None')
                else:
                    rings_str = VIEWER_DEFAULT_RINGS.get(planet_num, 'None')
            elif isinstance(r, str):
                rings_str = r
            else:
                rings_str = ' '.join(str(x) for x in (r if isinstance(r, list) else [r]))
            pairs.append(('rings', rings_str))
        else:
            pairs.append(('rings', VIEWER_DEFAULT_RINGS.get(planet_num, 'None')))
        if 'torus' in p and p['torus'] is not None:
            pairs.append(('torus', str(p['torus'])))
        if 'torus_inc' in p and p['torus_inc'] is not None:
            pairs.append(('torus_inc', str(p['torus_inc'])))
        if 'torus_rad' in p and p['torus_rad'] is not None:
            pairs.append(('torus_rad', str(p['torus_rad'])))

        # Required params that crash FORTRAN if missing (sent by CGI form)
        pairs.append(('labels', str(p.get('labels', 'Small (6 points)'))))
        pairs.append(('moonpts', str(p.get('moonpts', '3'))))
        pairs.append(('blank', str(p.get('blank', 'No'))))
        pairs.append(('opacity', str(p.get('opacity', 'Transparent'))))
        pairs.append(('peris', str(p.get('peris', 'None'))))
        pairs.append(('peripts', str(p.get('peripts', '4'))))
        pairs.append(('meridians', str(p.get('meridians', 'No'))))
        if 'arcmodel' in p and p['arcmodel'] is not None and str(p['arcmodel']).strip() != '':
            pairs.append(('arcmodel', str(p['arcmodel'])))
        if 'arcpts' in p and p['arcpts'] is not None:
            pairs.append(('arcpts', str(p['arcpts'])))
        if 'additional' in p and p['additional'] is not None:
            pairs.append(('additional', str(p['additional'])))
        if 'extra_ra' in p and p['extra_ra'] is not None:
            pairs.append(('extra_ra', str(p['extra_ra'])))
        if 'extra_ra_type' in p and p['extra_ra_type'] is not None:
            pairs.append(('extra_ra_type', str(p['extra_ra_type'])))
        if 'extra_dec' in p and p['extra_dec'] is not None:
            pairs.append(('extra_dec', str(p['extra_dec'])))
        if 'extra_name' in p and p['extra_name'] is not None:
            pairs.append(('extra_name', str(p['extra_name'])))
        for other in p.get('other') or []:
            pairs.append(('other', str(other)))

        if 'title' in p:
            pairs.append(('title', str(p['title'])))

    return pairs


@dataclass
class RunSpec:
    """Single run specification for ephemeris, tracker, or viewer.

    Parameters match CGI/env names and Python CLI. Used to drive both
    FORTRAN (via environment) and Python (via CLI or env).
    """

    tool: str  # "ephemeris" | "tracker" | "viewer"
    params: dict[str, Any] = field(default_factory=dict)

    def env_for_fortran(
        self,
        table_path: str | None = None,
        ps_path: str | None = None,
    ) -> dict[str, str]:
        """Build environment dict for FORTRAN (CGI-style).

        FORTRAN reads form parameters from QUERY_STRING (parsed when
        REQUEST_METHOD=GET via getcgivars()). Only a few variables are
        read directly from the environment via GETENV / WWW_GetEnv:
        NPLANET, EPHEM_FILE, TRACKER_POSTFILE, TRACKER_TEXTFILE,
        VIEWER_POSTFILE, VIEWER_TEXTFILE.
        """
        env: dict[str, str] = {}
        p = self.params

        # Required by getcgivars(): REQUEST_METHOD=GET and QUERY_STRING.
        env['REQUEST_METHOD'] = 'GET'
        if p.get('query_string'):
            env['QUERY_STRING'] = str(p['query_string'])
        else:
            pairs = _query_pairs(p, self.tool)
            env['QUERY_STRING'] = '&'.join(
                f'{quote(name, safe="")}{""}={quote(value, safe="")}' for name, value in pairs
            )

        # Variables read via WWW_GetEnv (real env vars, not QUERY_STRING).
        if 'planet' in p:
            env['NPLANET'] = str(int(p['planet']))
        if self.tool == 'ephemeris' and table_path:
            env['EPHEM_FILE'] = table_path
        if self.tool == 'tracker':
            if ps_path:
                env['TRACKER_POSTFILE'] = ps_path
            if table_path:
                env['TRACKER_TEXTFILE'] = table_path
        if self.tool == 'viewer':
            if ps_path:
                env['VIEWER_POSTFILE'] = ps_path
            if table_path:
                env['VIEWER_TEXTFILE'] = table_path

        return env

    def cli_args_for_python(self) -> list[str]:
        """Build CLI argument list for ephemeris-tools.

        Uses the original Python CLI values (not FORTRAN translations).
        """
        args = [self.tool]
        p = self.params
        if 'planet' in p:
            args.extend(['--planet', str(int(p['planet']))])
        if self.tool in ('ephemeris', 'tracker') and 'start' in p and p['start']:
            args.extend(['--start', str(p['start'])])
        if self.tool in ('ephemeris', 'tracker') and 'stop' in p and p['stop']:
            args.extend(['--stop', str(p['stop'])])
        if self.tool in ('ephemeris', 'tracker'):
            if 'interval' in p:
                args.extend(['--interval', str(p['interval'])])
            if 'time_unit' in p:
                args.extend(['--time-unit', str(p['time_unit'])])
            if self.tool == 'ephemeris' and 'columns' in p and p['columns']:
                args.append('--columns')
                args.extend(str(c) for c in p['columns'])
            if self.tool == 'ephemeris' and 'mooncols' in p and p['mooncols']:
                args.append('--mooncols')
                args.extend(str(c) for c in p['mooncols'])
        if p.get('moons'):
            args.append('--moons')
            args.extend(str(m) for m in p['moons'])
        if 'ephem' in p:
            args.extend(['--ephem', str(p['ephem'])])
        if 'viewpoint' in p:
            args.extend(['--viewpoint', str(p['viewpoint'])])
        if 'observatory' in p:
            args.extend(['--observatory', str(p['observatory'])])
        if 'latitude' in p and p['latitude'] is not None:
            args.extend(['--latitude', str(p['latitude'])])
        if 'longitude' in p and p['longitude'] is not None:
            args.extend(['--longitude', str(p['longitude'])])
        if 'lon_dir' in p:
            args.extend(['--lon-dir', str(p['lon_dir'])])
        if 'altitude' in p and p['altitude'] is not None:
            args.extend(['--altitude', str(p['altitude'])])
        if 'sc_trajectory' in p:
            args.extend(['--sc-trajectory', str(p['sc_trajectory'])])
        if self.tool == 'viewer':
            if p.get('time'):
                args.extend(['--time', str(p['time'])])
            if 'fov' in p:
                args.extend(['--fov', str(p['fov'])])
            if 'fov_unit' in p:
                args.extend(['--fov-unit', str(p['fov_unit'])])
            if 'center' in p:
                args.extend(['--center', str(p['center'])])
            if 'center_body' in p:
                args.extend(['--center-body', str(p['center_body'])])
            if p.get('center_ansa'):
                args.extend(['--center-ansa', str(p['center_ansa'])])
            if p.get('center_ew'):
                args.extend(['--center-ew', str(p['center_ew'])])
            if 'center_ra' in p and p['center_ra'] not in (None, ''):
                args.extend(['--center-ra', str(p['center_ra'])])
            if p.get('center_ra_type'):
                args.extend(['--center-ra-type', str(p['center_ra_type'])])
            if 'center_dec' in p and p['center_dec'] not in (None, ''):
                args.extend(['--center-dec', str(p['center_dec'])])
            if p.get('center_star'):
                args.extend(['--center-star', str(p['center_star'])])
            if p.get('rings'):
                args.append('--rings')
                args.extend(
                    str(r) for r in (p['rings'] if isinstance(p['rings'], list) else [p['rings']])
                )
            if 'torus' in p and p['torus'] is not None:
                args.extend(['--torus', str(p['torus'])])
            if 'torus_inc' in p and p['torus_inc'] is not None:
                args.extend(['--torus-inc', str(p['torus_inc'])])
            if 'torus_rad' in p and p['torus_rad'] is not None:
                args.extend(['--torus-rad', str(p['torus_rad'])])
            if 'additional' in p and p['additional'] is not None:
                args.extend(['--additional', str(p['additional'])])
            if 'extra_name' in p and p['extra_name'] is not None:
                args.extend(['--extra-name', str(p['extra_name'])])
            if 'extra_ra' in p and p['extra_ra'] is not None:
                args.extend(['--extra-ra', str(p['extra_ra'])])
            if 'extra_ra_type' in p and p['extra_ra_type'] is not None:
                args.extend(['--extra-ra-type', str(p['extra_ra_type'])])
            if 'extra_dec' in p and p['extra_dec'] is not None:
                args.extend(['--extra-dec', str(p['extra_dec'])])
            if p.get('other'):
                args.append('--other')
                args.extend(str(o) for o in p['other'])
            if 'labels' in p and p['labels'] is not None:
                args.extend(['--labels', str(p['labels'])])
            if 'moonpts' in p and p['moonpts'] is not None:
                args.extend(['--moonpts', str(p['moonpts'])])
            if 'blank' in p and p['blank'] is not None:
                args.extend(['--blank', str(p['blank'])])
            if 'opacity' in p and p['opacity'] is not None:
                args.extend(['--opacity', str(p['opacity'])])
            if 'peris' in p and p['peris'] is not None:
                args.extend(['--peris', str(p['peris'])])
            if 'peripts' in p and p['peripts'] is not None:
                args.extend(['--peripts', str(p['peripts'])])
            if 'meridians' in p and p['meridians'] is not None:
                args.extend(['--meridians', str(p['meridians'])])
            if 'arcmodel' in p and p['arcmodel'] is not None and str(p['arcmodel']).strip() != '':
                args.extend(['--arcmodel', str(p['arcmodel'])])
            if 'arcpts' in p and p['arcpts'] is not None:
                args.extend(['--arcpts', str(p['arcpts'])])
            if 'title' in p:
                args.extend(['--title', str(p['title'])])
        if self.tool == 'tracker' and 'rings' in p and p['rings']:
            args.append('--rings')
            args.extend(
                str(r) for r in (p['rings'] if isinstance(p['rings'], list) else [p['rings']])
            )
        if self.tool == 'tracker':
            if 'xrange' in p and p['xrange'] is not None:
                args.extend(['--xrange', str(p['xrange'])])
            if 'xunit' in p:
                args.extend(['--xunit', str(p['xunit'])])
        return args
