"""Build EphemerisParams, ViewerParams, TrackerParams from CGI-style env vars."""

from __future__ import annotations

import logging

from ephemeris_tools.constants import DEFAULT_INTERVAL
from ephemeris_tools.params import (
    EphemerisParams,
    ExtraStar,
    Observer,
    TrackerParams,
    ViewerCenter,
    ViewerDisplayInfo,
    ViewerParams,
    _get_env,
    _get_keys_env,
    _normalize_time_unit,
    _parse_observatory_coords,
    _parse_sexagesimal_to_degrees,
    _safe_float,
    parse_column_spec,
    parse_mooncol_spec,
)

logger = logging.getLogger(__name__)


def ephemeris_params_from_env() -> EphemerisParams | None:
    """Build EphemerisParams from CGI-style environment variables.

    Reads NPLANET, start, stop, interval, viewpoint, columns, etc. from env.

    Returns:
        EphemerisParams or None if required keys are missing/invalid.
    """
    nplanet_s = _get_env('NPLANET')
    if len(nplanet_s) == 0:
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
    if len(start) == 0 or len(stop) == 0:
        return None

    interval_s = _get_env('interval', '1')
    try:
        interval = float(interval_s)
    except ValueError as e:
        logger.error('Invalid interval %r (must be number): %s; using 1.0', interval_s, e)
        interval = DEFAULT_INTERVAL
    time_unit = _normalize_time_unit(_get_env('time_unit', 'hour'))

    ephem_s = _get_env('ephem', '0')
    try:
        ephem_version = int(ephem_s.split()[0])
    except (ValueError, IndexError) as e:
        logger.error('Invalid ephem %r (must be integer): %s; using 0 (latest)', ephem_s, e)
        ephem_version = 0

    viewpoint = _get_env('viewpoint', 'observatory')
    observatory = _get_env('observatory', "Earth's center")
    if observatory.strip().lower() == "earth's center":
        observatory = "Earth's center"
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
        # In CGI mode we preserve exactly what the form submitted, so empty
        # selections stay empty instead of injecting CLI defaults.
        columns=columns,
        mooncols=mooncols,
        moon_ids=moon_ids,
        ephem_display=_get_env('ephem') or None,
        mooncols_display=_get_keys_env('mooncols') or None,
        moons_display=_get_keys_env('moons') or None,
    )


def viewer_params_from_env() -> ViewerParams | None:
    """Build ``ViewerParams`` from CGI-style environment variables."""
    nplanet_s = _get_env('NPLANET')
    if len(nplanet_s) == 0:
        return None
    try:
        planet_num = int(nplanet_s)
    except ValueError:
        return None
    if planet_num < 4 or planet_num > 9:
        logger.error('NPLANET %d out of range (must be 4-9)', planet_num)
        return None
    time_str = _get_env('time')
    if len(time_str) == 0:
        return None
    fov_s = _get_env('fov', '1')
    try:
        fov_value = float(fov_s)
    except ValueError:
        # FORTRAN list-directed READ treats comma as a value separator, so
        # strings like "557,000" parse as 557. Emulate that behavior.
        head = fov_s.split(',', 1)[0].strip()
        try:
            fov_value = float(head)
        except ValueError:
            fov_value = 1.0
    fov_unit = _get_env('fov_unit', 'degrees')

    center_mode = _get_env('center', 'body')
    if center_mode == 'J2000':
        ra_type = _get_env('center_ra_type', 'hours').strip().lower()
        is_ra_hours = not ra_type.startswith('d')
        try:
            ra_deg = _parse_sexagesimal_to_degrees(
                _get_env('center_ra', '0'),
                is_ra_hours=is_ra_hours,
            )
        except ValueError:
            ra_deg = 0.0
        try:
            dec_deg = _parse_sexagesimal_to_degrees(
                _get_env('center_dec', '0'),
                is_ra_hours=False,
            )
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
    observer = Observer(name="Earth's center")
    viewpoint_display: str | None = None
    if viewpoint == 'latlon':
        lat_s = _get_env('latitude')
        lon_s = _get_env('longitude')
        alt_s = _get_env('altitude')
        lon_dir = _get_env('lon_dir', 'east')
        try:
            lat = float(lat_s) if lat_s else None
        except ValueError:
            lat = None
        try:
            lon = float(lon_s) if lon_s else None
        except ValueError:
            lon = None
        if lon is not None and lon_dir.lower() == 'west':
            lon = -lon
        try:
            alt = float(alt_s) if alt_s else None
        except ValueError:
            alt = None
        observer = Observer(latitude_deg=lat, longitude_deg=lon, lon_dir=lon_dir, altitude_m=alt)
        if lat_s and lon_s and alt_s:
            # FORTRAN captions preserve original CGI precision for lat/lon/alt text.
            viewpoint_display = f'({lat_s}, {lon_s} {lon_dir}, {alt_s})'
    elif viewpoint == 'observatory':
        obs_name = _get_env('observatory', "Earth's center")
        if obs_name.strip().lower() == "earth's center":
            obs_name = "Earth's center"
        coords = _parse_observatory_coords(obs_name)
        if coords is None:
            observer = Observer(name=obs_name)
        else:
            lat, lon, alt = coords
            observer = Observer(
                name=obs_name,
                latitude_deg=lat,
                longitude_deg=lon,
                altitude_m=alt,
            )
    elif viewpoint:
        observer = Observer(name=viewpoint)

    moon_tokens = _get_keys_env('moons')
    from ephemeris_tools.planets import parse_moon_spec

    moon_ids = parse_moon_spec(planet_num, moon_tokens) if moon_tokens else None
    rings_raw = _get_env('rings')
    ring_names = None
    if rings_raw:
        ring_names = []
        for comma_part in rings_raw.split(','):
            for amp_part in comma_part.split('&'):
                token = amp_part.strip()
                if token:
                    ring_names.append(token)
    blank_flag = _get_env('blank', '').lower()
    blank_disks = blank_flag in {'yes', 'y', 'true', '1'}
    meridians_flag = _get_env('meridians', '').lower()
    meridians = meridians_flag in {'yes', 'y', 'true', '1'}
    opacity = _get_env('opacity', 'Transparent') or 'Transparent'
    peris = _get_env('peris', 'None') or 'None'
    peripts_s = _get_env('peripts', '4')
    try:
        peripts = float(peripts_s)
    except ValueError:
        peripts = 4.0
    arcmodel = _get_env('arcmodel') or None
    arcpts_s = _get_env('arcpts', '4')
    try:
        arcpts = float(arcpts_s)
    except ValueError:
        arcpts = 4.0
    other_bodies = _get_keys_env('other')
    labels = _get_env('labels', 'Small (6 points)')
    moonpts_s = _get_env('moonpts', '0')
    try:
        moonpts = float(moonpts_s)
    except ValueError:
        moonpts = 0.0
    title = _get_env('title')
    standard_flag = _get_env('standard', '').lower()
    show_standard_stars = standard_flag in {'yes', 'y', 'true', '1'}
    additional_flag = _get_env('additional', '').lower()
    extra_star: ExtraStar | None = None
    if additional_flag in {'yes', 'y', 'true', '1'}:
        extra_ra_s = _get_env('extra_ra', '')
        extra_dec_s = _get_env('extra_dec', '')
        extra_ra_type = _get_env('extra_ra_type', 'hours').strip().lower()
        is_extra_ra_hours = not extra_ra_type.startswith('d')
        if extra_ra_s.strip() and extra_dec_s.strip():
            try:
                extra_star = ExtraStar(
                    name=_get_env('extra_name', ''),
                    ra_deg=_parse_sexagesimal_to_degrees(
                        extra_ra_s,
                        is_ra_hours=is_extra_ra_hours,
                    ),
                    dec_deg=_parse_sexagesimal_to_degrees(
                        extra_dec_s,
                        is_ra_hours=False,
                    ),
                )
            except ValueError:
                extra_star = None
    ephem_s = _get_env('ephem', '0')
    parts = (ephem_s or '').strip().split()
    ephem_value = parts[0] if parts else '0'
    try:
        ephem_version = int(ephem_value)
    except (ValueError, IndexError):
        ephem_version = 0

    display = ViewerDisplayInfo(
        ephem_display=_get_env('ephem') or None,
        moons_display=_get_env('moons') or None,
        rings_display=_get_env('rings') or None,
        viewpoint_display=viewpoint_display,
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
        opacity=opacity,
        labels=labels,
        moonpts=moonpts,
        peris=peris,
        peripts=peripts,
        meridians=meridians,
        arcmodel=arcmodel,
        arcpts=arcpts,
        torus=_get_env('torus', '').strip().lower() in {'yes', 'y', 'true', '1'},
        torus_inc=_safe_float(_get_env('torus_inc', '6.8') or '6.8', 6.8),
        torus_rad=_safe_float(_get_env('torus_rad', '422000') or '422000', 422000),
        other_bodies=other_bodies if other_bodies else None,
        show_standard_stars=show_standard_stars,
        extra_star=extra_star,
        title=title,
        display=display,
    )


def tracker_params_from_env() -> TrackerParams | None:
    """Build ``TrackerParams`` from CGI-style environment variables."""
    nplanet_s = _get_env('NPLANET')
    if len(nplanet_s) == 0:
        return None
    try:
        planet_num = int(nplanet_s)
    except ValueError:
        return None
    if planet_num < 4 or planet_num > 9:
        logger.error('NPLANET %d out of range (must be 4-9)', planet_num)
        return None
    start_time = _get_env('start')
    stop_time = _get_env('stop')
    if len(start_time) == 0 or len(stop_time) == 0:
        return None
    interval_s = _get_env('interval', '1')
    try:
        interval = float(interval_s)
    except ValueError:
        interval = DEFAULT_INTERVAL
    time_unit = _normalize_time_unit(_get_env('time_unit', 'hour'))
    viewpoint = _get_env('viewpoint', 'observatory')
    observer = Observer(name="Earth's center")
    if viewpoint == 'observatory':
        obs_name = _get_env('observatory', "Earth's center")
        if obs_name.strip().lower() == "earth's center":
            obs_name = "Earth's center"
        coords = _parse_observatory_coords(obs_name)
        if coords is None:
            observer = Observer(name=obs_name)
        else:
            lat, lon, alt = coords
            observer = Observer(
                name=obs_name,
                latitude_deg=lat,
                longitude_deg=lon,
                altitude_m=alt,
            )
    elif viewpoint == 'latlon':
        lat_s = _get_env('latitude')
        lon_s = _get_env('longitude')
        alt_s = _get_env('altitude')
        lat_deg: float | None
        lon_deg: float | None
        alt_m: float | None
        try:
            lat_deg = float(lat_s) if lat_s else None
        except ValueError:
            lat_deg = None
        try:
            lon_deg = float(lon_s) if lon_s else None
        except ValueError:
            lon_deg = None
        try:
            alt_m = float(alt_s) if alt_s else None
        except ValueError:
            alt_m = None
        lon_dir = _get_env('lon_dir', 'east')
        if lon_deg is not None and lon_dir.lower() == 'west':
            lon_deg = -lon_deg
        observer = Observer(
            latitude_deg=lat_deg,
            longitude_deg=lon_deg,
            altitude_m=alt_m,
            lon_dir=lon_dir,
        )
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
    xunit_raw = _get_env('xunit', 'arcsec')
    xunit = 'radii' if 'radii' in xunit_raw.lower() else 'arcsec'
    title = _get_env('title')
    ephem_s = _get_env('ephem', '0')
    parts = (ephem_s or '').strip().split()
    ephem_value = parts[0] if parts else '0'
    try:
        ephem_version = int(ephem_value)
    except (ValueError, IndexError):
        ephem_version = 0
    sc_traj_s = _get_env('sc_trajectory', '0')
    try:
        sc_trajectory = int(sc_traj_s[:4] or '0')
    except ValueError:
        sc_trajectory = 0
    ephem_display = _get_env('ephem') or None
    moons_display = _get_keys_env('moons') or None
    rings_display = _get_keys_env('rings') or None
    return TrackerParams(
        planet_num=planet_num,
        start_time=start_time,
        stop_time=stop_time,
        interval=interval,
        time_unit=time_unit,
        observer=observer,
        ephem_version=ephem_version,
        sc_trajectory=sc_trajectory,
        moon_ids=moon_ids,
        ring_names=ring_names,
        xrange=xrange,
        xunit=xunit,
        title=title,
        ephem_display=ephem_display,
        moons_display=moons_display,
        rings_display=rings_display,
    )
