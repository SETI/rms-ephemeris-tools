"""Tests for parameter dataclasses used by CLI/CGI/backend layers."""

from __future__ import annotations

from ephemeris_tools.params import (
    EphemerisParams,
    ExtraStar,
    Observer,
    TrackerParams,
    ViewerCenter,
    ViewerDisplayInfo,
    ViewerParams,
)


def test_observer_defaults() -> None:
    """Observer defaults are None/0 as expected."""
    observer = Observer()
    assert observer.name is None
    assert observer.latitude_deg is None
    assert observer.longitude_deg is None
    assert observer.altitude_m is None
    assert observer.sc_trajectory == 0


def test_viewer_center_defaults() -> None:
    """ViewerCenter defaults to body mode and all optional fields unset."""
    center = ViewerCenter()
    assert center.mode == 'body'
    assert center.body_name is None
    assert center.ansa_name is None
    assert center.ansa_ew is None
    assert center.ra_deg is None
    assert center.dec_deg is None
    assert center.star_name is None


def test_extra_star_defaults() -> None:
    """ExtraStar has deterministic empty defaults."""
    star = ExtraStar()
    assert star.name == ''
    assert star.ra_deg == 0.0
    assert star.dec_deg == 0.0


def test_viewer_display_info_defaults() -> None:
    """ViewerDisplayInfo stores optional display-only strings."""
    display = ViewerDisplayInfo()
    assert display.ephem_display is None
    assert display.moons_display is None
    assert display.rings_display is None


def test_viewer_params_defaults() -> None:
    """ViewerParams default values are stable and explicit."""
    params = ViewerParams(planet_num=6, time_str='2025-01-01 12:00')
    assert params.planet_num == 6
    assert params.time_str == '2025-01-01 12:00'
    assert params.fov_value == 1.0
    assert params.fov_unit == 'degrees'
    assert params.center.mode == 'body'
    assert params.observer.name is None
    assert params.ephem_version == 0
    assert params.moon_ids is None
    assert params.ring_names is None
    assert params.blank_disks is False
    assert params.opacity == 'Transparent'
    assert params.labels == 'Small (6 points)'
    assert params.moonpts == 0.0
    assert params.peris == 'None'
    assert params.peripts == 4.0
    assert params.meridians is False
    assert params.arcmodel is None
    assert params.arcpts == 4.0
    assert params.show_standard_stars is False
    assert params.extra_star is None
    assert params.other_bodies is None
    assert params.torus is False
    assert params.torus_inc == 6.8
    assert params.torus_rad == 422000.0
    assert params.title == ''
    assert params.display is None
    assert params.output_ps is None
    assert params.output_txt is None


def test_tracker_params_defaults() -> None:
    """TrackerParams default values are stable and explicit."""
    params = TrackerParams(
        planet_num=6,
        start_time='2025-01-01 00:00',
        stop_time='2025-01-02 00:00',
    )
    assert params.planet_num == 6
    assert params.start_time == '2025-01-01 00:00'
    assert params.stop_time == '2025-01-02 00:00'
    assert params.interval == 1.0
    assert params.time_unit == 'hours'
    assert params.observer.name is None
    assert params.ephem_version == 0
    assert params.moon_ids == []
    assert params.ring_names is None
    assert params.xrange is None
    assert params.xunit == 'arcsec'
    assert params.title == ''
    assert params.output_ps is None
    assert params.output_txt is None


def test_ephemeris_params_has_observer() -> None:
    """EphemerisParams includes nested Observer for shared API consistency."""
    params = EphemerisParams(
        planet_num=6,
        start_time='2025-01-01 00:00',
        stop_time='2025-01-01 02:00',
    )
    assert params.observer is not None
    assert params.observer.name is None
