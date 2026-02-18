"""Planet viewer PostScript rendering (port of rspk_drawview.f).

Generates PostScript via the Escher/Euclid pipeline to produce output
identical to the FORTRAN viewer.  The rendering flow mirrors
rspk_drawview.f exactly:

1. PS preamble (font macros, label macros)
2. Title, captions, credit, axis labels
3. Camera matrix and EUVIEW
4. SPICE geometry: observer, planet, Sun, bodies, rings
5. EUGEOM + EUBODY + EURING drawing
6. Border box, tick marks, labels
7. Moon labels, stars
8. EUCLR
"""

from ephemeris_tools.rendering.draw_view_helpers import (
    FOV_PTS,
    _rspk_write_label,
    camera_matrix,
    radec_to_plot,
)
from ephemeris_tools.rendering.draw_view_impl import (
    DrawPlanetaryViewOptions,
    draw_planetary_view,
)

__all__ = [
    'FOV_PTS',
    'DrawPlanetaryViewOptions',
    '_rspk_write_label',
    'camera_matrix',
    'draw_planetary_view',
    'radec_to_plot',
]
