"""Vector and matrix utilities (replicate NAIF SPICE toolkit routines)."""

from __future__ import annotations

import math

Vec3 = list[float]  # mutable 3-vector


def _dnint(x: float) -> float:
    """FORTRAN DNINT: round half away from zero (not banker's rounding)."""
    if x >= 0.0:
        return float(int(x + 0.5))
    return -float(int(-x + 0.5))


def _vdot(a: Vec3, b: Vec3) -> float:
    """Dot product of two 3-vectors (SPICE VDOT)."""
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _vnorm(v: Vec3) -> float:
    """Euclidean norm of 3-vector (SPICE VNORM)."""
    return math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])


def _vsub(a: Vec3, b: Vec3) -> Vec3:
    """Vector difference a - b (SPICE VSUB)."""
    return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]


def _vadd(a: Vec3, b: Vec3) -> Vec3:
    """Vector sum a + b (SPICE VADD)."""
    return [a[0] + b[0], a[1] + b[1], a[2] + b[2]]


def _vscl(s: float, v: Vec3) -> Vec3:
    """Scale vector: s * v (SPICE VSCL)."""
    return [s * v[0], s * v[1], s * v[2]]


def _vlcom(a: float, v1: Vec3, b: float, v2: Vec3) -> Vec3:
    """Linear combination a*v1 + b*v2 (SPICE VLCOM)."""
    return [a * v1[0] + b * v2[0], a * v1[1] + b * v2[1], a * v1[2] + b * v2[2]]


def _vhat(v: Vec3) -> Vec3:
    """Unit vector in direction of v; zero vector if v is zero (SPICE VHAT)."""
    n = _vnorm(v)
    if n == 0.0:
        return [0.0, 0.0, 0.0]
    return [v[0] / n, v[1] / n, v[2] / n]


def _vequ(src: Vec3) -> Vec3:
    """Copy 3-vector (SPICE VEQU)."""
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
