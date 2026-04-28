"""Matplotlib helpers for tracker and viewer tools.

Exports ``MplCanvas`` (``SegmentSink`` implementation that buffers segments and
draws them in ``finalize``) and small ornament dataclasses used when composing
figures.  High-level rendering is invoked from
``ephemeris_tools.rendering.mpl.renderer_view`` / ``renderer_tracker`` (not from
this package's ``__all__``).

All heavy matplotlib imports stay inside those modules so Escher-only code
paths avoid loading matplotlib at import time.
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
