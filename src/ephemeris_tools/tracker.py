"""Moon tracker tool: PostScript plot and text table (port of tracker3_xxx.f)."""

from __future__ import annotations

import math
from typing import TextIO

from ephemeris_tools.spice.common import get_state

# Radians to arcsec for tracker plot
_RAD_TO_ARCSEC = 180.0 / math.pi * 3600.0


def _interval_seconds(interval: float, time_unit: str) -> float:
    """Convert interval and time_unit to seconds."""
    u = time_unit.lower()[:4]
    if u == "sec":
        return max(abs(interval), 1.0)
    if u == "min":
        return max(abs(interval) * 60.0, 1.0)
    if u == "hour":
        return max(abs(interval) * 3600.0, 1.0)
    if u == "day":
        return max(abs(interval) * 86400.0, 1.0)
    return max(abs(interval) * 3600.0, 1.0)


def _ring_options_to_flags(planet_num: int, ring_options: list[int], nrings: int) -> list[bool]:
    """Convert CGI ring option codes to ring_flags (FORTRAN tracker3_xxx.f logic)."""
    flags = [False] * max(nrings, 1)
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
        elif planet_num == 7 and opt == 71:  # Uranus Epsilon
            flags[0] = True
        elif planet_num == 8 and opt == 81:  # Neptune Adams
            flags[0] = True
    return flags


def run_tracker(
    planet_num: int,
    start_time: str,
    stop_time: str,
    interval: float,
    time_unit: str,
    viewpoint: str,
    moon_ids: list[int],
    ephem_version: int = 1,
    xrange: float | None = None,
    xscaled: bool = False,
    title: str = "",
    ring_options: list[int] | None = None,
    output_ps: TextIO | None = None,
    output_txt: TextIO | None = None,
) -> None:
    """Generate moon tracker plot and optional text table."""
    from ephemeris_tools.spice.load import load_spice_files
    from ephemeris_tools.spice.observer import set_observer_id
    from ephemeris_tools.constants import EARTH_ID
    from ephemeris_tools.time_utils import parse_datetime, tai_from_day_sec, tdb_from_tai
    from ephemeris_tools.spice.geometry import moon_tracker_offsets
    from ephemeris_tools.viewer import get_planet_config

    ok, reason = load_spice_files(planet_num, ephem_version)
    if not ok:
        raise RuntimeError(f"Failed to load SPICE kernels: {reason}")
    set_observer_id(EARTH_ID)

    start_parsed = parse_datetime(start_time)
    stop_parsed = parse_datetime(stop_time)
    if start_parsed is None or stop_parsed is None:
        raise ValueError("Invalid start or stop time")
    day1, sec1 = start_parsed
    day2, sec2 = stop_parsed
    tai1 = tai_from_day_sec(day1, sec1)
    tai2 = tai_from_day_sec(day2, sec2)
    dsec = _interval_seconds(interval, time_unit)
    ntimes = int((tai2 - tai1) / dsec) + 1
    if ntimes < 2:
        raise ValueError("Time range too short or interval too large")
    if ntimes > 10000:
        raise ValueError("Number of time steps exceeds limit of 10000")

    cfg = get_planet_config(planet_num)
    if cfg is None:
        raise ValueError(f"Unknown planet number: {planet_num}")
    state = get_state()
    # Moon body IDs only (exclude planet center, e.g. 699 for Saturn).
    track_moon_ids = [
        m.id for m in cfg.moons
        if m.id != state.planet_id
    ]
    if moon_ids:
        track_moon_ids = [tid for tid in track_moon_ids if tid in moon_ids]
    id_to_name = {m.id: m.name for m in cfg.moons}
    moon_names = [id_to_name.get(tid, str(tid)) for tid in track_moon_ids]

    times_tai: list[float] = []
    moon_offsets_arcsec: list[list[float]] = [[] for _ in track_moon_ids]
    limb_arcsec: list[float] = []

    for i in range(ntimes):
        tai = tai1 + i * dsec
        et = tdb_from_tai(tai)
        offsets_rad, limb_rad = moon_tracker_offsets(et, track_moon_ids)
        times_tai.append(tai)
        limb_arcsec.append(limb_rad * _RAD_TO_ARCSEC)
        for j, o in enumerate(offsets_rad):
            moon_offsets_arcsec[j].append(o * _RAD_TO_ARCSEC)

    # X-axis range: user xrange (arcsec or radii per xscaled) or from limb.
    if xrange is not None and xrange > 0:
        xrange_val = xrange
    else:
        xrange_val = max(limb_arcsec) * 2.0 if limb_arcsec else 100.0
        xrange_val = max(xrange_val, 10.0)
        xscaled = False
    if not xscaled:
        xrange_val = max(xrange_val, 10.0)

    # Planet radius (km) for ring drawing - from SPICE to match FORTRAN.
    import cspyce
    radii = cspyce.bodvrd(str(state.planet_id), "RADII")
    rplanet_km = radii[0]

    # Ring data: FORTRAN constants; ring_flags from ring_options if provided.
    from ephemeris_tools.rendering.draw_tracker import (
        RING_DATA,
        PLANET_GRAY,
        draw_moon_tracks,
    )
    nrings, ring_rads_list, ring_grays_list = RING_DATA.get(
        planet_num, (0, [0.0], [0.75])
    )
    if ring_options:
        ring_flags = _ring_options_to_flags(planet_num, ring_options, nrings)
    else:
        ring_flags = [False] * max(nrings, 1)
    ring_rads_km = (ring_rads_list + [0.0] * 5)[:5]
    ring_grays = (ring_grays_list + [0.5] * 5)[:5]

    dt = (tai2 - tai1) / (ntimes - 1) if ntimes > 1 else 1.0
    out_name = getattr(output_ps, "name", None) if output_ps else None
    filename = str(out_name) if out_name else "tracker.ps"

    # Captions: Ephemeris and Viewpoint (match original FORTRAN output).
    ephem_caption = str(ephem_version)
    viewpoint_caption = (viewpoint or "Earth").strip()
    if not viewpoint_caption or viewpoint_caption.lower() == "earth":
        viewpoint_caption = "Earth's center"
    ncaptions = 2
    lcaptions = ["Ephemeris:", "Viewpoint:"]
    rcaptions = [ephem_caption, viewpoint_caption]

    if output_ps:
        draw_moon_tracks(
            output_ps,
            planet_num=planet_num,
            ntimes=ntimes,
            time1_tai=tai1,
            time2_tai=tai2,
            dt=dt,
            xrange=xrange_val,
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
            title=title or "",
            ncaptions=ncaptions,
            lcaptions=lcaptions,
            rcaptions=rcaptions,
            align_loc=180.0,
            filename=filename,
        )
