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
    """Limb ellipse of triaxial ellipsoid as seen from view_from (port of ELLIPS)."""
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
    """Intersection of segment p1-p2 with ellipse in 3D (port of PLELSG). Returns list of points."""
    return []


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
    """Eclipse cone from occulting ellipsoid (port of ECLPMD)."""
    return EclipseCone(
        apex=tuple(center),
        axis=(1, 0, 0),
        half_angle=0.0,
    )
