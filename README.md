# rms-ephemeris-tools

<!-- pyml disable MD025 -->

[![GitHub release; latest by date](https://img.shields.io/github/v/release/SETI/rms-ephemeris-tools)](https://github.com/SETI/rms-ephemeris-tools/releases)
[![GitHub Release Date](https://img.shields.io/github/release-date/SETI/rms-ephemeris-tools)](https://github.com/SETI/rms-ephemeris-tools/releases)
[![Test Status](https://img.shields.io/github/actions/workflow/status/SETI/rms-ephemeris-tools/run-tests.yml?branch=main)](https://github.com/SETI/rms-ephemeris-tools/actions)
[![Documentation Status](https://readthedocs.org/projects/rms-ephemeris-tools/badge/?version=latest)](https://rms-ephemeris-tools.readthedocs.io/en/latest/?badge=latest)
[![Code coverage](https://img.shields.io/codecov/c/github/SETI/rms-ephemeris-tools/main?logo=codecov)](https://codecov.io/gh/SETI/rms-ephemeris-tools)
<br />
[![PyPI - Version](https://img.shields.io/pypi/v/rms-ephemeris-tools)](https://pypi.org/project/rms-ephemeris-tools)
[![PyPI - Format](https://img.shields.io/pypi/format/rms-ephemeris-tools)](https://pypi.org/project/rms-ephemeris-tools)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/rms-ephemeris-tools)](https://pypi.org/project/rms-ephemeris-tools)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/rms-ephemeris-tools)](https://pypi.org/project/rms-ephemeris-tools)
<br />
[![GitHub commits since latest release](https://img.shields.io/github/commits-since/SETI/rms-ephemeris-tools/latest)](https://github.com/SETI/rms-ephemeris-tools/commits/main/)
[![GitHub commit activity](https://img.shields.io/github/commit-activity/m/SETI/rms-ephemeris-tools)](https://github.com/SETI/rms-ephemeris-tools/commits/main/)
[![GitHub last commit](https://img.shields.io/github/last-commit/SETI/rms-ephemeris-tools)](https://github.com/SETI/rms-ephemeris-tools/commits/main/)
<br />
[![Number of GitHub open issues](https://img.shields.io/github/issues-raw/SETI/rms-ephemeris-tools)](https://github.com/SETI/rms-ephemeris-tools/issues)
[![Number of GitHub closed issues](https://img.shields.io/github/issues-closed-raw/SETI/rms-ephemeris-tools)](https://github.com/SETI/rms-ephemeris-tools/issues)
[![Number of GitHub open pull requests](https://img.shields.io/github/issues-pr-raw/SETI/rms-ephemeris-tools)](https://github.com/SETI/rms-ephemeris-tools/pulls)
[![Number of GitHub closed pull requests](https://img.shields.io/github/issues-pr-closed-raw/SETI/rms-ephemeris-tools)](https://github.com/SETI/rms-ephemeris-tools/pulls)
<br />
![GitHub License](https://img.shields.io/github/license/SETI/rms-ephemeris-tools)
[![Number of GitHub stars](https://img.shields.io/github/stars/SETI/rms-ephemeris-tools)](https://github.com/SETI/rms-ephemeris-tools/stargazers)
![GitHub forks](https://img.shields.io/github/forks/SETI/rms-ephemeris-tools)
[![DOI](https://zenodo.org/badge/rms-ephemeris-tools.svg)](https://zenodo.org/badge/latestdoi/{rms-ephemeris-tools})
<!-- start-after-point -->

# Introduction

Planetary ephemeris generator, moon tracker, and planet viewer (Python port of the PDS Ring-Moon Systems Node FORTRAN tools).

Full documentation: [Read the Docs](https://rms-ephemeris-tools.readthedocs.io).

# For users

## Install

Create a virtual environment and install the package into it (do not install into system Python):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install rms-ephemeris-tools
```

This provides the `ephemeris-tools` command.

To deploy the bundled web forms and sample files (e.g. for a CGI server), use the
`install_ephemeris_tools_files` command with a target directory:

```bash
install_ephemeris_tools_files /path/to/htdocs/tools
```

Files from the package’s `web/tools` tree are copied into the given directory
(subdirectories such as `samples/` are preserved). Works when the package is
installed from PyPI or from source.

## Environment variables

| Variable | Purpose | Default |
|----------|---------|---------|
| **SPICE_PATH** | Root directory for SPICE kernels. Must contain `SPICE_planets.txt`, `SPICE_spacecraft.txt`, and kernel files (e.g. `leapseconds.ker`, planet/moon SPKs). | `/var/www/SPICE/` |
| `TEMP_PATH` | Directory for temporary or output files. | `/var/www/work/` |
| `STARLIST_PATH` | Directory for star catalog files (e.g. `starlist_sat.txt`). | `/var/www/documents/tools/` |
| `JULIAN_LEAPSECS` | Path to a NAIF LSK leap-second file. If unset, the code looks under `SPICE_PATH`, then `leapsecs.txt`; if missing or not LSK format, rms-julian’s bundled LSK is used. | (see above) |
| `EPHEMERIS_TOOLS_LOG_LEVEL` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. | `WARNING` |

Ensure `SPICE_PATH` contains (or points to) the expected config and kernel files. Without these, ephemeris/tracker/viewer runs will fail when loading kernels.

## Running the tools

```bash
ephemeris-tools <command> [options]
```

### Ephemeris table

```bash
ephemeris-tools ephemeris --planet saturn --start "2025-01-01 00:00" --stop "2025-01-01 02:00" --interval 1 --time-unit hour -o ephem.txt
```

`--planet` accepts a name (`mars`, `jupiter`, `saturn`, `uranus`, `neptune`, `pluto`) or number 4–9. Use `--observer` as a shortcut to set the observer in one argument (e.g. `--observer Cassini` or `--observer 19.82 -155.47 4205`). Use `-v` / `--verbose` for INFO-level logging. All three subcommands accept `--cgi` to read parameters from environment variables instead of the command line (for CGI server integration). See the [CLI reference](https://rms-ephemeris-tools.readthedocs.io/en/latest/user_guide/cli.html) for the full argument list.

### Moon tracker

```bash
ephemeris-tools tracker --planet saturn --start "2025-01-01 00:00" --stop "2025-01-02 00:00" -o tracker.ps
```

To convert the PostScript output to PNG (requires Ghostscript):

```bash
gs -dSAFER -dBATCH -dNOPAUSE -sDEVICE=png16m -r150 -sOutputFile=tracker.png tracker.ps
```

### Planet viewer

```bash
ephemeris-tools viewer --planet saturn --time "2025-01-01 12:00" -o view.ps
```

To convert the PostScript output to PNG (requires Ghostscript):

```bash
gs -dSAFER -dBATCH -dNOPAUSE -sDEVICE=png16m -r150 -sOutputFile=view.png view.ps
```

# For developers

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/SETI/rms-ephemeris-tools.git
   cd rms-ephemeris-tools
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

3. Install the package in editable mode with dev extras:

   ```bash
   pip install -e ".[dev]"
   ```

4. Set up environment variables: configure all of the variables listed in the user section (`SPICE_PATH`, `TEMP_PATH`, `STARLIST_PATH`, `JULIAN_LEAPSECS`, `EPHEMERIS_TOOLS_LOG_LEVEL`) as needed so ephemeris, tracker, and viewer runs (and tests that need kernels) can find config and kernel files.

## Documentation

Documentation is built with Sphinx and published at [Read the Docs](https://rms-ephemeris-tools.readthedocs.io). To build locally (dev extras include Sphinx):

```bash
cd docs && make html
```

Output is in `docs/_build/html`.

## Testing

With the dev extras installed:

```bash
pytest tests/ -v
```

Tests that require SPICE kernels but cannot find them (e.g. missing or invalid `SPICE_PATH`) will be **skipped**. Tests that do not need kernels run without any SPICE setup.

Lint and type-check:

```bash
ruff check src tests
ruff format src tests
mypy src
```

## Quality checks

Run linting, type checking, tests, Sphinx docs build, and Markdown lint in one command:

```bash
./scripts/run-all-checks.sh           # all checks, parallel (default)
./scripts/run-all-checks.sh -c        # code checks only (ruff, mypy, pytest)
./scripts/run-all-checks.sh -d        # docs checks only (sphinx, pymarkdown)
```

## Parameter sweep scripts

Exercise `ephemeris-tools` across many parameter combinations:

```bash
./scripts/test_ephemeris_param_sweep.sh [OUTDIR]
./scripts/test_viewer_param_sweep.sh [OUTDIR]
./scripts/test_tracker_param_sweep.sh [OUTDIR]
```

Set `EPHEMERIS_TOOLS_CMD` to override the command. Viewer and tracker sweeps require [Ghostscript](https://www.ghostscript.com/) for PS to PNG conversion. See `scripts/README_param_sweep.md` for details.

## Server comparison

Compare live server output against stored golden copies:

```bash
python -m tests.compare_servers
python -m tests.compare_servers --replace --server staging
```

See `tests/compare_servers/README.md` for full options.

## FORTRAN comparison scripts

The repository includes scripts for generating random query URLs and running FORTRAN-vs-Python comparisons.

### Generate random URLs

```bash
python scripts/generate_random_query_urls.py -n 100 -o /tmp/random_urls.txt --tool viewer
```

### Run FORTRAN comparison with predefined test files

To run the comparison using the hand-written URL lists in ``test_files/``:

```bash
./scripts/run-fortran-comparison-test-files.sh --jobs 8
```

Uses ``test_files/ephemeris-test-urls.txt``, ``test_files/tracker-test-urls.txt``, and ``test_files/viewer-test-urls.txt``. Output and failure directories are the same as for random comparisons (and are rotated if they already exist).

### Run FORTRAN comparison manually

To compare Python output against FORTRAN for a single URL or a file of URLs:

```bash
python -m tests.compare_fortran viewer --test-file /tmp/random_urls.txt -o /tmp/compare -j 4
```

Use `ephemeris`, `tracker`, or `viewer` as the tool; pass `--url <url>` for a single URL or `--test-file <path>` for a list. With multiple URLs, use `-j N` for parallel runs. See the Developer's Guide for full options.

### Random comparisons (ephemeris, tracker, viewer)

The script below generates random URLs for all three tools and runs the FORTRAN comparison for each (i.e. it runs both URL generation and `tests.compare_fortran` per tool):

```bash
./scripts/run-random-fortran-comparisons.sh 100 --jobs 8
./scripts/run-random-fortran-comparisons.sh 50 --dir /path/to/my/dir --jobs 4
```

- Positional argument: number of random queries per tool.
- Optional `--jobs N` is passed through to `tests.compare_fortran`.
- Optional `--dir DIR`: top-level directory for output and query files (default: `/tmp`). Uses `DIR/<tool>_out`, `DIR/<tool>_failed`, and `DIR/random_queries_<tool>.txt`.
- Output directories (under `/tmp` or `--dir`): `ephemeris_out`, `tracker_out`, `viewer_out`, and `ephemeris_failed`, `tracker_failed`, `viewer_failed`.
- If a target directory already exists, it is renamed with a single timestamp suffix per run (e.g. `viewer_out_20260226_185932`).

# Contributing

See the [Contributing Guide](https://github.com/SETI/rms-ephemeris-tools/blob/main/CONTRIBUTING.md).

# Licensing

Licensed under the [Apache License v2.0](https://github.com/SETI/rms-ephemeris-tools/blob/main/LICENSE).
