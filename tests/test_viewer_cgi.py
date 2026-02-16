"""Tests for viewer CGI environment parsing."""

from __future__ import annotations

from ephemeris_tools.params import viewer_params_from_env


def test_viewer_params_from_env_basic(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Viewer CGI env parses into ViewerParams."""
    monkeypatch.setenv('NPLANET', '8')
    monkeypatch.setenv('time', '2025-01-01 12:00')
    monkeypatch.setenv('fov', '3')
    monkeypatch.setenv('fov_unit', 'Neptune radii')
    monkeypatch.setenv('center', 'body')
    monkeypatch.setenv('center_body', 'Neptune')
    monkeypatch.setenv('viewpoint', 'observatory')
    monkeypatch.setenv('observatory', "Earth's Center")
    monkeypatch.setenv('moons', '802 Triton & Nereid')
    monkeypatch.setenv('rings', 'LeVerrier, Adams')
    params = viewer_params_from_env()
    assert params is not None
    assert params.planet_num == 8
    assert params.time_str == '2025-01-01 12:00'
    assert params.fov_value == 3.0
    assert params.fov_unit == 'Neptune radii'
    assert params.center.mode == 'body'
    assert params.center.body_name == 'Neptune'
    assert params.moon_ids == [802]
    assert params.ring_names == ['LeVerrier', 'Adams']
