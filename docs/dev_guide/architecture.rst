.. _architecture:

Architecture
============

Overview
--------

rms-ephemeris-tools is a Python port of the PDS Ring-Moon Systems Node FORTRAN
tools. It provides:

1. **Ephemeris generator** — Time-series tables of planetary and moon positions,
   geometry (phase, opening, distances), and optional columns (RA/Dec, etc.).
2. **Moon tracker** — Time-series PostScript plots of moon positions relative to
   the planet limb and rings, with optional text tables.
3. **Planet viewer** — PostScript sky charts showing planet, moons, rings, and
   background stars at a given time.

All three tools rely on **NAIF SPICE** (via the **cspyce** library) for
ephemerides and geometry, and **rms-julian** for time conversions where needed.

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
- **Tracker**: :py:mod:`ephemeris_tools.tracker` drives the time loop and
  delegates PostScript rendering to :py:mod:`ephemeris_tools.rendering.draw_tracker`
  and Euclid/Escher layers.
- **Viewer**: :py:mod:`ephemeris_tools.viewer` loads config (planet/moons/rings),
  computes geometry (SPICE, :py:mod:`ephemeris_tools.spice.geometry`), and
  delegates drawing to :py:mod:`ephemeris_tools.rendering.draw_view`, which uses
  :py:mod:`ephemeris_tools.rendering.euclid`, :py:mod:`ephemeris_tools.rendering.escher`,
  and :py:mod:`ephemeris_tools.rendering.planet_grid`.

Package layout
--------------

- **ephemeris_tools** (root): Core entry points and shared utilities.
- **ephemeris_tools.cli**: Argument parsing, CGI env reading, and command
  dispatch (ephemeris, tracker, viewer).
- **ephemeris_tools.params**: Dataclasses and env-based parameter parsing for
  ephemeris/tracker/viewer.
- **ephemeris_tools.spice**: SPICE loading, observer state, body matrices,
  geometry (lat/lon, rings, orbits), and time-shift support for moons.
- **ephemeris_tools.planets**: Planet-specific config (moons, rings, arcs) for
  Mars, Jupiter, Saturn, Uranus, Neptune, Pluto.
- **ephemeris_tools.rendering**: PostScript/Euclid/Escher pipeline: 3D geometry,
  projection, and drawing (draw_tracker, draw_view, planet_grid, etc.). The
  Euclid and Escher layers are implemented as packages (``euclid``, ``escher``)
  with submodules; their public APIs are unchanged and documented under
  :py:mod:`ephemeris_tools.rendering.euclid` and
  :py:mod:`ephemeris_tools.rendering.escher`.

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
- Optional: **matplotlib** for some rendering backends

Testing and quality
-------------------

- **pytest**: Unit and integration tests under ``tests/``.
- **ruff**: Linting and formatting (line length 100).
- **mypy**: Static type checking; all public APIs annotated.
- **Sphinx**: Documentation under ``docs/``; build with ``cd docs && make html``.
