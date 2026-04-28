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

        Returns:
            None

        Raises:
            TypeError: If ``begin``/``end`` are not length-3 numeric sequences.
            ValueError: If ``color`` is outside the supported range, coordinates
                are non-finite, or ``z`` is invalid for the implementation.

        Notes:
            Segments with endpoints behind the camera (``z <= 0``) are typically
            clipped or ignored rather than drawn. Implementations should validate
            inputs where practical so callers can rely on the errors above.
        """
        ...

    def dump(self) -> None:
        """Flush any buffered segments to the output device.

        Returns:
            None

        Raises:
            OSError: If the underlying device fails while flushing (e.g. broken
                pipe or disk full when writing PostScript).
        """
        ...

    def set_linewidth(self, pts: float) -> None:
        """Set current line width in PostScript points for subsequent segments.

        Parameters:
            pts: Line width in points; ``pts <= 0`` resets to a default width in
                ``MplCanvas``; other implementations may match that behaviour or
                raise ``ValueError`` for negative widths.

        Returns:
            None

        Raises:
            ValueError: If an implementation rejects ``pts`` (e.g. invalid or
                negative when not clamped).

        Notes:
            Affects all ``draw`` calls until the next ``set_linewidth``.
        """
        ...

    def set_dashed(self, dashed: bool) -> None:
        """Enable or disable dashed-line mode for subsequent draw() calls.

        Parameters:
            dashed: True to draw dashed lines; False for solid.

        Returns:
            None

        Raises:
            None for normal use: implementations take a ``bool`` and should not
            raise for valid input.
        """
        ...
