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
    """Draw star symbol at position (port of EUSTAR)."""
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
    """Draw overlay segments in image plane (port of EUTEMP)."""
    for i in range(nsegs):
        beg = (-xbegin[i], -ybegin[i], 1.0)
        end = (-xend[i], -yend[i], 1.0)
        esdraw(beg, end, color, view_state, escher_state)
    esdump(view_state, escher_state)
