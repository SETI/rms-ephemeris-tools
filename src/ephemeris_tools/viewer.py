"""Planet viewer tool: PostScript diagram and tables (port of viewer3_*.f)."""

from __future__ import annotations

import math
import sys
from typing import TextIO

from ephemeris_tools.planets import (
    JUPITER_CONFIG,
    MARS_CONFIG,
    NEPTUNE_CONFIG,
    PLUTO_CONFIG,
    SATURN_CONFIG,
    URANUS_CONFIG,
)

_PLANET_CONFIGS = {
    4: MARS_CONFIG,
    5: JUPITER_CONFIG,
    6: SATURN_CONFIG,
    7: URANUS_CONFIG,
    8: NEPTUNE_CONFIG,
    9: PLUTO_CONFIG,
}

_DEG2RAD = math.pi / 180.0
_RAD2DEG = 180.0 / math.pi
_RAD2ARCSEC = 180.0 / math.pi * 3600.0
_AU_KM = 149597870.7
_MAX_ARCSEC = 360.0 * 3600.0


def get_planet_config(planet_num: int):
    """Return PlanetConfig for planet number (4=Mars..9=Pluto)."""
    return _PLANET_CONFIGS.get(planet_num)


def _ra_hms(ra_rad: float) -> str:
    """Format RA in radians as 'hh mm ss.ssss' (hours, 4 decimals in seconds)."""
    from ephemeris_tools.angle_utils import dms_string
    ra_deg = ra_rad * _RAD2DEG
    ra_h = (ra_deg / 15.0) % 24.0
    return dms_string(ra_h, "hms", ndecimal=4)


def _dec_dms(dec_rad: float) -> str:
    """Format Dec in radians as 'dd mm ss.sss' (degrees)."""
    from ephemeris_tools.angle_utils import dms_string
    dec_deg = dec_rad * _RAD2DEG
    return dms_string(dec_deg, "dms", ndecimal=3)


def _write_fov_table(
    stream: TextIO,
    et: float,
    cfg,
    planet_ra: float,
    planet_dec: float,
    body_ids: list[int],
    id_to_name: dict[int, str],
) -> None:
    """Write Field of View Description (J2000) and body/ring geometry tables."""
    from ephemeris_tools.spice.geometry import (
        body_lonlat,
        body_phase,
        body_radec,
        body_ranges,
        planet_phase,
        planet_ranges,
    )

    cosdec = math.cos(planet_dec)

    stream.write("\n")
    stream.write("Field of View Description (J2000)\n")
    stream.write("---------------------------------\n")
    stream.write("\n")
    stream.write(
        "     Body          RA                 Dec              "
        "  RA (deg)   Dec (deg)   dRA (\")   dDec (\")\n"
    )

    for body_id in body_ids:
        ra, dec = body_radec(et, body_id)
        dra_arcsec = (ra - planet_ra) * cosdec * _RAD2ARCSEC
        ddec_arcsec = (dec - planet_dec) * _RAD2ARCSEC
        if dra_arcsec < -0.5 * _MAX_ARCSEC:
            dra_arcsec += _MAX_ARCSEC
        if dra_arcsec > 0.5 * _MAX_ARCSEC:
            dra_arcsec -= _MAX_ARCSEC
        ra_deg = ra * _RAD2DEG
        dec_deg = dec * _RAD2DEG
        name = id_to_name.get(body_id, str(body_id))
        ra_str = _ra_hms(ra)
        dec_str = _dec_dms(dec)
        stream.write(
            f"  {body_id:3d} {name:10s}  {ra_str:>18} {dec_str:>18}  "
            f"{ra_deg:10.6f} {dec_deg:12.6f} {dra_arcsec:10.4f} {ddec_arcsec:10.4f}\n"
        )

    stream.write("\n")
    stream.write("                   Sub-Observer    Sub-Solar     \n")
    lon_dir = cfg.longitude_direction
    stream.write(
        f"  Body       Lon(deg{lon_dir}) Lat(deg)  Lon(deg{lon_dir}) Lat(deg)  "
        "Phase(deg)  Distance(10^6 km)\n"
    )

    for body_id in body_ids:
        subobs_lon, subobs_lat, subsol_lon, subsol_lat = body_lonlat(et, body_id)
        phase = body_phase(et, body_id)
        _, obs_dist = body_ranges(et, body_id)
        name = id_to_name.get(body_id, str(body_id))
        stream.write(
            f"  {body_id:3d} {name:10s} "
            f"{subobs_lon * _RAD2DEG:10.3f}{subobs_lat * _RAD2DEG:10.3f} "
            f"{subsol_lon * _RAD2DEG:10.3f}{subsol_lat * _RAD2DEG:10.3f} "
            f"{phase * _RAD2DEG:13.5f} {obs_dist / 1e6:15.6f}\n"
        )

    # Ring geometry (if rings exist).
    if cfg.rings:
        from ephemeris_tools.spice.rings import ring_opening

        stream.write("\n")
        sun_dist, obs_dist = planet_ranges(et)
        phase_deg = planet_phase(et) * _RAD2DEG
        geom = ring_opening(et)
        sun_b_deg = geom.sun_b * _RAD2DEG
        sun_db_deg = geom.sun_db * _RAD2DEG
        litstr = "(lit)" if not geom.is_dark else "(unlit)"
        stream.write(
            f"  Ring sub-solar latitude (deg): {sun_b_deg:9.5f}  "
            f"({sun_b_deg - sun_db_deg:9.5f}  to  {sun_b_deg + sun_db_deg:9.5f})\n"
        )
        stream.write(
            f" Ring plane opening angle (deg): {geom.obs_b * _RAD2DEG:9.5f}  {litstr}\n"
        )
        stream.write(f"  Ring center phase angle (deg): {phase_deg:9.5f}\n")
        stream.write(
            f"      Sub-solar longitude (deg): {geom.sun_long * _RAD2DEG:9.5f}  "
            "from ring plane ascending node\n"
        )
        stream.write(
            f"   Sub-observer longitude (deg): {geom.obs_long * _RAD2DEG:9.5f}\n"
        )
        stream.write("\n")
        stream.write(f"       Sun-planet distance (AU): {sun_dist / _AU_KM:9.5f}\n")
        stream.write(f"  Observer-planet distance (AU): {obs_dist / _AU_KM:9.5f}\n")
        stream.write(f"       Sun-planet distance (km): {sun_dist / 1e6:12.6f} x 10^6\n")
        stream.write(f"  Observer-planet distance (km): {obs_dist / 1e6:12.6f} x 10^6\n")
        stream.write("\n")


def run_viewer(
    planet_num: int,
    time_str: str,
    fov: float,
    center_ra: float,
    center_dec: float,
    viewpoint: str,
    ephem_version: int = 1,
    moon_ids: list[int] | None = None,
    output_ps: TextIO | None = None,
    output_txt: TextIO | None = None,
) -> None:
    """Generate planet viewer PostScript diagram and Field of View table."""
    cfg = get_planet_config(planet_num)
    if cfg is None:
        raise ValueError(f"Unknown planet number: {planet_num}")
    from ephemeris_tools.spice.load import load_spice_files
    from ephemeris_tools.spice.observer import set_observer_id
    from ephemeris_tools.constants import EARTH_ID
    from ephemeris_tools.time_utils import parse_datetime, tai_from_day_sec, tdb_from_tai
    from ephemeris_tools.spice.geometry import body_radec, limb_radius

    ok, reason = load_spice_files(planet_num, ephem_version)
    if not ok:
        raise RuntimeError(f"Failed to load SPICE kernels: {reason}")
    set_observer_id(EARTH_ID)

    parsed = parse_datetime(time_str)
    if parsed is None:
        raise ValueError(f"Invalid time: {time_str!r}")
    day, sec = parsed
    et = tdb_from_tai(tai_from_day_sec(day, sec))

    fov_rad = fov * _DEG2RAD

    _, limb_rad_rad = limb_radius(et)
    planet_ra, planet_dec = body_radec(et, cfg.planet_id)
    if center_ra == 0.0 and center_dec == 0.0:
        center_ra_rad = planet_ra
        center_dec_rad = planet_dec
    else:
        center_ra_rad = center_ra * _DEG2RAD
        center_dec_rad = center_dec * _DEG2RAD

    track_moon_ids = [m.id for m in cfg.moons if m.id != cfg.planet_id]
    if moon_ids:
        track_moon_ids = [tid for tid in track_moon_ids if tid in moon_ids]
    id_to_name = {m.id: m.name for m in cfg.moons}

    # Table: planet first, then moons (same order as FORTRAN moon_flags).
    table_body_ids = [cfg.planet_id] + track_moon_ids
    _write_fov_table(
        sys.stdout, et, cfg, planet_ra, planet_dec, table_body_ids, id_to_name
    )
    if output_txt:
        _write_fov_table(
            output_txt, et, cfg, planet_ra, planet_dec, table_body_ids, id_to_name
        )

    # Plot: 400x400 pt, center (200, 200). Scale: half_plot / fov_rad rad per pt.
    half_plot = 200.0
    scale = half_plot / fov_rad

    def to_plot(ra: float, dec: float) -> tuple[float, float]:
        dx = (ra - center_ra_rad) * math.cos(center_dec_rad)
        dy = dec - center_dec_rad
        return (-dx * scale, dy * scale)

    bodies: list[tuple[float, float, str, bool]] = []
    px, py = to_plot(planet_ra, planet_dec)
    bodies.append((px, py, cfg.planet_name, True))

    for mid in track_moon_ids:
        ra, dec = body_radec(et, mid)
        mx, my = to_plot(ra, dec)
        name = id_to_name.get(mid, str(mid))
        bodies.append((mx, my, name.upper(), False))

    limb_plot = limb_rad_rad * scale
    title = f"{cfg.planet_name}  {time_str}"

    if output_ps:
        from ephemeris_tools.rendering.draw_view import draw_planetary_view
        draw_planetary_view(
            output_ps,
            planet_name=cfg.planet_name,
            limb_radius_plot=limb_plot,
            bodies_plot=bodies,
            title=title,
        )
