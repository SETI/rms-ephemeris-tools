"""Planet-specific configurations (moons, rings, orbital elements)."""

import logging

from ephemeris_tools.planets.base import ArcSpec, MoonSpec, PlanetConfig, RingSpec
from ephemeris_tools.planets.jupiter import JUPITER_CONFIG
from ephemeris_tools.planets.mars import MARS_CONFIG
from ephemeris_tools.planets.neptune import NEPTUNE_CONFIG
from ephemeris_tools.planets.pluto import PLUTO_CONFIG
from ephemeris_tools.planets.saturn import SATURN_CONFIG
from ephemeris_tools.planets.uranus import URANUS_CONFIG

logger = logging.getLogger(__name__)

_PLANET_CONFIGS: dict[int, PlanetConfig] = {
    4: MARS_CONFIG,
    5: JUPITER_CONFIG,
    6: SATURN_CONFIG,
    7: URANUS_CONFIG,
    8: NEPTUNE_CONFIG,
    9: PLUTO_CONFIG,
}


def get_moon_name_to_index(planet_num: int) -> dict[str, int]:
    """Return mapping of lowercase moon name -> 1-based index for the planet."""
    cfg = _PLANET_CONFIGS.get(planet_num)
    if cfg is None:
        return {}
    out: dict[str, int] = {}
    for i, moon in enumerate(cfg.moons):
        if moon.id == cfg.planet_id:
            continue
        # First moon is at list index 1, which is 1-based index 1
        out[moon.name.lower()] = i
    return out


def parse_moon_spec(planet_num: int, tokens: list[str]) -> list[int]:
    """Convert list of moon tokens to moon IDs (1-based indices or NAIF IDs).

    Each token may be: a 1-based index (e.g. 1, 2), a NAIF ID (e.g. 601, 602),
    or a case-insensitive moon name (e.g. io, europa for Jupiter). Returns
    list of values that are either 1-based indices (1-99) or NAIF IDs (>=100).
    Caller should convert to full moon_ids: [v if v >= 100 else 100*planet_num+v].
    """
    name_to_idx = get_moon_name_to_index(planet_num)
    out: list[int] = []
    for s in tokens:
        s = s.strip()
        if not s:
            continue
        try:
            idx = int(s)
            if idx >= 1:
                out.append(idx)
            continue
        except ValueError:
            pass
        key = s.lower()
        if key in name_to_idx:
            out.append(name_to_idx[key])
        else:
            logger.warning('Unknown moon name %r for planet %s', s, planet_num)
    return out


__all__ = [
    'JUPITER_CONFIG',
    'MARS_CONFIG',
    'NEPTUNE_CONFIG',
    'PLUTO_CONFIG',
    'SATURN_CONFIG',
    'URANUS_CONFIG',
    'ArcSpec',
    'MoonSpec',
    'PlanetConfig',
    'RingSpec',
    'get_moon_name_to_index',
    'parse_moon_spec',
]
