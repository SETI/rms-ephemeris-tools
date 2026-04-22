"""MplCanvas: matplotlib SegmentSink.

Receives 3D camera-frame segments from Euclid, projects them to 2D projection-
plane (FOV) coordinates, clips them to the FOV rectangle, and accumulates them
for later rendering via finalize().

Projection:
    x = -begin[0] / z   (same sign convention as escher/view.py esdraw)
    y = -begin[1] / z

Clipping uses the same _esclip algorithm as escher/view.py so that MplCanvas
and EscherSink produce geometrically identical 2D coordinates.  Unlike Escher,
MplCanvas stores floating-point FOV coordinates directly without the integer
pixel rounding used by the PostScript device layer.

Segments are grouped by (color, linewidth, dashed) for efficient rendering as
matplotlib LineCollection objects.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # avoid unconditional matplotlib import at module level
    import matplotlib.axes
    import numpy as np

# Color code to grayscale float (0 = white, 1 = black, 2-10 = 0.1-0.9)
_GRAY_LEVEL: tuple[float, ...] = (
    1.0,   # 0 = white
    0.0,   # 1 = black
    0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9,
)

# Epsilon for near-zero z in 3D projection
_EPS = 1.0e-12


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
    """Clip line segment (x1,y1)-(x2,y2) to the FOV rectangle.

    Exact copy of the _esclip algorithm from escher/view.py so that MplCanvas
    and EscherSink produce geometrically identical 2D clipped endpoints.

    Returns:
        (cx1, cy1, cx2, cy2, inside) where inside is False if fully outside.
    """
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
        if y1 > ymax:
            check = y2 < ymax
        elif y1 < ymin:
            check = y2 > ymin
        else:
            check = (x2 > xmax) or (x2 < xmin) or (y2 > ymax) or (y2 < ymin)
            if not check:
                return (x1, y1, x2, y2, True)
            onensd = True

    if not check:
        return (x1, y1, x2, y2, False)

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

    if dy == 0.0:
        if (x1 < xmin) and (x2 > xmax):
            return (xmin, y1, xmax, y2, True)
        if (x1 < xmin) and (x2 > xmin):
            return (xmin, y1, x2, y2, True)
        if (x2 < xmin) and (x1 > xmax):
            return (xmax, y1, xmin, y2, True)
        if (x2 < xmin) and (x1 > xmin):
            return (x1, y1, xmin, y2, True)

    if dx == 0.0:
        if (y1 < ymin) and (y2 > ymax):
            return (x1, ymin, x2, ymax, True)
        if (y1 < ymin) and (y2 > ymin):
            return (x1, ymin, x2, y2, True)
        if (y2 < ymin) and (y1 > ymax):
            return (x1, ymax, x2, ymin, True)
        if (y2 < ymin) and (y1 > ymin):
            return (x1, y1, x2, ymin, True)

    ymaxy1 = ymax - y1
    if nwpnts < possbl and ((0 < ymaxy1 < dy) or (0 > ymaxy1 > dy)):
        s = ymaxy1 / dy
        x = s * dx + x1
        if (x < xmax) and (x > xmin):
            xend[nwpnts] = x
            yend[nwpnts] = ymax
            nwpnts += 1

    yminy1 = ymin - y1
    if nwpnts < possbl and ((0 < yminy1 < dy) or (0 > yminy1 > dy)):
        s = yminy1 / dy
        x = s * dx + x1
        if (x < xmax) and (x > xmin):
            xend[nwpnts] = x
            yend[nwpnts] = ymin
            nwpnts += 1

    xmaxx1 = xmax - x1
    if nwpnts < possbl and ((0 < xmaxx1 < dx) or (0 > xmaxx1 > dx)):
        s = xmaxx1 / dx
        y = s * dy + y1
        if (y < ymax) and (y > ymin):
            xend[nwpnts] = xmax
            yend[nwpnts] = y
            nwpnts += 1

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


@dataclass
class _SegGroup:
    """A group of line segments sharing the same color, linewidth, and dash style."""

    gray: float
    linewidth: float
    dashed: bool
    segments: list[tuple[float, float, float, float]] = field(default_factory=list)

    def add(self, x1: float, y1: float, x2: float, y2: float) -> None:
        """Append one clipped 2D segment."""
        self.segments.append((x1, y1, x2, y2))


class MplCanvas:
    """Matplotlib implementation of SegmentSink.

    Receives 3D camera-frame segments from Euclid, projects and clips them to
    FOV-space 2D coordinates, and accumulates them for later rendering by
    finalize() which draws them onto a matplotlib Axes using LineCollections.

    Usage::

        canvas = MplCanvas(xmin=-delta, xmax=delta, ymin=-delta, ymax=delta)
        eubody(..., sink=canvas)
        euring(..., sink=canvas)
        canvas.finalize(ax)

    Parameters:
        xmin, xmax, ymin, ymax: FOV bounds in projection-plane units.
    """

    def __init__(
        self,
        xmin: float,
        xmax: float,
        ymin: float,
        ymax: float,
    ) -> None:
        self._xmin = xmin
        self._xmax = xmax
        self._ymin = ymin
        self._ymax = ymax
        self._linewidth: float = 1.0
        self._dashed: bool = False
        self._groups: list[_SegGroup] = []
        self._current_group: _SegGroup | None = None

    # ------------------------------------------------------------------
    # SegmentSink protocol implementation
    # ------------------------------------------------------------------

    def draw(
        self,
        begin: tuple[float, float, float],
        end: tuple[float, float, float],
        color: int,
    ) -> None:
        """Project a 3D segment and clip to FOV; store if visible."""
        sign1 = 1.0 if begin[2] >= 0 else -1.0
        sign2 = 1.0 if end[2] >= 0 else -1.0
        z1 = begin[2] if abs(begin[2]) >= _EPS else sign1 * _EPS
        z2 = end[2] if abs(end[2]) >= _EPS else sign2 * _EPS
        bx = -begin[0] / z1
        by = -begin[1] / z1
        ex = -end[0] / z2
        ey = -end[1] / z2
        bx, by, ex, ey, inside = _esclip(
            self._xmin, self._xmax, self._ymin, self._ymax, bx, by, ex, ey
        )
        if not inside:
            return
        gray = _GRAY_LEVEL[max(0, min(color, len(_GRAY_LEVEL) - 1))]
        self._get_group(gray).add(bx, by, ex, ey)

    def dump(self) -> None:
        """No-op: MplCanvas stores segments directly without buffering."""

    def set_linewidth(self, pts: float) -> None:
        """Set current line width (points) for subsequent draw() calls."""
        self._linewidth = pts if pts > 0 else 1.0
        self._current_group = None  # force new group on next draw

    def set_dashed(self, dashed: bool) -> None:
        """Enable or disable dashed-line mode for subsequent draw() calls."""
        self._dashed = dashed
        self._current_group = None  # force new group on next draw

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_group(self, gray: float) -> _SegGroup:
        """Return the current group, creating a new one if attributes changed."""
        if (
            self._current_group is not None
            and math.isclose(self._current_group.gray, gray)
            and math.isclose(self._current_group.linewidth, self._linewidth)
            and self._current_group.dashed == self._dashed
        ):
            return self._current_group
        grp = _SegGroup(
            gray=gray,
            linewidth=self._linewidth,
            dashed=self._dashed,
        )
        self._groups.append(grp)
        self._current_group = grp
        return grp

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------

    def finalize(self, ax: 'matplotlib.axes.Axes', linewidth_scale: float = 1.0) -> None:
        """Draw all accumulated segments on *ax* as LineCollection objects.

        One LineCollection per distinct (gray, linewidth, dashed) group.

        Axis limits match the PostScript ``esview`` / ``_esmap2`` mapping:
        FOV *x* increases to the right; FOV *y* increases toward the bottom of
        the figure (``uy`` is negative because the PS viewport has *v1* > *v2*).

        Parameters:
            ax: Target matplotlib Axes.
            linewidth_scale: Multiply each stored linewidth by this factor
                (useful for DPI-independent sizing).
        """
        import numpy as np  # noqa: PLC0415 - lazy import
        from matplotlib.collections import LineCollection  # noqa: PLC0415

        for grp in self._groups:
            if not grp.segments:
                continue
            segs_arr = [
                [[x1, y1], [x2, y2]] for (x1, y1, x2, y2) in grp.segments
            ]
            color_val = str(grp.gray)
            lw = max(0.5, grp.linewidth * linewidth_scale)
            ls = (0, (4, 4)) if grp.dashed else 'solid'
            lc = LineCollection(
                segs_arr,
                colors=color_val,
                linewidths=lw,
                linestyles=ls,
            )
            ax.add_collection(lc)

        # Set axis limits so that the FOV exactly fills the axes box.
        ax.set_xlim(self._xmin, self._xmax)
        ax.set_ylim(self._ymax, self._ymin)

    @property
    def fov(self) -> tuple[float, float, float, float]:
        """Return (xmin, xmax, ymin, ymax) FOV bounds."""
        return (self._xmin, self._xmax, self._ymin, self._ymax)

    @property
    def has_segments(self) -> bool:
        """True if any visible segments were received."""
        return any(bool(g.segments) for g in self._groups)
