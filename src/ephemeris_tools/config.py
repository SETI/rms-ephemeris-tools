"""Configuration: SPICE paths and temp/starlist paths from environment."""

import os
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
