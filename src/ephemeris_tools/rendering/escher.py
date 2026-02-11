"""Escher PostScript output layer — Python port of FORTRAN Escher library.

Replicates the exact PostScript output from esdv07.f, esfile.f, eslwid.f,
eswrit.f, esmove.f so that Python viewer output can match FORTRAN byte-for-byte.

Coordinate system: 0.1 0.1 scale (1 unit = 0.1 points). All coordinates
are integers in this scaled space.
"""

from __future__ import annotations

import math
from typing import TextIO

BSIZE = 5000  # segment buffer size (5 values per segment)

# Page bounds (Escher parameters from esdv07.f)
MINX = 360
MAXX = 5760
MINY = 1800
MAXY = 7200

# Grayscale strings: segment color 0 = white, 1 = black, 2..10 = 0.1..0.9 (FORTRAN GRAY(0:10))
_GRAY: list[str] = [
    '1.0 G',  # 0 = white
    '0.0 G',  # 1 = black
    '0.1 G',
    '0.2 G',
    '0.3 G',
    '0.4 G',
    '0.5 G',
    '0.6 G',
    '0.7 G',
    '0.8 G',
    '0.9 G',
]

BUFSZ = 64
MINWIDTH = 5


class EscherState:
    """Mutable state for Escher PS output (replaces FORTRAN common block)."""

    def __init__(self) -> None:
        self.outfil = ' '
        self.creator = ' '
        self.fonts = ' '
        self.outuni: TextIO | None = None
        self.xsave = 0
        self.ysave = 0
        self.drawn = False
        self.open = False
        self.oldcol = -9999
        self.oldwidth = MINWIDTH
        self.external_stream = False  # If True, ESCL07 full-page does not close outuni.


def _opairi(x: int, y: int, suffix: str) -> str:
    """Format ordered pair of integers as 'X Y suffix' (matches OPAIRI + MOVETO(2:))."""
    return f'{x} {y} {suffix}'


def esfile(
    filename: str,
    creator: str,
    fonts: str,
    state: EscherState,
) -> None:
    """Set output filename, creator, and fonts. Initialize state (port of ESFILE)."""
    state.outfil = filename.strip() if filename else ' '
    state.creator = (creator or ' ').strip()
    state.fonts = (fonts or ' ').strip()
    state.outuni = None
    state.drawn = False


def esopen(state: EscherState) -> None:
    """Open file and write PS header (same as first-call block in ESDR07). Call after ESFILE."""
    _ensure_open(state)


def write_ps_header(state: EscherState) -> None:
    """Write the PS file header to state.outuni.

    Use when output stream is already set (e.g. by caller).
    """
    if state.outuni is None:
        return
    outfil = (state.outfil or '').strip() or 'view.ps'
    f2 = len(outfil)
    f1 = f2
    for i in range(f2 - 1, -1, -1):
        if outfil[i] in '/:]':
            f1 = i
            break
    title = outfil[f1 + 1 : f2] if f1 < f2 else outfil
    creator_nb = (state.creator or '').rstrip()
    fonts_nb = (state.fonts or '').rstrip()
    f = state.outuni
    f.write('%!PS-Adobe-2.0 EPSF-2.0\n')
    f.write(f'%%Title: {title}\n')
    f.write(f'%%Creator: {creator_nb}\n')
    f.write('%%BoundingBox: 0 0 612 792\n')
    f.write('%%Pages: 1\n')
    f.write(f'%%DocumentFonts: {fonts_nb}\n')
    f.write('%%EndComments\n')
    f.write('% \n')
    f.write('0.1 0.1 scale\n')
    f.write('8 setlinewidth\n')
    f.write('1 setlinecap\n')
    f.write('1 setlinejoin\n')
    f.write('/L {lineto} def\n')
    f.write('/M {moveto} def\n')
    f.write('/N {newpath} def\n')
    f.write('/G {setgray} def\n')
    f.write('/S {stroke} def\n')


def _ensure_open(state: EscherState) -> TextIO:
    """Open file on first use and write PS header (from ESDR07 first-call block)."""
    if state.outuni is not None:
        return state.outuni
    state.open = True
    outfil = state.outfil.strip() or 'escher.ps'
    # Extract basename for %%Title (last path component)
    f2 = len(outfil)
    f1 = f2
    for i in range(f2 - 1, -1, -1):
        if outfil[i] in '/:]':
            f1 = i
            break
    title = outfil[f1 + 1 : f2] if f1 < f2 else outfil
    creator_nb = state.creator.rstrip()
    fonts_nb = state.fonts.rstrip()
    # File is stored in state.outuni and must stay open for subsequent writes (SIM115).
    f = open(outfil, 'w', encoding='utf-8')  # noqa: SIM115
    state.outuni = f
    f.write('%!PS-Adobe-2.0 EPSF-2.0\n')
    f.write(f'%%Title: {title}\n')
    f.write(f'%%Creator: {creator_nb}\n')
    f.write('%%BoundingBox: 0 0 612 792\n')
    f.write('%%Pages: 1\n')
    f.write(f'%%DocumentFonts: {fonts_nb}\n')
    f.write('%%EndComments\n')
    f.write('% \n')
    f.write('0.1 0.1 scale\n')
    f.write('8 setlinewidth\n')
    f.write('1 setlinecap\n')
    f.write('1 setlinejoin\n')
    f.write('/L {lineto} def\n')
    f.write('/M {moveto} def\n')
    f.write('/N {newpath} def\n')
    f.write('/G {setgray} def\n')
    f.write('/S {stroke} def\n')
    return f


def esdr07(nsegs: int, segs: list[int], state: EscherState) -> None:
    """Draw segment buffer to PostScript (port of ESDR07).

    segs: flat list of 5-tuples (BP, BL, EP, EL, COLOR) per segment.
    nsegs: number of values (must be multiple of 5).
    """
    if nsegs < 5:
        return
    f = _ensure_open(state)
    # Group connected segments with same color
    offset = 0
    bp = segs[offset]
    bl = segs[offset + 1]
    ep = segs[offset + 2]
    el = segs[offset + 3]
    color = segs[offset + 4]
    xarray = [bp, ep]
    yarray = [bl, el]
    count = 2
    lstcol = segs[4]
    lastep = ep
    lastel = el
    maxdsp = max(abs(ep - bp), abs(el - bl))

    i = 5
    while i < nsegs:
        offset = i
        bp = segs[offset]
        bl = segs[offset + 1]
        ep = segs[offset + 2]
        el = segs[offset + 3]
        color = segs[offset + 4]

        if bp == lastep and bl == lastel and color == lstcol and count < BUFSZ:
            lastep = ep
            lastel = el
            maxdsp = max(maxdsp, max(abs(ep - bp), abs(el - bl)))
            count += 1
            xarray.append(ep)
            yarray.append(el)
        else:
            # Flush current path
            if maxdsp == 0:
                if xarray[count - 1] < MAXX:
                    xarray[count - 1] = xarray[count - 1] + 1
                else:
                    xarray[count - 1] = xarray[count - 1] - 1
            if lstcol >= 0:
                f.write('N\n')
                f.write(_opairi(xarray[0], yarray[0], 'M') + '\n')
                state.xsave = xarray[0]
                state.ysave = yarray[0]
                lastln = _opairi(xarray[0], yarray[0], 'L')
                for m in range(1, count):
                    lineto = _opairi(xarray[m], yarray[m], 'L')
                    if lineto != lastln:
                        f.write(lineto + '\n')
                        state.xsave = xarray[m]
                        state.ysave = yarray[m]
                        state.drawn = True
                    lastln = lineto
                col_out = 1 if lstcol > 10 else lstcol
                if col_out != state.oldcol and col_out >= 0:
                    f.write(_GRAY[min(col_out, 10)] + '\n')
                    state.oldcol = col_out
                f.write('S\n')

            count = 2
            xarray = [bp, ep]
            yarray = [bl, el]
            maxdsp = max(abs(ep - bp), abs(el - bl))
            lstcol = color
            lastep = ep
            lastel = el
        i += 5

    # Flush remaining path
    if maxdsp == 0:
        if xarray[count - 1] < MAXX:
            xarray[count - 1] = xarray[count - 1] + 1
        else:
            xarray[count - 1] = xarray[count - 1] - 1
    if lstcol >= 0:
        f.write('N\n')
        f.write(_opairi(xarray[0], yarray[0], 'M') + '\n')
        state.xsave = xarray[0]
        state.ysave = yarray[0]
        lastln = _opairi(xarray[0], yarray[0], 'L')
        for m in range(1, count):
            lineto = _opairi(xarray[m], yarray[m], 'L')
            if lineto != lastln:
                f.write(lineto + '\n')
                state.xsave = xarray[m]
                state.ysave = yarray[m]
                state.drawn = True
            lastln = lineto
        col_out = 1 if lstcol > 10 else lstcol
        if col_out != state.oldcol and col_out >= 0:
            f.write(_GRAY[min(col_out, 10)] + '\n')
            state.oldcol = col_out
        f.write('S\n')


def eslwid(points: float, state: EscherState) -> None:
    """Set line width in points (port of ESLWID). Writes only when changed."""
    if state.outuni is None:
        return
    width = max(_nint(points * 10.0), MINWIDTH)
    if width == state.oldwidth:
        return
    state.outuni.write(f'{width:3d} setlinewidth\n')
    state.oldwidth = width


def eswrit(string: str, state: EscherState) -> None:
    """Write raw string to PostScript file (port of ESWRIT)."""
    if state.outuni is None:
        return
    state.outuni.write(string)
    if string and not string.endswith('\n'):
        state.outuni.write('\n')


def esmove(state: EscherState) -> None:
    """Emit moveto to last stroked point (port of ESMOVE)."""
    if state.outuni is None:
        return
    state.outuni.write(_opairi(state.xsave, state.ysave, 'M') + '\n')


def escl07(hmin: int, hmax: int, vmin: int, vmax: int, state: EscherState) -> None:
    """Clear region or close page (port of ESCL07).

    If (hmin,hmax,vmin,vmax) equals (MINX,MAXX,MINY,MAXY), writes showpage and closes.
    Otherwise draws white filled rectangle.
    """
    if state.outuni is None:
        return
    if hmin == MINX and hmax == MAXX and vmin == MINY and vmax == MAXY:
        state.outuni.write('showpage\n')
        if not getattr(state, 'external_stream', False):
            state.outuni.close()
            state.outuni = None
            state.open = False
        return
    f = state.outuni
    f.write('% \n')
    f.write('% CLEAR PART OF THE PAGE\n')
    f.write('% \n')
    f.write('N\n')
    f.write(_opairi(hmin, vmin, 'M') + '\n')
    f.write(_opairi(hmin, vmax, 'L') + '\n')
    f.write(_opairi(hmax, vmax, 'L') + '\n')
    f.write(_opairi(hmax, vmin, 'L') + '\n')
    f.write(_opairi(hmin, vmin, 'L') + '\n')
    f.write('closepath\n')
    f.write('1 G\n')
    f.write('fill\n')
    f.write('0 G\n')
    state.oldcol = 1


def espl07() -> tuple[int, int, int, int]:
    """Return graphics boundaries (port of ESPL07)."""
    return (MINX, MAXX, MINY, MAXY)


# --- Escher view/draw/dump bridge (escher.f + esmap.f + esclip.f) ---


class EscherViewState:
    """Viewport and FOV for 3D->2D mapping; segment buffer for ESDRAW/ESDUMP."""

    def __init__(self) -> None:
        self.device = 0
        self.view = (0.0, 0.0, 0.0, 0.0)  # Hmin, Hmax, Vmin, Vmax (0-1)
        self.fov = (0.0, 0.0, 0.0, 0.0)  # Xmin, Xmax, Ymin, Ymax
        self._xmin = 0.0
        self._xmax = 0.0
        self._ymin = 0.0
        self._ymax = 0.0
        self._ux = 0.0
        self._uy = 0.0
        self._xcen = 0.0
        self._ycen = 0.0
        self._pcen = 0.0
        self._lcen = 0.0
        self.segbuf: list[int] = []
        self._initialized = False


def _esclip(
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
) -> tuple[float, float, float, float, bool]:
    """Clip segment to rectangle (port of ESCLIP).

    FORTRAN treats boundary points (x==xmin, etc.) as INSIDE the
    rectangle (region 9).  Intersection tests use strict inequalities.
    """
    # ------------------------------------------------------------------
    # Classify first endpoint into regions (FORTRAN uses strict .GT./.LT.)
    # ------------------------------------------------------------------
    onensd = False
    twonsd = False
    check = False

    if x1 > xmax:
        if y1 > ymax:
            check = (x2 < xmax) and (y2 < ymax)
        elif y1 < ymin:
            check = (x2 < xmax) and (y2 > ymin)
        else:
            check = x2 < xmax
    elif x1 < xmin:
        if y1 > ymax:
            check = (x2 > xmin) and (y2 < ymax)
        elif y1 < ymin:
            check = (x2 > xmin) and (y2 > ymin)
        else:
            check = x2 > xmin
    else:
        # x1 is between xmin and xmax (inclusive)
        if y1 > ymax:
            check = y2 < ymax
        elif y1 < ymin:
            check = y2 > ymin
        else:
            # Region 9: first endpoint inside (boundary counts as inside)
            check = (x2 > xmax) or (x2 < xmin) or (y2 > ymax) or (y2 < ymin)
            if not check:
                return (x1, y1, x2, y2, True)
            onensd = True

    if not check:
        return (x1, y1, x2, y2, False)

    # ------------------------------------------------------------------
    # At least one endpoint needs clipping
    # ------------------------------------------------------------------
    if onensd:
        possbl = 1
    else:
        twonsd = (x2 <= xmax) and (x2 >= xmin) and (y2 <= ymax) and (y2 >= ymin)
        possbl = 1 if twonsd else 2

    nwpnts = 0
    xend = [0.0, 0.0]
    yend = [0.0, 0.0]

    dx = x2 - x1
    dy = y2 - y1

    # Horizontal segment special case
    if dy == 0.0:
        if (x1 < xmin) and (x2 > xmax):
            return (xmin, y1, xmax, y2, True)
        if (x1 < xmin) and (x2 > xmin):
            return (xmin, y1, x2, y2, True)
        if (x2 < xmin) and (x1 > xmax):
            return (xmax, y1, xmin, y2, True)
        if (x2 < xmin) and (x1 > xmin):
            return (x1, y1, xmin, y2, True)

    # Vertical segment special case
    if dx == 0.0:
        if (y1 < ymin) and (y2 > ymax):
            return (x1, ymin, x2, ymax, True)
        if (y1 < ymin) and (y2 > ymin):
            return (x1, ymin, x2, y2, True)
        if (y2 < ymin) and (y1 > ymax):
            return (x1, ymax, x2, ymin, True)
        if (y2 < ymin) and (y1 > ymin):
            return (x1, y1, x2, ymin, True)

    # General case: check intersections with all four edges
    # Top edge
    ymaxy1 = ymax - y1
    if nwpnts < possbl and ((0 < ymaxy1 < dy) or (0 > ymaxy1 > dy)):
        s = ymaxy1 / dy
        x = s * dx + x1
        if (x < xmax) and (x > xmin):
            xend[nwpnts] = x
            yend[nwpnts] = ymax
            nwpnts += 1

    # Bottom edge
    yminy1 = ymin - y1
    if nwpnts < possbl and ((0 < yminy1 < dy) or (0 > yminy1 > dy)):
        s = yminy1 / dy
        x = s * dx + x1
        if (x < xmax) and (x > xmin):
            xend[nwpnts] = x
            yend[nwpnts] = ymin
            nwpnts += 1

    # Right edge
    xmaxx1 = xmax - x1
    if nwpnts < possbl and ((0 < xmaxx1 < dx) or (0 > xmaxx1 > dx)):
        s = xmaxx1 / dx
        y = s * dy + y1
        if (y < ymax) and (y > ymin):
            xend[nwpnts] = xmax
            yend[nwpnts] = y
            nwpnts += 1

    # Left edge
    xminx1 = xmin - x1
    if nwpnts < possbl and ((0 < xminx1 < dx) or (0 > xminx1 > dx)):
        s = xminx1 / dx
        y = s * dy + y1
        if (y < ymax) and (y > ymin):
            xend[nwpnts] = xmin
            yend[nwpnts] = y
            nwpnts += 1

    if nwpnts == possbl:
        start = 0
        rx1, ry1 = x1, y1
        rx2, ry2 = x2, y2
        if not onensd:
            rx1 = xend[start]
            ry1 = yend[start]
            start += 1
        if not twonsd:
            rx2 = xend[start]
            ry2 = yend[start]
        return (rx1, ry1, rx2, ry2, True)

    return (x1, y1, x2, y2, False)


def esview(
    device: int,
    view: tuple[float, float, float, float],
    fov: tuple[float, float, float, float],
    view_state: EscherViewState,
    escher_state: EscherState,
) -> None:
    """Set device, viewport (0-1), and FOV; set up mapping (port of ESVIEW + ESMAP1)."""
    view_state.device = device
    view_state.view = view
    view_state.fov = fov
    view_state.segbuf = []
    hmin, hmax, vmin, vmax = view
    xmin, xmax, ymin, ymax = fov
    view_state._xmin = xmin
    view_state._xmax = xmax
    view_state._ymin = ymin
    view_state._ymax = ymax
    if xmax == xmin:
        raise ValueError(f'FOV has zero width: xmin={xmin!r}, xmax={xmax!r}')
    if ymax == ymin:
        raise ValueError(f'FOV has zero height: ymin={ymin!r}, ymax={ymax!r}')
    left, right, bottom, top = espl07()
    pix0, pix1 = float(left), float(right)
    lam0, lam1 = float(bottom), float(top)
    ux = (hmax - hmin) * (pix1 - pix0) / (xmax - xmin)
    uy = (vmax - vmin) * (lam1 - lam0) / (ymax - ymin)
    u = min(abs(ux), abs(uy))
    ux = math.copysign(u, ux)
    uy = math.copysign(u, uy)
    view_state._ux = ux
    view_state._uy = uy
    view_state._xcen = (xmin + xmax) / 2.0
    view_state._ycen = (ymin + ymax) / 2.0
    view_state._pcen = pix0 + (hmax + hmin) * (pix1 - pix0) / 2.0
    view_state._lcen = lam0 + (vmax + vmin) * (lam1 - lam0) / 2.0
    view_state._initialized = True
    _ = escher_state  # unused but required for API


def _nint(x: float) -> int:
    """FORTRAN IDNINT: round half away from zero (not banker's rounding)."""
    if x >= 0.0:
        return int(x + 0.5)
    return -int(-x + 0.5)


def _esmap2(x: float, y: float, view_state: EscherViewState) -> tuple[int, int]:
    """Map projection (x,y) to pixel/line (port of ESMAP2)."""
    p = _nint(view_state._pcen + view_state._ux * (x - view_state._xcen))
    line = _nint(view_state._lcen + view_state._uy * (y - view_state._ycen))
    return (p, line)


# Epsilon for points near the camera plane (z=0) to avoid zero division in projection
_ESDRAW_EPS = 1e-12


def esdraw(
    begin: tuple[float, float, float],
    end: tuple[float, float, float],
    color: int,
    view_state: EscherViewState,
    escher_state: EscherState,
) -> None:
    """Project 3D segment to 2D, clip, map, buffer; flush if full (port of ESDRAW)."""
    if not view_state._initialized or view_state.device == 0:
        return
    sign1 = 1.0 if begin[2] >= 0 else -1.0
    sign2 = 1.0 if end[2] >= 0 else -1.0
    z1 = begin[2] if abs(begin[2]) >= _ESDRAW_EPS else sign1 * _ESDRAW_EPS
    z2 = end[2] if abs(end[2]) >= _ESDRAW_EPS else sign2 * _ESDRAW_EPS
    bx = -begin[0] / z1
    by = -begin[1] / z1
    ex = -end[0] / z2
    ey = -end[1] / z2
    bx, by, ex, ey, inside = _esclip(
        view_state._xmin,
        view_state._xmax,
        view_state._ymin,
        view_state._ymax,
        bx,
        by,
        ex,
        ey,
    )
    if not inside:
        return
    p1, l1 = _esmap2(bx, by, view_state)
    p2, l2 = _esmap2(ex, ey, view_state)
    view_state.segbuf.extend([p1, l1, p2, l2, color])
    if len(view_state.segbuf) >= BSIZE:
        n = len(view_state.segbuf)
        segs = view_state.segbuf[:]
        view_state.segbuf = []
        esdr07(n, segs, escher_state)


def esdump(view_state: EscherViewState, escher_state: EscherState) -> None:
    """Flush segment buffer to ESDR07 (port of ESDUMP)."""
    if not view_state.segbuf:
        return
    n = len(view_state.segbuf)
    segs = view_state.segbuf[:]
    view_state.segbuf = []
    esdr07(n, segs, escher_state)


def esclr(
    device: int,
    region: tuple[float, float, float, float],
    escher_state: EscherState,
) -> None:
    """Clear viewport (port of ESCLR). Region is (Hmin,Hmax,Vmin,Vmax) in 0-1."""
    _ = device
    hmin, hmax, vmin, vmax = region
    left, right, bottom, top = espl07()
    pix0 = float(left)
    pix1 = float(right)
    line0 = float(bottom)
    line1 = float(top)
    hmin, hmax = min(hmin, hmax), max(hmin, hmax)
    vmin, vmax = min(vmin, vmax), max(vmin, vmax)
    ihmin = _nint(pix0 + hmin * (pix1 - pix0))
    ihmax = _nint(pix0 + hmax * (pix1 - pix0))
    ivmin = _nint(line0 + vmin * (line1 - line0))
    ivmax = _nint(line0 + vmax * (line1 - line0))
    escl07(ihmin, ihmax, ivmin, ivmax, escher_state)
