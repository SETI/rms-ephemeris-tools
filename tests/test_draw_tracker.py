"""Tests for tracker y-axis label placement behavior."""

from __future__ import annotations

from io import StringIO

from ephemeris_tools.rendering.draw_tracker import _label_yaxis
from ephemeris_tools.time_utils import (
    day_sec_from_tai,
    parse_datetime,
    tai_from_day_sec,
    ymd_from_day,
)


def _yt_lines(text: str) -> list[str]:
    """Return only y-axis tick/label PostScript lines."""

    return [line for line in text.splitlines() if ' YT1' in line or ' YT2' in line]


def test_label_yaxis_case_6_017_first_major_tick_and_spacing() -> None:
    """Case 6_017: first major is FEB-19 and has 4 minors before MAR-01."""
    out = StringIO()
    parsed1 = parse_datetime('1550-02-17 00:00:00')
    parsed2 = parse_datetime('1550-04-20 00:00:00')
    assert parsed1 is not None
    assert parsed2 is not None
    day1, sec1 = parsed1
    day2, sec2 = parsed2
    tai1 = tai_from_day_sec(day1, sec1)
    tai2 = tai_from_day_sec(day2, sec2)
    _label_yaxis(
        out=out,
        tai1=tai1,
        tai2=tai2,
        dt=86400.0,
        day_sec_from_tai=day_sec_from_tai,
        ymd_from_day=ymd_from_day,
        tai_from_day_sec=tai_from_day_sec,
    )
    lines = _yt_lines(out.getvalue())
    major_indexes = [i for i, line in enumerate(lines) if ' YT1' in line]
    assert '(1550-FEB-19' in lines[major_indexes[0]]
    assert '(MAR-01' in lines[major_indexes[1]]
    assert major_indexes[1] - major_indexes[0] - 1 == 4


def test_label_yaxis_case_7_027_first_major_tick_and_no_mar_31() -> None:
    """Case 7_027: first major is MAR-21 and major label '(31)' is absent."""
    out = StringIO()
    parsed1 = parse_datetime('2000-03-18 00:00:00')
    parsed2 = parse_datetime('2000-05-20 00:00:00')
    assert parsed1 is not None
    assert parsed2 is not None
    day1, sec1 = parsed1
    day2, sec2 = parsed2
    tai1 = tai_from_day_sec(day1, sec1)
    tai2 = tai_from_day_sec(day2, sec2)
    _label_yaxis(
        out=out,
        tai1=tai1,
        tai2=tai2,
        dt=36000.0,
        day_sec_from_tai=day_sec_from_tai,
        ymd_from_day=ymd_from_day,
        tai_from_day_sec=tai_from_day_sec,
    )
    lines = _yt_lines(out.getvalue())
    first_major = next(line for line in lines if ' YT1' in line)
    assert '(2000-MAR-21' in first_major
    assert '(31)' not in first_major
