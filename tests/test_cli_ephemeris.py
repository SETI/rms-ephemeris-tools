"""Tests for simplified ephemeris CLI argument parsing."""

from __future__ import annotations

import sys
from typing import Any

from ephemeris_tools.cli import main as cli_main


def test_cli_ephemeris_observer_and_moons(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    """Ephemeris CLI accepts --observer and moon names/NAIF IDs."""
    captured: dict[str, Any] = {}

    def _fake_generate(params, *_args, **_kwargs):  # type: ignore[no-untyped-def]
        captured['value'] = params
        return None

    monkeypatch.setattr('ephemeris_tools.ephemeris.generate_ephemeris', _fake_generate)
    monkeypatch.setattr(
        'ephemeris_tools.input_params.write_input_parameters_ephemeris',
        lambda *_: None,
    )
    monkeypatch.setattr(
        sys,
        'argv',
        [
            'ephemeris-tools',
            'ephemeris',
            '--planet',
            'neptune',
            '--start',
            '2025-01-01 00:00',
            '--stop',
            '2025-01-02 00:00',
            '--observer',
            'earth',
            '--moons',
            'triton',
            '802',
        ],
    )
    rc = cli_main.main()
    assert rc == 0
    params = captured['value']
    assert params.planet_num == 8
    assert params.observer.name == "Earth's Center"
    assert params.moon_ids == [801, 802]
