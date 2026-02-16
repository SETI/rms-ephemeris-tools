"""Euclid 3D rendering engine — Python port of FORTRAN Euclid toolkit.

Introduction
------------
Euclid renders the appearance of a collection of solid ellipsoids illuminated
by a number of light sources. The scene is realistic: bodies partially or
completely behind others are properly obscured, and shadows cast by bodies
onto other bodies are portrayed accurately. In addition to ellipsoids, Euclid
can draw elliptical rings, stars, and figures overlaid onto the image plane.

To use Euclid you must have a working copy of Escher — the subroutine package
that draws vectors on the display device (here, PostScript via the Escher layer).

Overview
--------
Euclid is an umbrella for entry points that give freedom in composing pictures,
analogous to composing a still photograph with a pinhole camera. Main entry
points:

  - euinit   Turn on the camera (call once per program).
  - euview   Choose lens/zoom and film (field of view, device, viewport).
  - eugeom   Place camera, subjects, and lighting.
  - euclr    Advance the film (clear the drawing region).
  - eubody   Shoot and develop one body at a time.

Additional entry points eustar, euring, eutemp allow stars, rings, and
temperature/illumination refinements in the image.

Typical usage (single picture)::

    euinit()
    euview(...)
    euclr(...)
    eugeom(...)
    for each body:
        eubody(...)

This package produces segment arrays for the Escher layer (ESDRAW/ESDUMP) so
that viewer PostScript matches FORTRAN byte-for-byte.
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
