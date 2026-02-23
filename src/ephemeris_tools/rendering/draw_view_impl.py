"""Implementation of draw_planetary_view (port of rspk_drawview.f main routine)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TextIO

import cspyce

from ephemeris_tools.constants import DEFAULT_ALIGN_LOC_POINTS
from ephemeris_tools.rendering.draw_view_finish import draw_view_box_labels_stars_close
from ephemeris_tools.rendering.draw_view_helpers import (
    _DEVICE,
    _H1,
    _H2,
    _STAR_DIAMPTS,
    _V1,
    _V2,
    DARK_LINE,
    FOV_PTS,
    HALFPI,
    LIT_LINE,
    LOOP_DLON,
    LOOP_WIDTH,
    MAX_ARCPTS,
    MAX_MINSIZE,
    MAX_NLOOPS,
    MAX_NMOONS,
    MAX_NRINGS,
    MOON_LATS,
    MOON_MERIDS,
    NO_LINE,
    PLANET_LATS,
    PLANET_MERIDS,
    RING_THICKNESS,
    SHADOW_LINE,
    SUN_ID,
    TWOPI,
    _opsgnd,
    _rspk_draw_bodies,
    _rspk_draw_rings,
    _vhat,
    _vnorm,
    _vrotv,
    _write_ps_preamble,
    camera_matrix,
)
from ephemeris_tools.rendering.escher import (
    EscherState,
    EscherViewState,
    esfile,
    write_ps_header,
)
from ephemeris_tools.rendering.euclid import (
    EuclidState,
    eubody,
    eugeom,
    euview,
)


@dataclass(frozen=True)
class DrawPlanetaryViewOptions:
    """Options for draw_planetary_view (geometry, moons, rings, stars, captions)."""

    obs_time: float
    fov: float
    center_ra: float
    center_dec: float
    planet_name: str
    blank_disks: bool = False
    prime_pts: float = 0.0
    nmoons: int = 0
    moon_flags: list[bool] = field(default_factory=list)
    moon_ids: list[int] = field(default_factory=list)
    moon_names: list[str] = field(default_factory=list)
    moon_labelpts: float = 0.0
    moon_diampts: float = 0.0
    nrings: int = 0
    ring_flags: list[bool] = field(default_factory=list)
    ring_rads: list[float] = field(default_factory=list)
    ring_elevs: list[float] = field(default_factory=list)
    ring_eccs: list[float] = field(default_factory=list)
    ring_incs: list[float] = field(default_factory=list)
    ring_peris: list[float] = field(default_factory=list)
    ring_nodes: list[float] = field(default_factory=list)
    ring_offsets: list[list[float]] = field(default_factory=list)
    ring_opaqs: list[bool] = field(default_factory=list)
    ring_dashed: list[bool] = field(default_factory=list)
    ring_method: int = 0
    narcs: int = 0
    arc_flags: list[bool] = field(default_factory=list)
    arc_rings: list[int] = field(default_factory=list)
    arc_minlons: list[float] = field(default_factory=list)
    arc_maxlons: list[float] = field(default_factory=list)
    arc_width: float = 4.0
    nstars: int = 0
    star_ras: list[float] = field(default_factory=list)
    star_decs: list[float] = field(default_factory=list)
    star_names: list[str] = field(default_factory=list)
    star_labels: bool = False
    star_diampts: float = _STAR_DIAMPTS
    title: str = ''
    ncaptions: int = 0
    lcaptions: list[str] = field(default_factory=list)
    rcaptions: list[str] = field(default_factory=list)
    align_loc: float = DEFAULT_ALIGN_LOC_POINTS


def draw_planetary_view(output: TextIO, options: DrawPlanetaryViewOptions) -> None:
    """Generate PostScript showing planetary system at a time.

    Ported from RSPK_DrawView. Renders planet and moons as triaxial ellipsoids
    with terminators, optional rings (with vertical offsets and opacity), arcs,
    and stars. Frame is J2000 (dec up, RA left). Title and captions supported.

    Parameters:
        output: Open text stream for PostScript output.
        options: Geometry and display options (obs_time, fov, center, planet,
            moons, rings, arcs, stars, title, captions). See DrawPlanetaryViewOptions.
    """
    from ephemeris_tools.spice.bodmat import bodmat
    from ephemeris_tools.spice.common import get_state
    from ephemeris_tools.spice.observer import observer_state
    from ephemeris_tools.spice.shifts import spkapp_shifted

    spice_state = get_state()
    planet_id = spice_state.planet_id
    planet_num = spice_state.planet_num

    # Default list args; copy ring_flags before padding so we do not mutate caller's list
    moon_flags = list(options.moon_flags)
    moon_ids = list(options.moon_ids)
    moon_names = list(options.moon_names)
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
    arc_flags = list(options.arc_flags)
    arc_rings = list(options.arc_rings)
    arc_minlons = list(options.arc_minlons)
    arc_maxlons = list(options.arc_maxlons)
    star_ras = list(options.star_ras)
    star_decs = list(options.star_decs)
    star_names = list(options.star_names)
    lcaptions = list(options.lcaptions) if options.lcaptions else []
    rcaptions = list(options.rcaptions) if options.rcaptions else []

    out_name = getattr(output, 'name', '') or 'view.ps'

    # ===================================================================
    # Initialize the PostScript file
    # ===================================================================
    escher_state = EscherState()
    escher_state.outuni = output
    escher_state.open = True
    escher_state.external_stream = True
    escher_state.outfil = out_name
    escher_state.creator = f'{options.planet_name} Viewer, PDS Ring-Moon Systems Node'
    escher_state.fonts = 'Helvetica'

    esfile(out_name, escher_state.creator, escher_state.fonts, escher_state)
    escher_state.outuni = output
    escher_state.open = True
    escher_state.external_stream = True
    write_ps_header(escher_state)
    _write_ps_preamble(
        escher_state,
        options.planet_name,
        options.title,
        options.ncaptions,
        lcaptions,
        rcaptions,
        options.align_loc,
        options.moon_labelpts,
    )

    # ===================================================================
    # Initialize camera
    # ===================================================================
    if not (0 < options.fov < math.pi):
        raise ValueError(f'options.fov must be in (0, pi), got {options.fov!r}')
    delta = math.tan(options.fov / 2.0)
    view_state = EscherViewState()
    euclid_state = EuclidState()

    euview(
        _DEVICE,
        _H1,
        _H2,
        _V1,
        _V2,
        -delta,
        delta,
        -delta,
        delta,
        euclid_state,
        view_state,
        escher_state,
    )

    # Meridian and latitude count
    if options.blank_disks:
        pmerids, plats = 0, 0
        mmerids, mlats = 0, 0
        term_line = LIT_LINE
    else:
        pmerids, plats = PLANET_MERIDS, PLANET_LATS
        mmerids, mlats = MOON_MERIDS, MOON_LATS
        term_line = DARK_LINE

    # ===================================================================
    # Set up observer and planet geometry (SPICE calls)
    # ===================================================================

    # Observer state
    obs_pv = list(observer_state(options.obs_time))

    # Planet state
    _planet_pv, planet_dt = cspyce.spkapp(planet_id, options.obs_time, 'J2000', obs_pv[:6], 'LT')
    planet_dpv = list(_planet_pv)
    planet_time = options.obs_time - planet_dt
    planet_pv = list(cspyce.spkssb(planet_id, planet_time, 'J2000'))

    # Planet rotation matrix (J2000 -> body frame)
    planet_mat = bodmat(planet_id, planet_time)

    # Sun location and radius
    sun_pv, _sun_dt = cspyce.spkapp(SUN_ID, planet_time, 'J2000', planet_pv[:6], 'LT+S')
    sun_dpv = list(sun_pv)
    sun_loc = [planet_pv[i] + sun_dpv[i] for i in range(3)]
    sun_radii_arr = cspyce.bodvar(SUN_ID, 'RADII')
    sun_rad = float(sun_radii_arr[0])

    # Camera C-matrix
    cmat = camera_matrix(options.center_ra, options.center_dec)

    # ===================================================================
    # Build body list
    # ===================================================================

    nbodies = 0
    body_locs: list[list[float]] = []
    body_axes: list[list[list[float]]] = []
    body_pts: list[float] = []
    body_dist: list[float] = []
    body_los: list[list[float]] = []
    body_names_list: list[str] = []

    # Body 1: Planet
    nbodies += 1
    planet_loc = [obs_pv[i] + planet_dpv[i] for i in range(3)]
    body_locs.append(planet_loc)

    # planet_mat is J2000→body.  Its rows ARE the body axes in J2000
    # (matching FORTRAN: XPOSE then column extraction).
    p_radii_arr = cspyce.bodvar(planet_id, 'RADII')
    planet_axes_scaled = [[planet_mat[i][j] * p_radii_arr[i] for j in range(3)] for i in range(3)]
    body_axes.append(planet_axes_scaled)
    body_pts.append(0.0)
    body_dist.append(0.0)
    body_los.append([0.0, 0.0, 0.0])
    body_names_list.append(' ')  # Never label planet

    # Body 2: Dummy body at middle of field of view
    nbodies += 1
    dummy_axes = [_vhat(planet_axes_scaled[i]) for i in range(3)]
    body_axes.append(dummy_axes)
    # Locate along optic axis, 2x planet distance
    tempvec = [planet_dpv[i] for i in range(3)]
    tdist = _vnorm(tempvec)
    optic_vec = [2.0 * tdist * cmat[j][2] for j in range(3)]
    dummy_loc = [obs_pv[i] + optic_vec[i] for i in range(3)]
    body_locs.append(dummy_loc)
    body_pts.append(0.0)
    body_dist.append(0.0)
    body_los.append([0.0, 0.0, 0.0])
    body_names_list.append(' ')

    # Bodies 3+: Moons
    use_nmoons = min(options.nmoons, MAX_NMOONS)
    for imoon in range(use_nmoons):
        if imoon >= len(moon_flags) or not moon_flags[imoon]:
            continue
        if imoon >= len(moon_ids):
            continue
        mid = moon_ids[imoon]

        # Moon position
        try:
            moon_pv, mdt = spkapp_shifted(mid, options.obs_time, 'J2000', obs_pv[:6], 'LT')
        except Exception:
            continue
        moon_dpv = list(moon_pv)
        moon_loc = [obs_pv[i] + moon_dpv[i] for i in range(3)]
        body_locs.append(moon_loc)
        body_los.append(list(moon_dpv[:3]))

        # Moon axes - use moon's own BODMAT if available, else planet_mat
        try:
            if cspyce.bodfnd(mid, 'POLE_RA'):
                moon_rot = bodmat(mid, options.obs_time - mdt)
                moon_mat = [list(row) for row in moon_rot]
            else:
                moon_mat = [list(row) for row in planet_mat]
        except Exception:
            moon_mat = [list(row) for row in planet_mat]

        # moon_mat is J2000→body. Its rows are the body axes in J2000.
        try:
            m_radii_arr = list(cspyce.bodvar(mid, 'RADII'))
        except Exception:
            m_radii_arr = [1.0, 1.0, 1.0]
        moon_axes = [[moon_mat[i][j] * m_radii_arr[i] for j in range(3)] for i in range(3)]
        body_axes.append(moon_axes)

        # Projected diameter in points
        moon_dist_km = _vnorm(moon_dpv[:3])
        body_pts_val = 2.0 * m_radii_arr[0] * FOV_PTS / (moon_dist_km * options.fov)
        body_pts.append(body_pts_val)

        # Name
        mname = moon_names[imoon] if imoon < len(moon_names) else ''
        body_names_list.append(mname)

        # Distance from planet
        tv = [moon_loc[i] - planet_loc[i] for i in range(3)]
        body_dist.append(_vnorm(tv))

        nbodies += 1

    # ===================================================================
    # Determine ring shapes (FORTRAN lines 698-820)
    # ===================================================================

    use_nrings = min(options.nrings, MAX_NRINGS)

    # Ensure ring and arc lists have at least use_nrings / narcs entries to avoid IndexError
    _def_f = False
    _def_0 = 0.0
    _def_03 = [0.0, 0.0, 0.0]
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
    use_narcs = min(
        options.narcs,
        len(arc_rings),
        len(arc_flags),
        len(arc_minlons),
        len(arc_maxlons),
    )
    while len(arc_rings) < options.narcs:
        arc_rings.append(0)
    while len(arc_flags) < options.narcs:
        arc_flags.append(_def_f)
    while len(arc_minlons) < options.narcs:
        arc_minlons.append(_def_0)
    while len(arc_maxlons) < options.narcs:
        arc_maxlons.append(_def_0)

    # Planet pole vector (reversed for Uranus)
    pole = _vhat(planet_axes_scaled[2])
    if planet_num == 7:
        pole = [-pole[0], -pole[1], -pole[2]]

    # Equatorial plane ascending node (J2000)
    j2000_z = [0.0, 0.0, 1.0]
    ascnode = [
        j2000_z[1] * pole[2] - j2000_z[2] * pole[1],
        j2000_z[2] * pole[0] - j2000_z[0] * pole[2],
        j2000_z[0] * pole[1] - j2000_z[1] * pole[0],
    ]

    # Extrapolate planet's relative location at observer-received time
    offset = [planet_dt * planet_pv[3 + i] for i in range(3)]

    r_ring_locs: list[list[float]] = []
    r_ring_axes1: list[list[float]] = []
    r_ring_axes2: list[list[float]] = []
    r_ring_axes3: list[list[float]] = []
    r_ring_dark: list[bool] = []

    last_opaq = 0
    nloops = 0
    loop_locs: list[list[float]] = []
    loop_axes1: list[list[float]] = []
    loop_axes2: list[list[float]] = []
    loop_ring: list[int] = []

    for iring in range(use_nrings):
        # Initialize ring arrays to zeros even for skipped rings
        if not ring_flags[iring]:
            r_ring_locs.append([0.0, 0.0, 0.0])
            r_ring_axes1.append([0.0, 0.0, 0.0])
            r_ring_axes2.append([0.0, 0.0, 0.0])
            r_ring_axes3.append([0.0, 0.0, 0.0])
            r_ring_dark.append(False)
            continue

        rad = ring_rads[iring] if iring < len(ring_rads) else 0.0
        ecc = ring_eccs[iring] if iring < len(ring_eccs) else 0.0

        # Track outermost opaque ring
        if iring < len(ring_opaqs) and ring_opaqs[iring]:
            last_opaq = iring + 1  # 1-based

        # Compute ring pole and ascending node from ring inclination/node
        rn = ring_nodes[iring] if iring < len(ring_nodes) else 0.0
        ri = ring_incs[iring] if iring < len(ring_incs) else 0.0

        # VROTV(ascnode, pole, ring_nodes(iring)) -> ringnode
        ringnode = _vrotv(ascnode, pole, rn)
        # VROTV(pole, ringnode, ring_incs(iring)) -> ringpole
        ringpole = _vrotv(pole, ringnode, ri)
        ringpole = _vhat(ringpole)

        # Ring axes
        ring_ax3 = [RING_THICKNESS * ringpole[i] for i in range(3)]
        r_ring_axes3.append(ring_ax3)

        # Pericenter direction
        rp = ring_peris[iring] if iring < len(ring_peris) else 0.0
        peri = _vrotv(ringnode, ringpole, rp - rn)
        peri = _vhat(peri)
        ring_ax1 = [rad * peri[i] for i in range(3)]
        r_ring_axes1.append(ring_ax1)

        # Minor axis = peri rotated 90 degrees around ringpole
        minor_dir = _vrotv(peri, ringpole, HALFPI)
        ring_ax2 = [rad * math.sqrt(1.0 - ecc * ecc) * minor_dir[i] for i in range(3)]
        r_ring_axes2.append(ring_ax2)

        # Ring center = planet_loc - ecc * major_axis + elevation + offset
        ring_loc = [-ecc * ring_ax1[i] + planet_loc[i] for i in range(3)]
        # Add vertical elevation
        re = ring_elevs[iring] if iring < len(ring_elevs) else 0.0
        ring_loc = [ring_loc[i] + re * pole[i] for i in range(3)]

        # Add ring offset
        if iring < len(ring_offsets):
            ro = ring_offsets[iring]
            ring_loc = [ring_loc[i] + ro[i] for i in range(3)]

        r_ring_locs.append(ring_loc)

        # Determine if ring is dark (observer and Sun on opposite sides)
        tempvec_obs = [ring_loc[i] - obs_pv[i] + offset[i] for i in range(3)]
        dot1 = -(
            ringpole[0] * tempvec_obs[0]
            + ringpole[1] * tempvec_obs[1]
            + ringpole[2] * tempvec_obs[2]
        )
        sun_hat = _vhat(sun_dpv[:3])
        dot2 = ringpole[0] * sun_hat[0] + ringpole[1] * sun_hat[1] + ringpole[2] * sun_hat[2]

        is_dashed = ring_dashed[iring] if iring < len(ring_dashed) else False
        if is_dashed:
            r_ring_dark.append(False)
        else:
            sun_dist_val = _vnorm(sun_dpv[:3])
            sun_angular = sun_rad / sun_dist_val if sun_dist_val > 0 else 0
            r_ring_dark.append(_opsgnd(dot1, dot2) and abs(dot2) > sun_angular)

        # Arc loops for this ring
        for iarc in range(use_narcs):
            if iarc >= len(arc_rings) or arc_rings[iarc] != iring + 1:  # 1-based comparison
                continue
            if iarc >= len(arc_flags) or not arc_flags[iarc]:
                continue

            # Mean anomaly range
            lon1 = (arc_minlons[iarc] if iarc < len(arc_minlons) else 0.0) - rp
            lon2 = (arc_maxlons[iarc] if iarc < len(arc_maxlons) else 0.0) - rp
            if lon2 < lon1:
                lon2 += TWOPI

            nsteps = max(int((lon2 - lon1) / LOOP_DLON), 1)
            dlon = (lon2 - lon1) / nsteps

            lon = lon1 - dlon
            for _istep in range(nsteps):
                lon += dlon
                if nloops >= MAX_NLOOPS:
                    break
                nloops += 1

                # Vectors from ring center to loop ends
                vec1 = [math.cos(lon) * ring_ax1[i] + math.sin(lon) * ring_ax2[i] for i in range(3)]
                vec2 = [
                    math.cos(lon + dlon) * ring_ax1[i] + math.sin(lon + dlon) * ring_ax2[i]
                    for i in range(3)
                ]

                # Loop center and axes
                tmid = [0.5 * vec1[i] + 0.5 * vec2[i] for i in range(3)]
                la1 = [vec1[i] - tmid[i] for i in range(3)]
                la2 = _vhat(tmid)
                la2 = [LOOP_WIDTH * la2[i] for i in range(3)]
                ll = [tmid[i] + ring_loc[i] for i in range(3)]

                loop_axes1.append(la1)
                loop_axes2.append(la2)
                loop_locs.append(ll)
                loop_ring.append(iring + 1)  # 1-based

    # ===================================================================
    # Render scene based on ring_method
    # ===================================================================

    use_diampts = min(MAX_MINSIZE, options.moon_diampts)
    use_arcpts = min(MAX_ARCPTS, options.arc_width)

    transparent_method = 0
    semi_transparent_method = 1
    # OPAQUE_METHOD = 2

    if options.ring_method == transparent_method or last_opaq == 0:
        # Case 0: Transparent — simplest case
        eugeom(
            1,
            [sun_loc],
            [sun_rad],
            obs_pv[:3],
            [cmat[0], cmat[1], cmat[2]],
            nbodies,
            body_locs,
            body_axes,
            euclid_state,
        )

        _rspk_draw_bodies(
            nbodies=nbodies,
            body_pts=body_pts,
            body_names=body_names_list,
            body_dist=body_dist,
            body_diampts=use_diampts,
            update_names=True,
            mindist=0.0,
            pmerids=pmerids,
            plats=plats,
            mmerids=mmerids,
            mlats=mlats,
            lit_line=LIT_LINE,
            dark_line=DARK_LINE,
            term_line=term_line,
            lit_line2=LIT_LINE,
            dark_line2=DARK_LINE,
            term_line2=term_line,
            prime_pts=options.prime_pts,
            euclid_state=euclid_state,
            view_state=view_state,
            escher_state=escher_state,
        )

        _rspk_draw_rings(
            iring1=1,
            iring2=use_nrings,
            ring_flags=ring_flags,
            ring_locs=r_ring_locs,
            ring_axes1=r_ring_axes1,
            ring_axes2=r_ring_axes2,
            ring_dark=r_ring_dark,
            ring_dashed=ring_dashed,
            nloops=nloops,
            loop_locs=loop_locs,
            loop_axes1=loop_axes1,
            loop_axes2=loop_axes2,
            loop_ring=loop_ring,
            arc_width=use_arcpts,
            lit_line=LIT_LINE,
            dark_line=DARK_LINE,
            shadow_line=SHADOW_LINE,
            term_line=term_line,
            euclid_state=euclid_state,
            view_state=view_state,
            escher_state=escher_state,
        )

    elif options.ring_method == semi_transparent_method:
        # Case 1: Semi-transparent — two passes
        lo = last_opaq - 1  # 0-based index for outermost opaque ring

        # First pass: unlit bodies
        eugeom(
            1,
            [sun_loc],
            [sun_rad],
            obs_pv[:3],
            [cmat[0], cmat[1], cmat[2]],
            nbodies,
            body_locs,
            body_axes,
            euclid_state,
        )
        _rspk_draw_bodies(
            nbodies=nbodies,
            body_pts=body_pts,
            body_names=body_names_list,
            body_dist=body_dist,
            body_diampts=use_diampts,
            update_names=True,
            mindist=ring_rads[lo] if lo < len(ring_rads) else 0.0,
            pmerids=pmerids,
            plats=plats,
            mmerids=mmerids,
            mlats=mlats,
            lit_line=DARK_LINE,
            dark_line=DARK_LINE,
            term_line=DARK_LINE,
            lit_line2=LIT_LINE,
            dark_line2=DARK_LINE,
            term_line2=term_line,
            prime_pts=options.prime_pts,
            euclid_state=euclid_state,
            view_state=view_state,
            escher_state=escher_state,
        )

        # Redefine with outermost opaque ring as flat ellipsoid
        ext_locs = [*body_locs, r_ring_locs[lo]]
        ext_axes = [*body_axes, [r_ring_axes1[lo], r_ring_axes2[lo], r_ring_axes3[lo]]]
        eugeom(
            1,
            [sun_loc],
            [sun_rad],
            obs_pv[:3],
            [cmat[0], cmat[1], cmat[2]],
            nbodies + 1,
            ext_locs,
            ext_axes,
            euclid_state,
        )

        # Re-draw lit, but not interior moons
        _rspk_draw_bodies(
            nbodies=nbodies,
            body_pts=body_pts,
            body_names=body_names_list,
            body_dist=body_dist,
            body_diampts=use_diampts,
            update_names=False,
            mindist=ring_rads[lo] if lo < len(ring_rads) else 0.0,
            pmerids=pmerids,
            plats=plats,
            mmerids=mmerids,
            mlats=mlats,
            lit_line=LIT_LINE,
            dark_line=DARK_LINE,
            term_line=term_line,
            lit_line2=NO_LINE,
            dark_line2=NO_LINE,
            term_line2=NO_LINE,
            prime_pts=options.prime_pts,
            euclid_state=euclid_state,
            view_state=view_state,
            escher_state=escher_state,
        )

        # Draw opaque ring invisibly
        eubody(
            nbodies + 1, 0, 0, 1, NO_LINE, NO_LINE, NO_LINE, euclid_state, view_state, escher_state
        )

        # Exterior rings
        _rspk_draw_rings(
            iring1=last_opaq + 1,
            iring2=use_nrings,
            ring_flags=ring_flags,
            ring_locs=r_ring_locs,
            ring_axes1=r_ring_axes1,
            ring_axes2=r_ring_axes2,
            ring_dark=r_ring_dark,
            ring_dashed=ring_dashed,
            nloops=nloops,
            loop_locs=loop_locs,
            loop_axes1=loop_axes1,
            loop_axes2=loop_axes2,
            loop_ring=loop_ring,
            arc_width=use_arcpts,
            lit_line=LIT_LINE,
            dark_line=DARK_LINE,
            shadow_line=SHADOW_LINE,
            term_line=term_line,
            euclid_state=euclid_state,
            view_state=view_state,
            escher_state=escher_state,
        )

        # Re-define without rings
        eugeom(
            1,
            [sun_loc],
            [sun_rad],
            obs_pv[:3],
            [cmat[0], cmat[1], cmat[2]],
            nbodies,
            body_locs,
            body_axes,
            euclid_state,
        )

        # Set up bodies without drawing (for correct ring lighting)
        _rspk_draw_bodies(
            nbodies=nbodies,
            body_pts=body_pts,
            body_names=body_names_list,
            body_dist=body_dist,
            body_diampts=use_diampts,
            update_names=False,
            mindist=0.0,
            pmerids=pmerids,
            plats=plats,
            mmerids=mmerids,
            mlats=mlats,
            lit_line=NO_LINE,
            dark_line=NO_LINE,
            term_line=NO_LINE,
            lit_line2=NO_LINE,
            dark_line2=NO_LINE,
            term_line2=NO_LINE,
            prime_pts=0.0,
            euclid_state=euclid_state,
            view_state=view_state,
            escher_state=escher_state,
        )

        # Interior rings
        _rspk_draw_rings(
            iring1=1,
            iring2=last_opaq,
            ring_flags=ring_flags,
            ring_locs=r_ring_locs,
            ring_axes1=r_ring_axes1,
            ring_axes2=r_ring_axes2,
            ring_dark=r_ring_dark,
            ring_dashed=ring_dashed,
            nloops=nloops,
            loop_locs=loop_locs,
            loop_axes1=loop_axes1,
            loop_axes2=loop_axes2,
            loop_ring=loop_ring,
            arc_width=use_arcpts,
            lit_line=LIT_LINE,
            dark_line=DARK_LINE,
            shadow_line=SHADOW_LINE,
            term_line=term_line,
            euclid_state=euclid_state,
            view_state=view_state,
            escher_state=escher_state,
        )

    else:
        # Case 2: Opaque
        lo = last_opaq - 1

        ext_locs = [*body_locs, r_ring_locs[lo]]
        ext_axes = [*body_axes, [r_ring_axes1[lo], r_ring_axes2[lo], r_ring_axes3[lo]]]
        eugeom(
            1,
            [sun_loc],
            [sun_rad],
            obs_pv[:3],
            [cmat[0], cmat[1], cmat[2]],
            nbodies + 1,
            ext_locs,
            ext_axes,
            euclid_state,
        )

        _rspk_draw_bodies(
            nbodies=nbodies,
            body_pts=body_pts,
            body_names=body_names_list,
            body_dist=body_dist,
            body_diampts=use_diampts,
            update_names=True,
            mindist=ring_rads[lo] if lo < len(ring_rads) else 0.0,
            pmerids=pmerids,
            plats=plats,
            mmerids=mmerids,
            mlats=mlats,
            lit_line=LIT_LINE,
            dark_line=DARK_LINE,
            term_line=term_line,
            lit_line2=NO_LINE,
            dark_line2=NO_LINE,
            term_line2=NO_LINE,
            prime_pts=options.prime_pts,
            euclid_state=euclid_state,
            view_state=view_state,
            escher_state=escher_state,
        )

        eubody(
            nbodies + 1, 0, 0, 1, NO_LINE, NO_LINE, NO_LINE, euclid_state, view_state, escher_state
        )

        _rspk_draw_rings(
            iring1=last_opaq + 1,
            iring2=use_nrings,
            ring_flags=ring_flags,
            ring_locs=r_ring_locs,
            ring_axes1=r_ring_axes1,
            ring_axes2=r_ring_axes2,
            ring_dark=r_ring_dark,
            ring_dashed=ring_dashed,
            nloops=nloops,
            loop_locs=loop_locs,
            loop_axes1=loop_axes1,
            loop_axes2=loop_axes2,
            loop_ring=loop_ring,
            arc_width=use_arcpts,
            lit_line=LIT_LINE,
            dark_line=DARK_LINE,
            shadow_line=SHADOW_LINE,
            term_line=term_line,
            euclid_state=euclid_state,
            view_state=view_state,
            escher_state=escher_state,
        )

        # Re-define without rings
        eugeom(
            1,
            [sun_loc],
            [sun_rad],
            obs_pv[:3],
            [cmat[0], cmat[1], cmat[2]],
            nbodies,
            body_locs,
            body_axes,
            euclid_state,
        )

        # Re-draw interior moons
        _rspk_draw_bodies(
            nbodies=nbodies,
            body_pts=body_pts,
            body_names=body_names_list,
            body_dist=body_dist,
            body_diampts=use_diampts,
            update_names=True,
            mindist=ring_rads[lo] if lo < len(ring_rads) else 0.0,
            pmerids=pmerids,
            plats=plats,
            mmerids=mmerids,
            mlats=mlats,
            lit_line=NO_LINE,
            dark_line=NO_LINE,
            term_line=NO_LINE,
            lit_line2=LIT_LINE,
            dark_line2=DARK_LINE,
            term_line2=term_line,
            prime_pts=options.prime_pts,
            euclid_state=euclid_state,
            view_state=view_state,
            escher_state=escher_state,
        )

        # Interior rings
        _rspk_draw_rings(
            iring1=1,
            iring2=last_opaq,
            ring_flags=ring_flags,
            ring_locs=r_ring_locs,
            ring_axes1=r_ring_axes1,
            ring_axes2=r_ring_axes2,
            ring_dark=r_ring_dark,
            ring_dashed=ring_dashed,
            nloops=nloops,
            loop_locs=loop_locs,
            loop_axes1=loop_axes1,
            loop_axes2=loop_axes2,
            loop_ring=loop_ring,
            arc_width=use_arcpts,
            lit_line=LIT_LINE,
            dark_line=DARK_LINE,
            shadow_line=SHADOW_LINE,
            term_line=term_line,
            euclid_state=euclid_state,
            view_state=view_state,
            escher_state=escher_state,
        )

    draw_view_box_labels_stars_close(
        escher_state=escher_state,
        view_state=view_state,
        euclid_state=euclid_state,
        cmat=cmat,
        delta=delta,
        moon_labelpts=options.moon_labelpts,
        body_names_list=body_names_list,
        body_los=body_los,
        body_pts=body_pts,
        use_diampts=use_diampts,
        fov=options.fov,
        nbodies=nbodies,
        nstars=options.nstars,
        star_ras=star_ras,
        star_decs=star_decs,
        star_names=star_names,
        star_labels=options.star_labels,
        star_diampts=options.star_diampts,
    )
