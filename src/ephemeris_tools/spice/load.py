"""SPICE kernel loading (ported from rspk_loadfiles.f and rspk_loadsc.f)."""

from __future__ import annotations

import logging
from pathlib import Path

import cspyce

from ephemeris_tools.config import get_spice_path
from ephemeris_tools.spice.common import MAXSHIFTS, get_state

logger = logging.getLogger(__name__)


def load_spice_files(planet: int, version: int = 0) -> tuple[bool, str | None]:
    """Load SPICE kernels for the given planet.

    Returns (True, None) if loaded, (False, reason) on failure.

    planet: 4=Mars, 5=Jupiter, 6=Saturn, 7=Uranus, 8=Neptune, 9=Pluto.
    version: ephemeris version or 0 for latest.
    """
    state = get_state()
    if state.planet_num != 0 and state.planet_num != planet:
        return (False, "SPICE already loaded for a different planet")
    base = Path(get_spice_path())
    if not base.exists():
        return (False, f"SPICE_PATH directory does not exist: {base}")
    if not base.is_dir():
        return (False, f"SPICE_PATH is not a directory: {base}")
    if not state.pool_loaded:
        for ker in ("leapseconds.ker", "p_constants.ker"):
            p = base / ker
            if p.exists():
                try:
                    cspyce.furnsh(str(p))
                except Exception as e:
                    logger.warning("Failed to load %s: %s", p, e)
        state.pool_loaded = True
    config_path = base / "SPICE_planets.txt"
    if not config_path.exists():
        logger.warning("Config not found: %s", config_path)
        return (
            False,
            f"SPICE_planets.txt not found under {base}. "
            "Ensure SPICE_PATH points to a SPICE kernel tree that includes SPICE_planets.txt.",
        )
    load_version = version
    loaded = False
    with config_path.open() as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("!"):
                continue
            parts = line.split(',')
            if len(parts) < 3:
                logger.error(
                    "SPICE_planets.txt line %d: expected at least 3 fields (planet version filename), got %d: %r",
                    line_no,
                    len(parts),
                    line,
                )
                continue
            try:
                p = int(parts[0])
                v = int(parts[1])
                filename = parts[2].strip('"')
            except ValueError as e:
                logger.error(
                    "SPICE_planets.txt line %d: bad value (planet/version must be integer): %r - %s",
                    line_no,
                    line,
                    e,
                )
                continue
            if load_version == 0 and p == planet:
                load_version = v
            if p == planet and v == load_version:
                kpath = base / filename
                if kpath.exists():
                    try:
                        cspyce.furnsh(str(kpath))
                        loaded = True
                    except Exception as e:
                        logger.warning("Failed to load %s: %s", kpath, e)
    if not loaded:
        return (
            False,
            f"No kernel files for planet {planet} (version {load_version}) found under {base}. "
            "Check SPICE_planets.txt for planet/version and that the listed kernel files exist.",
        )
    state.planet_num = planet
    state.planet_id = planet * 100 + 99
    state.nshifts = 0
    state.shift_id = [0] * MAXSHIFTS
    state.shift_dt = [0.0] * MAXSHIFTS
    return (True, None)


def load_spacecraft(
    sc_id: str,
    planet: int,
    version: int = 0,
    set_obs: bool = True,
) -> bool:
    """Load SPICE kernels for spacecraft at planet. Optionally set observer to spacecraft.

    sc_id: e.g. 'CAS', 'VG1', 'NH'.
    planet: 5=Jupiter, 6=Saturn, etc.
    version: 0 for latest.
    """
    state = get_state()
    if state.planet_num != 0 and state.planet_num != planet:
        return False
    base = Path(get_spice_path())
    if not state.pool_loaded:
        for ker in ("leapseconds.ker", "p_constants.ker"):
            p = base / ker
            if p.exists():
                try:
                    cspyce.furnsh(str(p))
                except Exception as e:
                    logger.warning("Failed to load %s: %s", p, e)
        state.pool_loaded = True
    config_path = base / "SPICE_spacecraft.txt"
    if not config_path.exists():
        logger.warning("Config not found: %s", config_path)
        return False
    sc_upper = sc_id.strip().upper()
    load_version = version
    loaded = False
    with config_path.open() as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line or line.startswith("!"):
                continue
            parts = line.split()
            if len(parts) < 5:
                logger.error(
                    "SPICE_spacecraft.txt line %d: expected at least 5 fields (name planet version naif_id filename), got %d: %r",
                    line_no,
                    len(parts),
                    line,
                )
                continue
            try:
                name = parts[0].upper()
                p = int(parts[1])
                v = int(parts[2])
                naif_id = int(parts[3])
                filename = parts[4]
            except (ValueError, IndexError) as e:
                logger.error(
                    "SPICE_spacecraft.txt line %d: bad value (planet/version/naif_id must be integer): %r - %s",
                    line_no,
                    line,
                    e,
                )
                continue
            if name == sc_upper and p == planet and load_version == 0:
                load_version = v
            if name == sc_upper and p == planet and v == load_version:
                kpath = base / filename
                if kpath.exists():
                    try:
                        cspyce.furnsh(str(kpath))
                        loaded = True
                        if set_obs:
                            state.obs_id = naif_id
                            state.obs_is_set = True
                    except Exception as e:
                        logger.warning("Failed to load %s: %s", kpath, e)
    if not loaded:
        return False
    state.planet_num = planet
    state.planet_id = planet * 100 + 99
    return True
