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
    assert params.observer.name == "Earth's Center"
    assert 601 in params.moon_ids
