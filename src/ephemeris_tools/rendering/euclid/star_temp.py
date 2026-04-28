"""Star symbol and overlay segments (EUSTAR, EUTEMP)."""

from __future__ import annotations

from ephemeris_tools.rendering.protocols import SegmentSink
from ephemeris_tools.rendering.euclid.state import EuclidState
from ephemeris_tools.rendering.euclid.vec_math import _mtxv


def eustar(
    strpos: tuple[float, float, float],
    nstars: int,
    font: list[tuple[tuple[float, float], tuple[float, float]]],
    fntsiz: int,
    fntscl: float,
    color: int,
    euclid_state: EuclidState,
    sink: SegmentSink,
) -> None:
    """Draw star/point markers with a line-segment font (port of EUSTAR).

    Characters are scaled by fntscl times the display size so they do not
    scale with zoom. Font is a list of ((x1,y1),(x2,y2)) segment endpoints.

    Parameters:
        strpos: Position of the point (e.g. star) in scene coordinates.
        nstars: Number of points (unused; single point drawn).
        font: Segment list for the marker; font[i] = ((x1,y1), (x2,y2)).
        fntsiz: Number of segments to use.
        fntscl: Scale factor (0-1) for marker size vs display.
        color: Color code for drawing.
        euclid_state: Euclid state.
        sink: Segment sink (Escher PostScript or matplotlib canvas).
    """
    _ = nstars
    cam = euclid_state.camera
    if cam is None:
        return
    star = _mtxv(cam, list(strpos))
    if star[2] <= 0:
        return
    center_proj_x = -star[0] / star[2]
    center_proj_y = -star[1] / star[2]

    # Glyph scale derived from FOV: scale = fntscl * half_fov_width.
    # This is mathematically equivalent to the original Escher pixel mapping
    # (0.5 * fntscl * hspan * page_width / ux) which simplifies to fntscl * delta
    # when the view region and FOV are both square.
    x1, x2, y1, y2 = euclid_state.fov
    fov_w = x2 - x1
    fov_h = y2 - y1
    if abs(fov_w) < 1.0e-12 or abs(fov_h) < 1.0e-12:
        return
    dx_proj_scale = fntscl * fov_w / 2.0
    dy_proj_scale = fntscl * fov_h / 2.0

    for i in range(min(fntsiz, len(font))):
        (fx1, fy1), (fx2, fy2) = font[i]
        proj_x1 = center_proj_x + (fx1 * dx_proj_scale)
        proj_y1 = center_proj_y + (fy1 * dy_proj_scale)
        proj_x2 = center_proj_x + (fx2 * dx_proj_scale)
        proj_y2 = center_proj_y + (fy2 * dy_proj_scale)
        beg = (-proj_x1 * star[2], -proj_y1 * star[2], star[2])
        end = (-proj_x2 * star[2], -proj_y2 * star[2], star[2])
        sink.draw(beg, end, color)
    sink.dump()


def eutemp(
    xbegin: list[float],
    ybegin: list[float],
    xend: list[float],
    yend: list[float],
    nsegs: int,
    color: int,
    sink: SegmentSink,
) -> None:
    """Draw line-segment overlay on the image plane (port of EUTEMP).

    Draws reference marks (e.g. angle scale) in image-plane coordinates.
    Segment i has start (xbegin[i], ybegin[i]) and end (xend[i], yend[i]).

    Parameters:
        xbegin: x-coordinates of segment starts.
        ybegin: y-coordinates of segment starts.
        xend: x-coordinates of segment ends.
        yend: y-coordinates of segment ends.
        nsegs: Number of segments.
        color: Color code for drawing.
        sink: Segment sink (Escher PostScript or matplotlib canvas).
    """
    if nsegs < 0:
        raise ValueError(f'nsegs must be non-negative; got {nsegs}')
    lens = (len(xbegin), len(ybegin), len(xend), len(yend))
    if len(set(lens)) != 1:
        raise ValueError(
            'eutemp segment lists must have equal lengths; '
            f'got len(xbegin)={lens[0]}, len(ybegin)={lens[1]}, '
            f'len(xend)={lens[2]}, len(yend)={lens[3]}'
        )
    cap = lens[0]
    if nsegs > cap:
        raise ValueError(
            f'nsegs={nsegs} exceeds coordinate list length {cap}'
        )
    n = min(nsegs, cap)
    for i in range(n):
        beg = (-xbegin[i], -ybegin[i], 1.0)
        end = (-xend[i], -yend[i], 1.0)
        sink.draw(beg, end, color)
    sink.dump()
