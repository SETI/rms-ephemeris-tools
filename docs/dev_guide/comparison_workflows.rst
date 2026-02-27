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
