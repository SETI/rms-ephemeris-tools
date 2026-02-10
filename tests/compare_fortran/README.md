# FORTRAN vs Python Comparison Framework

Run the same ephemeris/tracker/viewer scenario under both the **FORTRAN** tools and the **Python** `ephemeris-tools` with identical arguments or environment variables, then compare table and PostScript outputs to find differences.

## Prerequisites

- **Python**: Install the project (`pip install -e .` or use the repo venv). SPICE kernels must be configured (see main README).
- **FORTRAN** (optional): To compare against FORTRAN, you must build the FORTRAN tools from `original/tools-FORTRAN/` and provide the executable path. The FORTRAN binaries read parameters from **environment variables** (same names as the CGI interface). This framework sets those env vars and the output file paths (`EPHEM_FILE`, `TRACKER_POSTFILE`, `VIEWER_POSTFILE`, etc.) so the FORTRAN code writes to a known location.

## Usage

From the **repository root**:

```bash
# Run Python only (no FORTRAN); write ephemeris table to /tmp/compare/python_table.txt
python -m tests.compare_fortran ephemeris --planet 6 --start 2022-01-01 --stop 2022-01-02 -o /tmp/compare

# Run both Python and FORTRAN and compare ephemeris tables
python -m tests.compare_fortran ephemeris --planet 6 --start 2022-01-01 --stop 2022-01-02 \
  --fortran-cmd /path/to/ephem3_xxx.bin -o /tmp/compare

# Tracker: compare PostScript and text table
python -m tests.compare_fortran tracker --planet 6 --start 2022-01-01 --stop 2022-01-03 \
  --fortran-cmd /path/to/tracker3_xxx.bin -o /tmp/compare

# Viewer: compare PostScript and FOV text output
python -m tests.compare_fortran viewer --planet 6 --time "2022-01-01 12:00" --fov 0.1 \
  --fortran-cmd /path/to/viewer3_sat.bin -o /tmp/compare
```

### Arguments and environment

- **Arguments** to `python -m tests.compare_fortran` are the same logical parameters as the Python CLI (`ephemeris-tools ephemeris ...`) and the FORTRAN CGI (e.g. `start`, `stop`, `NPLANET`). The framework converts them into:
  - **Python**: CLI args for `ephemeris-tools`
  - **FORTRAN**: environment variables (e.g. `NPLANET`, `start`, `stop`, `EPHEM_FILE`, `TRACKER_POSTFILE`, etc.)
- You can also **set environment variables** before running; the Python run uses the current process env, and the FORTRAN run gets the same vars (plus the output paths we add). So you can do:
  ```bash
  export NPLANET=6
  export start="2022-01-01 00:00"
  export stop="2022-01-02 00:00"
  python -m tests.compare_fortran ephemeris -o /tmp/out --fortran-cmd /path/to/ephem3_xxx.bin
  ```
  if you add support in the CLI to pass through env (currently the CLI uses its own defaults and explicit args; the `RunSpec.env_for_fortran()` builds env from the spec params).

### Output files

With `-o /tmp/compare`:

| Tool      | Python outputs           | FORTRAN outputs (if `--fortran-cmd` given) |
|-----------|--------------------------|--------------------------------------------|
| ephemeris | `python_table.txt`       | `fortran_table.txt`                        |
| tracker   | `python.ps`, `python_tracker.txt` | `fortran.ps`, `fortran_tracker.txt` |
| viewer    | `python.ps`, `python_tracker.txt` (FOV table) | `fortran.ps`, `fortran_tracker.txt` |

Comparison is done automatically when `--fortran-cmd` is provided. Exit code 0 if all outputs match; 1 if any differ or a run failed.

## Comparison rules

- **Tables**: Lines are normalized (strip, collapse whitespace). Optionally, numeric fields are compared to a fixed number of significant digits (`--float-tol 6` by default) to avoid false diffs from formatting.
- **PostScript**: Variable headers such as `%%Creator` and `%%CreationDate` are ignored so only structural and drawing differences are reported.

## FORTRAN setup

The FORTRAN tools in `original/tools-FORTRAN/` are built with Make (see `make_all.sh` etc.). The resulting binaries (e.g. `ephem3_xxx.bin`) expect:

- **Environment**: `NPLANET`, `start`, `stop`, `interval`, `time_unit`, `ephem`, `viewpoint`, `observatory`, `latitude`, `longitude`, `lon_dir`, `altitude`, `columns#1`…, `mooncols#1`…, `moons#1`…, and either `EPHEM_FILE` (ephemeris), `TRACKER_POSTFILE`/`TRACKER_TEXTFILE` (tracker), or `VIEWER_POSTFILE`/`VIEWER_TEXTFILE` (viewer).
- **SPICE**: `SPICEPATH` or equivalent so the FORTRAN can find kernels.

This framework sets the output file paths to the paths under `-o`, so the FORTRAN program writes there. No Perl or CGI is required.

## Programmatic use

```python
from pathlib import Path
from tests.compare_fortran import RunSpec, run_python, run_fortran, compare_tables, compare_postscript

spec = RunSpec("ephemeris", {"planet": 6, "start": "2022-01-01", "stop": "2022-01-02"})
out = Path("/tmp/compare")
run_python(spec, out_table=out / "py.txt")
run_fortran(spec, ["/path/to/ephem3_xxx.bin"], out_table=out / "fort.txt")
result = compare_tables(out / "py.txt", out / "fort.txt", float_tolerance=6)
print(result.same, result.message)
```
