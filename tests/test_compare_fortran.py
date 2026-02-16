"""Tests for the FORTRAN vs Python comparison framework."""

from __future__ import annotations

import tempfile
import urllib.parse
from pathlib import Path

import pytest

from tests.compare_fortran import RunSpec, compare_postscript, compare_tables, run_python
from tests.compare_fortran.spec import (
    VIEWER_DEFAULT_RINGS,
    VIEWER_RING_CODE_TO_FORM,
    VIEWER_VALID_RING_FORMS,
)


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
    parsed = urllib.parse.parse_qs(env['QUERY_STRING'])
    assert 'start' in parsed
    assert parsed['start'][0] == '2022-01-01 00:00'
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


def test_compare_tables_ignore_column_suffixes() -> None:
    """compare_tables with ignore_column_suffixes treats ignored columns as matching."""
    # Tables differ only in MIMA_orbit and MIMA_open (known FORTRAN bug); rest match.
    table_a = 'mjd phase MIMA_ra MIMA_dec MIMA_orbit MIMA_open\n1.0 5.0 1.1 2.2 100.0 3.14\n'
    table_b = 'mjd phase MIMA_ra MIMA_dec MIMA_orbit MIMA_open\n1.0 5.0 1.1 2.2 99.0 3.00\n'
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(table_a)
        path_a = Path(f.name)
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(table_b)
        path_b = Path(f.name)
    try:
        res = compare_tables(
            path_a,
            path_b,
            ignore_column_suffixes=('_orbit', '_open'),
        )
        assert res.same is True
        res_strict = compare_tables(path_a, path_b)
        assert res_strict.same is False
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


def test_query_string_jupiter_moon_cgi_format() -> None:
    """QUERY_STRING uses CGI format for Jupiter moons (NNN Name (Jn))."""
    spec = RunSpec(
        'tracker',
        {'planet': 5, 'start': '2022-01-01', 'stop': '2022-01-02', 'moons': [1, 2]},
    )
    env = spec.env_for_fortran()
    parsed = urllib.parse.parse_qs(env['QUERY_STRING'])
    assert parsed.get('moons') == ['001 Io (J1)', '002 Europa (J2)']


def test_query_string_mars_moon_cgi_format() -> None:
    """QUERY_STRING uses CGI format for Mars moons (NNN Name (Mn))."""
    spec = RunSpec(
        'tracker',
        {'planet': 4, 'start': '2022-01-01', 'stop': '2022-01-02', 'moons': [1, 2]},
    )
    env = spec.env_for_fortran()
    parsed = urllib.parse.parse_qs(env['QUERY_STRING'])
    assert parsed.get('moons') == ['001 Phobos (M1)', '002 Deimos (M2)']


def test_query_string_column_cgi_format() -> None:
    """QUERY_STRING uses CGI format for ephemeris columns (NNN Description)."""
    spec = RunSpec(
        'ephemeris',
        {
            'planet': 6,
            'start': '2022-01-01',
            'stop': '2022-01-02',
            'columns': [1, 3],
        },
    )
    env = spec.env_for_fortran()
    parsed = urllib.parse.parse_qs(env['QUERY_STRING'])
    assert parsed.get('columns') == [
        '001 Modified Julian Date',
        '003 Year, Month, Day, Hour, Minute, Second',
    ]


def test_query_string_mooncol_cgi_format() -> None:
    """QUERY_STRING uses CGI format for moon columns (NNN Description)."""
    spec = RunSpec(
        'ephemeris',
        {
            'planet': 6,
            'start': '2022-01-01',
            'stop': '2022-01-02',
            'mooncols': [5, 8],
        },
    )
    env = spec.env_for_fortran()
    parsed = urllib.parse.parse_qs(env['QUERY_STRING'])
    assert parsed.get('mooncols') == [
        '005 RA & Dec',
        '008 Orbital longitude relative to observer',
    ]


def test_query_string_tracker_ring_cgi_format() -> None:
    """QUERY_STRING uses CGI format for tracker rings (NNN Description)."""
    spec = RunSpec(
        'tracker',
        {
            'planet': 6,
            'start': '2022-01-01',
            'stop': '2022-01-02',
            'rings': [61, 62],
        },
    )
    env = spec.env_for_fortran()
    parsed = urllib.parse.parse_qs(env['QUERY_STRING'])
    assert parsed.get('rings') == ['061 Main Rings', '062 G Ring']


def test_query_string_viewer_has_no_start_stop() -> None:
    """Viewer QUERY_STRING does not include start/stop (viewer uses only time=)."""
    spec = RunSpec(
        'viewer',
        {'planet': 6, 'time': '2022-01-01 12:00', 'moons': [1]},
    )
    env = spec.env_for_fortran()
    parsed = urllib.parse.parse_qs(env['QUERY_STRING'])
    assert 'start' not in parsed
    assert 'stop' not in parsed
    assert 'time' in parsed


def test_query_string_viewer_single_moons_cutoff() -> None:
    """Viewer QUERY_STRING sends a single moons= entry (cutoff), not one per moon."""
    spec = RunSpec(
        'viewer',
        {
            'planet': 6,
            'time': '2022-01-01 12:00',
            'moons': [1, 3, 2],
        },
    )
    env = spec.env_for_fortran()
    parsed = urllib.parse.parse_qs(env['QUERY_STRING'])
    moons = parsed.get('moons')
    assert moons is not None
    assert len(moons) == 1
    assert moons[0].startswith('003 ')
    assert 'Tethys' in moons[0]
    assert '(S3)' in moons[0]


def test_cli_args_viewer_includes_moons() -> None:
    """cli_args_for_python() includes --moons for viewer tool."""
    spec = RunSpec(
        'viewer',
        {'planet': 6, 'time': '2022-01-01 12:00', 'moons': [1, 2]},
    )
    args = spec.cli_args_for_python()
    assert '--moons' in args
    idx = args.index('--moons')
    assert args[idx + 1 : idx + 3] == ['1', '2']


def test_viewer_ring_defaults_match_fortran_form_values() -> None:
    """VIEWER_DEFAULT_RINGS and VIEWER_RING_CODE_TO_FORM use only FORTRAN-valid form values."""
    for planet, default in VIEWER_DEFAULT_RINGS.items():
        valid = VIEWER_VALID_RING_FORMS.get(planet, frozenset())
        assert default in valid, (
            f'planet {planet}: default {default!r} not in VIEWER_VALID_RING_FORMS'
        )
    for planet, code_map in VIEWER_RING_CODE_TO_FORM.items():
        valid = VIEWER_VALID_RING_FORMS.get(planet, frozenset())
        for code, form_value in code_map.items():
            assert form_value in valid, (
                f'planet {planet} code {code}: {form_value!r} not in VIEWER_VALID_RING_FORMS'
            )


def test_viewer_ring_codes_cover_python_ring_names() -> None:
    """Every Python --rings name/code (params.RING_NAME_TO_CODE) has a viewer
    form mapping where applicable."""
    from ephemeris_tools.params import RING_NAME_TO_CODE

    for planet, name_to_code in RING_NAME_TO_CODE.items():
        code_to_form = VIEWER_RING_CODE_TO_FORM.get(planet)
        if code_to_form is None:
            continue
        for _name, code in name_to_code.items():
            assert code in code_to_form, (
                f'planet {planet} ring code {code} from params has no '
                'VIEWER_RING_CODE_TO_FORM entry'
            )
