"""Ephemeris generator, moon tracker, and planet viewer tools.

This package provides three main tools ported from FORTRAN:
- Ephemeris generator: time-series tables of planetary and moon positions/geometry
- Moon tracker: time-series plots of moon positions relative to planet limb and rings
- Planet viewer: sky charts showing planet, moons, rings, and background stars

All tools use SPICE kernels via cspyce and rms-julian for time conversions.
"""

__all__: list[str] = []
