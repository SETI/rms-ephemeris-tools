"""Limb/terminator ellipse and plane-intersection helpers (ELLIPS, ECLPMD, ELIPLN, etc.)."""

from __future__ import annotations

import math

from ephemeris_tools.rendering.euclid.vec_math import (
    Vec3,
    _frame,
    _mxmt,
    _mxv,
    _vadd,
    _vdot,
    _vequ,
    _vhat,
    _vlcom,
    _vnorm,
    _vscl,
    _vsep,
    _vsub,
    _vtmv,
)


def _ellips(
    axis1: Vec3,
    axis2: Vec3,
    axis3: Vec3,
    center: Vec3,
    vufrom: Vec3,
) -> tuple[Vec3, Vec3, Vec3, Vec3, bool]:
    """Compute limb ellipse of triaxial body (port of ELLIPS).

    Returns:
        (normal, major, minor, midpnt, cansee).
    """
    r1sqr = _vdot(axis1, axis1)
    r2sqr = _vdot(axis2, axis2)
    r3sqr = _vdot(axis3, axis3)

    if r1sqr == 0.0 or r2sqr == 0.0 or r3sqr == 0.0:
        return ([0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], False)

    sight = _vsub(vufrom, center)

    cansee = (
        (_vdot(axis1, sight) ** 2) / (r1sqr**2)
        + (_vdot(axis2, sight) ** 2) / (r2sqr**2)
        + (_vdot(axis3, sight) ** 2) / (r3sqr**2)
    ) > 1.0

    if not cansee:
        return ([0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], False)

    # Build E matrix: diag(1/r1sqr, 1/r2sqr, 1/r3sqr)
    e_diag: list[Vec3] = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    e_diag[0][0] = 1.0 / r1sqr
    e_diag[1][1] = 1.0 / r2sqr
    e_diag[2][2] = 1.0 / r3sqr

    axes: list[Vec3] = [
        [axis1[0], axis1[1], axis1[2]],
        [axis2[0], axis2[1], axis2[2]],
        [axis3[0], axis3[1], axis3[2]],
    ]
    axes_t = [[axes[j][i] for j in range(3)] for i in range(3)]

    # E = E_diag * Axes^T then E = E^T * E
    e = _mxmt(e_diag, axes_t)
    e_sym: list[Vec3] = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    for i in range(3):
        for j in range(3):
            e_sym[i][j] = e[0][i] * e[0][j] + e[1][i] * e[1][j] + e[2][i] * e[2][j]
    e = e_sym

    normal = _mxv(e, sight)
    unitn = _vhat(normal)
    normal = _vequ(unitn)
    _, u, v = _frame(unitn)

    tempv1 = _vtmv(sight, e, sight)
    if tempv1 == 0.0:
        return (normal, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], True)

    lam = 1.0 / tempv1
    midpnt = _vadd(center, _vscl(lam, sight))

    alpha = _vtmv(u, e, u)
    beta = _vtmv(v, e, u)
    gamma = _vtmv(v, e, v)

    if alpha <= 0.0 or gamma <= 0.0:
        return (normal, [0.0, 0.0, 0.0], [0.0, 0.0, 0.0], midpnt, True)

    middle = (alpha + gamma) * 0.5
    tempv = [(alpha - gamma) * 0.5, beta, 0.0]
    radius = _vnorm(tempv)

    denom_a = middle - radius
    denom_b = middle + radius
    if denom_a <= 0.0:
        denom_a = 1e-30
    if denom_b <= 0.0:
        denom_b = 1e-30

    a = math.sqrt((1.0 - lam) / denom_a)
    b = math.sqrt((1.0 - lam) / denom_b)

    if radius == 0.0:
        ctheta = 1.0
        stheta = 0.0
    else:
        c2thta = tempv[0] / radius
        ctheta = math.sqrt((1.0 + c2thta) * 0.5)
        stheta = math.copysign(math.sqrt((1.0 - c2thta) * 0.5), beta)

    major = _vscl(a, _vlcom(-stheta, u, ctheta, v))
    minor = _vscl(b, _vlcom(ctheta, u, stheta, v))

    return (normal, major, minor, midpnt, cansee)


def _eclpmd(
    axis1: Vec3,
    axis2: Vec3,
    axis3: Vec3,
    center: Vec3,
    source: Vec3,
    radius: float,
) -> tuple[Vec3, Vec3, Vec3, Vec3, Vec3, Vec3, bool]:
    """Compute terminator/eclipse model (port of ECLPMD).

    Returns:
        (normal, major, minor, midpnt, vertex, caxis, canecl).
    """
    sight = _vsub(center, source)
    r1sqr = _vdot(axis1, axis1)
    r2sqr = _vdot(axis2, axis2)
    r3sqr = _vdot(axis3, axis3)

    bigone = max(math.sqrt(r1sqr), math.sqrt(r2sqr), math.sqrt(r3sqr))

    canecl = False
    if r1sqr > 0.0 and r2sqr > 0.0 and r3sqr > 0.0:
        canecl = (
            (_vdot(axis1, sight) ** 2) / (r1sqr**2)
            + (_vdot(axis2, sight) ** 2) / (r2sqr**2)
            + (_vdot(axis3, sight) ** 2) / (r3sqr**2)
        ) > 1.0 and _vnorm(sight) > bigone + radius

    z3 = [0.0, 0.0, 0.0]
    if not canecl:
        return (z3[:], z3[:], z3[:], z3[:], z3[:], z3[:], False)

    denom = radius - bigone
    if abs(denom) <= 0.0001:
        t = bigone * 10000.0
    else:
        t = bigone / denom

    vertex = _vlcom(1.0, center, t, sight)
    caxis = _vhat(sight)

    normal, major, minor, midpnt, canecl = _ellips(axis1, axis2, axis3, center, vertex)

    if _vdot(caxis, normal) < 0.0:
        normal = [-normal[0], -normal[1], -normal[2]]

    return (normal, major, minor, midpnt, vertex, caxis, canecl)


def _ovrlap(centr1: Vec3, r1: float, centr2: Vec3, r2: float) -> int:
    """Disk overlap test (port of OVRLAP). Returns -1,0,1,2,3."""
    a = _vnorm(centr1)
    b_val = _vnorm(centr2)
    if a == 0.0 or b_val == 0.0:
        return -1

    talpha = r1 / a
    tbeta = r2 / b_val
    calpha = 1.0 / math.sqrt(1.0 + talpha * talpha)
    cbeta = 1.0 / math.sqrt(1.0 + tbeta * tbeta)
    salpha = talpha * calpha
    sbeta = tbeta * cbeta

    gamma = _vsep(centr1, centr2)
    alpha = math.atan2(salpha, calpha)
    beta = math.atan2(sbeta, cbeta)

    intsct = 0
    if alpha + beta > gamma:
        if alpha + gamma <= beta:
            intsct = 1
        elif beta + gamma <= alpha:
            intsct = 2
        else:
            intsct = 3
    return intsct


def _elipln(
    normal: Vec3,
    constn: float,
    major: Vec3,
    minor: Vec3,
) -> tuple[int, list[float], list[float]]:
    """Ellipse-plane intersection (port of ELIPLN).

    Returns:
        (nintsc, cosins[2], sins[2]).
    """
    a = _vdot(major, normal)
    b = _vdot(minor, normal)
    a2 = a * a
    b2 = b * b
    a2pb2 = a2 + b2
    bc = b * constn
    c2 = constn * constn
    discrm = a2pb2 - c2

    if not (-a2pb2 <= bc <= a2pb2):
        return (0, [0.0, 0.0], [0.0, 0.0])
    if discrm < 0.0:
        return (0, [0.0, 0.0], [0.0, 0.0])
    if a2pb2 == 0.0:
        return (-1, [1.0, 0.0], [0.0, 1.0])

    if discrm == 0.0:
        a_n = a / a2pb2
        b_n = b / a2pb2
        return (1, [a_n * constn, 0.0], [b_n * constn, 0.0])

    root = math.sqrt(discrm)
    a_n = a / a2pb2
    b_n = b / a2pb2
    bc2 = b_n * constn
    ac2 = a_n * constn
    aroot = a_n * root
    broot = b_n * root
    return (
        2,
        [ac2 - broot, ac2 + broot],
        [bc2 + aroot, bc2 - aroot],
    )


def _plpnts(
    major: Vec3,
    minor: Vec3,
    center: Vec3,
    normls: list[Vec3],
    consts: list[float],
    n: int,
    solve: list[bool],
) -> tuple[list[float], list[float], int]:
    """Find ellipse-plane intersections (port of PLPNTS).

    Returns:
        (pointx, pointy, meetns).
    """
    pointx: list[float] = []
    pointy: list[float] = []
    meetns = 0
    for i in range(n):
        if solve[i]:
            c = consts[i] - _vdot(center, normls[i])
            found, cosins, sins = _elipln(normls[i], c, major, minor)
            for j in range(max(0, found)):
                pointx.append(cosins[j])
                pointy.append(sins[j])
                meetns += 1
    return (pointx, pointy, meetns)


def _arderd(x1: float, y1: float, x2: float, y2: float) -> bool:
    """Angle ordering test (port of ARDERD)."""
    if y1 >= 0.0:
        quad1 = 1 if x1 >= 0.0 else 2
    else:
        quad1 = 3 if x1 <= 0.0 else 4

    if y2 >= 0.0:
        quad2 = 1 if x2 >= 0.0 else 2
    else:
        quad2 = 3 if x2 <= 0.0 else 4

    if quad1 == quad2:
        return x2 * y1 <= x1 * y2
    return quad1 < quad2


def _asort(
    xcoord: list[float],
    ycoord: list[float],
    n: int,
) -> None:
    """Shell sort by angle (port of ASORT). Sorts in place."""
    gap = n // 2
    while gap > 0:
        for i in range(gap, n):
            j = i - gap
            while j >= 0:
                jg = j + gap
                if _arderd(xcoord[j], ycoord[j], xcoord[jg], ycoord[jg]):
                    j = -1  # break
                else:
                    xcoord[j], xcoord[jg] = xcoord[jg], xcoord[j]
                    ycoord[j], ycoord[jg] = ycoord[jg], ycoord[j]
                j -= gap
        gap = gap // 2
