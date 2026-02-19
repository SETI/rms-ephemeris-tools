"""Planet viewer tool: PostScript diagram and tables (port of viewer3_*.f)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any, TextIO, TypedDict, cast

from ephemeris_tools.constants import (
    ARCMIN_PER_DEGREE,
    ARCSEC_PER_DEGREE,
    DEGREES_PER_CIRCLE,
    HALF_CIRCLE_DEGREES,
    NOON_SECONDS_OFFSET,
    SECONDS_PER_DAY,
)
from ephemeris_tools.planets import (
    JUPITER_CONFIG,
    MARS_CONFIG,
    NEPTUNE_CONFIG,
    PLUTO_CONFIG,
    SATURN_CONFIG,
    URANUS_CONFIG,
)

if TYPE_CHECKING:
    from ephemeris_tools.planets.base import PlanetConfig, RingSpec

# Import for viewer_params_from_legacy_kwargs (runtime).
from ephemeris_tools.params import (
    ExtraStar,
    Observer,
    ViewerCenter,
    ViewerDisplayInfo,
    ViewerParams,
)


class _RunViewerKwargs(TypedDict, total=True):
    """Keyword arguments for run_viewer (legacy signature from ViewerParams)."""

    planet_num: int
    time_str: str
    fov: float
    center_mode: str
    center_ra: float
    center_dec: float
    center_body_name: str | None
    center_ansa_name: str | None
    center_ansa_ew: str
    viewpoint: str
    ephem_version: int
    moon_ids: list[int] | None
    moon_selection_display: str | None
    blank_disks: bool
    ring_selection: list[str] | None
    ring_selection_display: str | None
    output_ps: TextIO | None
    output_txt: TextIO | None
    fov_unit: str | None
    observer_latitude: float | None
    observer_longitude: float | None
    observer_altitude: float | None
    observer_lon_dir: str
    viewpoint_display: str | None
    labels: str | None
    moon_points: float
    meridian_points: float
    opacity: str
    peris: str
    peripts: float
    arcmodel: str | None
    arcpts: float
    torus: bool
    torus_inc: float
    torus_rad: float
    extra_star_name: str | None
    extra_star_ra_deg: float | None
    extra_star_dec_deg: float | None
    other_bodies: list[str] | None
    title: str


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
_RAD2ARCSEC = 180.0 / math.pi * ARCSEC_PER_DEGREE
_AU_KM = 149597870.7
_MAX_ARCSEC = DEGREES_PER_CIRCLE * ARCSEC_PER_DEGREE
_SEC_PER_DAY = SECONDS_PER_DAY
_PLUTO_CHARON_SEP_KM = 19571.0
# Moon label point sizes for small/medium/large selection (FORTRAN labelpts)
_MOON_LABEL_SMALL_PTS = 6.0
_MOON_LABEL_MEDIUM_PTS = 9.0
_MOON_LABEL_LARGE_PTS = 12.0


def _fortran_nint(value: float) -> int:
    """Return FORTRAN-compatible nearest integer (ties away from zero)."""
    return int(value + 0.5) if value >= 0.0 else int(value - 0.5)


def _fortran_fixed(value: float, decimals: int) -> str:
    """Format a float with FORTRAN tie-away rounding and fixed decimals."""
    scale = 10**decimals
    rounded = _fortran_nint(value * scale) / scale
    return f'{rounded:.{decimals}f}'


def _label_points_from_selection(labels: str | None) -> float:
    """Convert CGI label size selection to point size."""
    if labels is None:
        return 0.0
    s = labels.strip().lower()
    if 'small' in s:
        return _MOON_LABEL_SMALL_PTS
    if 'medium' in s:
        return _MOON_LABEL_MEDIUM_PTS
    if 'large' in s:
        return _MOON_LABEL_LARGE_PTS
    return 0.0


def _ring_method_from_opacity(opacity: str | None) -> int:
    """Map CGI opacity selection to FORTRAN ring method integer."""
    if opacity is None:
        return 0
    selection = opacity.strip()
    if selection == 'Transparent':
        return 0
    if 'Semi-' in selection:
        return 1
    if selection == 'Opaque':
        return 2
    return 0


def _neptune_arc_model_index(arcmodel: str | None) -> int:
    """Return Neptune arc model index (1..3) from CGI arcmodel string."""
    if arcmodel is None:
        return 3
    if '#1' in arcmodel:
        return 1
    if '#2' in arcmodel:
        return 2
    if '#3' in arcmodel:
        return 3
    return 3


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

    def _norm_deg(deg: float) -> float:
        deg = deg % DEGREES_PER_CIRCLE
        return deg + DEGREES_PER_CIRCLE if deg < 0.0 else deg

    peri_deg_list = [
        _norm_deg(r.peri_rad * _RAD2DEG + r.dperi_dt * ddays + B1950_TO_J2000_URANUS)
        for r in cfg.rings
    ]
    node_deg_list = [
        _norm_deg(r.node_rad * _RAD2DEG + r.dnode_dt * ddays + B1950_TO_J2000_URANUS)
        for r in cfg.rings
    ]
    return (peri_deg_list, node_deg_list)


def _propagated_neptune_arcs(
    et: float,
    cfg: PlanetConfig,
    *,
    arc_model_index: int = 3,
) -> list[tuple[float, float]]:
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
    arc_motion_deg_day = [820.1194, 820.1118, 820.1121][max(1, min(3, arc_model_index)) - 1]
    for arc in cfg.arcs:
        minlon = (
            arc.minlon_deg + arc_motion_deg_day * ddays + b1950_to_j2000_nep
        ) % DEGREES_PER_CIRCLE
        maxlon = (
            arc.maxlon_deg + arc_motion_deg_day * ddays + b1950_to_j2000_nep
        ) % DEGREES_PER_CIRCLE
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

    ref_tai = tai_from_day_sec(0, NOON_SECONDS_OFFSET)
    ref_et = tdb_from_tai(ref_tai)
    obs_pv = observer_state(et)
    state = get_state()
    _planet_dpv, dt = cspyce.spkapp(state.planet_id, et, 'J2000', obs_pv[:6].tolist(), 'LT')
    # FORTRAN uses: (obs_time - ref_time - dt) in seconds directly
    elapsed_sec = et - ref_et - dt
    r = cfg.rings[cfg.f_ring_index]
    peri_rad = r.peri_rad + FRING_DPERI_DT * elapsed_sec
    node_rad = r.node_rad + FRING_DNODE_DT * elapsed_sec
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

        _planet_dpv, dt = cspyce.spkapp(state.planet_id, et, 'J2000', obs_pv[:6].tolist(), 'LT')
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


def _compute_mars_deimos_ring_node(et: float) -> float | None:
    """Compute Mars Deimos ring node longitude in radians.

    This mirrors the FORTRAN `viewer3_mar.f` logic used for `ring_nodes(3:4)`,
    where node longitude is measured relative to the equator ascending node.
    """
    import cspyce

    from ephemeris_tools.spice.bodmat import bodmat
    from ephemeris_tools.spice.common import get_state
    from ephemeris_tools.spice.observer import observer_state

    state = get_state()
    if state.planet_num != 4:
        return None

    obs_pv = observer_state(et)
    _planet_dpv, dt = cspyce.spkapp(state.planet_id, et, 'J2000', obs_pv[:6].tolist(), 'LT')
    planet_time = et - dt
    planet_pv = cspyce.spkssb(state.planet_id, planet_time, 'J2000')
    rotmat = bodmat(state.planet_id, planet_time)

    # FORTRAN uses the third row of BODMAT as equator pole in J2000.
    eq_pole = [rotmat[2][0], rotmat[2][1], rotmat[2][2]]
    j2000_pole = [0.0, 0.0, 1.0]

    def _cross(a: list[float], b: list[float]) -> list[float]:
        return [
            a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0],
        ]

    # Equator ascending node in body frame -> reference longitude.
    ascnode_eq = _cross(j2000_pole, eq_pole)
    tempvec = cspyce.mxv(rotmat, ascnode_eq)
    reflon = math.atan2(tempvec[1], tempvec[0])

    # Orbit-plane ascending node in body frame -> Deimos ring node longitude.
    orbit_pole = _cross(list(planet_pv[:3]), list(planet_pv[3:6]))
    ascnode_orbit = _cross(orbit_pole, eq_pole)
    tempvec = cspyce.mxv(rotmat, ascnode_orbit)
    nodelon = math.atan2(tempvec[1], tempvec[0])

    return nodelon - reflon


# Uranus viewer form option 71 = "Alpha, Beta, Eta, Gamma, Delta, Epsilon" (six major rings).
_URANUS_OPTION_71_NAMES: frozenset[str] = frozenset(
    {'Alpha', 'Beta', 'Eta', 'Gamma', 'Delta', 'Epsilon'}
)

_NEPTUNE_RING_NAME_TO_INDEX: dict[str, int] = {
    'galle': 0,
    'leverrier': 1,
    'arago': 2,
    'adams': 3,
}

_PLUTO_RING_NAME_TO_INDEX: dict[str, int] = {
    'charon': 0,
    'nix': 1,
    'hydra': 2,
    'kerberos': 3,
    'styx': 4,
}


def _resolve_viewer_ring_flags(
    planet_num: int,
    ring_selection: list[str],
    rings: list[RingSpec],
) -> list[bool]:
    """Resolve ring selection tokens to per-ring visibility flags.

    Each token may be a numeric group code (e.g. ``71`` for all six
    major Uranus rings) or an individual ring name that is matched
    case-insensitively against the config ring entries.  Group codes
    are the same codes used by the FORTRAN web form (51, 52, 61, 62,
    63, 71, 81).

    Parameters:
        planet_num: Planet number (4-9).
        ring_selection: Raw tokens from the CLI (e.g. ``['alpha']``,
            ``['71']``, ``['alpha', 'beta']``).
        rings: List of RingSpec from planet config.

    Returns:
        One bool per ring; True = draw.
    """
    n = len(rings)
    if n == 0:
        return []
    flags = [False] * n
    if planet_num == 7:
        # FORTRAN viewer3_ura.f initializes baseline Uranus ring flags before
        # parsing user-selected ring groups.
        for i in (3, 4, 5, 6, 7, 9, 10):
            if i < n:
                flags[i] = True

    # Split tokens into numeric group codes and individual ring names
    codes: list[int] = []
    names: set[str] = set()
    for tok in ring_selection:
        tok = tok.strip()
        if len(tok) == 0:
            continue
        try:
            codes.append(int(tok))
        except ValueError:
            names.add(tok.lower())

    # Apply numeric group codes (FORTRAN form compatibility)
    for opt in codes:
        if planet_num == 5:
            # Jupiter (viewer3_jup.f):
            # 51 Main -> ring flags 1,2 ; 52 Gossamer -> ring flags 3,4,5,6.
            if opt == 51:
                for i in (0, 1):
                    if i < n:
                        flags[i] = True
            elif opt == 52:
                for i in (2, 3, 4, 5):
                    if i < n:
                        flags[i] = True
        elif planet_num == 6:
            # Saturn: 61=Main (0), 62=G+E (1,2), 63=outer (3,4)
            if opt == 61 and n > 0:
                flags[0] = True
            elif opt == 62 and n >= 3:
                flags[1] = True
                flags[2] = True
            elif opt == 63 and n >= 5:
                flags[3] = True
                flags[4] = True
        elif planet_num == 7 and opt == 71:
            for i, r in enumerate(rings):
                if r.name in _URANUS_OPTION_71_NAMES:
                    flags[i] = True
        elif planet_num == 8 and opt == 81:
            # Neptune: 81=rings (LeVerrier, Adams; show all 4 by default)
            for i in range(n):
                flags[i] = True

    # Apply individual ring names (case-insensitive match against config)
    if names:
        if planet_num == 7:
            # Match FORTRAN viewer3_ura.f group semantics exactly.
            if 'nine major rings' in names:
                for i in (0, 1, 2):
                    if i < n:
                        flags[i] = True
            if 'all inner rings' in names:
                for i in (0, 1, 2, 8):
                    if i < n:
                        flags[i] = True
            if 'all rings' in names:
                for i in (0, 1, 2, 8, 11, 12, 13, 14, 15, 16):
                    if i < n:
                        flags[i] = True
        elif 'all rings' in names:
            for i in range(n):
                flags[i] = True
        if planet_num == 6:
            # FORTRAN viewer3_sat.f keeps A/B/C rings enabled.
            if {'a', 'b', 'c'} & names:
                for i in range(min(5, n)):
                    flags[i] = True
            # Saturn optional groups: F (6), G (7/8), E (9), FORTRAN 1-based.
            if 'f' in names and n > 5:
                flags[5] = True
            if 'g' in names:
                if n > 6:
                    flags[6] = True
                if n > 7:
                    flags[7] = True
            if 'e' in names and n > 8:
                flags[8] = True
        if planet_num == 8:
            for name, idx in _NEPTUNE_RING_NAME_TO_INDEX.items():
                if name in names and idx < n:
                    flags[idx] = True
        if planet_num == 5:
            if any('main' in name for name in names):
                for i in (0, 1):
                    if i < n:
                        flags[i] = True
            if any('gossamer' in name for name in names):
                for i in (2, 3, 4, 5):
                    if i < n:
                        flags[i] = True
        if planet_num == 9:
            for name, idx in _PLUTO_RING_NAME_TO_INDEX.items():
                if name in names and idx < n:
                    flags[idx] = True
        if planet_num == 4:
            # Mars ring selections are moon names mapped to ring-pair indices.
            if 'phobos' in names and n >= 2:
                flags[0] = True
                flags[1] = True
            if 'deimos' in names and n >= 4:
                flags[2] = True
                flags[3] = True
        for i, r in enumerate(rings):
            ring_name = r.name
            if ring_name is not None and ring_name.lower() in names:
                flags[i] = True

    return flags


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
    *,
    et: float,
    cfg: PlanetConfig,
    planet_ra: float,
    planet_dec: float,
    body_ids: list[int],
    id_to_name: dict[int, str],
    neptune_arc_model: int = 3,
    ring_names: list[str] | None = None,
) -> None:
    """Write Field of View Description (J2000) and body/ring geometry tables."""
    from ephemeris_tools.constants import EARTH_ID
    from ephemeris_tools.spice.common import get_state
    from ephemeris_tools.spice.geometry import (
        body_lonlat,
        body_phase,
        body_radec,
        body_ranges,
        planet_phase,
        planet_ranges,
    )

    cosdec = math.cos(planet_dec)

    # FORTRAN uses arcsec for Earth observer, degrees for spacecraft
    state = get_state()
    is_earth_observer = state.obs_id == EARTH_ID or state.obs_id == 0

    stream.write('\n')
    stream.write('Field of View Description (J2000)\n')
    stream.write('---------------------------------\n')
    stream.write('\n')
    if is_earth_observer:
        stream.write(
            '     Body          RA                  Dec                  '
            'RA (deg)   Dec (deg)    dRA (")   dDec (")\n'
        )
    else:
        stream.write(
            '     Body          RA                  Dec                  '
            'RA (deg)   Dec (deg)   dRA (deg)  dDec (deg)\n'
        )

    for body_id in body_ids:
        ra, dec = body_radec(et, body_id)
        if is_earth_observer:
            dra_display = (ra - planet_ra) * cosdec * _RAD2ARCSEC
            ddec_display = (dec - planet_dec) * _RAD2ARCSEC
            if dra_display < -0.5 * _MAX_ARCSEC:
                dra_display += _MAX_ARCSEC
            if dra_display > 0.5 * _MAX_ARCSEC:
                dra_display -= _MAX_ARCSEC
        else:
            dra_display = (ra - planet_ra) * cosdec * _RAD2DEG
            ddec_display = (dec - planet_dec) * _RAD2DEG
            if dra_display < -HALF_CIRCLE_DEGREES:
                dra_display += DEGREES_PER_CIRCLE
            if dra_display > HALF_CIRCLE_DEGREES:
                dra_display -= DEGREES_PER_CIRCLE
        ra_deg = ra * _RAD2DEG
        dec_deg = dec * _RAD2DEG
        name = id_to_name.get(body_id, str(body_id))
        ra_str = _ra_hms(ra)
        dec_str = _dec_dms(dec)
        if is_earth_observer:
            fmt = (
                f' {body_id:3d} {name:10s}  {ra_str:>18} {dec_str:>18}    '
                f'{ra_deg:10.6f}{dec_deg:12.6f} {dra_display:10.4f} {ddec_display:10.4f}\n'
            )
        else:
            fmt = (
                f' {body_id:3d} {name:10s}  {ra_str:>18} {dec_str:>18}    '
                f'{ra_deg:10.6f}{dec_deg:12.6f} {dra_display:11.6f} {ddec_display:11.6f}\n'
            )
        stream.write(fmt)

    stream.write('\n')
    stream.write('                   Sub-Observer  ' + '       ' + 'Sub-Solar     \n')
    lon_dir = cfg.longitude_direction
    stream.write(
        f'     Body          Lon(deg{lon_dir}) Lat(deg)   Lon(deg{lon_dir}) Lat(deg)   '
        f'Phase(deg)   Distance(10^6 km)\n'
    )

    for body_id in body_ids:
        subobs_lon, subobs_lat, subsol_lon, subsol_lat = body_lonlat(et, body_id)
        phase = body_phase(et, body_id)
        _, obs_dist = body_ranges(et, body_id)
        name = id_to_name.get(body_id, str(body_id))
        stream.write(
            f' {body_id:3d} {name:10s} '
            f'{subobs_lon * _RAD2DEG:10.3f}{subobs_lat * _RAD2DEG:10.3f} '
            f'{subsol_lon * _RAD2DEG:10.3f}{subsol_lat * _RAD2DEG:10.3f}'
            f'{phase * _RAD2DEG:13.5f}{obs_dist / 1e6:15.6f}\n'
        )

    # Ring table and geometry (if rings exist). Order: ring table first, then sub-solar lat etc.
    if cfg.rings:
        # Uranus: pericenter/ascending node table first (FORTRAN: first 10 rings only).
        if cfg.planet_num == 7:
            peri_deg_list, node_deg_list = _propagated_uranus_rings(et, cfg)
            stream.write('\n')
            stream.write(
                '     Ring          Pericenter   Ascending Node (deg, from ring plane '
                'ascending node)\n'
            )
            n_uranus_table = 10
            for i, r in enumerate(cfg.rings[:n_uranus_table]):
                name = (r.name or '')[:10].ljust(10)
                peri_deg = 0.0 if r.ecc == 0.0 else peri_deg_list[i]
                node_deg = 0.0 if r.inc_rad == 0.0 else node_deg_list[i]
                stream.write(f'     {name}   {peri_deg:8.3f}     {node_deg:8.3f}\n')

        # Resolve ring selection for Saturn F ring block (written after sun-planet table).
        ring_flags = (
            _resolve_viewer_ring_flags(cfg.planet_num, ring_names or [], cfg.rings)
            if ring_names is not None
            else []
        )
        f_ring_selected = (
            cfg.f_ring_index is not None
            and cfg.planet_num == 6
            and cfg.f_ring_index < len(cfg.rings)
            and cfg.f_ring_index < len(ring_flags)
            and ring_flags[cfg.f_ring_index]
        )

        # Ring geometry: sub-solar latitude, opening angle, phase, longitudes, distances.
        from ephemeris_tools.spice.rings import ring_opening

        stream.write('\n')
        sun_dist, obs_dist = planet_ranges(et)
        phase_deg = planet_phase(et) * _RAD2DEG
        geom = ring_opening(et)
        sun_b_deg = geom.sun_b * _RAD2DEG
        sun_db_deg = geom.sun_db * _RAD2DEG
        litstr = '(lit)' if not geom.is_dark else '(unlit)'
        stream.write(
            f'   Ring sub-solar latitude (deg): {sun_b_deg:9.5f}  '
            f'({sun_b_deg - sun_db_deg:9.5f}  to {sun_b_deg + sun_db_deg:9.5f})\n'
        )
        stream.write(f'  Ring plane opening angle (deg): {geom.obs_b * _RAD2DEG:9.5f}  {litstr}\n')
        stream.write(f'   Ring center phase angle (deg): {phase_deg:9.5f}\n')
        stream.write(
            f'       Sub-solar longitude (deg): {geom.sun_long * _RAD2DEG:9.5f}  '
            'from ring plane ascending node\n'
        )
        stream.write(f'    Sub-observer longitude (deg): {geom.obs_long * _RAD2DEG:9.5f}\n')
        stream.write('\n')
        stream.write(f'        Sun-planet distance (AU): {sun_dist / _AU_KM:9.5f}\n')
        stream.write(f'   Observer-planet distance (AU): {obs_dist / _AU_KM:9.5f}\n')
        stream.write(f'        Sun-planet distance (km): {sun_dist / 1e6:12.6f} x 10^6\n')
        stream.write(f'   Observer-planet distance (km): {obs_dist / 1e6:12.6f} x 10^6\n')
        light_time_sec = obs_dist / 299792.458
        stream.write(f'         Light travel time (sec): {light_time_sec:12.6f}\n')
        stream.write('\n')

        # Saturn: F ring pericenter/node when selected (after sun-planet table).
        if f_ring_selected:
            propagated = _propagated_saturn_f_ring(et, cfg)
            if propagated is not None:
                peri_rad, node_rad = propagated
                peri_deg = (peri_rad * _RAD2DEG) % 360.0
                node_deg = (node_rad * _RAD2DEG) % 360.0
            else:
                if cfg.f_ring_index is not None:
                    ring = cfg.rings[cfg.f_ring_index]
                    peri_deg = (ring.peri_rad * _RAD2DEG) % 360.0
                    node_deg = (ring.node_rad * _RAD2DEG) % 360.0
                else:
                    peri_deg = 0.0
                    node_deg = 0.0
            stream.write(
                f'      F Ring pericenter (deg): {peri_deg:9.5f}  from ring plane ascending node\n'
            )
            stream.write(f'  F Ring ascending node (deg): {node_deg:9.5f}\n')
            stream.write('\n')

    if cfg.arcs and cfg.planet_num == 8:
        arc_minmax = _propagated_neptune_arcs(et, cfg, arc_model_index=neptune_arc_model)
        stream.write('\n')
        for i in range(len(cfg.arcs) - 1, -1, -1):
            minlon, maxlon = arc_minmax[i]
            arc = cfg.arcs[i]
            name = (arc.name or '')[:12].ljust(12)
            suffix = 'from ring plane ascending node' if i == len(cfg.arcs) - 1 else ''
            stream.write(f'  {name} longitude (deg): {minlon:9.5f}  to {maxlon:9.5f}  {suffix}\n')


# FOV unit multipliers (deg) when fov is scale factor. FORTRAN viewer3_*.f fov_unit parsing.
_FOV_UNIT_MULT_DEG = {
    'galileo': 8.1e-3 * _RAD2DEG,
    'galileo ssi': 8.1e-3 * _RAD2DEG,
    'cassini iss wide': 61.2e-3 * _RAD2DEG,
    'cassini iss narrow': 6.1e-3 * _RAD2DEG,
    'cassini': 6.1e-3 * _RAD2DEG,
    'vims 64x64': 32e-3 * _RAD2DEG,
    'vims 12x12': 6e-3 * _RAD2DEG,
    'uvis slit': 59e-3 * _RAD2DEG,
    'lorri': 0.2907,
    'voyager iss narrow': 7.292e-3 * _RAD2DEG,
    'voyager iss wide': 5.463e-2 * _RAD2DEG,
}


def _fov_deg_from_unit(
    fov: float,
    fov_unit: str | None,
    *,
    et: float | None = None,
    cfg: PlanetConfig | None = None,
) -> float:
    """Convert FOV to degrees using fov_unit (e.g. arcmin -> deg).

    Parameters:
        fov: FOV value in the given unit.
        fov_unit: Unit string (deg, arcmin, arcsec, etc.) or None for degrees.

    Returns:
        FOV in degrees.
    """
    if fov_unit is None or len(fov_unit) == 0:
        return fov
    s = fov_unit.lower()
    if 'radii' in s and et is not None and cfg is not None:
        from ephemeris_tools.spice.geometry import planet_ranges

        _sun_dist_km, obs_dist_km = planet_ranges(et)
        if obs_dist_km > 0:
            ratio = cfg.equatorial_radius_km / obs_dist_km
            clamped = max(-1.0, min(1.0, ratio))
            return fov * math.asin(clamped) * _RAD2DEG
        return fov
    if ('pluto-charon separation' in s or 'pluto charon separation' in s) and et is not None:
        from ephemeris_tools.spice.geometry import planet_ranges

        _sun_dist_km, obs_dist_km = planet_ranges(et)
        if obs_dist_km > 0:
            ratio = _PLUTO_CHARON_SEP_KM / obs_dist_km
            clamped = max(-1.0, min(1.0, ratio))
            return fov * math.asin(clamped) * _RAD2DEG
        return fov
    if ('kilometer' in s or s.strip() == 'km') and et is not None:
        from ephemeris_tools.spice.geometry import planet_ranges

        _sun_dist_km, obs_dist_km = planet_ranges(et)
        if obs_dist_km > 0:
            ratio = 1.0 / obs_dist_km
            clamped = max(-1.0, min(1.0, ratio))
            return fov * math.asin(clamped) * _RAD2DEG
        return fov
    if s in ('deg', 'degree', 'degrees'):
        return fov
    if s in ('arcmin', 'minutes of arc', 'minute of arc'):
        return fov / ARCMIN_PER_DEGREE
    if s in ('arcsec', 'seconds of arc', 'second of arc'):
        return fov / ARCSEC_PER_DEGREE
    if s in ('milliradians', 'milliradian', 'mrad'):
        return fov * (_RAD2DEG / 1000.0)
    if s in ('microradians', 'microradian', 'urad'):
        return fov * (_RAD2DEG / 1_000_000.0)
    for key, mult in sorted(_FOV_UNIT_MULT_DEG.items(), key=lambda kv: -len(kv[0])):
        if key in s:
            return fov * mult
    return fov


def _normalize_body_name(name: str) -> str:
    """Normalize body-like names for forgiving CGI matching."""
    return name.split('(')[0].strip().lower()


def _resolve_center_body_id(cfg: PlanetConfig, center_body_name: str | None) -> int:
    """Resolve center body name to NAIF ID, defaulting to the planet."""
    if center_body_name is None or center_body_name.strip() == '':
        return cfg.planet_id
    wanted = _normalize_body_name(center_body_name)
    if wanted == _normalize_body_name(cfg.planet_name):
        return cfg.planet_id
    for moon in cfg.moons:
        if moon.id == cfg.planet_id:
            continue
        if _normalize_body_name(moon.name) == wanted:
            return moon.id
    return cfg.planet_id


def _resolve_center_ansa_radius_km(cfg: PlanetConfig, center_ansa_name: str | None) -> float | None:
    """Resolve center ring ansa name to a representative ring radius."""
    if center_ansa_name is None or center_ansa_name.strip() == '':
        return None
    target = center_ansa_name.lower().replace(' ring', '').strip()
    # Jupiter viewer rings are named in FORTRAN but unnamed in Python config.
    if cfg.planet_num == 5:
        jupiter_radius_map = {
            'halo': 122000.0,
            'main': 129000.0,
            'amalthea': 181350.0,
            'thebe': 221900.0,
        }
        if target in jupiter_radius_map:
            return jupiter_radius_map[target]
    # Neptune viewer rings are indexed by name in FORTRAN, but the Python ring
    # specs are unnamed; map canonical names to the FORTRAN ring index.
    if cfg.planet_num == 8:
        neptune_index = {
            'galle': 0,
            'leverrier': 1,
            'arago': 2,
            'adams': 3,
        }.get(target)
        if neptune_index is not None and neptune_index < len(cfg.rings):
            return cfg.rings[neptune_index].outer_km
    if cfg.planet_num == 9:
        pluto_index = _PLUTO_RING_NAME_TO_INDEX.get(target)
        if pluto_index is not None and pluto_index < len(cfg.rings):
            return cfg.rings[pluto_index].outer_km
    if cfg.planet_num == 4:
        mars_radius_map = {
            'phobos': 9378.0,
            'deimos': 23459.0,
        }
        if target in mars_radius_map:
            return mars_radius_map[target]
    # FORTRAN viewer3_ura.f uses a custom mapping for Uranus center ansa:
    # Epsilon -> average of rings 10 and 11, Nu -> ring 13, Mu -> ring 16.
    if cfg.planet_num == 7:
        if target == 'epsilon' and len(cfg.rings) >= 11:
            return 0.5 * (cfg.rings[9].outer_km + cfg.rings[10].outer_km)
        if target == 'nu' and len(cfg.rings) >= 13:
            return cfg.rings[12].outer_km
        if target == 'mu' and len(cfg.rings) >= 16:
            return cfg.rings[15].outer_km
    matched_radii: list[float] = []
    for ring in cfg.rings:
        ring_name = ring.name or ''
        if len(ring_name) == 0:
            continue
        if ring_name.lower().replace(' ring', '').strip() == target:
            matched_radii.append(ring.outer_km)
    if len(matched_radii) == 0:
        return None
    # Prefer the outermost matching component for multi-part ring names.
    return max(matched_radii)


def _strip_leading_option_code(text: str) -> str:
    """Strip leading numeric CGI option code from a selection label."""
    s = text.strip()
    idx = 0
    while idx < len(s) and s[idx].isdigit():
        idx += 1
    if idx == 0:
        return s
    while idx < len(s) and s[idx].isspace():
        idx += 1
    return s[idx:] if idx < len(s) else s


def _viewer_call_kwargs_from_params(params: ViewerParams) -> _RunViewerKwargs:
    """Convert a ``ViewerParams`` object to legacy ``run_viewer`` keyword args."""
    center_ra = (
        params.center.ra_deg
        if params.center.mode == 'J2000' and params.center.ra_deg is not None
        else 0.0
    )
    center_dec = (
        params.center.dec_deg
        if params.center.mode == 'J2000' and params.center.dec_deg is not None
        else 0.0
    )
    if params.observer.name is not None and params.observer.name.strip() != '':
        viewpoint = params.observer.name
    elif params.observer.latitude_deg is not None and params.observer.longitude_deg is not None:
        viewpoint = 'latlon'
    else:
        viewpoint = 'Earth'
    ring_display = None
    if params.display is not None and params.display.rings_display:
        ring_display = params.display.rings_display
    elif params.ring_names:
        ring_display = ', '.join(params.ring_names)
    moon_display = None
    if params.display is not None and params.display.moons_display:
        moon_display = params.display.moons_display
    viewpoint_display = None
    if params.display is not None and params.display.viewpoint_display:
        viewpoint_display = params.display.viewpoint_display
    return {
        'planet_num': params.planet_num,
        'time_str': params.time_str,
        'fov': params.fov_value,
        'center_mode': params.center.mode,
        'center_ra': center_ra,
        'center_dec': center_dec,
        'center_body_name': params.center.body_name,
        'center_ansa_name': params.center.ansa_name,
        'center_ansa_ew': params.center.ansa_ew or 'east',
        'viewpoint': viewpoint,
        'ephem_version': params.ephem_version,
        'moon_ids': params.moon_ids,
        'moon_selection_display': moon_display,
        'blank_disks': params.blank_disks,
        'ring_selection': params.ring_names,
        'ring_selection_display': ring_display,
        'output_ps': params.output_ps,
        'output_txt': params.output_txt,
        'fov_unit': params.fov_unit,
        'observer_latitude': params.observer.latitude_deg,
        'observer_longitude': params.observer.longitude_deg,
        'observer_altitude': params.observer.altitude_m,
        'observer_lon_dir': params.observer.lon_dir,
        'viewpoint_display': viewpoint_display,
        'labels': params.labels,
        'moon_points': params.moonpts,
        'meridian_points': 1.3 if params.meridians else 0.0,
        'opacity': params.opacity,
        'peris': params.peris,
        'peripts': params.peripts,
        'arcmodel': params.arcmodel,
        'arcpts': params.arcpts,
        'torus': params.torus,
        'torus_inc': params.torus_inc,
        'torus_rad': params.torus_rad,
        'extra_star_name': params.extra_star.name if params.extra_star is not None else None,
        'extra_star_ra_deg': params.extra_star.ra_deg if params.extra_star is not None else None,
        'extra_star_dec_deg': params.extra_star.dec_deg if params.extra_star is not None else None,
        'other_bodies': params.other_bodies,
        'title': params.title,
    }


def viewer_params_from_legacy_kwargs(**kwargs: object) -> ViewerParams:
    """Build ViewerParams from flat legacy keyword arguments (e.g. for tests).

    Accepts the same keyword names as the legacy run_viewer signature
    (and _RunViewerKwargs). Used by tests that call run_viewer with
    keyword arguments.
    """

    def _get(key: str, default: object = None) -> object:
        return kwargs.get(key, default)

    center = ViewerCenter(
        mode=str(_get('center_mode', 'J2000')),
        ra_deg=float(cast(Any, _get('center_ra', 0.0))) if _get('center_ra') is not None else None,
        dec_deg=float(cast(Any, _get('center_dec', 0.0)))
        if _get('center_dec') is not None
        else None,
        body_name=cast('str | None', _get('center_body_name')),
        ansa_name=cast('str | None', _get('center_ansa_name')),
        ansa_ew=str(_get('center_ansa_ew', 'east')) if _get('center_ansa_ew') else None,
    )
    observer = Observer(
        name=cast('str | None', _get('viewpoint')),
        latitude_deg=float(cast(Any, x)) if (x := _get('observer_latitude')) is not None else None,
        longitude_deg=float(cast(Any, x))
        if (x := _get('observer_longitude')) is not None
        else None,
        altitude_m=float(cast(Any, x)) if (x := _get('observer_altitude')) is not None else None,
        lon_dir=str(_get('observer_lon_dir', 'east')),
    )
    extra = _get('extra_star_name'), _get('extra_star_ra_deg'), _get('extra_star_dec_deg')
    if extra[0] is not None or extra[1] is not None or extra[2] is not None:
        extra_star = ExtraStar(
            name=str(extra[0] or ''),
            ra_deg=float(cast(Any, extra[1])) if extra[1] is not None else 0.0,
            dec_deg=float(cast(Any, extra[2])) if extra[2] is not None else 0.0,
        )
    else:
        extra_star = None
    display = ViewerDisplayInfo(
        moons_display=cast('str | None', _get('moon_selection_display')),
        rings_display=cast('str | None', _get('ring_selection_display')),
        viewpoint_display=cast('str | None', _get('viewpoint_display')),
    )
    return ViewerParams(
        planet_num=int(cast(Any, _get('planet_num', 0))),
        time_str=str(_get('time_str', '')),
        fov_value=float(cast(Any, _get('fov', 1.0))),
        fov_unit=str(_get('fov_unit') or 'degrees'),
        center=center,
        observer=observer,
        ephem_version=int(cast(Any, _get('ephem_version', 0))),
        moon_ids=cast('list[int] | None', _get('moon_ids')),
        ring_names=cast('list[str] | None', _get('ring_selection')),
        blank_disks=bool(_get('blank_disks', False)),
        opacity=str(_get('opacity', 'Transparent')),
        peris=str(_get('peris', 'None') or 'None'),
        peripts=float(cast(Any, _get('peripts', 4.0))),
        labels=str(_get('labels') or 'Small (6 points)'),
        moonpts=float(cast(Any, _get('moon_points', 0.0))),
        meridians=bool(float(cast(Any, _get('meridian_points') or 0)) > 0),
        arcmodel=cast('str | None', _get('arcmodel')),
        arcpts=float(cast(Any, _get('arcpts', 4.0))),
        torus=bool(_get('torus', False)),
        torus_inc=float(cast(Any, _get('torus_inc', 6.8))),
        torus_rad=float(cast(Any, _get('torus_rad', 422000.0))),
        extra_star=extra_star,
        other_bodies=cast('list[str] | None', _get('other_bodies')),
        title=str(_get('title', '')),
        display=display,
        output_ps=cast('TextIO | None', _get('output_ps')),
        output_txt=cast('TextIO | None', _get('output_txt')),
    )
