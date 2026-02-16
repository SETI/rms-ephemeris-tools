"""Euclid constants (from euclid.f PARAMETER declarations)."""

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
