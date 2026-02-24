# FORTRAN vs Python Comparison Framework

Run the same ephemeris/tracker/viewer scenario under both the **FORTRAN** tools and the **Python** `ephemeris-tools` with identical arguments or environment variables, then compare table and PostScript outputs to find differences.

## Prerequisites

- **Python**: Install the project (`pip install -e .` or use the repo venv). SPICE kernels must be configured (see main README).
- **FORTRAN** (optional): To compare against FORTRAN, build the FORTRAN tools from `fortran/Tools/` (see Makefiles there). The framework **auto-detects** the executable from `repo_root/fortran/Tools/` (e.g. `ephem3_xxx.bin`, `tracker3_xxx.bin`, `viewer3_sat.bin` by tool and `--planet`). Use `--fortran-cmd` to override. FORTRAN binaries read parameters from **environment variables**; this framework sets those and the output paths (`EPHEM_FILE`, `TRACKER_POSTFILE`, etc.).

## Usage

From the **repository root**:

```bash
# Run Python only (no FORTRAN or binary not found); write outputs to /tmp/compare
python -m tests.compare_fortran ephemeris --planet 6 --start 2022-01-01 --stop 2022-01-02 -o /tmp/compare

# Run both Python and FORTRAN and compare (binary auto-detected from fortran/Tools/)
python -m tests.compare_fortran ephemeris --planet 6 --start 2022-01-01 --stop 2022-01-02 -o /tmp/compare
python -m tests.compare_fortran tracker --planet 6 --start 2022-01-01 --stop 2022-01-03 -o /tmp/compare
python -m tests.compare_fortran viewer --planet 6 --time "2022-01-01 12:00" --fov 0.1 -o /tmp/compare

# Override FORTRAN binary path
python -m tests.compare_fortran ephemeris ... --fortran-cmd /path/to/ephem3_xxx.bin -o /tmp/compare
```

## Complete command-line options

`python -m tests.compare_fortran` supports two run modes:

- **Direct mode**: provide a `tool` (`ephemeris`, `tracker`, `viewer`) and CLI args.
- **Query mode**: provide `--url/--query-string` or `--test-file` with CGI URLs.

### Positional

- `tool` (optional when using query mode): `ephemeris | tracker | viewer`

### Query/batch input

- `--url`, `--query-string`: single CGI URL or raw query string
- `--test-file`: file containing one CGI URL/query string per line

### Common options

- `--planet`: planet number or name (`4..9`, `mars..pluto`), default `6`
- `--ephem`: ephemeris version integer, default `0`
- `--viewpoint`: observer mode/name, default `observatory`
- `--observatory`: observatory label, default `"Earth's center"`
- `--latitude`: observer latitude (float), default `None`
- `--longitude`: observer longitude (float), default `None`
- `--lon-dir`: `east | west`, default `east`
- `--altitude`: observer altitude (float), default `None`
- `--sc-trajectory`: spacecraft trajectory flag (int), default `0`
- `--fortran-cmd`: override FORTRAN executable path
- `-o`, `--output-dir`: output directory

### Ephemeris/tracker time window options

- `--start`: start timestamp (string), default `2022-01-01 00:00`
- `--stop`: stop timestamp (string), default `2022-01-02 00:00`
- `--interval`: interval value (float), default `1.0`
- `--time-unit`: `sec | min | hour | day`, default `hour`

### Ephemeris column options

- `--columns`: column list (space-separated entries)
- `--mooncols`: moon-column list (space-separated entries)

### Moon/ring selection options

- `--moons`: moon list (space-separated entries)
- `--rings`: ring list (space-separated entries)

### Viewer options

- `--time`: observation timestamp (viewer only), default `2022-01-01 12:00`
- `--fov`: field of view (float), default `1.0`
- `--fov-unit`: `deg | arcmin | arcsec`, default `deg`
- `--center`: viewer center mode/value, default `body`
- `--center-body`: viewer center body string, default empty

### Tracker x-axis options

- `--xrange`: x-axis half-range (float), default `None` (or tool default logic)
- `--xunit`: `arcsec | radii`, default `arcsec`
- `--title`: title string, default empty

### Comparison tolerance options

- `--float-tol`: significant-digit tolerance for numeric comparisons.
  - Default: `6`
  - `0` means exact (disables significant-digit tolerance)
- `--lsd-tol`: tolerance in least-significant-digit units. Values match when
  `|a-b| <= lsd_tol * lsd`, where `lsd` is inferred from the printed form.
  - Default: `1.0`
  - E.g. 1.001 with lsd_tol=1 allows ±0.001; 10.5 allows ±0.1; 7 allows ±1
  - Set `0` for exact numeric comparison

### Arguments and environment

- **Arguments** to `python -m tests.compare_fortran` are the same logical parameters as the Python CLI (`ephemeris-tools ephemeris ...`) and the FORTRAN CGI (e.g. `start`, `stop`, `NPLANET`). The framework converts them into:
  - **Python**: CLI args for `ephemeris-tools`
  - **FORTRAN**: environment variables (e.g. `NPLANET`, `start`, `stop`, `EPHEM_FILE`, `TRACKER_POSTFILE`, etc.)
- You can also **set environment variables** before running; the Python run uses the current process env, and the FORTRAN run gets the same vars (plus the output paths we add). So you can do:
  ```bash
  export NPLANET=6
  export start="2022-01-01 00:00"
  export stop="2022-01-02 00:00"
  python -m tests.compare_fortran ephemeris -o /tmp/out
  ```
  (FORTRAN binary is auto-detected from `fortran/Tools/`; use `--fortran-cmd` to override.)

### Output files

With `-o /tmp/compare`:

| Tool      | Python outputs                                | FORTRAN outputs (when binary used)                 |
|-----------|-----------------------------------------------|----------------------------------------------------|
| ephemeris | `python_stdout.txt`, `python_table.txt`       | `fortran_stdout.txt`, `fortran_table.txt`          |
| tracker   | `python_stdout.txt`, `python.ps`, `python_tracker.txt` | `fortran_stdout.txt`, `fortran.ps`, `fortran_tracker.txt` |
| viewer    | `python_stdout.txt`, `python.ps`, `python_viewer.txt` | `fortran_stdout.txt`, `fortran.ps`, `fortran_viewer.txt` |

Comparison runs when a FORTRAN binary is available (auto-detected from `fortran/Tools/` or set via `--fortran-cmd`). Exit code 0 if all outputs match; 1 if any differ or a run failed.

## Comparison rules

- **Printed output (stdout)**: The "Input Parameters" section printed to stdout by both
  Python and FORTRAN is captured to `python_stdout.txt` and `fortran_stdout.txt` and
  compared (same normalization and tolerance as tables).
- **Tables**:
  - lines are normalized (strip, collapse whitespace);
  - FORTRAN overflow markers (`*****`) are ignored at the individual field/cell level
    (only that field is excluded from numeric comparison; the row remains in the output
    and counts as a skipped-field for `--float-tol`/`--lsd-tol`; the row is not dropped
    entirely). Skipped overflow fields are reflected in the diff summary and exit code
    where applicable;
  - numeric fields can be compared with `--float-tol` (significant digits) and/or
    `--lsd-tol` (least-significant-digit tolerance).
- **PostScript**: Variable headers such as `%%Creator` and `%%CreationDate` are ignored so only structural and drawing differences are reported.

In `--test-file` batch mode, `summary.txt` includes `largest_table_abs_diff=<value>`
for the largest numeric table difference seen across the run.

## FORTRAN setup

The FORTRAN tools in `fortran/Tools/` are built with Make (see `make_ephem.sh`, `make_trackers.sh`, `make_viewers.sh`). Binaries: `ephem3_xxx.bin`, `tracker3_xxx.bin`, `viewer3_jup.bin`, `viewer3_mar.bin`, `viewer3_nep.bin`, `viewer3_plu.bin`, `viewer3_sat.bin`, `viewer3_ura.bin`. They expect:

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
run_fortran(spec, ["/path/to/fortran/Tools/ephem3_xxx.bin"], out_table=out / "fort.txt")
result = compare_tables(out / "py.txt", out / "fort.txt", lsd_tolerance=1)
print(result.same, result.message)
```
