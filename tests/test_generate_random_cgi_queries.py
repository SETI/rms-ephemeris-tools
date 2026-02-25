"""Tests for scripts/generate_random_cgi_queries.py."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest


def _load_generator_module() -> ModuleType:
    """Load generate_random_cgi_queries as a module from scripts/."""
    script = Path(__file__).resolve().parent.parent / 'scripts' / 'generate_random_cgi_queries.py'
    spec = importlib.util.spec_from_file_location('generate_random_cgi_queries', script)
    assert spec is not None
    assert spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_generate_one_url_viewer() -> None:
    """Viewer URL is full pds-rings URL and contains mandatory params."""
    mod = _load_generator_module()
    mod.random.seed(123)
    url = mod.generate_one_url('viewer')
    assert url.startswith('https://pds-rings.seti.org/cgi-bin/tools/viewer3_xxx.pl?')
    assert 'abbrev=' in url
    assert 'time=' in url
    assert 'fov=' in url
    assert 'fov_unit=' in url
    assert '&' in url
    assert '\n' not in url


def test_generate_one_url_tracker() -> None:
    """Tracker URL is full pds-rings URL and contains start, stop, interval."""
    mod = _load_generator_module()
    mod.random.seed(456)
    url = mod.generate_one_url('tracker')
    assert url.startswith('https://pds-rings.seti.org/cgi-bin/tools/tracker3_xxx.pl?')
    assert 'abbrev=' in url
    assert 'start=' in url
    assert 'stop=' in url
    assert 'interval=' in url
    assert 'time_unit=' in url
    assert '\n' not in url


def test_generate_one_url_ephemeris() -> None:
    """Ephemeris URL is full pds-rings URL and contains start, stop, interval."""
    mod = _load_generator_module()
    mod.random.seed(789)
    url = mod.generate_one_url('ephemeris')
    assert url.startswith('https://pds-rings.seti.org/cgi-bin/tools/ephem3_xxx.pl?')
    assert 'abbrev=' in url
    assert 'start=' in url
    assert 'stop=' in url
    assert 'interval=' in url
    assert '\n' not in url


def test_generate_one_url_invalid_tool_raises() -> None:
    """Unknown tool raises ValueError."""
    mod = _load_generator_module()
    with pytest.raises(ValueError, match='Unknown tool'):
        mod.generate_one_url('invalid')


def test_cli_writes_count_lines(tmp_path: Path) -> None:
    """CLI -n N -o FILE writes exactly N full URLs per line."""
    out = tmp_path / 'urls.txt'
    script = Path(__file__).resolve().parent.parent / 'scripts' / 'generate_random_cgi_queries.py'
    result = subprocess.run(
        [sys.executable, str(script), '-n', '7', '-o', str(out), '--seed', '1'],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    lines = out.read_text().strip().splitlines()
    assert len(lines) == 7
    for line in lines:
        assert line.startswith('https://pds-rings.seti.org/cgi-bin/tools/')
        assert '?' in line
        assert '=' in line
        assert '\n' not in line.strip()


def test_cli_tool_filter(tmp_path: Path) -> None:
    """CLI --tool viewer produces only viewer full URLs (time, fov, viewer3 path)."""
    out = tmp_path / 'viewer_only.txt'
    script = Path(__file__).resolve().parent.parent / 'scripts' / 'generate_random_cgi_queries.py'
    result = subprocess.run(
        [sys.executable, str(script), '-n', '3', '-o', str(out), '--tool', 'viewer', '--seed', '2'],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0
    lines = out.read_text().strip().splitlines()
    assert len(lines) == 3
    for line in lines:
        assert line.startswith('https://pds-rings.seti.org/cgi-bin/tools/viewer3_xxx.pl?')
        assert 'time=' in line
        assert 'fov=' in line
        assert 'version=3.1' in line
