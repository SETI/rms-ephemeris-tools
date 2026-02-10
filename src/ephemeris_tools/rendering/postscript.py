"""PostScript output (ported from escher ESDV07, ESCLIP, ESMAP, ESMOVE, ESWRIT)."""

from __future__ import annotations

from typing import TextIO


def clip_line(
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
) -> tuple[float, float, float, float, bool]:
    """Clip segment to rectangle. Returns (x1, y1, x2, y2, inside).

    Inside is True if the (possibly clipped) segment lies inside the rectangle.
    Port of ESCLIP: interior is x > xmin, x < xmax, y > ymin, y < ymax.
    """
    dx = x2 - x1
    dy = y2 - y1

    def in_rect(x: float, y: float) -> bool:
        return xmin < x < xmax and ymin < y < ymax

    p1_in = in_rect(x1, y1)
    p2_in = in_rect(x2, y2)
    if p1_in and p2_in:
        return (x1, y1, x2, y2, True)
    if not p1_in and not p2_in:
        if dx == 0 and dy == 0:
            return (x1, y1, x2, y2, False)
        hits: list[tuple[float, float]] = []
        for edge, (cx, cy, param) in [
            ("top", (0, ymax, (ymax - y1) / dy if dy != 0 else None)),
            ("bot", (0, ymin, (ymin - y1) / dy if dy != 0 else None)),
            ("right", (xmax, 0, (xmax - x1) / dx if dx != 0 else None)),
            ("left", (xmin, 0, (xmin - x1) / dx if dx != 0 else None)),
        ]:
            if param is None:
                continue
            if 0 <= param <= 1:
                if edge in ("top", "bot"):
                    px = x1 + param * dx
                    if xmin < px < xmax:
                        hits.append((px, cy))
                else:
                    py = y1 + param * dy
                    if ymin < py < ymax:
                        hits.append((cx, py))
        if len(hits) >= 2:
            return (hits[0][0], hits[0][1], hits[1][0], hits[1][1], True)
        return (x1, y1, x2, y2, False)

    if not p1_in:
        x1, y1, x2, y2 = x2, y2, x1, y1
        dx, dy = -dx, -dy
    t = 1.0
    if dx != 0:
        if x2 >= xmax:
            tt = (xmax - x1) / dx
            if 0 <= tt < t:
                t = tt
        if x2 <= xmin:
            tt = (xmin - x1) / dx
            if 0 <= tt < t:
                t = tt
    if dy != 0:
        if y2 >= ymax:
            tt = (ymax - y1) / dy
            if 0 <= tt < t:
                t = tt
        if y2 <= ymin:
            tt = (ymin - y1) / dy
            if 0 <= tt < t:
                t = tt
    x2 = x1 + t * dx
    y2 = y1 + t * dy
    return (x1, y1, x2, y2, True)


class PostScriptFile:
    """PostScript device: write lines, move, stroke, set gray, text (port of escher)."""

    def __init__(self, stream: TextIO) -> None:
        self._stream = stream
        self._path: list[str] = []
        self._line_width = 1.0
        self._gray = 0.0

    def _emit(self, s: str) -> None:
        self._stream.write(s + "\n")

    def write_line(self, s: str) -> None:
        """Write one raw PostScript line (for custom plotting)."""
        self._emit(s)

    def header(self, width_pt: float = 612, height_pt: float = 792) -> None:
        """Write PostScript header (portrait, margins)."""
        self._emit("%!PS-Adobe-3.0")
        self._emit("%%Creator: ephemeris_tools")
        self._emit("%%Pages: 1")
        self._emit("%%Page: 1 1")
        self._emit("save")
        self._emit("/inch {72 mul} def")
        self._emit("1 inch 2.5 inch translate")
        self._emit("72 72 scale")
        self._emit("0 setlinejoin 1 setlinecap")

    def footer(self) -> None:
        """Write PostScript footer."""
        self._emit("restore")
        self._emit("showpage")
        self._emit("%%Trailer")

    def set_line_width(self, points: float) -> None:
        """Set line width in points."""
        self._line_width = points
        self._emit(f"{points} setlinewidth")

    def set_gray(self, level: float) -> None:
        """Set gray level 0 (black) to 1 (white)."""
        self._gray = level
        self._emit(f"{level} setgray")

    def move_to(self, x: float, y: float) -> None:
        """Move current point (no draw)."""
        self._emit(f"{x} {y} moveto")

    def line_to(self, x: float, y: float) -> None:
        """Append line to path."""
        self._emit(f"{x} {y} lineto")

    def draw_line(self, x1: float, y1: float, x2: float, y2: float) -> None:
        """Draw a single line segment (move, line, stroke)."""
        self._emit(f"{x1} {y1} moveto")
        self._emit(f"{x2} {y2} lineto")
        self._emit("stroke")

    def stroke(self) -> None:
        """Stroke the current path and clear it."""
        self._emit("stroke")

    def write_string(self, text: str, x: float, y: float, size: float = 10, font: str = "Helvetica") -> None:
        """Draw a text string at (x, y) with given font and size."""
        self._emit(f"/{font} findfont {size} scalefont setfont")
        self._emit(f"{x} {y} moveto")
        safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        self._emit(f"({safe}) show")

    def map_projection_to_device(
        self,
        view: tuple[float, float, float, float],
        fov: tuple[float, float, float, float],
        pi0: float,
        pi1: float,
        lam0: float,
        lam1: float,
    ) -> None:
        """Set mapping from projection (pi, lam) to device (p, l). ESMAP1."""
        self._view = view
        self._fov = fov
        self._pi0, self._pi1 = pi0, pi1
        self._lam0, self._lam1 = lam0, lam1

    def project(self, x: float, y: float) -> tuple[float, float]:
        """Map projection coords (x, y) to device (p, l). ESMAP2."""
        v0, v1, v2, v3 = getattr(self, "_view", (0, 1, 0, 1))
        f0, f1, f2, f3 = getattr(self, "_fov", (0, 1, 0, 1))
        pi0, pi1 = getattr(self, "_pi0", 0), getattr(self, "_pi1", 1)
        lam0, lam1 = getattr(self, "_lam0", 0), getattr(self, "_lam1", 1)
        px = (x - v0) / (v1 - v0) * (pi1 - pi0) + pi0 if v1 != v0 else pi0
        py = (y - v2) / (v3 - v2) * (lam1 - lam0) + lam0 if v3 != v2 else lam0
        return (px, py)
