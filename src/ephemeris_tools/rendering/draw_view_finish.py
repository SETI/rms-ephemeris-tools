"""Box, labels, stars, and close step for draw_planetary_view (split from impl)."""

from __future__ import annotations

from ephemeris_tools.rendering.draw_view_helpers import (
    _DEVICE,
    _STAR_FONTSIZE,
    _STAR_WIDTH,
    AXIS_LINE,
    FOV_PTS,
    STAR_LINE,
    _radrec,
    _rspk_annotate,
    _rspk_labels2,
)
from ephemeris_tools.rendering.escher import EscherState, EscherViewState, eslwid, eswrit
from ephemeris_tools.rendering.euclid import (
    STARFONT_PLUS,
    EuclidState,
    euclr,
    eustar,
    eutemp,
)


def draw_view_box_labels_stars_close(
    *,
    escher_state: EscherState,
    view_state: EscherViewState,
    euclid_state: EuclidState,
    cmat: list[list[float]],
    delta: float,
    moon_labelpts: float,
    body_names_list: list[str],
    body_los: list[list[float]],
    body_pts: list[float],
    use_diampts: float,
    fov: float,
    nbodies: int,
    nstars: int,
    star_ras: list[float],
    star_decs: list[float],
    star_names: list[str],
    star_labels: bool,
    star_diampts: float,
) -> None:
    """Draw box borders, axis labels, moon labels, stars, then euclr (port of RSPK_DrawView)."""
    eswrit('%Draw box...', escher_state)
    eutemp([-delta], [-delta], [-delta], [delta], 1, AXIS_LINE, view_state, escher_state)
    eutemp([-delta], [delta], [delta], [delta], 1, AXIS_LINE, view_state, escher_state)
    eutemp([delta], [delta], [delta], [-delta], 1, AXIS_LINE, view_state, escher_state)
    eutemp([delta], [-delta], [-delta], [-delta], 1, AXIS_LINE, view_state, escher_state)

    _rspk_labels2(cmat, delta, AXIS_LINE, view_state, escher_state)

    if moon_labelpts > 0.0:
        eswrit('%Label moons...', escher_state)
        for ibody in range(2, nbodies):
            bi = ibody
            bname = body_names_list[bi] if bi < len(body_names_list) else ''
            if not bname.strip():
                continue
            blos = body_los[bi] if bi < len(body_los) else [0.0, 0.0, 0.0]
            bpts = body_pts[bi] if bi < len(body_pts) else 0.0
            radius = max(bpts, use_diampts) * 0.5 * fov / FOV_PTS
            _rspk_annotate(
                bname.strip(),
                blos,
                radius,
                cmat,
                delta,
                view_state,
                escher_state,
            )

    if nstars > 0:
        eswrit('%Draw stars...', escher_state)
        eslwid(_STAR_WIDTH, escher_state)

    for i in range(nstars):
        sra = star_ras[i] if i < len(star_ras) else 0.0
        sdec = star_decs[i] if i < len(star_decs) else 0.0
        los = list(_radrec(1.0, sra, sdec))
        eustar(
            (los[0], los[1], los[2]),
            1,
            STARFONT_PLUS,
            _STAR_FONTSIZE,
            star_diampts / FOV_PTS,
            STAR_LINE,
            euclid_state,
            view_state,
            escher_state,
        )
        sname = star_names[i] if i < len(star_names) else ''
        if star_labels and sname.strip():
            _rspk_annotate(
                sname.strip(),
                los,
                0.0,
                cmat,
                delta,
                view_state,
                escher_state,
            )
    if nstars > 0:
        eslwid(0.0, escher_state)

    euclr(_DEVICE, 0.0, 1.0, 0.0, 1.0, escher_state)
