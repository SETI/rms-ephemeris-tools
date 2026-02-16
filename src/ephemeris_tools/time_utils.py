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
    """Parse date/time string to UTC (day, sec) (replaces FJUL_ParseDT).

    Parameters:
        string: Date/time string (format accepted by rms-julian).

    Returns:
        (day, sec) where day is days since J2000, sec is seconds within that day;
        None on parse failure.
    """
    _ensure_leapsecs()
    try:
        result = julian.day_sec_from_string(string)
        day, sec = result[0], result[1]
        return (int(day), float(sec))
    except (ValueError, TypeError, LookupError, OSError):
        return None


def tai_from_day_sec(day: int, sec: float) -> float:
    """Convert UTC (day, sec) to TAI seconds (replaces FJUL_TAIofDUTC + secs).

    Parameters:
        day: Days since J2000.
        sec: Seconds within that day.

    Returns:
        TAI in seconds.
    """
    _ensure_leapsecs()
    return float(julian.tai_from_day_sec(day, sec))


def tdb_from_tai(tai: float) -> float:
    """Convert TAI to TDB seconds (replaces FJUL_ETofTAI). Used as ET for SPICE.

    Parameters:
        tai: TAI in seconds.

    Returns:
        TDB (ephemeris time) in seconds.
    """
    return float(julian.tdb_from_tai(tai))


def tai_from_tdb(tdb: float) -> float:
    """Convert TDB seconds to TAI (inverse of FJUL_ETofTAI).

    Parameters:
        tdb: TDB (ephemeris time) in seconds.

    Returns:
        TAI in seconds.
    """
    return float(julian.tai_from_tdb(tdb))


def mjd_from_tai(tai: float) -> float:
    """Convert TAI to Modified Julian Date (replaces FJUL_MJDofTAI).

    Parameters:
        tai: TAI in seconds.

    Returns:
        MJD (float).
    """
    return float(julian.mjd_from_tai(tai))


def day_sec_from_tai(tai: float) -> tuple[int, float]:
    """Convert TAI to UTC (day, sec) (replaces FJUL_DUTCofTAI).

    Parameters:
        tai: TAI in seconds.

    Returns:
        (day, sec) where day is days since J2000.
    """
    _ensure_leapsecs()
    day, sec = julian.day_sec_from_tai(tai)
    return (int(day), float(sec))


def ymd_from_day(day: int) -> tuple[int, int, int]:
    """Convert day since J2000 to calendar date (replaces FJUL_YMDofDUTC).

    Parameters:
        day: Days since J2000.

    Returns:
        (year, month, day).
    """
    return julian.ymd_from_day(day)


def yd_from_day(day: int) -> tuple[int, int]:
    """Convert day since J2000 to year and day-of-year (replaces FJUL_YDofDUTC).

    Parameters:
        day: Days since J2000.

    Returns:
        (year, day_of_year).
    """
    return julian.yd_from_day(day)


def hms_from_sec(sec: float) -> tuple[int, int, float]:
    """Convert seconds within day to (hour, minute, second) (replaces FJUL_HMSofSec).

    Parameters:
        sec: Seconds within day (0..86400).

    Returns:
        (hour, minute, second).
    """
    return julian.hms_from_sec(sec)


def tai_from_jd(jd: float) -> float:
    """Convert Julian Date to TAI seconds (replaces FJUL_TAIofJD).

    Parameters:
        jd: Julian Date.

    Returns:
        TAI in seconds.
    """
    return float(julian.tai_from_jd(jd))


def day_from_ymd(year: int, month: int, day: int) -> int:
    """Convert calendar date to days since J2000 (replaces FJUL_DUTCofYMD).

    Parameters:
        year, month, day: Calendar date.

    Returns:
        Days since J2000.
    """
    return int(julian.day_from_ymd(year, month, day))


def format_utc(tai: float, fmt: str | None = None) -> str:
    """Format TAI as UTC string (replaces FJUL_FormatPDS / FJUL_FormatDate).

    Parameters:
        tai: TAI in seconds.
        fmt: Optional format string for rms-julian; None = default.

    Returns:
        Formatted UTC string.
    """
    _ensure_leapsecs()
    if fmt is not None:
        return julian.format_tai(tai, fmt)
    return julian.format_tai(tai)


def utc_to_et(day: int, sec: float) -> float:
    """Convert UTC (day, sec) to ET (TDB) seconds for SPICE.

    Parameters:
        day: Days since J2000.
        sec: Seconds within day.

    Returns:
        ET (TDB) in seconds.
    """
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
