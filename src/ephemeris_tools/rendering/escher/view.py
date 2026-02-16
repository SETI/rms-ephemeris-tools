"""Viewport, 3D->2D mapping, segment buffer and clip (ESVIEW, ESDRAW, ESDUMP, ESCLR)."""

from __future__ import annotations

import math

from ephemeris_tools.rendering.escher.constants import BSIZE
from ephemeris_tools.rendering.escher.ps_output import (
    _nint,
    escl07,
    esdr07,
    espl07,
)
from ephemeris_tools.rendering.escher.state import EscherState, EscherViewState


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
    """Clip line segment to rectangle (port of ESCLIP).

    Boundary points (x==xmin, etc.) are treated as inside the rectangle.
    Intersection tests use strict inequalities.

    Parameters:
        xmin, xmax, ymin, ymax: Rectangle bounds.
        x1, y1: First endpoint of segment.
        x2, y2: Second endpoint of segment.

    Returns:
        Tuple of (clipped_x1, clipped_y1, clipped_x2, clipped_y2, inside).
        inside is False if segment is entirely outside.
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


def _esmap2(x: float, y: float, view_state: EscherViewState) -> tuple[int, int]:
    """Map point in projection (x,y) space to device pixel/line (port of ESMAP2).

    Parameters:
        x, y: Coordinates in projection (FOV) space.
        view_state: View state from esview (must be initialized).

    Returns:
        Tuple of (pixel, line) in device coordinates.
    """
    p = _nint(view_state._pcen + view_state._ux * (x - view_state._xcen))
    line = _nint(view_state._lcen + view_state._uy * (y - view_state._ycen))
    return (p, line)


# Epsilon for points near the camera plane (z=0) to avoid zero division in projection
_ESDRAW_EPS = 1e-12


def esview(
    device: int,
    view: tuple[float, float, float, float],
    fov: tuple[float, float, float, float],
    view_state: EscherViewState,
    escher_state: EscherState,
) -> None:
    """Set display device, viewport, and FOV; set up projection mapping (ESVIEW + ESMAP1).

    VIEW is the region of the device (0-1 in H and V). FOV is the field of view
    rectangle in projection space (xmin, xmax, ymin, ymax). Scaling preserves
    aspect ratio (squares in projection map to squares on device).

    Parameters:
        device: Graphics device number.
        view: (Hmin, Hmax, Vmin, Vmax) in 0-1.
        fov: (Xmin, Xmax, Ymin, Ymax) in projection space.
        view_state: Updated with mapping and segment buffer cleared.
        escher_state: Escher output state (unused but required for API).

    Raises:
        ValueError: If FOV has zero width or height.
    """
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


def esdraw(
    begin: tuple[float, float, float],
    end: tuple[float, float, float],
    color: int,
    view_state: EscherViewState,
    escher_state: EscherState,
) -> None:
    """Draw a 3D line segment: project to 2D, clip to FOV, map to device, buffer (port of ESDRAW).

    Segments are buffered; when buffer is full they are flushed to PostScript
    via esdr07. Call esdump to flush remaining segments.

    Parameters:
        begin: Start point (x, y, z) in projection space (z > 0 visible).
        end: End point (x, y, z).
        color: Color code for the segment.
        view_state: View state from esview.
        escher_state: Escher output state.
    """
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
    """Flush segment buffer to PostScript (port of ESDUMP).

    Writes all buffered segments via esdr07 and clears the buffer.

    Parameters:
        view_state: View state (segbuf cleared).
        escher_state: Escher output state.
    """
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
    """Clear a region of the display (port of ESCLR).

    Region is (Hmin, Hmax, Vmin, Vmax) in 0-1. Full page clear writes
    showpage and may close the file (unless external_stream is set).

    Parameters:
        device: Graphics device (unused; kept for API compatibility).
        region: (Hmin, Hmax, Vmin, Vmax) in 0-1.
        escher_state: Escher output state.
    """
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
