"""Euclid 3D rendering engine — Python port of FORTRAN Euclid toolkit.

Produces segment arrays for the Escher layer (ESDRAW/ESDUMP) so that
viewer PostScript matches FORTRAN byte-for-byte.

Entry points: euinit, euview, eugeom, eubody, euring, eustar, eutemp, euclr.
"""

from ephemeris_tools.rendering.euclid.body import eubody
from ephemeris_tools.rendering.euclid.clear import euclr
from ephemeris_tools.rendering.euclid.constants import STARFONT_PLUS
from ephemeris_tools.rendering.euclid.init_geom import eugeom, euinit, euview
from ephemeris_tools.rendering.euclid.ring import euring
from ephemeris_tools.rendering.euclid.star_temp import eustar, eutemp
from ephemeris_tools.rendering.euclid.state import EuclidState

__all__: list[str] = [
    'STARFONT_PLUS',
    'EuclidState',
    'eubody',
    'euclr',
    'eugeom',
    'euinit',
    'euring',
    'eustar',
    'eutemp',
    'euview',
]
