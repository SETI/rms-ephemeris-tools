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

With --test-file or --url, use -j N to run N URL comparisons in parallel (default 1).
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from ephemeris_tools.params import (
    _is_ra_hours_from_raw,
    _parse_sexagesimal_to_degrees,
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

# Absolute tolerance for tracker text-table ephemeris comparison (spacecraft ephemeris).
TRACKER_EPHEMERIS_ABS_TOL = 0.06

# Progress display: bar width, terminal fallback size, min columns when trimming, log interval.
PROGRESS_BAR_WIDTH = 28
TERMINAL_FALLBACK_COLS = 120
TERMINAL_FALLBACK_LINES = 20
PROGRESS_MIN_DISPLAY_COLS = 20
PROGRESS_LOG_INTERVAL = 10


def _format_duration(seconds: float) -> str:
    """Format duration seconds as MM:SS or HH:MM:SS."""
    total = max(0, round(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours > 0:
        return f'{hours:02d}:{minutes:02d}:{secs:02d}'
    return f'{minutes:02d}:{secs:02d}'


def _emit_progress(
    *,
    current: int,
    total: int,
    passed: int,
    failed: int,
    skipped: int,
    started_at: float,
    is_tty: bool,
) -> None:
    """Render progress for batch URL runs."""
    elapsed = max(0.0, time.monotonic() - started_at)
    fraction = (current / total) if total > 0 else 0.0
    width = PROGRESS_BAR_WIDTH
    filled = round(width * fraction)
    bar = f'[{"#" * filled}{"-" * (width - filled)}]'
    pct = 100.0 * fraction
    rate = (current / elapsed) if elapsed > 0 and current > 0 else 0.0
    remaining = max(0, total - current)
    eta = (remaining / rate) if rate > 0 else 0.0
    line = (
        f'{bar} {current}/{total} {pct:6.2f}% '
        f'pass={passed} fail={failed} skip={skipped} '
        f'elapsed={_format_duration(elapsed)} eta={_format_duration(eta)}'
    )

    if is_tty:
        term_cols = shutil.get_terminal_size(
            fallback=(TERMINAL_FALLBACK_COLS, TERMINAL_FALLBACK_LINES)
        ).columns
        trimmed = line[: max(PROGRESS_MIN_DISPLAY_COLS, term_cols - 1)]
        print(f'\r{trimmed}', end='', file=sys.stderr, flush=True)
        if current == total:
            print('', file=sys.stderr, flush=True)
        return

    # Non-interactive logs: print first, every N cases, and final line.
    if current == 1 or current == total or current % PROGRESS_LOG_INTERVAL == 0:
        print(line, file=sys.stderr, flush=True)


def _parse_center_angle(value: str, *, is_ra_hours: bool) -> float | str:
    """Parse viewer center angle, allowing sexagesimal URL values."""
    s = value.strip()
    if s == '':
        return ''
    try:
        return float(s)
    except ValueError:
        return _parse_sexagesimal_to_degrees(s, is_ra_hours=is_ra_hours)


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
    # Match parse_cgi.sh: planet from first 3 chars (jup,sat,plu); jupec->jup->5, satc->sat->6
    short = abbrev[:3] if len(abbrev) >= 3 else abbrev
    planet = _ABBREV_TO_PLANET.get(short, 6)
    params: dict[str, Any] = {'planet': planet, 'query_string': raw_query}

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
        params['center_ansa'] = qs.get('center_ansa', [''])[0]
        params['center_ew'] = qs.get('center_ew', ['east'])[0]
        center_ra_raw = qs.get('center_ra', [''])[0]
        params['center_ra_type'] = qs.get('center_ra_type', [''])[0]
        is_ra_hours = _is_ra_hours_from_raw(params['center_ra_type'])
        params['center_ra'] = _parse_center_angle(center_ra_raw, is_ra_hours=is_ra_hours)
        center_dec_raw = qs.get('center_dec', [''])[0]
        params['center_dec'] = _parse_center_angle(center_dec_raw, is_ra_hours=False)
        params['center_star'] = qs.get('center_star', [''])[0]
        params['rings'] = qs.get('rings', [None])[0]
        params['torus'] = qs.get('torus', [None])[0]
        params['torus_inc'] = qs.get('torus_inc', [None])[0]
        params['torus_rad'] = qs.get('torus_rad', [None])[0]
        params['labels'] = qs.get('labels', [None])[0]
        params['moonpts'] = qs.get('moonpts', [None])[0]
        params['blank'] = qs.get('blank', [None])[0]
        params['opacity'] = qs.get('opacity', [None])[0]
        params['peris'] = qs.get('peris', [None])[0]
        params['peripts'] = qs.get('peripts', [None])[0]
        params['meridians'] = qs.get('meridians', [None])[0]
        params['arcmodel'] = qs.get('arcmodel', [None])[0]
        params['arcpts'] = qs.get('arcpts', [None])[0]
        params['additional'] = qs.get('additional', [None])[0]
        params['extra_name'] = qs.get('extra_name', [None])[0]
        params['extra_ra'] = qs.get('extra_ra', [None])[0]
        params['extra_ra_type'] = qs.get('extra_ra_type', [None])[0]
        params['extra_dec'] = qs.get('extra_dec', [None])[0]
        params['other'] = qs.get('other', [])
        params['title'] = qs.get('title', [''])[0]

    params['viewpoint'] = qs.get('viewpoint', ['observatory'])[0]
    params['observatory'] = qs.get('observatory', ["Earth's center"])[0]
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
    float_tol: int | None,
    lsd_tol: float | None,
    viewer_min_similarity_pct: float | None = None,
) -> tuple[bool, list[str], float | None]:
    """Execute one comparison spec and return (passed, detail lines, max_table_abs_diff).

    For viewer and tracker, pass/fail is based only on image similarity
    (axis anti-mask), not on stdout or PostScript. When viewer_min_similarity_pct
    is set (e.g. 99.99), they pass if image similarity >= that value.

    Returns:
        A 3-tuple: (passed, detail_lines, max_table_abs_diff). passed is True
        if the comparison passed (or FORTRAN was skipped). detail_lines is a
        list of summary/detail strings. max_table_abs_diff is the maximum
        absolute difference from table comparisons (float), or None if no
        table comparison was performed or no numeric diff was recorded.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    details: list[str] = [f'tool={spec.tool} planet={spec.params.get("planet", "?")}']
    max_table_abs_diff: float | None = None

    py_table = out_dir / 'python_table.txt'
    py_ps = out_dir / 'python.ps'
    py_txt = out_dir / f'python_{spec.tool}.txt'
    fort_table = out_dir / 'fortran_table.txt'
    fort_ps = out_dir / 'fortran.ps'
    fort_txt = out_dir / f'fortran_{spec.tool}.txt'

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
        # Keep viewer FOV description on stdout for Python/FORTRAN parity.
        py_txt_use = None
        fort_txt_use = None

    result_py = run_python(spec, out_table=py_table_use, out_ps=py_ps_use, out_txt=py_txt_use)
    if result_py.returncode != 0:
        details.append('python_failed')
        details.append((result_py.stderr or result_py.stdout or '').strip())
        return (False, details, None)

    if fort_cmd is None:
        details.append('fortran_skipped')
        return (True, details, None)

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
        return (False, details, None)

    # Compare printed output (stdout: Input Parameters section)
    py_stdout_path = out_dir / 'python_stdout.txt'
    fort_stdout_path = out_dir / 'fortran_stdout.txt'
    py_stdout_path.write_text(result_py.stdout or '')
    fort_stdout_path.write_text(result_fort.stdout or '')
    res_stdout = compare_tables(
        py_stdout_path,
        fort_stdout_path,
        float_tolerance=float_tol,
        lsd_tolerance=lsd_tol,
    )
    details.append(f'stdout: {res_stdout.message}')
    details.extend(res_stdout.details)
    all_ok = res_stdout.same

    if py_table_use and fort_table_use:
        res = compare_tables(
            py_table_use,
            fort_table_use,
            float_tolerance=float_tol,
            lsd_tolerance=lsd_tol,
            ignore_column_suffixes=('_orbit', '_open'),
        )
        details.append(f'table: {res.message}')
        details.extend(res.details)
        all_ok = all_ok and res.same
        if res.max_abs_diff is not None:
            max_table_abs_diff = (
                res.max_abs_diff
                if max_table_abs_diff is None
                else max(max_table_abs_diff, res.max_abs_diff)
            )
    if py_txt_use and fort_txt_use and py_txt_use.exists() and fort_txt_use.exists():
        # Tracker text table: allow small spacecraft ephemeris differences (up to TRACKER_EPHEMERIS_ABS_TOL).
        txt_abs_tol = TRACKER_EPHEMERIS_ABS_TOL if spec.tool == 'tracker' else None
        res = compare_tables(
            py_txt_use,
            fort_txt_use,
            float_tolerance=float_tol,
            lsd_tolerance=lsd_tol,
            abs_tolerance=txt_abs_tol,
        )
        details.append(f'text: {res.message}')
        details.extend(res.details)
        all_ok = all_ok and res.same
        if res.max_abs_diff is not None:
            max_table_abs_diff = (
                res.max_abs_diff
                if max_table_abs_diff is None
                else max(max_table_abs_diff, res.max_abs_diff)
            )
    if py_ps_use and fort_ps_use:
        res_ps = compare_postscript(py_ps_use, fort_ps_use)
        details.append(f'ps: {res_ps.message}')
        details.extend(res_ps.details)
        if spec.tool not in ('viewer', 'tracker'):
            all_ok = all_ok and res_ps.same
        diff_img = out_dir / 'diff.png'
        res_img = compare_postscript_images(
            py_ps_use,
            fort_ps_use,
            diff_image_path=diff_img,
            ignore_axis_pixels=(spec.tool in ('viewer', 'tracker')),
            min_similarity_pct=(
                viewer_min_similarity_pct if spec.tool in ('viewer', 'tracker') else None
            ),
        )
        details.append(f'image: {res_img.message}')
        details.extend(res_img.details)
        all_ok = all_ok and res_img.same
    return (all_ok, details, max_table_abs_diff)


def _run_one_url(
    idx: int,
    url: str,
    repo_root: Path,
    *,
    out_dir: Path,
    fortran_cmd_str: str | None,
    float_tol: int | None,
    lsd_tol: float | None,
    viewer_min_similarity_pct: float | None,
) -> tuple[int, str, bool, list[str], float | None, Path, bool]:
    """Execute one URL comparison; return (idx, url, passed, details, max_diff, case_dir, skipped).

    Used for parallel batch runs. Caller must write comparison.txt and aggregate results.
    """
    spec = spec_from_query_input(url)
    planet = int(spec.params.get('planet', 6))
    case_dir = out_dir / f'{spec.tool}_{planet}_{idx:03d}'
    case_fort_cmd: list[str] | None
    if fortran_cmd_str:
        case_fort_cmd = fortran_cmd_str.split()
    else:
        derived = _default_fortran_binary(spec.tool, planet, repo_root)
        case_fort_cmd = [str(derived)] if derived is not None else None
    case_dir.mkdir(parents=True, exist_ok=True)
    ok, details, case_max_diff = _execute_spec(
        spec=spec,
        out_dir=case_dir,
        fort_cmd=case_fort_cmd,
        float_tol=float_tol,
        lsd_tol=lsd_tol,
        viewer_min_similarity_pct=viewer_min_similarity_pct,
    )
    (case_dir / 'comparison.txt').write_text('\n'.join(details) + '\n')
    skipped = 'fortran_skipped' in details
    return (idx, url, ok, details, case_max_diff, case_dir, skipped)


def main() -> int:
    """Run Python (and optionally FORTRAN) with same inputs; compare outputs and exit.

    Parses CLI for tool (ephemeris/tracker/viewer), URL or test file, and comparison
    options. In URL/test-file mode runs each case (optionally in parallel), writes
    summary and comparison files to the output directory, and optionally collects
    failed case artifacts. In single-run mode invokes Python and optionally FORTRAN,
    compares table/PostScript/image output, and prints results to stdout/stderr.

    Returns:
        Exit code: 0 on success, 1 on failure (e.g. comparison mismatch or run error).
    """
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
    parser.add_argument('--observatory', type=str, default="Earth's center")
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
    parser.add_argument(
        '--lsd-tol',
        type=float,
        default=1.0,
        help='Tolerance in least-significant-digit units. Values match when |a-b| <= '
        'lsd_tol * lsd, where lsd is inferred from the printed form. E.g. 1.001 with '
        'lsd_tol=1 allows ±0.001; 10.5 allows ±0.1; 7 allows ±1. Set 0 for exact.',
    )
    parser.add_argument(
        '--viewer-image-min-similarity',
        type=float,
        default=99.97,
        metavar='PCT',
        help='For viewer and tracker, minimum image similarity (percent) to pass; '
        'only content pixels (axis anti-mask) are used. Default 99.97. PostScript '
        'differences do not cause viewer or tracker failure.',
    )
    parser.add_argument(
        '--collect-failed-to',
        type=str,
        default=None,
        metavar='DIR',
        help='After running, copy all files from each failed case (comparison.txt, '
        'stdout, table, PS, PNG) into this directory with case-prefixed names. '
        'Only used with --test-file or --url.',
    )
    parser.add_argument(
        '-j',
        '--jobs',
        type=int,
        default=1,
        metavar='N',
        help='Number of parallel jobs when comparing multiple URLs (--test-file or '
        'multiple --url). Default 1 (sequential). Ignored for single-URL or CLI runs.',
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
        failed_dirs: list[Path] = []
        passed_count = 0
        skipped_count = 0
        started_at = time.monotonic()
        is_tty = sys.stderr.isatty()
        run_max_table_abs_diff: float | None = None
        float_tol = args.float_tol if args.float_tol > 0 else None
        lsd_tol = args.lsd_tol if args.lsd_tol > 0 else None
        jobs = max(1, int(args.jobs))
        if jobs > 1:
            result_by_idx: dict[int, tuple[str, bool, list[str], Path, float | None, bool]] = {}
            with ThreadPoolExecutor(max_workers=jobs) as executor:
                future_to_idx = {
                    executor.submit(
                        _run_one_url,
                        idx,
                        url,
                        repo_root,
                        out_dir=out_dir,
                        fortran_cmd_str=args.fortran_cmd,
                        float_tol=float_tol,
                        lsd_tol=lsd_tol,
                        viewer_min_similarity_pct=args.viewer_image_min_similarity,
                    ): idx
                    for idx, url in enumerate(urls, start=1)
                }
                for fut in as_completed(future_to_idx):
                    idx = future_to_idx[fut]
                    try:
                        _idx, url, ok, details, case_max_diff, case_dir, skipped = fut.result()
                        result_by_idx[idx] = (url, ok, details, case_dir, case_max_diff, skipped)
                    except Exception:
                        url = urls[idx - 1] if idx <= len(urls) else ''
                        details = [f'exception in worker: {traceback.format_exc()}']
                        result_by_idx[idx] = (
                            url,
                            False,
                            details,
                            out_dir,
                            None,
                            False,
                        )
                    n_done = len(result_by_idx)
                    _emit_progress(
                        current=n_done,
                        total=len(urls),
                        passed=sum(1 for r in result_by_idx.values() if r[1]),
                        failed=sum(1 for r in result_by_idx.values() if not r[1]),
                        skipped=sum(1 for r in result_by_idx.values() if r[5]),
                        started_at=started_at,
                        is_tty=is_tty,
                    )
            for idx in range(1, len(urls) + 1):
                url, ok, details, case_dir, case_max_diff, skipped = result_by_idx[idx]
                all_details_lines.append(f'## case {idx}')
                all_details_lines.append(url)
                all_details_lines.extend(details)
                all_details_lines.append('')
                if skipped:
                    skipped_count += 1
                if ok:
                    passed_count += 1
                else:
                    failed.append(f'line {idx}: {url}')
                    failed_dirs.append(case_dir)
                if case_max_diff is not None:
                    run_max_table_abs_diff = (
                        case_max_diff
                        if run_max_table_abs_diff is None
                        else max(run_max_table_abs_diff, case_max_diff)
                    )
        else:
            for idx, url in enumerate(urls, start=1):
                _idx, _url, ok, details, case_max_diff, case_dir, skipped = _run_one_url(
                    idx,
                    url,
                    repo_root,
                    out_dir=out_dir,
                    fortran_cmd_str=args.fortran_cmd,
                    float_tol=float_tol,
                    lsd_tol=lsd_tol,
                    viewer_min_similarity_pct=args.viewer_image_min_similarity,
                )
                all_details_lines.append(f'## case {idx}')
                all_details_lines.append(url)
                all_details_lines.extend(details)
                all_details_lines.append('')
                if skipped:
                    skipped_count += 1
                if ok:
                    passed_count += 1
                else:
                    failed.append(f'line {idx}: {url}')
                    failed_dirs.append(case_dir)
                if case_max_diff is not None:
                    run_max_table_abs_diff = (
                        case_max_diff
                        if run_max_table_abs_diff is None
                        else max(run_max_table_abs_diff, case_max_diff)
                    )
                _emit_progress(
                    current=idx,
                    total=len(urls),
                    passed=passed_count,
                    failed=len(failed),
                    skipped=skipped_count,
                    started_at=started_at,
                    is_tty=is_tty,
                )
        total = len(urls)
        failed_count = len(failed)
        summary_lines.append(f'total={total}')
        summary_lines.append(f'passed={passed_count}')
        summary_lines.append(f'failed={failed_count}')
        summary_lines.append(f'skipped={skipped_count}')
        if run_max_table_abs_diff is not None:
            summary_lines.append(f'largest_table_abs_diff={run_max_table_abs_diff:.6g}')
        if failed:
            summary_lines.append('failed_tests:')
            summary_lines.extend(failed)
        (out_dir / 'summary.txt').write_text('\n'.join(summary_lines) + '\n')
        (out_dir / 'all_comparisons.txt').write_text('\n'.join(all_details_lines) + '\n')
        if args.collect_failed_to and failed_dirs:
            collect_dir = Path(args.collect_failed_to)
            collect_dir.mkdir(parents=True, exist_ok=True)

            def _copy_with_prefix(src: Path, *, prefix: str) -> None:
                if not src.is_file():
                    return
                dest = collect_dir / (prefix + src.name)
                shutil.copy2(src, dest)

            for case_dir in failed_dirs:
                prefix = case_dir.name + '_'
                for path in case_dir.iterdir():
                    if path.is_file():
                        _copy_with_prefix(path, prefix=prefix)

                # Ensure ephemeris failed cases include output tables and stdout files
                # in the collected failure directory even if only summary artifacts are
                # present by default.
                if case_dir.name.startswith('ephemeris_'):
                    _copy_with_prefix(case_dir / 'python_table.txt', prefix=prefix)
                    _copy_with_prefix(case_dir / 'fortran_table.txt', prefix=prefix)
                    _copy_with_prefix(case_dir / 'python_stdout.txt', prefix=prefix)
                    _copy_with_prefix(case_dir / 'fortran_stdout.txt', prefix=prefix)
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
    py_txt = out_dir / f'python_{spec.tool}.txt'
    fort_table = out_dir / 'fortran_table.txt'
    fort_ps = out_dir / 'fortran.ps'
    fort_txt = out_dir / f'fortran_{spec.tool}.txt'

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
        # Keep viewer FOV description on stdout for Python/FORTRAN parity.
        py_txt_use = None
        fort_txt_use = None

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

        # Compare printed output (stdout: Input Parameters section)
        py_stdout_path = out_dir / 'python_stdout.txt'
        fort_stdout_path = out_dir / 'fortran_stdout.txt'
        py_stdout_path.write_text(result_py.stdout or '')
        fort_stdout_path.write_text(result_fort.stdout or '')
        res_stdout = compare_tables(
            py_stdout_path,
            fort_stdout_path,
            float_tolerance=(args.float_tol if args.float_tol > 0 else None),
            lsd_tolerance=(args.lsd_tol if args.lsd_tol > 0 else None),
        )
        print('Printed output (stdout):', res_stdout.message)
        for d in res_stdout.details:
            print(d)
        exit_code = 0
        if not res_stdout.same and args.tool not in ('viewer', 'tracker'):
            exit_code = 1

        if py_table_use and fort_table_use:
            # Ignore *_orbit and *_open columns: known FORTRAN bug in RSPK_OrbitOpen.
            res = compare_tables(
                py_table_use,
                fort_table_use,
                float_tolerance=(args.float_tol if args.float_tol > 0 else None),
                lsd_tolerance=(args.lsd_tol if args.lsd_tol > 0 else None),
                ignore_column_suffixes=('_orbit', '_open'),
            )
            print('Table:', res.message)
            for d in res.details:
                print(d)
            if not res.same and args.tool not in ('viewer', 'tracker'):
                exit_code = 1
        if py_txt_use and fort_txt_use and (py_txt_use.exists() and fort_txt_use.exists()):
            res = compare_tables(
                py_txt_use,
                fort_txt_use,
                float_tolerance=(args.float_tol if args.float_tol > 0 else None),
                lsd_tolerance=(args.lsd_tol if args.lsd_tol > 0 else None),
            )
            print(f'Text table ({spec.tool}):', res.message)
            for d in res.details:
                print(d)
            if not res.same and args.tool not in ('viewer', 'tracker'):
                exit_code = 1
        if py_ps_use and fort_ps_use:
            res = compare_postscript(py_ps_use, fort_ps_use)
            print(res.message)
            for d in res.details:
                print(d)
            if not res.same and args.tool not in ('viewer', 'tracker'):
                exit_code = 1
            # Pixel comparison via Ghostscript rendering
            diff_img = out_dir / 'diff.png'
            res_img = compare_postscript_images(
                py_ps_use,
                fort_ps_use,
                diff_image_path=diff_img,
                ignore_axis_pixels=(args.tool in ('viewer', 'tracker')),
                min_similarity_pct=(
                    args.viewer_image_min_similarity if args.tool in ('viewer', 'tracker') else None
                ),
            )
            print(res_img.message)
            for d in res_img.details:
                print(d)
            if not res_img.same:
                exit_code = 1
        return exit_code

    print('Outputs written to', out_dir)
    return 0


if __name__ == '__main__':
    sys.exit(main())
