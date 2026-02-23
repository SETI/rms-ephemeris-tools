"""3D geometry for viewer/tracker.

Ported from euclid: ELLIPS, ECLPMD, FOVCLP, PLELSG, etc.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass


@dataclass
class EllipseLimb:
    """Observed limb ellipse of a triaxial ellipsoid (port of ELLIPS output)."""

    normal: tuple[float, float, float]
    major: tuple[float, float, float]
    minor: tuple[float, float, float]
    midpt: tuple[float, float, float]
    can_see: bool


def _vnorm(v: Sequence[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def _vdot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(ax * bx for ax, bx in zip(a, b, strict=True))


def ellipsoid_limb(
    axis1: Sequence[float],
    axis2: Sequence[float],
    axis3: Sequence[float],
    center: Sequence[float],
    view_from: Sequence[float],
) -> EllipseLimb:
    """Limb ellipse of triaxial ellipsoid as seen from view_from (port of ELLIPS).

    Parameters:
        axis1, axis2, axis3: Principal axes from center (length = semi-axis length).
        center: Center of ellipsoid.
        view_from: Viewpoint position.

    Returns:
        EllipseLimb with normal, major, minor, midpt, and can_see.
    """
    a1, _a2, _a3 = list(axis1), list(axis2), list(axis3)
    cen = list(center)
    vf = list(view_from)
    obs = [vf[i] - cen[i] for i in range(3)]
    d = _vnorm(obs)
    if d < 1e-10:
        return EllipseLimb(
            normal=(0.0, 0.0, 1.0),
            major=(1.0, 0.0, 0.0),
            minor=(0.0, 1.0, 0.0),
            midpt=(cen[0], cen[1], cen[2]),
            can_see=False,
        )
    u = [obs[i] / d for i in range(3)]
    aa = [_vnorm(a1) ** 2, _vnorm(_a2) ** 2, _vnorm(_a3) ** 2]
    denom = sum(u[i] * u[i] / aa[i] for i in range(3))
    if denom <= 0:
        return EllipseLimb(
            normal=(u[0], u[1], u[2]),
            major=(1.0, 0.0, 0.0),
            minor=(0.0, 1.0, 0.0),
            midpt=(cen[0], cen[1], cen[2]),
            can_see=False,
        )
    lam = 1 / math.sqrt(denom)
    midpt_list = [cen[i] + lam * u[i] for i in range(3)]
    normal_list = [u[i] / aa[i] for i in range(3)]
    nnorm = _vnorm(normal_list)
    normal_list = [normal_list[i] / nnorm for i in range(3)]
    t1 = [a1[i] * a1[i] * u[i] for i in range(3)]
    t1n = _vnorm(t1)
    if t1n < 1e-12:
        major_vals: tuple[float, float, float] = (1.0, 0.0, 0.0)
    else:
        major_vals = (t1[0] / t1n, t1[1] / t1n, t1[2] / t1n)
    minor_list = [
        normal_list[1] * major_vals[2] - normal_list[2] * major_vals[1],
        normal_list[2] * major_vals[0] - normal_list[0] * major_vals[2],
        normal_list[0] * major_vals[1] - normal_list[1] * major_vals[0],
    ]
    mn = _vnorm(minor_list)
    if mn < 1e-12:
        minor_vals: tuple[float, float, float] = (0.0, 1.0, 0.0)
    else:
        minor_vals = (minor_list[0] / mn, minor_list[1] / mn, minor_list[2] / mn)
    return EllipseLimb(
        normal=(normal_list[0], normal_list[1], normal_list[2]),
        major=major_vals,
        minor=minor_vals,
        midpt=(midpt_list[0], midpt_list[1], midpt_list[2]),
        can_see=True,
    )


def fov_clip(x: float, y: float, z: float, cos_fov: float) -> tuple[float, float, float] | None:
    """Test if point is inside FOV cone about z-axis (port of FOVCLP).

    Parameters:
        x, y, z: Point coordinates.
        cos_fov: Cosine of half-angle of cone.

    Returns:
        (x, y, z) if point is inside cone (z/r >= cos_fov), else None.
    """
    r = math.sqrt(x * x + y * y + z * z)
    if r < 1e-10:
        return (x, y, z)
    if z / r >= cos_fov:
        return (x, y, z)
    return None


def segment_ellipse_intersect(
    p1: Sequence[float],
    p2: Sequence[float],
    center: Sequence[float],
    major: Sequence[float],
    minor: Sequence[float],
) -> list[tuple[float, float, float]]:
    """Intersection of segment p1-p2 with ellipse in 3D (port of PLELSG).

    Ellipse lies in the plane through center with semi-axes major and minor.

    Parameters:
        p1, p2: Segment endpoints.
        center: Center of ellipse.
        major: Semi-major axis vector.
        minor: Semi-minor axis vector.

    Returns:
        List of 0, 1, or 2 intersection points.
    """
    p1, p2 = list(p1), list(p2)
    center = list(center)
    major = list(major)
    minor = list(minor)
    a = _vnorm(major)
    b = _vnorm(minor)
    if a < 1e-12 or b < 1e-12:
        return []
    u_dir = [major[i] / a for i in range(3)]
    v_dir = [minor[i] / b for i in range(3)]
    d = [p2[i] - p1[i] for i in range(3)]
    p1_c = [p1[i] - center[i] for i in range(3)]
    u0 = sum(p1_c[i] * u_dir[i] for i in range(3))
    v0 = sum(p1_c[i] * v_dir[i] for i in range(3))
    du = sum(d[i] * u_dir[i] for i in range(3))
    dv = sum(d[i] * v_dir[i] for i in range(3))
    aa = (du * du) / (a * a) + (dv * dv) / (b * b)
    bb = 2.0 * (u0 * du / (a * a) + v0 * dv / (b * b))
    cc = (u0 * u0) / (a * a) + (v0 * v0) / (b * b) - 1.0
    disc = bb * bb - 4 * aa * cc
    if disc < 0:
        return []
    sqrt_d = math.sqrt(disc)
    out: list[tuple[float, float, float]] = []
    for sign in (-1, 1):
        t = (
            (-bb + sign * sqrt_d) / (2 * aa)
            if abs(aa) > 1e-12
            else (-cc / bb if abs(bb) > 1e-12 else -1)
        )
        if 0 <= t <= 1:
            pt: tuple[float, float, float] = (
                p1[0] + t * d[0],
                p1[1] + t * d[1],
                p1[2] + t * d[2],
            )
            if not out or _vnorm([pt[i] - out[-1][i] for i in range(3)]) > 1e-10:
                out.append(pt)
    return out


def ray_plane_intersect(
    refpt: Sequence[float],
    normal: Sequence[float],
    direction: Sequence[float],
    origin: Sequence[float] | None = None,
) -> tuple[float, float, float] | None:
    """Intersection of ray from origin in direction with plane (port of PLNRAY).

    Plane: <normal, x - refpt> = 0.

    Parameters:
        refpt: Point on the plane.
        normal: Plane normal.
        direction: Ray direction (need not be unit).
        origin: Ray origin (default (0,0,0)).

    Returns:
        Intersection point or None if ray is parallel or hits behind origin.
    """
    if origin is None:
        origin = (0.0, 0.0, 0.0)
    denom = _vdot(normal, direction)
    if abs(denom) < 1e-12:
        return None
    diff = [refpt[i] - origin[i] for i in range(3)]
    t = _vdot(normal, diff) / denom
    if t < 0:
        return None
    return (
        origin[0] + t * direction[0],
        origin[1] + t * direction[1],
        origin[2] + t * direction[2],
    )


def disk_overlap(
    center1: Sequence[float],
    r1: float,
    center2: Sequence[float],
    r2: float,
) -> bool:
    """Return True if two disks in the plane overlap (port of OVRLAP).

    Disks are in the xy-plane; z is ignored. Overlap when distance < r1 + r2.

    Parameters:
        center1: Center of first disk (x, y [, z]).
        r1: Radius of first disk.
        center2: Center of second disk.
        r2: Radius of second disk.

    Returns:
        True if disks overlap.
    """
    d = math.sqrt((center2[0] - center1[0]) ** 2 + (center2[1] - center1[1]) ** 2)
    return d < r1 + r2


@dataclass
class EclipseCone:
    """Eclipse/shadow cone from ellipsoid occulting a spherical source (port of ECLPMD)."""

    apex: tuple[float, float, float]
    axis: tuple[float, float, float]
    half_angle: float


def eclipse_model(
    axes: Sequence[float],
    center: Sequence[float],
    source: Sequence[float],
    radius: float,
) -> EclipseCone:
    """Eclipse cone from occulting triaxial ellipsoid and spherical source (port of ECLPMD).

    Parameters:
        axes: Ellipsoid semi-axes (axis1, axis2, axis3) as 3-vectors.
        center: Center of ellipsoid.
        source: Position of light source.
        radius: Radius of spherical source.

    Returns:
        EclipseCone with apex, axis (unit vector toward dark side), and half_angle.
    """
    center = list(center)
    source = list(source)
    sight = [center[i] - source[i] for i in range(3)]
    r1sqr = _vdot(axes[0:3], axes[0:3])
    r2sqr = _vdot(axes[3:6], axes[3:6])
    r3sqr = _vdot(axes[6:9], axes[6:9])
    a1, a2, a3 = _vnorm(axes[0:3]), _vnorm(axes[3:6]), _vnorm(axes[6:9])
    bigone = max(a1, a2, a3)
    can_ecl = False
    if r1sqr > 0 and r2sqr > 0 and r3sqr > 0:
        d1 = _vdot(axes[0:3], sight) ** 2 / (r1sqr * r1sqr)
        d2 = _vdot(axes[3:6], sight) ** 2 / (r2sqr * r2sqr)
        d3 = _vdot(axes[6:9], sight) ** 2 / (r3sqr * r3sqr)
        sight_norm = _vnorm(sight)
        can_ecl = (d1 + d2 + d3 > 1.0) and (sight_norm > bigone + radius)
    if not can_ecl:
        return EclipseCone(
            apex=(center[0], center[1], center[2]),
            axis=(1.0, 0.0, 0.0),
            half_angle=0.0,
        )
    denom = radius - bigone
    if abs(denom) <= 0.0001:
        t = bigone * 10000.0
    else:
        t = bigone / denom
    vertex = [center[i] + t * sight[i] for i in range(3)]
    axis_norm = _vnorm(sight)
    if axis_norm < 1e-12:
        caxis: tuple[float, float, float] = (1.0, 0.0, 0.0)
    else:
        caxis = (sight[0] / axis_norm, sight[1] / axis_norm, sight[2] / axis_norm)
    dist_vertex_center = t * axis_norm
    if dist_vertex_center > 1e-12:
        half_angle = math.asin(min(1.0, bigone / dist_vertex_center))
    else:
        half_angle = 0.0
    return EclipseCone(
        apex=(vertex[0], vertex[1], vertex[2]),
        axis=caxis,
        half_angle=half_angle,
    )
