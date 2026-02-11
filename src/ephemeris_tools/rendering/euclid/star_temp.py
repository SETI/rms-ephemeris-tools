"""Star symbol and overlay segments (EUSTAR, EUTEMP)."""

from __future__ import annotations

from ephemeris_tools.rendering.escher import (
    EscherState,
    EscherViewState,
    esdraw,
    esdump,
)
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
    view_state: EscherViewState,
    escher_state: EscherState,
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
        view_state: Escher view state.
        escher_state: Escher output state.
    """
    _ = nstars
    cam = euclid_state.camera
    if cam is None:
        return
    star = _mtxv(cam, list(strpos))
    if star[2] <= 0:
        return
    for i in range(min(fntsiz, len(font))):
        (fx1, fy1), (fx2, fy2) = font[i]
        scale = fntscl * star[2]
        x1 = fx1 * scale
        y1 = fy1 * scale
        x2 = fx2 * scale
        y2 = fy2 * scale
        beg = (-x1 * star[2], -y1 * star[2], star[2])
        end = (-x2 * star[2], -y2 * star[2], star[2])
        esdraw(beg, end, color, view_state, escher_state)
    esdump(view_state, escher_state)


def eutemp(
    xbegin: list[float],
    ybegin: list[float],
    xend: list[float],
    yend: list[float],
    nsegs: int,
    color: int,
    view_state: EscherViewState,
    escher_state: EscherState,
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
        view_state: Escher view state.
        escher_state: Escher output state.
    """
    for i in range(nsegs):
        beg = (-xbegin[i], -ybegin[i], 1.0)
        end = (-xend[i], -yend[i], 1.0)
        esdraw(beg, end, color, view_state, escher_state)
    esdump(view_state, escher_state)
