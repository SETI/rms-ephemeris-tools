"""Planet lat/lon grid for viewer (port of Euclid EUBODY meridian/lat curves)."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    import numpy as np

from ephemeris_tools.constants import SUN_ID
from ephemeris_tools.spice.bodmat import bodmat
from ephemeris_tools.spice.common import get_state
from ephemeris_tools.spice.observer import observer_state

# FORTRAN: PLANET_MERIDS=12, PLANET_LATS=11 (15°-spaced latitude circles).
PLANET_MERIDS = 12
PLANET_LATS = 11
TWOPI = 2.0 * math.pi

LineType = Literal['lit', 'dark', 'terminator']


def _vnorm(v: tuple[float, float, float]) -> float:
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def _vdot(a: tuple[float, float, float], b: tuple[float, float, float]) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _mtv(m: list[list[float]], v: tuple[float, float, float]) -> tuple[float, float, float]:
    """Matrix (3x3) transpose times vector: m.T @ v."""
    return (
        m[0][0] * v[0] + m[1][0] * v[1] + m[2][0] * v[2],
        m[0][1] * v[0] + m[1][1] * v[1] + m[2][1] * v[2],
        m[0][2] * v[0] + m[1][2] * v[1] + m[2][2] * v[2],
    )


def _surface_point_body(
    a: float, b: float, c: float, lat_rad: float, lon_rad: float
) -> tuple[float, float, float]:
    """Point on ellipsoid surface in body frame (x along a, y along b, z along c)."""
    clat = math.cos(lat_rad)
    slat = math.sin(lat_rad)
    clon = math.cos(lon_rad)
    slon = math.sin(lon_rad)
    return (
        a * clat * clon,
        b * clat * slon,
        c * slat,
    )


def _surface_normal_body(
    a: float, b: float, c: float, lat_rad: float, lon_rad: float
) -> tuple[float, float, float]:
    """Outward unit normal at surface point (normalized: (x/a^2, y/b^2, z/c^2) / norm)."""
    p = _surface_point_body(a, b, c, lat_rad, lon_rad)
    n = (p[0] / (a * a), p[1] / (b * b), p[2] / (c * c))
    nn = _vnorm(n)
    return (n[0] / nn, n[1] / nn, n[2] / nn)


def _segment_circle_intersect(
    x0: float, y0: float, x1: float, y1: float, r: float
) -> tuple[float, float] | None:
    """If segment (x0,y0)-(x1,y1) intersects circle x^2+y^2=r^2, return the
    intersection point on the segment (on the circle boundary); else None."""
    dx = x1 - x0
    dy = y1 - y0
    dr2 = dx * dx + dy * dy
    if dr2 < 1e-20:
        return None
    dot = x0 * dx + y0 * dy
    disc = r * r * dr2 - (x0 * y1 - x1 * y0) ** 2
    if disc < 0:
        return None
    t = (-dot - math.sqrt(disc)) / dr2
    if 0 <= t <= 1:
        return (x0 + t * dx, y0 + t * dy)
    t = (-dot + math.sqrt(disc)) / dr2
    if 0 <= t <= 1:
        return (x0 + t * dx, y0 + t * dy)
    return None


def _inside_circle(x: float, y: float, r: float) -> bool:
    return x * x + y * y <= r * r * 1.0001


def compute_planet_grid(
    et: float,
    planet_id: int,
    center_ra_rad: float,
    center_dec_rad: float,
    scale: float,
    n_meridians: int = PLANET_MERIDS,
    n_lats: int = PLANET_LATS,
) -> tuple[float, list[tuple[list[tuple[float, float]], LineType]]]:
    """Compute limb radius and latitude/longitude grid segments for the planet.

    No direct Fortran equivalent; used by viewer to draw planet grid in plot
    coordinates. Meridians and latitude circles; lit=black, dark=light gray,
    terminator=black.

    Parameters:
        et: Ephemeris time.
        planet_id: SPICE planet ID.
        center_ra_rad, center_dec_rad: View center (radians).
        scale: Scale factor (plot units per radian).
        n_meridians: Number of meridian circles.
        n_lats: Number of latitude circles.

    Returns:
        (limb_radius_plot, segments). Each segment is (points, line_type) with
        points in plot coordinates (origin at view center).
    """
    import cspyce

    get_state()
    obs_pv = observer_state(et)
    planet_dpv, dt = cspyce.spkapp(planet_id, et, 'J2000', obs_pv[:6].tolist(), 'LT')
    planet_time = et - dt
    planet_pv = cspyce.spkssb(planet_id, planet_time, 'J2000')
    sun_dpv, _ = cspyce.spkapp(SUN_ID, planet_time, 'J2000', planet_pv[:6], 'LT+S')
    rot_raw = bodmat(planet_id, planet_time)
    state = get_state()
    rot: list[list[float]] | np.ndarray
    if state.planet_num == 7:
        rot = [
            list(rot_raw[0]),
            list(rot_raw[1]),
            [-rot_raw[2][0], -rot_raw[2][1], -rot_raw[2][2]],
        ]
    else:
        rot = rot_raw
    rot_t = [list(col) for col in zip(rot[0], rot[1], rot[2], strict=True)]
    radii = cspyce.bodvrd(str(planet_id), 'RADII')
    a, b, c = float(radii[0]), float(radii[1]), float(radii[2])

    obs_to_planet = (
        float(planet_dpv[0]),
        float(planet_dpv[1]),
        float(planet_dpv[2]),
    )
    dist_obs = _vnorm(obs_to_planet)
    view_dir = (
        obs_to_planet[0] / dist_obs,
        obs_to_planet[1] / dist_obs,
        obs_to_planet[2] / dist_obs,
    )
    sun_from_planet = (
        float(sun_dpv[0]),
        float(sun_dpv[1]),
        float(sun_dpv[2]),
    )
    sun_norm = _vnorm(sun_from_planet)
    sun_dir = (
        sun_from_planet[0] / sun_norm,
        sun_from_planet[1] / sun_norm,
        sun_from_planet[2] / sun_norm,
    )

    limb_rad_rad = math.asin(min(1.0, a / dist_obs))
    limb_radius_plot = limb_rad_rad * scale

    def to_plot(offset_j2000: tuple[float, float, float]) -> tuple[float, float]:
        """Map J2000 offset from planet to 2D plot (x, y) in observer frame."""
        vx = obs_to_planet[0] + offset_j2000[0]
        vy = obs_to_planet[1] + offset_j2000[1]
        vz = obs_to_planet[2] + offset_j2000[2]
        r = math.sqrt(vx * vx + vy * vy + vz * vz)
        if r < 1e-10:
            return (0.0, 0.0)
        ra = math.atan2(vy, vx)
        dec = math.asin(max(-1.0, min(1.0, vz / r)))
        dx_ra = ra - center_ra_rad
        dx_dec = dec - center_dec_rad
        px = -dx_ra * math.cos(center_dec_rad) * scale
        py = dx_dec * scale
        return (px, py)

    def body_to_j2000(vb: tuple[float, float, float]) -> tuple[float, float, float]:
        """Rotate body-frame vector to J2000. bodmat gives J2000→body, so use R^T."""
        rot_t_transpose = [list(row) for row in zip(rot_t[0], rot_t[1], rot_t[2], strict=True)]
        return _mtv(rot_t_transpose, vb)

    def classify(lat_rad: float, lon_rad: float) -> tuple[bool, LineType]:
        """Return (visible from observer, line type lit/dark) for body lat/lon."""
        normal_b = _surface_normal_body(a, b, c, lat_rad, lon_rad)
        normal_j = body_to_j2000(normal_b)
        toward_obs = _vdot(normal_j, view_dir) > 0
        toward_sun = _vdot(normal_j, sun_dir) > 0
        if toward_sun:
            line_type: LineType = 'lit'
        else:
            line_type = 'dark'
        return (toward_obs, line_type)

    segments: list[tuple[list[tuple[float, float]], LineType]] = []
    n_sample = 120

    def emit_curve(
        sample_pts: list[tuple[float, float]],
        sample_visible: list[bool],
        sample_type: list[LineType],
    ) -> None:
        """Emit segment polylines from sampled curve; clip to limb circle."""
        points_plot: list[tuple[float, float]] = []
        for i, (lat_rad, lon_rad) in enumerate(sample_pts):
            pt_body = _surface_point_body(a, b, c, lat_rad, lon_rad)
            pt_j2000 = body_to_j2000(pt_body)
            px, py = to_plot(pt_j2000)
            inside = _inside_circle(px, py, limb_radius_plot)
            if not inside:
                if points_plot:
                    inter = _segment_circle_intersect(
                        points_plot[-1][0],
                        points_plot[-1][1],
                        px,
                        py,
                        limb_radius_plot,
                    )
                    if inter:
                        points_plot.append(inter)
                    seg_type = sample_type[i - 1] if i > 0 else sample_type[i]
                    if points_plot:
                        segments.append((list(points_plot), seg_type))
                    points_plot = []
                continue
            if not sample_visible[i]:
                if points_plot:
                    seg_type = sample_type[i - 1]
                    segments.append((list(points_plot), seg_type))
                    points_plot = []
                continue
            if points_plot and i > 0 and sample_type[i] != sample_type[i - 1]:
                inter_lat = (sample_pts[i - 1][0] + lat_rad) / 2
                inter_lon = (sample_pts[i - 1][1] + lon_rad) / 2
                pt_mid = _surface_point_body(a, b, c, inter_lat, inter_lon)
                pt_mid_j = body_to_j2000(pt_mid)
                mx, my = to_plot(pt_mid_j)
                if _inside_circle(mx, my, limb_radius_plot):
                    points_plot.append((mx, my))
                    segments.append((list(points_plot), 'terminator'))
                    points_plot = [(mx, my)]
                else:
                    segments.append((list(points_plot), sample_type[i - 1]))
                    points_plot = []
            points_plot.append((px, py))
        if points_plot:
            segments.append((list(points_plot), sample_type[-1]))

    # Meridians: fixed longitude, lat -90 to 90.
    for im in range(n_meridians):
        lon_rad = (im * TWOPI / n_meridians) % TWOPI
        sample_pts = []
        sample_visible = []
        sample_type = []
        for j in range(n_sample + 1):
            t = -1.0 + 2.0 * j / n_sample
            lat_rad = math.asin(max(-1.0, min(1.0, t)))
            pt_body = _surface_point_body(a, b, c, lat_rad, lon_rad)
            pt_j2000 = body_to_j2000(pt_body)
            px, py = to_plot(pt_j2000)
            inside = _inside_circle(px, py, limb_radius_plot)
            vis, ltype = classify(lat_rad, lon_rad)
            sample_pts.append((lat_rad, lon_rad))
            sample_visible.append(vis and inside)
            sample_type.append(ltype)
        emit_curve(sample_pts, sample_visible, sample_type)

    # Latitude circles: fixed latitude, lon 0 to 2*pi.
    for il in range(n_lats):
        lat_rad = math.pi * (il + 1) / (n_lats + 1) - math.pi / 2
        sample_pts = []
        sample_visible = []
        sample_type = []
        for j in range(n_sample + 1):
            lon_rad = j * TWOPI / n_sample
            pt_body = _surface_point_body(a, b, c, lat_rad, lon_rad)
            pt_j2000 = body_to_j2000(pt_body)
            px, py = to_plot(pt_j2000)
            inside = _inside_circle(px, py, limb_radius_plot)
            vis, ltype = classify(lat_rad, lon_rad)
            sample_pts.append((lat_rad, lon_rad))
            sample_visible.append(vis and inside)
            sample_type.append(ltype)
        emit_curve(sample_pts, sample_visible, sample_type)

    return (limb_radius_plot, segments)
