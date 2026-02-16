"""CLI to run Python and (optionally) FORTRAN with the same inputs and compare outputs.

The FORTRAN binary is auto-detected from repo_root/fortran/Tools/ (ephem3_xxx.bin,
tracker3_xxx.bin, or viewer3_<planet>.bin by tool and --planet). Use --fortran-cmd
to override.

Usage:
  python -m tests.compare_fortran ephemeris --planet saturn --start 2022-01-01 \\
    --stop 2022-01-02 -o /tmp/out
  python -m tests.compare_fortran tracker --planet 6 --start 2022-01-01 \\
    --stop 2022-01-03 -o /tmp/out
  python -m tests.compare_fortran viewer --planet saturn --time 2022-01-01 12:00 \\
    --fov 0.1 -o /tmp/out --moons mimas enceladus
  python -m tests.compare_fortran ephemeris ... --fortran-cmd /path/to/ephem3_xxx.bin -o /tmp/out

With a FORTRAN binary (auto-detected or --fortran-cmd): runs both, compares outputs.
Without: runs only Python and writes outputs (no comparison).
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from ephemeris_tools.params import (
    parse_column_spec,
    parse_mooncol_spec,
    parse_planet,
    parse_ring_spec,
)
from ephemeris_tools.planets import parse_moon_spec
from tests.compare_fortran.diff_utils import (
    compare_postscript,
    compare_postscript_images,
    compare_tables,
)
from tests.compare_fortran.runner import run_fortran, run_python
from tests.compare_fortran.spec import DEFAULT_TRACKER_MOONS_SATURN, RunSpec

# Planet number (4-9) -> viewer FORTRAN binary suffix (viewer3_<suffix>.bin).
_VIEWER_BINARY_SUFFIX: dict[int, str] = {
    4: 'mar',
    5: 'jup',
    6: 'sat',
    7: 'ura',
    8: 'nep',
    9: 'plu',
}

_ABBREV_TO_PLANET: dict[str, int] = {
    'mar': 4,
    'jup': 5,
    'sat': 6,
    'ura': 7,
    'nep': 8,
    'plu': 9,
}


def _tool_from_query_url(url_or_query: str) -> str:
    """Infer tool name from CGI URL path."""
    parsed = urlparse(url_or_query)
    path = parsed.path.lower()
    if 'ephem3_xxx' in path:
        return 'ephemeris'
    if 'tracker3_xxx' in path:
        return 'tracker'
    if 'viewer3_xxx' in path:
        return 'viewer'
    raise ValueError(f'Cannot infer tool from URL path: {parsed.path!r}')


def _parse_int_prefix(value: str) -> int | None:
    """Parse leading integer prefix from a CGI value like ``001 Io (J1)``."""
    value = value.strip()
    digits = ''
    for ch in value:
        if ch.isdigit():
            digits += ch
        else:
            break
    if not digits:
        return None
    return int(digits)


def _normalize_time_unit(value: str) -> str:
    """Normalize CGI time units to CLI choices."""
    lowered = value.strip().lower()
    if lowered.startswith('sec'):
        return 'sec'
    if lowered.startswith('min'):
        return 'min'
    if lowered.startswith('hour'):
        return 'hour'
    if lowered.startswith('day'):
        return 'day'
    return 'hour'


def spec_from_query_input(url_or_query: str) -> RunSpec:
    """Build RunSpec from a CGI URL or raw query string."""
    parsed = urlparse(url_or_query)
    raw_query = parsed.query if parsed.query else url_or_query
    qs = parse_qs(raw_query, keep_blank_values=True)
    tool = _tool_from_query_url(url_or_query) if parsed.query else 'ephemeris'
    if parsed.query == '':
        tool_key = qs.get('tool', [''])[0].strip().lower()
        if tool_key in {'ephemeris', 'tracker', 'viewer'}:
            tool = tool_key
    abbrev = qs.get('abbrev', ['sat'])[0].strip().lower()
    planet = _ABBREV_TO_PLANET.get(abbrev, 6)
    params: dict[str, Any] = {'planet': planet}

    ephem_vals = qs.get('ephem')
    if ephem_vals:
        ephem_int = _parse_int_prefix(ephem_vals[0])
        params['ephem'] = ephem_int if ephem_int is not None else 0

    if tool in {'ephemeris', 'tracker'}:
        params['start'] = qs.get('start', [''])[0]
        params['stop'] = qs.get('stop', [''])[0]
        interval_s = qs.get('interval', ['1'])[0]
        try:
            params['interval'] = float(interval_s)
        except ValueError:
            params['interval'] = 1.0
        params['time_unit'] = _normalize_time_unit(qs.get('time_unit', ['hour'])[0])
    if tool == 'viewer':
        params['time'] = qs.get('time', [''])[0]
        fov_s = qs.get('fov', ['1'])[0].replace(',', '')
        try:
            params['fov'] = float(fov_s)
        except ValueError:
            params['fov'] = 1.0
        params['fov_unit'] = qs.get('fov_unit', ['degrees'])[0]
        params['center'] = qs.get('center', ['body'])[0]
        params['center_body'] = qs.get('center_body', [''])[0]
        params['rings'] = qs.get('rings', [None])[0]
        params['title'] = qs.get('title', [''])[0]

    params['viewpoint'] = qs.get('viewpoint', ['observatory'])[0]
    params['observatory'] = qs.get('observatory', ["Earth's Center"])[0]
    params['lon_dir'] = qs.get('lon_dir', ['east'])[0]
    for key in ('latitude', 'longitude', 'altitude'):
        raw = qs.get(key, [''])[0]
        if raw.strip() == '':
            params[key] = None
        else:
            try:
                params[key] = float(raw)
            except ValueError:
                params[key] = None

    params['columns'] = []
    for value in qs.get('columns', []):
        col = _parse_int_prefix(value)
        if col is not None:
            params['columns'].append(col)

    params['mooncols'] = []
    for value in qs.get('mooncols', []):
        col = _parse_int_prefix(value)
        if col is not None:
            params['mooncols'].append(col)

    params['moons'] = []
    for value in qs.get('moons', []):
        moon = _parse_int_prefix(value)
        if moon is not None:
            params['moons'].append(moon)

    if tool == 'tracker':
        params['rings'] = []
        for value in qs.get('rings', []):
            ring = _parse_int_prefix(value)
            if ring is not None:
                params['rings'].append(ring)
        xrange_s = qs.get('xrange', [''])[0]
        try:
            params['xrange'] = float(xrange_s) if xrange_s else None
        except ValueError:
            params['xrange'] = None
        xunit_raw = qs.get('xunit', ['arcsec'])[0]
        params['xunit'] = 'radii' if 'radii' in xunit_raw.lower() else 'arcsec'
        params['title'] = qs.get('title', [''])[0]

    return RunSpec(tool=tool, params=params)


def _read_test_urls(test_file: Path) -> list[str]:
    """Read non-empty, non-comment URLs from a test file."""
    urls: list[str] = []
    for line in test_file.read_text().splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('#'):
            continue
        urls.append(stripped)
    return urls


def _default_fortran_binary(tool: str, planet: int, repo_root: Path) -> Path | None:
    """Return path to FORTRAN binary in repo_root/fortran/Tools/ if it exists and is executable."""
    if tool == 'ephemeris':
        name = 'ephem3_xxx.bin'
    elif tool == 'tracker':
        name = 'tracker3_xxx.bin'
    elif tool == 'viewer':
        suffix = _VIEWER_BINARY_SUFFIX.get(planet)
        if suffix is None:
            return None
        name = f'viewer3_{suffix}.bin'
    else:
        return None
    path = repo_root / 'fortran' / 'Tools' / name
    if path.is_file() and os.access(path, os.X_OK):
        return path
    return None


def _execute_spec(
    *,
    spec: RunSpec,
    out_dir: Path,
    fort_cmd: list[str] | None,
    float_tol: int,
) -> tuple[bool, list[str]]:
    """Execute one comparison spec and return (passed, detail lines)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    details: list[str] = [f'tool={spec.tool} planet={spec.params.get("planet", "?")}']

    py_table = out_dir / 'python_table.txt'
    py_ps = out_dir / 'python.ps'
    py_txt = out_dir / 'python_tracker.txt'
    fort_table = out_dir / 'fortran_table.txt'
    fort_ps = out_dir / 'fortran.ps'
    fort_txt = out_dir / 'fortran_tracker.txt'

    if spec.tool == 'ephemeris':
        py_table_use = py_table
        fort_table_use = fort_table
        py_ps_use = fort_ps_use = None
        py_txt_use = fort_txt_use = None
    elif spec.tool == 'tracker':
        py_table_use = None
        fort_table_use = None
        py_ps_use = py_ps
        fort_ps_use = fort_ps
        py_txt_use = py_txt
        fort_txt_use = fort_txt
    else:
        py_table_use = fort_table_use = None
        py_ps_use = py_ps
        fort_ps_use = fort_ps
        py_txt_use = py_txt
        fort_txt_use = fort_txt

    result_py = run_python(spec, out_table=py_table_use, out_ps=py_ps_use, out_txt=py_txt_use)
    if result_py.returncode != 0:
        details.append('python_failed')
        details.append((result_py.stderr or result_py.stdout or '').strip())
        return (False, details)

    if fort_cmd is None:
        details.append('fortran_skipped')
        return (True, details)

    result_fort = run_fortran(
        spec,
        fort_cmd,
        out_table=fort_table_use,
        out_ps=fort_ps_use,
        out_txt=fort_txt_use,
    )
    fort_stdout = result_fort.stdout or ''
    fort_failed = (
        result_fort.returncode != 0
        or 'Invalid value found for variable' in fort_stdout
        or 'Error---' in fort_stdout
    )
    if fort_failed:
        details.append('fortran_failed')
        details.append((result_fort.stderr or fort_stdout or '').strip())
        return (False, details)

    all_ok = True
    if py_table_use and fort_table_use:
        res = compare_tables(
            py_table_use,
            fort_table_use,
            float_tolerance=float_tol,
            ignore_column_suffixes=('_orbit', '_open'),
        )
        details.append(f'table: {res.message}')
        details.extend(res.details)
        all_ok = all_ok and res.same
    if py_txt_use and fort_txt_use and py_txt_use.exists() and fort_txt_use.exists():
        res = compare_tables(py_txt_use, fort_txt_use, float_tolerance=float_tol)
        details.append(f'text: {res.message}')
        details.extend(res.details)
        all_ok = all_ok and res.same
    if py_ps_use and fort_ps_use:
        res_ps = compare_postscript(py_ps_use, fort_ps_use)
        details.append(f'ps: {res_ps.message}')
        details.extend(res_ps.details)
        all_ok = all_ok and res_ps.same
        diff_img = out_dir / 'diff.png'
        res_img = compare_postscript_images(py_ps_use, fort_ps_use, diff_image_path=diff_img)
        details.append(f'image: {res_img.message}')
        details.extend(res_img.details)
    return (all_ok, details)


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Run Python (and optionally FORTRAN) with same inputs; compare outputs.',
    )
    parser.add_argument(
        'tool',
        nargs='?',
        choices=['ephemeris', 'tracker', 'viewer'],
        help='Tool to run',
    )
    parser.add_argument(
        '--url',
        '--query-string',
        dest='query_input',
        type=str,
        default=None,
        help='Single CGI URL/query string to parse and compare',
    )
    parser.add_argument(
        '--test-file',
        type=str,
        default=None,
        help='Path to file containing one CGI URL/query string per line',
    )
    parser.add_argument(
        '--planet', type=parse_planet, default=6, help='Planet number or name (4-9 / mars..pluto)'
    )
    parser.add_argument(
        '--start',
        type=str,
        default='2022-01-01 00:00',
        help='Start time (ephemeris/tracker only)',
    )
    parser.add_argument(
        '--stop',
        type=str,
        default='2022-01-02 00:00',
        help='Stop time (ephemeris/tracker only)',
    )
    parser.add_argument(
        '--interval', type=float, default=1.0, help='Time step (ephemeris/tracker only)'
    )
    parser.add_argument(
        '--time-unit',
        type=str,
        default='hour',
        choices=['sec', 'min', 'hour', 'day'],
        help='Time step unit (ephemeris/tracker only)',
    )
    parser.add_argument(
        '--ephem', type=int, default=0, help='Ephemeris version (0=latest, matches web/FORTRAN)'
    )
    parser.add_argument('--viewpoint', type=str, default='observatory')
    parser.add_argument('--observatory', type=str, default="Earth's Center")
    parser.add_argument('--latitude', type=float, default=None)
    parser.add_argument('--longitude', type=float, default=None)
    parser.add_argument('--lon-dir', type=str, default='east', choices=['east', 'west'])
    parser.add_argument('--altitude', type=float, default=None)
    parser.add_argument('--sc-trajectory', type=int, default=0)
    parser.add_argument('--columns', type=str, nargs='*', default=None)
    parser.add_argument('--mooncols', type=str, nargs='*', default=None)
    parser.add_argument('--moons', type=str, nargs='*', default=None)
    parser.add_argument(
        '--time',
        type=str,
        default='',
        help='Observation time (viewer only; use instead of --start/--stop)',
    )
    parser.add_argument('--fov', type=float, default=1.0, help='Viewer field of view')
    parser.add_argument('--fov-unit', type=str, default='deg', choices=['deg', 'arcmin', 'arcsec'])
    parser.add_argument('--center', type=str, default='body')
    parser.add_argument('--center-body', type=str, default='')
    parser.add_argument('--rings', type=str, nargs='*', default=None)
    parser.add_argument('--title', type=str, default='')
    parser.add_argument('--xrange', type=float, default=None)
    parser.add_argument('--xunit', type=str, default='arcsec', choices=['arcsec', 'radii'])
    parser.add_argument(
        '--fortran-cmd',
        type=str,
        default=None,
        help='Override FORTRAN executable (default: repo_root/fortran/Tools/<tool>.bin).',
    )
    parser.add_argument(
        '-o',
        '--output-dir',
        type=str,
        default=None,
        help='Output directory for table/PS files (default: current dir)',
    )
    parser.add_argument(
        '--float-tol',
        type=int,
        default=6,
        help='Compare numeric table fields to this many significant digits (0 = exact)',
    )
    args = parser.parse_args()

    if args.query_input or args.test_file:
        repo_root = Path(__file__).resolve().parent.parent.parent
        out_dir = Path(args.output_dir or '.')
        out_dir.mkdir(parents=True, exist_ok=True)
        if args.test_file:
            urls = _read_test_urls(Path(args.test_file))
        else:
            urls = [args.query_input or '']
        summary_lines: list[str] = []
        all_details_lines: list[str] = []
        failed: list[str] = []
        passed_count = 0
        for idx, url in enumerate(urls, start=1):
            spec = spec_from_query_input(url)
            planet = int(spec.params.get('planet', 6))
            case_dir = out_dir / f'{spec.tool}_{planet}_{idx:03d}'
            if args.fortran_cmd:
                case_fort_cmd = args.fortran_cmd.split()
            else:
                derived = _default_fortran_binary(spec.tool, planet, repo_root)
                case_fort_cmd = [str(derived)] if derived is not None else None
            ok, details = _execute_spec(
                spec=spec,
                out_dir=case_dir,
                fort_cmd=case_fort_cmd,
                float_tol=args.float_tol,
            )
            (case_dir / 'comparison.txt').write_text('\n'.join(details) + '\n')
            all_details_lines.append(f'## case {idx}')
            all_details_lines.append(url)
            all_details_lines.extend(details)
            all_details_lines.append('')
            if ok:
                passed_count += 1
            else:
                failed.append(f'line {idx}: {url}')
        total = len(urls)
        failed_count = len(failed)
        skipped_count = 0
        summary_lines.append(f'total={total}')
        summary_lines.append(f'passed={passed_count}')
        summary_lines.append(f'failed={failed_count}')
        summary_lines.append(f'skipped={skipped_count}')
        if failed:
            summary_lines.append('failed_tests:')
            summary_lines.extend(failed)
        (out_dir / 'summary.txt').write_text('\n'.join(summary_lines) + '\n')
        (out_dir / 'all_comparisons.txt').write_text('\n'.join(all_details_lines) + '\n')
        return 1 if failed_count > 0 else 0

    if args.tool is None:
        parser.error('tool is required unless --url/--query-string or --test-file is provided')

    if args.tool == 'viewer' and ('--start' in sys.argv or '--stop' in sys.argv):
        print(
            'viewer does not accept --start or --stop; use --time for observation time.',
            file=sys.stderr,
        )
        return 1

    # Repo root: this file is tests/compare_fortran/__main__.py.
    repo_root = Path(__file__).resolve().parent.parent.parent
    if args.fortran_cmd:
        fort_cmd = args.fortran_cmd.split()
    else:
        derived = _default_fortran_binary(args.tool, args.planet, repo_root)
        fort_cmd = [str(derived)] if derived is not None else None

    out_dir = Path(args.output_dir or '.')
    out_dir.mkdir(parents=True, exist_ok=True)

    # FORTRAN ephemeris requires at least one column in QUERY_STRING or ncolumns=0
    # and it writes only blank lines. Use same defaults as Python CLI.
    default_ephem_columns = [1, 2, 3, 15, 8]
    default_ephem_mooncols = [5, 6, 8, 9]  # RA&Dec, offset, orb lon, orb open (match CLI default)
    columns_resolved = (
        parse_column_spec(args.columns) if args.columns is not None else default_ephem_columns
    )
    mooncols_resolved = parse_mooncol_spec(args.mooncols) if args.mooncols is not None else None
    moons_raw = args.moons or []
    moons_resolved = (
        parse_moon_spec(args.planet, [str(x) for x in moons_raw]) if moons_raw else None
    )

    params = {
        'planet': args.planet,
        'ephem': args.ephem,
        'viewpoint': args.viewpoint,
        'observatory': args.observatory,
        'latitude': args.latitude,
        'longitude': args.longitude,
        'lon_dir': args.lon_dir,
        'altitude': args.altitude,
        'sc_trajectory': args.sc_trajectory,
        'columns': columns_resolved if args.tool == 'ephemeris' else None,
        'mooncols': (mooncols_resolved if mooncols_resolved is not None else default_ephem_mooncols)
        if args.tool == 'ephemeris'
        else None,
        'moons': moons_resolved
        or (DEFAULT_TRACKER_MOONS_SATURN if args.tool == 'tracker' and args.planet == 6 else None),
        'time': args.time or '2022-01-01 12:00',
        'fov': args.fov,
        'fov_unit': args.fov_unit,
        'center': args.center,
        'center_body': args.center_body,
        'rings': parse_ring_spec(args.planet, args.rings) if args.rings else None,
        'title': args.title,
        'xrange': args.xrange or (180.0 if args.tool == 'tracker' else None),
        'xunit': args.xunit,
    }
    # Viewer uses only --time; ephemeris/tracker use --start, --stop, --interval, --time-unit.
    if args.tool in ('ephemeris', 'tracker'):
        params['start'] = args.start
        params['stop'] = args.stop
        params['interval'] = args.interval
        params['time_unit'] = args.time_unit
    spec = RunSpec(tool=args.tool, params=params)

    py_table = out_dir / 'python_table.txt'
    py_ps = out_dir / 'python.ps'
    py_txt = out_dir / 'python_tracker.txt'
    fort_table = out_dir / 'fortran_table.txt'
    fort_ps = out_dir / 'fortran.ps'
    fort_txt = out_dir / 'fortran_tracker.txt'

    if spec.tool == 'ephemeris':
        py_table_use = py_table
        fort_table_use = fort_table
        py_ps_use = fort_ps_use = None
        py_txt_use = fort_txt_use = None
    elif spec.tool == 'tracker':
        py_table_use = None
        fort_table_use = None
        py_ps_use = py_ps
        fort_ps_use = fort_ps
        py_txt_use = py_txt
        fort_txt_use = fort_txt
    else:
        py_table_use = fort_table_use = None
        py_ps_use = py_ps
        fort_ps_use = fort_ps
        py_txt_use = py_txt
        fort_txt_use = fort_txt

    print('Running Python...', flush=True)
    result_py = run_python(spec, out_table=py_table_use, out_ps=py_ps_use, out_txt=py_txt_use)
    if result_py.returncode != 0:
        print('Python failed:', result_py.stderr or result_py.stdout, file=sys.stderr)
        return 1
    print('Python OK.', flush=True)

    if fort_cmd:
        print('Running FORTRAN...', flush=True)
        result_fort = run_fortran(
            spec,
            fort_cmd,
            out_table=fort_table_use,
            out_ps=fort_ps_use,
            out_txt=fort_txt_use,
        )
        # FORTRAN error handlers call "call exit" which returns 0.
        # Detect errors from stdout ("Invalid value found for variable").
        fort_stdout = result_fort.stdout or ''
        fort_failed = (
            result_fort.returncode != 0
            or 'Invalid value found for variable' in fort_stdout
            or 'Error---' in fort_stdout
        )
        if fort_failed:
            print(
                'FORTRAN failed:',
                result_fort.stderr or fort_stdout,
                file=sys.stderr,
            )
            return 1
        print('FORTRAN OK.', flush=True)

        exit_code = 0
        if py_table_use and fort_table_use:
            # Ignore *_orbit and *_open columns: known FORTRAN bug in RSPK_OrbitOpen.
            res = compare_tables(
                py_table_use,
                fort_table_use,
                float_tolerance=args.float_tol,
                ignore_column_suffixes=('_orbit', '_open'),
            )
            print(res.message)
            for d in res.details:
                print(d)
            if not res.same:
                exit_code = 1
        if py_txt_use and fort_txt_use and (py_txt_use.exists() and fort_txt_use.exists()):
            res = compare_tables(
                py_txt_use,
                fort_txt_use,
                float_tolerance=args.float_tol,
            )
            print('Tracker text table:', res.message)
            for d in res.details:
                print(d)
            if not res.same:
                exit_code = 1
        if py_ps_use and fort_ps_use:
            res = compare_postscript(py_ps_use, fort_ps_use)
            print(res.message)
            for d in res.details:
                print(d)
            if not res.same:
                exit_code = 1
            # Pixel comparison via Ghostscript rendering
            diff_img = out_dir / 'diff.png'
            res_img = compare_postscript_images(
                py_ps_use,
                fort_ps_use,
                diff_image_path=diff_img,
            )
            print(res_img.message)
            for d in res_img.details:
                print(d)
        return exit_code

    print('Outputs written to', out_dir)
    return 0


if __name__ == '__main__':
    sys.exit(main())
