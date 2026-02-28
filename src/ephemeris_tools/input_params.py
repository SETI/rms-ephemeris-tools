"""Input Parameters section (port of FORTRAN Summarize request)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, TextIO

if TYPE_CHECKING:
    from argparse import Namespace

    from ephemeris_tools.params import EphemerisParams, TrackerParams, ViewerParams


def _strip_cgi_code(s: str | None) -> str:
    """Strip leading 'NNN ' (three digits + space) from CGI form value; return rest.

    None and empty strings are normalized to '' and returned as ''. For inputs
    shorter than 4 characters, or not starting with three decimal digits followed
    by a space, the stripped input is returned unchanged. If the string begins
    with a three-digit code plus space (e.g. "200 foo"), returns s[4:].lstrip()
    (e.g. "foo").

    Parameters:
        s: CGI form value (str or None). None and empty strings are accepted.

    Returns:
        str: The input with leading "NNN " removed and outer whitespace
        normalized; never None. Empty string for None or empty input.

    Raises:
        Nothing. Callers can rely on no exceptions for any input.
    """
    s = (s or '').strip()
    if len(s) >= 4 and s[:3].isdecimal() and s[3] == ' ':
        return s[4:].lstrip()
    return s


def _w(stream: TextIO, line: str) -> None:
    """Write a line to the stream (helper for input parameters section)."""
    stream.write(line + '\n')


def _html_escape_title(s: str) -> str:
    """Escape < and > for tracker Title line to match FORTRAN WWW_Lookup sanitization."""
    return s.replace('<', '&lt;').replace('>', '&gt;')


# Match FORTRAN ephemeris stdout: interval unit always plural (e.g. "1 hours").
_TIME_UNIT_PLURAL = {'hour': 'hours', 'day': 'days', 'min': 'minutes', 'sec': 'seconds'}

# Default RA unit when not specified by display or args (used for diagram center RA).
DEFAULT_RA_TYPE = 'degrees'


def write_input_parameters_ephemeris(stream: TextIO, params: EphemerisParams) -> None:
    """Write Input Parameters section for ephemeris (port of ephem3_xxx Summarize).

    Parameters:
        stream: Output text stream.
        params: Ephemeris parameters to summarize.
    """
    from ephemeris_tools.constants import (
        COL_DISPLAY_TEMPLATES,
        EPHEM_DESCRIPTIONS_BY_PLANET,
        MCOL_DISPLAY_BY_ID,
        PLANET_NUM_TO_NAME,
    )
    from ephemeris_tools.planets import get_moon_display_name

    _w(stream, 'Input Parameters')
    _w(stream, '----------------')
    _w(stream, ' ')

    # Tabulation parameters
    start = (params.start_time or ' ').strip() or ' '
    stop = (params.stop_time or ' ').strip() or ' '
    _w(stream, f'     Start time: {start}')
    _w(stream, f'      Stop time: {stop}')

    interval_s = str(params.interval).strip() if params.interval is not None else '1'
    try:
        interval_val = float(interval_s)
    except (TypeError, ValueError):
        interval_val = 1.0
    if interval_val == int(interval_val):
        interval_s = str(int(interval_val))
    time_unit = params.time_unit or 'hour'
    time_unit_display = _TIME_UNIT_PLURAL.get(time_unit, time_unit)
    _w(stream, f'       Interval: {interval_s} {time_unit_display}')

    if params.ephem_display and str(params.ephem_display).strip():
        ephem_s = _strip_cgi_code(params.ephem_display.strip())
        _w(stream, f'      Ephemeris: {ephem_s}')
    else:
        ephem_s = EPHEM_DESCRIPTIONS_BY_PLANET.get(params.planet_num, str(params.ephem_version))
        _w(stream, f'      Ephemeris: {ephem_s}')

    # Viewpoint
    if params.viewpoint == 'latlon' and (
        params.latitude_deg is not None or params.longitude_deg is not None
    ):
        lat = params.latitude_deg if params.latitude_deg is not None else ''
        _w(stream, f'      Viewpoint: Lat = {lat} (deg)')
        # FORTRAN prints raw CGI value (positive for west); Python stores negated for SPICE.
        lon_deg = params.longitude_deg
        if lon_deg is not None and (params.lon_dir or '').lower() == 'west':
            lon_deg = abs(lon_deg)
        lon = lon_deg if lon_deg is not None else ''
        _w(stream, f'                 Lon = {lon} (deg {params.lon_dir})')
        alt = params.altitude_m if params.altitude_m is not None else ''
        _w(stream, f'                 Alt = {alt} (m)')
    else:
        vp = (params.observatory or "Earth's center").strip()
        if len(vp) == 0:
            vp = "Earth's center"
        if params.sc_trajectory:
            vp = f'{vp} ({params.sc_trajectory})'
        _w(stream, f'      Viewpoint: {vp}')

    _w(stream, ' ')

    # General columns
    planet_name = PLANET_NUM_TO_NAME.get(params.planet_num, 'planet')
    if params.columns_display is not None and len(params.columns_display) > 0:
        for i, col_str in enumerate(params.columns_display):
            s = _strip_cgi_code(col_str)
            prefix = 'General columns: ' if i == 0 else '                 '
            _w(stream, f'{prefix}{s}')
    elif params.columns:
        for i, c in enumerate(params.columns):
            tpl = COL_DISPLAY_TEMPLATES.get(c)
            s = tpl.format(planet=planet_name) if tpl else str(c)
            prefix = 'General columns: ' if i == 0 else '                 '
            _w(stream, f'{prefix}{s}')
    else:
        _w(stream, 'General columns:')
    _w(stream, ' ')

    # Moon columns
    if params.mooncols_display is not None and len(params.mooncols_display) > 0:
        for i, m in enumerate(params.mooncols_display):
            s = _strip_cgi_code(m)
            prefix = '   Moon columns: ' if i == 0 else '                 '
            _w(stream, f'{prefix}{s}')
    elif params.mooncols:
        for i, c in enumerate(params.mooncols):
            s = MCOL_DISPLAY_BY_ID.get(c, str(c))
            prefix = '   Moon columns: ' if i == 0 else '                 '
            _w(stream, f'{prefix}{s}')
    else:
        _w(stream, '   Moon columns:')
    _w(stream, ' ')

    # Moon selection
    if params.moons_display is not None and len(params.moons_display) > 0:
        for i, m in enumerate(params.moons_display):
            s = _strip_cgi_code(m)
            prefix = ' Moon selection: ' if i == 0 else '                 '
            _w(stream, f'{prefix}{s}')
    elif params.moon_ids:
        for i, mid in enumerate(params.moon_ids):
            moon_name = get_moon_display_name(params.planet_num, mid)
            prefix = ' Moon selection: ' if i == 0 else '                 '
            _w(stream, f'{prefix}{moon_name or mid}')
    else:
        _w(stream, ' Moon selection:')
    _w(stream, ' ')


def write_input_parameters_tracker(stream: TextIO, args: Namespace | TrackerParams) -> None:
    """Write Input Parameters section for tracker (port of tracker3_xxx Summarize).

    Parameters:
        stream: Output text stream.
        args: Parsed CLI/namespace with start, stop, interval, viewpoint, etc.
    """
    _w(stream, 'Input Parameters')
    _w(stream, '----------------')
    _w(stream, ' ')

    _now = datetime.now(timezone.utc)
    _fallback_start = _now.strftime('%Y-%m-%d %H:%M')
    _fallback_stop = (_now + timedelta(days=1)).strftime('%Y-%m-%d %H:%M')
    start = (
        getattr(args, 'start', None) or getattr(args, 'start_time', None) or ' '
    ).strip() or _fallback_start
    stop = (
        getattr(args, 'stop', None) or getattr(args, 'stop_time', None) or ' '
    ).strip() or _fallback_stop
    _w(stream, f'     Start time: {start}')
    _w(stream, f'      Stop time: {stop}')

    interval = getattr(args, 'interval', 1.0)
    if interval is not None and interval == int(interval):
        interval_s = str(int(interval))
    else:
        interval_s = str(interval).strip() if interval is not None else '1'
    try:
        interval_val = float(interval_s)
    except (TypeError, ValueError):
        interval_val = 1.0
    if interval_val == int(interval_val):
        interval_s = str(int(interval_val))
    time_unit = getattr(args, 'time_unit', 'hour') or 'hour'
    time_unit_display = _TIME_UNIT_PLURAL.get(time_unit, time_unit)
    _w(stream, f'       Interval: {interval_s} {time_unit_display}')
    ephem_display = getattr(args, 'ephem_display', None)
    if ephem_display and str(ephem_display).strip():
        s = _strip_cgi_code(str(ephem_display))
        _w(stream, f'      Ephemeris: {s}')
    else:
        _w(stream, f'      Ephemeris: {getattr(args, "ephem", 0)}')

    # Viewpoint
    viewpoint = (getattr(args, 'viewpoint', None) or ' ').strip()
    observer_obj = getattr(args, 'observer', None)
    if observer_obj is not None:
        if observer_obj.name:
            _w(stream, f'      Viewpoint: {observer_obj.name}')
        elif observer_obj.latitude_deg is not None or observer_obj.longitude_deg is not None:
            _w(stream, f'      Viewpoint: Lat = {observer_obj.latitude_deg} (deg)')
            lon_display = observer_obj.longitude_deg
            lon_dir = (getattr(observer_obj, 'lon_dir', None) or 'east').strip().lower()
            if lon_display is not None and lon_dir == 'west':
                lon_display = abs(lon_display)
            _w(stream, f'                 Lon = {lon_display} (deg {lon_dir})')
            _w(stream, f'                 Alt = {observer_obj.altitude_m} (m)')
        else:
            _w(stream, "      Viewpoint: Earth's center")
    elif viewpoint == 'latlon':
        lat = getattr(args, 'latitude', None)
        _w(stream, f'      Viewpoint: Lat = {lat} (deg)')
        lon = getattr(args, 'longitude', None)
        lon_dir = getattr(args, 'lon_dir', 'east')
        _w(stream, f'                 Lon = {lon} (deg {lon_dir})')
        alt = getattr(args, 'altitude', None)
        _w(stream, f'                 Alt = {alt} (m)')
    elif viewpoint and getattr(args, 'observatory', None):
        vp = (getattr(args, 'observatory', None) or '').strip()
        sc = getattr(args, 'sc_trajectory', 0)
        if sc:
            vp = f'{vp} ({sc})'
        _w(stream, f'      Viewpoint: {vp}')
    else:
        _w(stream, "      Viewpoint: Earth's center")

    _w(stream, ' ')

    # Moon selection (FORTRAN: use display strings, strip leading "NNN " code)
    moons_display = getattr(args, 'moons_display', None)
    if moons_display and len(moons_display) > 0:
        for i, m in enumerate(moons_display):
            s = _strip_cgi_code(m)
            prefix = ' Moon selection: ' if i == 0 else '                 '
            _w(stream, f'{prefix}{s}')
    else:
        moons = getattr(args, 'moons', None) or getattr(args, 'moon_ids', None) or []
        if moons:
            for i, m in enumerate(moons):
                prefix = ' Moon selection: ' if i == 0 else '                 '
                _w(stream, f'{prefix}{m}')
        else:
            _w(stream, ' Moon selection:')
    _w(stream, ' ')

    # Ring selection (if not Mars)
    planet_value = getattr(args, 'planet_num', None) or getattr(args, 'planet', 6)
    planet = int(planet_value) if planet_value is not None else 6
    if planet != 4:
        rings_display = getattr(args, 'rings_display', None)
        if rings_display and len(rings_display) > 0:
            for i, r in enumerate(rings_display):
                s = _strip_cgi_code(r)
                prefix = ' Ring selection: ' if i == 0 else '                 '
                _w(stream, f'{prefix}{s}')
        else:
            rings = getattr(args, 'rings', None) or getattr(args, 'ring_names', None) or []
            if rings:
                for i, r in enumerate(rings):
                    s = _strip_cgi_code(r)
                    prefix = ' Ring selection: ' if i == 0 else '                 '
                    _w(stream, f'{prefix}{s}')
            else:
                _w(stream, ' Ring selection:')
        _w(stream, ' ')

    # Plot options (xrange as integer when whole; xunit matches FORTRAN raw CGI value)
    xrange_val = getattr(args, 'xrange', None)
    xunit = getattr(args, 'xunit', 'arcsec') or 'arcsec'
    if xrange_val is not None and xrange_val == int(xrange_val):
        xrange_s = str(int(xrange_val))
    else:
        xrange_s = (str(xrange_val).strip() if xrange_val is not None else ' ') or ' '
    # CLI uses normalized 'arcsec'|'radii'; CGI preserves raw (e.g. "degrees", "Uranus radii")
    if xunit in ('arcsec', 'radii'):
        xunit_display = f'{_PLANET_NAMES[planet]} radii' if xunit == 'radii' else 'arcsec'
    else:
        xunit_display = xunit
    _w(stream, f'     Plot scale: {xrange_s} {xunit_display}')

    # Title (empty -> ""). Escape < and > to match FORTRAN WWW_GetKey (WWW_Lookup sanitization).
    title = (getattr(args, 'title', None) or '').strip()
    _w(stream, f'          Title: "{_html_escape_title(title)}"')
    _w(stream, ' ')


_PLANET_NAMES = {4: 'Mars', 5: 'Jupiter', 6: 'Saturn', 7: 'Uranus', 8: 'Neptune', 9: 'Pluto'}


def write_input_parameters_viewer(stream: TextIO, args: Namespace | ViewerParams) -> None:
    """Write Input Parameters section for viewer (port of viewer3_* Summarize).

    Parameters:
        stream: Output text stream.
        args: Parsed CLI/namespace with time, fov, center, viewpoint, etc.
    """
    _w(stream, 'Input Parameters')
    _w(stream, '----------------')
    _w(stream, ' ')

    # Observation time (FORTRAN: 2 leading spaces)
    time_str = (
        getattr(args, 'time', None) or getattr(args, 'time_str', None) or ' '
    ).strip() or datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
    _w(stream, f'  Observation time: {time_str}')

    # Ephemeris (FORTRAN: 9 spaces; strip leading "NNN " version prefix like FORTRAN string(5:))
    display = getattr(args, 'display', None)
    ephem_display = getattr(display, 'ephem_display', None) or getattr(args, 'ephem_display', None)
    if ephem_display and str(ephem_display).strip():
        s = _strip_cgi_code(ephem_display)
        _w(stream, f'         Ephemeris: {s}')
    else:
        _w(stream, f'         Ephemeris: {getattr(args, "ephem", 0)}')

    # Field of view (FORTRAN: 5 spaces; integer when whole number, e.g. 5 not 5.0)
    fov = getattr(args, 'fov', None)
    if fov is None:
        fov = getattr(args, 'fov_value', 1.0)
    fov_unit = getattr(args, 'fov_unit', 'deg')
    fov_val = 1.0 if fov is None else fov
    try:
        fov_f = float(fov_val)
        fov_s = str(int(fov_f)) if fov_f == int(fov_f) else str(fov_f)
    except (TypeError, ValueError):
        fov_s = str(fov)
    if fov_s.startswith('0.') and len(fov_s) > 2:
        fov_s = '.' + fov_s[2:]
    _w(stream, f'     Field of view: {fov_s} ({fov_unit})')

    # Diagram center
    center_obj = getattr(args, 'center', None)
    center_ra = getattr(args, 'center_ra', 0.0)
    center_dec = getattr(args, 'center_dec', 0.0)
    if not hasattr(args, 'center_ra'):
        center_ra = getattr(center_obj, 'ra_deg', center_ra)
    if not hasattr(args, 'center_dec'):
        center_dec = getattr(center_obj, 'dec_deg', center_dec)
    mode = getattr(center_obj, 'mode', None)
    val = getattr(center_obj, 'center', center_obj) if center_obj is not None else None
    if isinstance(mode, str):
        center_mode = mode
    elif isinstance(val, str):
        center_mode = val
    else:
        center_mode = 'body'
    center = center_mode.strip().lower()
    center_body = (
        getattr(center_obj, 'body_name', None) or getattr(args, 'center_body', None) or ' '
    ).strip()
    if len(center_body) == 0:
        center_body = _PLANET_NAMES.get(getattr(args, 'planet', 6), 'Saturn')
    try:
        center_ra_num = float(center_ra)
    except (TypeError, ValueError):
        center_ra_num = 0.0
    try:
        center_dec_num = float(center_dec)
    except (TypeError, ValueError):
        center_dec_num = 0.0
    if center == 'ansa':
        center_ansa = (
            getattr(center_obj, 'ansa_name', None) or getattr(args, 'center_ansa', None) or 'A Ring'
        ).strip()
        center_ew = (
            getattr(center_obj, 'ansa_ew', None) or getattr(args, 'center_ew', None) or 'east'
        ).strip()
        _w(stream, f'    Diagram center: {center_ansa} {center_ew} ansa')
    elif center == 'j2000' or (center_ra_num != 0.0 or center_dec_num != 0.0):
        center_ra_display = getattr(display, 'center_ra_display', None)
        center_dec_display = getattr(display, 'center_dec_display', None)
        if center_ra_display is not None:
            center_ra_print = center_ra_display.strip()
        else:
            center_ra_print = str(center_ra)
        if center_dec_display is not None:
            center_dec_print = center_dec_display.strip()
        else:
            center_dec_print = str(center_dec)
        ra_type_display = getattr(display, 'center_ra_type_display', None)
        if ra_type_display is not None:
            ra_type = ra_type_display.strip()
        else:
            raw = getattr(args, 'center_ra_type', None)
            ra_type = (raw.strip() if raw is not None else '') or DEFAULT_RA_TYPE
        _w(stream, f'    Diagram center: RA  = {center_ra_print} {ra_type}')
        _w(stream, f'                    Dec = {center_dec_print}')
    elif center == 'star':
        center_star = (
            getattr(center_obj, 'star_name', None) or getattr(args, 'center_star', None) or ' '
        ).strip()
        _w(stream, f'    Diagram center: Star = {center_star}')
    else:
        _w(stream, f'    Diagram center: {center_body}')

    # Viewpoint (FORTRAN: 9 leading spaces)
    viewpoint = (getattr(args, 'viewpoint', None) or ' ').strip()
    observer_obj = getattr(args, 'observer', None)
    if observer_obj is not None:
        if observer_obj.name:
            _w(stream, f'         Viewpoint: {observer_obj.name}')
        elif observer_obj.latitude_deg is not None or observer_obj.longitude_deg is not None:
            _w(stream, f'         Viewpoint: Lat = {observer_obj.latitude_deg} (deg)')
            lon_display = observer_obj.longitude_deg
            lon_dir = (getattr(observer_obj, 'lon_dir', None) or 'east').strip().lower()
            if lon_display is not None and lon_dir == 'west':
                lon_display = abs(lon_display)
            _w(stream, f'                    Lon = {lon_display} (deg {lon_dir})')
            _w(stream, f'                    Alt = {observer_obj.altitude_m} (m)')
        else:
            _w(stream, "         Viewpoint: Earth's center")
    elif viewpoint == 'latlon':
        lat = getattr(args, 'latitude', None)
        _w(stream, f'         Viewpoint: Lat = {lat} (deg)')
        lon = getattr(args, 'longitude', None)
        lon_dir = getattr(args, 'lon_dir', 'east')
        _w(stream, f'                    Lon = {lon} (deg {lon_dir})')
        alt = getattr(args, 'altitude', None)
        _w(stream, f'                    Alt = {alt} (m)')
    elif viewpoint and (getattr(args, 'observatory', None) or '').strip():
        obs = (getattr(args, 'observatory', None) or '').strip()
        sc = getattr(args, 'sc_trajectory', 0)
        if sc:
            obs = f'{obs} ({sc})'
        _w(stream, f'         Viewpoint: {obs}')
    else:
        _w(stream, "         Viewpoint: Earth's center")

    # Moon selection (FORTRAN: 4 spaces; strip leading "NNN " like FORTRAN string(5:))
    moons_display = getattr(display, 'moons_display', None) or getattr(args, 'moons_display', None)
    if moons_display and str(moons_display).strip():
        parts = moons_display.strip().split(None, 1)
        moon_str = parts[1] if len(parts) == 2 and parts[0].isdigit() else moons_display.strip()
    else:
        moons = getattr(args, 'moons', None) or getattr(args, 'moon_ids', None) or []
        moon_str = ' '.join(str(m) for m in moons).strip() if moons else ' '
    _w(stream, f'    Moon selection: {moon_str}')
    moremoons = getattr(args, 'moremoons', None)
    if moremoons:
        _w(stream, f'                    {moremoons}')

    # Ring selection (FORTRAN: 4 spaces)
    rings_display = getattr(display, 'rings_display', None) or getattr(args, 'rings_display', None)
    if rings_display and str(rings_display).strip():
        ring_str = rings_display.strip()
    else:
        rings = getattr(args, 'rings', None) or getattr(args, 'ring_names', None) or []
        ring_str = ', '.join(str(r) for r in rings).strip() if rings else ' '
    _w(stream, f'    Ring selection: {ring_str}')

    # Io torus (Jupiter only; FORTRAN: 10 spaces before "Io torus:")
    if getattr(args, 'planet_num', None) == 5:
        if getattr(args, 'torus', False):
            torus_inc = getattr(args, 'torus_inc', 6.8)
            torus_rad = getattr(args, 'torus_rad', 422000)
            inc_str = f'{torus_inc:g}'
            rad_str = str(int(torus_rad)) if float(torus_rad).is_integer() else f'{torus_rad:g}'
            _w(stream, f'          Io torus: Inclination = {inc_str} deg; Radius = {rad_str} km')
        else:
            _w(stream, '          Io torus: No')

    # Arc model (Neptune only; FORTRAN Saturn does not have this line)
    arcmodel = (getattr(args, 'arcmodel', None) or '').strip()
    if arcmodel:
        _w(stream, f'       Arc model: {arcmodel}')

    # Standard stars (FORTRAN: 4 spaces)
    standard = (
        'Yes'
        if getattr(args, 'show_standard_stars', False)
        else (getattr(args, 'standard', None) or 'No')
    )
    if not isinstance(standard, str):
        standard = 'No'
    _w(stream, f'    Standard stars: {str(standard).strip()}')

    # Additional star (FORTRAN: 3 spaces)
    additional = getattr(display, 'additional_display', None)
    if additional is None:
        additional = getattr(args, 'additional', None)
    has_extra_star = getattr(args, 'extra_star', None) is not None
    if (
        additional is None
        or (isinstance(additional, str) and len(additional.strip()) == 0)
        or (isinstance(additional, str) and additional.strip().lower() in {'no', 'n', 'false', '0'})
    ) and not has_extra_star:
        _w(stream, '   Additional star: No')
    else:
        extra_name = (
            getattr(display, 'extra_name_display', None)
            or getattr(args, 'extra_name', None)
            or getattr(getattr(args, 'extra_star', None), 'name', None)
            or ' '
        ).strip()
        _w(stream, f'   Additional star: {extra_name}')
        extra_ra = (
            getattr(display, 'extra_ra_display', None) or getattr(args, 'extra_ra', None) or ' '
        ).strip()
        extra_ra_type = (
            getattr(display, 'extra_ra_type_display', None)
            or getattr(args, 'extra_ra_type', None)
            or 'hours'
        ).strip()
        _w(stream, f'                    RA  = {extra_ra} {extra_ra_type}')
        extra_dec = (
            getattr(display, 'extra_dec_display', None) or getattr(args, 'extra_dec', None) or ' '
        ).strip()
        _w(stream, f'                    Dec = {extra_dec}')

    # Other bodies (FORTRAN: 6 spaces)
    other = getattr(args, 'other_bodies', None) or getattr(args, 'other', None) or []
    if len(other) == 0:
        _w(stream, '      Other bodies: None')
    else:
        other_list = other if isinstance(other, (list, tuple)) else [other]
        for i, o in enumerate(other_list):
            prefix = '      Other bodies: ' if i == 0 else '                    '
            _w(stream, f'{prefix}{o}')

    # Title (FORTRAN: 13 spaces). Escape < and > to match FORTRAN WWW_GetKey sanitization.
    title = (getattr(args, 'title', None) or '').strip()
    _w(stream, f'             Title: "{_html_escape_title(title)}"')

    # Moon labels (FORTRAN: 7 spaces)
    labels = (getattr(args, 'labels', None) or 'Small (6 points)').strip()
    _w(stream, f'       Moon labels: {labels}')

    # Moon enlargement (FORTRAN: 2 spaces; integer when whole number)
    moonpts_display = getattr(display, 'moonpts_display', None)
    if moonpts_display is not None:
        moonpts = moonpts_display.strip()
    else:
        moonpts_val = getattr(args, 'moonpts', None) or 0
        try:
            fval = float(moonpts_val)
            moonpts = str(int(fval)) if fval == int(fval) else str(moonpts_val)
        except (TypeError, ValueError):
            moonpts = str(moonpts_val).strip()
    _w(stream, f'  Moon enlargement: {moonpts} (points)')

    # Blank disks (FORTRAN: 7 spaces)
    blank_display = getattr(display, 'blank_display', None)
    if blank_display is not None:
        blank = blank_display.strip()
    else:
        blank = (getattr(args, 'blank', None) or 'No').strip()
    _w(stream, f'       Blank disks: {blank}')

    # Ring plot type (Saturn only); pericenter markers and marker size (Saturn and Uranus).
    planet_num = getattr(args, 'planet_num', None)
    rings_list = getattr(args, 'ring_names', None) or getattr(args, 'rings', None) or []
    if planet_num == 6 and rings_list:
        opacity = (getattr(args, 'opacity', None) or '').strip()
        _w(stream, f'    Ring plot type: {opacity or "Transparent"}')
    if planet_num in (6, 7) and rings_list:
        peris = (getattr(args, 'peris', None) or '').strip()
        _w(stream, f'Pericenter markers: {peris or "None"}')
        peripts_val = getattr(args, 'peripts', None)
        try:
            if peripts_val is None:
                peripts_str = '4'
            else:
                p = float(peripts_val)
                peripts_str = str(int(p)) if p == int(p) else str(p)
        except (TypeError, ValueError):
            peripts_str = '4'
        _w(stream, f'       Marker size: {peripts_str} (points)')
    if planet_num == 8:
        arcpts_val = getattr(args, 'arcpts', None)
        try:
            if arcpts_val is None:
                arcpts_str = ''
            else:
                a = float(arcpts_val)
                arcpts_str = str(int(a)) if a == int(a) else str(a)
        except (TypeError, ValueError):
            arcpts_str = str(arcpts_val).strip() if arcpts_val is not None else ''
        _w(stream, f'      Arc weight: {arcpts_str} (points)')

    # Prime meridians (FORTRAN: 3 spaces)
    meridians_display = getattr(display, 'meridians_display', None)
    if meridians_display is not None:
        meridians = meridians_display.strip()
    else:
        meridians_raw = getattr(args, 'meridians', None)
        if isinstance(meridians_raw, bool):
            meridians = 'Yes' if meridians_raw else 'No'
        else:
            meridians = (meridians_raw or 'Yes').strip()
    _w(stream, f'   Prime meridians: {meridians}')

    _w(stream, ' ')
