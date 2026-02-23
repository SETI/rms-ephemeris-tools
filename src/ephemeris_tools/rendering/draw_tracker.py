"""Moon tracker PostScript rendering: byte-for-byte identical to rspk_trackmoons.f."""

from __future__ import annotations

import math
from collections.abc import Callable
from datetime import date, datetime
from typing import TextIO

from ephemeris_tools.time_utils import (
    day_sec_from_tai,
    tai_from_day_sec,
    ymd_from_day,
)

# FORTRAN planet_names(4:8) - no Pluto in original; we add 9 for compatibility
PLANET_NAMES = {
    4: 'Mars',
    5: 'Jupiter',
    6: 'Saturn',
    7: 'Uranus',
    8: 'Neptune',
    9: 'Pluto',
}

# FORTRAN ring constants by planet (tracker3_xxx.f): (nrings, rads_km, grays)
RING_DATA = {
    4: (0, [0.0], [0.75]),
    5: (3, [129000.0, 181350.0, 221900.0], [0.75, 0.85, 0.90]),
    6: (
        5,
        [136780.0, 166000.0, 173000.0, 180990.0, 301650.0],
        [0.75, 1.00, 0.875, 1.00, 0.875],
    ),
    7: (1, [51149.32], [0.75]),
    8: (1, [62932.0], [0.75]),
    9: (0, [0.0], [0.75]),
}
PLANET_GRAY = 0.50

# RSPK_LabelXAxis constants (STEP1, STEP2)
STEP1 = (2, 5, 10, 20, 50, 100, 200, 500, 1000)
STEP2 = (1, 1, 2, 5, 10, 20, 50, 100, 200)

# RSPK_LabelYAxis constants (minutes)
STEP1_MINS = (60, 120, 360, 720, 1440, 2880, 7200, 14400, 44640)
STEP2_MINS = (15, 30, 60, 120, 360, 720, 1440, 2880, 7200)
MINS_PER_HOUR = 60
MINS_PER_DAY = 60 * 24
MONTH_NAMES = (
    'JAN',
    'FEB',
    'MAR',
    'APR',
    'MAY',
    'JUN',
    'JUL',
    'AUG',
    'SEP',
    'OCT',
    'NOV',
    'DEC',
)
PLOT_HEIGHT = 612.0
BAND_WIDTH = 16.0


def _track_string(s: str) -> str:
    """Escape ( ) and degree for PostScript and wrap in parentheses (RSPK_TrackString).

    Unicode degree (U+00B0) is replaced with \\260 so PostScript emits one byte 0xB0
    and only the degree glyph is shown (avoids UTF-8 C2 B0 rendering as prime + degree).
    """
    temp = s.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
    temp = temp.replace('\u00b0', '\\260')
    return f'({temp})'


def _emit(out: TextIO, line: str) -> None:
    """Write a line to the output stream (helper for PostScript emission)."""
    out.write(line + '\n')


def _plot_limb(
    out: TextIO,
    nrecs: int,
    limb_arcsec: list[float],
    xscaled: bool,
    rp: float,
) -> None:
    """Plot gray band for planetary limb/ring zone (port of RSPK_PlotLimb)."""
    for sign in (-1, 1):
        if xscaled:
            val = sign * rp
            _emit(out, f'{val:8.2f} Xcoord dup DJ newpath moveto 0 lineto')
        else:
            _emit(out, f'{sign * rp * limb_arcsec[0]:8.2f} F')
            for irec in range(1, nrecs):
                _emit(out, f'{sign * rp * limb_arcsec[irec]:8.2f} N')
            _emit(out, 'D')
        _emit(out, '0 Xcoord dup 0 lineto DJ lineto closepath fill')


def _plot_moon(
    out: TextIO,
    nrecs: int,
    imoon: int,
    moon_arcsec: list[list[float]],
    limb_arcsec: list[float],
    xrange: float,
    xscaled: bool,
    name: str,
    excluded: list[bool],
    irecband: int,
) -> None:
    """Plot one moon's track curve and optional label (port of RSPK_PlotMoon)."""
    xmax = -1e37
    imax = -1
    first = True
    for irec in range(nrecs):
        x = moon_arcsec[imoon][irec]
        if xscaled:
            x = x / limb_arcsec[irec]
        char = 'F' if first else 'N'
        first = False
        _emit(out, f'{x:8.2f} {char}')
        if x < xrange and x > xmax and not excluded[irec]:
            imax = irec
            xmax = x
    _emit(out, 'D stroke')
    if xmax <= -xrange:
        return
    # PutLab expects: y_index (1-based), x_val, (name). Original FORTRAN uses ALL CAPS.
    name_ps = _track_string(name.strip().upper())
    _emit(out, f'{imax + 1:4d} {xmax:8.2f} {name_ps} PutLab')
    for j in range(max(0, imax - irecband), min(nrecs, imax + irecband + 1)):
        excluded[j] = True


def _label_xaxis(
    out: TextIO,
    xrange: float,
    xscaled: bool,
    planetstr: str,
) -> None:
    """Draw x-axis labels and tick marks (port of RSPK_LabelXAxis)."""
    max_xstep = 2.0 * xrange / 3.0
    i = len(STEP1) - 1
    while i >= 1 and STEP1[i] > max_xstep:
        i -= 1
    mark1 = STEP1[i]
    mark2 = STEP2[i]
    _emit(out, '0 (0) XT1')
    mark = mark2
    while mark <= int(xrange):
        if mark % mark1 == 0:
            label = str(mark).lstrip()
            _emit(out, f'{mark:4d} ({label}) XT1')
            _emit(out, f'{-mark:4d} (-{label}) XT1')
        else:
            _emit(out, f'{mark:4d} XT2')
            _emit(out, f'{-mark:4d} XT2')
        mark += mark2
    if xscaled:
        _emit(out, f'({planetstr} radii) Xlabel')
    else:
        _emit(out, '(Arcsec) Xlabel')


def _label_yaxis(
    out: TextIO,
    tai1: float,
    tai2: float,
    dt: float,
    day_sec_from_tai: Callable[[float], tuple[int, float]],
    ymd_from_day: Callable[[int], tuple[int, int, int]],
    tai_from_day_sec: Callable[[int, float], float],
    use_doy_format: bool = False,
) -> None:
    """Draw y-axis (time) labels and tick marks (port of RSPK_LabelYAxis).

    Parameters:
        out: Output stream.
        tai1, tai2: TAI time range (seconds).
        dt: Time step between records.
        day_sec_from_tai: Convert TAI to (day, sec).
        ymd_from_day: Convert day to (year, month, day).
        tai_from_day_sec: Convert (day, sec) to TAI.
        use_doy_format: If True, use YYYY-DDD HHh format (e.g. spacecraft).
    """
    max_mark1_mins = (tai2 - tai1) / 60.0 / 4.0
    i = len(STEP1_MINS) - 1
    while i >= 1 and STEP1_MINS[i] > max_mark1_mins:
        i -= 1
    mark1_imins = STEP1_MINS[i]
    mark2_imins = STEP2_MINS[i]
    k2 = 16
    if mark1_imins >= MINS_PER_DAY:
        k2 = 11
    if mark1_imins >= 31 * MINS_PER_DAY:
        k2 = 8
    day1, _ = day_sec_from_tai(tai1)
    dutc_ref = day1
    if mark1_imins > MINS_PER_DAY:
        # Align multi-day major ticks to an absolute day cadence.
        mark1_days = mark1_imins // MINS_PER_DAY
        dutc_ref = dutc_ref - (dutc_ref % mark1_days)
    tick_imins = MINS_PER_DAY if mark2_imins > MINS_PER_DAY else mark2_imins
    iticks_per_day = MINS_PER_DAY // tick_imins
    secs_per_tick = 86400.0 / iticks_per_day
    iticks_per_mark1 = mark1_imins // tick_imins
    iticks_per_mark2 = mark2_imins // tick_imins
    yprev = mprev = dprev = -99999
    last_mark1_tick = last_mark2_tick = -99999
    first_mark1 = True
    for tick in range(100000):
        days = tick // iticks_per_day
        secs = (tick - days * iticks_per_day) * secs_per_tick
        dutc = dutc_ref + days
        y, m, d = ymd_from_day(dutc)
        h = int(secs / 3600.0)
        tai = tai_from_day_sec(dutc, secs)
        if tai > tai2:
            break
        qmark2 = False
        if y != yprev:
            qmark1 = True
            k1 = 1
        elif m != mprev:
            qmark1 = True
            k1 = 6
        else:
            qmark1 = tick >= last_mark1_tick + iticks_per_mark1
            qmark2 = tick >= last_mark2_tick + iticks_per_mark2
            k1 = 10 if d != dprev else 13
        yprev, mprev, dprev = y, m, d
        if qmark1:
            last_mark1_tick = last_mark2_tick = tick
        elif qmark2:
            last_mark2_tick = tick
        if tai < tai1:
            continue
        if qmark1:
            k1_use = 1 if first_mark1 else k1
            first_mark1 = False
            if use_doy_format:
                doy = (date(y, m, d) - date(y, 1, 1)).days + 1
                label = f'{y:4d}-{doy:03d} {h:2d}h'
            else:
                # FORTRAN format: (i4, '-', a3, '-', i2.2, 1x, i2, 'h')
                # = 15 chars; pad to 32 to match FORTRAN character*32 label
                label = f'{y:4d}-{MONTH_NAMES[m - 1]}-{d:02d} {h:2d}h'
            # Pad to at least k2 chars (FORTRAN label is space-padded)
            label = label.ljust(32)
            # FORTRAN: label(k1:k2) — 1-based inclusive
            label = label[k1_use - 1 : k2]
            y_index = (tai - tai1) / dt + 1.0
            _emit(out, f'{y_index:7.2f} ({label}) YT1')
        elif qmark2:
            y_index = (tai - tai1) / dt + 1.0
            _emit(out, f'{y_index:7.2f} YT2')


def draw_moon_tracks(
    output: TextIO,
    planet_num: int,
    ntimes: int,
    time1_tai: float,
    time2_tai: float,
    dt: float,
    xrange: float,
    xscaled: bool,
    moon_arcsec: list[list[float]],
    limb_arcsec: list[float],
    moon_names: list[str],
    nrings: int,
    ring_flags: list[bool],
    ring_rads_km: list[float],
    ring_grays: list[float],
    planet_gray: float,
    rplanet_km: float,
    title: str,
    ncaptions: int,
    lcaptions: list[str],
    rcaptions: list[str],
    align_loc: float,
    filename: str,
    use_doy_format: bool = False,
) -> None:
    """Generate PostScript and table of east-west moon offsets (port of RSPK_TrackMoons).

    Time increases downward; west is toward the right. Moon positions are solid
    lines; rings and planet are gray zones. Title and captions supported.

    Parameters:
        output: PostScript output stream.
        planet_num: Planet index (4=Mars, 5=Jupiter, etc.).
        ntimes: Number of time steps.
        time1_tai, time2_tai: Start and stop TAI (seconds).
        dt: Time step (seconds).
        xrange: Half-range of x-axis (arcsec or planet radii).
        xscaled: True to use planet radii on x-axis.
        moon_arcsec: [moon][time] offset in arcsec.
        limb_arcsec: Limb offset per time.
        moon_names: Name per moon.
        nrings, ring_flags, ring_rads_km, ring_grays: Ring data.
        planet_gray, rplanet_km: Planet gray level and radius (km).
        title, ncaptions, lcaptions, rcaptions, align_loc: Title and captions.
        filename: Output filename (for PostScript comments).
        use_doy_format: True for YYYY-DDD HHh on y-axis (spacecraft).
    """
    nmoons = len(moon_names)
    planetstr = PLANET_NAMES.get(planet_num, 'Planet')
    i1 = max(filename.rfind('/'), filename.rfind(']'), filename.rfind(':')) + 1
    title_basename = filename[i1:] if i1 > 0 else filename

    _emit(output, '%!PS-Adobe-2.0 EPSF-2.0')
    _emit(output, f'%%Title: {title_basename}')
    _emit(output, f'%%Creator: {planetstr} Moon Tracker, PDS Ring-Moon Systems Node')
    _emit(output, '%%BoundingBox: 0 0 612 792')
    _emit(output, '%%Pages: 1')
    _emit(output, '%%DocumentFonts: Helvetica')
    _emit(output, '%%EndComments')
    _emit(output, '%')
    _emit(output, '1 setlinewidth')
    _emit(output, '/TextHeight 12 def')
    _emit(output, '/Helvetica findfont TextHeight scalefont setfont')
    _emit(output, '/in {72 mul} def')
    _emit(output, '/min {2 copy gt {exch} if pop} def')
    _emit(output, '/max {2 copy lt {exch} if pop} def')
    _emit(output, '/I1  2.0 in def')
    _emit(output, '/I2  7.5 in def')
    _emit(output, '/J1  2.0 in def')
    _emit(output, '/J2 10.0 in def')
    _emit(output, '/DI I2 I1 sub def')
    _emit(output, '/DJ J2 J1 sub def')
    _emit(output, '/Ticksize1 0.2 in def')
    _emit(output, '/Ticksize2 0.1 in def')
    _emit(output, '/DrawBox {newpath 0 0 moveto 0 DJ lineto')
    _emit(output, '  DI DJ lineto DI 0 lineto closepath stroke} def')
    _emit(output, '/ClipBox {newpath 0 0 moveto 0 DJ lineto')
    _emit(output, '  DI DJ lineto DI 0 lineto closepath clip} def')
    _emit(output, '/SetLimits {/Y2 exch def /Y1 exch def /X2 exch def')
    _emit(output, '  /X1 exch def')
    _emit(output, '  /DX X2 X1 sub def /XSCALE DI DX div def')
    _emit(output, '  /DY Y2 Y1 sub def /YSCALE DJ DY div def} def')
    _emit(output, '/Xcoord {X1 sub XSCALE mul} def')
    _emit(output, '/Ycoord {Y1 sub YSCALE mul} def')
    _emit(output, '/LabelBelow {dup stringwidth pop -0.5 mul')
    _emit(output, '  TextHeight -1.3 mul rmoveto show} def')
    _emit(output, '/LabelLeft {dup stringwidth pop TextHeight 0.3 mul')
    _emit(output, '  add neg TextHeight -0.5 mul rmoveto show} def')
    _emit(output, '/Xlabel {gsave DI 2 div TextHeight -3.0 mul')
    _emit(output, '  translate 1.2 1.2 scale dup stringwidth pop')
    _emit(output, '  -0.5 mul 0 moveto show grestore} def')
    _emit(output, '%')
    _emit(output, '% Macros for plotting ticks')
    _emit(output, '% Usage: x label XT1; x XT2; y label YT1; y YT2')
    _emit(output, '/XT1 {exch Xcoord dup DJ newpath moveto dup')
    _emit(output, '  DJ Ticksize1 sub lineto stroke dup 0 newpath')
    _emit(output, ' moveto dup Ticksize1 lineto stroke 0 moveto')
    _emit(output, '  LabelBelow} def')
    _emit(output, '/XT2 {Xcoord dup DJ newpath moveto dup')
    _emit(output, '  DJ Ticksize2 sub lineto stroke dup 0 newpath')
    _emit(output, '  moveto Ticksize2 lineto stroke} def')
    _emit(output, '/YT1 {exch Ycoord dup DI exch newpath moveto dup')
    _emit(output, '  DI Ticksize1 sub exch lineto stroke dup 0 exch')
    _emit(output, '  newpath moveto dup Ticksize1 exch lineto stroke')
    _emit(output, '  0 exch moveto LabelLeft} def')
    _emit(output, '/YT2 {Ycoord dup DI exch newpath moveto dup')
    _emit(output, '  DI Ticksize2 sub exch lineto stroke dup 0 exch')
    _emit(output, '  newpath moveto Ticksize2 exch lineto stroke} def')
    _emit(output, '%')
    _emit(output, '% Macro for labeling curves')
    _emit(output, '% Usage: y x label PutLab')
    _emit(output, '/PutLab {gsave 3 copy pop Xcoord exch Ycoord')
    _emit(output, '  translate 1 1 scale ( ) stringwidth pop')
    _emit(output, '  TextHeight -0.5 mul moveto show pop pop')
    _emit(output, '  grestore} def')
    _emit(output, '%')
    _emit(output, '% Macros for plotting curves downward')
    _emit(output, '% Usage: x1 F x2 N x3 N ... xn N D stroke')
    _emit(output, '/F {newpath Xcoord DJ moveto DJ YSCALE add dup} def')
    _emit(output, '/N {Xcoord exch lineto YSCALE add dup} def')
    _emit(output, '/D {pop pop} def')
    _emit(output, '%%EndProlog')
    _emit(output, '%')
    _emit(output, '% shift origin')
    _emit(output, 'gsave I1 J1 translate')

    _emit(output, f'{xrange:10.3f} {-xrange:10.3f} {ntimes:6d} 1 SetLimits gsave ClipBox')

    for i in range(nrings - 1, -1, -1):
        if ring_flags[i]:
            _emit(output, f'{ring_grays[i]:4.2f} setgray')
            _plot_limb(output, ntimes, limb_arcsec, xscaled, ring_rads_km[i] / rplanet_km)
    _emit(output, f'{planet_gray:4.2f} setgray')
    _plot_limb(output, ntimes, limb_arcsec, xscaled, 1.0)
    _emit(output, '0.00 setgray')

    irecband = int(BAND_WIDTH / PLOT_HEIGHT / 2 * ntimes)
    excluded = [False] * ntimes
    # FORTRAN: do i = 1, irecband+1 → excluded(i) = .TRUE.
    for i in range(irecband + 1):
        excluded[i] = True
    # FORTRAN: do i = ntimes-irecband, ntimes → excluded(i) = .TRUE.
    # In 0-based Python: indices (ntimes-1-irecband) to (ntimes-1)
    for i in range(max(0, ntimes - 1 - irecband), ntimes):
        excluded[i] = True

    _emit(output, 'ClipBox 1.5 setlinewidth')
    for i in range(nmoons):
        _plot_moon(
            output,
            ntimes,
            i,
            moon_arcsec,
            limb_arcsec,
            xrange,
            xscaled,
            moon_names[i],
            excluded,
            irecband,
        )

    _emit(output, 'grestore DrawBox')

    _label_xaxis(output, xrange, xscaled, planetstr)
    _label_yaxis(
        output,
        time1_tai,
        time2_tai,
        dt,
        day_sec_from_tai,
        ymd_from_day,
        tai_from_day_sec,
        use_doy_format,
    )

    _emit(output, 'grestore')

    if title.strip():
        _emit(output, 'gsave 4.5 in 10.5 in translate')
        _emit(output, '1.4 1.4 scale')
        _emit(output, _track_string(title.strip()))
        _emit(output, 'dup stringwidth pop')
        _emit(output, '-0.5 mul TextHeight neg moveto show grestore')

    if ncaptions > 0 and len(lcaptions) >= ncaptions and len(rcaptions) >= ncaptions:
        _emit(output, 'gsave')
        _emit(output, f'{int(align_loc) + 72:4d} 1.25 in translate')
        _emit(output, '0 TextHeight 0.4 mul translate')
        for i in range(ncaptions):
            _emit(output, '0 TextHeight -1.4 mul translate')
            _emit(output, '0 0 moveto')
            # FORTRAN: RSPK_TrackString writes parenthesized text on one line,
            # then 'show' on the next line.
            rcap = rcaptions[i].strip() if rcaptions[i].strip() else ''
            _emit(output, _track_string(rcap))
            _emit(output, 'show')
            lcap = lcaptions[i].strip() + '  '
            _emit(output, _track_string(lcap))
            _emit(output, 'dup stringwidth pop neg 0 moveto show')
        _emit(output, 'grestore')

    _emit(output, 'gsave 1 in 0.5 in translate 0.5 0.5 scale')
    _emit(output, '0 0 moveto')
    # FDATE-style 24-char date (e.g. "Wed Jun 30 21:49:08 1993")
    fdate_str = datetime.now().strftime('%a %b %d %H:%M:%S %Y')[:24]
    _emit(
        output,
        _track_string(
            f'Generated by the {planetstr} Tracker Tool, PDS Ring-Moon Systems Node, {fdate_str}'
        ),
    )
    _emit(output, 'show grestore')
    _emit(output, 'showpage')


def draw_moon_tracks_arcsec(
    output: TextIO,
    planet_num: int,
    times: list[float],
    moon_offsets: list[list[float]],
    limb_rad: float,
) -> None:
    """Draw moon tracks with x-axis in arcsec (port of RSPK_TrackMoons in arcsec mode).

    Convenience wrapper: builds limb_arcsec from single limb_rad and calls
    draw_moon_tracks with xscaled=False.

    Parameters:
        output: PostScript output stream.
        planet_num: Planet index.
        times: List of TAI times (seconds).
        moon_offsets: [moon][time] offset in radians (converted to arcsec).
        limb_rad: Limb radius in radians (used for all times).
    """

    rad_to_arcsec = 180.0 / math.pi * 3600.0
    limb_a = limb_rad * rad_to_arcsec
    limb_list = [limb_a] * len(times) if times else [0.0]
    ntimes = len(times)
    if ntimes < 2:
        return
    time1_tai = times[0]
    time2_tai = times[-1]
    dt = (time2_tai - time1_tai) / (ntimes - 1)
    xrange = max(abs(limb_a) * 2, 10.0)
    nrings, ring_rads_list, ring_grays_list = RING_DATA.get(planet_num, (0, [0.0], [0.75]))
    ring_flags = [False] * max(nrings, 1)
    ring_rads_km = (ring_rads_list + [0.0] * 5)[:5]
    ring_grays = (ring_grays_list + [0.5] * 5)[:5]
    rplanet_km = 60268.0
    draw_moon_tracks(
        output,
        planet_num,
        ntimes,
        time1_tai,
        time2_tai,
        dt,
        xrange,
        False,
        moon_offsets,
        limb_list,
        [str(i) for i in range(len(moon_offsets))],
        nrings,
        ring_flags,
        ring_rads_km,
        ring_grays,
        PLANET_GRAY,
        rplanet_km,
        '',
        0,
        [],
        [],
        180.0,
        'tracker.ps',
    )


def draw_moon_tracks_degree(
    output: TextIO,
    planet_num: int,
    times: list[float],
    moon_offsets: list[list[float]],
    limb_rad: float,
) -> None:
    """Draw moon tracks with x-axis in degrees (port of RSPK_TrackMoonC).

    Same as draw_moon_tracks_arcsec but x-axis in degrees; suitable for
    Cassini-style plots.
    """
    """Legacy: degree tracker. Not FORTRAN-identical."""
    draw_moon_tracks_arcsec(output, planet_num, times, moon_offsets, limb_rad)
