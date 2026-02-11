"""Run specification: tool type and parameters (CLI/env compatible)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote

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

# Moon index → CGI form value used by FORTRAN tracker/ephemeris HTML forms.
# Format: "NNN Name (Xn)" where NNN = zero-padded index, X = planet letter.
_SATURN_MOON_CGI: dict[int, str] = {
    1: '001 Mimas (S1)',
    2: '002 Enceladus (S2)',
    3: '003 Tethys (S3)',
    4: '004 Dione (S4)',
    5: '005 Rhea (S5)',
    6: '006 Titan (S6)',
    7: '007 Hyperion (S7)',
    8: '008 Iapetus (S8)',
    9: '009 Phoebe (S9)',
    10: '010 Janus (S10)',
    11: '011 Epimetheus (S11)',
    12: '012 Helene (S12)',
    13: '013 Telesto (S13)',
    14: '014 Calypso (S14)',
    15: '015 Atlas (S15)',
    16: '016 Prometheus (S16)',
    17: '017 Pandora (S17)',
    18: '018 Pan (S18)',
    32: '032 Methone (S32)',
    33: '033 Pallene (S33)',
    34: '034 Polydeuces (S34)',
    35: '035 Daphnis (S35)',
    49: '049 Anthe (S49)',
    53: '053 Aegaeon (S53)',
}

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

    # Time range (ephemeris / tracker)
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

    # Multi-value params (ephemeris / tracker)
    for col in p.get('columns') or []:
        pairs.append(('columns', str(col)))
    for col in p.get('mooncols') or []:
        pairs.append(('mooncols', str(col)))
    # FORTRAN moons: CGI format "NNN Name (Xn)" from HTML form.
    planet_num = int(p.get('planet', 6))
    moon_cgi = _SATURN_MOON_CGI if planet_num == 6 else {}
    for moon in p.get('moons') or []:
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
        # Tracker rings: each option as a separate "rings" parameter.
        if p.get('rings'):
            for r in p['rings'] if isinstance(p['rings'], list) else [p['rings']]:
                pairs.append(('rings', str(r)))
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
        if 'center_ra' in p:
            pairs.append(('center_ra', str(p['center_ra'])))
        if 'center_dec' in p:
            pairs.append(('center_dec', str(p['center_dec'])))

        # Rings
        if 'rings' in p and p['rings'] is not None:
            r = p['rings']
            rings_str = ' '.join(str(x) for x in (r if isinstance(r, list) else [r]))
            pairs.append(('rings', rings_str))

        # Required params that crash FORTRAN if missing (sent by CGI form)
        pairs.append(('labels', str(p.get('labels', 'Small (6 points)'))))
        pairs.append(('moonpts', str(p.get('moonpts', '3'))))
        pairs.append(('blank', str(p.get('blank', 'No'))))
        pairs.append(('opacity', str(p.get('opacity', 'Transparent'))))
        pairs.append(('peris', str(p.get('peris', 'None'))))
        pairs.append(('peripts', str(p.get('peripts', '4'))))
        pairs.append(('meridians', str(p.get('meridians', 'No'))))

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
            if p.get('rings'):
                args.append('--rings')
                args.extend(
                    str(r) for r in (p['rings'] if isinstance(p['rings'], list) else [p['rings']])
                )
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
