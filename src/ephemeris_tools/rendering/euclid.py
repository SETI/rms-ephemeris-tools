"""Euclid 3D rendering engine — Python port of FORTRAN Euclid toolkit.

Produces segment arrays for the Escher layer (ESDRAW/ESDUMP) so that
viewer PostScript matches FORTRAN byte-for-byte.

Entry points: euinit, euview, eugeom, eubody, euring, eustar, eutemp, euclr.
"""

from __future__ import annotations

import math

from ephemeris_tools.rendering.escher import (
    EscherState,
    EscherViewState,
    esclr,
    esdraw,
    esdump,
    esview,
)

# ---------------------------------------------------------------------------
# Constants (from euclid.f PARAMETER declarations)
# ---------------------------------------------------------------------------
MXSRCS = 4
MXBODS = 100
MAXMER = 50
MAXLAT = 50
MAXBLP = 1 + MXSRCS + MAXMER + MAXLAT  # 105
STDSEG = 96
MXSEGS = STDSEG + 3 * MAXBLP + 3 * MXSRCS * MXBODS  # 1511
_PI = 3.14159265358979323846
LIMFOV = _PI * 5.0 / 12.0  # 75 degrees

# Default star font: + cross (2 segments)
STARFONT_PLUS: list[tuple[tuple[float, float], tuple[float, float]]] = [
    ((-1.0, 0.0), (1.0, 0.0)),
    ((0.0, -1.0), (0.0, 1.0)),
]

# ---------------------------------------------------------------------------
# Numeric utilities
# ---------------------------------------------------------------------------


def _dnint(x: float) -> float:
    """FORTRAN DNINT: round half away from zero (not banker's rounding)."""
    if x >= 0.0:
        return float(int(x + 0.5))
    return -float(int(-x + 0.5))


# ---------------------------------------------------------------------------
# Vector / matrix utilities (replicate NAIF SPICE toolkit routines)
# ---------------------------------------------------------------------------
Vec3 = list[float]  # mutable 3-vector


def _vdot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _vnorm(v: Vec3) -> float:
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def _vsub(a: Vec3, b: Vec3) -> Vec3:
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def _vadd(a: Vec3, b: Vec3) -> Vec3:
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]


def _vscl(s: float, v: Vec3) -> Vec3:
    return [s * v[0], s * v[1], s * v[2]]


def _vlcom(a: float, v1: Vec3, b: float, v2: Vec3) -> Vec3:
    return [a * v1[0] + b * v2[0], a * v1[1] + b * v2[1], a * v1[2] + b * v2[2]]


def _vhat(v: Vec3) -> Vec3:
    n = _vnorm(v)
    if n == 0.0:
        return [0.0, 0.0, 0.0]
    return [v[0] / n, v[1] / n, v[2] / n]


def _vequ(src: Vec3) -> Vec3:
    return [src[0], src[1], src[2]]


def _v3t(v: Vec3) -> tuple[float, float, float]:
    """Return a 3-vector as a fixed-length tuple for typed APIs."""
    return (v[0], v[1], v[2])


def _vsep(a: Vec3, b: Vec3) -> float:
    """Angular separation between two vectors (radians)."""
    ha = _vhat(a)
    hb = _vhat(b)
    d = _vdot(ha, hb)
    d = max(-1.0, min(1.0, d))
    return math.acos(d)


def _mtxv(m: list[Vec3], v: Vec3) -> Vec3:
    """Transpose(m) * v: m is row-major 3x3."""
    return [
        m[0][0] * v[0] + m[1][0] * v[1] + m[2][0] * v[2],
        m[0][1] * v[0] + m[1][1] * v[1] + m[2][1] * v[2],
        m[0][2] * v[0] + m[1][2] * v[1] + m[2][2] * v[2],
    ]


def _mxv(m: list[Vec3], v: Vec3) -> Vec3:
    """m * v: m is row-major 3x3."""
    return [
        m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
        m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
        m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
    ]


def _mtxm(a: list[Vec3], b: list[Vec3]) -> list[Vec3]:
    """Transpose(a) * b: both row-major 3x3."""
    r: list[Vec3] = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    for i in range(3):
        for j in range(3):
            r[i][j] = a[0][i] * b[0][j] + a[1][i] * b[1][j] + a[2][i] * b[2][j]
    return r


def _mxmt(a: list[Vec3], b: list[Vec3]) -> list[Vec3]:
    """a * Transpose(b): both row-major 3x3."""
    r: list[Vec3] = [[0.0, 0.0, 0.0], [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]]
    for i in range(3):
        for j in range(3):
            r[i][j] = a[i][0] * b[j][0] + a[i][1] * b[j][1] + a[i][2] * b[j][2]
    return r


def _vtmv(v: Vec3, m: list[Vec3], w: Vec3) -> float:
    """v^T * M * w (scalar quadratic form)."""
    mw = _mxv(m, w)
    return _vdot(v, mw)


def _frame(x: Vec3) -> tuple[Vec3, Vec3, Vec3]:
    """Build orthonormal frame from x. Returns (x_hat, y, z) like SPICE FRAME."""
    xh = _vhat(x)
    # Pick reference axis
    ax, ay, az = abs(xh[0]), abs(xh[1]), abs(xh[2])
    if ax <= ay and ax <= az:
        ref = [1.0, 0.0, 0.0]
    elif ay <= ax and ay <= az:
        ref = [0.0, 1.0, 0.0]
    else:
        ref = [0.0, 0.0, 1.0]
    # y = cross(x, ref) normalized
    y = [
        xh[1] * ref[2] - xh[2] * ref[1],
        xh[2] * ref[0] - xh[0] * ref[2],
        xh[0] * ref[1] - xh[1] * ref[0],
    ]
    y = _vhat(y)
    z = [xh[1] * y[2] - xh[2] * y[1], xh[2] * y[0] - xh[0] * y[2], xh[0] * y[1] - xh[1] * y[0]]
    return (xh, y, z)


def _opsgnd(a: float, b: float) -> bool:
    """True if a and b have opposite signs (FORTRAN OPSGND)."""
    return (a > 0.0 and b < 0.0) or (a < 0.0 and b > 0.0)


def _smsgnd(a: float, b: float) -> bool:
    """True if a and b have the same sign (FORTRAN SMSGND)."""
    return a * b >= 0.0


def _brcktd(x: float, lo: float, hi: float) -> float:
    """Clamp x to [lo, hi]."""
    return max(lo, min(hi, x))


# ---------------------------------------------------------------------------
# Euclid helper functions (ports of standalone FORTRAN subroutines)
# ---------------------------------------------------------------------------


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


def _euskip(major: float, center: Vec3, fovrad: float) -> int:
    """Determine segment skip count (port of EUSKIP)."""
    x = _vnorm(center)
    if x > 0.0 and fovrad > 0.0:
        ratio = major / (x * fovrad)
    else:
        ratio = 1.0
    if ratio > 0.2:
        return 1
    if ratio > 0.1:
        return 2
    if ratio > 0.04:
        return 3
    if ratio > 0.01:
        return 4
    return 6


def _fovclp(p: Vec3, q: Vec3, cosfov: float) -> tuple[Vec3, Vec3]:
    """Clip segment to FOV cone (port of FOVCLP). Returns (p, q)."""
    x = _vhat(p)
    y = _vhat(q)

    if x[2] >= cosfov and y[2] >= cosfov:
        return (_vequ(p), _vequ(q))

    cossqr = cosfov * cosfov
    qsubp = _vsub(q, p)

    c = p[2] * p[2] - cossqr * _vdot(p, p)
    b = p[2] * qsubp[2] - cossqr * _vdot(p, qsubp)
    a = qsubp[2] * qsubp[2] - cossqr * _vdot(qsubp, qsubp)

    discrm = b * b - a * c
    dump = False
    t_vals: list[float] = []

    if discrm <= 0.0:
        dump = True
    elif a == 0.0:
        if b != 0.0:
            t_vals.append(-c / b)
        else:
            dump = True
    else:
        sq = math.sqrt(discrm)
        t_vals.append((-b + sq) / a)
        t_vals.append((-b - sq) / a)

    # Keep only t in (0, 1)
    t_valid: list[float] = [t for t in t_vals if 0.0 < t < 1.0]

    if len(t_valid) == 0:
        dump = True

    if dump:
        sq = math.sqrt(1.0 - cossqr)
        pv = [sq, 0.0, cosfov]
        return (pv, _vequ(pv))

    pout = _vequ(p)
    qout = _vequ(q)

    if x[2] >= cosfov and y[2] < cosfov:
        s = min(t_valid) if len(t_valid) > 1 else t_valid[0]
        qout = _vlcom(1.0 - s, p, s, q)
    elif x[2] < cosfov and y[2] >= cosfov:
        s = max(t_valid) if len(t_valid) > 1 else t_valid[0]
        pout = _vlcom(1.0 - s, p, s, q)
    elif p[2] > 0.0 and q[2] > 0.0 and len(t_valid) >= 2:
        pout = _vlcom(1.0 - t_valid[0], p, t_valid[0], q)
        qout = _vlcom(1.0 - t_valid[1], p, t_valid[1], q)
    else:
        sq = math.sqrt(1.0 - cossqr)
        pout = [sq, 0.0, cosfov]
        qout = _vequ(pout)

    return (pout, qout)


def _smside(
    p: Vec3,
    q: Vec3,
    normal: Vec3,
    center: Vec3,
    refpnt: Vec3,
) -> bool:
    """Test if segment and refpnt are on same side of plane (port of SMSIDE)."""
    c = _vdot(center, normal)
    rfside = _vdot(refpnt, normal) - c
    pside = _vdot(p, normal) - c
    qside = _vdot(q, normal) - c

    testp = rfside * pside
    testq = rfside * qside

    if testp >= 0.0 and testq >= 0.0:
        return True
    if testp <= 0.0 and testq <= 0.0:
        return False

    small = min(abs(testp), abs(testq))
    if small == abs(testp):
        return testq >= 0.0
    return testp >= 0.0


def _plelsg(
    p: Vec3,
    q: Vec3,
    normal: Vec3,
    major: Vec3,
    minor: Vec3,
    center: Vec3,
    refpnt: Vec3,
) -> tuple[list[Vec3], list[Vec3], list[bool], list[bool], int]:
    """Project segment onto plane, intersect with ellipse (port of PLELSG).

    Returns:
        (begsub_list, endsub_list, inside_list, inback_list, nsub).
    """
    quanta = 134217728.0  # 2^27

    pref = _vsub(p, refpnt)
    qref = _vsub(q, refpnt)
    cref = _vsub(center, refpnt)

    num = _vdot(normal, cref)
    denomp = _vdot(normal, pref)
    denomq = _vdot(normal, qref)

    aquad = _vdot(major, major)
    aquad = aquad * aquad
    bquad = _vdot(minor, minor)
    bquad = bquad * bquad

    # Determine behind flag
    if num != denomp:
        behind = _opsgnd(num - denomp, num)
    elif num != denomq:
        behind = _opsgnd(num - denomq, num)
    else:
        behind = False

    # Check if endpoints are on opposite sides of plane
    if _opsgnd(denomp - num, denomq - num):
        intsct = (num - denomp) / (denomq - denomp)
        intsct = _brcktd(intsct, 0.0, 1.0)
    else:
        intsct = 2.0

    # Maximum subsegments = 4
    max_sub = 5
    t_arr = [0.0] * (max_sub + 2)
    inelip = [False] * (max_sub + 2)
    subpnt = 1

    if not _smsgnd(denomp, denomq):
        # Some point projects to infinity
        tsub = 0.0
        tempp = denomp
        tempq = denomq
        if not _smsgnd(denomp, num):
            if denomp == 0.0:
                tsub = 0.5
            else:
                tint = denomp / (denomq - denomp)
                tsub = (1.0 + tint) * 0.5
            pref = _vlcom(1.0 - tsub, pref, tsub, qref)
            tempp = _vdot(normal, pref)
            tempq = denomq
        elif not _smsgnd(denomq, num):
            if denomq == 0.0:
                tsub = 0.5
            else:
                tint = denomp / (denomq - denomp)
                tsub = tint * 0.5
            qref = _vlcom(1.0 - tsub, pref, tsub, qref)
            tempp = denomp
            tempq = _vdot(normal, qref)
        else:
            # Fallback
            return ([_vequ(p)], [_vequ(q)], [False], [False], 1)

        if tempp == 0.0 or tempq == 0.0:
            return ([_vequ(p)], [_vequ(q)], [False], [False], 1)

        prjp = _vscl(num / tempp, pref)
        prjq = _vscl(num / tempq, qref)
        pc = _vsub(prjp, cref)
        qc = _vsub(prjq, cref)

        majorp = _vdot(major, pc)
        majorq = _vdot(major, qc)
        minorp = _vdot(minor, pc)
        minorq = _vdot(minor, qc)

        if aquad == 0.0 or bquad == 0.0:
            return ([_vequ(p)], [_vequ(q)], [False], [False], 1)

        insidp = (majorp * majorp / aquad) + (minorp * minorp / bquad)
        insidq = (majorq * majorq / aquad) + (minorq * minorq / bquad)

        alpha = (majorp - majorq) ** 2 / aquad + (minorp - minorq) ** 2 / bquad
        beta_v = majorp * (majorq - majorp) / aquad + minorp * (minorq - minorp) / bquad
        gamma_v = insidp - 1.0
        discrm = beta_v * beta_v - alpha * gamma_v

        cands = 0
        s_arr = [0.0, 0.0]
        if discrm > 0.0 and alpha != 0.0:
            sq = math.sqrt(discrm)
            cands = 2
            s_arr[0] = (-beta_v - sq) / alpha
            s_arr[1] = (-beta_v + sq) / alpha

        if cands != 0:
            for i in range(cands):
                a_v = s_arr[i] * tempp
                b_v = (1.0 - s_arr[i]) * tempq
                denom = b_v + a_v
                if denom != 0.0:
                    s_arr[i] = a_v / denom
                else:
                    s_arr[i] = 0.5

            if denomp <= 0.0:
                for i in range(cands):
                    t_arr[i + 2] = tsub + (1.0 - tsub) * s_arr[i]
            elif denomq <= 0.0:
                for i in range(cands):
                    t_arr[i + 2] = tsub * s_arr[i]

            if t_arr[2] > t_arr[3]:
                t_arr[2], t_arr[3] = t_arr[3], t_arr[2]

            inelip[1] = False
            if t_arr[2] > 0.0 and t_arr[3] < 1.0:
                subpnt += 2
                inelip[1] = False
                inelip[2] = True
                inelip[3] = False
            elif t_arr[2] <= 0.0:
                if 0.0 < t_arr[3] < 1.0:
                    subpnt += 1
                    t_arr[2] = t_arr[3]
                    if denomp * num <= 0.0:
                        inelip[1] = False
                        inelip[2] = True
                    else:
                        inelip[1] = True
                        inelip[2] = False
            elif t_arr[3] >= 1.0:
                if 0.0 < t_arr[2] < 1.0:
                    subpnt += 1
                    if denomp * num <= 0.0:
                        inelip[1] = False
                        inelip[2] = True
                    else:
                        inelip[1] = True
                        inelip[2] = False
        else:
            inelip[1] = False

    elif (num / denomp > 0.0 if denomp != 0.0 else False) and (
        num / denomq > 0.0 if denomq != 0.0 else False
    ):
        # Entire segment projects normally
        prjp = _vscl(num / denomp, pref)
        prjq = _vscl(num / denomq, qref)
        pc = _vsub(prjp, cref)
        qc = _vsub(prjq, cref)

        majorp = _vdot(major, pc)
        majorq = _vdot(major, qc)
        minorp = _vdot(minor, pc)
        minorq = _vdot(minor, qc)

        if aquad == 0.0 or bquad == 0.0:
            return ([_vequ(p)], [_vequ(q)], [False], [False], 1)

        insidp = (majorp * majorp / aquad) + (minorp * minorp / bquad)
        insidq = (majorq * majorq / aquad) + (minorq * minorq / bquad)

        if insidq <= 1.0 and insidp <= 1.0:
            inelip[1] = True
        else:
            alpha = (majorp - majorq) ** 2 / aquad + (minorp - minorq) ** 2 / bquad
            beta_v = majorp * (majorq - majorp) / aquad + minorp * (minorq - minorp) / bquad
            gamma_v = insidp - 1.0
            discrm = beta_v * beta_v - alpha * gamma_v

            if insidq < 1.0 and insidp > 1.0 and discrm > 0.0 and alpha != 0.0:
                subpnt += 1
                t_arr[subpnt] = (-beta_v - math.sqrt(discrm)) / alpha
                inelip[1] = False
                inelip[2] = True
            elif insidp < 1.0 and insidq > 1.0 and discrm > 0.0 and alpha != 0.0:
                subpnt += 1
                t_arr[subpnt] = (-beta_v + math.sqrt(discrm)) / alpha
                t_arr[subpnt] = t_arr[subpnt] + (1.0 - t_arr[subpnt]) * 0.01
                inelip[1] = True
                inelip[2] = False
            elif (
                discrm > 0.0
                and gamma_v >= 0.0
                and beta_v < 0.0
                and -beta_v < alpha
                and alpha != 0.0
                and alpha + beta_v + beta_v + gamma_v >= 0.0
            ):
                if gamma_v == 0.0:
                    subpnt += 1
                    inelip[1] = True
                    inelip[2] = False
                    t_arr[subpnt] = -2.0 * beta_v / alpha
                elif alpha + beta_v + beta_v + gamma_v == 0.0:
                    subpnt += 1
                    inelip[1] = False
                    inelip[2] = True
                    t_arr[subpnt] = (-beta_v - math.sqrt(discrm)) / alpha
                else:
                    inelip[1] = False
                    inelip[2] = True
                    inelip[3] = False
                    sq = math.sqrt(discrm)
                    subpnt += 1
                    t_arr[subpnt] = (-beta_v - sq) / alpha
                    subpnt += 1
                    t_arr[subpnt] = (-beta_v + sq) / alpha
            else:
                inelip[1] = False

        # Map T values back to original segment
        for i in range(2, subpnt + 1):
            a_v = t_arr[i] * denomp
            b_v = (1.0 - t_arr[i]) * denomq
            denom = b_v + a_v
            if denom != 0.0:
                t_arr[i] = a_v / denom
            else:
                t_arr[i] = 0.5

    else:
        return ([_vequ(p)], [_vequ(q)], [False], [False], 1)

    # Set boundary T values
    subpnt += 1
    t_arr[1] = 0.0
    t_arr[subpnt] = 1.0

    # Insert plane intersection point
    if 0.0 < intsct < 1.0:
        i = 1
        while i <= subpnt and intsct > t_arr[i]:
            i += 1
        j = subpnt + 1
        while j > i:
            t_arr[j] = t_arr[j - 1]
            inelip[j] = inelip[j - 1]
            j -= 1
        t_arr[i] = intsct
        subpnt += 1

    # Build fat intervals
    tl = [0.0] * (subpnt + 2)
    tu = [0.0] * (subpnt + 2)
    tl[1] = 0.0
    tu[1] = 0.0
    tl[subpnt] = 1.0
    tu[subpnt] = 1.0

    if subpnt > 2:
        for i in range(2, subpnt):
            tl[i] = max(0.0, (_dnint(quanta * t_arr[i]) - 1.0) / quanta)
            tu[i] = min(1.0, (_dnint(quanta * t_arr[i]) + 1.0) / quanta)

        j = 2
        i = 2
        while i < subpnt:
            if tu[j] >= tl[i]:
                tu[j] = tu[i]
                inelip[j] = inelip[i]
            else:
                j += 1
                tl[j] = tl[i]
                tu[j] = tu[i]
                inelip[j] = inelip[i]
            i += 1

        j += 1
        tl[j] = 1.0
        tu[j] = 1.0
        subpnt = j

    nsub = subpnt - 1

    # Construct subsegments
    begsub_list: list[Vec3] = []
    endsub_list: list[Vec3] = []
    inside_list: list[bool] = []
    inback_list: list[bool] = []

    for i in range(1, nsub + 1):
        beg = _vlcom(1.0 - tu[i], p, tu[i], q)
        end = _vlcom(1.0 - tl[i + 1], p, tl[i + 1], q)
        begsub_list.append(beg)
        endsub_list.append(end)
        inside_list.append(inelip[i])
        if intsct > tu[i]:
            inback_list.append(behind)
        else:
            inback_list.append(not behind)

    return (begsub_list, endsub_list, inside_list, inback_list, nsub)


# ---------------------------------------------------------------------------
# Euclid state
# ---------------------------------------------------------------------------


class EuclidState:
    """Geometry and view state for Euclid (replaces FORTRAN saved variables)."""

    def __init__(self) -> None:
        self.device = 0
        self.view = (0.0, 0.0, 0.0, 0.0)
        self.fov = (0.0, 0.0, 0.0, 0.0)
        # Initialized by euinit
        self.stdcos: list[float] = [0.0] * (STDSEG + 1)
        self.stdsin: list[float] = [0.0] * (STDSEG + 1)
        self.cosfov = 0.0
        self.kaxis: Vec3 = [0.0, 0.0, 1.0]
        self.initialized = False
        # EUVIEW state
        self.fovcen: Vec3 = [0.0, 0.0, 1.0]
        self.fovrad = 0.0
        self.dspdev = 0
        # EUGEOM state
        self.nlight = 0
        self.nbody = 0
        self.radii: list[float] = []
        self.lights: list[Vec3] = []
        self.obsrvr: Vec3 = [0.0, 0.0, 0.0]
        self.camera: list[Vec3] = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        self.centrs: list[Vec3] = []
        self.prnpls: list[list[Vec3]] = []  # prnpls[body][axis] = Vec3
        self.a: list[Vec3] = []  # axis lengths a[body] = [a1, a2, a3]
        self.biga: list[float] = []
        self.smalla: list[float] = []
        self.lnorml: list[Vec3] = []
        self.lmajor: list[Vec3] = []
        self.lminor: list[Vec3] = []
        self.lcentr: list[Vec3] = []
        self.cansee: list[bool] = []
        self.tnorml: list[list[Vec3]] = []  # tnorml[body][lsrce]
        self.tmajor: list[list[Vec3]] = []
        self.tminor: list[list[Vec3]] = []
        self.tcentr: list[list[Vec3]] = []
        self.vertex: list[list[Vec3]] = []
        self.ecaxis: list[list[Vec3]] = []
        self.canecl: list[list[bool]] = []  # canecl[body][lsrce]


def euinit(state: EuclidState) -> None:
    """Initialize Euclid trig tables (port of EUINIT)."""
    angle = 2.0 * _PI / float(STDSEG)
    q4 = STDSEG // 4  # 24
    state.stdcos[q4] = 0.0
    state.stdsin[q4] = 1.0

    q8 = STDSEG // 8  # 12
    for i in range(1, q8 + 1):
        state.stdcos[i] = math.cos(float(i) * angle)
        state.stdsin[i] = math.sin(float(i) * angle)

    for i in range(q8 + 1, q4):
        state.stdsin[i] = state.stdcos[q4 - i]
        state.stdcos[i] = state.stdsin[q4 - i]

    j = 1
    for i in range(q4 + 1, STDSEG + 1):
        state.stdcos[i] = -state.stdsin[j]
        state.stdsin[i] = state.stdcos[j]
        j += 1

    state.kaxis = [0.0, 0.0, 1.0]
    state.cosfov = math.cos(LIMFOV)
    state.initialized = True


# ---------------------------------------------------------------------------
# Main entry points
# ---------------------------------------------------------------------------


def euview(
    device: int,
    h1: float,
    h2: float,
    v1: float,
    v2: float,
    x1: float,
    x2: float,
    y1: float,
    y2: float,
    euclid_state: EuclidState,
    view_state: EscherViewState,
    escher_state: EscherState,
) -> None:
    """Set viewport and FOV, initialize Escher (port of EUVIEW)."""
    if not euclid_state.initialized:
        euinit(euclid_state)

    # Compute corner directions
    corners = [
        _vhat([-x1, -y1, 1.0]),
        _vhat([-x1, -y2, 1.0]),
        _vhat([-x2, -y1, 1.0]),
        _vhat([-x2, -y2, 1.0]),
    ]

    fovcen = _vhat([-0.5 * (x1 + x2), -0.5 * (y1 + y2), 1.0])
    mincos = 2.0
    cosang = 0.0
    for c in corners:
        cosang = _vdot(c, fovcen)
        if cosang < mincos:
            mincos = cosang

    if cosang <= 0.001:
        mincos = 2.0
        for c in corners:
            if c[2] < mincos:
                mincos = c[2]
        fovcen = [0.0, 0.0, 1.0]

    euclid_state.fovrad = math.sqrt(1.0 - mincos * mincos) / mincos
    euclid_state.fovcen = fovcen
    euclid_state.dspdev = device
    euclid_state.device = device
    euclid_state.view = (h1, h2, v1, v2)
    euclid_state.fov = (x1, x2, y1, y2)

    view = (h1, h2, v1, v2)
    fov = (x1, x2, y1, y2)
    esview(device, view, fov, view_state, escher_state)


def eugeom(
    nlites: int,
    source: list[Vec3],
    srcrad: list[float],
    obsrve: Vec3,
    camfrm: list[Vec3],
    nbods: int,
    bodies: list[Vec3],
    axes: list[list[Vec3]],
    euclid_state: EuclidState,
) -> None:
    """Store scene geometry, compute limbs/terminators (port of EUGEOM)."""
    if not euclid_state.initialized:
        euinit(euclid_state)

    st = euclid_state
    st.nlight = nlites
    st.nbody = nbods
    st.radii = srcrad[:nlites]
    st.obsrvr = _vequ(obsrve)
    st.camera = [_vequ(camfrm[i]) for i in range(3)]

    # Translate to camera-centered frame, rotate to camera frame
    st.centrs = []
    st.prnpls = []
    for i in range(nbods):
        cv = _vsub(bodies[i], obsrve)
        st.centrs.append(_mtxv(camfrm, cv))
        body_axes: list[Vec3] = []
        for j in range(3):
            body_axes.append(_mtxv(camfrm, axes[i][j]))
        st.prnpls.append(body_axes)

    st.lights = []
    for i in range(nlites):
        lv = _vsub(source[i], obsrve)
        st.lights.append(_mtxv(camfrm, lv))

    # Axis lengths
    st.a = []
    st.biga = []
    st.smalla = []
    for i in range(nbods):
        a1 = _vnorm(st.prnpls[i][0])
        a2 = _vnorm(st.prnpls[i][1])
        a3 = _vnorm(st.prnpls[i][2])
        st.a.append([a1, a2, a3])
        st.biga.append(max(a1, a2, a3))
        st.smalla.append(min(a1, a2, a3))

    # Limb ellipses
    vupnt: Vec3 = [0.0, 0.0, 0.0]
    st.lnorml = []
    st.lmajor = []
    st.lminor = []
    st.lcentr = []
    st.cansee = []
    for i in range(nbods):
        normal, major, minor, midpnt, cs = _ellips(
            st.prnpls[i][0],
            st.prnpls[i][1],
            st.prnpls[i][2],
            st.centrs[i],
            vupnt,
        )
        st.lnorml.append(normal)
        st.lmajor.append(major)
        st.lminor.append(minor)
        st.lcentr.append(midpnt)
        st.cansee.append(cs)

    # Terminator planes and eclipse cones
    st.tnorml = [[[0.0, 0.0, 0.0] for _ in range(nlites)] for _ in range(nbods)]
    st.tmajor = [[[0.0, 0.0, 0.0] for _ in range(nlites)] for _ in range(nbods)]
    st.tminor = [[[0.0, 0.0, 0.0] for _ in range(nlites)] for _ in range(nbods)]
    st.tcentr = [[[0.0, 0.0, 0.0] for _ in range(nlites)] for _ in range(nbods)]
    st.vertex = [[[0.0, 0.0, 0.0] for _ in range(nlites)] for _ in range(nbods)]
    st.ecaxis = [[[0.0, 0.0, 0.0] for _ in range(nlites)] for _ in range(nbods)]
    st.canecl = [[False for _ in range(nlites)] for _ in range(nbods)]

    for j in range(nlites):
        for i in range(nbods):
            tn, tm, tmi, tc, vx, ca, ce = _eclpmd(
                st.prnpls[i][0],
                st.prnpls[i][1],
                st.prnpls[i][2],
                st.centrs[i],
                st.lights[j],
                srcrad[j],
            )
            st.tnorml[i][j] = tn
            st.tmajor[i][j] = tm
            st.tminor[i][j] = tmi
            st.tcentr[i][j] = tc
            st.vertex[i][j] = vx
            st.ecaxis[i][j] = ca
            st.canecl[i][j] = ce


def eubody(
    body: int,
    merids: int,
    latcir: int,
    srcreq: int,
    bright: int,
    dark: int,
    term: int,
    euclid_state: EuclidState,
    view_state: EscherViewState,
    escher_state: EscherState,
) -> None:
    """Draw one body (port of EUBODY)."""
    st = euclid_state
    bi = body - 1  # 0-based index

    if bi < 0 or bi >= st.nbody:
        return
    if not st.cansee[bi]:
        return

    # Check FOV overlap
    intsec = _ovrlap(st.lcentr[bi], st.biga[bi], st.fovcen, st.fovrad)
    if intsec == 0:
        return

    # Find candidate occulting bodies
    occltd = False
    bodyd = _vnorm(st.centrs[bi])
    fbodyd = bodyd + st.biga[bi]
    nbodyd = bodyd - st.biga[bi]
    nocand = 0
    ocands: list[int] = []

    i = 0
    while i < st.nbody and not occltd:
        if i != bi and st.cansee[i]:
            near = _vnorm(st.centrs[i]) - st.biga[i]
            if near < fbodyd:
                intsec = _ovrlap(
                    st.lcentr[bi],
                    st.biga[bi],
                    st.lcentr[i],
                    st.biga[i],
                )
                if intsec > 1:
                    ocands.append(i)
                    nocand += 1
                elif intsec == 1:
                    ocands.append(i)
                    nocand += 1
                    if _vnorm(st.centrs[i]) < nbodyd:
                        intsec2 = _ovrlap(
                            st.lcentr[bi],
                            st.biga[bi],
                            st.centrs[i],
                            st.smalla[i],
                        )
                        occltd = intsec2 == 1
        i += 1

    if occltd:
        return

    # NOVIEW check
    intsec = _ovrlap(
        st.lcentr[bi],
        st.biga[bi],
        st.kaxis,
        math.tan(LIMFOV),
    )
    noview = intsec != 1

    # Unit vectors along body axes
    tempv1 = _vhat(st.prnpls[bi][0])
    tempv2 = _vhat(st.prnpls[bi][1])
    tempv3 = _vhat(st.prnpls[bi][2])

    # Set up planes array
    planes = 0
    fplans = 0
    pnorml: list[Vec3] = []
    pmajor: list[Vec3] = []
    pminor: list[Vec3] = []
    pcentr: list[Vec3] = []
    tsrce: list[int] = []

    # First: limb plane
    pnorml.append(_vequ(st.lnorml[bi]))
    pmajor.append(_vequ(st.lmajor[bi]))
    pminor.append(_vequ(st.lminor[bi]))
    pcentr.append(_vequ(st.lcentr[bi]))
    tsrce.append(0)
    planes = 1
    fplans = 1

    # Terminator planes
    for lsrce in range(st.nlight):
        if st.canecl[bi][lsrce]:
            pnorml.append(_vequ(st.tnorml[bi][lsrce]))
            pmajor.append(_vequ(st.tmajor[bi][lsrce]))
            pminor.append(_vequ(st.tminor[bi][lsrce]))
            pcentr.append(_vequ(st.tcentr[bi][lsrce]))
            tsrce.append(lsrce + 1)  # 1-based light source index
            planes += 1
            fplans += 1

    # Meridian planes
    if merids > 0:
        basesn = math.sin(_PI / float(merids))
        basecs = math.cos(_PI / float(merids))
        cosang = 1.0
        sinang = 0.0
        a2 = st.a[bi][0] ** 2
        b2 = st.a[bi][1] ** 2
        num_v = a2 * b2
        denom_v = a2 * sinang * sinang + b2 * cosang * cosang

        for _ in range(merids):
            n = _vlcom(-sinang, tempv1, cosang, tempv2)
            mj = _vlcom(cosang, tempv1, sinang, tempv2)
            if denom_v > 0.0:
                t = math.sqrt(num_v / denom_v)
            else:
                t = 1.0
            mj = _vscl(t, mj)
            mi = _vequ(st.prnpls[bi][2])
            ct = _vequ(st.centrs[bi])
            pnorml.append(n)
            pmajor.append(mj)
            pminor.append(mi)
            pcentr.append(ct)
            tsrce.append(0)
            planes += 1

            x = cosang
            y = sinang
            sinang = y * basecs + x * basesn
            cosang = x * basecs - y * basesn
            denom_v = a2 * sinang * sinang + b2 * cosang * cosang

    # Latitude planes
    if latcir > 0:
        basesn = math.sin(_PI / float(latcir + 1))
        basecs = math.cos(_PI / float(latcir + 1))
        cosang = basesn
        sinang = -basecs
        a2 = st.a[bi][0] ** 2
        c2 = st.a[bi][2] ** 2
        ab = st.a[bi][0] * st.a[bi][1]

        for _ in range(latcir):
            if cosang == 0.0:
                cosang = 1e-30
            tanang = sinang / cosang
            num_v = c2 * tanang
            factor_sq = a2 + num_v * tanang
            if factor_sq > 0.0:
                factor = 1.0 / math.sqrt(factor_sq)
            else:
                factor = 1.0
            z = num_v * factor
            xv = a2 * factor
            yv = ab * factor

            mj = _vscl(xv, tempv1)
            mi = _vscl(yv, tempv2)
            ct_off = _vscl(z, tempv3)
            ct = _vadd(st.centrs[bi], ct_off)
            pnorml.append(_vequ(tempv3))
            pmajor.append(mj)
            pminor.append(mi)
            pcentr.append(ct)
            tsrce.append(0)
            planes += 1

            x = cosang
            y = sinang
            sinang = y * basecs + x * basesn
            cosang = x * basecs - y * basesn

    # Compute plane constants
    pconst: list[float] = []
    for i in range(planes):
        pconst.append(_vdot(pcentr[i], pnorml[i]))

    # Find eclipse candidates
    npsecl = 0
    ndfecl = 0
    drkreq = 1 + st.nlight - srcreq

    necand: list[int] = [0] * st.nlight
    ecands: list[list[int]] = [[] for _ in range(st.nlight)]
    eclpsd: list[bool] = [False] * st.nlight

    for j in range(st.nlight):
        srcbod = _vsub(st.centrs[bi], st.lights[j])
        bodyd_j = _vnorm(srcbod)
        fbodyd_j = bodyd_j + st.biga[bi]
        nbodyd_j = bodyd_j - st.biga[bi]
        necand[j] = 0
        eclpsd[j] = False

        i = 0
        while i < st.nbody and not eclpsd[j]:
            if i != bi and st.canecl[i][j]:
                canbod = _vsub(st.centrs[i], st.lights[j])
                if _vnorm(canbod) - st.biga[i] < fbodyd_j:
                    canbod2 = _vsub(st.tcentr[i][j], st.vertex[i][j])
                    eclbod = _vsub(st.centrs[bi], st.vertex[i][j])
                    x = st.biga[bi] / _vnorm(eclbod) if _vnorm(eclbod) > 0 else 1.0
                    x = 1.0 - x * x
                    if x <= 0.0:
                        ecands[j].append(i)
                        necand[j] += 1
                    else:
                        eclbod_s = _vscl(x, eclbod)
                        intsec = _ovrlap(eclbod_s, st.biga[bi], canbod2, st.biga[i])
                        if intsec > 1:
                            ecands[j].append(i)
                            necand[j] += 1
                        elif intsec == 1:
                            ecands[j].append(i)
                            necand[j] += 1
                            canbod3 = _vsub(st.centrs[i], st.lights[j])
                            if _vnorm(canbod3) + st.smalla[i] < nbodyd_j:
                                canbod4 = _vsub(st.centrs[i], st.vertex[i][j])
                                intsec2 = _ovrlap(
                                    eclbod_s,
                                    st.biga[bi],
                                    canbod4,
                                    st.smalla[i],
                                )
                                eclpsd[j] = intsec2 == 1
            i += 1

        if necand[j] > 0:
            npsecl += 1
        if eclpsd[j]:
            ndfecl += 1

    # Compute skip count
    skip = _euskip(st.biga[bi], st.centrs[bi], st.fovrad)

    # Process each ellipse
    solve = [True] * planes

    for ellpse in range(planes):
        solve[ellpse] = False

        # Find intersections with other planes
        coeffx, coeffy, meetns = _plpnts(
            pmajor[ellpse],
            pminor[ellpse],
            pcentr[ellpse],
            pnorml,
            pconst,
            planes,
            solve,
        )

        # Update solve array
        if ellpse < fplans - 1:
            solve[ellpse] = True
        elif ellpse == fplans - 1:
            solve[ellpse] = True
            for idx in range(ellpse + 1, planes):
                solve[idx] = False

        # Sort intersection points
        if meetns > 0:
            _asort(coeffx, coeffy, meetns)

        # Generate segments from this ellipse
        segno = 0
        nxtstd = skip
        nxtaux = 0

        begcan = _vadd(pmajor[ellpse], pcentr[ellpse])

        # Determine visibility relative to limb
        if ellpse > 0:
            vuside = -pconst[0]
            x = -pconst[0] + _vdot(begcan, pnorml[0])
            begvis = not _opsgnd(x, vuside)
        else:
            begvis = True
            endvis = True

        begseg_list: list[Vec3] = []
        endseg_list: list[Vec3] = []

        # Merge standard and auxiliary endpoints
        while nxtstd <= STDSEG - 1 and nxtaux < meetns:
            if _arderd(st.stdcos[nxtstd], st.stdsin[nxtstd], coeffx[nxtaux], coeffy[nxtaux]):
                cosang_v = st.stdcos[nxtstd]
                sinang_v = st.stdsin[nxtstd]
                nxtstd += skip
            else:
                cosang_v = coeffx[nxtaux]
                sinang_v = coeffy[nxtaux]
                nxtaux += 1

            endcan = _vadd(
                _vlcom(cosang_v, pmajor[ellpse], sinang_v, pminor[ellpse]),
                pcentr[ellpse],
            )

            if ellpse > 0:
                x = _vdot(endcan, st.lnorml[bi]) - pconst[0]
                endvis = not _opsgnd(x, vuside)
            else:
                endvis = True

            if endvis and begvis:
                segno += 1
                begseg_list.append(_vequ(begcan))
                endseg_list.append(_vequ(endcan))

            if ellpse == 0:
                pass  # limb point tracking omitted (not needed for PS output)

            begcan = _vequ(endcan)
            begvis = endvis

        # Remaining endpoints
        moresg = True
        while moresg:
            if nxtstd <= STDSEG - 1:
                cosang_v = st.stdcos[nxtstd]
                sinang_v = st.stdsin[nxtstd]
                nxtstd += skip
            elif nxtaux < meetns:
                cosang_v = coeffx[nxtaux]
                sinang_v = coeffy[nxtaux]
                nxtaux += 1
            else:
                cosang_v = 1.0
                sinang_v = 0.0
                moresg = False

            endcan = _vadd(
                _vlcom(cosang_v, pmajor[ellpse], sinang_v, pminor[ellpse]),
                pcentr[ellpse],
            )

            if ellpse > 0:
                x = _vdot(endcan, st.lnorml[bi]) - pconst[0]
                endvis = not _opsgnd(x, vuside)

            if endvis and begvis:
                segno += 1
                begseg_list.append(_vequ(begcan))
                endseg_list.append(_vequ(endcan))

            begcan = _vequ(endcan)
            begvis = endvis

        numseg = segno

        # Check occultation by other bodies
        vupnt_occ: Vec3 = [0.0, 0.0, 0.0]
        kept_beg: list[Vec3] = []
        kept_end: list[Vec3] = []

        si = 0
        while si < len(begseg_list):
            bc = _vequ(begseg_list[si])
            ec = _vequ(endseg_list[si])
            savseg = True

            oi = 0
            while oi < nocand and savseg:
                j_occ = ocands[oi]
                bsub, esub, ins, inb, ns = _plelsg(
                    bc,
                    ec,
                    st.lnorml[j_occ],
                    st.lmajor[j_occ],
                    st.lminor[j_occ],
                    st.lcentr[j_occ],
                    vupnt_occ,
                )

                sub = 0
                while sub < ns and inb[sub] and ins[sub]:
                    sub += 1

                if sub < ns:
                    bc = _vequ(bsub[sub])
                    ec = _vequ(esub[sub])
                    sub += 1
                else:
                    savseg = False

                while sub < ns:
                    if not (inb[sub] and ins[sub]):
                        begseg_list.append(_vequ(bsub[sub]))
                        endseg_list.append(_vequ(esub[sub]))
                    sub += 1
                oi += 1

            if savseg:
                kept_beg.append(bc)
                kept_end.append(ec)
            si += 1

        begseg_list = kept_beg
        endseg_list = kept_end
        numseg = len(begseg_list)

        # Determine shadow/illumination
        bright_segs: list[Vec3] = []
        bright_ends: list[Vec3] = []

        for si in range(numseg):
            bc = _vequ(begseg_list[si])
            ec = _vequ(endseg_list[si])

            ndark_v = 0
            nillum = 0

            ls = 0
            unknwn = ls < st.nlight
            while unknwn:
                if tsrce[ellpse] != ls + 1:
                    if _smside(bc, ec, st.tnorml[bi][ls], st.tcentr[bi][ls], st.lights[ls]):
                        nillum += 1
                    else:
                        ndark_v += 1
                else:
                    ndark_v += 1
                ls += 1

                if ellpse == 0 or ellpse >= fplans:
                    unknwn = nillum < srcreq and ndark_v < drkreq
                else:
                    unknwn = nillum < srcreq and ls < st.nlight

            if ellpse == 0 or ellpse >= fplans:
                if ndark_v == drkreq:
                    if noview:
                        bc, ec = _fovclp(bc, ec, st.cosfov)
                    esdraw(_v3t(bc), _v3t(ec), dark, view_state, escher_state)
                else:
                    bright_segs.append(bc)
                    bright_ends.append(ec)
            else:
                if ndark_v == drkreq and nillum == srcreq - 1:
                    if noview:
                        bc, ec = _fovclp(bc, ec, st.cosfov)
                    esdraw(_v3t(bc), _v3t(ec), term, view_state, escher_state)

        # Eclipse checks on remaining bright segments
        numseg_b = len(bright_segs)

        if ndfecl >= drkreq:
            for si in range(numseg_b):
                bc = bright_segs[si]
                ec = bright_ends[si]
                if noview:
                    bc, ec = _fovclp(bc, ec, st.cosfov)
                esdraw(_v3t(bc), _v3t(ec), dark, view_state, escher_state)
            numseg_b = 0

        if npsecl == 0 and numseg_b > 0:
            for si in range(numseg_b):
                bc = bright_segs[si]
                ec = bright_ends[si]
                if noview:
                    bc, ec = _fovclp(bc, ec, st.cosfov)
                esdraw(_v3t(bc), _v3t(ec), bright, view_state, escher_state)
            numseg_b = 0

        # Per-segment eclipse check
        si = 0
        while si < numseg_b:
            bc = _vequ(bright_segs[si])
            ec = _vequ(bright_ends[si])

            lsrce = 0
            nillum = 0
            ndark_v = 0
            notecl = ndark_v < drkreq
            notlit = nillum < srcreq

            while lsrce < st.nlight and notecl and notlit:
                curdrk = ndark_v
                unknwn2 = True

                if st.canecl[bi][lsrce] and not _smside(
                    bc, ec, st.tnorml[bi][lsrce], st.tcentr[bi][lsrce], st.lights[lsrce]
                ):
                    ndark_v += 1
                    unknwn2 = False

                j2 = 0
                notecl = ndark_v < drkreq
                notlit = nillum < srcreq
                unknwn2 = unknwn2 and notecl and notlit and (j2 < necand[lsrce])

                while unknwn2:
                    k = ecands[lsrce][j2]
                    bsub, esub, ins, inb, ns = _plelsg(
                        bc,
                        ec,
                        st.tnorml[k][lsrce],
                        st.tmajor[k][lsrce],
                        st.tminor[k][lsrce],
                        st.tcentr[k][lsrce],
                        st.vertex[k][lsrce],
                    )
                    if ns > 1:
                        bc = _vequ(bsub[0])
                        ec = _vequ(esub[0])
                        for sub in range(1, ns):
                            bright_segs.append(_vequ(bsub[sub]))
                            bright_ends.append(_vequ(esub[sub]))
                            numseg_b += 1

                    if (
                        ns >= 1
                        and ins[0]
                        and not _smside(
                            bc, ec, st.tnorml[k][lsrce], st.tcentr[k][lsrce], st.lights[lsrce]
                        )
                    ):
                        ndark_v += 1
                        unknwn2 = False

                    j2 += 1
                    unknwn2 = unknwn2 and (j2 < necand[lsrce])
                    notecl = ndark_v < drkreq

                if curdrk == ndark_v:
                    nillum += 1
                notlit = nillum < srcreq
                lsrce += 1

            if notecl:
                if noview:
                    bc, ec = _fovclp(bc, ec, st.cosfov)
                esdraw(_v3t(bc), _v3t(ec), bright, view_state, escher_state)
            else:
                if noview:
                    bc, ec = _fovclp(bc, ec, st.cosfov)
                esdraw(_v3t(bc), _v3t(ec), dark, view_state, escher_state)

            si += 1

    # Flush segment buffer
    esdump(view_state, escher_state)


def euring(
    ring_center: Vec3,
    major: Vec3,
    minor: Vec3,
    srcreq: int,
    bright: int,
    dark: int,
    euclid_state: EuclidState,
    view_state: EscherViewState,
    escher_state: EscherState,
) -> None:
    """Draw ring ellipse (port of EURING)."""
    st = euclid_state
    if not st.initialized:
        euinit(st)

    # Transform ring to camera frame
    rcentr = _vsub(ring_center, st.obsrvr)
    rcentr = _mtxv(st.camera, rcentr)
    rmajor = _mtxv(st.camera, major)
    rminor = _mtxv(st.camera, minor)

    largst = _vnorm(rmajor)
    intsec = _ovrlap(rcentr, largst, st.fovcen, st.fovrad)
    if intsec == 0:
        return

    # Find candidate occulting bodies
    occltd = False
    ringd = _vnorm(rcentr)
    fringd = ringd + largst
    nringd = ringd - largst

    x = largst / _vnorm(rcentr) if _vnorm(rcentr) > 0 else 1.0
    x = 1.0 - x * x
    occrng = _vscl(x, rcentr)

    nocand = 0
    ocands_r: list[int] = []

    i = 0
    while i < st.nbody and not occltd:
        near = _vnorm(st.centrs[i]) - st.biga[i]
        if st.cansee[i] and near < fringd:
            if x <= 0.0:
                ocands_r.append(i)
                nocand += 1
            else:
                intsec = _ovrlap(occrng, largst, st.lcentr[i], st.biga[i])
                if intsec > 1:
                    ocands_r.append(i)
                    nocand += 1
                elif intsec == 1:
                    ocands_r.append(i)
                    nocand += 1
                    if _vnorm(st.centrs[i]) + st.smalla[i] < nringd:
                        intsec2 = _ovrlap(
                            occrng,
                            largst,
                            st.centrs[i],
                            st.smalla[i],
                        )
                        occltd = intsec2 == 1
        i += 1

    if occltd:
        return

    # NOVIEW check
    if x < 0.0:
        noview = True
    else:
        intsec = _ovrlap(rcentr, largst, st.kaxis, math.tan(LIMFOV))
        noview = intsec != 1

    # Eclipse candidates
    drkreq = 1 + st.nlight - srcreq
    npsecl = 0
    ndfecl = 0
    necand_r: list[int] = [0] * st.nlight
    ecands_r: list[list[int]] = [[] for _ in range(st.nlight)]
    eclpsd_r: list[bool] = [False] * st.nlight

    for j in range(st.nlight):
        srcrng = _vsub(rcentr, st.lights[j])
        ringd_j = _vnorm(srcrng)
        fringd_j = ringd_j + largst
        nringd_j = ringd_j - largst
        necand_r[j] = 0
        eclpsd_r[j] = False

        i = 0
        while i < st.nbody and not eclpsd_r[j]:
            canbod = _vsub(st.centrs[i], st.lights[j])
            if st.canecl[i][j] and _vnorm(canbod) - st.biga[i] < fringd_j:
                canbod2 = _vsub(st.tcentr[i][j], st.vertex[i][j])
                eclrng = _vsub(rcentr, st.vertex[i][j])
                xv = largst / _vnorm(eclrng) if _vnorm(eclrng) > 0 else 1.0
                xv = 1.0 - xv * xv
                if xv <= 0.0:
                    ecands_r[j].append(i)
                    necand_r[j] += 1
                else:
                    eclrng_s = _vscl(xv, eclrng)
                    intsec = _ovrlap(eclrng_s, largst, canbod2, st.biga[i])
                    if intsec > 1:
                        ecands_r[j].append(i)
                        necand_r[j] += 1
                    elif intsec == 1:
                        ecands_r[j].append(i)
                        necand_r[j] += 1
                        canbod3 = _vsub(st.centrs[i], st.lights[j])
                        if _vnorm(canbod3) + st.smalla[i] < nringd_j:
                            canbod4 = _vsub(st.centrs[i], st.vertex[i][j])
                            intsec2 = _ovrlap(eclrng_s, largst, canbod4, st.smalla[i])
                            eclpsd_r[j] = intsec2 == 1
            i += 1

        if necand_r[j] > 0:
            npsecl += 1
        if eclpsd_r[j]:
            ndfecl += 1

    # Generate ring segments
    skip = _euskip(largst, rcentr, st.fovrad)

    begseg_list: list[Vec3] = [_vadd(rcentr, rmajor)]
    endseg_list: list[Vec3] = []

    nxtstd = skip
    segno = 0
    while nxtstd < STDSEG:
        cosang_v = st.stdcos[nxtstd]
        sinang_v = st.stdsin[nxtstd]
        endpt = _vadd(rcentr, _vlcom(cosang_v, rmajor, sinang_v, rminor))
        endseg_list.append(endpt)
        segno += 1
        begseg_list.append(_vequ(endpt))
        nxtstd += skip

    # Close the ring
    endseg_list.append(_vadd(rcentr, rmajor))
    segno += 1
    numseg = segno

    # Remove extra begin entry
    begseg_list = begseg_list[:numseg]

    # Check occultation
    vupnt_occ: Vec3 = [0.0, 0.0, 0.0]
    kept_beg: list[Vec3] = []
    kept_end: list[Vec3] = []

    si = 0
    while si < len(begseg_list):
        bc = _vequ(begseg_list[si])
        ec = _vequ(endseg_list[si])
        savseg = True

        oi = 0
        while oi < nocand and savseg:
            j_occ = ocands_r[oi]
            bsub, esub, ins, inb, ns = _plelsg(
                bc,
                ec,
                st.lnorml[j_occ],
                st.lmajor[j_occ],
                st.lminor[j_occ],
                st.lcentr[j_occ],
                vupnt_occ,
            )

            sub = 0
            while sub < ns and inb[sub] and ins[sub]:
                sub += 1

            if sub < ns:
                bc = _vequ(bsub[sub])
                ec = _vequ(esub[sub])
                sub += 1
            else:
                savseg = False

            while sub < ns:
                if not (inb[sub] and ins[sub]):
                    begseg_list.append(_vequ(bsub[sub]))
                    endseg_list.append(_vequ(esub[sub]))
                sub += 1
            oi += 1

        if savseg:
            kept_beg.append(bc)
            kept_end.append(ec)
        si += 1

    begseg_list = kept_beg
    endseg_list = kept_end
    numseg = len(begseg_list)

    # Eclipse checks
    if ndfecl >= drkreq:
        for si in range(numseg):
            bc = begseg_list[si]
            ec = endseg_list[si]
            if noview:
                bc, ec = _fovclp(bc, ec, st.cosfov)
            esdraw(_v3t(bc), _v3t(ec), dark, view_state, escher_state)
        numseg = 0

    if npsecl == 0 and numseg > 0:
        for si in range(numseg):
            bc = begseg_list[si]
            ec = endseg_list[si]
            if noview:
                bc, ec = _fovclp(bc, ec, st.cosfov)
            esdraw(_v3t(bc), _v3t(ec), bright, view_state, escher_state)
        numseg = 0

    # Per-segment eclipse check
    si = 0
    while si < numseg:
        bc = _vequ(begseg_list[si])
        ec = _vequ(endseg_list[si])

        lsrce = 0
        nillum = 0
        ndark_v = 0
        notecl = True
        notlit = True

        while lsrce < st.nlight and notecl and notlit:
            curdrk = ndark_v
            unknwn2 = True

            j2 = 0
            notecl = ndark_v < drkreq
            notlit = nillum < srcreq
            unknwn2 = unknwn2 and notecl and notlit and (j2 < necand_r[lsrce])

            while unknwn2:
                k = ecands_r[lsrce][j2]
                bsub, esub, ins, inb, ns = _plelsg(
                    bc,
                    ec,
                    st.tnorml[k][lsrce],
                    st.tmajor[k][lsrce],
                    st.tminor[k][lsrce],
                    st.tcentr[k][lsrce],
                    st.vertex[k][lsrce],
                )
                if ns > 1:
                    bc = _vequ(bsub[0])
                    ec = _vequ(esub[0])
                    for sub in range(1, ns):
                        begseg_list.append(_vequ(bsub[sub]))
                        endseg_list.append(_vequ(esub[sub]))
                        numseg += 1

                if (
                    ns >= 1
                    and ins[0]
                    and not _smside(
                        bc, ec, st.tnorml[k][lsrce], st.tcentr[k][lsrce], st.lights[lsrce]
                    )
                ):
                    ndark_v += 1
                    unknwn2 = False

                j2 += 1
                unknwn2 = unknwn2 and (j2 < necand_r[lsrce])
                notecl = ndark_v < drkreq

            if curdrk == ndark_v:
                nillum += 1
            notlit = nillum < srcreq
            lsrce += 1

        if notecl:
            if noview:
                bc, ec = _fovclp(bc, ec, st.cosfov)
            esdraw(_v3t(bc), _v3t(ec), bright, view_state, escher_state)
        else:
            if noview:
                bc, ec = _fovclp(bc, ec, st.cosfov)
            esdraw(_v3t(bc), _v3t(ec), dark, view_state, escher_state)

        si += 1

    esdump(view_state, escher_state)


def eustar(
    strpos: tuple[float, float, float],
    nstars: int,
    font: list[tuple[tuple[float, float], tuple[float, float]]],
    fntsiz: int,
    fntscl: float,
    color: int,
    euclid_state: EuclidState,
    view_state: EscherViewState,
    escher_state: EscherState,
) -> None:
    """Draw star symbol at position (port of EUSTAR)."""
    _ = nstars
    cam = euclid_state.camera
    if cam is None:
        return
    star = _mtxv(cam, list(strpos))
    if star[2] <= 0:
        return
    for i in range(min(fntsiz, len(font))):
        (fx1, fy1), (fx2, fy2) = font[i]
        scale = fntscl * star[2]
        x1 = fx1 * scale
        y1 = fy1 * scale
        x2 = fx2 * scale
        y2 = fy2 * scale
        beg = (-x1 * star[2], -y1 * star[2], star[2])
        end = (-x2 * star[2], -y2 * star[2], star[2])
        esdraw(beg, end, color, view_state, escher_state)
    esdump(view_state, escher_state)


def eutemp(
    xbegin: list[float],
    ybegin: list[float],
    xend: list[float],
    yend: list[float],
    nsegs: int,
    color: int,
    view_state: EscherViewState,
    escher_state: EscherState,
) -> None:
    """Draw overlay segments in image plane (port of EUTEMP)."""
    for i in range(nsegs):
        beg = (-xbegin[i], -ybegin[i], 1.0)
        end = (-xend[i], -yend[i], 1.0)
        esdraw(beg, end, color, view_state, escher_state)
    esdump(view_state, escher_state)


def euclr(
    device: int,
    hmin: float,
    hmax: float,
    vmin: float,
    vmax: float,
    escher_state: EscherState,
) -> None:
    """Clear viewport (port of EUCLR)."""
    region = (hmin, hmax, vmin, vmax)
    esclr(device, region, escher_state)
