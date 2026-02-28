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
    return {moon.name.lower(): i for i, moon in enumerate(cfg.moons) if moon.id != cfg.planet_id}


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
    cgi_group_map: dict[int, dict[int, list[int]]] = {
        # Viewer CGI group codes from the FORTRAN form.
        4: {402: [401, 402]},
        5: {
            504: [501, 502, 503, 504],
            505: [501, 502, 503, 504, 505],
            516: [501, 502, 503, 504, 505, 514, 515, 516],
        },
        6: {
            609: [601, 602, 603, 604, 605, 606, 607, 608, 609],
            618: [
                601,
                602,
                603,
                604,
                605,
                606,
                607,
                608,
                609,
                610,
                611,
                612,
                613,
                614,
                615,
                616,
                617,
                618,
            ],
            653: [
                601,
                602,
                603,
                604,
                605,
                606,
                607,
                608,
                609,
                610,
                611,
                612,
                613,
                614,
                615,
                616,
                617,
                618,
                632,
                633,
                634,
                635,
                649,
                653,
            ],
        },
        7: {
            705: [701, 702, 703, 704, 705],
            715: [701, 702, 703, 704, 705, 706, 707, 708, 709, 710, 711, 712, 713, 714, 715],
            727: [
                701,
                702,
                703,
                704,
                705,
                706,
                707,
                708,
                709,
                710,
                711,
                712,
                713,
                714,
                715,
                725,
                726,
                727,
            ],
        },
        8: {802: [801, 802], 814: [801, 802, 803, 804, 805, 806, 807, 808, 814]},
        9: {901: [901], 903: [901, 902, 903], 905: [901, 902, 903, 904, 905]},
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
        if len(digits) == 0:
            return None
        return int(digits)

    for s in tokens:
        s = s.strip()
        if len(s) == 0:
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
            # FORTRAN viewer reads first 3 chars as group/max-ID; resolve group codes.
            if num in cgi_group_map.get(planet_num, {}):
                for moon_id in cgi_group_map[planet_num][num]:
                    _append_unique(moon_id)
                continue
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
                # FORTRAN viewer reads string(1:3) and uses it as max moon ID or group
                # code; match that by resolving known group codes with or without text.
                if num in cgi_group_map.get(planet_num, {}):
                    for moon_id in cgi_group_map[planet_num][num]:
                        _append_unique(moon_id)
                    continue
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


_PLANET_LETTER: dict[int, str] = {
    4: 'M',
    5: 'J',
    6: 'S',
    7: 'U',
    8: 'N',
    9: 'P',
}


def get_moon_display_name(planet_num: int, moon_id: int) -> str | None:
    """Return display name for moon (e.g. 'Ganymede (J3)').

    Parameters:
        planet_num: Planet number (4-9).
        moon_id: NAIF moon body ID (e.g. 503 for Ganymede).

    Returns:
        Display string (name + letter index) or None if unknown.

    Raises:
        None. Invalid planet_num or moon_id yields None; no exceptions are raised.
    """
    cfg = _PLANET_CONFIGS.get(planet_num)
    if cfg is None:
        return None
    moon = cfg.moon_by_id(moon_id)
    if moon is None:
        return None
    idx = moon_id % 100
    if planet_num not in _PLANET_LETTER:
        logger.warning('Missing _PLANET_LETTER for planet_num=%s; moon=%s', planet_num, moon.name)
        return None
    letter = _PLANET_LETTER[planet_num]
    return f'{moon.name} ({letter}{idx})'


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
    'get_moon_display_name',
    'get_moon_name_to_index',
    'parse_moon_spec',
]
