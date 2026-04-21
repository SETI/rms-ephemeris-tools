"""EscherSink: wraps (EscherViewState, EscherState) as a SegmentSink.

Used as the adapter between the new SegmentSink protocol (accepted by the
updated Euclid entry points) and the existing Escher PostScript device layer.
"""

from __future__ import annotations

from ephemeris_tools.rendering.escher.ps_output import eslwid, eswrit
from ephemeris_tools.rendering.escher.state import EscherState, EscherViewState
from ephemeris_tools.rendering.escher.view import esdraw, esdump


class EscherSink:
    """Adapts the (EscherViewState, EscherState) pair to the SegmentSink protocol.

    Passes draw()/dump() directly to esdraw()/esdump(), and forwards
    set_linewidth() / set_dashed() to the matching Escher helpers.
    """

    def __init__(self, view_state: EscherViewState, escher_state: EscherState) -> None:
        """Wrap an Escher view/output state pair.

        Parameters:
            view_state: Escher viewport and projection state.
            escher_state: Escher PostScript output state.
        """
        self._view_state = view_state
        self._escher_state = escher_state

    @property
    def view_state(self) -> EscherViewState:
        """Wrapped Escher view state (viewport / projection)."""
        return self._view_state

    @property
    def escher_state(self) -> EscherState:
        """Wrapped Escher output state (PostScript stream)."""
        return self._escher_state

    def draw(
        self,
        begin: tuple[float, float, float],
        end: tuple[float, float, float],
        color: int,
    ) -> None:
        """Forward to esdraw (3-D projection, clip, buffer, PostScript output)."""
        esdraw(begin, end, color, self._view_state, self._escher_state)

    def dump(self) -> None:
        """Flush the segment buffer via esdump."""
        esdump(self._view_state, self._escher_state)

    def set_linewidth(self, pts: float) -> None:
        """Set PostScript line width via eslwid."""
        eslwid(pts, self._escher_state)

    def set_dashed(self, dashed: bool) -> None:
        """Enable or disable PostScript dash pattern via eswrit."""
        if dashed:
            eswrit('[30 30] 0 setdash', self._escher_state)
        else:
            eswrit('[] 0 setdash', self._escher_state)
