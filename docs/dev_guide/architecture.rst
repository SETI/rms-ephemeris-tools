.. _architecture:

Architecture
============

Overview
--------

rms-ephemeris-tools is a Python port of the PDS Ring-Moon Systems Node FORTRAN
tools. It provides:

1. **Ephemeris generator** — Time-series tables of planetary and moon positions,
   geometry (phase, opening, distances), and optional columns (RA/Dec, etc.).
2. **Moon tracker** — Time-series plots of moon positions relative to the planet
   limb and rings, with optional text tables.  Default output is **PNG** via the
   Matplotlib backend; legacy PostScript is available with ``--backend escher``.
3. **Planet viewer** — Sky charts showing planet, moons, rings, and background
   stars at a given time.  Default output is **PNG** via the Matplotlib backend;
   legacy PostScript is available with ``--backend escher``.

All three tools rely on **NAIF SPICE** (via the **cspyce** library) for
ephemerides and geometry, and **rms-julian** for time conversions where needed.

Rendering backends
------------------

Tracker and viewer support two rendering backends selected with ``--backend``
(CLI) or the ``BACKEND`` environment variable (CGI):

.. list-table::
   :header-rows: 1
   :widths: 15 15 70

   * - Backend
     - Flag
     - Description
   * - ``mpl`` *(default)*
     - ``--backend mpl``
     - Matplotlib-based renderer.  Output format is inferred from the ``-o``
       file extension (``png``, ``pdf``, ``svg``, ``ps``/``eps``); defaults to
       PNG.  Resolution is controlled by ``--dpi`` (default 150).
   * - ``escher``
     - ``--backend escher``
     - Legacy PostScript renderer (FORTRAN-compatible).  Output must be a
       ``.ps`` file.  Used by FORTRAN byte-for-byte comparison tests.

The Matplotlib backend consumes the same 3D line segments produced by the
**Euclid** 3D engine via the :py:class:`~ephemeris_tools.rendering.protocols.SegmentSink`
protocol.  The Escher adapter (:py:class:`~ephemeris_tools.rendering.escher.sink.EscherSink`)
wraps the existing ``EscherViewState``/``EscherState`` pair to satisfy the same
protocol, so FORTRAN-parity tests are unaffected.

High-level flow
----------------

- **CLI** (``ephemeris_tools.cli.main``) parses arguments and builds parameter
  objects (e.g. :py:class:`ephemeris_tools.params.EphemerisParams`). For CGI,
  parameters are read from the environment via ``ephemeris_tools.cli.cgi``.
- **Parameters** are defined in :py:mod:`ephemeris_tools.params` (dataclasses and
  env parsing). Ephemeris-specific input writing is in
  :py:mod:`ephemeris_tools.input_params`.
- **SPICE** must be loaded before ephemeris/tracker/viewer runs:
  :py:func:`ephemeris_tools.spice.load.load_spice_files` (and optionally
  :py:func:`ephemeris_tools.spice.load.load_spacecraft`). Observer and time
  setup use :py:mod:`ephemeris_tools.spice.observer` and
  :py:mod:`ephemeris_tools.spice.common` (global state).
- **Ephemeris**: :py:mod:`ephemeris_tools.ephemeris` iterates over time steps,
  calls SPICE for positions and geometry, and writes formatted rows via
  :py:mod:`ephemeris_tools.record`.
- **Tracker**: :py:mod:`ephemeris_tools.tracker` drives the time loop, then
  dispatches to :py:mod:`ephemeris_tools.rendering.draw_tracker` (Escher) or
  :py:mod:`ephemeris_tools.rendering.mpl.renderer_tracker` (Matplotlib) depending
  on ``params.backend``.
- **Viewer**: :py:mod:`ephemeris_tools.viewer` loads config (planet/moons/rings),
  computes geometry (SPICE, :py:mod:`ephemeris_tools.spice.geometry`), then
  dispatches to :py:mod:`ephemeris_tools.rendering.draw_view` (Escher) or
  :py:mod:`ephemeris_tools.rendering.mpl.renderer_view` (Matplotlib) depending
  on ``params.backend``.

Package layout
--------------

- **ephemeris_tools** (root): Core entry points and shared utilities, including
  :py:mod:`~ephemeris_tools.viewer_helpers` (FOV table, labels),
  :py:mod:`~ephemeris_tools.params_env` (CGI env→dataclass), and
  :py:mod:`~ephemeris_tools.install_web_tools` (``install_ephemeris_tools_files``
  console script for deploying web forms).
- **ephemeris_tools.cli**: Argument parsing, CGI env reading, and command
  dispatch (ephemeris, tracker, viewer).
- **ephemeris_tools.params**: Dataclasses and CLI-based parameter parsing for
  ephemeris/tracker/viewer. ``params_env`` builds the same dataclasses from
  CGI-style environment variables and is re-exported through ``params``.
- **ephemeris_tools.spice**: SPICE loading, observer state, body matrices,
  geometry (lat/lon, rings, orbits), and time-shift support for moons.
- **ephemeris_tools.planets**: Planet-specific config (moons, rings, arcs) for
  Mars, Jupiter, Saturn, Uranus, Neptune, Pluto.
- **ephemeris_tools.rendering**: 3D geometry and rendering pipeline.

  - ``euclid/`` — 3D scene engine (ellipsoid limbs, terminators, rings,
    occultation, eclipses).  Emits 3D camera-frame segments via the
    :py:class:`~ephemeris_tools.rendering.protocols.SegmentSink` protocol.
  - ``escher/`` — Legacy PostScript device layer.  ``EscherSink`` adapts the
    ``EscherViewState``/``EscherState`` pair to ``SegmentSink``.
  - ``mpl/`` — Matplotlib backend.  ``MplCanvas`` implements ``SegmentSink``;
    ``renderer_view`` and ``renderer_tracker`` drive the full figure pipeline.
  - ``protocols.py`` — ``SegmentSink`` protocol definition.
  - ``draw_tracker.py``, ``draw_view*.py`` — Escher rendering orchestration
    (unchanged from FORTRAN port; used for the escher backend path).

Data flow
---------

- **Time**: User times (strings) → parsed via :py:mod:`ephemeris_tools.time_utils`
  → TAI/day+sec → TDB/ET for SPICE.
- **Observer**: Set via :py:func:`ephemeris_tools.spice.observer.set_observer_id`
  or :py:func:`ephemeris_tools.spice.observer.set_observer_location`; state in
  :py:mod:`ephemeris_tools.spice.common`.
- **Planet/moon IDs**: From :py:mod:`ephemeris_tools.constants` and
  :py:mod:`ephemeris_tools.planets`; SPICE kernels loaded per planet/version in
  :py:mod:`ephemeris_tools.spice.load`.

Dependencies
------------

- **cspyce**: SPICE API for Python
- **rms-julian**: Time parsing and conversions (used where needed)
- **numpy**: Arrays (e.g. rotation matrices, state vectors)
- **matplotlib** ≥ 3.8: Matplotlib backend for tracker/viewer (lazy-loaded;
  only imported when the ``mpl`` backend is invoked)

Testing and quality
-------------------

- **pytest**: Unit and integration tests under ``tests/``.
- **FORTRAN comparison**: Run Python vs FORTRAN with identical inputs.  Use
  ``scripts/run-fortran-comparison-test-files.sh`` for the predefined URL lists
  in ``test_files/``, or ``scripts/run-random-fortran-comparisons.sh`` for
  random URLs.  See :ref:`comparison_workflows`.

  .. note::
     FORTRAN byte-for-byte PostScript comparison tests always run through the
     ``escher`` backend.  The ``mpl`` backend produces a freely redesigned
     layout and is not subject to PostScript parity checks.

- **ruff**: Linting and formatting (line length 100).
- **mypy**: Static type checking; all public APIs annotated.
- **Sphinx**: Documentation under ``docs/``; build with ``cd docs && make html``.
