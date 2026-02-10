"""CLI to run Python and (optionally) FORTRAN with the same inputs and compare outputs.

Usage:
  python -m tests.compare_fortran ephemeris --planet 6 --start 2022-01-01 --stop 2022-01-02 -o /tmp/out
  python -m tests.compare_fortran ephemeris --planet 6 --start 2022-01-01 --stop 2022-01-02 \\
    --fortran-cmd /path/to/ephem3_xxx.bin -o /tmp/out
  python -m tests.compare_fortran tracker --planet 6 --start 2022-01-01 --stop 2022-01-03 \\
    --fortran-cmd /path/to/tracker3_xxx.bin -o /tmp/out
  python -m tests.compare_fortran viewer --planet 6 --time 2022-01-01 12:00 --fov 0.1 \\
    --fortran-cmd /path/to/viewer3_sat.bin -o /tmp/out

With --fortran-cmd: runs both, compares table and/or PostScript, reports differences.
Without --fortran-cmd: runs only Python and writes outputs (no comparison).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tests.compare_fortran.spec import RunSpec
from tests.compare_fortran.runner import run_python, run_fortran
from tests.compare_fortran.diff_utils import compare_tables, compare_postscript


def _parse_planet(s: str) -> int:
    v = int(s)
    if not (4 <= v <= 9):
        raise ValueError("planet must be 4-9")
    return v


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run Python (and optionally FORTRAN) with same inputs; compare outputs.",
    )
    parser.add_argument(
        "tool",
        choices=["ephemeris", "tracker", "viewer"],
        help="Tool to run",
    )
    parser.add_argument("--planet", type=_parse_planet, default=6, help="Planet number 4-9")
    parser.add_argument("--start", type=str, default="2022-01-01 00:00", help="Start time")
    parser.add_argument("--stop", type=str, default="2022-01-02 00:00", help="Stop time")
    parser.add_argument("--interval", type=float, default=1.0, help="Time step")
    parser.add_argument("--time-unit", type=str, default="hour", choices=["sec", "min", "hour", "day"])
    parser.add_argument("--ephem", type=int, default=1, help="Ephemeris version")
    parser.add_argument("--viewpoint", type=str, default="observatory")
    parser.add_argument("--observatory", type=str, default="Earth's Center")
    parser.add_argument("--latitude", type=float, default=None)
    parser.add_argument("--longitude", type=float, default=None)
    parser.add_argument("--lon-dir", type=str, default="east", choices=["east", "west"])
    parser.add_argument("--altitude", type=float, default=None)
    parser.add_argument("--sc-trajectory", type=int, default=0)
    parser.add_argument("--columns", type=int, nargs="*", default=None)
    parser.add_argument("--mooncols", type=int, nargs="*", default=None)
    parser.add_argument("--moons", type=int, nargs="*", default=None)
    parser.add_argument("--time", type=str, default="", help="Viewer observation time")
    parser.add_argument("--fov", type=float, default=1.0, help="Viewer field of view")
    parser.add_argument("--fov-unit", type=str, default="deg", choices=["deg", "arcmin", "arcsec"])
    parser.add_argument("--center", type=str, default="body")
    parser.add_argument("--center-body", type=str, default="")
    parser.add_argument("--rings", type=int, nargs="*", default=None)
    parser.add_argument("--title", type=str, default="")
    parser.add_argument("--xrange", type=float, default=None)
    parser.add_argument("--xunit", type=str, default="arcsec", choices=["arcsec", "radii"])
    parser.add_argument(
        "--fortran-cmd",
        type=str,
        default=None,
        help="FORTRAN executable path (or 'env args... /path/to/bin'). If set, run FORTRAN and compare.",
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default=None,
        help="Output directory for table/PS files (default: current dir)",
    )
    parser.add_argument(
        "--float-tol",
        type=int,
        default=6,
        help="Compare numeric table fields to this many significant digits (0 = exact)",
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir or ".")
    out_dir.mkdir(parents=True, exist_ok=True)

    params = {
        "planet": args.planet,
        "start": args.start,
        "stop": args.stop,
        "interval": args.interval,
        "time_unit": args.time_unit,
        "ephem": args.ephem,
        "viewpoint": args.viewpoint,
        "observatory": args.observatory,
        "latitude": args.latitude,
        "longitude": args.longitude,
        "lon_dir": args.lon_dir,
        "altitude": args.altitude,
        "sc_trajectory": args.sc_trajectory,
        "columns": args.columns,
        "mooncols": args.mooncols,
        "moons": args.moons,
        "time": args.time or "2022-01-01 12:00",
        "fov": args.fov,
        "fov_unit": args.fov_unit,
        "center": args.center,
        "center_body": args.center_body,
        "rings": args.rings,
        "title": args.title,
        "xrange": args.xrange,
        "xunit": args.xunit,
    }
    spec = RunSpec(tool=args.tool, params=params)

    py_table = out_dir / "python_table.txt"
    py_ps = out_dir / "python.ps"
    py_txt = out_dir / "python_tracker.txt"
    fort_table = out_dir / "fortran_table.txt"
    fort_ps = out_dir / "fortran.ps"
    fort_txt = out_dir / "fortran_tracker.txt"

    if spec.tool == "ephemeris":
        py_table_use = py_table
        fort_table_use = fort_table
        py_ps_use = fort_ps_use = None
        py_txt_use = fort_txt_use = None
    elif spec.tool == "tracker":
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

    print("Running Python...", flush=True)
    result_py = run_python(spec, out_table=py_table_use, out_ps=py_ps_use, out_txt=py_txt_use)
    if result_py.returncode != 0:
        print("Python failed:", result_py.stderr or result_py.stdout, file=sys.stderr)
        return 1
    print("Python OK.", flush=True)

    if args.fortran_cmd:
        print("Running FORTRAN...", flush=True)
        fort_cmd = args.fortran_cmd.split()
        result_fort = run_fortran(
            spec,
            fort_cmd,
            out_table=fort_table_use,
            out_ps=fort_ps_use,
            out_txt=fort_txt_use,
        )
        if result_fort.returncode != 0:
            print("FORTRAN failed:", result_fort.stderr or result_fort.stdout, file=sys.stderr)
            return 1
        print("FORTRAN OK.", flush=True)

        exit_code = 0
        if py_table_use and fort_table_use:
            res = compare_tables(
                py_table_use,
                fort_table_use,
                float_tolerance=args.float_tol if args.float_tol else None,
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
                float_tolerance=args.float_tol if args.float_tol else None,
            )
            print("Tracker text table:", res.message)
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
        return exit_code

    print("Outputs written to", out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
