"""Tests for simplified tracker CLI argument parsing."""

from __future__ import annotations

import sys
from typing import Any

from ephemeris_tools.cli import main as cli_main


def test_cli_tracker_simplified_args(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Tracker CLI accepts simplified --observer and moon/ring names."""
    captured: dict[str, Any] = {}

    def _fake_run_tracker(params_or_planet, *args, **kwargs):  # type: ignore[no-untyped-def]
        captured['value'] = params_or_planet
        return None

    monkeypatch.setattr('ephemeris_tools.cli.main.run_tracker', _fake_run_tracker)
    monkeypatch.setattr(
        'ephemeris_tools.input_params.write_input_parameters_tracker',
        lambda *_: None,
    )
    monkeypatch.setattr(
        sys,
        'argv',
        [
            'ephemeris-tools',
            'tracker',
            '--planet',
            'saturn',
            '--start',
            '2025-01-01 00:00',
            '--stop',
            '2025-01-02 00:00',
            '--observer',
            'earth',
            '--moons',
            'mimas',
            '602',
            '--rings',
            'main',
            'gossamer',
        ],
    )
    rc = cli_main.main()
    assert rc == 0
    params = captured['value']
    assert params.planet_num == 6
    assert params.observer.name == "Earth's center"
    assert 601 in params.moon_ids


def test_cli_tracker_backend_mpl_sets_output_image(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Tracker --backend mpl (default) stores output path as output_image."""
    captured: dict = {}

    monkeypatch.setattr('ephemeris_tools.cli.main.run_tracker', lambda p: captured.update(value=p))
    monkeypatch.setattr(
        'ephemeris_tools.input_params.write_input_parameters_tracker', lambda *_: None
    )
    monkeypatch.setattr(
        sys,
        'argv',
        [
            'ephemeris-tools', 'tracker',
            '--planet', 'saturn',
            '--start', '2025-01-01 00:00',
            '--stop', '2025-01-02 00:00',
            '-o', '/tmp/tracker_test.png',
        ],
    )
    rc = cli_main.main()
    assert rc == 0
    params = captured['value']
    assert params.backend == 'mpl'
    assert params.output_image == '/tmp/tracker_test.png'
    assert params.output_ps is None


def test_cli_tracker_backend_escher_opens_output_ps(
    monkeypatch, tmp_path  # type: ignore[no-untyped-def]
) -> None:
    """Tracker --backend escher opens output as a text file for PostScript."""
    captured: dict = {}

    monkeypatch.setattr('ephemeris_tools.cli.main.run_tracker', lambda p: captured.update(value=p))
    monkeypatch.setattr(
        'ephemeris_tools.input_params.write_input_parameters_tracker', lambda *_: None
    )
    ps_path = str(tmp_path / 'tracker_test.ps')
    monkeypatch.setattr(
        sys,
        'argv',
        [
            'ephemeris-tools', 'tracker',
            '--planet', 'saturn',
            '--start', '2025-01-01 00:00',
            '--stop', '2025-01-02 00:00',
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


def test_cli_tracker_dpi_forwarded_to_params(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Tracker --dpi value is stored in params.dpi."""
    captured: dict = {}

    monkeypatch.setattr('ephemeris_tools.cli.main.run_tracker', lambda p: captured.update(value=p))
    monkeypatch.setattr(
        'ephemeris_tools.input_params.write_input_parameters_tracker', lambda *_: None
    )
    monkeypatch.setattr(
        sys,
        'argv',
        [
            'ephemeris-tools', 'tracker',
            '--planet', 'saturn',
            '--start', '2025-01-01 00:00',
            '--stop', '2025-01-02 00:00',
            '--dpi', '72',
        ],
    )
    rc = cli_main.main()
    assert rc == 0
    assert captured['value'].dpi == 72
