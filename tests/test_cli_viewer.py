"""Tests for simplified viewer CLI argument parsing."""

from __future__ import annotations

import sys
from typing import Any

from ephemeris_tools.cli import main as cli_main


def test_cli_viewer_simplified_args(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Viewer CLI accepts simplified --fov/--center/--observer forms."""
    captured: dict[str, Any] = {}

    def _fake_run_viewer(params_or_planet, *args, **kwargs):  # type: ignore[no-untyped-def]
        captured['value'] = params_or_planet
        return None

    monkeypatch.setattr('ephemeris_tools.cli.main.run_viewer', _fake_run_viewer)
    monkeypatch.setattr(
        'ephemeris_tools.input_params.write_input_parameters_viewer',
        lambda *_: None,
    )
    monkeypatch.setattr(
        sys,
        'argv',
        [
            'ephemeris-tools',
            'viewer',
            '--planet',
            'neptune',
            '--time',
            '2025-01-01 12:00',
            '--fov',
            '3',
            'Neptune',
            'radii',
            '--center',
            'leverrier',
            'west',
            '--observer',
            '19.827',
            '-155.472',
            '4215',
            '--moons',
            'triton',
            '802',
            '--rings',
            'leverrier',
            'adams',
        ],
    )
    rc = cli_main.main()
    assert rc == 0
    params = captured['value']
    assert params.planet_num == 8
    assert params.fov_value == 3.0
    assert params.fov_unit == 'Neptune radii'
    assert params.center.mode == 'ansa'
