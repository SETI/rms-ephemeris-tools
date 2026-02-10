# rms-ephemeris-tools

Planetary ephemeris generator, moon tracker, and planet viewer (Python port of the PDS Ring-Moon Systems Node FORTRAN tools). Uses SPICE kernels via [cspyce](https://github.com/SetiInstitute/cspyce) and [rms-julian](https://github.com/SetiInstitute/rms-julian) for time conversions.

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

## License

Apache-2.0.
