"""Moon tracker tool: PostScript plot and text table (port of tracker3_xxx.f)."""

from __future__ import annotations

import math
from typing import TextIO, TypedDict, cast

from ephemeris_tools.params import Observer, TrackerParams
from ephemeris_tools.spice.common import get_state


class _RunTrackerKwargs(TypedDict, total=True):
    """Keyword arguments for run_tracker (legacy signature from TrackerParams)."""

    planet_num: int
    start_time: str
    stop_time: str
    interval: float
    time_unit: str
    viewpoint: str
    moon_ids: list[int] | None
    ephem_version: int
    xrange: float | None
    xscaled: bool
    title: str
    ring_options: list[int] | None
    observer_latitude: float | None
    observer_longitude: float | None
    observer_altitude: float | None
    output_ps: TextIO | None
    output_txt: TextIO | None


# Radians to arcsec for tracker plot
_RAD_TO_ARCSEC = 180.0 / math.pi * 3600.0


def _ring_options_to_flags(planet_num: int, ring_options: list[int], nrings: int) -> list[bool]:
    """Convert CGI ring option codes to ring visibility flags (tracker3_xxx.f).

    Parameters:
        planet_num: Planet number (5=Jupiter, 6=Saturn, etc.).
        ring_options: List of option codes (e.g. 61=Saturn main, 62=G+E).
        nrings: Number of ring entries in geometry.

    Returns:
        List of bool, one per ring; True = show.
    """
    required = 5 if planet_num == 6 else (3 if planet_num == 5 else 1)
    flags = [False] * max(nrings, required, 1)
    for opt in ring_options:
        if planet_num == 5:  # Jupiter: 51=Main, 52=Gossamer
            if opt == 51:
                flags[0] = True
            elif opt == 52:
                flags[1] = flags[2] = True
        elif planet_num == 6:  # Saturn: 61=Main, 62=G+E, 63=outer
            if opt == 61:
                flags[0] = True
            elif opt == 62:
                flags[1] = flags[2] = True
            elif opt == 63:
                flags[3] = flags[4] = True
        elif (planet_num == 7 and opt == 71) or (planet_num == 8 and opt == 81):  # Uranus Epsilon
            flags[0] = True
    return flags


def _tracker_call_kwargs_from_params(params: TrackerParams) -> _RunTrackerKwargs:
    """Convert a ``TrackerParams`` object to legacy ``run_tracker`` kwargs."""
    viewpoint = params.observer.name if params.observer.name is not None else 'Earth'
    xunit = params.xunit.lower()
    ring_options = None
    if params.ring_names:
        from ephemeris_tools.params import parse_ring_spec

        ring_options = parse_ring_spec(params.planet_num, params.ring_names)
    return {
        'planet_num': params.planet_num,
        'start_time': params.start_time,
        'stop_time': params.stop_time,
        'interval': params.interval,
        'time_unit': params.time_unit,
        'viewpoint': viewpoint,
        'moon_ids': params.moon_ids,
        'ephem_version': params.ephem_version,
        'xrange': params.xrange,
        'xscaled': 'radii' in xunit,
        'title': params.title,
        'ring_options': ring_options,
        'observer_latitude': params.observer.latitude_deg,
        'observer_longitude': params.observer.longitude_deg,
        'observer_altitude': params.observer.altitude_m,
        'output_ps': params.output_ps,
        'output_txt': params.output_txt,
    }


def run_tracker(params: TrackerParams) -> None:
    """Generate moon tracker PostScript plot and optional text table (tracker3_xxx.f).

    Loads SPICE, computes moon offsets over the time range, draws plot and table.

    Parameters:
        params: Structured tracker inputs (planet, time range, interval, observer,
            moons, rings, output streams).

    Raises:
        ValueError: Invalid time range or planet.
        RuntimeError: SPICE load failure.
    """
    kwargs = _tracker_call_kwargs_from_params(params)
    _run_tracker_impl(**kwargs)


def _run_tracker_impl(
    *,
    planet_num: int,
    start_time: str = '',
    stop_time: str = '',
    interval: float = 1.0,
    time_unit: str = 'hour',
    viewpoint: str = 'Earth',
    moon_ids: list[int] | None = None,
    ephem_version: int = 0,
    xrange: float | None = None,
    xscaled: bool = False,
    title: str = '',
    ring_options: list[int] | None = None,
    observer_latitude: float | None = None,
    observer_longitude: float | None = None,
    observer_altitude: float | None = None,
    output_ps: TextIO | None = None,
    output_txt: TextIO | None = None,
) -> None:
    """Internal tracker implementation (flat kwargs from TrackerParams)."""
    from ephemeris_tools.constants import EARTH_ID
    from ephemeris_tools.spice.geometry import moon_tracker_offsets

    if moon_ids is None:
        moon_ids = []

    from ephemeris_tools.spice.load import load_spice_files
    from ephemeris_tools.spice.observer import set_observer_id, set_observer_location
    from ephemeris_tools.time_utils import (
        interval_seconds,
        parse_datetime,
        tai_from_day_sec,
        tdb_from_tai,
    )
    from ephemeris_tools.viewer import get_planet_config

    ok, reason = load_spice_files(planet_num, ephem_version)
    if not ok:
        raise RuntimeError(f'Failed to load SPICE kernels: {reason}')
    if observer_latitude is not None and observer_longitude is not None:
        set_observer_location(
            observer_latitude,
            observer_longitude,
            observer_altitude if observer_altitude is not None else 0.0,
        )
    else:
        from ephemeris_tools.constants import spacecraft_code_to_id, spacecraft_name_to_code
        from ephemeris_tools.spice.load import load_spacecraft

        code = spacecraft_name_to_code(viewpoint)
        if code is not None:
            sc_id = spacecraft_code_to_id(code)
            if sc_id:
                load_spacecraft(sc_id, planet_num, ephem_version, set_obs=True)
            else:
                set_observer_id(EARTH_ID)
        else:
            set_observer_id(EARTH_ID)

    start_parsed = parse_datetime(start_time)
    stop_parsed = parse_datetime(stop_time)
    if start_parsed is None or stop_parsed is None:
        raise ValueError('Invalid start or stop time')
    day1, sec1 = start_parsed
    day2, sec2 = stop_parsed
    tai1 = tai_from_day_sec(day1, sec1)
    tai2 = tai_from_day_sec(day2, sec2)
    dsec = interval_seconds(interval, time_unit, min_seconds=60.0, round_to_minutes=True)
    ntimes = int((tai2 - tai1) / dsec) + 1
    if ntimes < 2:
        raise ValueError('Time range too short or interval too large')
    if ntimes > 10000:
        raise ValueError('Number of time steps exceeds limit of 10000')

    cfg = get_planet_config(planet_num)
    if cfg is None:
        raise ValueError(f'Unknown planet number: {planet_num}')
    state = get_state()
    # Moon body IDs only (exclude planet center, e.g. 699 for Saturn).
    track_moon_ids = [m.id for m in cfg.moons if m.id != state.planet_id]
    if moon_ids:
        track_moon_ids = [tid for tid in track_moon_ids if tid in moon_ids]
    id_to_name = {m.id: m.name for m in cfg.moons}
    moon_names = [id_to_name.get(tid, str(tid)) for tid in track_moon_ids]

    # FORTRAN quirk (tracker3_xxx + rspk_trackmoons): moon geometry is sampled
    # on an evenly stretched grid from start->stop, while table timestamps use
    # the original fixed interval grid.
    sample_dt = (tai2 - tai1) / (ntimes - 1) if ntimes > 1 else 1.0
    table_times_tai: list[float] = []
    moon_offsets_arcsec: list[list[float]] = [[] for _ in track_moon_ids]
    limb_arcsec: list[float] = []

    for i in range(ntimes):
        sample_tai = tai1 + i * sample_dt
        table_tai = tai1 + i * dsec
        et = tdb_from_tai(sample_tai)
        offsets_rad, limb_rad = moon_tracker_offsets(et, track_moon_ids)
        table_times_tai.append(table_tai)
        limb_arcsec.append(limb_rad * _RAD_TO_ARCSEC)
        for j, o in enumerate(offsets_rad):
            moon_offsets_arcsec[j].append(o * _RAD_TO_ARCSEC)

    # X-axis range: user xrange (arcsec or radii per xscaled) or from limb.
    explicit_xrange = xrange is not None and xrange > 0
    if explicit_xrange:
        xrange_val = xrange
    else:
        xrange_val = max(limb_arcsec) * 2.0 if limb_arcsec else 100.0
        xrange_val = max(xrange_val, 10.0)
        xscaled = False
    if not xscaled and not explicit_xrange:
        xrange_val = max(xrange_val if xrange_val is not None else 0.0, 10.0)

    # Planet radius (km) for ring drawing - from SPICE to match FORTRAN.
    import cspyce

    radii = cspyce.bodvrd(str(state.planet_id), 'RADII')
    rplanet_km = radii[0]

    # Ring data: FORTRAN constants; ring_flags from ring_options if provided.
    from ephemeris_tools.rendering.draw_tracker import (
        PLANET_GRAY,
        RING_DATA,
        draw_moon_tracks,
    )

    nrings, ring_rads_list, ring_grays_list = RING_DATA.get(planet_num, (0, [0.0], [0.75]))
    if ring_options:
        ring_flags = _ring_options_to_flags(planet_num, ring_options, nrings)
    else:
        ring_flags = [False] * max(nrings, 1)
    ring_rads_km = (ring_rads_list + [0.0] * 5)[:5]
    ring_grays = (ring_grays_list + [0.5] * 5)[:5]

    out_name = getattr(output_ps, 'name', None) if output_ps else None
    filename = str(out_name) if out_name else 'tracker.ps'

    # Captions: Ephemeris and Viewpoint (match original FORTRAN output).
    # FORTRAN: rcaptions(1) = WWW_GetKey('ephem')(5:) — kernel description.
    from ephemeris_tools.constants import EPHEM_DESCRIPTIONS_BY_PLANET

    ephem_caption = EPHEM_DESCRIPTIONS_BY_PLANET.get(planet_num, 'DE440')

    # FORTRAN caption text in current CGI behavior does not append empty
    # parentheses for non-spacecraft observers.
    viewpoint_caption = (viewpoint or 'Earth').strip()
    if not viewpoint_caption or viewpoint_caption.lower() in ('earth', 'observatory'):
        viewpoint_caption = "Earth's center"

    ncaptions = 2
    lcaptions = ['Ephemeris:', 'Viewpoint:']
    rcaptions = [ephem_caption, viewpoint_caption]

    # FORTRAN uses DOY format only for spacecraft observers (not Earth, JWST, HST).
    # obs_isc==0 means Earth's center or ground-based observatory.
    # The Python viewpoint string is "observatory", "latlon", "Earth", or a spacecraft name.
    from ephemeris_tools.constants import SPACECRAFT_IDS, SPACECRAFT_NAMES

    obs_is_spacecraft = False
    obs_vp = (viewpoint or '').strip()
    if obs_vp.lower() not in ('', 'earth', 'observatory', 'latlon'):
        # Check if it matches a known spacecraft name/ID
        for sc_name in SPACECRAFT_NAMES:
            if obs_vp.lower() == sc_name.lower():
                obs_is_spacecraft = True
                break
        if not obs_is_spacecraft:
            for sc_id in SPACECRAFT_IDS:
                if obs_vp.upper() == sc_id:
                    obs_is_spacecraft = True
                    break
    use_doy_format = (
        obs_is_spacecraft and 'JWST' not in obs_vp.upper() and 'HST' not in obs_vp.upper()
    )
    if output_ps:
        draw_moon_tracks(
            output_ps,
            planet_num=planet_num,
            ntimes=ntimes,
            time1_tai=tai1,
            time2_tai=tai2,
            dt=sample_dt,
            xrange=xrange_val if xrange_val is not None else 100.0,
            xscaled=xscaled,
            moon_arcsec=moon_offsets_arcsec,
            limb_arcsec=limb_arcsec,
            moon_names=moon_names,
            nrings=nrings,
            ring_flags=ring_flags,
            ring_rads_km=ring_rads_km,
            ring_grays=ring_grays,
            planet_gray=PLANET_GRAY,
            rplanet_km=rplanet_km,
            title=title or '',
            ncaptions=ncaptions,
            lcaptions=lcaptions,
            rcaptions=rcaptions,
            align_loc=180.0,
            filename=filename,
            use_doy_format=use_doy_format,
        )

    if output_txt:
        from ephemeris_tools.time_utils import (
            day_sec_from_tai,
            hms_from_sec,
            mjd_from_tai,
            ymd_from_day,
        )

        header = ' mjd        year mo dy hr mi   limb'
        for name in moon_names[:25]:
            # FORTRAN: moon_names are uppercase (transformed in tracker3_xxx.f)
            uname = name.upper()
            header += ' ' + (uname[:9] if len(uname) >= 9 else uname + ' ' * (9 - len(uname)))
        output_txt.write(header.rstrip() + '\n')
        for irec in range(ntimes):
            tai = table_times_tai[irec]
            day, sec = day_sec_from_tai(tai)
            _, _, sec_frac = hms_from_sec(sec)
            if sec_frac >= 30.0:
                tai = tai + 30.0
                day, sec = day_sec_from_tai(tai)
            year, month, day = ymd_from_day(day)
            hour, minute, _ = hms_from_sec(sec)
            mjd = mjd_from_tai(tai)
            limb = limb_arcsec[irec]
            row = f'{mjd:11.4f}{year:5d}{month:3d}{day:3d}{hour:3d}{minute:3d}{limb:7.3f}'
            for j in range(len(track_moon_ids)):
                row += f'{moon_offsets_arcsec[j][irec]:10.3f}'
            for _ in range(len(track_moon_ids), 25):
                row += ' ' * 10
            output_txt.write(row.rstrip() + '\n')
        output_txt.flush()


def tracker_params_from_legacy_kwargs(**kwargs: object) -> TrackerParams:
    """Build TrackerParams from flat legacy keyword arguments (e.g. for tests).

    Accepts the same keyword names as the legacy run_tracker signature.
    """

    def _get(key: str, default: object = None) -> object:
        return kwargs.get(key, default)

    observer = Observer(
        name=cast('str | None', _get('viewpoint')),
        latitude_deg=cast('float | None', _get('observer_latitude')),
        longitude_deg=cast('float | None', _get('observer_longitude')),
        altitude_m=cast('float | None', _get('observer_altitude')),
    )
    xscaled = bool(_get('xscaled', False))
    return TrackerParams(
        planet_num=int(cast('int', _get('planet_num', 0))),
        start_time=str(_get('start_time', '')),
        stop_time=str(_get('stop_time', '')),
        interval=float(cast('float', _get('interval', 1.0))),
        time_unit=str(_get('time_unit', 'hour')),
        observer=observer,
        ephem_version=int(cast('int', _get('ephem_version', 0))),
        moon_ids=cast('list[int]', _get('moon_ids') or []),
        ring_names=None,
        xrange=cast('float | None', _get('xrange')),
        xunit='radii' if xscaled else 'arcsec',
        title=str(_get('title', '')),
        output_ps=cast('TextIO | None', _get('output_ps')),
        output_txt=cast('TextIO | None', _get('output_txt')),
    )
