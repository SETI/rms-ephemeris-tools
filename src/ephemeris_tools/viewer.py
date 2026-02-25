"""Planet viewer tool: PostScript diagram and tables (port of viewer3_*.f)."""

from __future__ import annotations

import logging
import math
import sys
from pathlib import Path
from typing import TextIO

import cspyce

from ephemeris_tools.config import get_starlist_path
from ephemeris_tools.constants import (
    DEFAULT_ALIGN_LOC_POINTS,
    EARTH_ID,
    EPHEM_DESCRIPTIONS_BY_PLANET,
    MAX_FOV_DEGREES,
    SUN_ID,
    spacecraft_code_to_id,
    spacecraft_name_to_code,
)
from ephemeris_tools.params import ViewerParams
from ephemeris_tools.rendering.draw_view import (
    FOV_PTS,
    DrawPlanetaryViewOptions,
    draw_planetary_view,
    radec_to_plot,
)
from ephemeris_tools.rendering.planet_grid import compute_planet_grid
from ephemeris_tools.spice.geometry import (
    anti_sun,
    body_lonlat,
    body_phase,
    body_radec,
    limb_radius,
)
from ephemeris_tools.spice.load import load_spacecraft, load_spice_files
from ephemeris_tools.spice.observer import (
    observer_state,
    set_observer_id,
    set_observer_location,
)
from ephemeris_tools.spice.rings import ansa_radec
from ephemeris_tools.stars import read_stars
from ephemeris_tools.time_utils import parse_datetime, tai_from_day_sec, tdb_from_tai
from ephemeris_tools.viewer_helpers import (
    _DEG2RAD,
    _RAD2DEG,
    _compute_jupiter_torus_node,
    _compute_mars_deimos_ring_node,
    _compute_ring_center_offsets,
    _fortran_fixed,
    _fov_deg_from_unit,
    _label_points_from_selection,
    _neptune_arc_model_index,
    _propagated_neptune_arcs,
    _propagated_saturn_f_ring,
    _propagated_uranus_rings,
    _resolve_center_ansa_radius_km,
    _resolve_center_body_id,
    _resolve_viewer_ring_flags,
    _ring_method_from_opacity,
    _strip_leading_option_code,
    _viewer_call_kwargs_from_params,
    _write_fov_table,
    get_planet_config,
)

logger = logging.getLogger(__name__)

__all__ = [
    '_fov_deg_from_unit',
    '_propagated_saturn_f_ring',
    '_resolve_center_ansa_radius_km',
    '_resolve_viewer_ring_flags',
    '_viewer_call_kwargs_from_params',
    'get_planet_config',
    'run_viewer',
]


def run_viewer(params: ViewerParams) -> None:
    """Generate planet viewer PostScript diagram and FOV table (port of viewer3_*.f).

    Loads SPICE, sets observer, computes geometry, and draws planet/rings/moons.
    Writes PostScript to params.output_ps (if set) and FOV table to params.output_txt
    or stdout.

    Parameters:
        params: Structured viewer inputs (planet, time, FOV, center, observer,
            rings, moons, display options, output streams).

    Raises:
        ValueError: Unknown planet or invalid time.
        RuntimeError: SPICE load failure.
    """
    kwargs = _viewer_call_kwargs_from_params(params)
    _run_viewer_impl(**kwargs)


def _run_viewer_impl(
    *,
    planet_num: int,
    time_str: str = '',
    fov: float = 1.0,
    center_mode: str = 'J2000',
    center_ra: float = 0.0,
    center_dec: float = 0.0,
    center_body_name: str | None = None,
    center_ansa_name: str | None = None,
    center_ansa_ew: str = 'east',
    center_star_name: str | None = None,
    viewpoint: str = 'Earth',
    ephem_version: int = 0,
    ephem_display: str | None = None,
    moon_ids: list[int] | None = None,
    moon_selection_display: str | None = None,
    blank_disks: bool = False,
    ring_selection: list[str] | None = None,
    ring_selection_display: str | None = None,
    output_ps: TextIO | None = None,
    output_txt: TextIO | None = None,
    fov_unit: str | None = None,
    observer_latitude: float | None = None,
    observer_longitude: float | None = None,
    observer_altitude: float | None = None,
    observer_lon_dir: str = 'east',
    viewpoint_display: str | None = None,
    labels: str | None = None,
    moon_points: float = 0.0,
    meridian_points: float = 0.0,
    opacity: str = 'Transparent',
    peris: str = 'None',
    peripts: float = 4.0,
    arcmodel: str | None = None,
    arcpts: float = 4.0,
    torus: bool = False,
    torus_inc: float = 6.8,
    torus_rad: float = 422000.0,
    show_standard_stars: bool = False,
    extra_star_name: str | None = None,
    extra_star_ra_deg: float | None = None,
    extra_star_dec_deg: float | None = None,
    other_bodies: list[str] | None = None,
    title: str = '',
) -> None:
    """Internal viewer implementation (flat kwargs from ViewerParams)."""
    cfg = get_planet_config(planet_num)
    if cfg is None:
        raise ValueError(f'Unknown planet number: {planet_num}')

    spacecraft_observer_id: int | None = None
    if observer_latitude is None and observer_longitude is None:
        viewpoint_code = spacecraft_name_to_code(viewpoint)
        if viewpoint_code is not None:
            sc_abbrev = spacecraft_code_to_id(viewpoint_code)
            if sc_abbrev:
                try:
                    # FORTRAN loads spacecraft kernels before planet kernels.
                    # This affects SPICE segment precedence for encounter geometry.
                    if load_spacecraft(sc_abbrev, planet_num, ephem_version, set_obs=False):
                        spacecraft_observer_id = viewpoint_code
                except Exception:
                    spacecraft_observer_id = None

    # Match FORTRAN viewer: load "other" spacecraft kernels before planet kernels
    # so the user-selected planet ephemeris still takes precedence.
    for other_name in other_bodies or []:
        token = other_name.strip()
        if token == '':
            continue
        low = token.lower()
        if low in {'sun', 'anti-sun', 'antisun', 'earth', 'barycenter'}:
            continue
        sc_code = spacecraft_name_to_code(token)
        if sc_code is None:
            continue
        sc_abbrev = spacecraft_code_to_id(sc_code)
        if not sc_abbrev:
            continue
        try:
            load_spacecraft(sc_abbrev, planet_num, ephem_version, set_obs=False)
        except Exception:
            # Keep viewer behavior tolerant of unavailable spacecraft kernels.
            pass

    ok, reason = load_spice_files(planet_num, ephem_version)
    if not ok:
        raise RuntimeError(f'Failed to load SPICE kernels: {reason}')
    if observer_latitude is not None and observer_longitude is not None:
        set_observer_location(
            observer_latitude,
            observer_longitude,
            observer_altitude if observer_altitude is not None else 0.0,
        )
    else:
        if spacecraft_observer_id is not None:
            set_observer_id(spacecraft_observer_id)
        else:
            use_earth = True
            code = spacecraft_name_to_code(viewpoint)
            if code is not None:
                sc_id = spacecraft_code_to_id(code)
                if sc_id:
                    try:
                        use_earth = not load_spacecraft(
                            sc_id, planet_num, ephem_version, set_obs=True
                        )
                    except Exception:
                        # FORTRAN viewer keeps running for named observatories even when
                        # no trajectory kernels exist for that name at the target epoch.
                        pass
            if use_earth:
                set_observer_id(EARTH_ID)

    parsed = parse_datetime(time_str)
    if parsed is None:
        raise ValueError(f'Invalid time: {time_str!r}')
    day, sec = parsed
    et = tdb_from_tai(tai_from_day_sec(day, sec))
    try:
        observer_state(et)
    except Exception:
        set_observer_id(EARTH_ID)

    fov_deg = _fov_deg_from_unit(fov, fov_unit, et=et, cfg=cfg)
    fov_rad = fov_deg * _DEG2RAD
    # FORTRAN clamps FOV to MAX_FOV_DEGREES to prevent projection singularities
    fov_rad = min(fov_rad, MAX_FOV_DEGREES * _DEG2RAD)

    _, _limb_rad_rad = limb_radius(et)
    planet_ra, planet_dec = body_radec(et, cfg.planet_id)
    caption_center_body_id = cfg.planet_id
    caption_center_body_name = cfg.planet_name
    centered_star_name: str | None = None
    centered_star_ra_rad: float | None = None
    centered_star_dec_rad: float | None = None
    if center_mode == 'J2000' and (center_ra != 0.0 or center_dec != 0.0):
        center_ra_rad = center_ra * _DEG2RAD
        center_dec_rad = center_dec * _DEG2RAD
    elif center_mode == 'body':
        center_body_id = _resolve_center_body_id(cfg, center_body_name)
        center_ra_rad, center_dec_rad = body_radec(et, center_body_id)
        caption_center_body_id = center_body_id
        if center_body_id == cfg.barycenter_id and cfg.barycenter_id is not None:
            caption_center_body_id = cfg.planet_id
            caption_center_body_name = cfg.planet_name
        elif center_body_id != cfg.planet_id:
            for moon in cfg.moons:
                if moon.id == center_body_id:
                    caption_center_body_name = moon.name
                    break
    elif center_mode == 'ansa':
        ring_radius_km = _resolve_center_ansa_radius_km(cfg, center_ansa_name)
        if ring_radius_km is None:
            center_ra_rad = planet_ra
            center_dec_rad = planet_dec
        else:
            # Match FORTRAN viewer3_*.f semantics:
            # center_ew='west' -> right ansa, 'east' -> left ansa.
            is_right_ansa = center_ansa_ew.strip().lower() == 'west'
            center_ra_rad, center_dec_rad = ansa_radec(et, ring_radius_km, is_right_ansa)
    elif center_mode == 'star':
        target_star = (center_star_name or '').strip()
        if len(target_star) == 0:
            center_ra_rad = planet_ra
            center_dec_rad = planet_dec
        else:
            starlist_candidates = [
                Path(get_starlist_path()) / cfg.starlist_file,
                Path(__file__).resolve().parents[2] / 'web' / 'tools' / cfg.starlist_file,
            ]
            center_ra_rad = planet_ra
            center_dec_rad = planet_dec
            found_center_star = False
            for starlist_path in starlist_candidates:
                if not starlist_path.exists():
                    continue
                try:
                    for star in read_stars(starlist_path, max_stars=1000):
                        if star.name == target_star:
                            center_ra_rad = star.ra
                            center_dec_rad = star.dec
                            centered_star_name = star.name
                            centered_star_ra_rad = star.ra
                            centered_star_dec_rad = star.dec
                            found_center_star = True
                            break
                except OSError:
                    continue
                if found_center_star:
                    break
            if not found_center_star:
                raise ValueError(f'Invalid value found for variable CENTER_STAR: {target_star}')
    elif center_ra == 0.0 and center_dec == 0.0:
        center_ra_rad = planet_ra
        center_dec_rad = planet_dec
    else:
        center_ra_rad = center_ra * _DEG2RAD
        center_dec_rad = center_dec * _DEG2RAD

    track_moon_ids = [m.id for m in cfg.moons if m.id != cfg.planet_id]
    if moon_ids:
        track_moon_ids = [tid for tid in track_moon_ids if tid in moon_ids]
    id_to_name = {m.id: m.name for m in cfg.moons}

    # Table: planet first, then moons (same order as FORTRAN moon_flags).
    table_body_ids = [cfg.planet_id, *track_moon_ids]
    neptune_arc_model = _neptune_arc_model_index(arcmodel)

    if output_txt is None:
        _write_fov_table(
            sys.stdout,
            et=et,
            cfg=cfg,
            planet_ra=planet_ra,
            planet_dec=planet_dec,
            body_ids=table_body_ids,
            id_to_name=id_to_name,
            neptune_arc_model=neptune_arc_model,
            ring_names=ring_selection,
        )
    elif output_txt is not None:
        _write_fov_table(
            output_txt,
            et=et,
            cfg=cfg,
            planet_ra=planet_ra,
            planet_dec=planet_dec,
            body_ids=table_body_ids,
            id_to_name=id_to_name,
            neptune_arc_model=neptune_arc_model,
            ring_names=ring_selection,
        )

    # Plot: FOV_PTS diameter, scale = FOV_PTS / (2*tan(fov/2)) for camera projection.
    scale = FOV_PTS / (2.0 * math.tan(fov_rad / 2.0))

    def to_plot(ra: float, dec: float) -> tuple[float, float] | None:
        """Convert (ra, dec) in radians to plot (x, y) via camera projection."""
        return radec_to_plot(ra, dec, center_ra_rad, center_dec_rad, fov_rad)

    bodies: list[tuple[float, float, str, bool]] = []
    plot_result = to_plot(planet_ra, planet_dec)
    if plot_result is not None:
        px, py = plot_result
        bodies.append((px, py, cfg.planet_name, True))

    for mid in track_moon_ids:
        ra, dec = body_radec(et, mid)
        plot_result = to_plot(ra, dec)
        if plot_result is None:
            continue
        mx, my = plot_result
        name = id_to_name.get(mid, str(mid))
        bodies.append((mx, my, name.upper(), False))

    # Use CGI/CLI title directly; blank title remains blank.
    title = title or ''

    if not blank_disks:
        compute_planet_grid(
            et,
            cfg.planet_id,
            center_ra_rad,
            center_dec_rad,
            scale,
        )

    if output_ps:
        # Build caption strings matching FORTRAN viewer3_*.f exactly
        # In FORTRAN, lcaptions use ':' suffix, rcaptions come from CGI params
        lc: list[str] = []
        rc: list[str] = []

        # Caption 1: Time (UTC)
        lc.append('Time (UTC):')
        rc.append(time_str)

        # Caption 2: Ephemeris — prefer raw CGI/legacy display string when present.
        lc.append('Ephemeris:')
        if ephem_display is not None and ephem_display.strip():
            ephem_caption = _strip_leading_option_code(ephem_display.strip())
        else:
            ephem_caption = EPHEM_DESCRIPTIONS_BY_PLANET.get(planet_num, 'DE440')
        rc.append(ephem_caption)

        # Caption 3: Viewpoint
        lc.append('Viewpoint:')
        viewpoint_text = (
            "Earth's center"
            if 'earth' in viewpoint.lower() or viewpoint == 'observatory'
            else viewpoint
        )
        if viewpoint_display:
            viewpoint_text = viewpoint_display
        elif (
            viewpoint == 'latlon'
            and observer_latitude is not None
            and observer_longitude is not None
            and observer_altitude is not None
        ):
            lon_dir = observer_lon_dir.lower()
            viewpoint_text = (
                f'({observer_latitude:.7f}, {observer_longitude:.7f} {lon_dir},'
                f' {observer_altitude:g})'
            )
        rc.append(viewpoint_text)

        # Caption 4: Moon selection — prefer raw CGI display text when available.
        lc.append('Moon selection:')
        if moon_selection_display:
            rc.append(_strip_leading_option_code(moon_selection_display))
        elif track_moon_ids:
            rc.append(', '.join(id_to_name.get(mid, str(mid)) for mid in track_moon_ids))
        else:
            rc.append('')

        # Caption 5: Ring selection — from CLI/CGI rings value
        lc.append('Ring selection:')
        rc.append(ring_selection_display if ring_selection_display else '')

        # Caption 6: Center body (lon,lat)
        subobs_lon, subobs_lat, _sslon, _sslat = body_lonlat(et, caption_center_body_id)
        lon_dir = cfg.longitude_direction if hasattr(cfg, 'longitude_direction') else 'W'
        lon_deg = subobs_lon * _RAD2DEG
        lat_deg = subobs_lat * _RAD2DEG
        lc.append(f'{caption_center_body_name} center (lon,lat):')
        # FORTRAN format: ('(',f7.3,'\260 ',a1,',',f7.3,'\260)')
        lon_text = _fortran_fixed(lon_deg, 3)
        lat_text = _fortran_fixed(lat_deg, 3)
        rc.append(f'({lon_text:>7s}\260 {lon_dir},{lat_text:>7s}\260)')

        # Caption 7: Phase angle
        phase_rad = body_phase(et, caption_center_body_id)
        phase_deg = phase_rad * _RAD2DEG
        lc.append(f'{caption_center_body_name} phase angle: ')
        # FORTRAN format: (f7.3,'\260') → e.g. '  2.920\260'
        rc.append(f'{phase_deg:7.3f}\260')

        if planet_num == 5 and torus:
            lc.append('Io torus:')
            torus_inc_text = f'{torus_inc:g}'
            if float(torus_rad).is_integer():
                torus_rad_text = str(int(torus_rad))
            else:
                torus_rad_text = f'{torus_rad:g}'
            rc.append(f'Inclination = {torus_inc_text} deg; Radius = {torus_rad_text} km')

        ncaptions = len(lc)

        # Build moon arrays for RSPK_DrawView
        # FORTRAN passes moon_flags(0:NMOONS) where 0 = planet (always False)
        all_moons = [m for m in cfg.moons if m.id != cfg.planet_id]
        f_nmoons = len(all_moons) + 1  # +1 because FORTRAN includes planet as index 0
        f_moon_flags = [False]  # index 0 = planet, always False
        f_moon_ids = [cfg.planet_id]
        f_moon_names = [' ']
        for m in all_moons:
            f_moon_flags.append(True)
            f_moon_ids.append(m.id)
            f_moon_names.append(m.name)

        if moon_ids:
            for i in range(1, len(f_moon_ids)):
                if f_moon_ids[i] not in moon_ids:
                    f_moon_flags[i] = False
            # Fallback: if selection filtered out every moon (e.g. wrong planet or
            # parse mismatch), show all moons so we do not emit a diagram with no
            # moons when the user requested a valid group (e.g. 609 = S1-S9).
            if not any(f_moon_flags[1:]):
                logger.warning(
                    'Moon selection %r matched no moons for planet %s; showing all moons.',
                    moon_ids,
                    planet_num,
                )
                for i in range(1, len(f_moon_flags)):
                    f_moon_flags[i] = True

        # Build ring arrays
        f_nrings = len(cfg.rings) if hasattr(cfg, 'rings') and cfg.rings else 0
        f_ring_flags: list[bool] = []
        f_ring_rads: list[float] = []
        f_ring_elevs: list[float] = []
        f_ring_eccs: list[float] = []
        f_ring_incs: list[float] = []
        f_ring_peris: list[float] = []
        f_ring_nodes: list[float] = []
        f_ring_offsets: list[list[float]] = []
        f_ring_opaqs: list[bool] = []
        f_ring_dashed: list[bool] = []
        f_narcs = 0
        f_arc_flags: list[bool] = []
        f_arc_rings: list[int] = []
        f_arc_minlons: list[float] = []
        f_arc_maxlons: list[float] = []

        if hasattr(cfg, 'rings') and cfg.rings:
            ring_offset_list = _compute_ring_center_offsets(et, cfg)
            mars_deimos_node = _compute_mars_deimos_ring_node(et) if planet_num == 4 else None
            uranus_peri_nodes: tuple[list[float], list[float]] | None = None
            if planet_num == 7:
                peri_deg_list, node_deg_list = _propagated_uranus_rings(et, cfg)
                uranus_peri_nodes = (peri_deg_list, node_deg_list)
            saturn_f_ring_peri_node: tuple[float, float] | None = None
            if planet_num == 6:
                saturn_f_ring_peri_node = _propagated_saturn_f_ring(et, cfg)
            resolved_flags: list[bool] | None = None
            if ring_selection:
                resolved_flags = _resolve_viewer_ring_flags(planet_num, ring_selection, cfg.rings)
            for i, r in enumerate(cfg.rings):
                if resolved_flags is not None:
                    flag = resolved_flags[i] if i < len(resolved_flags) else False
                else:
                    flag = not r.dashed  # FORTRAN: dashed rings hidden by default
                f_ring_flags.append(flag)
                f_ring_rads.append(r.outer_km)
                f_ring_elevs.append(r.elev_km)
                f_ring_eccs.append(r.ecc)
                f_ring_incs.append(r.inc_rad)
                if (
                    planet_num == 7
                    and uranus_peri_nodes is not None
                    and i < len(uranus_peri_nodes[0])
                ):
                    f_ring_peris.append(uranus_peri_nodes[0][i] * _DEG2RAD)
                elif (
                    planet_num == 6
                    and cfg.f_ring_index is not None
                    and i == cfg.f_ring_index
                    and saturn_f_ring_peri_node is not None
                ):
                    f_ring_peris.append(saturn_f_ring_peri_node[0])
                else:
                    f_ring_peris.append(r.peri_rad)
                if planet_num == 4 and i in (2, 3) and mars_deimos_node is not None:
                    f_ring_nodes.append(mars_deimos_node)
                elif (
                    planet_num == 7
                    and uranus_peri_nodes is not None
                    and i < len(uranus_peri_nodes[1])
                ):
                    f_ring_nodes.append(uranus_peri_nodes[1][i] * _DEG2RAD)
                elif (
                    planet_num == 6
                    and cfg.f_ring_index is not None
                    and i == cfg.f_ring_index
                    and saturn_f_ring_peri_node is not None
                ):
                    f_ring_nodes.append(saturn_f_ring_peri_node[1])
                else:
                    f_ring_nodes.append(r.node_rad)
                f_ring_offsets.append(
                    list(ring_offset_list[i]) if i < len(ring_offset_list) else [0.0, 0.0, 0.0]
                )
                f_ring_opaqs.append(r.opaque)
                f_ring_dashed.append(r.dashed)
            if planet_num == 5 and torus and len(f_ring_flags) >= 7:
                torus_idx = 6  # FORTRAN ring #7
                f_ring_flags[torus_idx] = True
                f_ring_rads[torus_idx] = torus_rad
                f_ring_incs[torus_idx] = torus_inc * _DEG2RAD
                torus_node_rad = _compute_jupiter_torus_node(et)
                if torus_node_rad is not None:
                    f_ring_nodes[torus_idx] = torus_node_rad
            # Pericenter markers: zero-length arcs at ring pericenter (FORTRAN style).
            peris_lower = (peris or '').strip().lower()
            if planet_num == 7 and peris_lower and peris_lower != 'none':
                # Uranus: FORTRAN arc_rings(1:7) = rings 1,2,3,4,5,10,11 (1-based).
                # Epsi: only rings 10,11. Else: rings 1,2,3 if selected; 4,5,10,11 always.
                n_rings = len(f_ring_flags)
                uranus_arc_ring_indices = (0, 1, 2, 3, 4, 9, 10)  # 0-based
                if peris_lower.startswith('epsi'):
                    for idx in (9, 10):
                        if idx < n_rings and f_ring_flags[idx]:
                            f_arc_flags.append(True)
                            f_arc_rings.append(idx + 1)
                            f_arc_minlons.append(f_ring_peris[idx])
                            f_arc_maxlons.append(f_ring_peris[idx])
                else:
                    for slot, idx in enumerate(uranus_arc_ring_indices):
                        if idx >= n_rings:
                            continue
                        if slot < 3 and not f_ring_flags[idx]:  # rings 1,2,3: only if selected
                            continue
                        f_arc_flags.append(True)
                        f_arc_rings.append(idx + 1)
                        f_arc_minlons.append(f_ring_peris[idx])
                        f_arc_maxlons.append(f_ring_peris[idx])
                f_narcs = len(f_arc_flags)
            elif planet_num == 6 and peris_lower and peris_lower != 'none':
                # Saturn: single pericenter marker on F ring when selected.
                n_rings = len(f_ring_flags)
                if (
                    cfg.f_ring_index is not None
                    and cfg.f_ring_index < n_rings
                    and f_ring_flags[cfg.f_ring_index]
                ):
                    f_arc_flags.append(True)
                    f_arc_rings.append(cfg.f_ring_index + 1)
                    f_arc_minlons.append(f_ring_peris[cfg.f_ring_index])
                    f_arc_maxlons.append(f_ring_peris[cfg.f_ring_index])
                f_narcs = len(f_arc_flags)
        if planet_num == 8 and hasattr(cfg, 'arcs') and cfg.arcs:
            arc_minmax = _propagated_neptune_arcs(et, cfg, arc_model_index=neptune_arc_model)
            f_narcs = len(cfg.arcs)
            for i, arc in enumerate(cfg.arcs):
                f_arc_flags.append(True)
                f_arc_rings.append(int(arc.ring_index))
                minlon_deg, maxlon_deg = arc_minmax[i]
                f_arc_minlons.append(minlon_deg * _DEG2RAD)
                f_arc_maxlons.append(maxlon_deg * _DEG2RAD)

        star_ras: list[float] = []
        star_decs: list[float] = []
        star_names: list[str] = []
        if (
            center_mode == 'star'
            and show_standard_stars
            and centered_star_name is not None
            and centered_star_ra_rad is not None
            and centered_star_dec_rad is not None
        ):
            star_ras.append(centered_star_ra_rad)
            star_decs.append(centered_star_dec_rad)
            star_names.append(centered_star_name)
        if extra_star_ra_deg is not None and extra_star_dec_deg is not None:
            star_ras.append(extra_star_ra_deg * _DEG2RAD)
            star_decs.append(extra_star_dec_deg * _DEG2RAD)
            star_names.append(extra_star_name or '')
        for other_name in other_bodies or []:
            token = other_name.strip()
            if token == '':
                continue
            low = token.lower()
            try:
                if low == 'sun':
                    ra, dec = body_radec(et, SUN_ID)
                elif low in {'anti-sun', 'antisun'}:
                    ra, dec = anti_sun(et, cfg.planet_id)
                elif low == 'earth':
                    ra, dec = body_radec(et, EARTH_ID)
                elif low == 'barycenter' and cfg.barycenter_id is not None:
                    ra, dec = body_radec(et, cfg.barycenter_id)
                else:
                    known_spacecraft_id = spacecraft_name_to_code(token)
                    if known_spacecraft_id is not None:
                        body_id = known_spacecraft_id
                    else:
                        body_id = cspyce.bodn2c(token)
                    ra, dec = body_radec(et, body_id)
            except Exception:
                continue
            star_ras.append(ra)
            star_decs.append(dec)
            star_names.append(token)

        draw_options = DrawPlanetaryViewOptions(
            obs_time=et,
            fov=fov_rad,
            center_ra=center_ra_rad,
            center_dec=center_dec_rad,
            planet_name=cfg.planet_name,
            blank_disks=blank_disks,
            prime_pts=meridian_points,
            nmoons=f_nmoons,
            moon_flags=f_moon_flags,
            moon_ids=f_moon_ids,
            moon_names=f_moon_names,
            moon_labelpts=_label_points_from_selection(labels),
            moon_diampts=moon_points,
            nrings=f_nrings,
            ring_flags=f_ring_flags,
            ring_rads=f_ring_rads,
            ring_elevs=f_ring_elevs,
            ring_eccs=f_ring_eccs,
            ring_incs=f_ring_incs,
            ring_peris=f_ring_peris,
            ring_nodes=f_ring_nodes,
            ring_offsets=f_ring_offsets,
            ring_opaqs=f_ring_opaqs,
            ring_dashed=f_ring_dashed,
            ring_method=_ring_method_from_opacity(opacity),
            narcs=f_narcs,
            arc_flags=f_arc_flags,
            arc_rings=f_arc_rings,
            arc_minlons=f_arc_minlons,
            arc_maxlons=f_arc_maxlons,
            arc_width=peripts if (planet_num in (6, 7) and f_narcs > 0) else arcpts,
            nstars=len(star_ras),
            star_ras=star_ras,
            star_decs=star_decs,
            star_names=star_names,
            star_labels=_label_points_from_selection(labels) > 0.0,
            title=title,
            ncaptions=ncaptions,
            lcaptions=lc,
            rcaptions=rc,
            align_loc=DEFAULT_ALIGN_LOC_POINTS,
        )
        draw_planetary_view(output_ps, draw_options)
