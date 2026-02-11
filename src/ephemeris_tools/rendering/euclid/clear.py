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
    """Clear viewport (port of EUCLR)."""
    region = (hmin, hmax, vmin, vmax)
    esclr(device, region, escher_state)
