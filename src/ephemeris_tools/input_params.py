"""Input Parameters section (port of FORTRAN Summarize request)."""

from __future__ import annotations

from typing import TYPE_CHECKING, TextIO

if TYPE_CHECKING:
    from argparse import Namespace

    from ephemeris_tools.params import EphemerisParams


def _w(stream: TextIO, line: str) -> None:
    stream.write(line + "\n")


def write_input_parameters_ephemeris(stream: TextIO, params: EphemerisParams) -> None:
    """Write Input Parameters section for ephemeris (ephem3_xxx.f)."""
    _w(stream, "Input Parameters")
    _w(stream, "----------------")
    _w(stream, " ")

    # Tabulation parameters
    start = (params.start_time or " ").strip() or " "
    stop = (params.stop_time or " ").strip() or " "
    _w(stream, f"     Start time: {start}")
    _w(stream, f"      Stop time: {stop}")

    interval_s = str(params.interval).strip() if params.interval is not None else "1"
    _w(stream, f"       Interval: {interval_s} {params.time_unit}")
    _w(stream, f"      Ephemeris: {params.ephem_version}")

    # Viewpoint
    if params.viewpoint == "latlon" and (
        params.latitude_deg is not None or params.longitude_deg is not None
    ):
        lat = params.latitude_deg if params.latitude_deg is not None else ""
        _w(stream, f"      Viewpoint: Lat = {lat} (deg)")
        lon = params.longitude_deg if params.longitude_deg is not None else ""
        _w(stream, f"                 Lon = {lon} (deg {params.lon_dir})")
        alt = params.altitude_m if params.altitude_m is not None else ""
        _w(stream, f"                 Alt = {alt} (m)")
    else:
        vp = (params.observatory or "Earth's Center").strip()
        if not vp:
            vp = "Earth's Center"
        if params.sc_trajectory:
            vp = f"{vp} ({params.sc_trajectory})"
        _w(stream, f"      Viewpoint: {vp}")

    _w(stream, " ")

    # General columns
    if params.columns:
        for i, c in enumerate(params.columns):
            prefix = "General columns: " if i == 0 else "                 "
            _w(stream, f"{prefix}{c}")
        _w(stream, " ")
    else:
        _w(stream, "General columns:")
    _w(stream, " ")

    # Moon columns
    if params.mooncols:
        for i, c in enumerate(params.mooncols):
            prefix = "   Moon columns: " if i == 0 else "                 "
            _w(stream, f"{prefix}{c}")
        _w(stream, " ")
    else:
        _w(stream, "   Moon columns:")
    _w(stream, " ")

    # Moon selection
    if params.moon_ids:
        for i, mid in enumerate(params.moon_ids):
            prefix = " Moon selection: " if i == 0 else "                 "
            _w(stream, f"{prefix}{mid}")
        _w(stream, " ")
    else:
        _w(stream, " Moon selection:")
    _w(stream, " ")


def write_input_parameters_tracker(stream: TextIO, args: Namespace) -> None:
    """Write Input Parameters section for tracker (tracker3_xxx.f)."""
    _w(stream, "Input Parameters")
    _w(stream, "----------------")
    _w(stream, " ")

    start = (getattr(args, "start", None) or " ").strip() or "2025-01-01 00:00"
    stop = (getattr(args, "stop", None) or " ").strip() or "2025-01-02 00:00"
    _w(stream, f"     Start time: {start}")
    _w(stream, f"      Stop time: {stop}")

    interval = getattr(args, "interval", 1.0)
    interval_s = str(interval).strip() if interval is not None else "1"
    time_unit = getattr(args, "time_unit", "hour")
    _w(stream, f"       Interval: {interval_s} {time_unit}")
    _w(stream, f"      Ephemeris: {getattr(args, 'ephem', 0)}")

    # Viewpoint
    viewpoint = (getattr(args, "viewpoint", None) or " ").strip()
    if viewpoint == "latlon":
        lat = getattr(args, "latitude", None)
        _w(stream, f"      Viewpoint: Lat = {lat} (deg)")
        lon = getattr(args, "longitude", None)
        lon_dir = getattr(args, "lon_dir", "east")
        _w(stream, f"                 Lon = {lon} (deg {lon_dir})")
        alt = getattr(args, "altitude", None)
        _w(stream, f"                 Alt = {alt} (m)")
    elif viewpoint and getattr(args, "observatory", None):
        vp = (getattr(args, "observatory", None) or "").strip()
        sc = getattr(args, "sc_trajectory", 0)
        if sc:
            vp = f"{vp} ({sc})"
        _w(stream, f"      Viewpoint: {vp}")
    else:
        _w(stream, "      Viewpoint: Earth's Center")

    _w(stream, " ")

    # Moon selection
    moons = getattr(args, "moons", None) or []
    if moons:
        for i, m in enumerate(moons):
            prefix = " Moon selection: " if i == 0 else "                 "
            _w(stream, f"{prefix}{m}")
    else:
        _w(stream, " Moon selection:")
    _w(stream, " ")

    # Ring selection (if not Mars)
    planet = getattr(args, "planet", 6)
    if planet != 4:
        rings = getattr(args, "rings", None) or []
        if rings:
            for i, r in enumerate(rings):
                prefix = " Ring selection: " if i == 0 else "                 "
                _w(stream, f"{prefix}{r}")
        else:
            _w(stream, " Ring selection:")
        _w(stream, " ")

    # Plot options
    xrange = getattr(args, "xrange", None)
    xunit = getattr(args, "xunit", "arcsec")
    xrange_s = (str(xrange).strip() if xrange is not None else " ").strip() or " "
    _w(stream, f"     Plot scale: {xrange_s} {xunit}")

    # Title
    title = (getattr(args, "title", None) or " ").strip() or " "
    _w(stream, f'          Title: "{title}"')
    _w(stream, " ")


_PLANET_NAMES = {4: "Mars", 5: "Jupiter", 6: "Saturn", 7: "Uranus", 8: "Neptune", 9: "Pluto"}


def write_input_parameters_viewer(stream: TextIO, args: Namespace) -> None:
    """Write Input Parameters section for viewer (viewer3_sat.f)."""
    _w(stream, "Input Parameters")
    _w(stream, "----------------")
    _w(stream, " ")

    # Observation time
    time_str = (getattr(args, "time", None) or " ").strip() or "2025-01-01 12:00"
    _w(stream, f"  Observation time: {time_str}")

    # Ephemeris
    _w(stream, f"         Ephemeris: {getattr(args, 'ephem', 0)}")

    # Field of view
    fov = getattr(args, "fov", 1.0)
    fov_unit = getattr(args, "fov_unit", "deg")
    _w(stream, f"     Field of view: {fov} ({fov_unit})")

    # Diagram center
    center_ra = getattr(args, "center_ra", 0.0)
    center_dec = getattr(args, "center_dec", 0.0)
    center = (getattr(args, "center", None) or "body").strip().lower()
    center_body = (getattr(args, "center_body", None) or " ").strip()
    if not center_body:
        center_body = _PLANET_NAMES.get(getattr(args, "planet", 6), "Saturn")
    if center == "ansa":
        center_ansa = (getattr(args, "center_ansa", None) or "A Ring").strip()
        center_ew = (getattr(args, "center_ew", None) or "east").strip()
        _w(stream, f"    Diagram center: {center_ansa} {center_ew} ansa")
    elif center == "j2000" or (center_ra != 0.0 or center_dec != 0.0):
        ra_type = (getattr(args, "center_ra_type", None) or "hours").strip()
        _w(stream, f"    Diagram center: RA  = {center_ra} {ra_type}")
        _w(stream, f"                    Dec = {center_dec}")
    elif center == "star":
        center_star = (getattr(args, "center_star", None) or " ").strip()
        _w(stream, f"    Diagram center: Star = {center_star}")
    else:
        _w(stream, f"    Diagram center: {center_body}")

    # Viewpoint
    viewpoint = (getattr(args, "viewpoint", None) or " ").strip()
    if viewpoint == "latlon":
        lat = getattr(args, "latitude", None)
        _w(stream, f"         Viewpoint: Lat = {lat} (deg)")
        lon = getattr(args, "longitude", None)
        lon_dir = getattr(args, "lon_dir", "east")
        _w(stream, f"                    Lon = {lon} (deg {lon_dir})")
        alt = getattr(args, "altitude", None)
        _w(stream, f"                    Alt = {alt} (m)")
    elif viewpoint and (getattr(args, "observatory", None) or "").strip():
        obs = (getattr(args, "observatory", None) or "").strip()
        sc = getattr(args, "sc_trajectory", 0)
        if sc:
            obs = f"{obs} ({sc})"
        _w(stream, f"         Viewpoint: {obs}")
    else:
        _w(stream, "         Viewpoint: Earth's Center")

    # Moon selection
    moons = getattr(args, "moons", None) or []
    moon_str = " ".join(str(m) for m in moons).strip() if moons else " "
    _w(stream, f"    Moon selection: {moon_str}")
    moremoons = getattr(args, "moremoons", None)
    if moremoons:
        _w(stream, f"                    {moremoons}")

    # Ring selection
    rings = getattr(args, "rings", None) or []
    ring_str = " ".join(str(r) for r in rings).strip() if rings else " "
    _w(stream, f"    Ring selection: {ring_str}")

    # Arc model (Neptune; printed for all, blank if N/A)
    arcmodel = (getattr(args, "arcmodel", None) or " ").strip()
    _w(stream, f"       Arc model: {arcmodel}")

    # Standard stars
    standard = (getattr(args, "standard", None) or "No").strip()
    _w(stream, f"    Standard stars: {standard}")

    # Additional star
    additional = getattr(args, "additional", None)
    if not additional:
        _w(stream, "   Additional star: No")
    else:
        extra_name = (getattr(args, "extra_name", None) or " ").strip()
        _w(stream, f"   Additional star: {extra_name}")
        extra_ra = (getattr(args, "extra_ra", None) or " ").strip()
        extra_ra_type = (getattr(args, "extra_ra_type", None) or "hours").strip()
        _w(stream, f"                    RA  = {extra_ra} {extra_ra_type}")
        extra_dec = (getattr(args, "extra_dec", None) or " ").strip()
        _w(stream, f"                    Dec = {extra_dec}")

    # Other bodies
    other = getattr(args, "other", None) or []
    if not other:
        _w(stream, "      Other bodies: None")
    else:
        other_list = other if isinstance(other, (list, tuple)) else [other]
        for i, o in enumerate(other_list):
            prefix = "      Other bodies: " if i == 0 else "                    "
            _w(stream, f"{prefix}{o}")

    # Title
    title = (getattr(args, "title", None) or " ").strip() or " "
    _w(stream, f'             Title: "{title}"')

    # Moon labels
    labels = (getattr(args, "labels", None) or "Small (6 points)").strip()
    _w(stream, f"       Moon labels: {labels}")

    # Moon enlargement
    moonpts = (getattr(args, "moonpts", None) or "0").strip()
    _w(stream, f"  Moon enlargement: {moonpts} (points)")

    # Blank disks
    blank = (getattr(args, "blank", None) or "No").strip()
    _w(stream, f"       Blank disks: {blank}")

    # Ring plot type
    opacity = (getattr(args, "opacity", None) or "Transparent").strip()
    _w(stream, f"    Ring plot type: {opacity}")

    # Pericenter markers
    peris = (getattr(args, "peris", None) or "None").strip()
    _w(stream, f"Pericenter markers: {peris}")
    peripts = (getattr(args, "peripts", None) or "4").strip()
    _w(stream, f"       Marker size: {peripts} (points)")

    # Arc weight (Neptune)
    arcpts = (getattr(args, "arcpts", None) or " ").strip()
    _w(stream, f"      Arc weight: {arcpts} (points)")

    # Prime meridians
    meridians = (getattr(args, "meridians", None) or "Yes").strip()
    _w(stream, f"   Prime meridians: {meridians}")

    _w(stream, " ")
