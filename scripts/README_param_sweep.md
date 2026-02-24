# Parameter sweep test scripts

These scripts run `ephemeris-tools` many times, varying one parameter (and some combinations), and write outputs to obviously-named files for validation.

**Random URL generator:** `generate_random_cgi_queries.py` produces random full CGI URLs (one per line) for viewer/tracker/ephemeris using host `pds-rings.seti.org`. Example: `python scripts/generate_random_cgi_queries.py -n 100 -o urls.txt` (see script docstring for options).

## Scripts

| Script | Tool | Output | PS→PNG |
|--------|------|--------|--------|
| `test_ephemeris_param_sweep.sh` | ephemeris | `.txt` tables | N/A |
| `test_viewer_param_sweep.sh` | viewer | `.ps` → `.png` | Yes (then PS removed) |
| `test_tracker_param_sweep.sh` | tracker | `.ps` + `.txt` → `.png` + `.txt` | Yes (PS removed) |

## Usage

```bash
# From repo root (after: pip install -e .)
./scripts/test_ephemeris_param_sweep.sh [OUTDIR]   # default: ./param_sweep_ephemeris
./scripts/test_viewer_param_sweep.sh [OUTDIR]     # default: ./param_sweep_viewer
./scripts/test_tracker_param_sweep.sh [OUTDIR]    # default: ./param_sweep_tracker
```

Optional: set `EPHEMERIS_TOOLS_CMD` to use a different command (e.g. `python -m ephemeris_tools.cli.main`).

## Requirements

- **ephemeris-tools** on PATH (or install from repo: `pip install -e .`)
- **viewer / tracker**: **ghostscript** (`gs`) for PostScript → PNG conversion

## What each script varies

- **Ephemeris**: planet, columns (IDs and names), mooncols (IDs and names), moons (per planet), and combinations.
- **Viewer**: planet, moons, rings (per planet), fov/fov-unit, and combinations.
- **Tracker**: planet, moons, rings, xrange/xunit, and combinations.

Output filenames are descriptive (e.g. `ephem_planet_saturn.txt`, `viewer_uranus_rings_alpha.png`, `tracker_saturn_moons_rings.txt`).
