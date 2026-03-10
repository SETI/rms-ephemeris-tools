"""Input Parameters section (port of FORTRAN Summarize request)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, TextIO

from ephemeris_tools.constants import (
    COL_DISPLAY_TEMPLATES,
    EPHEM_DESCRIPTIONS_BY_PLANET,
    MCOL_DISPLAY_BY_ID,
    PLANET_NUM_TO_NAME,
)
from ephemeris_tools.planets import get_moon_display_name

if TYPE_CHECKING:
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


def write_input_parameters_tracker(stream: TextIO, params: TrackerParams) -> None:
    """Write Input Parameters section for tracker (port of tracker3_xxx Summarize).

    Parameters:
        stream: Output text stream.
        params: Tracker parameters (from CLI or CGI).
    """
    _w(stream, 'Input Parameters')
    _w(stream, '----------------')
    _w(stream, ' ')

    _now = datetime.now(timezone.utc)
    _fallback_start = _now.strftime('%Y-%m-%d %H:%M')
    _fallback_stop = (_now + timedelta(days=1)).strftime('%Y-%m-%d %H:%M')
    start = (params.start_time or ' ').strip() or _fallback_start
    stop = (params.stop_time or ' ').strip() or _fallback_stop
    _w(stream, f'     Start time: {start}')
    _w(stream, f'      Stop time: {stop}')

    interval = params.interval
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
    time_unit = params.time_unit or 'hour'
    time_unit_display = _TIME_UNIT_PLURAL.get(time_unit, time_unit)
    _w(stream, f'       Interval: {interval_s} {time_unit_display}')
    ephem_display = params.ephem_display
    if ephem_display and str(ephem_display).strip():
        s = _strip_cgi_code(str(ephem_display))
        _w(stream, f'      Ephemeris: {s}')
    else:
        _w(stream, f'      Ephemeris: {params.ephem_version}')

    # Viewpoint
    observer_obj = params.observer
    if observer_obj is not None:
        if observer_obj.name:
            _w(stream, f'      Viewpoint: {observer_obj.name}')
        elif observer_obj.latitude_deg is not None or observer_obj.longitude_deg is not None:
            _w(stream, f'      Viewpoint: Lat = {observer_obj.latitude_deg} (deg)')
            lon_display = observer_obj.longitude_deg
            lon_dir = (observer_obj.lon_dir or 'east').strip().lower()
            if lon_display is not None and lon_dir == 'west':
                lon_display = abs(lon_display)
            _w(stream, f'                 Lon = {lon_display} (deg {lon_dir})')
            _w(stream, f'                 Alt = {observer_obj.altitude_m} (m)')
        else:
            _w(stream, "      Viewpoint: Earth's center")
    else:
        _w(stream, "      Viewpoint: Earth's center")

    _w(stream, ' ')

    # Moon selection (FORTRAN: use display strings, strip leading "NNN " code)
    moons_display = params.moons_display
    if moons_display and len(moons_display) > 0:
        for i, m in enumerate(moons_display):
            s = _strip_cgi_code(m)
            prefix = ' Moon selection: ' if i == 0 else '                 '
            _w(stream, f'{prefix}{s}')
    else:
        moons = params.moon_ids or []
        if moons:
            for i, mid in enumerate(moons):
                prefix = ' Moon selection: ' if i == 0 else '                 '
                _w(stream, f'{prefix}{mid}')
        else:
            _w(stream, ' Moon selection:')
    _w(stream, ' ')

    # Ring selection (if not Mars)
    planet = int(params.planet_num) if params.planet_num is not None else 6
    if planet != 4:
        rings_display = params.rings_display
        if rings_display and len(rings_display) > 0:
            for i, r in enumerate(rings_display):
                s = _strip_cgi_code(r)
                prefix = ' Ring selection: ' if i == 0 else '                 '
                _w(stream, f'{prefix}{s}')
        else:
            rings = params.ring_names or []
            if rings:
                for i, r in enumerate(rings):
                    s = _strip_cgi_code(r)
                    prefix = ' Ring selection: ' if i == 0 else '                 '
                    _w(stream, f'{prefix}{s}')
            else:
                _w(stream, ' Ring selection:')
        _w(stream, ' ')

    # Plot options (xrange as integer when whole; xunit matches FORTRAN raw CGI value)
    xrange_val = params.xrange
    xunit = params.xunit or 'arcsec'
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
    title = (params.title or '').strip()
    _w(stream, f'          Title: "{_html_escape_title(title)}"')
    _w(stream, ' ')


_PLANET_NAMES = {4: 'Mars', 5: 'Jupiter', 6: 'Saturn', 7: 'Uranus', 8: 'Neptune', 9: 'Pluto'}


def write_input_parameters_viewer(stream: TextIO, params: ViewerParams) -> None:
    """Write Input Parameters section for viewer (port of viewer3_* Summarize).

    Parameters:
        stream: Output text stream.
        params: Viewer parameters (from CLI or CGI).
    """
    _w(stream, 'Input Parameters')
    _w(stream, '----------------')
    _w(stream, ' ')

    # Observation time (FORTRAN: 2 leading spaces)
    time_str = (params.time_str or ' ').strip() or datetime.now(timezone.utc).strftime(
        '%Y-%m-%d %H:%M'
    )
    _w(stream, f'  Observation time: {time_str}')

    # Ephemeris (FORTRAN: 9 spaces; strip leading "NNN " version prefix like FORTRAN string(5:))
    display = params.display
    ephem_display = display.ephem_display if display else None
    if ephem_display and str(ephem_display).strip():
        s = _strip_cgi_code(ephem_display)
        _w(stream, f'         Ephemeris: {s}')
    else:
        _w(stream, f'         Ephemeris: {params.ephem_version}')

    # Field of view (FORTRAN: 5 spaces; integer when whole number, e.g. 5 not 5.0)
    fov_val = params.fov_value
    fov_unit = params.fov_unit or 'deg'
    try:
        fov_f = float(fov_val)
        fov_s = str(int(fov_f)) if fov_f == int(fov_f) else str(fov_f)
    except (TypeError, ValueError):
        fov_s = str(fov_val)
    if fov_s.startswith('0.') and len(fov_s) > 2:
        fov_s = '.' + fov_s[2:]
    _w(stream, f'     Field of view: {fov_s} ({fov_unit})')

    # Diagram center
    center_obj = params.center
    center_ra = center_obj.ra_deg if center_obj.ra_deg is not None else 0.0
    center_dec = center_obj.dec_deg if center_obj.dec_deg is not None else 0.0
    center = (center_obj.mode or 'body').strip().lower()
    center_body = (center_obj.body_name or ' ').strip()
    if len(center_body) == 0:
        center_body = _PLANET_NAMES.get(params.planet_num, 'Saturn')
    try:
        center_ra_num = float(center_ra)
    except (TypeError, ValueError):
        center_ra_num = 0.0
    try:
        center_dec_num = float(center_dec)
    except (TypeError, ValueError):
        center_dec_num = 0.0
    if center == 'ansa':
        center_ansa = (center_obj.ansa_name or 'A Ring').strip()
        center_ew = (center_obj.ansa_ew or 'east').strip()
        _w(stream, f'    Diagram center: {center_ansa} {center_ew} ansa')
    elif center == 'j2000' or (center_ra_num != 0.0 or center_dec_num != 0.0):
        center_ra_display = display.center_ra_display if display else None
        center_dec_display = display.center_dec_display if display else None
        if center_ra_display is not None:
            center_ra_print = center_ra_display.strip()
        else:
            center_ra_print = str(center_ra)
        if center_dec_display is not None:
            center_dec_print = center_dec_display.strip()
        else:
            center_dec_print = str(center_dec)
        ra_type_display = display.center_ra_type_display if display else None
        if ra_type_display is not None:
            ra_type = ra_type_display.strip()
        else:
            ra_type = DEFAULT_RA_TYPE
        _w(stream, f'    Diagram center: RA  = {center_ra_print} {ra_type}')
        _w(stream, f'                    Dec = {center_dec_print}')
    elif center == 'star':
        center_star = (center_obj.star_name or ' ').strip()
        _w(stream, f'    Diagram center: Star = {center_star}')
    else:
        _w(stream, f'    Diagram center: {center_body}')

    # Viewpoint (FORTRAN: 9 leading spaces)
    observer_obj = params.observer
    if observer_obj is not None:
        if observer_obj.name:
            _w(stream, f'         Viewpoint: {observer_obj.name}')
        elif observer_obj.latitude_deg is not None or observer_obj.longitude_deg is not None:
            _w(stream, f'         Viewpoint: Lat = {observer_obj.latitude_deg} (deg)')
            lon_display = observer_obj.longitude_deg
            lon_dir = (observer_obj.lon_dir or 'east').strip().lower()
            if lon_display is not None and lon_dir == 'west':
                lon_display = abs(lon_display)
            _w(stream, f'                    Lon = {lon_display} (deg {lon_dir})')
            _w(stream, f'                    Alt = {observer_obj.altitude_m} (m)')
        else:
            _w(stream, "         Viewpoint: Earth's center")
    else:
        _w(stream, "         Viewpoint: Earth's center")

    # Moon selection (FORTRAN: 4 spaces; strip leading "NNN " like FORTRAN string(5:))
    moons_display = display.moons_display if display else None
    if moons_display and str(moons_display).strip():
        parts = moons_display.strip().split(None, 1)
        moon_str = parts[1] if len(parts) == 2 and parts[0].isdigit() else moons_display.strip()
    else:
        moons = params.moon_ids or []
        moon_str = ' '.join(str(m) for m in moons).strip() if moons else ' '
    _w(stream, f'    Moon selection: {moon_str}')
    if params.moremoons:
        _w(stream, '                    Yes')

    # Ring selection (FORTRAN: 4 spaces)
    rings_display = display.rings_display if display else None
    if rings_display and str(rings_display).strip():
        ring_str = rings_display.strip()
    else:
        rings = params.ring_names or []
        ring_str = ', '.join(str(r) for r in rings).strip() if rings else ' '
    _w(stream, f'    Ring selection: {ring_str}')

    # Io torus (Jupiter only; FORTRAN: 10 spaces before "Io torus:")
    if params.planet_num == 5:
        if params.torus:
            inc_str = f'{params.torus_inc:g}'
            rad_str = (
                str(int(params.torus_rad))
                if float(params.torus_rad).is_integer()
                else f'{params.torus_rad:g}'
            )
            _w(stream, f'          Io torus: Inclination = {inc_str} deg; Radius = {rad_str} km')
        else:
            _w(stream, '          Io torus: No')

    # Arc model (Neptune only; FORTRAN Saturn does not have this line)
    arcmodel = (params.arcmodel or '').strip()
    if arcmodel:
        _w(stream, f'       Arc model: {arcmodel}')

    # Standard stars (FORTRAN: 4 spaces)
    standard = 'Yes' if params.show_standard_stars else 'No'
    _w(stream, f'    Standard stars: {standard}')

    # Additional star (FORTRAN: 3 spaces)
    additional = display.additional_display if display else None
    has_extra_star = params.extra_star is not None
    if (
        additional is None
        or (isinstance(additional, str) and len(additional.strip()) == 0)
        or (isinstance(additional, str) and additional.strip().lower() in {'no', 'n', 'false', '0'})
    ) and not has_extra_star:
        _w(stream, '   Additional star: No')
    else:
        extra_name = (
            (display.extra_name_display if display else None)
            or (params.extra_star.name if params.extra_star else None)
            or ' '
        ).strip()
        _w(stream, f'   Additional star: {extra_name}')
        extra_ra = (
            (display.extra_ra_display if display else None)
            or (params.extra_star.ra_deg if params.extra_star else None)
            or ' '
        )
        extra_ra = str(extra_ra).strip() if extra_ra is not None else ' '
        extra_ra_type = ((display.extra_ra_type_display if display else None) or 'hours').strip()
        _w(stream, f'                    RA  = {extra_ra} {extra_ra_type}')
        extra_dec = (
            (display.extra_dec_display if display else None)
            or (params.extra_star.dec_deg if params.extra_star else None)
            or ' '
        )
        extra_dec = str(extra_dec).strip() if extra_dec is not None else ' '
        _w(stream, f'                    Dec = {extra_dec}')

    # Other bodies (FORTRAN: 6 spaces)
    other = params.other_bodies or []
    if len(other) == 0:
        _w(stream, '      Other bodies: None')
    else:
        other_list = other if isinstance(other, (list, tuple)) else [other]
        for i, o in enumerate(other_list):
            prefix = '      Other bodies: ' if i == 0 else '                    '
            _w(stream, f'{prefix}{o}')

    # Title (FORTRAN: 13 spaces). Escape < and > to match FORTRAN WWW_GetKey sanitization.
    title = (params.title or '').strip()
    _w(stream, f'             Title: "{_html_escape_title(title)}"')

    # Moon labels (FORTRAN: 7 spaces)
    labels = (params.labels or 'Small (6 points)').strip()
    _w(stream, f'       Moon labels: {labels}')

    # Moon enlargement (FORTRAN: 2 spaces; integer when whole number)
    moonpts_display = display.moonpts_display if display else None
    if moonpts_display is not None:
        moonpts = moonpts_display.strip()
    else:
        moonpts_val = params.moonpts or 0
        try:
            fval = float(moonpts_val)
            moonpts = str(int(fval)) if fval == int(fval) else str(moonpts_val)
        except (TypeError, ValueError):
            moonpts = str(moonpts_val).strip()
    _w(stream, f'  Moon enlargement: {moonpts} (points)')

    # Blank disks (FORTRAN: 7 spaces)
    blank_display = display.blank_display if display else None
    if blank_display is not None:
        blank = blank_display.strip()
    else:
        blank = 'Yes' if params.blank_disks else 'No'
    _w(stream, f'       Blank disks: {blank}')

    # Ring plot type (Saturn only); pericenter markers and marker size (Saturn and Uranus).
    planet_num = params.planet_num
    rings_list = params.ring_names or []
    if planet_num == 6 and rings_list:
        opacity = (params.opacity or '').strip()
        _w(stream, f'    Ring plot type: {opacity or "Transparent"}')
    if planet_num in (6, 7) and rings_list:
        peris = (params.peris or '').strip()
        _w(stream, f'Pericenter markers: {peris or "None"}')
        peripts_val = params.peripts
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
        arcpts_val = params.arcpts
        try:
            if arcpts_val is None:
                arcpts_str = '4'
            else:
                a = float(arcpts_val)
                arcpts_str = str(int(a)) if a == int(a) else str(a)
        except (TypeError, ValueError):
            arcpts_str = str(arcpts_val).strip() if arcpts_val is not None else '4'
        _w(stream, f'      Arc weight: {arcpts_str} (points)')

    # Prime meridians (FORTRAN: 3 spaces)
    meridians_display = display.meridians_display if display else None
    if meridians_display is not None:
        meridians = meridians_display.strip()
    else:
        meridians = 'Yes' if params.meridians else 'No'
    _w(stream, f'   Prime meridians: {meridians}')

    _w(stream, ' ')
