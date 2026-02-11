"""Time conversion wrappers around rms-julian (replaces FORTRAN Julian library)."""

from __future__ import annotations

import logging

import julian

from ephemeris_tools.config import get_leapsecs_path

logger = logging.getLogger(__name__)

# Leap seconds loaded once at first use.
_leapsecs_loaded = False


def _ensure_leapsecs() -> None:
    """Load leap seconds file if not already loaded (replaces FJUL_InitLeaps).

    rms-julian requires a NAIF LSK (e.g. naif0012.tls). If the configured file
    is missing or not in LSK format (e.g. plain leapsecs.txt), falls back to
    rms-julian's bundled LSK.
    """
    global _leapsecs_loaded
    if _leapsecs_loaded:
        return
    path = get_leapsecs_path()
    try:
        julian.load_lsk(path)
        _leapsecs_loaded = True
    except (OSError, KeyError, ValueError) as e:
        logger.info(
            'Leap seconds from %s not used (%s); using rms-julian bundled LSK.',
            path,
            e,
        )
        try:
            julian.load_lsk()
        except Exception as fallback_err:
            logger.error(
                'Fallback to rms-julian bundled LSK failed: %s',
                fallback_err,
                exc_info=True,
            )
            raise
        _leapsecs_loaded = True


def parse_datetime(string: str) -> tuple[int, float] | None:
    """Parse date/time string to (day, sec) in UTC. Returns None on parse failure.

    day = days since J2000 (Jan 1 2000), sec = seconds within that day.
    Replaces FJUL_ParseDT(string, ' ', dutc, secs).
    """
    _ensure_leapsecs()
    try:
        result = julian.day_sec_from_string(string)
        day, sec = result[0], result[1]
        return (int(day), float(sec))
    except (ValueError, TypeError, LookupError, OSError):
        return None


def tai_from_day_sec(day: int, sec: float) -> float:
    """Convert UTC (day, sec) to TAI seconds. Replaces FJUL_TAIofDUTC(dutc) + secs."""
    _ensure_leapsecs()
    return float(julian.tai_from_day_sec(day, sec))


def tdb_from_tai(tai: float) -> float:
    """Convert TAI seconds to TDB (barycentric dynamical time) in seconds.

    Used as ET (ephemeris time) for SPICE. Replaces FJUL_ETofTAI(tai).
    """
    return float(julian.tdb_from_tai(tai))


def tai_from_tdb(tdb: float) -> float:
    """Convert TDB seconds to TAI. Replaces inverse of FJUL_ETofTAI."""
    return float(julian.tai_from_tdb(tdb))


def mjd_from_tai(tai: float) -> float:
    """Convert TAI seconds to Modified Julian Date. Replaces FJUL_MJDofTAI(tai, 0)."""
    return float(julian.mjd_from_tai(tai))


def day_sec_from_tai(tai: float) -> tuple[int, float]:
    """Convert TAI seconds to UTC (day, sec). Replaces FJUL_DUTCofTAI(tai, secs)."""
    _ensure_leapsecs()
    day, sec = julian.day_sec_from_tai(tai)
    return (int(day), float(sec))


def ymd_from_day(day: int) -> tuple[int, int, int]:
    """Convert day (since J2000) to (year, month, day). Replaces FJUL_YMDofDUTC(dutc)."""
    return julian.ymd_from_day(day)


def yd_from_day(day: int) -> tuple[int, int]:
    """Convert day to (year, day_of_year). Replaces FJUL_YDofDUTC(dutc)."""
    return julian.yd_from_day(day)


def hms_from_sec(sec: float) -> tuple[int, int, float]:
    """Convert seconds within day to (hour, minute, second). Replaces FJUL_HMSofSec."""
    return julian.hms_from_sec(sec)


def tai_from_jd(jd: float) -> float:
    """Convert Julian Date to TAI seconds. Replaces FJUL_TAIofJD(jd, 2)."""
    return float(julian.tai_from_jd(jd))


def day_from_ymd(year: int, month: int, day: int) -> int:
    """Convert calendar date to day since J2000. Replaces FJUL_DUTCofYMD."""
    return int(julian.day_from_ymd(year, month, day))


def format_utc(tai: float, fmt: str | None = None) -> str:
    """Format TAI as UTC string. Replaces FJUL_FormatPDS / FJUL_FormatDate etc."""
    _ensure_leapsecs()
    if fmt is not None:
        return julian.format_tai(tai, fmt)
    return julian.format_tai(tai)


def utc_to_et(day: int, sec: float) -> float:
    """Convert UTC (day, sec) to ET (TDB) seconds for SPICE. Common convenience."""
    tai = tai_from_day_sec(day, sec)
    return tdb_from_tai(tai)


def interval_seconds(
    interval: float,
    time_unit: str,
    *,
    min_seconds: float = 1.0,
    round_to_minutes: bool = False,
) -> float:
    """Convert interval and time_unit to seconds.

    Parameters:
        interval: Numeric interval value.
        time_unit: One of 'sec', 'min', 'hour', 'day' (case-insensitive, first 4 chars).
        min_seconds: Minimum returned value (e.g. 60.0 for tracker).
        round_to_minutes: If True, round result to nearest minute (60 * n).

    Returns:
        Interval in seconds, at least min_seconds, optionally rounded to minutes.
    """
    u = time_unit.strip().lower()[:4]
    if u in ('sec', 'seco'):
        dsec = abs(interval)
    elif u in ('min', 'minu'):
        dsec = abs(interval) * 60.0
    elif u == 'hour':
        dsec = abs(interval) * 3600.0
    elif u == 'day':
        dsec = abs(interval) * 86400.0
    else:
        raise ValueError(f'Invalid time_unit {time_unit!r}; expected one of sec, min, hour, day')
    dsec = max(dsec, min_seconds)
    if round_to_minutes:
        dsec = 60.0 * int(dsec / 60.0 + 0.5)
    return dsec
