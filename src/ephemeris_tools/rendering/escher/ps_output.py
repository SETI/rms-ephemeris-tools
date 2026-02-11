"""PostScript file handling and segment drawing (ESFILE, ESDR07, ESLWID, etc.)."""

from __future__ import annotations

from typing import TextIO

from ephemeris_tools.rendering.escher.constants import (
    _GRAY,
    BUFSZ,
    MAXX,
    MINWIDTH,
)
from ephemeris_tools.rendering.escher.state import EscherState


def _opairi(x: int, y: int, suffix: str) -> str:
    """Format ordered pair of integers as 'X Y suffix' (matches OPAIRI + MOVETO(2:))."""
    return f'{x} {y} {suffix}'


def _nint(x: float) -> int:
    """FORTRAN IDNINT: round half away from zero (not banker's rounding)."""
    if x >= 0.0:
        return int(x + 0.5)
    return -int(-x + 0.5)


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


def esopen(state: EscherState) -> None:
    """Open file and write PS header (same as first-call block in ESDR07). Call after ESFILE."""
    _ensure_open(state)


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
    from ephemeris_tools.rendering.escher.constants import MAXX, MAXY, MINX, MINY

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
    from ephemeris_tools.rendering.escher.constants import MAXX, MAXY, MINX, MINY

    return (MINX, MAXX, MINY, MAXY)
