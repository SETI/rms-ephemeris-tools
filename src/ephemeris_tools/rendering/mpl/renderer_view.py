"""Matplotlib renderer for the planet viewer (draw_planetary_view_mpl).

Produces PNG/PDF/SVG/PS output via matplotlib savefig.  Reuses the same SPICE
geometry pipeline as draw_planetary_view but replaces the Escher/PostScript
device layer with MplCanvas and draws ornaments natively with matplotlib.

Layout is freely redesigned (not a pixel-for-pixel replica of the PS output).
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import cspyce

from ephemeris_tools.rendering.draw_view_helpers import (
    HALFPI,
    LIT_LINE,
    LOOP_DLON,
    LOOP_WIDTH,
    MAX_NLOOPS,
    MAX_NMOONS,
    MAX_NRINGS,
    MOON_LATS,
    MOON_MERIDS,
    PLANET_LATS,
    PLANET_MERIDS,
    RING_THICKNESS,
    SUN_ID,
    TWOPI,
    _opsgnd,
    _vhat,
    _vnorm,
    _vrotv,
    camera_matrix,
)
from ephemeris_tools.rendering.draw_view_impl import DrawPlanetaryViewOptions
from ephemeris_tools.rendering.escher import EscherState, EscherViewState
from ephemeris_tools.rendering.euclid import (
    EuclidState,
    STARFONT_PLUS,
    eubody,
    eugeom,
    euinit,
    euring,
    eustar,
    euview,
)
from ephemeris_tools.rendering.mpl.canvas import MplCanvas
from ephemeris_tools.rendering.mpl.theme import apply_theme, figure_and_axes, infer_format
from ephemeris_tools.spice.bodmat import bodmat
from ephemeris_tools.spice.common import get_state
from ephemeris_tools.spice.observer import observer_state
from ephemeris_tools.spice.shifts import spkapp_shifted

if TYPE_CHECKING:
    import matplotlib.axes
    import matplotlib.figure

# Color code constants matching the PS renderer
_LIT = LIT_LINE
_DARK = 8   # 0.8 gray for dark regions
_TERM = 5   # 0.5 gray for terminator
_STAR_FNTSIZE = 2
_STAR_FNTSCL = 0.012

# Device / viewport constants (same page region as PS renderer, only used for
# euview which needs them to set up euclid_state geometry).
_DEVICE = 7
_H1, _H2 = 0.066666667, 1.0
_V1, _V2 = 0.988888889, 0.055555556

# Tick length in FOV units (fraction of half-FOV)
_TICK_MAJOR = 0.04
_TICK_MINOR = 0.02


def draw_planetary_view_mpl(
    output_path: str,
    options: DrawPlanetaryViewOptions,
    dpi: int = 150,
) -> None:
    """Render a planetary scene to an image file using matplotlib.

    Supports PNG, PDF, SVG, PS/EPS output; format is inferred from *output_path*
    extension (defaults to PNG for unrecognised extensions).

    Parameters:
        output_path: Path to the output image file.
        options: Geometry and display options (same as draw_planetary_view).
        dpi: Dots per inch for raster outputs (PNG/TIFF).
    """
    apply_theme()

    if not (0 < options.fov < math.pi):
        raise ValueError(f'options.fov must be in (0, pi), got {options.fov!r}')
    delta = math.tan(options.fov / 2.0)

    # ------------------------------------------------------------------
    # Camera / projection setup
    # Initialise euclid_state via euview using a dummy Escher pair (no PS).
    # ------------------------------------------------------------------
    euclid_state = EuclidState()
    euinit(euclid_state)

    view_state = EscherViewState()
    escher_state = EscherState()

    euview(
        _DEVICE, _H1, _H2, _V1, _V2,
        -delta, delta, -delta, delta,
        euclid_state, view_state, escher_state,
    )

    # ------------------------------------------------------------------
    # SPICE geometry
    # ------------------------------------------------------------------
    spice_state = get_state()
    planet_id = spice_state.planet_id
    planet_num = spice_state.planet_num

    obs_pv = list(observer_state(options.obs_time))

    _planet_pv, planet_dt = cspyce.spkapp(planet_id, options.obs_time, 'J2000', obs_pv[:6], 'LT')
    planet_dpv = list(_planet_pv)
    planet_time = options.obs_time - planet_dt
    planet_pv = list(cspyce.spkssb(planet_id, planet_time, 'J2000'))

    planet_mat = bodmat(planet_id, planet_time)

    sun_pv, _sun_dt = cspyce.spkapp(SUN_ID, planet_time, 'J2000', planet_pv[:6], 'LT+S')
    sun_dpv = list(sun_pv)
    sun_loc = [planet_pv[i] + sun_dpv[i] for i in range(3)]
    sun_radii_arr = cspyce.bodvar(SUN_ID, 'RADII')
    sun_rad = float(sun_radii_arr[0])

    cmat = camera_matrix(options.center_ra, options.center_dec)

    # ------------------------------------------------------------------
    # Build body list (same logic as draw_view_impl.py)
    # ------------------------------------------------------------------
    moon_flags = list(options.moon_flags)
    moon_ids = list(options.moon_ids)
    moon_names = list(options.moon_names)

    nbodies = 0
    body_locs: list[list[float]] = []
    body_axes: list[list[list[float]]] = []
    body_merids: list[int] = []
    body_lats: list[int] = []
    body_los: list[list[float]] = []
    body_names_disp: list[str] = []

    # Body 1: Planet
    planet_loc = [obs_pv[i] + planet_dpv[i] for i in range(3)]
    p_radii_arr = cspyce.bodvar(planet_id, 'RADII')
    planet_axes_scaled = [
        [planet_mat[i][j] * p_radii_arr[i] for j in range(3)] for i in range(3)
    ]
    body_locs.append(planet_loc)
    body_axes.append(planet_axes_scaled)
    body_merids.append(PLANET_MERIDS if not options.blank_disks else 0)
    body_lats.append(PLANET_LATS if not options.blank_disks else 0)
    body_los.append(planet_dpv[:3])
    body_names_disp.append('')
    nbodies += 1

    # Body 2: Dummy body along optic axis
    dummy_axes = [_vhat(planet_axes_scaled[i]) for i in range(3)]
    tempvec = planet_dpv[:3]
    tdist = _vnorm(tempvec)
    optic_vec = [2.0 * tdist * cmat[j][2] for j in range(3)]
    dummy_loc = [obs_pv[i] + optic_vec[i] for i in range(3)]
    body_locs.append(dummy_loc)
    body_axes.append(dummy_axes)
    body_merids.append(0)
    body_lats.append(0)
    body_los.append([0.0, 0.0, 0.0])
    body_names_disp.append('')
    nbodies += 1

    # Moon label list for ornaments
    moon_label_data: list[tuple[str, float, float]] = []  # (name, x, y)

    # Bodies 3+: Moons
    use_nmoons = min(options.nmoons, MAX_NMOONS)
    for imoon in range(use_nmoons):
        if imoon >= len(moon_flags) or not moon_flags[imoon]:
            continue
        if imoon >= len(moon_ids):
            continue
        mid = moon_ids[imoon]
        try:
            moon_pv, mdt = spkapp_shifted(mid, options.obs_time, 'J2000', obs_pv[:6], 'LT')
        except Exception:
            continue
        moon_dpv = list(moon_pv)
        moon_loc = [obs_pv[i] + moon_dpv[i] for i in range(3)]
        body_locs.append(moon_loc)
        body_los.append(list(moon_dpv[:3]))
        try:
            if cspyce.bodfnd(mid, 'POLE_RA'):
                moon_rot = bodmat(mid, options.obs_time - mdt)
                moon_mat = [list(row) for row in moon_rot]
            else:
                moon_mat = [list(row) for row in planet_mat]
        except Exception:
            moon_mat = [list(row) for row in planet_mat]
        try:
            m_radii_arr = list(cspyce.bodvar(mid, 'RADII'))
        except Exception:
            m_radii_arr = [1.0, 1.0, 1.0]
        moon_axes = [[moon_mat[i][j] * m_radii_arr[i] for j in range(3)] for i in range(3)]
        body_axes.append(moon_axes)
        body_merids.append(MOON_MERIDS if not options.blank_disks else 0)
        body_lats.append(MOON_LATS if not options.blank_disks else 0)
        mname = moon_names[imoon] if imoon < len(moon_names) else ''
        body_names_disp.append(mname)

        # Projected moon position for labelling
        cam = list(cspyce.mtxv(cmat, moon_dpv[:3]))
        if cam[2] > 0:
            mx = -cam[0] / cam[2]
            my = -cam[1] / cam[2]
            if abs(mx) < delta and abs(my) < delta and mname.strip():
                moon_label_data.append((mname.strip().upper(), mx, my))

        nbodies += 1

    # ------------------------------------------------------------------
    # Ring geometry (same logic as draw_view_impl.py)
    # ------------------------------------------------------------------
    ring_flags = list(options.ring_flags)
    ring_rads = list(options.ring_rads)
    ring_elevs = list(options.ring_elevs)
    ring_eccs = list(options.ring_eccs)
    ring_incs = list(options.ring_incs)
    ring_peris = list(options.ring_peris)
    ring_nodes = list(options.ring_nodes)
    ring_offsets = list(options.ring_offsets)
    ring_opaqs = list(options.ring_opaqs)
    ring_dashed = list(options.ring_dashed)

    use_nrings = min(options.nrings, MAX_NRINGS)
    _def_f, _def_0, _def_03 = False, 0.0, [0.0, 0.0, 0.0]
    while len(ring_flags) < use_nrings:
        ring_flags.append(_def_f)
    while len(ring_rads) < use_nrings:
        ring_rads.append(_def_0)
    while len(ring_eccs) < use_nrings:
        ring_eccs.append(_def_0)
    while len(ring_nodes) < use_nrings:
        ring_nodes.append(_def_0)
    while len(ring_incs) < use_nrings:
        ring_incs.append(_def_0)
    while len(ring_peris) < use_nrings:
        ring_peris.append(_def_0)
    while len(ring_elevs) < use_nrings:
        ring_elevs.append(_def_0)
    while len(ring_offsets) < use_nrings:
        ring_offsets.append(_def_03)
    while len(ring_opaqs) < use_nrings:
        ring_opaqs.append(_def_f)
    while len(ring_dashed) < use_nrings:
        ring_dashed.append(_def_f)

    pole = _vhat(planet_axes_scaled[2])
    if planet_num == 7:
        pole = [-pole[0], -pole[1], -pole[2]]
    j2000_z = [0.0, 0.0, 1.0]
    ascnode = [
        j2000_z[1] * pole[2] - j2000_z[2] * pole[1],
        j2000_z[2] * pole[0] - j2000_z[0] * pole[2],
        j2000_z[0] * pole[1] - j2000_z[1] * pole[0],
    ]
    offset = [planet_dt * planet_pv[3 + i] for i in range(3)]

    r_ring_locs: list[list[float]] = []
    r_ring_axes1: list[list[float]] = []
    r_ring_axes2: list[list[float]] = []
    r_ring_axes3: list[list[float]] = []
    r_ring_dark: list[bool] = []

    nloops = 0
    loop_locs: list[list[float]] = []
    loop_axes1: list[list[float]] = []
    loop_axes2: list[list[float]] = []
    loop_ring: list[int] = []

    arc_flags = list(options.arc_flags)
    arc_rings = list(options.arc_rings)
    arc_minlons = list(options.arc_minlons)
    arc_maxlons = list(options.arc_maxlons)
    use_narcs = min(
        options.narcs,
        len(arc_rings), len(arc_flags), len(arc_minlons), len(arc_maxlons),
    )

    for iring in range(use_nrings):
        if not ring_flags[iring]:
            r_ring_locs.append([0.0, 0.0, 0.0])
            r_ring_axes1.append([0.0, 0.0, 0.0])
            r_ring_axes2.append([0.0, 0.0, 0.0])
            r_ring_axes3.append([0.0, 0.0, 0.0])
            r_ring_dark.append(False)
            continue

        rad = ring_rads[iring]
        ecc = ring_eccs[iring]
        rn = ring_nodes[iring]
        ri = ring_incs[iring]
        ringnode = _vrotv(ascnode, pole, rn)
        ringpole = _vhat(_vrotv(pole, ringnode, ri))
        ring_ax3 = [RING_THICKNESS * ringpole[i] for i in range(3)]
        r_ring_axes3.append(ring_ax3)
        rp = ring_peris[iring]
        peri = _vhat(_vrotv(ringnode, ringpole, rp - rn))
        ring_ax1 = [rad * peri[i] for i in range(3)]
        r_ring_axes1.append(ring_ax1)
        minor_dir = _vrotv(peri, ringpole, HALFPI)
        ring_ax2 = [rad * math.sqrt(1.0 - ecc * ecc) * minor_dir[i] for i in range(3)]
        r_ring_axes2.append(ring_ax2)
        ring_loc = [-ecc * ring_ax1[i] + planet_loc[i] for i in range(3)]
        re = ring_elevs[iring]
        ring_loc = [ring_loc[i] + re * pole[i] for i in range(3)]
        if iring < len(ring_offsets):
            ro = ring_offsets[iring]
            ring_loc = [ring_loc[i] + ro[i] for i in range(3)]
        r_ring_locs.append(ring_loc)

        tempvec_obs = [ring_loc[i] - obs_pv[i] + offset[i] for i in range(3)]
        dot1 = -(ringpole[0]*tempvec_obs[0] + ringpole[1]*tempvec_obs[1] + ringpole[2]*tempvec_obs[2])
        sun_hat = _vhat(sun_dpv[:3])
        dot2 = ringpole[0]*sun_hat[0] + ringpole[1]*sun_hat[1] + ringpole[2]*sun_hat[2]
        is_dashed = ring_dashed[iring]
        if is_dashed:
            r_ring_dark.append(False)
        else:
            sun_dist_val = _vnorm(sun_dpv[:3])
            sun_angular = sun_rad / sun_dist_val if sun_dist_val > 0 else 0
            r_ring_dark.append(_opsgnd(dot1, dot2) and abs(dot2) > sun_angular)

        for iarc in range(use_narcs):
            if arc_rings[iarc] != iring + 1 or not arc_flags[iarc]:
                continue
            lon1 = arc_minlons[iarc] - rp
            lon2 = arc_maxlons[iarc] - rp
            if lon2 < lon1:
                lon2 += TWOPI
            nsteps = max(int((lon2 - lon1) / LOOP_DLON), 1)
            dlon = (lon2 - lon1) / nsteps
            lon = lon1 - dlon
            for _ in range(nsteps):
                lon += dlon
                if nloops >= MAX_NLOOPS:
                    break
                nloops += 1
                vec1 = [math.cos(lon)*ring_ax1[i] + math.sin(lon)*ring_ax2[i] for i in range(3)]
                vec2 = [math.cos(lon+dlon)*ring_ax1[i] + math.sin(lon+dlon)*ring_ax2[i]
                        for i in range(3)]
                tmid = [0.5*vec1[i] + 0.5*vec2[i] for i in range(3)]
                la1 = [vec1[i] - tmid[i] for i in range(3)]
                la2 = [LOOP_WIDTH * v for v in _vhat(tmid)]
                ll = [tmid[i] + ring_loc[i] for i in range(3)]
                loop_axes1.append(la1)
                loop_axes2.append(la2)
                loop_locs.append(ll)
                loop_ring.append(iring + 1)

    # ------------------------------------------------------------------
    # Create MplCanvas and render 3D scene
    # ------------------------------------------------------------------
    canvas = MplCanvas(xmin=-delta, xmax=delta, ymin=-delta, ymax=delta)

    eugeom(
        1, [sun_loc], [sun_rad],
        obs_pv[:3],
        [cmat[0], cmat[1], cmat[2]],
        nbodies, body_locs, body_axes,
        euclid_state,
    )

    term_color = _DARK if not options.blank_disks else _LIT

    # Draw planet (body 1) and dummy body (body 2)
    eubody(1, body_merids[0], body_lats[0], 1, _LIT, _DARK, term_color, euclid_state, canvas)
    eubody(2, 0, 0, 1, 0, 0, 0, euclid_state, canvas)

    # Draw moons (bodies 3+)
    for ibody in range(3, nbodies + 1):
        bi = ibody - 1
        eubody(ibody, body_merids[bi], body_lats[bi], 1, _LIT, _DARK, term_color,
               euclid_state, canvas)

    # Draw rings
    for iring in range(use_nrings):
        if not ring_flags[iring]:
            continue
        lit = _LIT
        dark = 6  # slightly dark for ring underside
        if r_ring_dark[iring]:
            lit, dark = dark, dark
        is_dash = ring_dashed[iring] if iring < len(ring_dashed) else False
        if is_dash:
            canvas.set_dashed(True)
        euring(r_ring_locs[iring], r_ring_axes1[iring], r_ring_axes2[iring],
               1, lit, dark, euclid_state, canvas)
        if is_dash:
            canvas.set_dashed(False)

    # Draw arc loops
    for iloop in range(nloops):
        iring = loop_ring[iloop] - 1
        lit = _LIT
        dark = 6
        if iring < len(r_ring_dark) and r_ring_dark[iring]:
            lit, dark = dark, dark
        euring(loop_locs[iloop], loop_axes1[iloop], loop_axes2[iloop],
               1, lit, dark, euclid_state, canvas)

    # Draw stars
    star_ras = list(options.star_ras)
    star_decs = list(options.star_decs)
    star_names = list(options.star_names)
    for i in range(options.nstars):
        sra = star_ras[i] if i < len(star_ras) else 0.0
        sdec = star_decs[i] if i < len(star_decs) else 0.0
        los = list(cspyce.radrec(1.0, sra, sdec))
        eustar(
            (los[0], los[1], los[2]),
            1, STARFONT_PLUS, 2, _STAR_FNTSCL, 1,
            euclid_state, canvas,
        )

    # ------------------------------------------------------------------
    # Build matplotlib figure
    # ------------------------------------------------------------------
    fig, ax = figure_and_axes(
        fig_width_in=8.0,
        fig_height_in=8.5,
        left=0.14, right=0.91, top=0.88, bottom=0.16,
    )

    canvas.finalize(ax)

    # Draw border box
    ax.set_aspect('equal', adjustable='box')
    for spine in ax.spines.values():
        spine.set_linewidth(1.0)
        spine.set_color('black')

    # RA/Dec axis ticks (simple: 5 ticks per side)
    _add_radec_ticks(ax, cmat, delta, options.fov)

    # Moon labels with bucket-based collision avoidance
    if options.moon_labelpts > 0.0:
        _add_moon_labels(ax, fig, moon_label_data, delta, options.moon_labelpts)

    # Star labels
    if options.star_labels:
        for i in range(options.nstars):
            sra_i = star_ras[i] if i < len(star_ras) else 0.0
            sdec_i = star_decs[i] if i < len(star_decs) else 0.0
            sname = star_names[i] if i < len(star_names) else ''
            if not sname.strip():
                continue
            cam_s = list(cspyce.mtxv(cmat, list(cspyce.radrec(1.0, sra_i, sdec_i))))
            if cam_s[2] > 0:
                sx = -cam_s[0] / cam_s[2]
                sy = -cam_s[1] / cam_s[2]
                if abs(sx) < delta and abs(sy) < delta:
                    ax.annotate(
                        sname.strip(),
                        xy=(sx, sy), xytext=(4, -4),
                        textcoords='offset points', fontsize=7,
                        clip_on=False,
                    )

    # Title
    if options.title and options.title.strip():
        fig.suptitle(options.title.strip(), fontsize=11, y=0.97)

    # Captions (below axes inside the figure)
    _add_captions(fig, ax, options)

    # Footer (very bottom of figure)
    from datetime import datetime  # noqa: PLC0415
    planetstr = spice_state.planet_name if hasattr(spice_state, 'planet_name') else 'Planet'
    fdate = datetime.now().strftime('%Y-%m-%d %H:%M')
    fig.text(
        0.01, 0.005,
        f'Generated by the {planetstr} Viewer, PDS Ring-Moon Systems Node, {fdate}',
        ha='left', va='bottom', fontsize=6, color='#666666',
    )

    # Save
    fmt = infer_format(output_path)
    fig.savefig(output_path, format=fmt, dpi=dpi)

    import matplotlib.pyplot as plt  # noqa: PLC0415
    plt.close(fig)


def _add_radec_ticks(
    ax: 'matplotlib.axes.Axes',
    cmat: list[list[float]],
    delta: float,
    fov_rad: float,
) -> None:
    """Draw RA and Dec tick marks on the FOV axes using matplotlib.

    Uses the existing _STEP1/_STEP2 logic from draw_view_helpers for tick spacing.
    """
    import math  # noqa: PLC0415

    import cspyce  # noqa: PLC0415

    from ephemeris_tools.rendering.draw_view_helpers import (  # noqa: PLC0415
        _STEP1,
        _SUBSTEPS,
        _NCHOICES,
        _MINSTEPS,
        _TICKSIZE1,
        _TICKSIZE2,
        _fortran_data_real,
        _fortran_nint,
    )

    DPR = 180.0 / math.pi

    _, ra, dec = cspyce.recrad((cmat[0][2], cmat[1][2], cmat[2][2]))
    cos_dec = math.cos(dec)
    delta_ra = delta / cos_dec if abs(cos_dec) > 1e-12 else delta
    dtick1 = _TICKSIZE1 * delta
    dtick2 = _TICKSIZE2 * delta

    spr = DPR * 3600.0 / 15.0
    sdelta_ra = delta_ra * spr
    i = _NCHOICES
    while i >= 2:
        if 2.0 * sdelta_ra >= _MINSTEPS * _fortran_data_real(_STEP1[i]):
            break
        i -= 1
    nsubs_ra = _SUBSTEPS[i]
    ds_ra = _fortran_data_real(_STEP1[i]) / nsubs_ra
    ra_sec = ra * spr
    k1_ra = _fortran_nint((ra_sec - sdelta_ra) / ds_ra + 0.5)
    k2_ra = _fortran_nint((ra_sec + sdelta_ra) / ds_ra - 0.5)

    tick_lines_x = []
    tick_lines_y = []
    for k in range(k1_ra, k2_ra + 1):
        s = k * ds_ra
        ismajor = (k % nsubs_ra) == 0
        length = dtick1 if ismajor else dtick2
        j2000 = cspyce.radrec(1.0, s / spr, dec)
        cam = list(cspyce.mtxv(cmat, j2000))
        if cam[2] <= 0:
            continue
        x = -cam[0] / cam[2]
        if abs(x) <= delta:
            # Top tick
            tick_lines_x.append([x, x])
            tick_lines_y.append([delta - length, delta])
            # Bottom tick
            tick_lines_x.append([x, x])
            tick_lines_y.append([-delta + length, -delta])
            if ismajor:
                total_h = s / (DPR * 3600.0 / 15.0) * (180.0 / math.pi) / 15.0
                h = int(total_h)
                m = int((total_h - h) * 60)
                label = f'{h:02d}h{m:02d}m'
                # Bottom label
                ax.text(
                    x, -delta - dtick2 * 1.5,
                    label,
                    ha='center', va='top', fontsize=9,
                    clip_on=False,
                )
                # Top label (mirror)
                ax.text(
                    x, delta + dtick2 * 1.5,
                    label,
                    ha='center', va='bottom', fontsize=9,
                    clip_on=False,
                )

    spr_dec = DPR * 3600.0
    sdelta_dec = delta * spr_dec
    i = _NCHOICES
    while i >= 2:
        if 2.0 * sdelta_dec >= _MINSTEPS * _fortran_data_real(_STEP1[i]):
            break
        i -= 1
    nsubs_dec = _SUBSTEPS[i]
    ds_dec = _fortran_data_real(_STEP1[i]) / nsubs_dec
    dec_sec = dec * spr_dec
    k1_dec = _fortran_nint((dec_sec - sdelta_dec) / ds_dec + 0.5)
    k2_dec = _fortran_nint((dec_sec + sdelta_dec) / ds_dec - 0.5)

    for k in range(k1_dec, k2_dec + 1):
        s = k * ds_dec
        ismajor = (k % nsubs_dec) == 0
        length = dtick1 if ismajor else dtick2
        j2000 = cspyce.radrec(1.0, ra, s / spr_dec)
        cam = list(cspyce.mtxv(cmat, j2000))
        if cam[2] <= 0:
            continue
        y = -cam[1] / cam[2]
        if abs(y) <= delta:
            # Left tick (data x=delta = LEFT screen edge due to x-axis inversion)
            tick_lines_x.append([delta - length, delta])
            tick_lines_y.append([y, y])
            # Right tick (data x=-delta = RIGHT screen edge)
            tick_lines_x.append([-delta + length, -delta])
            tick_lines_y.append([y, y])
            if ismajor:
                deg_val = s / spr_dec * 180.0 / math.pi
                label = f'{deg_val:.1f}\u00b0'
                # Right margin label.
                ax.text(
                    -delta - dtick2 * 2, y,
                    label,
                    ha='left', va='center', fontsize=9,
                    clip_on=False,
                )
                # Left margin label (mirror).
                ax.text(
                    delta + dtick2 * 2, y,
                    label,
                    ha='right', va='center', fontsize=9,
                    clip_on=False,
                )

    # Draw all tick lines at once
    from matplotlib.collections import LineCollection  # noqa: PLC0415
    segs = [[[tick_lines_x[i][0], tick_lines_y[i][0]],
              [tick_lines_x[i][1], tick_lines_y[i][1]]]
             for i in range(len(tick_lines_x))]
    if segs:
        lc = LineCollection(segs, colors='black', linewidths=0.8)
        ax.add_collection(lc)

    ax.set_xlabel('Right Ascension \u2192 East', fontsize=9, labelpad=14)
    # Declination label on the LEFT (standard position); labelpad must clear
    # the custom left tick labels placed via ax.text() above.
    ax.set_ylabel('Declination \u2192 North', fontsize=9, labelpad=40)
    ax.yaxis.set_label_position('left')
    ax.tick_params(labelbottom=False, labelleft=False, bottom=False, left=False,
                   top=False, right=False)


def _add_captions(
    fig: 'matplotlib.figure.Figure',
    ax: 'matplotlib.axes.Axes',
    options: DrawPlanetaryViewOptions,
) -> None:
    """Add caption key-value lines below the axes inside the figure."""
    lcaptions = list(options.lcaptions) if options.lcaptions else []
    rcaptions = list(options.rcaptions) if options.rcaptions else []
    ncaptions = options.ncaptions

    if ncaptions <= 0 or not lcaptions:
        return

    # Place captions below the axes, with room for tick labels and xlabel above them.
    # Reserve ~0.07 of figure height for tick labels + xlabel, then start captions.
    ax_pos = ax.get_position()
    y_start = ax_pos.y0 - 0.075
    line_h = 0.026
    for i in range(min(ncaptions, len(lcaptions))):
        y = y_start - i * line_h
        if y < 0.015:
            break
        lc = lcaptions[i] if i < len(lcaptions) else ''
        rc = rcaptions[i] if i < len(rcaptions) else ''
        fig.text(ax_pos.x0, y, lc, ha='left', va='top', fontsize=7.5, fontweight='bold')
        fig.text(ax_pos.x0 + 0.20, y, rc, ha='left', va='top', fontsize=7.5)


def _add_moon_labels(
    ax: 'matplotlib.axes.Axes',
    fig: 'matplotlib.figure.Figure',
    moon_label_data: list[tuple[str, float, float]],
    delta: float,
    labelpts: float,
) -> None:
    """Place moon labels using 2-D bounding-box collision avoidance.

    Each moon is tried at up to 10 candidate offsets (right, left, above, below,
    and diagonal variants).  The first placement whose text bounding box does not
    overlap any already-placed box is used.  Moons are processed outer-first so
    isolated moons (Iapetus, Phoebe, Titan, Hyperion) always get their preferred
    slot; inner-cluster moons fill remaining gaps or are silently omitted.

    All geometry is computed in *axes-relative screen points* (+x right, +y up)
    so that the inverted x-axis is handled transparently.

    Parameters:
        ax: Target matplotlib Axes.
        fig: Parent figure (for size calculations).
        moon_label_data: List of (name, x_fov, y_fov) in FOV-plane coordinates.
        delta: Half-FOV tangent (= tan(fov/2)).
        labelpts: Font size in points.
    """
    label_fontsize = max(6.0, float(labelpts))

    # After set_aspect('equal', adjustable='box') matplotlib shrinks the axes box
    # to enforce equal data-unit width and height.  get_position() before draw
    # may still return the REQUESTED Bbox, not the shrunken one.  Compute the
    # actual square axes size ourselves so label-box arithmetic is consistent.
    ax_pos = ax.get_position()
    fig_w_in = fig.get_figwidth()
    fig_h_in = fig.get_figheight()
    requested_w_in = ax_pos.width * fig_w_in
    requested_h_in = ax_pos.height * fig_h_in
    # Equal aspect: axes will be the smallest square that fits.
    actual_in = min(requested_w_in, requested_h_in)
    ax_w_pt = actual_in * 72.0
    ax_h_pt = actual_in * 72.0

    # Approximate text box dimensions (em-square heuristic)
    char_w_pt = 0.58 * label_fontsize
    char_h_pt = 1.20 * label_fontsize
    gap = max(5.0, label_fontsize * 0.65)   # gap between dot edge and label edge
    pad = 1.5                               # extra padding for overlap test

    placed_boxes: list[tuple[float, float, float, float]] = []  # (x0,y0,x1,y1)

    # Outer moons first: they have unique screen positions → best label spots
    sorted_by_dist = sorted(moon_label_data, key=lambda t: -(t[1] ** 2 + t[2] ** 2))

    for mname, mx, my in sorted_by_dist:
        # Moon dot in axes-relative screen points.
        # x is inverted: high FOV-x (east/left on sky) → low screen-x (left on axes).
        sx = (delta - mx) / (2.0 * delta) * ax_w_pt
        sy = (my + delta) / (2.0 * delta) * ax_h_pt
        lw = len(mname) * char_w_pt
        lh = char_h_pt

        # Candidate placements: (left_edge_offset, bottom_edge_offset) in screen pts.
        # Positive x → screen-right; positive y → screen-up.
        candidates = [
            (gap,           -lh / 2),         # right, v-centred
            (-lw - gap,     -lh / 2),         # left,  v-centred
            (-lw / 2,       gap),             # above, h-centred
            (-lw / 2,       -lh - gap),       # below, h-centred
            (gap,           gap),             # top-right
            (gap,           -lh - gap),       # bottom-right
            (-lw - gap,     gap),             # top-left
            (-lw - gap,     -lh - gap),       # bottom-left
            (gap * 2.5,     -lh / 2),         # far right
            (-lw - gap * 2.5, -lh / 2),       # far left
        ]

        for off_x, off_y in candidates:
            bx0 = sx + off_x
            by0 = sy + off_y
            bx1 = bx0 + lw
            by1 = by0 + lh

            if not any(
                bx0 < pb[2] + pad and bx1 > pb[0] - pad
                and by0 < pb[3] + pad and by1 > pb[1] - pad
                for pb in placed_boxes
            ):
                placed_boxes.append((bx0, by0, bx1, by1))
                ax.annotate(
                    mname,
                    xy=(mx, my),
                    xytext=(off_x, off_y),
                    textcoords='offset points',
                    fontsize=label_fontsize,
                    color='black',
                    clip_on=False,
                    ha='left',
                    va='bottom',
                )
                break
        # If no non-overlapping position found, the moon label is silently omitted.
