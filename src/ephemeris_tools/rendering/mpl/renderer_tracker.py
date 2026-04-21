"""Matplotlib renderer for the moon tracker (draw_moon_tracks_mpl).

Produces PNG/PDF/SVG/PS output via matplotlib savefig.  Ports the tick-spacing
logic (STEP1/STEP1_MINS) and label anti-overlap logic from draw_tracker.py into
idiomatic matplotlib axes.  Time increases downward; west (positive x) is to
the right; planet/ring bands are gray filled regions.
"""

from __future__ import annotations

import math
from datetime import date, datetime

from ephemeris_tools.rendering.draw_tracker import (
    MONTH_NAMES,
    STEP1,
    STEP1_MINS,
    STEP2,
    STEP2_MINS,
    PLANET_NAMES,
    BAND_WIDTH,
)
from ephemeris_tools.rendering.mpl.theme import apply_theme, figure_and_axes, infer_format
from ephemeris_tools.time_utils import (
    day_sec_from_tai,
    tai_from_day_sec,
    yd_from_day,
    ymd_from_day,
)


def draw_moon_tracks_mpl(
    output_path: str,
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
    use_doy_format: bool = False,
    dpi: int = 150,
) -> None:
    """Render moon tracks to an image file using matplotlib.

    Parameters:
        output_path: Path to the output image file.
        planet_num: Planet index (4=Mars, 5=Jupiter, etc.).
        ntimes: Number of time steps.
        time1_tai, time2_tai: Start and stop TAI (seconds).
        dt: Time step in seconds.
        xrange: Half-range of x-axis (arcsec or planet radii).
        xscaled: True to use planet radii on x-axis.
        moon_arcsec: [moon][time] offset in arcsec.
        limb_arcsec: Limb radius per time step.
        moon_names: Name per moon.
        nrings, ring_flags, ring_rads_km, ring_grays: Ring data.
        planet_gray, rplanet_km: Planet shading and radius.
        title, ncaptions, lcaptions, rcaptions, align_loc: Ornaments.
        use_doy_format: True for YYYY-DDD HHh y-axis labels.
        dpi: Output resolution.
    """
    import numpy as np  # noqa: PLC0415
    import matplotlib.pyplot as plt  # noqa: PLC0415
    from matplotlib.collections import PolyCollection  # noqa: PLC0415

    apply_theme()

    nmoons = len(moon_names)
    planetstr = PLANET_NAMES.get(planet_num, 'Planet')

    # Time axis: y-values are record indices (1..ntimes)
    y_vals = np.arange(1, ntimes + 1, dtype=float)
    time_arr = np.array([time1_tai + i * dt for i in range(ntimes)])

    # x-axis values per moon per time
    def moon_x(imoon: int) -> 'np.ndarray':
        raw = np.array(moon_arcsec[imoon])
        if xscaled:
            limb_arr = np.array(limb_arcsec)
            with np.errstate(divide='ignore', invalid='ignore'):
                return np.where(limb_arr > 0, raw / limb_arr, 0.0)
        return raw

    def limb_x(scale: float) -> 'np.ndarray':
        if xscaled:
            return np.full(ntimes, scale)
        return np.array(limb_arcsec) * scale

    # Figure: wide-ish, tall
    fig, ax = figure_and_axes(
        fig_width_in=7.5,
        fig_height_in=10.0,
        left=0.18, right=0.92, top=0.92, bottom=0.06,
    )

    # Draw gray bands (rings, then planet) from inside out
    def fill_band(scale: float, gray: float) -> None:
        lx = limb_x(scale)
        rx = -lx
        # Polygon: left edge then right edge reversed
        xs_left = lx
        xs_right = rx
        verts = [
            list(zip(xs_left, y_vals)) + list(zip(xs_right[::-1], y_vals[::-1]))
        ]
        pc = PolyCollection(verts, facecolors=[str(gray)], edgecolors='none', zorder=1)
        ax.add_collection(pc)

    # Draw rings from outermost inward so inner rings overwrite outer ones
    for i in range(nrings - 1, -1, -1):
        if i < len(ring_flags) and ring_flags[i] and i < len(ring_rads_km):
            scale = ring_rads_km[i] / rplanet_km
            gray = ring_grays[i] if i < len(ring_grays) else 0.75
            fill_band(scale, gray)

    # Planet
    fill_band(1.0, planet_gray)

    # Moon tracks
    plot_height_frac = BAND_WIDTH / 612.0  # match FORTRAN irecband logic
    irecband = max(1, int(plot_height_frac * ntimes / 2))
    excluded = [False] * ntimes
    for i in range(min(irecband + 1, ntimes)):
        excluded[i] = True
    for i in range(max(0, ntimes - 1 - irecband), ntimes):
        excluded[i] = True

    ax.set_prop_cycle(None)  # reset color cycle
    colors = plt.rcParams['axes.prop_cycle'].by_key()['color']

    for imoon in range(nmoons):
        xs = moon_x(imoon)
        color = colors[imoon % len(colors)]
        ax.plot(xs, y_vals, lw=1.2, color=color, zorder=2)

        # Label at rightmost visible point outside exclusion zone
        xmax = -1e37
        imax = -1
        for irec in range(ntimes):
            x_val = float(xs[irec])
            if x_val < xrange and x_val > xmax and not excluded[irec]:
                xmax = x_val
                imax = irec
        if xmax > -xrange and imax >= 0:
            mname = moon_names[imoon].strip().upper()
            ax.annotate(
                mname,
                xy=(xmax, y_vals[imax]),
                xytext=(3, 0),
                textcoords='offset points',
                fontsize=7,
                va='center',
                color=color,
                zorder=3,
            )
            for j in range(max(0, imax - irecband), min(ntimes, imax + irecband + 1)):
                excluded[j] = True

    # Axis limits and invert y (time increases downward)
    ax.set_xlim(-xrange, xrange)
    ax.set_ylim(ntimes, 1)  # invert y

    # X-axis ticks (use draw_tracker.STEP1 spacing)
    x_ticks_major, x_ticks_minor, x_labels = _compute_x_ticks(xrange)
    ax.set_xticks(x_ticks_major)
    ax.set_xticklabels(x_labels, fontsize=7)
    ax.set_xticks(x_ticks_minor, minor=True)
    ax.tick_params(axis='x', which='major', length=5, top=True, bottom=True)
    ax.tick_params(axis='x', which='minor', length=3, top=True, bottom=True)

    # X-axis label
    if xscaled:
        ax.set_xlabel(f'{planetstr} radii', fontsize=9)
    elif use_doy_format:
        ax.set_xlabel('Degrees', fontsize=9)
    else:
        ax.set_xlabel('Arcsec', fontsize=9)

    # Y-axis (time) ticks and labels
    _apply_time_ticks(ax, time1_tai, time2_tai, dt, ntimes, use_doy_format)

    # Title
    if title and title.strip():
        fig.suptitle(title.strip(), fontsize=11, y=0.96)

    # Captions
    if ncaptions > 0 and lcaptions:
        ax_pos = ax.get_position()
        y_start = ax_pos.y0 - 0.01
        line_h = 0.025
        for i in range(min(ncaptions, len(lcaptions))):
            y_pos = y_start - i * line_h
            if y_pos < 0.0:
                break
            lc = lcaptions[i] if i < len(lcaptions) else ''
            rc = rcaptions[i] if i < len(rcaptions) else ''
            fig.text(ax_pos.x0, y_pos, lc, ha='left', va='top',
                     fontsize=7, fontweight='bold')
            fig.text(ax_pos.x0 + 0.20, y_pos, rc, ha='left', va='top', fontsize=7)

    # Footer
    fdate = datetime.now().strftime('%Y-%m-%d %H:%M')
    fig.text(
        0.01, 0.005,
        f'Generated by the {planetstr} Tracker Tool, PDS Ring-Moon Systems Node, {fdate}',
        ha='left', va='bottom', fontsize=5.5, color='#666666',
    )

    fmt = infer_format(output_path)
    fig.savefig(output_path, format=fmt, dpi=dpi)
    plt.close(fig)


def _compute_x_ticks(
    xrange: float,
) -> 'tuple[list[float], list[float], list[str]]':
    """Compute major and minor x-axis tick positions and labels.

    Mirrors the STEP1/STEP2 logic from draw_tracker._label_xaxis.
    """
    max_xstep = 2.0 * xrange / 3.0
    i = len(STEP1) - 1
    while i >= 1 and STEP1[i] > max_xstep:
        i -= 1
    mark1 = STEP1[i]
    mark2 = STEP2[i]

    major: list[float] = [0.0]
    minor: list[float] = []
    labels: list[str] = ['0']
    mark = mark2
    while mark <= int(xrange):
        if mark % mark1 == 0:
            major.append(float(mark))
            major.append(float(-mark))
            labels.append(str(mark))
            labels.append(f'-{mark}')
        else:
            minor.append(float(mark))
            minor.append(float(-mark))
        mark += mark2

    return major, minor, labels


def _apply_time_ticks(
    ax: object,
    tai1: float,
    tai2: float,
    dt: float,
    ntimes: int,
    use_doy_format: bool,
) -> None:
    """Apply time axis (y-axis) ticks to the axes, mirroring RSPK_LabelYAxis."""
    max_mark1_mins = (tai2 - tai1) / 60.0 / 4.0
    i = len(STEP1_MINS) - 1
    while i >= 1 and STEP1_MINS[i] > max_mark1_mins:
        i -= 1
    mark1_imins = STEP1_MINS[i]
    mark2_imins = STEP2_MINS[i]

    from ephemeris_tools.time_utils import (  # noqa: PLC0415
        day_sec_from_tai as _dsf,
        tai_from_day_sec as _tfs,
        yd_from_day as _ydf,
        ymd_from_day as _ymdf,
    )

    if use_doy_format:
        k2 = 13
        if mark1_imins >= 1440:
            k2 = 8
    else:
        k2 = 16
        if mark1_imins >= 1440:
            k2 = 11
        if mark1_imins >= 31 * 1440:
            k2 = 8

    day1, _ = _dsf(tai1)
    dutc_ref = day1
    if mark1_imins > 1440:
        mark1_days = int(mark1_imins // 1440)
        if use_doy_format:
            _, d_ref = _ydf(dutc_ref)
        else:
            _, _, d_ref = _ymdf(dutc_ref)
        dutc_ref = dutc_ref - ((d_ref - 1) % mark1_days)

    tick_imins = 1440 if mark2_imins > 1440 else mark2_imins
    iticks_per_day = 1440 // tick_imins
    secs_per_tick = 86400.0 / iticks_per_day
    iticks_per_mark1 = mark1_imins // tick_imins
    iticks_per_mark2 = mark2_imins // tick_imins

    major_ticks: list[float] = []
    major_labels: list[str] = []
    minor_ticks: list[float] = []

    yprev = mprev = dprev = -99999
    last_mark1_tick = last_mark2_tick = -99999
    first_mark1 = True

    for tick in range(100000):
        days = tick // iticks_per_day
        secs = (tick - days * iticks_per_day) * secs_per_tick
        dutc = dutc_ref + days
        y, m, d = _ymdf(dutc)
        doy = (date(y, m, d) - date(y, 1, 1)).days + 1 if use_doy_format else 0
        h = int(secs / 3600.0)
        tai = _tfs(dutc, secs)
        if tai > tai2:
            break
        qmark2 = False
        if y != yprev:
            qmark1 = True
            k1 = 1
        elif use_doy_format:
            qmark1 = tick >= last_mark1_tick + iticks_per_mark1
            qmark2 = tick >= last_mark2_tick + iticks_per_mark2
            k1 = 1 if doy != dprev else 10
        elif m != mprev:
            qmark1 = True
            k1 = 6
        else:
            qmark1 = tick >= last_mark1_tick + iticks_per_mark1
            qmark2 = tick >= last_mark2_tick + iticks_per_mark2
            k1 = 10 if d != dprev else 13
        yprev, mprev, dprev = y, m, (doy if use_doy_format else d)
        if qmark1:
            last_mark1_tick = last_mark2_tick = tick
        elif qmark2:
            last_mark2_tick = tick
        if tai < tai1:
            continue
        y_index = (tai - tai1) / dt + 1.0
        if qmark1:
            k1_use = 1 if first_mark1 else k1
            first_mark1 = False
            if k1_use > k2:
                k1_use = 1
            if use_doy_format:
                label = f'{y:4d}-{doy:03d} {h:2d}h'
            else:
                label = f'{y:4d}-{MONTH_NAMES[m - 1]}-{d:02d} {h:2d}h'
            label = label.ljust(32)
            label = label[k1_use - 1: k2].rstrip()
            major_ticks.append(y_index)
            major_labels.append(label)
        elif qmark2:
            minor_ticks.append(y_index)

    ax.set_yticks(major_ticks)  # type: ignore[union-attr]
    ax.set_yticklabels(major_labels, fontsize=7)  # type: ignore[union-attr]
    ax.set_yticks(minor_ticks, minor=True)  # type: ignore[union-attr]
    ax.tick_params(axis='y', which='major', length=5, left=True, right=True)  # type: ignore[union-attr]
    ax.tick_params(axis='y', which='minor', length=3, left=True, right=True)  # type: ignore[union-attr]
    ax.set_ylabel('Time', fontsize=9)  # type: ignore[union-attr]
