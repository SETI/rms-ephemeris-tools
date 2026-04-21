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


def test_cli_viewer_backend_mpl_sets_output_image(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Viewer --backend mpl (default) stores output path as output_image, not output_ps."""
    captured: dict = {}

    monkeypatch.setattr('ephemeris_tools.cli.main.run_viewer', lambda p: captured.update(value=p))
    monkeypatch.setattr(
        'ephemeris_tools.input_params.write_input_parameters_viewer', lambda *_: None
    )
    monkeypatch.setattr(
        sys,
        'argv',
        [
            'ephemeris-tools', 'viewer',
            '--planet', 'saturn',
            '--time', '2025-01-01 12:00',
            '-o', '/tmp/viewer_test.png',
        ],
    )
    rc = cli_main.main()
    assert rc == 0
    params = captured['value']
    assert params.backend == 'mpl'
    assert params.output_image == '/tmp/viewer_test.png'
    assert params.output_ps is None


def test_cli_viewer_backend_escher_opens_output_ps(
    monkeypatch, tmp_path  # type: ignore[no-untyped-def]
) -> None:
    """Viewer --backend escher opens output as a text file for PostScript."""
    captured: dict = {}

    monkeypatch.setattr('ephemeris_tools.cli.main.run_viewer', lambda p: captured.update(value=p))
    monkeypatch.setattr(
        'ephemeris_tools.input_params.write_input_parameters_viewer', lambda *_: None
    )
    ps_path = str(tmp_path / 'viewer_test.ps')
    monkeypatch.setattr(
        sys,
        'argv',
        [
            'ephemeris-tools', 'viewer',
            '--planet', 'saturn',
            '--time', '2025-01-01 12:00',
            '--backend', 'escher',
            '-o', ps_path,
        ],
    )
    rc = cli_main.main()
    assert rc == 0
    params = captured['value']
    assert params.backend == 'escher'
    assert params.output_ps is not None
    assert params.output_image is None


def test_cli_viewer_dpi_forwarded_to_params(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Viewer --dpi value is stored in params.dpi."""
    captured: dict = {}

    monkeypatch.setattr('ephemeris_tools.cli.main.run_viewer', lambda p: captured.update(value=p))
    monkeypatch.setattr(
        'ephemeris_tools.input_params.write_input_parameters_viewer', lambda *_: None
    )
    monkeypatch.setattr(
        sys,
        'argv',
        [
            'ephemeris-tools', 'viewer',
            '--planet', 'saturn',
            '--time', '2025-01-01 12:00',
            '--dpi', '300',
        ],
    )
    rc = cli_main.main()
    assert rc == 0
    assert captured['value'].dpi == 300
