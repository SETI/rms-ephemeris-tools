"""Escher PostScript constants (page bounds, buffer size, grayscale)."""

BSIZE = 5000  # segment buffer size (5 values per segment)

# Page bounds (Escher parameters from esdv07.f)
MINX = 360
MAXX = 5760
MINY = 1800
MAXY = 7200

# Grayscale strings: segment color 0 = white, 1 = black, 2..10 = 0.1..0.9 (FORTRAN GRAY(0:10))
_GRAY: list[str] = [
    '1.0 G',  # 0 = white
    '0.0 G',  # 1 = black
    '0.1 G',
    '0.2 G',
    '0.3 G',
    '0.4 G',
    '0.5 G',
    '0.6 G',
    '0.7 G',
    '0.8 G',
    '0.9 G',
]

BUFSZ = 64
MINWIDTH = 5
