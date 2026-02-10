"""Planet viewer PostScript rendering (port of rspk_drawview)."""

from __future__ import annotations

from typing import TextIO

# Plot size and center (points). All coordinates in points; no extra scale.
_VIEW_SIZE = 400.0
_VIEW_CX = _VIEW_SIZE / 2.0
_VIEW_CY = _VIEW_SIZE / 2.0
_MOON_RADIUS_PT = 2.0
_FONT_SIZE = 10.0
_MARGIN_LEFT = 72.0
_MARGIN_BOTTOM = 180.0


def _emit(out: TextIO, s: str) -> None:
    out.write(s + "\n")


def _write_string_safe(out: TextIO, text: str, x: float, y: float, size: float) -> None:
    """Draw text at (x, y), escaping parentheses for PostScript."""
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    _emit(out, f"/Helvetica findfont {size} scalefont setfont")
    _emit(out, f"{x} {y} moveto")
    _emit(out, f"({safe}) show")


def draw_planetary_view(
    output: TextIO,
    planet_name: str,
    limb_radius_plot: float,
    bodies_plot: list[tuple[float, float, str, bool]],
    title: str,
) -> None:
    """Generate PostScript diagram of planet and moons in field of view.

    bodies_plot: list of (x, y, label, is_planet) in plot coordinates (origin
    at center of field). Planet entry is drawn as a filled disk; moons as
    small circles with labels. Uses point coordinates (no 72x scale) so the
    diagram fits on the page.
    """
    _emit(output, "%!PS-Adobe-3.0")
    _emit(output, "%%Creator: ephemeris_tools")
    _emit(output, "%%Pages: 1")
    _emit(output, "%%Page: 1 1")
    _emit(output, "save")
    _emit(output, "/inch {72 mul} def")
    _emit(output, "1 inch 2.5 inch translate")
    _emit(output, "0 setlinejoin 1 setlinecap")
    _emit(output, "0 setgray")
    _emit(output, "1 setlinewidth")

    # Title above view box (y = view size + 16 pt).
    _write_string_safe(output, title, 0, _VIEW_SIZE + 16, _FONT_SIZE + 2)

    # View box and diagram in 0..400, 0..400.
    w = _VIEW_SIZE
    _emit(output, f"0 0 moveto {w} 0 rlineto 0 {w} rlineto {-w} 0 rlineto closepath stroke")

    for x, y, label, is_planet in bodies_plot:
        px = _VIEW_CX + x
        py = _VIEW_CY + y
        if is_planet:
            _emit(output, "0.85 setgray")
            _emit(output, f"{px} {py} {limb_radius_plot} 0 360 arc closepath fill")
            _emit(output, "0 setgray")
            _emit(output, f"{px} {py} {limb_radius_plot} 0 360 arc stroke")
        else:
            _emit(output, f"{px} {py} {_MOON_RADIUS_PT} 0 360 arc closepath fill")
            _write_string_safe(
                output, label, px + _MOON_RADIUS_PT + 2, py - _FONT_SIZE / 2, _FONT_SIZE
            )

    _emit(output, "restore")
    _emit(output, "showpage")
    _emit(output, "%%Trailer")
