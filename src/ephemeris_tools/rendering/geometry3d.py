"""3D geometry for viewer/tracker (ported from euclid: ELLIPS, ECLPMD, FOVCLP, PLELSG, etc.)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence


@dataclass
class EllipseLimb:
    """Observed limb ellipse of a triaxial ellipsoid (ELLIPS output)."""

    normal: tuple[float, float, float]
    major: tuple[float, float, float]
    minor: tuple[float, float, float]
    midpt: tuple[float, float, float]
    can_see: bool


def _vnorm(v: Sequence[float]) -> float:
    return math.sqrt(sum(x * x for x in v))


def _vdot(a: Sequence[float], b: Sequence[float]) -> float:
    return sum(ax * bx for ax, bx in zip(a, b))


def ellipsoid_limb(
    axis1: Sequence[float],
    axis2: Sequence[float],
    axis3: Sequence[float],
    center: Sequence[float],
    view_from: Sequence[float],
) -> EllipseLimb:
    """Limb ellipse of triaxial ellipsoid as seen from view_from (port of ELLIPS).

    Returns the projected limb as a 2D ellipse in 3D: normal to limb plane,
    semi-major and semi-minor vectors, and center (midpt). CANSEE is True
    when the observer is outside the body.
    """
    a1, a2, a3 = list(axis1), list(axis2), list(axis3)
    cen = list(center)
    vf = list(view_from)
    obs = [vf[i] - cen[i] for i in range(3)]
    d = _vnorm(obs)
    if d < 1e-10:
        return EllipseLimb(
            normal=(0, 0, 1),
            major=(1, 0, 0),
            minor=(0, 1, 0),
            midpt=tuple(cen),
            can_see=False,
        )
    u = [obs[i] / d for i in range(3)]
    aa = [a1[i] * a1[i] for i in range(3)]
    denom = sum(u[i] * u[i] / aa[i] for i in range(3))
    if denom <= 0:
        return EllipseLimb(
            normal=tuple(u),
            major=(1, 0, 0),
            minor=(0, 1, 0),
            midpt=tuple(cen),
            can_see=False,
        )
    lam = 1 / math.sqrt(denom)
    midpt = [cen[i] + lam * u[i] for i in range(3)]
    normal = [u[i] / aa[i] for i in range(3)]
    nnorm = _vnorm(normal)
    normal = [normal[i] / nnorm for i in range(3)]
    t1 = [a1[i] * a1[i] * u[i] for i in range(3)]
    t1n = _vnorm(t1)
    if t1n < 1e-12:
        major = (1, 0, 0)
    else:
        major = tuple(t1[i] / t1n for i in range(3))
    minor = [
        normal[1] * major[2] - normal[2] * major[1],
        normal[2] * major[0] - normal[0] * major[2],
        normal[0] * major[1] - normal[1] * major[0],
    ]
    mn = _vnorm(minor)
    if mn < 1e-12:
        minor = (0, 1, 0)
    else:
        minor = tuple(minor[i] / mn for i in range(3))
    return EllipseLimb(
        normal=tuple(normal),
        major=tuple(major),
        minor=tuple(minor),
        midpt=tuple(midpt),
        can_see=True,
    )


def fov_clip(
    x: float, y: float, z: float, cos_fov: float
) -> tuple[float, float, float] | None:
    """Clip point to field-of-view cone (port of FOVCLP). Returns clipped (x,y,z) or None."""
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

    Ellipse is in the plane through center spanned by major and minor semi-axis
    vectors. Returns 0, 1, or 2 intersection points.
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
    out = []
    for sign in (-1, 1):
        t = (-bb + sign * sqrt_d) / (2 * aa) if abs(aa) > 1e-12 else (-cc / bb if abs(bb) > 1e-12 else -1)
        if 0 <= t <= 1:
            pt = tuple(p1[i] + t * d[i] for i in range(3))
            if not out or _vnorm([pt[i] - out[-1][i] for i in range(3)]) > 1e-10:
                out.append(pt)
    return out


def ray_plane_intersect(
    refpt: Sequence[float],
    normal: Sequence[float],
    direction: Sequence[float],
) -> tuple[float, float, float] | None:
    """Ray-plane intersection (port of PLNRAY). Returns point or None."""
    denom = _vdot(normal, direction)
    if abs(denom) < 1e-12:
        return None
    diff = [refpt[i] - 0 for i in range(3)]
    t = _vdot(normal, diff) / denom
    if t < 0:
        return None
    return tuple(refpt[i] + t * direction[i] for i in range(3))


def disk_overlap(
    center1: Sequence[float],
    r1: float,
    center2: Sequence[float],
    r2: float,
) -> bool:
    """True if two disks (in plane) overlap (port of OVRLAP)."""
    d = math.sqrt(
        (center2[0] - center1[0]) ** 2
        + (center2[1] - center1[1]) ** 2
    )
    return d < r1 + r2


@dataclass
class EclipseCone:
    """Eclipse/shadow cone (port of ECLPMD)."""

    apex: tuple[float, float, float]
    axis: tuple[float, float, float]
    half_angle: float


def eclipse_model(
    axes: Sequence[float],
    center: Sequence[float],
    source: Sequence[float],
    radius: float,
) -> EclipseCone:
    """Eclipse cone from occulting triaxial ellipsoid (port of ECLPMD).

    Input: ellipsoid semi-axes (axis1, axis2, axis3) as 3-vectors, center, light
    source position, and source angular radius (e.g. Sun radius in rad).
    Output: cone apex (behind body), axis (unit vector toward dark side), half_angle
    (angular radius of body from apex). Used to classify ring segments as shadowed.
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
            apex=tuple(center),
            axis=(1, 0, 0),
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
        caxis = (1, 0, 0)
    else:
        caxis = tuple(sight[i] / axis_norm for i in range(3))
    dist_vertex_center = t * axis_norm
    if dist_vertex_center > 1e-12:
        half_angle = math.asin(min(1.0, bigone / dist_vertex_center))
    else:
        half_angle = 0.0
    return EclipseCone(
        apex=tuple(vertex),
        axis=caxis,
        half_angle=half_angle,
    )
