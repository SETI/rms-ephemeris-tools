"""Clear viewport (EUCLR)."""

from __future__ import annotations

from ephemeris_tools.rendering.escher import EscherState, esclr


def euclr(
    device: int,
    hmin: float,
    hmax: float,
    vmin: float,
    vmax: float,
    escher_state: EscherState,
) -> None:
    """Clear a region of the display (port of EUCLR).

    Same argument meanings as EUVIEW. Used for multi-exposure or inset images.

    Parameters:
        device: Display device number.
        hmin, hmax: Horizontal limits of region to clear (must differ, in [0,1]).
        vmin, vmax: Vertical limits of region to clear (must differ, in [0,1]).
        escher_state: Escher output state.
    """
    region = (hmin, hmax, vmin, vmax)
    esclr(device, region, escher_state)
