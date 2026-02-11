"""Escher PostScript output layer — Python port of FORTRAN Escher library.

Replicates the exact PostScript output from esdv07.f, esfile.f, eslwid.f,
eswrit.f, esmove.f so that Python viewer output can match FORTRAN byte-for-byte.

Coordinate system: 0.1 0.1 scale (1 unit = 0.1 points). All coordinates
are integers in this scaled space.
"""

from ephemeris_tools.rendering.escher.constants import MAXX, MAXY, MINX, MINY
from ephemeris_tools.rendering.escher.ps_output import (
    escl07,
    esdr07,
    esfile,
    eslwid,
    esmove,
    esopen,
    espl07,
    eswrit,
    write_ps_header,
)
from ephemeris_tools.rendering.escher.state import EscherState, EscherViewState
from ephemeris_tools.rendering.escher.view import esclr, esdraw, esdump, esview

__all__: list[str] = [
    'MAXX',
    'MAXY',
    'MINX',
    'MINY',
    'EscherState',
    'EscherViewState',
    'escl07',
    'esclr',
    'esdr07',
    'esdraw',
    'esdump',
    'esfile',
    'eslwid',
    'esmove',
    'esopen',
    'espl07',
    'esview',
    'eswrit',
    'write_ps_header',
]
