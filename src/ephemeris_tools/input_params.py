"""Input Parameters section (port of FORTRAN Summarize request)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, TextIO

if TYPE_CHECKING:
    from argparse import Namespace

    from ephemeris_tools.params import EphemerisParams, TrackerParams, ViewerParams


def _w(stream: TextIO, line: str) -> None:
    """Write a line to the stream (helper for input parameters section)."""
    stream.write(line + '\n')


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
    _w(stream, f'       Interval: {interval_s} {params.time_unit}')
    _w(stream, f'      Ephemeris: {params.ephem_version}')

    # Viewpoint
    if params.viewpoint == 'latlon' and (
        params.latitude_deg is not None or params.longitude_deg is not None
    ):
        lat = params.latitude_deg if params.latitude_deg is not None else ''
        _w(stream, f'      Viewpoint: Lat = {lat} (deg)')
        lon = params.longitude_deg if params.longitude_deg is not None else ''
        _w(stream, f'                 Lon = {lon} (deg {params.lon_dir})')
        alt = params.altitude_m if params.altitude_m is not None else ''
        _w(stream, f'                 Alt = {alt} (m)')
    else:
        vp = (params.observatory or "Earth's Center").strip()
        if not vp:
            vp = "Earth's Center"
        if params.sc_trajectory:
            vp = f'{vp} ({params.sc_trajectory})'
        _w(stream, f'      Viewpoint: {vp}')

    _w(stream, ' ')

    # General columns
    if params.columns:
        for i, c in enumerate(params.columns):
            prefix = 'General columns: ' if i == 0 else '                 '
            _w(stream, f'{prefix}{c}')
    else:
        _w(stream, 'General columns:')
    _w(stream, ' ')

    # Moon columns
    if params.mooncols:
        for i, c in enumerate(params.mooncols):
            prefix = '   Moon columns: ' if i == 0 else '                 '
            _w(stream, f'{prefix}{c}')
    else:
        _w(stream, '   Moon columns:')
    _w(stream, ' ')

    # Moon selection
    if params.moon_ids:
        for i, mid in enumerate(params.moon_ids):
            prefix = ' Moon selection: ' if i == 0 else '                 '
            _w(stream, f'{prefix}{mid}')
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
    interval_s = str(interval).strip() if interval is not None else '1'
    time_unit = getattr(args, 'time_unit', 'hour')
    _w(stream, f'       Interval: {interval_s} {time_unit}')
    _w(stream, f'      Ephemeris: {getattr(args, "ephem", 0)}')

    # Viewpoint
    viewpoint = (getattr(args, 'viewpoint', None) or ' ').strip()
    observer_obj = getattr(args, 'observer', None)
    if observer_obj is not None:
        if observer_obj.name:
            _w(stream, f'      Viewpoint: {observer_obj.name}')
        elif observer_obj.latitude_deg is not None or observer_obj.longitude_deg is not None:
            _w(stream, f'      Viewpoint: Lat = {observer_obj.latitude_deg} (deg)')
            _w(stream, f'                 Lon = {observer_obj.longitude_deg} (deg east)')
            _w(stream, f'                 Alt = {observer_obj.altitude_m} (m)')
        else:
            _w(stream, "      Viewpoint: Earth's Center")
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
        _w(stream, "      Viewpoint: Earth's Center")

    _w(stream, ' ')

    # Moon selection
    moons = getattr(args, 'moons', None) or []
    if moons:
        for i, m in enumerate(moons):
            prefix = ' Moon selection: ' if i == 0 else '                 '
            _w(stream, f'{prefix}{m}')
    else:
        _w(stream, ' Moon selection:')
    _w(stream, ' ')

    # Ring selection (if not Mars)
    planet = getattr(args, 'planet', 6)
    if planet != 4:
        rings = getattr(args, 'rings', None) or []
        if rings:
            for i, r in enumerate(rings):
                prefix = ' Ring selection: ' if i == 0 else '                 '
                _w(stream, f'{prefix}{r}')
        else:
            _w(stream, ' Ring selection:')
        _w(stream, ' ')

    # Plot options
    xrange = getattr(args, 'xrange', None)
    xunit = getattr(args, 'xunit', 'arcsec')
    xrange_s = (str(xrange).strip() if xrange is not None else ' ').strip() or ' '
    _w(stream, f'     Plot scale: {xrange_s} {xunit}')

    # Title
    title = (getattr(args, 'title', None) or ' ').strip() or ' '
    _w(stream, f'          Title: "{title}"')
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

    # Observation time (no leading spaces on label)
    time_str = (
        getattr(args, 'time', None) or getattr(args, 'time_str', None) or ' '
    ).strip() or datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
    _w(stream, f'Observation time: {time_str}')

    # Ephemeris (display string from form, or numeric version)
    display = getattr(args, 'display', None)
    ephem_display = getattr(display, 'ephem_display', None) or getattr(args, 'ephem_display', None)
    if ephem_display and str(ephem_display).strip():
        _w(stream, f'       Ephemeris: {ephem_display.strip()}')
    else:
        _w(stream, f'       Ephemeris: {getattr(args, "ephem", 0)}')

    # Field of view (omit leading zero for values < 1, e.g. .005 not 0.005)
    fov = getattr(args, 'fov', None)
    if fov is None:
        fov = getattr(args, 'fov_value', 1.0)
    fov_unit = getattr(args, 'fov_unit', 'deg')
    fov_s = str(fov)
    if fov_s.startswith('0.') and len(fov_s) > 2:
        fov_s = '.' + fov_s[2:]  # keep fractional part as-is, e.g. 0.005 -> .005
    _w(stream, f'   Field of view: {fov_s} ({fov_unit})')

    # Diagram center
    center_obj = getattr(args, 'center', None)
    center_ra = getattr(args, 'center_ra', 0.0)
    center_dec = getattr(args, 'center_dec', 0.0)
    mode = getattr(center_obj, 'mode', None)
    val = getattr(args, 'center', None)
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
    if not center_body:
        center_body = _PLANET_NAMES.get(getattr(args, 'planet', 6), 'Saturn')
    if center == 'ansa':
        center_ansa = (
            getattr(center_obj, 'ansa_name', None) or getattr(args, 'center_ansa', None) or 'A Ring'
        ).strip()
        center_ew = (
            getattr(center_obj, 'ansa_ew', None) or getattr(args, 'center_ew', None) or 'east'
        ).strip()
        _w(stream, f'  Diagram center: {center_ansa} {center_ew} ansa')
    elif center == 'j2000' or (center_ra != 0.0 or center_dec != 0.0):
        ra_type = (getattr(args, 'center_ra_type', None) or 'hours').strip()
        _w(stream, f'  Diagram center: RA  = {center_ra} {ra_type}')
        _w(stream, f'                    Dec = {center_dec}')
    elif center == 'star':
        center_star = (getattr(args, 'center_star', None) or ' ').strip()
        _w(stream, f'  Diagram center: Star = {center_star}')
    else:
        _w(stream, f'  Diagram center: {center_body}')

    # Viewpoint
    viewpoint = (getattr(args, 'viewpoint', None) or ' ').strip()
    observer_obj = getattr(args, 'observer', None)
    if observer_obj is not None:
        if observer_obj.name:
            _w(stream, f'       Viewpoint: {observer_obj.name}')
        elif observer_obj.latitude_deg is not None or observer_obj.longitude_deg is not None:
            _w(stream, f'       Viewpoint: Lat = {observer_obj.latitude_deg} (deg)')
            _w(stream, f'                    Lon = {observer_obj.longitude_deg} (deg east)')
            _w(stream, f'                    Alt = {observer_obj.altitude_m} (m)')
        else:
            _w(stream, "       Viewpoint: Earth's Center")
    elif viewpoint == 'latlon':
        lat = getattr(args, 'latitude', None)
        _w(stream, f'       Viewpoint: Lat = {lat} (deg)')
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
        _w(stream, f'       Viewpoint: {obs}')
    else:
        _w(stream, "       Viewpoint: Earth's Center")

    # Moon selection: strip leading "NNN " from display strings.
    # Example: "802 Triton & Nereid" -> "Triton & Nereid".
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
        _w(stream, f'                  {moremoons}')

    # Ring selection (display string from form to preserve commas, or joined)
    rings_display = getattr(display, 'rings_display', None) or getattr(args, 'rings_display', None)
    if rings_display and str(rings_display).strip():
        ring_str = rings_display.strip()
    else:
        rings = getattr(args, 'rings', None) or getattr(args, 'ring_names', None) or []
        ring_str = ', '.join(str(r) for r in rings).strip() if rings else ' '
    _w(stream, f'  Ring selection: {ring_str}')

    # Arc model (Neptune; printed for all, blank if N/A)
    arcmodel = (getattr(args, 'arcmodel', None) or '').strip()
    _w(stream, f'       Arc model: {arcmodel}')

    # Standard stars
    standard = (getattr(args, 'standard', None) or 'No').strip()
    _w(stream, f'  Standard stars: {standard}')

    # Additional star
    additional = getattr(args, 'additional', None)
    if not additional:
        _w(stream, ' Additional star: No')
    else:
        extra_name = (getattr(args, 'extra_name', None) or ' ').strip()
        _w(stream, f' Additional star: {extra_name}')
        extra_ra = (getattr(args, 'extra_ra', None) or ' ').strip()
        extra_ra_type = (getattr(args, 'extra_ra_type', None) or 'hours').strip()
        _w(stream, f'                    RA  = {extra_ra} {extra_ra_type}')
        extra_dec = (getattr(args, 'extra_dec', None) or ' ').strip()
        _w(stream, f'                    Dec = {extra_dec}')

    # Other bodies
    other = getattr(args, 'other', None) or []
    if not other:
        _w(stream, '    Other bodies: None')
    else:
        other_list = other if isinstance(other, (list, tuple)) else [other]
        for i, o in enumerate(other_list):
            prefix = '    Other bodies: ' if i == 0 else '                  '
            _w(stream, f'{prefix}{o}')

    # Title
    title = (getattr(args, 'title', None) or ' ').strip() or ' '
    _w(stream, f'           Title: "{title}"')

    # Moon labels
    labels = (getattr(args, 'labels', None) or 'Small (6 points)').strip()
    _w(stream, f'     Moon labels: {labels}')

    # Moon enlargement
    moonpts = str(getattr(args, 'moonpts', None) or '0').strip()
    _w(stream, f'Moon enlargement: {moonpts} (points)')

    # Blank disks
    blank = (getattr(args, 'blank', None) or 'No').strip()
    _w(stream, f'     Blank disks: {blank}')

    # Arc weight (Neptune)
    arcpts = str(getattr(args, 'arcpts', None) or '').strip()
    _w(stream, f'      Arc weight: {arcpts or " "} (points)')

    # Prime meridians
    meridians_raw = getattr(args, 'meridians', None)
    if isinstance(meridians_raw, bool):
        meridians = 'Yes' if meridians_raw else 'No'
    else:
        meridians = (meridians_raw or 'Yes').strip()
    _w(stream, f' Prime meridians: {meridians}')

    _w(stream, ' ')
