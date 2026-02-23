"""Shared constants and helper functions for draw_view (port of rspk_drawview.f)."""

from __future__ import annotations

import math
import struct
import time as _time

import cspyce

from ephemeris_tools.rendering.escher import (
    EscherState,
    EscherViewState,
    eslwid,
    esmove,
    eswrit,
)
from ephemeris_tools.rendering.euclid import (
    EuclidState,
    eubody,
    euring,
    eutemp,
)

# ---------------------------------------------------------------------------
# Constants (from rspk_drawview.f)
# ---------------------------------------------------------------------------

# PostScript: points per inch (standard); layout positions in points
_PS_POINTS_PER_INCH = 72.0
FOV_PTS = 7.0 * _PS_POINTS_PER_INCH  # 504.0
# Moon label font scale: scale = min(labelpts / MOON_LABEL_SCALE_DIVISOR, MOON_LABEL_SCALE_CAP)
MOON_LABEL_SCALE_DIVISOR = 12.0
MOON_LABEL_SCALE_CAP = 2.0
_DEVICE = 7
_H1 = 0.066666667
_H2 = 1.0
_V1 = 0.988888889
_V2 = 0.055555556
LIT_LINE = 1
DARK_LINE = 7
SHADOW_LINE = 10
AXIS_LINE = 1
NO_LINE = -1
STAR_LINE = 1
_STAR_FONTSIZE = 2
_STAR_WIDTH = 1.5
_STAR_DIAMPTS = 24.0
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
_MINSTEPS = 3.0
_TICKSIZE1 = 0.05
_TICKSIZE2 = 0.02
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
    return float(struct.unpack('!f', struct.pack('!f', value))[0])


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


def _rspk_escape(s: str) -> str:
    """Escape a string for PostScript: backslashes, parentheses, and degree symbol.

    The Unicode degree character (U+00B0) is emitted as UTF-8 (C2 B0), which
    PostScript interprets as two bytes; the first (0xC2) can render as a prime
    (U+2032) with common fonts. Replacing it with the PostScript escape \\260
    yields a single byte 0xB0 so only the degree glyph is shown.
    """
    return (
        s.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)').replace('\u00b0', '\\260')
    )


def _rspk_write_string(s: str, state: EscherState) -> None:
    """Write a PostScript-format string with escaped backslashes and parentheses."""
    eswrit(f'({_rspk_escape(s)})', state)


def _rspk_write_label(
    secs: float,
    offset: str,
    escher_state: EscherState,
) -> None:
    """Write a numeric label at the current point in deg/min/sec (port of RSPK_WriteLabel)."""
    secs1 = secs
    if offset == 'B':
        secs1 = secs1 % _MAXSECS
        if secs1 < 0.0:
            secs1 += _MAXSECS
    fsign = 1.0 if secs1 >= 0 else -1.0
    fsecs = abs(secs1)
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
    if (offset == 'B' and ims == 0) or (offset == 'L' and ims == 0):
        s = f'{ideg:3d} {imin:02d} {isec:02d}'
    else:
        s = s.rstrip('0 ').rstrip('.')
    s = s.lstrip()
    if fsign < 0:
        s = '-' + s
    esmove(escher_state)
    safe = _rspk_escape(s)
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
    """Write body name at position (port of RSPK_Annotate)."""
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
        name_safe = _rspk_escape(name)
        eswrit(f'({name_safe}) LabelBody', escher_state)


def _rspk_labels2(
    cmatrix: list[list[float]],
    delta: float,
    ltype: int,
    view_state: EscherViewState,
    escher_state: EscherState,
) -> None:
    """Plot RA/Dec tick marks and numeric labels on the figure (port of RSPK_Labels2)."""
    dpr = DPR
    _rng, ra, dec = cspyce.recrad((cmatrix[0][2], cmatrix[1][2], cmatrix[2][2]))
    delta_ra = delta / math.cos(dec) if abs(math.cos(dec)) > 1e-12 else delta
    dtick1 = _TICKSIZE1 * delta
    dtick2 = _TICKSIZE2 * delta
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
    _eps = 1e-12
    for k in range(k1, k2 + 1):
        s = k * ds
        length = dtick2
        ismajor = (k % nsubs) == 0
        if ismajor:
            length = dtick1
        j2000_los = cspyce.radrec(1.0, s / spr, dec)
        cam = list(cspyce.mtxv(cmatrix, j2000_los))
        if cam[2] <= _eps or abs(cam[2]) < _eps:
            continue
        x = -cam[0] / cam[2]
        if abs(x) <= delta:
            eutemp([x], [delta - length], [x], [delta], 1, ltype, view_state, escher_state)
            if ismajor:
                _rspk_write_label(s, 'B', escher_state)
            eutemp([x], [-delta + length], [x], [-delta], 1, ltype, view_state, escher_state)
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
        if cam[2] <= _eps or abs(cam[2]) < _eps:
            continue
        y = -cam[1] / cam[2]
        if abs(y) <= delta:
            eutemp([-delta + length], [y], [-delta], [y], 1, ltype, view_state, escher_state)
            if ismajor:
                _rspk_write_label(s, 'L', escher_state)
            eutemp([delta - length], [y], [delta], [y], 1, ltype, view_state, escher_state)


def _rspk_draw_bodies(
    *,
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
    """Draw all bodies (planet and moons) with terminators (port of RSPK_DrawBodies)."""
    l1, l2, l3 = lit_line, dark_line, term_line
    isvis = l1 != 0 or l2 != 0 or l3 != 0
    if isvis:
        eswrit('%Draw planet...', escher_state)
    if isvis and prime_pts > 0.0:
        eslwid(prime_pts, escher_state)
        eubody(1, 1, 0, 1, l1, l2, 0, euclid_state, view_state, escher_state)
        eubody(1, 0, 0, 1, 0, 0, 0, euclid_state, view_state, escher_state)
    eslwid(0.0, escher_state)
    eubody(1, pmerids, plats, 1, l1, l2, l3, euclid_state, view_state, escher_state)
    eubody(2, 2, 1, 1, 0, 0, 0, euclid_state, view_state, escher_state)
    for ibody in range(3, nbodies + 1):
        bi = ibody - 1
        inner = (body_dist[bi] < mindist) if bi < len(body_dist) else False
        bl1, bl2, bl3 = (lit_line2, dark_line2, term_line2) if inner else (l1, l2, l3)
        bvis = bl1 != 0 or bl2 != 0 or bl3 != 0
        bname = body_names[bi] if bi < len(body_names) else ''
        if bvis and bname.strip():
            eswrit(f'%Draw {bname.strip()}...', escher_state)
        bpts = body_pts[bi] if bi < len(body_pts) else 0.0
        if bvis and prime_pts > 0.0 and body_diampts == 0.0 and bpts > body_diampts * 8.0:
            eslwid(prime_pts, escher_state)
            eubody(ibody, 1, 0, 1, bl1, bl2, 0, euclid_state, view_state, escher_state)
            eubody(ibody, 0, 0, 1, 0, 0, 0, euclid_state, view_state, escher_state)
        escher_state.drawn = False
        eslwid(body_diampts - bpts, escher_state)
        eubody(ibody, mmerids, mlats, 1, bl1, bl2, bl3, euclid_state, view_state, escher_state)
        if update_names and bvis and not escher_state.drawn and bi < len(body_names):
            body_names[bi] = ' '
    eslwid(0.0, escher_state)


def _rspk_draw_rings(
    *,
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
    """Draw all rings and arc segments (port of RSPK_DrawRings)."""
    for iring in range(iring1, iring2 + 1):
        ri = iring - 1
        if ri < 0 or ri >= len(ring_flags) or not ring_flags[ri]:
            continue
        draw_line = dark_line if ring_dark[ri] else lit_line
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
    if nloops > 0:
        eswrit('%Draw arcs...', escher_state)
    eslwid(arc_width, escher_state)
    for iloop in range(nloops):
        iring = loop_ring[iloop]
        if iring1 <= iring <= iring2:
            ri = iring - 1
            draw_line = dark_line if (0 <= ri < len(ring_dark) and ring_dark[ri]) else lit_line
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
    """Camera orientation matrix for center (ra, dec) in J2000 (port of RSPK_DrawView)."""
    col3 = list(cspyce.radrec(1.0, center_ra_rad, center_dec_rad))
    temp = list(cspyce.vperp((0.0, 0.0, 1.0), col3))
    n2 = math.sqrt(temp[0] * temp[0] + temp[1] * temp[1] + temp[2] * temp[2])
    col2 = list(cspyce.vhat(temp)) if n2 >= 1e-12 else [1.0, 0.0, 0.0]
    col1 = list(cspyce.vcrss(col2, col3))
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
    cmat: list[list[float]] | None = None,
) -> tuple[float, float] | None:
    """Convert (ra, dec) to plot coordinates (x, y) in points. Returns None if behind camera."""
    if fov_rad <= 0:
        raise ValueError('fov_rad must be positive')
    if cmat is None:
        cmat = camera_matrix(center_ra_rad, center_dec_rad)
    los = list(cspyce.radrec(1.0, ra_rad, dec_rad))
    cam = list(cspyce.mtxv(cmat, los))
    if cam[2] <= 0.0:
        return None
    half = math.tan(fov_rad / 2.0)
    x_plot = -FOV_PTS * cam[0] / (cam[2] * 2.0 * half)
    y_plot = -FOV_PTS * cam[1] / (cam[2] * 2.0 * half)
    return (x_plot, y_plot)


def _generated_date_str() -> str:
    """Return current date for Generated-by footer (match FDATE format)."""
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


def _vrotv(v: list[float], axis: list[float], angle: float) -> list[float]:
    """Rotate vector v around axis by angle (radians). Port of SPICE VROTV."""
    ax = _vhat(axis)
    if _vnorm(ax) == 0.0:
        raise ValueError('axis must be non-zero')
    ca = math.cos(angle)
    sa = math.sin(angle)
    dot = v[0] * ax[0] + v[1] * ax[1] + v[2] * ax[2]
    cross = [
        ax[1] * v[2] - ax[2] * v[1],
        ax[2] * v[0] - ax[0] * v[2],
        ax[0] * v[1] - ax[1] * v[0],
    ]
    return [v[i] * ca + cross[i] * sa + ax[i] * dot * (1.0 - ca) for i in range(3)]


def _write_ps_preamble(
    escher_state: EscherState,
    planet_name: str,
    title: str,
    ncaptions: int,
    lcaptions: list[str],
    rcaptions: list[str],
    align_loc: float,
    moon_labelpts: float,
) -> None:
    """Write PostScript preamble macros, title, captions, credit footer, and axis labels."""
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
    scale_val = (
        min(moon_labelpts / MOON_LABEL_SCALE_DIVISOR, MOON_LABEL_SCALE_CAP)
        if moon_labelpts > 0.0
        else 1.0
    )
    scale_str = f'{scale_val:.3f}'
    eswrit('/LabelBody {gsave currentpoint translate', escher_state)
    eswrit('unscale', escher_state)
    eswrit(f'{scale_str} {scale_str} scale', escher_state)
    eswrit('TextHeight 0.2 mul dup', escher_state)
    eswrit('moveto show grestore} def', escher_state)
    eswrit('%%EndProlog', escher_state)
    eswrit('%', escher_state)
    if title.strip():
        eswrit('gsave unscale 324 756 translate 1.4 1.4 scale', escher_state)
        _rspk_write_string(title.strip(), escher_state)
        eswrit('dup stringwidth pop', escher_state)
        eswrit('-0.5 mul TextHeight neg moveto show grestore', escher_state)
    if ncaptions > 0:
        eswrit('gsave unscale', escher_state)
        align_int = _fortran_nint(align_loc) + int(_PS_POINTS_PER_INCH)
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
    eswrit(
        f'gsave unscale {int(_PS_POINTS_PER_INCH)} 36 translate 0.5 0.5 scale',
        escher_state,
    )
    eswrit('0 0 moveto', escher_state)
    date_str = _generated_date_str()
    footer_text = (
        f'Generated by the {_rspk_escape(planet_name)} Viewer Tool, '
        f'PDS Ring-Moon Systems Node, {_rspk_escape(date_str)}'
    )
    eswrit(f'({footer_text})', escher_state)
    eswrit('show grestore', escher_state)
    eswrit('gsave unscale', escher_state)
    eswrit('324 180 translate 1.2 1.2 scale', escher_state)
    eswrit('(Right Ascension (h m s)) dup stringwidth pop', escher_state)
    eswrit('-0.5 mul 0 moveto show grestore', escher_state)
    eswrit('gsave unscale', escher_state)
    eswrit('36 450 translate 1.2 1.2 scale 90 rotate', escher_state)
    eswrit('(Declination (d m s)) dup stringwidth pop', escher_state)
    eswrit('-0.5 mul TextHeight neg moveto show grestore', escher_state)
