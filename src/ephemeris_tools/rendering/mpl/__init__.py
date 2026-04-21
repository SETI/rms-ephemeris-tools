"""Matplotlib rendering backend for tracker and viewer tools.

Provides MplCanvas (SegmentSink), ornament dataclasses, and renderer entry
points that produce PNG/PDF/SVG output via matplotlib savefig.

All matplotlib imports are deferred to module level so that code paths using
only the Escher backend do not load matplotlib.
"""

from ephemeris_tools.rendering.mpl.canvas import MplCanvas
from ephemeris_tools.rendering.mpl.ornaments import (
    AxisLabelSpec,
    CaptionSpec,
    FooterSpec,
    MoonLabelSpec,
    StarLabelSpec,
    TitleSpec,
)

__all__ = [
    'AxisLabelSpec',
    'CaptionSpec',
    'FooterSpec',
    'MoonLabelSpec',
    'MplCanvas',
    'StarLabelSpec',
    'TitleSpec',
]
