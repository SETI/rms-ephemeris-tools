"""Escher and view state classes (FORTRAN common block equivalents)."""

from __future__ import annotations

from typing import TextIO

from ephemeris_tools.rendering.escher.constants import MINWIDTH


class EscherState:
    """Mutable state for Escher PS output (replaces FORTRAN common block)."""

    def __init__(self) -> None:
        self.outfil = ' '
        self.creator = ' '
        self.fonts = ' '
        self.outuni: TextIO | None = None
        self.xsave = 0
        self.ysave = 0
        self.drawn = False
        self.open = False
        self.oldcol = -9999
        self.oldwidth = MINWIDTH
        self.external_stream = False  # If True, ESCL07 full-page does not close outuni.


class EscherViewState:
    """Viewport and FOV for 3D->2D mapping; segment buffer for ESDRAW/ESDUMP."""

    def __init__(self) -> None:
        self.device = 0
        self.view = (0.0, 0.0, 0.0, 0.0)  # Hmin, Hmax, Vmin, Vmax (0-1)
        self.fov = (0.0, 0.0, 0.0, 0.0)  # Xmin, Xmax, Ymin, Ymax
        self._xmin = 0.0
        self._xmax = 0.0
        self._ymin = 0.0
        self._ymax = 0.0
        self._ux = 0.0
        self._uy = 0.0
        self._xcen = 0.0
        self._ycen = 0.0
        self._pcen = 0.0
        self._lcen = 0.0
        self.segbuf: list[int] = []
        self._initialized = False
