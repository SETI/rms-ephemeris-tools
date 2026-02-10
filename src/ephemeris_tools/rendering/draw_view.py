"""Planet viewer PostScript rendering (port of rspk_drawview)."""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import TextIO


def _generated_date_str() -> str:
    """Return current date as YYYY-MM-DD for Generated-by footer."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")

# Ring segment: (points in plot coords, line_type "lit"|"dark"|"shadowed", dashed, behind_planet).
RingSegment = tuple[list[tuple[float, float]], str, bool, bool]

# FOV circle diameter in points (7 inches * 72 pt/inch). Matches FORTRAN FOV_PTS.
FOV_PTS = 7.0 * 72.0  # 504.0

# Plot size and center (points). Matches FORTRAN: FOV circle diameter = FOV_PTS.
_VIEW_SIZE = FOV_PTS
_VIEW_CX = FOV_PTS / 2.0
_VIEW_CY = FOV_PTS / 2.0
_MOON_RADIUS_PT = 2.0
_FONT_SIZE = 10.0
_MARGIN_LEFT = 72.0
_MARGIN_BOTTOM = 180.0

# Font sizes used by FORTRAN viewer (Helvetica at 7, 8, 10, 12 pt).
_FONT_SIZES = (7, 8, 10, 12)

# Star symbol: + cross with 24 pt arm length (FORTRAN STAR_DIAMPTS).
_STAR_DIAMPTS = 24.0


def _emit(out: TextIO, s: str) -> None:
    out.write(s + "\n")


def _write_ps_header(
    out: TextIO,
    title: str = "Planetary Viewer",
    creator: str = "PDS Ring-Moon Systems Node",
) -> None:
    """Write PostScript header and prolog matching FORTRAN Escher (ESDR07) + rspk_drawview."""
    _emit(out, "%!PS-Adobe-2.0 EPSF-2.0")
    _emit(out, f"%%Title: {title}")
    _emit(out, f"%%Creator: {creator}")
    _emit(out, "%%BoundingBox: 0 0 612 792")
    _emit(out, "%%Pages: 1")
    _emit(out, "%%DocumentFonts: Helvetica")
    _emit(out, "%%EndComments")
    _emit(out, "%")
    _emit(out, "0.1 0.1 scale")
    _emit(out, "8 setlinewidth")
    _emit(out, "1 setlinecap")
    _emit(out, "1 setlinejoin")
    _emit(out, "/L {lineto} def")
    _emit(out, "/M {moveto} def")
    _emit(out, "/N {newpath} def")
    _emit(out, "/G {setgray} def")
    _emit(out, "/S {stroke} def")
    # Degree symbol macro (octal 260 = degree).
    _emit(out, "/degree { (\\260) show } def")
    # Label macro: x y (string) PutLab -> moveto show.
    _emit(out, "/PutLab { moveto show } def")
    for pt in _FONT_SIZES:
        _emit(out, f"/Helv{pt} /Helvetica findfont {pt} scalefont def")
    _emit(out, "%%EndProlog")
    _emit(out, "%")


def camera_matrix(
    center_ra_rad: float, center_dec_rad: float
) -> tuple[list[float], list[float], list[float]]:
    """Camera C-matrix columns in J2000 (port of RSPK_DrawView lines ~584-594).

    Z-axis (col3) = unit vector toward (center_ra, center_dec).
    Y-axis (col2) = projection of J2000 Z-pole onto plane perpendicular to Z.
    X-axis (col1) = Y cross Z (right-handed; left on plot = increasing RA).

    Returns:
        (col1, col2, col3) each a 3-vector.
    """
    # col3 = RADREC(1, center_ra, center_dec)
    cos_d = math.cos(center_dec_rad)
    col3 = [
        cos_d * math.cos(center_ra_rad),
        cos_d * math.sin(center_ra_rad),
        math.sin(center_dec_rad),
    ]
    # col2 = perpendicular projection of (0,0,1) onto plane perp to col3, then normalize
    temp = [0.0 - col3[0] * col3[2], 0.0 - col3[1] * col3[2], 1.0 - col3[2] * col3[2]]
    n2 = math.sqrt(temp[0] * temp[0] + temp[1] * temp[1] + temp[2] * temp[2])
    if n2 < 1e-12:
        col2 = [1.0, 0.0, 0.0]
    else:
        col2 = [temp[0] / n2, temp[1] / n2, temp[2] / n2]
    # col1 = col2 x col3
    col1 = [
        col2[1] * col3[2] - col2[2] * col3[1],
        col2[2] * col3[0] - col2[0] * col3[2],
        col2[0] * col3[1] - col2[1] * col3[0],
    ]
    return (col1, col2, col3)


def radec_to_plot(
    ra_rad: float,
    dec_rad: float,
    center_ra_rad: float,
    center_dec_rad: float,
    fov_rad: float,
) -> tuple[float, float]:
    """Convert (ra, dec) to plot (x, y) using camera matrix and FOV_PTS scale.

    Scale factor FOV_PTS / (2*tan(fov/2)) converts tangent-plane offsets to points.
    """
    col1, col2, col3 = camera_matrix(center_ra_rad, center_dec_rad)
    # Unit direction to (ra, dec) in J2000
    cos_d = math.cos(dec_rad)
    d = [cos_d * math.cos(ra_rad), cos_d * math.sin(ra_rad), math.sin(dec_rad)]
    x_cam = d[0] * col1[0] + d[1] * col1[1] + d[2] * col1[2]
    y_cam = d[0] * col2[0] + d[1] * col2[1] + d[2] * col2[2]
    z_cam = d[0] * col3[0] + d[1] * col3[1] + d[2] * col3[2]
    if z_cam <= 1e-12:
        return (0.0, 0.0)
    half = fov_rad / 2.0
    scale = FOV_PTS / (2.0 * math.tan(half))
    x_plot = scale * x_cam / z_cam
    y_plot = scale * y_cam / z_cam
    return (x_plot, y_plot)


def _write_string_safe(out: TextIO, text: str, x: float, y: float, size: float) -> None:
    """Draw text at (x, y), escaping parentheses for PostScript."""
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    _emit(out, f"/Helvetica findfont {size} scalefont setfont")
    _emit(out, f"{x} {y} moveto")
    _emit(out, f"({safe}) show")


def _draw_arcs_and_pericenters(
    out: TextIO,
    arcs_plot: list[list[tuple[float, float]]],
    pericenters_plot: list[tuple[float, float]],
    arc_width_pts: float,
) -> None:
    """Draw ring arcs (heavier line) and pericenter markers (filled circles)."""
    _emit(out, "0 setgray")
    for points in arcs_plot:
        if len(points) >= 2:
            _emit(out, f"{arc_width_pts} setlinewidth")
            _emit(out, f"{_VIEW_CX + points[0][0]} {_VIEW_CY + points[0][1]} moveto")
            for x, y in points[1:]:
                _emit(out, f"{_VIEW_CX + x} {_VIEW_CY + y} lineto")
            _emit(out, "stroke")
    for px, py in pericenters_plot:
        r = arc_width_pts / 2.0
        _emit(out, f"{_VIEW_CX + px} {_VIEW_CY + py} {r} 0 360 arc closepath fill")
    _emit(out, "1 setlinewidth")


def _draw_ring_segments(
    out: TextIO,
    ring_segments: list[RingSegment],
    ring_method: int,
) -> None:
    """Draw ring segments with lit/dark/shadowed style and opacity mode (0/1/2)."""
    for points, line_type, dashed, behind_planet in ring_segments:
        if ring_method == 2 and behind_planet:
            continue
        if ring_method == 1 and behind_planet:
            _emit(out, "0.85 setgray")
        elif line_type == "dark" or line_type == "shadowed":
            _emit(out, "0.85 setgray")
        else:
            _emit(out, "0 setgray")
        if dashed:
            _emit(out, "[4 4] 0 setdash")
        if len(points) >= 2:
            _emit(out, f"{_VIEW_CX + points[0][0]} {_VIEW_CY + points[0][1]} moveto")
            for x, y in points[1:]:
                _emit(out, f"{_VIEW_CX + x} {_VIEW_CY + y} lineto")
            _emit(out, "stroke")
        if dashed:
            _emit(out, "[] 0 setdash")
        _emit(out, "0 setgray")


def draw_planetary_view(
    output: TextIO,
    planet_name: str,
    limb_radius_plot: float,
    bodies_plot: list[tuple[float, float, str, bool]],
    title: str,
    planet_grid_segments: list[tuple[list[tuple[float, float]], str]] | None = None,
    ring_segments: list[RingSegment] | None = None,
    ring_method: int = 0,
    arcs_plot: list[list[tuple[float, float]]] | None = None,
    pericenters_plot: list[tuple[float, float]] | None = None,
    arc_width_pts: float = 4.0,
    ra_dec_tick_marks: list[tuple[float, float, float, float]] | None = None,
    ra_dec_tick_labels: list[tuple[float, float, str]] | None = None,
    caption_lines: list[tuple[str, str]] | None = None,
    show_compass: bool = True,
    stars_plot: list[tuple[float, float, str]] | None = None,
    star_diam_pts: float = _STAR_DIAMPTS,
    star_labels: bool = False,
    moon_diam_pts: float = _MOON_RADIUS_PT * 2.0,
    blank_disks: bool = False,
    limb_ellipse_plot: tuple[float, float, float, float] | None = None,
) -> None:
    """Generate PostScript diagram of planet and moons in field of view.

    bodies_plot: list of (x, y, label, is_planet) in plot coordinates (origin
    at center of field). When planet_grid_segments is provided (FORTRAN
    blank_disks=False), the planet is drawn with latitude/longitude lines at
    15° spacing: lit=black, dark=light gray, terminator=black. Otherwise the
    planet is a shaded disk. Moons are small circles with labels.

    ring_segments: optional list of (points, line_type, dashed, behind_planet).
    ring_method: 0=transparent, 1=semi (behind planet gray), 2=opaque (omit behind).
    arcs_plot: optional list of arc polylines in plot coords.
    pericenters_plot: optional list of (x,y) pericenter positions.
    arc_width_pts: line width for arcs and diameter for pericenter markers (points).
    ra_dec_tick_marks: optional list of (x1,y1,x2,y2) in plot coords for tick lines.
    ra_dec_tick_labels: optional list of (x_plot, y_plot, label_str) for tick labels.
    caption_lines: optional list of (left_label, right_value) for caption block below FOV.
    show_compass: if True, draw N and E orientation labels at top and left of FOV.
    stars_plot: optional list of (x, y, name) in plot coords for star/other-body markers.
    star_diam_pts: size of + cross arms for stars (points).
    star_labels: if True, draw star/body names next to markers.
    moon_diam_pts: minimum diameter in points for moon disks (unresolved moons stay visible).
    blank_disks: if True, draw planet and moons as white-filled circles (no grid/lines).
    limb_ellipse_plot: optional (maj_x, maj_y, min_x, min_y) semi-axis vectors for triaxial limb.
    """
    _write_ps_header(
        output,
        title=f"{planet_name} Viewer",
        creator=f"{planet_name} Viewer, PDS Ring-Moon Systems Node",
    )
    _emit(output, "save")
    _emit(output, "/inch {72 mul} def")
    _emit(output, "1 inch 2.5 inch translate")
    _emit(output, "0 setlinejoin 1 setlinecap")
    _emit(output, "0 setgray")
    _emit(output, "1 setlinewidth")

    # Title above view box (y = view size + 16 pt).
    _write_string_safe(output, title, 0, _VIEW_SIZE + 16, _FONT_SIZE + 2)

    # View box and FOV circle (radius FOV_PTS/2).
    w = _VIEW_SIZE
    _emit(output, f"0 0 moveto {w} 0 rlineto 0 {w} rlineto {-w} 0 rlineto closepath stroke")
    _emit(output, f"{_VIEW_CX} {_VIEW_CY} {FOV_PTS/2.0} 0 360 arc stroke")

    if ra_dec_tick_marks:
        for x1, y1, x2, y2 in ra_dec_tick_marks:
            _emit(output, f"{_VIEW_CX + x1} {_VIEW_CY + y1} moveto {_VIEW_CX + x2} {_VIEW_CY + y2} lineto stroke")
    if ra_dec_tick_labels:
        _emit(output, "/Helv8 /Helvetica findfont 8 scalefont setfont")
        for x_plot, y_plot, label_str in ra_dec_tick_labels:
            _write_string_safe(output, label_str, _VIEW_CX + x_plot, _VIEW_CY + y_plot, 8.0)

    if show_compass:
        r = FOV_PTS / 2.0
        _write_string_safe(output, "N", _VIEW_CX - 3, _VIEW_CY + r + 8, 10.0)
        _write_string_safe(output, "E", _VIEW_CX - r - 20, _VIEW_CY - 4, 10.0)

    if caption_lines:
        y_cap = -20.0
        for left_label, right_value in caption_lines:
            _write_string_safe(output, left_label, 0, y_cap, 8.0)
            _write_string_safe(output, right_value, 200, y_cap, 8.0)
            y_cap -= 12.0

    if ring_segments:
        _draw_ring_segments(output, ring_segments, ring_method)

    if arcs_plot or pericenters_plot:
        _draw_arcs_and_pericenters(
            output,
            arcs_plot or [],
            pericenters_plot or [],
            arc_width_pts,
        )

    half_arm = star_diam_pts / 2.0
    for sx, sy, sname in stars_plot or []:
        px = _VIEW_CX + sx
        py = _VIEW_CY + sy
        _emit(output, "0 setgray")
        _emit(output, f"{px - half_arm} {py} moveto {px + half_arm} {py} lineto stroke")
        _emit(output, f"{px} {py - half_arm} moveto {px} {py + half_arm} lineto stroke")
        if star_labels and sname:
            _write_string_safe(output, sname, px + half_arm + 2, py - _FONT_SIZE / 2, _FONT_SIZE)

    def _draw_limb(ox: float, oy: float, fill: bool) -> None:
        if limb_ellipse_plot is not None:
            maj_x, maj_y, min_x, min_y = limb_ellipse_plot
            _emit(output, "gsave")
            _emit(output, f"{ox} {oy} translate")
            _emit(output, f"{maj_x} {maj_y} {min_x} {min_y} 0 0 concat")
            _emit(output, "0 0 1 0 360 arc")
            if fill:
                _emit(output, "closepath fill")
            _emit(output, "stroke")
            _emit(output, "grestore")
        else:
            r_plot = limb_radius_plot
            if fill:
                _emit(output, f"{ox} {oy} {r_plot} 0 360 arc closepath fill")
            _emit(output, f"{ox} {oy} {r_plot} 0 360 arc stroke")

    moon_radius_pt = max(_MOON_RADIUS_PT, moon_diam_pts / 2.0)
    for x, y, label, is_planet in bodies_plot:
        px = _VIEW_CX + x
        py = _VIEW_CY + y
        if is_planet:
            r_plot = limb_radius_plot
            if blank_disks:
                _emit(output, "1 setgray")
                _draw_limb(px, py, fill=True)
                _emit(output, "0 setgray")
            elif planet_grid_segments is not None:
                _emit(output, "0 setgray")
                _draw_limb(px, py, fill=False)
                for points, line_type in planet_grid_segments:
                    if len(points) < 2:
                        continue
                    if line_type == "dark":
                        _emit(output, "0.85 setgray")
                    else:
                        _emit(output, "0 setgray")
                    _emit(output, f"{_VIEW_CX + points[0][0]} {_VIEW_CY + points[0][1]} moveto")
                    for qx, qy in points[1:]:
                        _emit(output, f"{_VIEW_CX + qx} {_VIEW_CY + qy} lineto")
                    _emit(output, "stroke")
                _emit(output, "0 setgray")
            else:
                _emit(output, "0.85 setgray")
                _draw_limb(px, py, fill=True)
                _emit(output, "0 setgray")
        else:
            r_moon = moon_radius_pt
            if blank_disks:
                _emit(output, "1 setgray")
                _emit(output, f"{px} {py} {r_moon} 0 360 arc closepath fill")
                _emit(output, "0 setgray")
                _emit(output, f"{px} {py} {r_moon} 0 360 arc stroke")
            else:
                _emit(output, f"{px} {py} {r_moon} 0 360 arc closepath fill")
            _write_string_safe(
                output, label, px + r_moon + 2, py - _FONT_SIZE / 2, _FONT_SIZE
            )

    _emit(output, "0 setgray")
    _write_string_safe(
        output,
        "Generated by RMS Node on " + _generated_date_str(),
        72,
        -70.0,
        8.0,
    )
    _emit(output, "restore")
    _emit(output, "showpage")
    _emit(output, "%%Trailer")
    _emit(output, "%%EOF")
