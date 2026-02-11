"""Shared state for SPICE layer (replaces FORTRAN RSPK_COMMON common block)."""

from __future__ import annotations

from dataclasses import dataclass, field

MAXSHIFTS = 20


@dataclass
class SpiceState:
    """Shared state for SPICE/RSPK layer (replaces FORTRAN RSPK_COMMON).

    Holds current planet, observer (ID or geodetic), and time-shift list for
    moon orbits. Modified by load_spice_files, set_observer_*, set_shift.
    """

    planet_num: int = 0
    planet_id: int = 0
    pool_loaded: bool = False
    obs_id: int = 0
    obs_is_set: bool = False
    obs_lat: float = 0.0
    obs_lon: float = 0.0
    obs_alt: float = 0.0
    nshifts: int = 0
    shift_id: list[int] = field(default_factory=lambda: [0] * MAXSHIFTS)
    shift_dt: list[float] = field(default_factory=lambda: [0.0] * MAXSHIFTS)

    def reset_shifts(self) -> None:
        """Clear all time shifts (no Fortran equivalent; utility)."""
        self.nshifts = 0
        self.shift_id = [0] * MAXSHIFTS
        self.shift_dt = [0.0] * MAXSHIFTS


# Module-level singleton (FORTRAN common block behavior)
_state = SpiceState()


def get_state() -> SpiceState:
    """Return the global SpiceState instance (replaces RSPK_COMMON access)."""
    return _state
