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

Planetary ephemeris generator, moon tracker, and planet viewer (Python port of
the PDS Ring-Moon Systems Node FORTRAN tools).

# Quick Start

## Environment setup

### 1. Python and virtual environment

- **Python**: 3.10 or newer.
- Use an isolated environment; do not install into system Python.

```bash
python3 -m venv .venv
source .venv/bin/activate   # Linux/macOS
# or:  .venv\Scripts\activate   # Windows
```

### 2. Install the package

```bash
pip install -e .
```

For development (tests, linting, type-checking):

```bash
pip install -e ".[dev]"
```

Optional rendering backend (matplotlib):

```bash
pip install -e ".[render]"
```

### 3. Environment variables

| Variable | Purpose | Default |
|----------|---------|---------|
| **`SPICE_PATH`** | Root directory for SPICE kernels. Must contain `SPICE_planets.txt`, `SPICE_spacecraft.txt`, and kernel files (e.g. `leapseconds.ker`, planet/moon SPKs). | `/var/www/SPICE/` |
| `TEMP_PATH` | Directory for temporary or output files. | `/var/www/work/` |
| `STARLIST_PATH` | Directory for star catalog files (e.g. `starlist_sat.txt`). | `/var/www/documents/tools/` |
| `JULIAN_LEAPSECS` | Path to a **NAIF LSK** leap-second file (e.g. `naif0012.tls`). If unset, the code looks for `naif0012.tls` (or similar) under `SPICE_PATH`, then `leapsecs.txt`. If that file is missing or not in LSK format, rms-julian’s bundled LSK is used. | (see above) |
| `EPHEMERIS_TOOLS_LOG` | Logging level: `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. | (default: WARNING) |

**Example (Linux/macOS):**

```bash
export SPICE_PATH=/path/to/your/SPICE
export TEMP_PATH=/tmp
```

**Example (.env or shell):**

```bash
SPICE_PATH=/data/SPICE
```

Ensure `SPICE_PATH` contains (or points to) the expected config and kernel files so that `load_spice_files()` and `load_spacecraft()` can find them.

### 4. SPICE kernel layout

Under `SPICE_PATH` the code expects:

- `SPICE_planets.txt` — planet/ephemeris version and kernel filenames.
- `SPICE_spacecraft.txt` — spacecraft IDs and kernel filenames (for observer).
- `leapseconds.ker` (or `leapsecs.txt` for rms-julian) — leap seconds.
- Kernel files referenced in the config (e.g. planetary SPKs, LSK).

Without these, ephemeris/tracker/viewer runs will fail when loading kernels.

## Running the tools

CLI entry point:

```bash
ephemeris-tools <command> [options]
```

### Ephemeris table

```bash
ephemeris-tools ephemeris --planet 6 --start "2025-01-01 00:00" --stop "2025-01-01 02:00" --interval 1 --time-unit hour -o ephem.txt
```

- `--planet`: 4=Mars, 5=Jupiter, 6=Saturn, 7=Uranus, 8=Neptune, 9=Pluto.
- `--cgi`: read parameters from environment (e.g. for CGI/web).
- `-v` / `--verbose`: set log level to INFO (otherwise WARNING and above go to stderr).

### Moon tracker

```bash
ephemeris-tools tracker --planet 6 --start "2025-01-01 00:00" --stop "2025-01-02 00:00" -o tracker.ps
```

### Planet viewer

```bash
ephemeris-tools viewer --planet 6 --time "2025-01-01 12:00" -o view.ps
```

## Testing

With the dev extras installed:

```bash
pytest tests/ -v
```

Tests that do not require SPICE (e.g. params, record formatting) run without `SPICE_PATH`. Tests or commands that load kernels need a valid `SPICE_PATH` and kernel set.

To run a quick check without SPICE:

```bash
pytest tests/test_ephemeris.py -v
```

Lint and type-check:

```bash
ruff check src tests
ruff format src tests
mypy src
```

# Installation

## Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/SETI/rms-ephemeris-tools.git
   cd rms-ephemeris-tools
   ```

2. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the package (editable with dev tools):

   ```bash
   pip install -e ".[dev]"
   ```

   Or install only runtime dependencies: `pip install -e .`

4. Set up SPICE kernels:
   - Download the required SPICE kernels for your mission
   - Set the `SPICE_PATH` environment variable to point to your kernels directory:

     ```bash
     export SPICE_PATH=/path/to/your/spice/kernels
     ```

> **Note**: To fix mypy operability with editable pip installs:
>
> ```bash
> export SETUPTOOLS_ENABLE_FEATURES="legacy-editable"
> ```

# Documentation

Comprehensive documentation is available in the `docs` directory.

To build the documentation:

```bash
cd docs
make html
```

The built documentation will be available in `docs/_build/html`.

# Contributing

Information on contributing to this package can be found in the
[Contributing Guide](https://github.com/SETI/rms-ephemeris-tools/blob/main/CONTRIBUTING.md).

# Licensing

This code is licensed under the [Apache License v2.0](https://github.com/SETI/rms-ephemeris-tools/blob/main/LICENSE).
