"""Planet-specific configurations (moons, rings, orbital elements)."""

from ephemeris_tools.planets.base import ArcSpec, MoonSpec, PlanetConfig, RingSpec
from ephemeris_tools.planets.jupiter import JUPITER_CONFIG
from ephemeris_tools.planets.mars import MARS_CONFIG
from ephemeris_tools.planets.neptune import NEPTUNE_CONFIG
from ephemeris_tools.planets.pluto import PLUTO_CONFIG
from ephemeris_tools.planets.saturn import SATURN_CONFIG
from ephemeris_tools.planets.uranus import URANUS_CONFIG

__all__ = [
    "ArcSpec",
    "JUPITER_CONFIG",
    "MARS_CONFIG",
    "MoonSpec",
    "NEPTUNE_CONFIG",
    "PlanetConfig",
    "PLUTO_CONFIG",
    "RingSpec",
    "SATURN_CONFIG",
    "URANUS_CONFIG",
]
