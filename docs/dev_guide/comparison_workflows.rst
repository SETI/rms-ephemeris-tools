.. _comparison_workflows:

Comparison Workflows
====================

This page documents helper commands for generating random CGI inputs and running
FORTRAN-vs-Python comparisons.

Random query generation
-----------------------

Use ``scripts/generate_random_query_urls.py`` to generate random URLs for a
single tool:

.. code-block:: bash

   python scripts/generate_random_query_urls.py -n 100 -o /tmp/random_viewer.txt --tool viewer

Common options:

- ``-n``: number of URLs to generate.
- ``-o``: output file path.
- ``--tool``: one of ``ephemeris``, ``tracker``, ``viewer``.

Predefined test-file comparison
-------------------------------

Use ``scripts/run-fortran-comparison-test-files.sh`` to run the FORTRAN
comparison using the hand-written URL lists in ``test_files/``:

.. code-block:: bash

   ./scripts/run-fortran-comparison-test-files.sh --jobs 8

This uses ``test_files/ephemeris-test-urls.txt``, ``test_files/tracker-test-urls.txt``,
and ``test_files/viewer-test-urls.txt``. Optional ``--jobs N`` is passed to
``tests.compare_fortran``. Output and failure directories are the same as below
(and are rotated if they already exist).

Batch FORTRAN comparison script (random URLs)
---------------------------------------------

Use ``scripts/run-random-fortran-comparisons.sh`` to generate random URLs and
run all three tools in one command:

.. code-block:: bash

   ./scripts/run-random-fortran-comparisons.sh 100 --jobs 8
   ./scripts/run-random-fortran-comparisons.sh 50 --dir /path/to/my/dir --jobs 4

Arguments:

- Positional ``<count>``: number of random queries generated per tool.
- Optional ``--jobs N``: parallelism passed to ``python -m tests.compare_fortran``.
- Optional ``--dir DIR``: top-level directory for output and query files (default:
  ``/tmp``). Uses ``DIR/<tool>_out``, ``DIR/<tool>_failed``, and
  ``DIR/random_queries_<tool>.txt``.

Output and failure directories
------------------------------

For each run, results are written under a top-level directory (default ``/tmp``;
override with ``--dir`` for ``run-random-fortran-comparisons.sh``):

- ``<dir>/ephemeris_out`` and ``<dir>/ephemeris_failed``
- ``<dir>/tracker_out`` and ``<dir>/tracker_failed``
- ``<dir>/viewer_out`` and ``<dir>/viewer_failed``

Random query files are written to ``<dir>/random_queries_<tool>.txt``. The
predefined test-file script (``run-fortran-comparison-test-files.sh``) always
uses ``/tmp``.

If one of those directories already exists, it is rotated before the run using
a single timestamp suffix shared by all rotated directories in that run, for
example:

- ``<dir>/viewer_out_20260226_185932``
- ``<dir>/tracker_failed_20260226_185932``

Failure artifact collection
---------------------------

When ``tests.compare_fortran`` is run with ``--collect-failed-to DIR``, all
files from each failed case directory are copied into ``DIR`` with
case-prefixed filenames (e.g. ``ephemeris_001_python_table.txt``). Collected
artifacts by tool:

- **Ephemeris**: ``comparison.txt``, ``python_stdout.txt``, ``fortran_stdout.txt``,
  ``python_table.txt``, ``fortran_table.txt``. The runner explicitly ensures
  table and stdout files are copied for ephemeris failures even when only
  summary artifacts might otherwise be present.

- **Tracker**: ``comparison.txt``, ``python_stdout.txt``, ``fortran_stdout.txt``,
  ``python.ps``, ``fortran.ps``, ``python_tracker.txt``, ``fortran_tracker.txt``,
  and any generated PNGs.

- **Viewer**: ``comparison.txt``, ``python_stdout.txt``, ``fortran_stdout.txt``,
  ``python.ps``, ``fortran.ps``, ``python_viewer.txt``, ``fortran_viewer.txt``,
  and any generated PNGs.

Server comparison
-----------------

Use ``python -m tests.compare_servers`` to compare live Ephemeris Tools
server output against stored golden copies:

.. code-block:: bash

   python -m tests.compare_servers
   python -m tests.compare_servers --replace --server staging
   python -m tests.compare_servers --test-file-paths test_files/viewer-test-urls.txt --limit-tests 0:10

Options:

- ``--run-ephemeris-type``: ``test`` or ``current`` (default: ``current``).
  Selects which SPICE kernels match the server.
- ``--replace``: Re-generate golden copies from the staging server instead of
  comparing.
- ``--test-file-paths``: One or more URL list files (default: all three in
  ``test_files/``).
- ``--golden-directory``: Path to golden copy storage (default:
  ``golden_copies``).
- ``--limit-tests``: Subset of tests as ``start:end`` (only with a single
  test file).
- ``--server``: Server to compare against (default: ``production``; or
  ``other`` for a custom URL prefix).
- ``--logfile-filename``: Custom log file name.
- ``--save-failing-tests``: Save failed outputs next to their golden copies.
- ``--hide-known-failures``: Index ranges of known failures to suppress in
  the log.

See ``tests/compare_servers/README.md`` for full details.

Parameter sweep scripts
-----------------------

The ``scripts/`` directory includes parameter sweep scripts that exercise
``ephemeris-tools`` across many input combinations and write outputs with
descriptive filenames.

.. list-table:: Parameter sweep scripts
   :header-rows: 1
   :widths: 35 15 20 15

   * - Script
     - Tool
     - Output
     - PS to PNG
   * - ``test_ephemeris_param_sweep.sh``
     - ephemeris
     - ``.txt`` tables
     - N/A
   * - ``test_viewer_param_sweep.sh``
     - viewer
     - ``.ps`` then ``.png``
     - Yes (PS removed)
   * - ``test_tracker_param_sweep.sh``
     - tracker
     - ``.ps`` + ``.txt`` then ``.png``
     - Yes (PS removed)

Usage:

.. code-block:: bash

   ./scripts/test_ephemeris_param_sweep.sh [OUTDIR]
   ./scripts/test_viewer_param_sweep.sh [OUTDIR]
   ./scripts/test_tracker_param_sweep.sh [OUTDIR]

Set ``EPHEMERIS_TOOLS_CMD`` to override the command (default:
``ephemeris-tools``). Viewer and tracker sweeps require
`Ghostscript <https://www.ghostscript.com/>`__ for PS to PNG conversion.

Quality checks
--------------

Use ``scripts/run-all-checks.sh`` to run linting, type checking, tests,
Sphinx build, and Markdown lint in one command:

.. code-block:: bash

   ./scripts/run-all-checks.sh           # all checks, parallel (default)
   ./scripts/run-all-checks.sh -s        # sequential
   ./scripts/run-all-checks.sh -c        # code checks only (ruff, mypy, pytest)
   ./scripts/run-all-checks.sh -d        # docs checks only (sphinx, pymarkdown)
   ./scripts/run-all-checks.sh -m        # markdown lint only

Options:

- ``-p`` / ``--parallel``: Run checks in parallel (default).
- ``-s`` / ``--sequential``: Run checks sequentially.
- ``-c`` / ``--code``: Code checks only (ruff, mypy, pytest).
- ``-d`` / ``--docs``: Documentation checks only (Sphinx, PyMarkdown).
- ``-m`` / ``--markdown``: Markdown lint only.
