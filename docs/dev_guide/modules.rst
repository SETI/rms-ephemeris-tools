.. _modules_overview:

Module descriptions
====================

Root package (ephemeris_tools)
------------------------------

- :py:mod:`ephemeris_tools.angle_utils`: Parsing of angle strings (hours, deg, d m s, etc.) for RA/Dec and viewer.
- :py:mod:`ephemeris_tools.config`: Path resolution for SPICE_PATH, TEMP_PATH, STARLIST_PATH.
- :py:mod:`ephemeris_tools.constants`: NAIF body IDs (planets, sun, moon), spacecraft codes, column IDs.
- :py:mod:`ephemeris_tools.params`: Dataclasses (:py:class:`~ephemeris_tools.params.EphemerisParams`, etc.) and env-based parsing for ephemeris/tracker/viewer.
- :py:mod:`ephemeris_tools.record`: Formatting of ephemeris table rows (fixed-width columns).
- :py:mod:`ephemeris_tools.input_params`: Writing of input parameter blocks to a stream (ephemeris/tracker/viewer).
- :py:mod:`ephemeris_tools.ephemeris`: Ephemeris table generation loop; SPICE calls and column output.
- :py:mod:`ephemeris_tools.time_utils`: Time string parsing, interval-to-seconds, TAI/day/sec and TDB conversion helpers.
- :py:mod:`ephemeris_tools.stars`: Star catalog reader (name, RA, Dec from file).
- :py:mod:`ephemeris_tools.tracker`: Moon tracker orchestration; time loop and call into rendering.
- :py:mod:`ephemeris_tools.viewer`: Planet viewer orchestration; config, geometry, and call into draw_view.

CLI (ephemeris_tools.cli)
-------------------------

- :py:mod:`ephemeris_tools.cli.cgi`: CGI-compatible env reading: :py:func:`~ephemeris_tools.cli.cgi.get_env`,
  :py:func:`~ephemeris_tools.cli.cgi.get_key`, :py:func:`~ephemeris_tools.cli.cgi.get_keys` (sanitized).
- :py:mod:`ephemeris_tools.cli.main`: Argument parsers for ephemeris, tracker, viewer; dispatch to ephemeris/tracker/viewer; :py:func:`~ephemeris_tools.cli.main.main` and :py:func:`~ephemeris_tools.cli.main.cli_main`.

Planets (ephemeris_tools.planets)
---------------------------------

- :py:mod:`ephemeris_tools.planets.base`: :py:class:`~ephemeris_tools.planets.base.MoonSpec`, :py:class:`~ephemeris_tools.planets.base.RingSpec`, :py:class:`~ephemeris_tools.planets.base.ArcSpec`, :py:class:`~ephemeris_tools.planets.base.PlanetConfig`.
- :py:mod:`ephemeris_tools.planets.mars`, :py:mod:`~ephemeris_tools.planets.jupiter`, :py:mod:`~ephemeris_tools.planets.saturn`, :py:mod:`~ephemeris_tools.planets.uranus`, :py:mod:`~ephemeris_tools.planets.neptune`, :py:mod:`~ephemeris_tools.planets.pluto`: Planet-specific config (planet_id, moons, rings, arcs, starlist).

SPICE (ephemeris_tools.spice)
-----------------------------

- :py:mod:`ephemeris_tools.spice.common`: Global state (planet, observer, loaded flags, time shifts); :py:func:`~ephemeris_tools.spice.common.get_state`.
- :py:mod:`ephemeris_tools.spice.load`: :py:func:`~ephemeris_tools.spice.load.load_spice_files`, :py:func:`~ephemeris_tools.spice.load.load_spacecraft`; reads SPICE_planets.txt / SPICE_spacecraft.txt.
- :py:mod:`ephemeris_tools.spice.observer`: :py:func:`~ephemeris_tools.spice.observer.set_observer_id`, :py:func:`~ephemeris_tools.spice.observer.set_observer_location`, :py:func:`~ephemeris_tools.spice.observer.observer_state` (6-vector in J2000).
- :py:mod:`ephemeris_tools.spice.bodmat`: Body-fixed rotation matrices (J2000 to body); tipbod and orbit fallback for moons.
- :py:mod:`ephemeris_tools.spice.geometry`: Body lat/lon (sub-observer, sub-solar), anti-sun, limb radius, planet ranges, moon tracker offsets.
- :py:mod:`ephemeris_tools.spice.orbits`: Observer ring opening (obs_b, obs_long), moon_distances (offsets, limb angle).
- :py:mod:`ephemeris_tools.spice.rings`: Ring opening geometry, ring_radec, ansa_radec (with edge-case handling).
- :py:mod:`ephemeris_tools.spice.shifts`: Time-shift support for moon orbits; :py:func:`~ephemeris_tools.spice.shifts.spkapp_shifted`.

Rendering (ephemeris_tools.rendering)
-------------------------------------

- :py:mod:`ephemeris_tools.rendering.geometry3d`: 3D helpers: ellipsoid limb, segment-ellipse intersect, ray-plane intersect, FOV clip.
- :py:mod:`ephemeris_tools.rendering.planet_grid`: Planet grid (meridians, latitude circles) in plot coords; limb radius.
- :py:mod:`ephemeris_tools.rendering.euclid`: Low-level drawing (bodies, rings, segments) and view state; port of FORTRAN Euclid layer. Submodules: ``constants``, ``vec_math``, ``ellipse``, ``segment_plane``, ``state``, ``init_geom`` (euinit, euview, eugeom), ``body`` (eubody), ``ring`` (euring), ``star_temp`` (eustar, eutemp), ``clear`` (euclr).
- :py:mod:`ephemeris_tools.rendering.escher`: PostScript buffer and mapping (FOV to pixel/line); port of FORTRAN Escher layer. Submodules: ``constants``, ``state``, ``ps_output`` (esfile, esdr07, eslwid, etc.), ``view`` (esview, esdraw, esdump, esclr).
- :py:mod:`ephemeris_tools.rendering.postscript`: PostScript file header/footer and prolog helpers.
- :py:mod:`ephemeris_tools.rendering.draw_tracker`: Tracker-specific drawing: time axis, moon positions, tick marks and labels.
- :py:mod:`ephemeris_tools.rendering.draw_view`: Viewer-specific drawing: bodies, rings, arcs, stars, labels; calls euclid/escher and planet_grid.
