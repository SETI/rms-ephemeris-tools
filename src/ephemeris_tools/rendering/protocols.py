"""Protocol for 3D line-segment rendering backends.

Euclid emits 3D camera-frame segments via draw(); backends (Escher/PostScript
or matplotlib) implement this protocol to render them on their respective devices.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SegmentSink(Protocol):
    """Receiver for 3D line segments produced by Euclid.

    Euclid calls draw() for every visible line segment and dump() to flush
    the buffer.  set_linewidth() and set_dashed() carry state that persists
    until the next call, mirroring eslwid/setdash in PostScript.
    """

    def draw(
        self,
        begin: tuple[float, float, float],
        end: tuple[float, float, float],
        color: int,
    ) -> None:
        """Accept a 3D line segment in camera-frame coordinates (z > 0 visible).

        Parameters:
            begin: Start point (x, y, z).
            end: End point (x, y, z).
            color: Integer color code 0-10 (0 = white, 1 = black, 2-10 = 0.1-0.9 gray).
        """
        ...

    def dump(self) -> None:
        """Flush any buffered segments to the output device."""
        ...

    def set_linewidth(self, pts: float) -> None:
        """Set current line width in PostScript points for subsequent segments.

        Parameters:
            pts: Line width in points (0 resets to default).
        """
        ...

    def set_dashed(self, dashed: bool) -> None:
        """Enable or disable dashed-line mode for subsequent draw() calls.

        Parameters:
            dashed: True to draw dashed lines; False for solid.
        """
        ...
