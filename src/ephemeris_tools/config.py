"""Configuration: SPICE paths and temp/starlist paths from environment."""

import os
from importlib.resources import files
from pathlib import Path

# Paths (from tools.inc and rspk_common.inc); env var overrides with sensible defaults.
DEFAULT_SPICE_PATH = '/var/www/SPICE/'
DEFAULT_TEMP_PATH = '/var/www/work/'
DEFAULT_STARLIST_PATH = '/var/www/documents/tools/'


def get_spice_path() -> str:
    """Return SPICE kernel root directory (SPICE_PATH env var or default).

    Returns:
        Path string (from tools.inc / rspk_common.inc convention).
    """
    return os.environ.get('SPICE_PATH', DEFAULT_SPICE_PATH)


def get_temp_path() -> str:
    """Return temporary/output directory (TEMP_PATH env var or default).

    Returns:
        Path string.
    """
    return os.environ.get('TEMP_PATH', DEFAULT_TEMP_PATH)


def get_starlist_path() -> str:
    """Return star catalog directory (STARLIST_PATH env var or default).

    Returns:
        Path string.
    """
    return os.environ.get('STARLIST_PATH', DEFAULT_STARLIST_PATH)


def get_starlist_candidate_paths(starlist_filename: str) -> list[Path]:
    """Return candidate paths for a starlist file for both checkout and installed use.

    Tries STARLIST_PATH first, then the bundled ephemeris_tools._web_tools
    package resource so starlists are found when the package is installed.

    Parameters:
        starlist_filename: Basename of the starlist file (e.g. starlist_sat.txt).

    Returns:
        List of Path candidates in order of preference; callers should use the
        first path that exists.
    """
    candidates: list[Path] = [Path(get_starlist_path()) / starlist_filename]
    try:
        pkg = files('ephemeris_tools._web_tools')
        pkg_path = Path(str(pkg))
        if pkg_path.is_dir():
            candidates.append(pkg_path / starlist_filename)
    except (ImportError, OSError, TypeError):
        pass
    return candidates


def get_leapsecs_path() -> str:
    """Return path to a NAIF LSK leap seconds file for rms-julian.

    rms-julian expects a NAIF LSK (e.g. naif0012.tls); plain leapsecs.txt may
    require fallback to bundled LSK. Prefers JULIAN_LEAPSECS, then .tls under
    SPICE_PATH, then leapsecs.txt.

    Returns:
        Path string to LSK or leapsecs file.
    """
    path = os.environ.get('JULIAN_LEAPSECS', '').strip()
    if path:
        return path
    base = Path(get_spice_path())
    for name in ('naif0012.tls', 'naif0011.tls', 'naif0010.tls', 'leapseconds.tls'):
        p = base / name
        if p.exists():
            return str(p)
    return str(base / 'leapsecs.txt')
