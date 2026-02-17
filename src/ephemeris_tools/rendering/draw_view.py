"""Planet viewer PostScript rendering (port of rspk_drawview.f).

Generates PostScript via the Escher/Euclid pipeline to produce output
identical to the FORTRAN viewer.  The rendering flow mirrors
rspk_drawview.f exactly:

1. PS preamble (font macros, label macros)
2. Title, captions, credit, axis labels
3. Camera matrix and EUVIEW
4. SPICE geometry: observer, planet, Sun, bodies, rings
5. EUGEOM + EUBODY + EURING drawing
6. Border box, tick marks, labels
7. Moon labels, stars
8. EUCLR
"""

from __future__ import annotations

import math
import struct
import time as _time
from typing import TextIO

import cspyce

from ephemeris_tools.rendering.escher import (
    EscherState,
    EscherViewState,
    esfile,
    eslwid,
    esmove,
    eswrit,
    write_ps_header,
)
from ephemeris_tools.rendering.euclid import (
    STARFONT_PLUS,
    EuclidState,
    eubody,
    euclr,
    eugeom,
    euring,
    eustar,
    eutemp,
    euview,
)

# ---------------------------------------------------------------------------
# Constants (from rspk_drawview.f)
# ---------------------------------------------------------------------------

# FOV circle diameter in points (7 inches * 72 pt/inch)
FOV_PTS = 7.0 * 72.0  # 504.0

# Euclid viewport constants
_DEVICE = 7
_H1 = 0.066666667  # 1/15
_H2 = 1.0
_V1 = 0.988888889  # 89/90
_V2 = 0.055555556  # 1/18

# Line types (rspk_drawview.f)
LIT_LINE = 1
DARK_LINE = 7
SHADOW_LINE = 10
AXIS_LINE = 1
NO_LINE = -1
STAR_LINE = 1

# Star rendering
_STAR_FONTSIZE = 2
_STAR_WIDTH = 1.5
_STAR_DIAMPTS = 24.0

# Drawing parameters
PLANET_MERIDS = 12
PLANET_LATS = 11
MOON_MERIDS = 12
MOON_LATS = 11
MAX_NMOONS = 40
MAX_NRINGS = 40
MAX_NLOOPS = 80
MAX_NBODIES = 2 + MAX_NMOONS + MAX_NRINGS
RING_THICKNESS = 1.0
MAX_MINSIZE = 10.0
MAX_ARCPTS = 10.0
LOOP_WIDTH = 1.0
LOOP_DLON = 0.01

# RA/Dec label constants
_MINSTEPS = 3.0
_TICKSIZE1 = 0.05
_TICKSIZE2 = 0.02
# 1-based FORTRAN tables; index 0 is an unused sentinel for parity.
_STEP1 = (
    0.0,
    0.001,
    0.002,
    0.005,
    0.01,
    0.02,
    0.05,
    0.1,
    0.2,
    0.5,
    1.0,
    2.0,
    5.0,
    10.0,
    30.0,
    60.0,
    120.0,
    300.0,
    600.0,
    1800.0,
    3600.0,
    7200.0,
    18000.0,
    36000.0,
    72000.0,
)
_SUBSTEPS = (0, 5, 4, 5, 5, 4, 5, 5, 4, 5, 5, 4, 5, 5, 6, 6, 4, 5, 5, 6, 6, 4, 5, 5, 6)
_NCHOICES = 24
_MAXSECS = 86400.0

SUN_ID = 10
HALFPI = math.pi / 2.0
TWOPI = 2.0 * math.pi
DPR = 180.0 / math.pi


def _fortran_nint(value: float) -> int:
    """Return FORTRAN-compatible nearest integer (ties away from zero)."""
    return int(value + 0.5) if value >= 0.0 else int(value - 0.5)


def _fortran_data_real(value: float) -> float:
    """Round-trip through IEEE float32 like FORTRAN DATA real literal parsing."""
    return struct.unpack('!f', struct.pack('!f', value))[0]


# ---------------------------------------------------------------------------
# Helper functions (ports of FORTRAN internal subroutines)
# ---------------------------------------------------------------------------


def _recrad(v: tuple[float, float, float]) -> tuple[float, float, float]:
    """Rectangular to spherical: (r, ra, dec)."""
    x, y, z = v
    r = math.sqrt(x * x + y * y + z * z)
    if r < 1e-15:
        return (0.0, 0.0, 0.0)
    lon = math.atan2(y, x)
    lat = math.asin(max(-1.0, min(1.0, z / r)))
    return (r, lon, lat)


def _radrec(r: float, lon_rad: float, lat_rad: float) -> tuple[float, float, float]:
    """Spherical to rectangular."""
    cos_lat = math.cos(lat_rad)
    return (
        r * cos_lat * math.cos(lon_rad),
        r * cos_lat * math.sin(lon_rad),
        r * math.sin(lat_rad),
    )


def _rspk_write_string(s: str, state: EscherState) -> None:
    """Write a PostScript-format string with escaped parentheses (port of RSPK_WriteString).

    Parentheses are escaped so the string can be used in PostScript. Backslashes
    are not escaped (for octal escapes like \\260). String length is limited by
    PostScript.

    Parameters:
        s: String to write.
        state: Escher state (outuni must be open).
    """
    safe = s.replace('(', '\\(').replace(')', '\\)')
    eswrit(f'({safe})', state)


def _rspk_write_label(
    secs: float,
    offset: str,
    escher_state: EscherState,
) -> None:
    """Write a numeric label at the current point in deg/min/sec (port of RSPK_WriteLabel).

    Parameters:
        secs: Value in seconds (e.g. arcseconds or time).
        offset: 'B' = below, 'L' = left (label placement).
        escher_state: Escher state.
    """
    secs1 = secs
    if offset == 'B':
        secs1 = secs1 % _MAXSECS
        if secs1 < 0.0:
            secs1 += _MAXSECS
    fsign = 1.0 if secs1 >= 0 else -1.0
    fsecs = abs(secs1)
    # FORTRAN parity: bottom-axis labels can land exactly on millisecond
    # half-boundaries due to binary rounding. A tiny positive bias reproduces
    # FORTRAN's label choice for RA ticks without affecting visible precision.
    # Keep this bias only for bottom-axis labels; left-axis labels in FORTRAN
    # do not use it and otherwise drift by 0.001 in several cases.
    if offset == 'B':
        ims = _fortran_nint(fsecs * 1000.0 + 1.0e-9)
    else:
        ims = _fortran_nint(fsecs * 1000.0)
    isec = ims // 1000
    ims = ims - 1000 * isec
    imin = isec // 60
    isec = isec - 60 * imin
    ideg = imin // 60
    imin = imin - 60 * ideg
    s = f'{ideg:3d} {imin:02d} {isec:02d}.{ims:03d}'
    if offset == 'B' and ims == 0:
        # FORTRAN omits fractional part for whole-second bottom labels.
        s = f'{ideg:3d} {imin:02d} {isec:02d}'
    elif offset == 'L' and ims == 0:
        # FORTRAN also omits fractional part for whole-second left labels.
        s = f'{ideg:3d} {imin:02d} {isec:02d}'
    elif offset in ('B', 'L'):
        # Match FORTRAN's trailing-zero suppression for non-integer labels
        # (e.g., 40.100 -> 40.1, 33.900 -> 33.9).
        s = s.rstrip('0 ').rstrip('.')
    elif offset not in ('B', 'L'):
        s = s.rstrip('0 ').rstrip('.')
    s = s.lstrip()
    if fsign < 0:
        s = '-' + s
    esmove(escher_state)
    safe = s.replace('(', '\\(').replace(')', '\\)')
    if offset == 'L':
        eswrit(f'({safe}) LabelLeft', escher_state)
    else:
        eswrit(f'({safe}) LabelBelow', escher_state)


def _rspk_annotate(
    name: str,
    los: list[float],
    radius: float,
    cmatrix: list[list[float]],
    delta: float,
    view_state: EscherViewState,
    escher_state: EscherState,
) -> None:
    """Write body name at position (port of RSPK_Annotate).

    Parameters:
        name: Label text (e.g. moon or star name).
        los: J2000 line-of-sight to the body (3-vector).
        radius: Sky radius of body (radians).
        cmatrix: Camera orientation matrix.
        delta: FOV size (for visibility check).
        view_state: Escher view state.
        escher_state: Escher output state.
    """
    # Match FORTRAN MTXV behavior for camera transform.
    cam = list(cspyce.mtxv(cmatrix, los))
    if cam[2] <= 0.0:
        return
    x = -cam[0] / cam[2]
    y = -cam[1] / cam[2]
    x = x + 0.7070 * radius
    y = y - 0.7070 * radius
    if abs(x) < delta and abs(y) < delta:
        eutemp([x], [y], [x], [y], 1, 1, view_state, escher_state)
        esmove(escher_state)
        name_safe = name.replace('(', '\\(').replace(')', '\\)')
        eswrit(f'({name_safe}) LabelBody', escher_state)


def _rspk_labels2(
    cmatrix: list[list[float]],
    delta: float,
    ltype: int,
    view_state: EscherViewState,
    escher_state: EscherState,
) -> None:
    """Plot RA/Dec tick marks and numeric labels on the figure (port of RSPK_Labels2).

    Parameters:
        cmatrix: Camera orientation matrix.
        delta: Field-of-view size (half-width).
        ltype: Line type (color) for tick marks.
        view_state: Escher view state.
        escher_state: Escher output state.
    """
    dpr = DPR
    _rng, ra, dec = cspyce.recrad((cmatrix[0][2], cmatrix[1][2], cmatrix[2][2]))
    delta_ra = delta / math.cos(dec) if abs(math.cos(dec)) > 1e-12 else delta
    dtick1 = _TICKSIZE1 * delta
    dtick2 = _TICKSIZE2 * delta

    # RA ticks
    spr = dpr * 3600.0 / 15.0
    sdelta = delta_ra * spr
    i = _NCHOICES
    while i >= 2:
        if 2.0 * sdelta >= _MINSTEPS * _fortran_data_real(_STEP1[i]):
            break
        i -= 1
    nsubs = _SUBSTEPS[i]
    ds = _fortran_data_real(_STEP1[i]) / nsubs
    ra_sec = ra * spr
    k1 = _fortran_nint((ra_sec - sdelta) / ds + 0.5)
    k2 = _fortran_nint((ra_sec + sdelta) / ds - 0.5)
    for k in range(k1, k2 + 1):
        s = k * ds
        length = dtick2
        ismajor = (k % nsubs) == 0
        if ismajor:
            length = dtick1
        j2000_los = cspyce.radrec(1.0, s / spr, dec)
        cam = list(cspyce.mtxv(cmatrix, j2000_los))
        x = -cam[0] / cam[2]
        if abs(x) <= delta:
            eutemp([x], [delta - length], [x], [delta], 1, ltype, view_state, escher_state)
            if ismajor:
                _rspk_write_label(s, 'B', escher_state)
            eutemp([x], [-delta + length], [x], [-delta], 1, ltype, view_state, escher_state)

    # Dec ticks
    spr = dpr * 3600.0
    sdelta = delta * spr
    i = _NCHOICES
    while i >= 2:
        if 2.0 * sdelta >= _MINSTEPS * _fortran_data_real(_STEP1[i]):
            break
        i -= 1
    nsubs = _SUBSTEPS[i]
    ds = _fortran_data_real(_STEP1[i]) / nsubs
    dec_sec = dec * spr
    k1 = _fortran_nint((dec_sec - sdelta) / ds + 0.5)
    k2 = _fortran_nint((dec_sec + sdelta) / ds - 0.5)
    for k in range(k1, k2 + 1):
        s = k * ds
        length = dtick2
        ismajor = (k % nsubs) == 0
        if ismajor:
            length = dtick1
        j2000_los = cspyce.radrec(1.0, ra, s / spr)
        cam = list(cspyce.mtxv(cmatrix, j2000_los))
        y = -cam[1] / cam[2]
        if abs(y) <= delta:
            eutemp([-delta + length], [y], [-delta], [y], 1, ltype, view_state, escher_state)
            if ismajor:
                _rspk_write_label(s, 'L', escher_state)
            eutemp([delta - length], [y], [delta], [y], 1, ltype, view_state, escher_state)


def _rspk_draw_bodies(
    nbodies: int,
    body_pts: list[float],
    body_names: list[str],
    body_dist: list[float],
    body_diampts: float,
    update_names: bool,
    mindist: float,
    pmerids: int,
    plats: int,
    mmerids: int,
    mlats: int,
    lit_line: int,
    dark_line: int,
    term_line: int,
    lit_line2: int,
    dark_line2: int,
    term_line2: int,
    prime_pts: float,
    euclid_state: EuclidState,
    view_state: EscherViewState,
    escher_state: EscherState,
) -> None:
    """Draw all bodies (planet and moons) with terminators (port of RSPK_DrawBodies).

    Optionally clears body names for bodies not visible. Uses prime_pts for
    prime meridian emphasis when > 0.
    """
    l1 = lit_line
    l2 = dark_line
    l3 = term_line
    isvis = l1 != 0 or l2 != 0 or l3 != 0

    if isvis:
        eswrit('%Draw planet...', escher_state)

    # Prime meridian pass
    if isvis and prime_pts > 0.0:
        eslwid(prime_pts, escher_state)
        eubody(1, 1, 0, 1, l1, l2, 0, euclid_state, view_state, escher_state)
        eubody(1, 0, 0, 1, 0, 0, 0, euclid_state, view_state, escher_state)

    eslwid(0.0, escher_state)
    eubody(1, pmerids, plats, 1, l1, l2, l3, euclid_state, view_state, escher_state)

    # Draw invisible object at middle of screen (toolkit lighting bug workaround)
    eubody(2, 2, 1, 1, 0, 0, 0, euclid_state, view_state, escher_state)

    # Draw moons
    for ibody in range(3, nbodies + 1):
        bi = ibody - 1  # 0-based index for arrays
        inner = (body_dist[bi] < mindist) if bi < len(body_dist) else False
        if inner:
            bl1, bl2, bl3 = lit_line2, dark_line2, term_line2
        else:
            bl1, bl2, bl3 = lit_line, dark_line, term_line

        bvis = bl1 != 0 or bl2 != 0 or bl3 != 0
        bname = body_names[bi] if bi < len(body_names) else ''
        if bvis and bname.strip():
            eswrit(f'%Draw {bname.strip()}...', escher_state)

        bpts = body_pts[bi] if bi < len(body_pts) else 0.0

        # FORTRAN draws prime and anti-meridian for moons only when:
        # isvis, prime_pts>0, body_diampts==0, and body_pts > body_diampts*8.
        if bvis and prime_pts > 0.0 and body_diampts == 0.0 and bpts > body_diampts * 8.0:
            eslwid(prime_pts, escher_state)
            eubody(ibody, 1, 0, 1, bl1, bl2, 0, euclid_state, view_state, escher_state)
            eubody(ibody, 0, 0, 1, 0, 0, 0, euclid_state, view_state, escher_state)

        # Draw body with minimum size line width
        # Match FORTRAN ESFLAG logic: detect whether this body produced any
        # rendered segments and clear the label name when it did not.
        escher_state.drawn = False
        eslwid(body_diampts - bpts, escher_state)
        eubody(ibody, mmerids, mlats, 1, bl1, bl2, bl3, euclid_state, view_state, escher_state)
        if update_names and bvis and not escher_state.drawn and bi < len(body_names):
            body_names[bi] = ' '

    eslwid(0.0, escher_state)


def _rspk_draw_rings(
    iring1: int,
    iring2: int,
    ring_flags: list[bool],
    ring_locs: list[list[float]],
    ring_axes1: list[list[float]],
    ring_axes2: list[list[float]],
    ring_dark: list[bool],
    ring_dashed: list[bool],
    nloops: int,
    loop_locs: list[list[float]],
    loop_axes1: list[list[float]],
    loop_axes2: list[list[float]],
    loop_ring: list[int],
    arc_width: float,
    lit_line: int,
    dark_line: int,
    shadow_line: int,
    term_line: int,
    euclid_state: EuclidState,
    view_state: EscherViewState,
    escher_state: EscherState,
) -> None:
    """Draw all rings and arc segments with lit/dark/shadow/terminator (port of RSPK_DrawRings).

    Differentiates dark (unlit) vs shadowed rings. iring1..iring2 index the ring
    list; loops are arc segments on specified rings.
    """
    for iring in range(iring1, iring2 + 1):
        ri = iring - 1  # 0-based
        if ri < 0 or ri >= len(ring_flags):
            continue
        if not ring_flags[ri]:
            continue

        draw_line = lit_line
        if ring_dark[ri]:
            draw_line = dark_line

        eswrit(f'%Draw ring #{iring:2d}...', escher_state)

        if ring_dashed[ri]:
            eswrit('[30 30] 0 setdash', escher_state)

        euring(
            ring_locs[ri],
            ring_axes1[ri],
            ring_axes2[ri],
            1,
            draw_line,
            shadow_line,
            euclid_state,
            view_state,
            escher_state,
        )

        if ring_dashed[ri]:
            eswrit('[] 0 setdash', escher_state)

    # Draw arcs as tiny loops
    if nloops > 0:
        eswrit('%Draw arcs...', escher_state)

    eslwid(arc_width, escher_state)
    for iloop in range(nloops):
        iring = loop_ring[iloop]
        if iring >= iring1 and iring <= iring2:
            ri = iring - 1
            draw_line = lit_line
            if ri >= 0 and ri < len(ring_dark) and ring_dark[ri]:
                draw_line = dark_line
            euring(
                loop_locs[iloop],
                loop_axes1[iloop],
                loop_axes2[iloop],
                1,
                draw_line,
                shadow_line,
                euclid_state,
                view_state,
                escher_state,
            )

    eslwid(0.0, escher_state)


def camera_matrix(center_ra_rad: float, center_dec_rad: float) -> list[list[float]]:
    """Camera orientation matrix for center (ra, dec) in J2000 (port of RSPK_DrawView).

    Parameters:
        center_ra_rad: Center right ascension (radians).
        center_dec_rad: Center declination (radians).

    Returns:
        3x3 row-major matrix (list of 3 rows); columns are camera x, y, z axes.
    """
    # Use SPICE vector primitives directly to match FORTRAN RADREC/VPERP/VHAT/VCRSS.
    col3 = list(cspyce.radrec(1.0, center_ra_rad, center_dec_rad))
    temp = list(cspyce.vperp((0.0, 0.0, 1.0), col3))
    n2 = math.sqrt(temp[0] * temp[0] + temp[1] * temp[1] + temp[2] * temp[2])
    if n2 < 1e-12:
        col2 = [1.0, 0.0, 0.0]
    else:
        col2 = list(cspyce.vhat(temp))
    col1 = list(cspyce.vcrss(col2, col3))

    # FORTRAN stores as cmatrix(3,3) column-major:
    # cmatrix(:,1) = col1, cmatrix(:,2) = col2, cmatrix(:,3) = col3
    # In row-major Python list-of-rows, cmatrix[row][col]:
    return [
        [col1[0], col2[0], col3[0]],
        [col1[1], col2[1], col3[1]],
        [col1[2], col2[2], col3[2]],
    ]


def radec_to_plot(
    ra_rad: float,
    dec_rad: float,
    center_ra_rad: float,
    center_dec_rad: float,
    fov_rad: float,
) -> tuple[float, float]:
    """Convert (ra, dec) to plot coordinates (x, y) in points.

    Uses camera matrix for center and FOV scale. Returns (0, 0) if point is
    behind the camera (z_cam <= 0).

    Parameters:
        ra_rad, dec_rad: Point RA/Dec in radians.
        center_ra_rad, center_dec_rad: FOV center in radians.
        fov_rad: Field of view in radians.

    Returns:
        (x_plot, y_plot) in points.
    """
    cmat = camera_matrix(center_ra_rad, center_dec_rad)
    cos_d = math.cos(dec_rad)
    d = [cos_d * math.cos(ra_rad), cos_d * math.sin(ra_rad), math.sin(dec_rad)]
    x_cam = d[0] * cmat[0][0] + d[1] * cmat[1][0] + d[2] * cmat[2][0]
    y_cam = d[0] * cmat[0][1] + d[1] * cmat[1][1] + d[2] * cmat[2][1]
    z_cam = d[0] * cmat[0][2] + d[1] * cmat[1][2] + d[2] * cmat[2][2]
    if z_cam <= 1e-12:
        return (0.0, 0.0)
    half = fov_rad / 2.0
    scale = FOV_PTS / (2.0 * math.tan(half))
    x_plot = scale * x_cam / z_cam
    y_plot = scale * y_cam / z_cam
    return (x_plot, y_plot)


def _generated_date_str() -> str:
    """Return current date for Generated-by footer (match FDATE format).

    FORTRAN FDATE() returns local time, e.g. 'Tue Feb 10 15:45:40 2026'.
    """
    return _time.strftime('%a %b %d %H:%M:%S %Y', _time.localtime())


def _vnorm(v: list[float]) -> float:
    """Vector magnitude."""
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def _vhat(v: list[float]) -> list[float]:
    """Unit vector."""
    n = _vnorm(v)
    if n == 0.0:
        return [0.0, 0.0, 0.0]
    return [v[0] / n, v[1] / n, v[2] / n]


def _opsgnd(a: float, b: float) -> bool:
    """True if a and b have opposite signs."""
    return (a > 0 and b < 0) or (a < 0 and b > 0)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def draw_planetary_view(
    output: TextIO,
    *,
    obs_time: float,
    fov: float,
    center_ra: float,
    center_dec: float,
    planet_name: str,
    blank_disks: bool = False,
    prime_pts: float = 0.0,
    nmoons: int = 0,
    moon_flags: list[bool] | None = None,
    moon_ids: list[int] | None = None,
    moon_names: list[str] | None = None,
    moon_labelpts: float = 0.0,
    moon_diampts: float = 0.0,
    nrings: int = 0,
    ring_flags: list[bool] | None = None,
    ring_rads: list[float] | None = None,
    ring_elevs: list[float] | None = None,
    ring_eccs: list[float] | None = None,
    ring_incs: list[float] | None = None,
    ring_peris: list[float] | None = None,
    ring_nodes: list[float] | None = None,
    ring_offsets: list[list[float]] | None = None,
    ring_opaqs: list[bool] | None = None,
    ring_dashed: list[bool] | None = None,
    ring_method: int = 0,
    narcs: int = 0,
    arc_flags: list[bool] | None = None,
    arc_rings: list[int] | None = None,
    arc_minlons: list[float] | None = None,
    arc_maxlons: list[float] | None = None,
    arc_width: float = 4.0,
    nstars: int = 0,
    star_ras: list[float] | None = None,
    star_decs: list[float] | None = None,
    star_names: list[str] | None = None,
    star_labels: bool = False,
    star_diampts: float = _STAR_DIAMPTS,
    title: str = '',
    ncaptions: int = 0,
    lcaptions: list[str] | None = None,
    rcaptions: list[str] | None = None,
    align_loc: float = 108.0,
) -> None:
    """Generate PostScript showing planetary system at a time (port of RSPK_DrawView).

    Renders planet and moons as triaxial ellipsoids with terminators, optional
    rings (with vertical offsets and opacity), arcs, and stars. Frame is J2000
    (dec up, RA left). Title and captions supported.

    Parameters:
        output: Open text stream for PostScript output.
        obs_time: SPICE ephemeris time (ET/TDB).
        fov: Field of view in radians.
        center_ra: Center RA in radians.
        center_dec: Center Dec in radians.
        planet_name: Planet name (e.g. "Saturn").
        blank_disks: True to leave disks blank.
        prime_pts: Line weight for prime meridian (0 = no emphasis).
        nmoons: Number of moons in list.
        moon_flags: Boolean flags for which moons to include.
        moon_ids: SPICE body IDs of moons.
        moon_names: Names of moons.
        moon_labelpts: Size of moon labels (points); 0 disables.
        moon_diampts: Minimum diameter of plotted disk (points).
        nrings: Number of rings.
        ring_flags: Boolean flags for which rings to include.
        ring_rads: Semimajor axis of each ring (km).
        ring_elevs: Vertical offset of each ring (km north).
        ring_eccs: Eccentricity of each ring.
        ring_incs: Inclination of each ring (radians).
        ring_peris: Pericenter longitude of each ring (radians).
        ring_nodes: Ascending node longitude of each ring (radians).
        ring_offsets: 3-vector offset of ring center from planet (J2000 km).
        ring_opaqs: True if ring is opaque.
        ring_dashed: True to plot ring as dashed line.
        ring_method: 0=transparent, 1=semi-transparent, 2=opaque.
        narcs: Number of ring arcs.
        arc_flags: Boolean flags for which arcs to include.
        arc_rings: Index (1-based) of ring where each arc falls.
        arc_minlons: Lower longitude limit of each arc (radians).
        arc_maxlons: Upper longitude limit of each arc (radians).
        arc_width: Width of plotted arc (points).
        nstars: Number of stars.
        star_ras: RA of each star (radians).
        star_decs: Dec of each star (radians).
        star_names: Names of stars.
        star_labels: True to label stars.
        star_diampts: Plotted diameter of stars (points).
        title: Title string above diagram.
        ncaptions: Number of caption lines.
        lcaptions: Left part of each caption line.
        rcaptions: Right part of each caption line.
        align_loc: Alignment distance from left edge (points).
    """
    from ephemeris_tools.spice.bodmat import bodmat
    from ephemeris_tools.spice.common import get_state
    from ephemeris_tools.spice.observer import observer_state
    from ephemeris_tools.spice.shifts import spkapp_shifted

    spice_state = get_state()
    planet_id = spice_state.planet_id
    planet_num = spice_state.planet_num

    # Default list args; copy ring_flags before padding so we do not mutate caller's list
    moon_flags = moon_flags or []
    moon_ids = moon_ids or []
    moon_names = moon_names or []
    ring_flags = list(ring_flags or [])
    ring_rads = ring_rads or []
    ring_elevs = ring_elevs or []
    ring_eccs = ring_eccs or []
    ring_incs = ring_incs or []
    ring_peris = ring_peris or []
    ring_nodes = ring_nodes or []
    ring_offsets = ring_offsets or []
    ring_opaqs = ring_opaqs or []
    ring_dashed = ring_dashed or []
    arc_flags = arc_flags or []
    arc_rings = arc_rings or []
    arc_minlons = arc_minlons or []
    arc_maxlons = arc_maxlons or []
    star_ras = star_ras or []
    star_decs = star_decs or []
    star_names = star_names or []
    lcaptions = lcaptions or []
    rcaptions = rcaptions or []

    out_name = getattr(output, 'name', '') or 'view.ps'

    # ===================================================================
    # Initialize the PostScript file
    # ===================================================================
    escher_state = EscherState()
    escher_state.outuni = output
    escher_state.open = True
    escher_state.external_stream = True
    escher_state.outfil = out_name
    escher_state.creator = f'{planet_name} Viewer, PDS Ring-Moon Systems Node'
    escher_state.fonts = 'Helvetica'

    esfile(out_name, escher_state.creator, escher_state.fonts, escher_state)
    escher_state.outuni = output
    escher_state.open = True
    escher_state.external_stream = True
    write_ps_header(escher_state)

    # Preamble macros (rspk_drawview lines 430-470)
    eswrit('/MakeDegreeFont {', escher_state)
    eswrit('findfont dup /CharStrings get /degree known {', escher_state)
    eswrit('dup length dict /newdict exch def {', escher_state)
    eswrit('1 index /FID ne { newdict 3 1 roll put }', escher_state)
    eswrit('{ pop pop } ifelse } forall', escher_state)
    eswrit('newdict /Encoding get dup length array copy', escher_state)
    eswrit('newdict exch /Encoding exch put', escher_state)
    eswrit('newdict /CharStrings get /degree known {', escher_state)
    eswrit('newdict /Encoding get 8#260 /degree put } if', escher_state)
    eswrit('newdict true } { pop false } ifelse } def', escher_state)
    # FORTRAN: '/MyFont /Helvetica ' // ' MakeDegreeFont ...' has two spaces
    eswrit('/MyFont /Helvetica  MakeDegreeFont { definefont pop } if', escher_state)
    eswrit('/unscale {10 10 scale} def', escher_state)
    eswrit('/TextHeight {11} def', escher_state)
    eswrit('/MyFont findfont TextHeight scalefont setfont', escher_state)
    eswrit('/LabelBelow {gsave currentpoint translate', escher_state)
    eswrit('unscale', escher_state)
    eswrit('dup stringwidth pop -0.5 mul TextHeight -1.3 mul', escher_state)
    eswrit('moveto show grestore} def', escher_state)
    eswrit('/LabelLeft {gsave currentpoint translate', escher_state)
    eswrit('unscale 90 rotate', escher_state)
    eswrit('dup stringwidth pop -0.5 mul TextHeight 0.3 mul', escher_state)
    eswrit('moveto show grestore} def', escher_state)

    # Moon label macro
    if moon_labelpts > 0.0:
        scale_val = min(moon_labelpts / 12.0, 2.0)
        scale_str = f'{scale_val:.3f}'
        eswrit('/LabelBody {gsave currentpoint translate', escher_state)
        eswrit('unscale', escher_state)
        eswrit(f'{scale_str} {scale_str} scale', escher_state)
        eswrit('TextHeight 0.2 mul dup', escher_state)
        eswrit('moveto show grestore} def', escher_state)

    eswrit('%%EndProlog', escher_state)
    eswrit('%', escher_state)

    # Title
    if title.strip():
        eswrit('gsave unscale 324 756 translate 1.4 1.4 scale', escher_state)
        _rspk_write_string(title.strip(), escher_state)
        eswrit('dup stringwidth pop', escher_state)
        eswrit('-0.5 mul TextHeight neg moveto show grestore', escher_state)

    # Captions
    if ncaptions > 0:
        eswrit('gsave unscale', escher_state)
        # FORTRAN: write(tempstr, '(i4)') nint(align_loc) + 72 → 4-char integer
        align_int = _fortran_nint(align_loc) + 72
        eswrit(f'{align_int:4d} 162 translate', escher_state)
        eswrit('0 TextHeight 0.4 mul translate', escher_state)
        for i in range(ncaptions):
            eswrit('0 TextHeight -1.25 mul translate', escher_state)
            eswrit('0 0 moveto', escher_state)
            rtext = rcaptions[i].rstrip() if i < len(rcaptions) else ''
            _rspk_write_string(rtext, escher_state)
            eswrit('show', escher_state)
            ltext = lcaptions[i].rstrip() if i < len(lcaptions) else ''
            _rspk_write_string(ltext + '  ', escher_state)
            eswrit('dup stringwidth pop neg 0 moveto show', escher_state)
        eswrit('grestore', escher_state)

    # Credit footer
    eswrit('gsave unscale 72 36 translate 0.5 0.5 scale', escher_state)
    eswrit('0 0 moveto', escher_state)
    date_str = _generated_date_str()
    # FORTRAN directly writes the string without RSPK_WriteString:
    eswrit(
        f'(Generated by the {planet_name} Viewer Tool, PDS Ring-Moon Systems Node, {date_str})',
        escher_state,
    )
    eswrit('show grestore', escher_state)

    # Axis labels
    eswrit('gsave unscale', escher_state)
    eswrit('324 180 translate 1.2 1.2 scale', escher_state)
    eswrit('(Right Ascension (h m s)) dup stringwidth pop', escher_state)
    eswrit('-0.5 mul 0 moveto show grestore', escher_state)
    eswrit('gsave unscale', escher_state)
    eswrit('36 450 translate 1.2 1.2 scale 90 rotate', escher_state)
    eswrit('(Declination (d m s)) dup stringwidth pop', escher_state)
    eswrit('-0.5 mul TextHeight neg moveto show grestore', escher_state)

    # ===================================================================
    # Initialize camera
    # ===================================================================
    delta = math.tan(fov / 2.0)
    view_state = EscherViewState()
    euclid_state = EuclidState()

    euview(
        _DEVICE,
        _H1,
        _H2,
        _V1,
        _V2,
        -delta,
        delta,
        -delta,
        delta,
        euclid_state,
        view_state,
        escher_state,
    )

    # Meridian and latitude count
    if blank_disks:
        pmerids, plats = 0, 0
        mmerids, mlats = 0, 0
        term_line = LIT_LINE
    else:
        pmerids, plats = PLANET_MERIDS, PLANET_LATS
        mmerids, mlats = MOON_MERIDS, MOON_LATS
        term_line = DARK_LINE

    # ===================================================================
    # Set up observer and planet geometry (SPICE calls)
    # ===================================================================

    # Observer state
    obs_pv = list(observer_state(obs_time))

    # Planet state
    _planet_pv, planet_dt = cspyce.spkapp(planet_id, obs_time, 'J2000', obs_pv[:6], 'LT')
    planet_dpv = list(_planet_pv)
    planet_time = obs_time - planet_dt
    planet_pv = list(cspyce.spkssb(planet_id, planet_time, 'J2000'))

    # Planet rotation matrix (J2000 -> body frame)
    planet_mat = bodmat(planet_id, planet_time)

    # Sun location and radius
    sun_pv, _sun_dt = cspyce.spkapp(SUN_ID, planet_time, 'J2000', planet_pv[:6], 'LT+S')
    sun_dpv = list(sun_pv)
    sun_loc = [planet_pv[i] + sun_dpv[i] for i in range(3)]
    sun_radii_arr = cspyce.bodvar(SUN_ID, 'RADII')
    sun_rad = float(sun_radii_arr[0])

    # Camera C-matrix
    cmat = camera_matrix(center_ra, center_dec)

    # ===================================================================
    # Build body list
    # ===================================================================

    nbodies = 0
    body_locs: list[list[float]] = []
    body_axes: list[list[list[float]]] = []
    body_pts: list[float] = []
    body_dist: list[float] = []
    body_los: list[list[float]] = []
    body_names_list: list[str] = []

    # Body 1: Planet
    nbodies += 1
    planet_loc = [obs_pv[i] + planet_dpv[i] for i in range(3)]
    body_locs.append(planet_loc)

    # planet_mat is J2000→body.  Its rows ARE the body axes in J2000
    # (matching FORTRAN: XPOSE then column extraction).
    p_radii_arr = cspyce.bodvar(planet_id, 'RADII')
    planet_axes_scaled = []
    for i in range(3):
        ax = [planet_mat[i][j] * p_radii_arr[i] for j in range(3)]
        planet_axes_scaled.append(ax)
    body_axes.append(planet_axes_scaled)
    body_pts.append(0.0)
    body_dist.append(0.0)
    body_los.append([0.0, 0.0, 0.0])
    body_names_list.append(' ')  # Never label planet

    # Body 2: Dummy body at middle of field of view
    nbodies += 1
    dummy_axes = []
    for i in range(3):
        dummy_axes.append(_vhat(planet_axes_scaled[i]))
    body_axes.append(dummy_axes)
    # Locate along optic axis, 2x planet distance
    tempvec = [planet_dpv[i] for i in range(3)]
    tdist = _vnorm(tempvec)
    optic_vec = [2.0 * tdist * cmat[j][2] for j in range(3)]
    dummy_loc = [obs_pv[i] + optic_vec[i] for i in range(3)]
    body_locs.append(dummy_loc)
    body_pts.append(0.0)
    body_dist.append(0.0)
    body_los.append([0.0, 0.0, 0.0])
    body_names_list.append(' ')

    # Bodies 3+: Moons
    use_nmoons = min(nmoons, MAX_NMOONS)
    for imoon in range(use_nmoons):
        if imoon >= len(moon_flags) or not moon_flags[imoon]:
            continue
        if imoon >= len(moon_ids):
            continue
        mid = moon_ids[imoon]

        # Moon position
        try:
            moon_pv, mdt = spkapp_shifted(mid, obs_time, 'J2000', obs_pv[:6], 'LT')
        except Exception:
            continue
        moon_dpv = list(moon_pv)
        moon_loc = [obs_pv[i] + moon_dpv[i] for i in range(3)]
        body_locs.append(moon_loc)
        body_los.append(list(moon_dpv[:3]))

        # Moon axes - use moon's own BODMAT if available, else planet_mat
        try:
            if cspyce.bodfnd(mid, 'POLE_RA'):
                moon_rot = bodmat(mid, obs_time - mdt)
                moon_mat = [list(row) for row in moon_rot]
            else:
                moon_mat = [list(row) for row in planet_mat]
        except Exception:
            moon_mat = [list(row) for row in planet_mat]

        # moon_mat is J2000→body. Its rows are the body axes in J2000.
        try:
            m_radii_arr = list(cspyce.bodvar(mid, 'RADII'))
        except Exception:
            m_radii_arr = [1.0, 1.0, 1.0]
        moon_axes = []
        for i in range(3):
            ax = [moon_mat[i][j] * m_radii_arr[i] for j in range(3)]
            moon_axes.append(ax)
        body_axes.append(moon_axes)

        # Projected diameter in points
        moon_dist_km = _vnorm(moon_dpv[:3])
        body_pts_val = 2.0 * m_radii_arr[0] * FOV_PTS / (moon_dist_km * fov)
        body_pts.append(body_pts_val)

        # Name
        mname = moon_names[imoon] if imoon < len(moon_names) else ''
        body_names_list.append(mname)

        # Distance from planet
        tv = [moon_loc[i] - planet_loc[i] for i in range(3)]
        body_dist.append(_vnorm(tv))

        nbodies += 1

    # ===================================================================
    # Determine ring shapes (FORTRAN lines 698-820)
    # ===================================================================

    use_nrings = min(nrings, MAX_NRINGS)

    # Ensure ring and arc lists have at least use_nrings / narcs entries to avoid IndexError
    _def_f = False
    _def_0 = 0.0
    _def_03 = [0.0, 0.0, 0.0]
    while len(ring_flags) < use_nrings:
        ring_flags.append(_def_f)
    while len(ring_rads) < use_nrings:
        ring_rads.append(_def_0)
    while len(ring_eccs) < use_nrings:
        ring_eccs.append(_def_0)
    while len(ring_nodes) < use_nrings:
        ring_nodes.append(_def_0)
    while len(ring_incs) < use_nrings:
        ring_incs.append(_def_0)
    while len(ring_peris) < use_nrings:
        ring_peris.append(_def_0)
    while len(ring_elevs) < use_nrings:
        ring_elevs.append(_def_0)
    while len(ring_offsets) < use_nrings:
        ring_offsets.append(_def_03)
    while len(ring_opaqs) < use_nrings:
        ring_opaqs.append(_def_f)
    while len(ring_dashed) < use_nrings:
        ring_dashed.append(_def_f)
    use_narcs = min(narcs, len(arc_rings), len(arc_flags), len(arc_minlons), len(arc_maxlons))
    while len(arc_rings) < narcs:
        arc_rings.append(0)
    while len(arc_flags) < narcs:
        arc_flags.append(_def_f)
    while len(arc_minlons) < narcs:
        arc_minlons.append(_def_0)
    while len(arc_maxlons) < narcs:
        arc_maxlons.append(_def_0)

    # Planet pole vector (reversed for Uranus)
    pole = _vhat(planet_axes_scaled[2])
    if planet_num == 7:
        pole = [-pole[0], -pole[1], -pole[2]]

    # Equatorial plane ascending node (J2000)
    j2000_z = [0.0, 0.0, 1.0]
    ascnode = [
        j2000_z[1] * pole[2] - j2000_z[2] * pole[1],
        j2000_z[2] * pole[0] - j2000_z[0] * pole[2],
        j2000_z[0] * pole[1] - j2000_z[1] * pole[0],
    ]

    # Extrapolate planet's relative location at observer-received time
    offset = [planet_dt * planet_pv[3 + i] for i in range(3)]

    r_ring_locs: list[list[float]] = []
    r_ring_axes1: list[list[float]] = []
    r_ring_axes2: list[list[float]] = []
    r_ring_axes3: list[list[float]] = []
    r_ring_dark: list[bool] = []

    last_opaq = 0
    nloops = 0
    loop_locs: list[list[float]] = []
    loop_axes1: list[list[float]] = []
    loop_axes2: list[list[float]] = []
    loop_ring: list[int] = []

    for iring in range(use_nrings):
        # Initialize ring arrays to zeros even for skipped rings
        if not ring_flags[iring]:
            r_ring_locs.append([0.0, 0.0, 0.0])
            r_ring_axes1.append([0.0, 0.0, 0.0])
            r_ring_axes2.append([0.0, 0.0, 0.0])
            r_ring_axes3.append([0.0, 0.0, 0.0])
            r_ring_dark.append(False)
            continue

        rad = ring_rads[iring] if iring < len(ring_rads) else 0.0
        ecc = ring_eccs[iring] if iring < len(ring_eccs) else 0.0

        # Track outermost opaque ring
        if iring < len(ring_opaqs) and ring_opaqs[iring]:
            last_opaq = iring + 1  # 1-based

        # Compute ring pole and ascending node from ring inclination/node
        rn = ring_nodes[iring] if iring < len(ring_nodes) else 0.0
        ri = ring_incs[iring] if iring < len(ring_incs) else 0.0

        # VROTV(ascnode, pole, ring_nodes(iring)) -> ringnode
        ringnode = _vrotv(ascnode, pole, rn)
        # VROTV(pole, ringnode, ring_incs(iring)) -> ringpole
        ringpole = _vrotv(pole, ringnode, ri)
        ringpole = _vhat(ringpole)

        # Ring axes
        ring_ax3 = [RING_THICKNESS * ringpole[i] for i in range(3)]
        r_ring_axes3.append(ring_ax3)

        # Pericenter direction
        rp = ring_peris[iring] if iring < len(ring_peris) else 0.0
        peri = _vrotv(ringnode, ringpole, rp - rn)
        peri = _vhat(peri)
        ring_ax1 = [rad * peri[i] for i in range(3)]
        r_ring_axes1.append(ring_ax1)

        # Minor axis = peri rotated 90 degrees around ringpole
        minor_dir = _vrotv(peri, ringpole, HALFPI)
        ring_ax2 = [rad * math.sqrt(1.0 - ecc * ecc) * minor_dir[i] for i in range(3)]
        r_ring_axes2.append(ring_ax2)

        # Ring center = planet_loc - ecc * major_axis + elevation + offset
        ring_loc = [-ecc * ring_ax1[i] + planet_loc[i] for i in range(3)]
        # Add vertical elevation
        re = ring_elevs[iring] if iring < len(ring_elevs) else 0.0
        ring_loc = [ring_loc[i] + re * pole[i] for i in range(3)]

        # Add ring offset
        if iring < len(ring_offsets):
            ro = ring_offsets[iring]
            ring_loc = [ring_loc[i] + ro[i] for i in range(3)]

        r_ring_locs.append(ring_loc)

        # Determine if ring is dark (observer and Sun on opposite sides)
        tempvec_obs = [ring_loc[i] - obs_pv[i] + offset[i] for i in range(3)]
        dot1 = -(
            ringpole[0] * tempvec_obs[0]
            + ringpole[1] * tempvec_obs[1]
            + ringpole[2] * tempvec_obs[2]
        )
        sun_hat = _vhat(sun_dpv[:3])
        dot2 = ringpole[0] * sun_hat[0] + ringpole[1] * sun_hat[1] + ringpole[2] * sun_hat[2]

        is_dashed = ring_dashed[iring] if iring < len(ring_dashed) else False
        if is_dashed:
            r_ring_dark.append(False)
        else:
            sun_dist_val = _vnorm(sun_dpv[:3])
            sun_angular = sun_rad / sun_dist_val if sun_dist_val > 0 else 0
            r_ring_dark.append(_opsgnd(dot1, dot2) and abs(dot2) > sun_angular)

        # Arc loops for this ring
        for iarc in range(use_narcs):
            if iarc >= len(arc_rings) or arc_rings[iarc] != iring + 1:  # 1-based comparison
                continue
            if iarc >= len(arc_flags) or not arc_flags[iarc]:
                continue

            # Mean anomaly range
            lon1 = (arc_minlons[iarc] if iarc < len(arc_minlons) else 0.0) - rp
            lon2 = (arc_maxlons[iarc] if iarc < len(arc_maxlons) else 0.0) - rp
            if lon2 < lon1:
                lon2 += TWOPI

            nsteps = max(int((lon2 - lon1) / LOOP_DLON), 1)
            dlon = (lon2 - lon1) / nsteps

            lon = lon1 - dlon
            for _istep in range(nsteps):
                lon += dlon
                if nloops >= MAX_NLOOPS:
                    break
                nloops += 1

                # Vectors from ring center to loop ends
                vec1 = [math.cos(lon) * ring_ax1[i] + math.sin(lon) * ring_ax2[i] for i in range(3)]
                vec2 = [
                    math.cos(lon + dlon) * ring_ax1[i] + math.sin(lon + dlon) * ring_ax2[i]
                    for i in range(3)
                ]

                # Loop center and axes
                tmid = [0.5 * vec1[i] + 0.5 * vec2[i] for i in range(3)]
                la1 = [vec1[i] - tmid[i] for i in range(3)]
                la2 = _vhat(tmid)
                la2 = [LOOP_WIDTH * la2[i] for i in range(3)]
                ll = [tmid[i] + ring_loc[i] for i in range(3)]

                loop_axes1.append(la1)
                loop_axes2.append(la2)
                loop_locs.append(ll)
                loop_ring.append(iring + 1)  # 1-based

    # ===================================================================
    # Render scene based on ring_method
    # ===================================================================

    use_diampts = min(MAX_MINSIZE, moon_diampts)
    use_arcpts = min(MAX_ARCPTS, arc_width)

    transparent_method = 0
    semi_transparent_method = 1
    # OPAQUE_METHOD = 2

    if ring_method == transparent_method or last_opaq == 0:
        # Case 0: Transparent — simplest case
        eugeom(
            1,
            [sun_loc],
            [sun_rad],
            obs_pv[:3],
            [cmat[0], cmat[1], cmat[2]],
            nbodies,
            body_locs,
            body_axes,
            euclid_state,
        )

        _rspk_draw_bodies(
            nbodies,
            body_pts,
            body_names_list,
            body_dist,
            use_diampts,
            True,
            0.0,
            pmerids,
            plats,
            mmerids,
            mlats,
            LIT_LINE,
            DARK_LINE,
            term_line,
            LIT_LINE,
            DARK_LINE,
            term_line,
            prime_pts,
            euclid_state,
            view_state,
            escher_state,
        )

        _rspk_draw_rings(
            1,
            use_nrings,
            ring_flags,
            r_ring_locs,
            r_ring_axes1,
            r_ring_axes2,
            r_ring_dark,
            ring_dashed,
            nloops,
            loop_locs,
            loop_axes1,
            loop_axes2,
            loop_ring,
            use_arcpts,
            LIT_LINE,
            DARK_LINE,
            SHADOW_LINE,
            term_line,
            euclid_state,
            view_state,
            escher_state,
        )

    elif ring_method == semi_transparent_method:
        # Case 1: Semi-transparent — two passes
        lo = last_opaq - 1  # 0-based index for outermost opaque ring

        # First pass: unlit bodies
        eugeom(
            1,
            [sun_loc],
            [sun_rad],
            obs_pv[:3],
            [cmat[0], cmat[1], cmat[2]],
            nbodies,
            body_locs,
            body_axes,
            euclid_state,
        )
        _rspk_draw_bodies(
            nbodies,
            body_pts,
            body_names_list,
            body_dist,
            use_diampts,
            True,
            ring_rads[lo] if lo < len(ring_rads) else 0.0,
            pmerids,
            plats,
            mmerids,
            mlats,
            DARK_LINE,
            DARK_LINE,
            DARK_LINE,
            LIT_LINE,
            DARK_LINE,
            term_line,
            prime_pts,
            euclid_state,
            view_state,
            escher_state,
        )

        # Redefine with outermost opaque ring as flat ellipsoid
        ext_locs = [*body_locs, r_ring_locs[lo]]
        ext_axes = [*body_axes, [r_ring_axes1[lo], r_ring_axes2[lo], r_ring_axes3[lo]]]
        eugeom(
            1,
            [sun_loc],
            [sun_rad],
            obs_pv[:3],
            [cmat[0], cmat[1], cmat[2]],
            nbodies + 1,
            ext_locs,
            ext_axes,
            euclid_state,
        )

        # Re-draw lit, but not interior moons
        _rspk_draw_bodies(
            nbodies,
            body_pts,
            body_names_list,
            body_dist,
            use_diampts,
            False,
            ring_rads[lo] if lo < len(ring_rads) else 0.0,
            pmerids,
            plats,
            mmerids,
            mlats,
            LIT_LINE,
            DARK_LINE,
            term_line,
            NO_LINE,
            NO_LINE,
            NO_LINE,
            prime_pts,
            euclid_state,
            view_state,
            escher_state,
        )

        # Draw opaque ring invisibly
        eubody(
            nbodies + 1, 0, 0, 1, NO_LINE, NO_LINE, NO_LINE, euclid_state, view_state, escher_state
        )

        # Exterior rings
        _rspk_draw_rings(
            last_opaq + 1,
            use_nrings,
            ring_flags,
            r_ring_locs,
            r_ring_axes1,
            r_ring_axes2,
            r_ring_dark,
            ring_dashed,
            nloops,
            loop_locs,
            loop_axes1,
            loop_axes2,
            loop_ring,
            use_arcpts,
            LIT_LINE,
            DARK_LINE,
            SHADOW_LINE,
            term_line,
            euclid_state,
            view_state,
            escher_state,
        )

        # Re-define without rings
        eugeom(
            1,
            [sun_loc],
            [sun_rad],
            obs_pv[:3],
            [cmat[0], cmat[1], cmat[2]],
            nbodies,
            body_locs,
            body_axes,
            euclid_state,
        )

        # Set up bodies without drawing (for correct ring lighting)
        _rspk_draw_bodies(
            nbodies,
            body_pts,
            body_names_list,
            body_dist,
            use_diampts,
            False,
            0.0,
            pmerids,
            plats,
            mmerids,
            mlats,
            NO_LINE,
            NO_LINE,
            NO_LINE,
            NO_LINE,
            NO_LINE,
            NO_LINE,
            0.0,
            euclid_state,
            view_state,
            escher_state,
        )

        # Interior rings
        _rspk_draw_rings(
            1,
            last_opaq,
            ring_flags,
            r_ring_locs,
            r_ring_axes1,
            r_ring_axes2,
            r_ring_dark,
            ring_dashed,
            nloops,
            loop_locs,
            loop_axes1,
            loop_axes2,
            loop_ring,
            use_arcpts,
            LIT_LINE,
            DARK_LINE,
            SHADOW_LINE,
            term_line,
            euclid_state,
            view_state,
            escher_state,
        )

    else:
        # Case 2: Opaque
        lo = last_opaq - 1

        ext_locs = [*body_locs, r_ring_locs[lo]]
        ext_axes = [*body_axes, [r_ring_axes1[lo], r_ring_axes2[lo], r_ring_axes3[lo]]]
        eugeom(
            1,
            [sun_loc],
            [sun_rad],
            obs_pv[:3],
            [cmat[0], cmat[1], cmat[2]],
            nbodies + 1,
            ext_locs,
            ext_axes,
            euclid_state,
        )

        _rspk_draw_bodies(
            nbodies,
            body_pts,
            body_names_list,
            body_dist,
            use_diampts,
            True,
            ring_rads[lo] if lo < len(ring_rads) else 0.0,
            pmerids,
            plats,
            mmerids,
            mlats,
            LIT_LINE,
            DARK_LINE,
            term_line,
            NO_LINE,
            NO_LINE,
            NO_LINE,
            prime_pts,
            euclid_state,
            view_state,
            escher_state,
        )

        eubody(
            nbodies + 1, 0, 0, 1, NO_LINE, NO_LINE, NO_LINE, euclid_state, view_state, escher_state
        )

        _rspk_draw_rings(
            last_opaq + 1,
            use_nrings,
            ring_flags,
            r_ring_locs,
            r_ring_axes1,
            r_ring_axes2,
            r_ring_dark,
            ring_dashed,
            nloops,
            loop_locs,
            loop_axes1,
            loop_axes2,
            loop_ring,
            use_arcpts,
            LIT_LINE,
            DARK_LINE,
            SHADOW_LINE,
            term_line,
            euclid_state,
            view_state,
            escher_state,
        )

        # Re-define without rings
        eugeom(
            1,
            [sun_loc],
            [sun_rad],
            obs_pv[:3],
            [cmat[0], cmat[1], cmat[2]],
            nbodies,
            body_locs,
            body_axes,
            euclid_state,
        )

        # Re-draw interior moons
        _rspk_draw_bodies(
            nbodies,
            body_pts,
            body_names_list,
            body_dist,
            use_diampts,
            True,
            ring_rads[lo] if lo < len(ring_rads) else 0.0,
            pmerids,
            plats,
            mmerids,
            mlats,
            NO_LINE,
            NO_LINE,
            NO_LINE,
            LIT_LINE,
            DARK_LINE,
            term_line,
            prime_pts,
            euclid_state,
            view_state,
            escher_state,
        )

        # Interior rings
        _rspk_draw_rings(
            1,
            last_opaq,
            ring_flags,
            r_ring_locs,
            r_ring_axes1,
            r_ring_axes2,
            r_ring_dark,
            ring_dashed,
            nloops,
            loop_locs,
            loop_axes1,
            loop_axes2,
            loop_ring,
            use_arcpts,
            LIT_LINE,
            DARK_LINE,
            SHADOW_LINE,
            term_line,
            euclid_state,
            view_state,
            escher_state,
        )

    # ===================================================================
    # Box borders, tick marks, labels
    # ===================================================================

    eswrit('%Draw box...', escher_state)
    eutemp([-delta], [-delta], [-delta], [delta], 1, AXIS_LINE, view_state, escher_state)
    eutemp([-delta], [delta], [delta], [delta], 1, AXIS_LINE, view_state, escher_state)
    eutemp([delta], [delta], [delta], [-delta], 1, AXIS_LINE, view_state, escher_state)
    eutemp([delta], [-delta], [-delta], [-delta], 1, AXIS_LINE, view_state, escher_state)

    _rspk_labels2(cmat, delta, AXIS_LINE, view_state, escher_state)

    # ===================================================================
    # Moon labels
    # ===================================================================

    if moon_labelpts > 0.0:
        eswrit('%Label moons...', escher_state)
        for ibody in range(2, nbodies):
            bi = ibody  # 0-based index in body_names_list
            bname = body_names_list[bi] if bi < len(body_names_list) else ''
            if not bname.strip():
                continue
            blos = body_los[bi] if bi < len(body_los) else [0.0, 0.0, 0.0]
            bpts = body_pts[bi] if bi < len(body_pts) else 0.0
            radius = max(bpts, use_diampts) * 0.5 * fov / FOV_PTS
            _rspk_annotate(
                bname.strip(),
                blos,
                radius,
                cmat,
                delta,
                view_state,
                escher_state,
            )

    # ===================================================================
    # Stars
    # ===================================================================

    if nstars > 0:
        eswrit('%Draw stars...', escher_state)
        eslwid(_STAR_WIDTH, escher_state)

    for i in range(nstars):
        sra = star_ras[i] if i < len(star_ras) else 0.0
        sdec = star_decs[i] if i < len(star_decs) else 0.0
        los = list(_radrec(1.0, sra, sdec))
        eustar(
            (los[0], los[1], los[2]),
            1,
            STARFONT_PLUS,
            _STAR_FONTSIZE,
            star_diampts / FOV_PTS,
            STAR_LINE,
            euclid_state,
            view_state,
            escher_state,
        )
        sname = star_names[i] if i < len(star_names) else ''
        if star_labels and sname.strip():
            _rspk_annotate(
                sname.strip(),
                los,
                0.0,
                cmat,
                delta,
                view_state,
                escher_state,
            )
    if nstars > 0:
        eslwid(0.0, escher_state)

    # ===================================================================
    # Close
    # ===================================================================

    euclr(_DEVICE, 0.0, 1.0, 0.0, 1.0, escher_state)


def _vrotv(v: list[float], axis: list[float], angle: float) -> list[float]:
    """Rotate vector v around axis by angle (radians). Port of SPICE VROTV."""
    ax = _vhat(axis)
    ca = math.cos(angle)
    sa = math.sin(angle)

    # Rodrigues' rotation formula: v*cos(a) + (axis x v)*sin(a) + axis*(axis.v)*(1-cos(a))
    dot = v[0] * ax[0] + v[1] * ax[1] + v[2] * ax[2]
    cross = [
        ax[1] * v[2] - ax[2] * v[1],
        ax[2] * v[0] - ax[0] * v[2],
        ax[0] * v[1] - ax[1] * v[0],
    ]
    return [v[i] * ca + cross[i] * sa + ax[i] * dot * (1.0 - ca) for i in range(3)]
