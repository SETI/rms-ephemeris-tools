"""Angle parsing and formatting (ported from viewer3_utils.f ParseAngle and DMS_string)."""

from __future__ import annotations

import re


def parse_angle(string: str) -> float | None:
    """Parse angle as hours or degrees, minutes, seconds. Returns value or None on failure.

    Accepts three numbers (deg/h, m, s), two (deg/h, m), or one (deg/h).
    Minutes and seconds must be non-negative. Leading minus makes result negative.
    Returned value is in the same units as the first number (hours or degrees).
    """
    s = string.strip()
    if len(s) == 0:
        return None
    # Try 3, 2, or 1 space-separated numbers
    parts = re.split(r"\s+", s)
    if len(parts) >= 3:
        try:
            v1 = float(parts[0])
            v2 = float(parts[1])
            v3 = float(parts[2])
        except ValueError:
            return None
        if v2 < 0 or v3 < 0:
            return None
        angle = abs(v1) + v2 / 60.0 + v3 / 3600.0
    elif len(parts) == 2:
        try:
            v1 = float(parts[0])
            v2 = float(parts[1])
        except ValueError:
            return None
        if v2 < 0:
            return None
        angle = abs(v1) + v2 / 60.0
    elif len(parts) == 1:
        try:
            angle = abs(float(parts[0]))
        except ValueError:
            return None
    else:
        return None
    # Leading minus
    first_nonblank = len(s) - len(s.lstrip())
    if first_nonblank < len(s) and s[first_nonblank] == "-":
        angle = -angle
    return angle


def dms_string(
    value: float,
    separator: str,
    ndecimal: int = 3,
) -> str:
    """Format angle as deg/h min sec with given separator characters.

    value: angle in degrees (or hours for RA).
    separator: 3-char string, e.g. 'hms' or 'dms' (chars between d/h-m, m-s, and after sec).
    ndecimal: 3 or 4 decimal places for seconds.
    """
    if len(separator) < 3:
        sep1 = sep2 = sep3 = " "
    else:
        sep1, sep2, sep3 = separator[0], separator[1], separator[2]
    isign = 1 if value >= 0 else -1
    secs = abs(value * 3600.0)
    ntens = 10**ndecimal
    ims = round(secs * ntens)
    isec = ims // ntens
    ims = ims - ntens * isec
    imin = isec // 60
    isec = isec - 60 * imin
    ideg = imin // 60
    imin = imin - 60 * ideg
    ideg = ideg * isign
    if ndecimal == 3:
        frac = f"{ims:03d}"
    else:
        frac = f"{ims:04d}"
    out = f"{ideg:3d}{sep1} {imin:02d}{sep2} {isec:02d}.{frac}{sep3}"
    if isign < 0 and ideg == 0:
        out = out[0:1] + "-" + out[2:]
    return out
