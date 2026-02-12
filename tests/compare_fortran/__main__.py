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


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Run Python (and optionally FORTRAN) with same inputs; compare outputs.',
    )
    parser.add_argument(
        'tool',
        choices=['ephemeris', 'tracker', 'viewer'],
        help='Tool to run',
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
    mooncols_resolved = (
        parse_mooncol_spec(args.mooncols) if args.mooncols is not None else None
    )
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
        'mooncols': (
            mooncols_resolved if mooncols_resolved is not None else default_ephem_mooncols
        )
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
