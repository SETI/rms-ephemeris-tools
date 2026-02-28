# Server Comparison Tests

The `tests.compare_servers` package compares live Ephemeris Tools server output (Planet Viewer, Moon Tracker, Ephemeris Generator) against stored "golden" copies, or generates new golden copies from the staging server.

Run as a module:

```bash
python -m tests.compare_servers [options]
```

Or run the script directly:

```bash
python tests/compare_servers/ephem_tools_unit_tests.py [options]
```

By default (no special options), the program compares all three tools on the production server against the golden copies in the golden directory and writes results to a log file.

## Operations

**Comparison** (default)
: Fetch HTML, PostScript, and tabular output from the requested server for each test URL. Clean responses and golden files (removing timestamps, server paths, and other non-deterministic content), then compare. Match and mismatch results are written to the log file.

**Golden copy replacement** (`--replace`)
: Fetch all outputs for each test URL from the **staging** server and save them into the golden directory. Each file is keyed by a UUID derived from the URL. Use this to refresh golden copies after intentional server or tool changes.

## Command-line options

`--run-ephemeris-type` {test,current}
: Which SPICE kernels the server uses. Use `test` for a frozen test set so results are stable across kernel updates; use `current` for the kernels currently installed on the server. Default: `current`.

`--replace`
: Replace golden copies instead of comparing. All golden files are generated from the staging server. Use `--test-file-paths` to limit which tools' golden copies are regenerated.

`--test-file-paths` PATH [PATH ...]
: Files containing test URLs (one per line). If not set, defaults to `test_files/viewer-test-urls.txt`, `test_files/tracker-test-urls.txt`, and `test_files/ephemeris-test-urls.txt`. When specified, only these files are used.

`--golden-directory` PATH
: Directory for golden copies. Default: `golden_copies` in the current working directory.

`--limit-tests` RANGE [RANGE ...]
: Run only a subset of tests. Each range is `start:end` (e.g. `1:10`). Only one test file should be in use when using this option.

`--server` {staging,production,server1,server2}|HOST|URL
: Server used for **comparison** (ignored when `--replace` is used). Keywords: `staging`, `production`, `server1`, `server2`. Otherwise provide a host name or URL prefix. Default: `production`.

`--logfile-filename` NAME
: Log file path. Default: `ephem_tools_unit_test_YYYY-MM-DD-HH-MM-SS.log`.

`--save-failing-tests`
: Write failing comparison responses into a `failed_tests` directory for inspection.

`--hide-known-failures` RANGE [RANGE ...]
: Treat specified test indices as known failures: log a warning instead of an error and do not count as failure. Use `start:end` format. Only one test file should be in use when using this option.
