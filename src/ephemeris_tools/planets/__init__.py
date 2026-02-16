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
    """Return mapping of lowercase moon name to list index for the planet.

    Parameters:
        planet_num: Planet number (4-9).

    Returns:
        Dict mapping moon name (lowercase) to index in moons list (planet center
        excluded from count).
    """
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
    """Convert moon tokens to NAIF moon IDs (CLI/CGI moon selection).

    Parameters:
        planet_num: Planet number (4-9).
        tokens: List of 1-based indices, NAIF IDs, or case-insensitive names.

    Returns:
        List of NAIF moon IDs. Supports ``classical`` and ``all`` group keywords.
        Unknown names are skipped (logged).
    """
    cfg = _PLANET_CONFIGS.get(planet_num)
    if cfg is None:
        logger.warning('Unknown planet number %r for moon parsing', planet_num)
        return []

    moon_ids = [moon.id for moon in cfg.moons if moon.id != cfg.planet_id]
    name_to_id = {
        moon.name.lower(): moon.id
        for moon in cfg.moons
        if moon.id != cfg.planet_id and moon.name.strip()
    }
    classical_map: dict[int, list[int]] = {
        4: [401, 402],  # Mars all
        5: [501, 502, 503, 504],  # Jupiter classical moons
        6: [601, 602, 603, 604, 605, 606, 607, 608, 609],  # Saturn S1-S9
        7: [701, 702, 703, 704, 705],  # Uranus U1-U5
        8: [801, 802],  # Neptune Triton + Nereid
        9: [901],  # Pluto Charon
    }

    out: list[int] = []
    seen: set[int] = set()

    def _append_unique(moon_id: int) -> None:
        if moon_id in seen:
            return
        seen.add(moon_id)
        out.append(moon_id)

    def _int_prefix(text: str) -> int | None:
        digits = ''
        for ch in text:
            if ch.isdigit():
                digits += ch
            else:
                break
        if not digits:
            return None
        return int(digits)

    for s in tokens:
        s = s.strip()
        if not s:
            continue
        key = s.lower()
        if key == 'classical':
            for moon_id in classical_map.get(planet_num, moon_ids):
                _append_unique(moon_id)
            continue
        if key == 'all':
            for moon_id in moon_ids:
                _append_unique(moon_id)
            continue
        try:
            num = int(s)
            if num >= 100:
                if num in moon_ids:
                    _append_unique(num)
                else:
                    logger.warning('Unknown NAIF moon ID %r for planet %s', num, planet_num)
            elif num >= 1:
                moon_id = 100 * planet_num + num
                if moon_id in moon_ids:
                    _append_unique(moon_id)
                else:
                    logger.warning('Unknown moon index %r for planet %s', num, planet_num)
            continue
        except ValueError:
            pref = _int_prefix(s)
            if pref is not None:
                num = pref
                if num >= 100:
                    if num in moon_ids:
                        _append_unique(num)
                    else:
                        logger.warning('Unknown NAIF moon ID %r for planet %s', num, planet_num)
                elif num >= 1:
                    moon_id = 100 * planet_num + num
                    if moon_id in moon_ids:
                        _append_unique(moon_id)
                    else:
                        logger.warning('Unknown moon index %r for planet %s', num, planet_num)
                continue
        if key in name_to_id:
            _append_unique(name_to_id[key])
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
