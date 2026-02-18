"""Tests for viewer backend parameter adaptation."""

from __future__ import annotations

from ephemeris_tools.params import (
    ExtraStar,
    Observer,
    ViewerCenter,
    ViewerDisplayInfo,
    ViewerParams,
)
from ephemeris_tools.planets import (
    JUPITER_CONFIG,
    MARS_CONFIG,
    NEPTUNE_CONFIG,
    PLUTO_CONFIG,
    SATURN_CONFIG,
    URANUS_CONFIG,
)
from ephemeris_tools.viewer import (
    _fov_deg_from_unit,
    _resolve_center_ansa_radius_km,
    _resolve_viewer_ring_flags,
    _viewer_call_kwargs_from_params,
)


def test_viewer_call_kwargs_from_params_j2000_center() -> None:
    """ViewerParams with J2000 center maps to legacy kwargs correctly."""
    params = ViewerParams(
        planet_num=8,
        time_str='2025-01-01 12:00',
        fov_value=3.0,
        fov_unit='degrees',
        center=ViewerCenter(mode='J2000', ra_deg=12.5, dec_deg=-30.0),
        observer=Observer(name='JWST'),
        ephem_version=0,
        moon_ids=[801, 802],
        ring_names=['LeVerrier', 'Adams'],
        blank_disks=True,
    )
    kwargs = _viewer_call_kwargs_from_params(params)
    assert kwargs['planet_num'] == 8
    assert kwargs['time_str'] == '2025-01-01 12:00'
    assert kwargs['fov'] == 3.0
    assert kwargs['fov_unit'] == 'degrees'
    assert kwargs['center_ra'] == 12.5
    assert kwargs['center_dec'] == -30.0
    assert kwargs['viewpoint'] == 'JWST'
    assert kwargs['moon_ids'] == [801, 802]
    assert kwargs['ring_selection'] == ['LeVerrier', 'Adams']
    assert kwargs['blank_disks'] is True


def test_viewer_call_kwargs_from_params_defaults_body_center() -> None:
    """Non-J2000 center falls back to planet-centered legacy coordinates."""
    params = ViewerParams(
        planet_num=6,
        time_str='2025-01-01 12:00',
        center=ViewerCenter(mode='body', body_name='Saturn'),
        observer=Observer(name=None),
    )
    kwargs = _viewer_call_kwargs_from_params(params)
    assert kwargs['center_ra'] == 0.0
    assert kwargs['center_dec'] == 0.0
    assert kwargs['viewpoint'] == 'Earth'


def test_resolve_viewer_ring_flags_mars_phobos_group() -> None:
    """Mars 'Phobos' ring selection enables the first ring pair."""
    flags = _resolve_viewer_ring_flags(4, ['Phobos'], MARS_CONFIG.rings)
    assert flags == [True, True, False, False]


def test_resolve_viewer_ring_flags_mars_both_groups() -> None:
    """Mars 'Phobos, Deimos' selection enables both ring pairs."""
    flags = _resolve_viewer_ring_flags(4, ['Phobos', 'Deimos'], MARS_CONFIG.rings)
    assert flags == [True, True, True, True]


def test_resolve_viewer_ring_flags_pluto_named_orbits() -> None:
    """Pluto orbit names select the expected ring indices."""
    flags = _resolve_viewer_ring_flags(9, ['Charon', 'Kerberos'], PLUTO_CONFIG.rings)
    assert flags == [True, False, False, True, False]


def test_resolve_viewer_ring_flags_uranus_nine_major_group() -> None:
    """Uranus rings include defaults plus explicit Nine-major selections."""
    flags = _resolve_viewer_ring_flags(7, ['Nine major rings'], URANUS_CONFIG.rings)
    expected = [False] * len(URANUS_CONFIG.rings)
    for i in (3, 4, 5, 6, 7, 9, 10):
        expected[i] = True
    expected[0] = True
    expected[1] = True
    expected[2] = True
    assert flags == expected


def test_resolve_viewer_ring_flags_uranus_all_inner_group() -> None:
    """Uranus all-inner adds 1,2,3,9 to the FORTRAN default ring baseline."""
    flags = _resolve_viewer_ring_flags(7, ['All inner rings'], URANUS_CONFIG.rings)
    expected = [False] * len(URANUS_CONFIG.rings)
    for i in (3, 4, 5, 6, 7, 9, 10):
        expected[i] = True
    expected[0] = True
    expected[1] = True
    expected[2] = True
    expected[8] = True
    assert flags == expected


def test_resolve_viewer_ring_flags_saturn_abc_names() -> None:
    """Saturn A/B/C names keep the first five FORTRAN rings enabled."""
    flags = _resolve_viewer_ring_flags(6, ['A', 'B', 'C'], SATURN_CONFIG.rings)
    expected = [False] * len(SATURN_CONFIG.rings)
    for i in range(5):
        expected[i] = True
    assert flags == expected


def test_viewer_call_kwargs_from_params_latlon_observer() -> None:
    """Lat/lon observers are passed through to run_viewer kwargs."""
    params = ViewerParams(
        planet_num=4,
        time_str='2025-01-01 12:00',
        observer=Observer(
            latitude_deg=33.0,
            longitude_deg=-116.0,
            lon_dir='west',
            altitude_m=1000.0,
        ),
    )
    kwargs = _viewer_call_kwargs_from_params(params)
    assert kwargs['viewpoint'] == 'latlon'
    assert kwargs['observer_latitude'] == 33.0
    assert kwargs['observer_longitude'] == -116.0
    assert kwargs['observer_lon_dir'] == 'west'
    assert kwargs['observer_altitude'] == 1000.0


def test_viewer_call_kwargs_from_params_passes_label_and_moon_points() -> None:
    """Viewer label and moon-point settings are forwarded to backend kwargs."""
    params = ViewerParams(
        planet_num=4,
        time_str='2025-01-01 12:00',
        labels='Large (12 points)',
        moonpts=2.5,
    )
    kwargs = _viewer_call_kwargs_from_params(params)
    assert kwargs['labels'] == 'Large (12 points)'
    assert kwargs['moon_points'] == 2.5


def test_viewer_call_kwargs_from_params_passes_meridian_points() -> None:
    """Meridian toggle maps to FORTRAN-equivalent prime meridian line width."""
    params = ViewerParams(
        planet_num=4,
        time_str='2025-01-01 12:00',
        meridians=True,
    )
    kwargs = _viewer_call_kwargs_from_params(params)
    assert kwargs['meridian_points'] == 1.3


def test_viewer_call_kwargs_from_params_passes_title() -> None:
    """Viewer title text is forwarded to backend kwargs."""
    params = ViewerParams(
        planet_num=4,
        time_str='2025-01-01 12:00',
        title='Hubble Closest View',
    )
    kwargs = _viewer_call_kwargs_from_params(params)
    assert kwargs['title'] == 'Hubble Closest View'


def test_viewer_call_kwargs_from_params_passes_moon_display_text() -> None:
    """Raw CGI moon selection text is forwarded for caption parity."""
    params = ViewerParams(
        planet_num=7,
        time_str='2025-01-01 12:00',
        display=ViewerDisplayInfo(moons_display='727 All inner moons (U1-U15,U25-U27)'),
    )
    kwargs = _viewer_call_kwargs_from_params(params)
    assert kwargs['moon_selection_display'] == '727 All inner moons (U1-U15,U25-U27)'


def test_resolve_center_ansa_radius_neptune_named_ring() -> None:
    """Neptune center ansa names map to FORTRAN ring-index radii."""
    radius = _resolve_center_ansa_radius_km(NEPTUNE_CONFIG, 'LeVerrier Ring')
    assert radius == 53200.0


def test_resolve_center_ansa_radius_jupiter_named_ring() -> None:
    """Jupiter named ansa ring maps to FORTRAN-equivalent radius."""
    radius = _resolve_center_ansa_radius_km(JUPITER_CONFIG, 'Main Ring')
    assert radius == 129000.0


def test_viewer_call_kwargs_from_params_passes_extra_star() -> None:
    """Extra star data is forwarded to run_viewer kwargs."""
    params = ViewerParams(
        planet_num=9,
        time_str='2025-01-01 12:00',
        extra_star=ExtraStar(
            name='Occulted Star',
            ra_deg=290.5,
            dec_deg=-21.98,
        ),
    )
    kwargs = _viewer_call_kwargs_from_params(params)
    assert kwargs['extra_star_name'] == 'Occulted Star'
    assert kwargs['extra_star_ra_deg'] == 290.5
    assert kwargs['extra_star_dec_deg'] == -21.98


def test_viewer_call_kwargs_from_params_passes_other_bodies() -> None:
    """Other background bodies are forwarded to run_viewer kwargs."""
    params = ViewerParams(
        planet_num=7,
        time_str='2025-01-01 12:00',
        other_bodies=['Sun', 'Anti-Sun'],
    )
    kwargs = _viewer_call_kwargs_from_params(params)
    assert kwargs['other_bodies'] == ['Sun', 'Anti-Sun']


def test_viewer_call_kwargs_from_params_prefers_observatory_name_over_latlon() -> None:
    """Observatory names with embedded coords should stay in viewpoint caption."""
    params = ViewerParams(
        planet_num=5,
        time_str='2025-01-01 12:00',
        observer=Observer(
            name='Yerkes Observatory (41.098, 88.557, 334.)',
            latitude_deg=41.098,
            longitude_deg=88.557,
            altitude_m=334.0,
        ),
    )
    kwargs = _viewer_call_kwargs_from_params(params)
    assert kwargs['viewpoint'] == 'Yerkes Observatory (41.098, 88.557, 334.)'


def test_viewer_call_kwargs_from_params_passes_viewpoint_display() -> None:
    """Preformatted lat/lon viewpoint caption is forwarded."""
    params = ViewerParams(
        planet_num=9,
        time_str='2025-01-01 12:00',
        display=ViewerDisplayInfo(viewpoint_display='(33.2319835, -116.7600221 east, 844)'),
    )
    kwargs = _viewer_call_kwargs_from_params(params)
    assert kwargs['viewpoint_display'] == '(33.2319835, -116.7600221 east, 844)'


def test_fov_deg_from_unit_voyager_wide_matches_fortran_constant() -> None:
    """Voyager ISS wide-angle unit matches FORTRAN radian multiplier."""
    fov_deg = _fov_deg_from_unit(1.0, 'Voyager ISS wide angle FOVs')
    assert abs(fov_deg - 3.130068434799687) < 1e-12
