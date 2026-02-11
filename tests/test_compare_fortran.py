"""Tests for the FORTRAN vs Python comparison framework."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from tests.compare_fortran import RunSpec, compare_postscript, compare_tables, run_python


def test_run_spec_env_and_cli() -> None:
    """RunSpec builds env (QUERY_STRING + GetEnv vars) and CLI args consistently."""
    spec = RunSpec(
        'ephemeris',
        {
            'planet': 6,
            'start': '2022-01-01 00:00',
            'stop': '2022-01-02 00:00',
            'interval': 1.0,
            'time_unit': 'hour',
        },
    )
    env = spec.env_for_fortran(table_path='/tmp/out.tab')
    assert env['REQUEST_METHOD'] == 'GET'
    assert 'QUERY_STRING' in env
    assert 'start=2022-01-01%2000%3A00' in env['QUERY_STRING'] or 'start=' in env['QUERY_STRING']
    assert 'stop=' in env['QUERY_STRING']
    assert 'interval=1' in env['QUERY_STRING']
    assert env['NPLANET'] == '6'
    assert env['EPHEM_FILE'] == '/tmp/out.tab'
    args = spec.cli_args_for_python()
    assert 'ephemeris' in args
    assert '--planet' in args
    assert '6' in args


def test_run_python_ephemeris_produces_table() -> None:
    """Running Python ephemeris with spec writes a table file (skips if SPICE missing)."""
    spec = RunSpec(
        'ephemeris',
        {
            'planet': 6,
            'start': '2022-01-01 00:00',
            'stop': '2022-01-02 00:00',
            'interval': 12.0,
            'time_unit': 'hour',
        },
    )
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / 'ephem.txt'
        result = run_python(spec, out_table=out)
        if result.returncode != 0 and 'SPICE' in (result.stderr or ''):
            pytest.skip('SPICE kernels not configured')
        assert result.returncode == 0
        assert out.exists()
        text = out.read_text()
        assert 'mjd' in text or 'year' in text


def test_compare_tables_same() -> None:
    """compare_tables reports same for identical content."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write('a 1 2\nb 3 4\n')
        path_a = Path(f.name)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write('a 1 2\nb 3 4\n')
        path_b = Path(f.name)
    try:
        res = compare_tables(path_a, path_b)
        assert res.same is True
    finally:
        path_a.unlink()
        path_b.unlink()


def test_compare_tables_different() -> None:
    """compare_tables reports diff when content differs."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write('a 1 2\n')
        path_a = Path(f.name)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write('a 1 3\n')
        path_b = Path(f.name)
    try:
        res = compare_tables(path_a, path_b)
        assert res.same is False
        assert res.num_diffs >= 1
    finally:
        path_a.unlink()
        path_b.unlink()


def test_compare_postscript_normalizes_creator() -> None:
    """compare_postscript ignores Creator/Date so matching structure passes."""
    ps_a = (
        '%!PS-Adobe-2.0\n%%Creator: Python\n%%CreationDate: 2022-01-01\n'
        '0 0 moveto 100 0 lineto stroke\n%%EOF\n'
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ps', delete=False) as f:
        f.write(ps_a)
        path_a = Path(f.name)
    ps_b = (
        '%!PS-Adobe-2.0\n%%Creator: FORTRAN\n%%CreationDate: 1999-01-01\n'
        '0 0 moveto 100 0 lineto stroke\n%%EOF\n'
    )
    with tempfile.NamedTemporaryFile(mode='w', suffix='.ps', delete=False) as f:
        f.write(ps_b)
        path_b = Path(f.name)
    try:
        res = compare_postscript(path_a, path_b)
        assert res.same is True
    finally:
        path_a.unlink()
        path_b.unlink()
