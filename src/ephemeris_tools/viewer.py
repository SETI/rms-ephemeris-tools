"""Planet viewer tool: PostScript diagram and tables (port of viewer3_*.f)."""

from __future__ import annotations

import math
import sys
from typing import TYPE_CHECKING, TextIO

from ephemeris_tools.planets import (
    JUPITER_CONFIG,
    MARS_CONFIG,
    NEPTUNE_CONFIG,
    PLUTO_CONFIG,
    SATURN_CONFIG,
    URANUS_CONFIG,
)

if TYPE_CHECKING:
    from ephemeris_tools.planets.base import PlanetConfig

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
_SEC_PER_DAY = 86400.0


def _propagated_uranus_rings(et: float, cfg: PlanetConfig) -> tuple[list[float], list[float]]:
    """Propagate Uranus ring elements to et (viewer3_*.f ring propagation).

    Parameters:
        et: Ephemeris time (seconds).
        cfg: Planet config with rings (e.g. Uranus).

    Returns:
        (peri_deg_list, node_deg_list) in degrees.
    """
    import cspyce

    from ephemeris_tools.planets.uranus import (
        B1950_TO_J2000_URANUS,
        URANUS_REF_EPOCH_HOUR,
        URANUS_REF_EPOCH_YMD,
    )
    from ephemeris_tools.spice.common import get_state
    from ephemeris_tools.spice.observer import observer_state
    from ephemeris_tools.time_utils import day_from_ymd, tai_from_day_sec, tdb_from_tai

    y, m, d = URANUS_REF_EPOCH_YMD
    day0 = day_from_ymd(y, m, d)
    ref_tai = tai_from_day_sec(day0, float(URANUS_REF_EPOCH_HOUR * 3600))
    ref_et = tdb_from_tai(ref_tai)
    obs_pv = observer_state(et)
    state = get_state()
    _planet_dpv, dt = cspyce.spkapp(state.planet_id, et, 'J2000', obs_pv[:6].tolist(), 'LT')
    ddays = (et - ref_et - dt) / _SEC_PER_DAY
    peri_deg_list = []
    node_deg_list = []
    for r in cfg.rings:
        peri_deg = r.peri_rad * _RAD2DEG + r.dperi_dt * ddays + B1950_TO_J2000_URANUS
        node_deg = r.node_rad * _RAD2DEG + r.dnode_dt * ddays + B1950_TO_J2000_URANUS
        peri_deg = peri_deg % 360.0
        if peri_deg < 0.0:
            peri_deg += 360.0
        node_deg = node_deg % 360.0
        if node_deg < 0.0:
            node_deg += 360.0
        peri_deg_list.append(peri_deg)
        node_deg_list.append(node_deg)
    return (peri_deg_list, node_deg_list)


def _propagated_neptune_arcs(et: float, cfg: PlanetConfig) -> list[tuple[float, float]]:
    """Propagate Neptune arc longitudes to et (viewer3_*.f arc propagation).

    Parameters:
        et: Ephemeris time (seconds).
        cfg: Planet config with arcs (Neptune).

    Returns:
        List of (minlon_deg, maxlon_deg) per arc.
    """
    import cspyce

    from ephemeris_tools.spice.common import get_state
    from ephemeris_tools.spice.observer import observer_state
    from ephemeris_tools.time_utils import tai_from_jd, tdb_from_tai

    neptune_ref_jed = 2447757.0
    ref_tai = tai_from_jd(neptune_ref_jed)
    ref_et = tdb_from_tai(ref_tai)
    obs_pv = observer_state(et)
    state = get_state()
    _planet_dpv, dt = cspyce.spkapp(state.planet_id, et, 'J2000', obs_pv[:6].tolist(), 'LT')
    ddays = (et - ref_et - dt) / _SEC_PER_DAY
    b1950_to_j2000_nep = 0.334321
    result = []
    for arc in cfg.arcs:
        minlon = (arc.minlon_deg + arc.motion_deg_day * ddays + b1950_to_j2000_nep) % 360.0
        maxlon = (arc.maxlon_deg + arc.motion_deg_day * ddays + b1950_to_j2000_nep) % 360.0
        if minlon < 0.0:
            minlon += 360.0
        if maxlon < 0.0:
            maxlon += 360.0
        result.append((minlon, maxlon))
    return result


def _propagated_saturn_f_ring(et: float, cfg: PlanetConfig) -> tuple[float, float] | None:
    """Propagate Saturn F ring elements to et.

    Parameters:
        et: Ephemeris time (seconds).
        cfg: Planet config (Saturn with f_ring_index set).

    Returns:
        (peri_rad, node_rad) in radians, or None if not applicable.
    """
    if cfg.f_ring_index is None or cfg.planet_num != 6:
        return None
    import cspyce

    from ephemeris_tools.planets.saturn import FRING_DNODE_DT, FRING_DPERI_DT
    from ephemeris_tools.spice.common import get_state
    from ephemeris_tools.spice.observer import observer_state
    from ephemeris_tools.time_utils import tai_from_day_sec, tdb_from_tai

    ref_tai = tai_from_day_sec(0, 12.0 * 3600.0)
    ref_et = tdb_from_tai(ref_tai)
    obs_pv = observer_state(et)
    state = get_state()
    _planet_dpv, dt = cspyce.spkapp(state.planet_id, et, 'J2000', obs_pv[:6].tolist(), 'LT')
    ddays = (et - ref_et - dt) / _SEC_PER_DAY
    r = cfg.rings[cfg.f_ring_index]
    peri_rad = r.peri_rad + FRING_DPERI_DT * ddays * _SEC_PER_DAY
    node_rad = r.node_rad + FRING_DNODE_DT * ddays * _SEC_PER_DAY
    return (peri_rad, node_rad)


def _compute_ring_center_offsets(et: float, cfg: PlanetConfig) -> list[tuple[float, float, float]]:
    """Compute ring center offset vectors in J2000 km (viewer3_*.f ring_offsets).

    Parameters:
        et: Ephemeris time (seconds).
        cfg: Planet config with rings (Mars/Pluto use offsets).

    Returns:
        List of (x, y, z) offset in km per ring.
    """
    import cspyce

    from ephemeris_tools.constants import SUN_ID
    from ephemeris_tools.spice.common import get_state
    from ephemeris_tools.spice.observer import observer_state

    nrings = len(cfg.rings)
    offsets = [(0.0, 0.0, 0.0)] * nrings
    state = get_state()
    obs_pv = observer_state(et)

    if cfg.planet_num == 4 and cfg.ring_offsets_km:
        from ephemeris_tools.spice.bodmat import bodmat

        planet_dpv, dt = cspyce.spkapp(state.planet_id, et, 'J2000', obs_pv[:6].tolist(), 'LT')
        planet_time = et - dt
        planet_pv = cspyce.spkssb(state.planet_id, planet_time, 'J2000')
        sun_dpv, _ = cspyce.spkapp(SUN_ID, planet_time, 'J2000', planet_pv[:6], 'LT+S')
        rotmat = bodmat(state.planet_id, planet_time)
        eq_pole = (rotmat[2][0], rotmat[2][1], rotmat[2][2])
        anti_sun = (-sun_dpv[0], -sun_dpv[1], -sun_dpv[2])
        dot = eq_pole[0] * anti_sun[0] + eq_pole[1] * anti_sun[1] + eq_pole[2] * anti_sun[2]
        antisun = [
            anti_sun[0] - dot * eq_pole[0],
            anti_sun[1] - dot * eq_pole[1],
            anti_sun[2] - dot * eq_pole[2],
        ]
        n = math.sqrt(antisun[0] ** 2 + antisun[1] ** 2 + antisun[2] ** 2)
        if n > 1e-12:
            antisun = [antisun[0] / n, antisun[1] / n, antisun[2] / n]
            for i, shift_km in cfg.ring_offsets_km.items():
                if i < nrings:
                    offsets[i] = (
                        shift_km * antisun[0],
                        shift_km * antisun[1],
                        shift_km * antisun[2],
                    )

    if cfg.planet_num == 9 and cfg.barycenter_id is not None:
        bary_dpv, _ = cspyce.spkapp(cfg.barycenter_id, et, 'J2000', obs_pv[:6].tolist(), 'LT')
        planet_dpv, _ = cspyce.spkapp(state.planet_id, et, 'J2000', obs_pv[:6].tolist(), 'LT')
        dx = bary_dpv[0] - planet_dpv[0]
        dy = bary_dpv[1] - planet_dpv[1]
        dz = bary_dpv[2] - planet_dpv[2]
        for i in range(1, nrings):
            offsets[i] = (dx, dy, dz)

    return offsets


def _compute_jupiter_torus_node(et: float) -> float | None:
    """Compute Io torus ring node in radians from Jupiter BODMAT (System III 248°).

    Parameters:
        et: Ephemeris time (seconds).

    Returns:
        Node longitude in radians, or None if not Jupiter.
    """
    import cspyce

    from ephemeris_tools.spice.bodmat import bodmat
    from ephemeris_tools.spice.common import get_state
    from ephemeris_tools.spice.observer import observer_state

    state = get_state()
    if state.planet_num != 5:
        return None
    obs_pv = observer_state(et)
    _planet_dpv, dt = cspyce.spkapp(state.planet_id, et, 'J2000', obs_pv[:6].tolist(), 'LT')
    planet_time = et - dt
    rotmat = bodmat(state.planet_id, planet_time)
    eq_pole = [rotmat[2][0], rotmat[2][1], rotmat[2][2]]
    j2000_pole = [0.0, 0.0, 1.0]
    ascnode = cspyce.ucrss(j2000_pole, eq_pole)
    tempvec = cspyce.mxv(rotmat, ascnode)
    reflon = math.atan2(tempvec[1], tempvec[0])
    torus_node_rad = math.radians(248.0) - reflon
    return torus_node_rad


def get_planet_config(planet_num: int) -> PlanetConfig | None:
    """Return PlanetConfig for planet number (port of viewer3_* planet config).

    Parameters:
        planet_num: Planet index 4 (Mars) through 9 (Pluto).

    Returns:
        PlanetConfig or None if planet_num not supported.
    """
    return _PLANET_CONFIGS.get(planet_num)


def _ra_hms(ra_rad: float) -> str:
    """Format RA in radians as 'hh mm ss.ssss' (hours, 4 decimals in seconds)."""
    from ephemeris_tools.angle_utils import dms_string

    ra_deg = ra_rad * _RAD2DEG
    ra_h = (ra_deg / 15.0) % 24.0
    return dms_string(ra_h, 'hms', ndecimal=4)


def _dec_dms(dec_rad: float) -> str:
    """Format Dec in radians as 'dd mm ss.sss' (degrees)."""
    from ephemeris_tools.angle_utils import dms_string

    dec_deg = dec_rad * _RAD2DEG
    return dms_string(dec_deg, 'dms', ndecimal=3)


def _write_fov_table(
    stream: TextIO,
    et: float,
    cfg: PlanetConfig,
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

    stream.write('\n')
    stream.write('Field of View Description (J2000)\n')
    stream.write('---------------------------------\n')
    stream.write('\n')
    stream.write(
        '     Body          RA                 Dec              '
        '  RA (deg)   Dec (deg)   dRA (")   dDec (")\n'
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
            f'  {body_id:3d} {name:10s}  {ra_str:>18} {dec_str:>18}  '
            f'{ra_deg:10.6f} {dec_deg:12.6f} {dra_arcsec:10.4f} {ddec_arcsec:10.4f}\n'
        )

    stream.write('\n')
    stream.write('                   Sub-Observer    Sub-Solar     \n')
    lon_dir = cfg.longitude_direction
    stream.write(
        f'  Body       Lon(deg{lon_dir}) Lat(deg)  Lon(deg{lon_dir}) Lat(deg)  '
        'Phase(deg)  Distance(10^6 km)\n'
    )

    for body_id in body_ids:
        subobs_lon, subobs_lat, subsol_lon, subsol_lat = body_lonlat(et, body_id)
        phase = body_phase(et, body_id)
        _, obs_dist = body_ranges(et, body_id)
        name = id_to_name.get(body_id, str(body_id))
        stream.write(
            f'  {body_id:3d} {name:10s} '
            f'{subobs_lon * _RAD2DEG:10.3f}{subobs_lat * _RAD2DEG:10.3f} '
            f'{subsol_lon * _RAD2DEG:10.3f}{subsol_lat * _RAD2DEG:10.3f} '
            f'{phase * _RAD2DEG:13.5f} {obs_dist / 1e6:15.6f}\n'
        )

    # Ring geometry (if rings exist).
    if cfg.rings:
        from ephemeris_tools.spice.rings import ring_opening

        stream.write('\n')
        sun_dist, obs_dist = planet_ranges(et)
        phase_deg = planet_phase(et) * _RAD2DEG
        geom = ring_opening(et)
        sun_b_deg = geom.sun_b * _RAD2DEG
        sun_db_deg = geom.sun_db * _RAD2DEG
        litstr = '(lit)' if not geom.is_dark else '(unlit)'
        stream.write(
            f'  Ring sub-solar latitude (deg): {sun_b_deg:9.5f}  '
            f'({sun_b_deg - sun_db_deg:9.5f}  to  {sun_b_deg + sun_db_deg:9.5f})\n'
        )
        stream.write(f' Ring plane opening angle (deg): {geom.obs_b * _RAD2DEG:9.5f}  {litstr}\n')
        stream.write(f'  Ring center phase angle (deg): {phase_deg:9.5f}\n')
        stream.write(
            f'      Sub-solar longitude (deg): {geom.sun_long * _RAD2DEG:9.5f}  '
            'from ring plane ascending node\n'
        )
        stream.write(f'   Sub-observer longitude (deg): {geom.obs_long * _RAD2DEG:9.5f}\n')
        stream.write('\n')
        stream.write(f'       Sun-planet distance (AU): {sun_dist / _AU_KM:9.5f}\n')
        stream.write(f'  Observer-planet distance (AU): {obs_dist / _AU_KM:9.5f}\n')
        stream.write(f'       Sun-planet distance (km): {sun_dist / 1e6:12.6f} x 10^6\n')
        stream.write(f'  Observer-planet distance (km): {obs_dist / 1e6:12.6f} x 10^6\n')
        stream.write('\n')

        if cfg.f_ring_index is not None and cfg.planet_num == 6:
            propagated = _propagated_saturn_f_ring(et, cfg)
            if propagated is not None:
                peri_rad, node_rad = propagated
                peri_deg = (peri_rad * _RAD2DEG) % 360.0
                if peri_deg < 0.0:
                    peri_deg += 360.0
                node_deg = (node_rad * _RAD2DEG) % 360.0
                if node_deg < 0.0:
                    node_deg += 360.0
            else:
                ring = cfg.rings[cfg.f_ring_index]
                peri_deg = (ring.peri_rad * _RAD2DEG) % 360.0
                if peri_deg < 0.0:
                    peri_deg += 360.0
                node_deg = (ring.node_rad * _RAD2DEG) % 360.0
                if node_deg < 0.0:
                    node_deg += 360.0
            stream.write('\n')
            stream.write(
                f'      F Ring pericenter (deg): {peri_deg:9.5f}  from ring plane ascending node\n'
            )
            stream.write(f'  F Ring ascending node (deg): {node_deg:9.5f}\n')

    if cfg.rings and cfg.planet_num == 7:
        peri_deg_list, node_deg_list = _propagated_uranus_rings(et, cfg)
        stream.write('\n')
        stream.write(
            '     Ring          Pericenter   Ascending Node (deg, from ring plane ascending node)\n'
        )
        for i, r in enumerate(cfg.rings):
            name = (r.name or '')[:10].ljust(10)
            peri_deg = 0.0 if r.ecc == 0.0 else peri_deg_list[i]
            node_deg = 0.0 if r.inc_rad == 0.0 else node_deg_list[i]
            stream.write(f'     {name}   {peri_deg:8.3f}     {node_deg:8.3f}\n')

    if cfg.arcs and cfg.planet_num == 8:
        arc_minmax = _propagated_neptune_arcs(et, cfg)
        stream.write('\n')
        for i in range(len(cfg.arcs) - 1, -1, -1):
            minlon, maxlon = arc_minmax[i]
            arc = cfg.arcs[i]
            name = (arc.name or '')[:12].ljust(12)
            suffix = 'from ring plane ascending node' if i == len(cfg.arcs) - 1 else ''
            stream.write(f'  {name} longitude (deg): {minlon:9.5f}  to {maxlon:9.5f}  {suffix}\n')


# FOV unit multipliers (deg) when fov is scale factor. FORTRAN viewer3_*.f fov_unit parsing.
_FOV_UNIT_MULT_DEG = {
    'galileo': 8.1e-3,
    'galileo ssi': 8.1e-3,
    'cassini': 6.1e-3,
    'vims 64x64': 32e-3,
    'vims 12x12': 6e-3,
    'uvis slit': 59e-3,
    'lorri': 0.2907,
}


def _fov_deg_from_unit(fov: float, fov_unit: str | None) -> float:
    """Convert FOV to degrees using fov_unit (e.g. arcmin -> deg).

    Parameters:
        fov: FOV value in the given unit.
        fov_unit: Unit string (deg, arcmin, arcsec, etc.) or None for degrees.

    Returns:
        FOV in degrees.
    """
    if not fov_unit or 'fov' not in fov_unit.lower():
        return fov
    s = fov_unit.lower()
    for key, mult in sorted(_FOV_UNIT_MULT_DEG.items(), key=lambda kv: -len(kv[0])):
        if key in s:
            return fov * mult
    return fov


def run_viewer(
    planet_num: int,
    time_str: str,
    fov: float,
    center_ra: float,
    center_dec: float,
    viewpoint: str,
    ephem_version: int = 0,
    moon_ids: list[int] | None = None,
    blank_disks: bool = False,
    output_ps: TextIO | None = None,
    output_txt: TextIO | None = None,
    fov_unit: str | None = None,
) -> None:
    """Generate planet viewer PostScript diagram and FOV table (port of viewer3_*.f).

    Loads SPICE, sets observer, computes geometry, and draws planet/rings/moons.
    Writes PostScript to output_ps (if set) and FOV table to output_txt or stdout.

    Parameters:
        planet_num: Planet index 4-9.
        time_str: Observation time string (parseable by parse_datetime).
        fov: Field of view value; units from fov_unit.
        center_ra, center_dec: Center RA/Dec in degrees (0,0 = planet center).
        viewpoint: Observer viewpoint (e.g. Earth, latlon).
        ephem_version: SPICE ephemeris version or 0.
        moon_ids: Optional moon body IDs to show; None = all.
        blank_disks: If True, draw planet/ring disks as blank.
        output_ps: PostScript output stream; None = no PS.
        output_txt: FOV table stream; None = stdout.
        fov_unit: Optional unit string for fov (e.g. deg, arcmin).

    Raises:
        ValueError: Unknown planet or invalid time.
        RuntimeError: SPICE load failure.
    """
    cfg = get_planet_config(planet_num)
    if cfg is None:
        raise ValueError(f'Unknown planet number: {planet_num}')
    from ephemeris_tools.constants import EARTH_ID
    from ephemeris_tools.spice.geometry import body_radec, limb_radius
    from ephemeris_tools.spice.load import load_spice_files
    from ephemeris_tools.spice.observer import set_observer_id
    from ephemeris_tools.time_utils import parse_datetime, tai_from_day_sec, tdb_from_tai

    ok, reason = load_spice_files(planet_num, ephem_version)
    if not ok:
        raise RuntimeError(f'Failed to load SPICE kernels: {reason}')
    set_observer_id(EARTH_ID)

    parsed = parse_datetime(time_str)
    if parsed is None:
        raise ValueError(f'Invalid time: {time_str!r}')
    day, sec = parsed
    et = tdb_from_tai(tai_from_day_sec(day, sec))

    fov_deg = _fov_deg_from_unit(fov, fov_unit)
    fov_rad = fov_deg * _DEG2RAD

    _, _limb_rad_rad = limb_radius(et)
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
    table_body_ids = [cfg.planet_id, *track_moon_ids]
    if not output_txt:
        _write_fov_table(sys.stdout, et, cfg, planet_ra, planet_dec, table_body_ids, id_to_name)
    if output_txt:
        _write_fov_table(output_txt, et, cfg, planet_ra, planet_dec, table_body_ids, id_to_name)

    # Plot: FOV_PTS diameter, scale = FOV_PTS / (2*tan(fov/2)) for camera projection.
    from ephemeris_tools.rendering.draw_view import FOV_PTS, radec_to_plot

    scale = FOV_PTS / (2.0 * math.tan(fov_rad / 2.0))

    def to_plot(ra: float, dec: float) -> tuple[float, float]:
        return radec_to_plot(ra, dec, center_ra_rad, center_dec_rad, fov_rad)

    bodies: list[tuple[float, float, str, bool]] = []
    px, py = to_plot(planet_ra, planet_dec)
    bodies.append((px, py, cfg.planet_name, True))

    for mid in track_moon_ids:
        ra, dec = body_radec(et, mid)
        mx, my = to_plot(ra, dec)
        name = id_to_name.get(mid, str(mid))
        bodies.append((mx, my, name.upper(), False))

    # FORTRAN: title from CGI 'title' key; when absent, keep blank so caption order matches.
    title = ''

    if not blank_disks:
        from ephemeris_tools.rendering.planet_grid import compute_planet_grid

        compute_planet_grid(
            et,
            cfg.planet_id,
            center_ra_rad,
            center_dec_rad,
            scale,
        )

    if output_ps:
        from ephemeris_tools.rendering.draw_view import draw_planetary_view
        from ephemeris_tools.spice.geometry import body_lonlat, body_phase

        # Build caption strings matching FORTRAN viewer3_*.f exactly
        # In FORTRAN, lcaptions use ':' suffix, rcaptions come from CGI params
        lc: list[str] = []
        rc: list[str] = []

        # Caption 1: Time (UTC)
        lc.append('Time (UTC):')
        rc.append(time_str)

        # Caption 2: Ephemeris — show kernel description (FORTRAN uses ephem string(5:))
        lc.append('Ephemeris:')
        from ephemeris_tools.constants import EPHEM_DESCRIPTIONS_BY_PLANET

        ephem_caption = EPHEM_DESCRIPTIONS_BY_PLANET.get(planet_num, 'DE440')
        rc.append(ephem_caption)

        # Caption 3: Viewpoint
        lc.append('Viewpoint:')
        viewpoint_display = (
            "Earth's center"
            if 'earth' in viewpoint.lower() or viewpoint == 'observatory'
            else viewpoint
        )
        # FORTRAN appends ' (sc_trajectory(5:))' if sc_trajectory key found
        # For default case with sc_trajectory=0, CGI value "0" → (5:) is blank
        # So output is "Earth's center ()" for typical case
        rc.append(viewpoint_display + ' ()')

        # Caption 4: Moon selection — FORTRAN uses moons CGI value(5:)
        lc.append('Moon selection:')
        # When no moons specified in CGI, the value is blank → (5:) is blank
        rc.append('')

        # Caption 5: Ring selection — from rings CGI value, typically blank
        lc.append('Ring selection:')
        rc.append('')

        # Caption 6: Center body (lon,lat)
        center_body_id = cfg.planet_id  # Default center is planet
        subobs_lon, subobs_lat, _sslon, _sslat = body_lonlat(et, center_body_id)
        lon_dir = cfg.longitude_direction if hasattr(cfg, 'longitude_direction') else 'W'
        lon_deg = subobs_lon * _RAD2DEG
        lat_deg = subobs_lat * _RAD2DEG
        lc.append(f'{cfg.planet_name} center (lon,lat):')
        # FORTRAN format: ('(',f7.3,'\260 ',a1,',',f7.3,'\260)')
        rc.append(f'({lon_deg:7.3f}\\260 {lon_dir},{lat_deg:7.3f}\\260)')

        # Caption 7: Phase angle
        phase_rad = body_phase(et, center_body_id)
        phase_deg = phase_rad * _RAD2DEG
        lc.append(f'{cfg.planet_name} phase angle: ')
        # FORTRAN format: (f7.3,'\260') → e.g. '  2.920\260'
        rc.append(f'{phase_deg:7.3f}\\260')

        ncaptions = len(lc)

        # Build moon arrays for RSPK_DrawView
        # FORTRAN passes moon_flags(0:NMOONS) where 0 = planet (always False)
        all_moons = [m for m in cfg.moons if m.id != cfg.planet_id]
        f_nmoons = len(all_moons) + 1  # +1 because FORTRAN includes planet as index 0
        f_moon_flags = [False]  # index 0 = planet, always False
        f_moon_ids = [cfg.planet_id]
        f_moon_names = [' ']
        for m in all_moons:
            f_moon_flags.append(True)  # Show all moons by default
            f_moon_ids.append(m.id)
            f_moon_names.append(m.name)

        # Filter moons if specific ones requested
        if moon_ids:
            for i in range(1, len(f_moon_ids)):
                if f_moon_ids[i] not in moon_ids:
                    f_moon_flags[i] = False

        # Build ring arrays
        f_nrings = len(cfg.rings) if hasattr(cfg, 'rings') and cfg.rings else 0
        f_ring_flags: list[bool] = []
        f_ring_rads: list[float] = []
        f_ring_elevs: list[float] = []
        f_ring_eccs: list[float] = []
        f_ring_incs: list[float] = []
        f_ring_peris: list[float] = []
        f_ring_nodes: list[float] = []
        f_ring_offsets: list[list[float]] = []
        f_ring_opaqs: list[bool] = []
        f_ring_dashed: list[bool] = []

        if hasattr(cfg, 'rings') and cfg.rings:
            ring_offset_list = _compute_ring_center_offsets(et, cfg)
            for i, r in enumerate(cfg.rings):
                f_ring_flags.append(not r.dashed)  # FORTRAN: dashed rings hidden by default
                f_ring_rads.append(r.outer_km)
                f_ring_elevs.append(getattr(r, 'elev_km', 0.0))
                f_ring_eccs.append(getattr(r, 'ecc', 0.0))
                f_ring_incs.append(getattr(r, 'inc_rad', 0.0))
                f_ring_peris.append(getattr(r, 'peri_rad', 0.0))
                f_ring_nodes.append(getattr(r, 'node_rad', 0.0))
                f_ring_offsets.append(
                    list(ring_offset_list[i]) if i < len(ring_offset_list) else [0.0, 0.0, 0.0]
                )
                f_ring_opaqs.append(getattr(r, 'opaque', False))
                f_ring_dashed.append(getattr(r, 'dashed', False))

        draw_planetary_view(
            output_ps,
            obs_time=et,
            fov=fov_rad,
            center_ra=center_ra_rad,
            center_dec=center_dec_rad,
            planet_name=cfg.planet_name,
            blank_disks=blank_disks,
            prime_pts=0.0,
            nmoons=f_nmoons,
            moon_flags=f_moon_flags,
            moon_ids=f_moon_ids,
            moon_names=f_moon_names,
            moon_labelpts=6.0,
            moon_diampts=3.0,
            nrings=f_nrings,
            ring_flags=f_ring_flags,
            ring_rads=f_ring_rads,
            ring_elevs=f_ring_elevs,
            ring_eccs=f_ring_eccs,
            ring_incs=f_ring_incs,
            ring_peris=f_ring_peris,
            ring_nodes=f_ring_nodes,
            ring_offsets=f_ring_offsets,
            ring_opaqs=f_ring_opaqs,
            ring_dashed=f_ring_dashed,
            ring_method=0,
            title=title,
            ncaptions=ncaptions,
            lcaptions=lc,
            rcaptions=rc,
            align_loc=108.0,
        )
