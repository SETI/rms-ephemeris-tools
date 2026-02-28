.. _cli:

Command-line interface
======================

The main entry point is:

.. code-block:: bash

   ephemeris-tools <command> [options]

where ``<command>`` is one of ``ephemeris``, ``tracker``, or ``viewer``.

Global options
--------------

These options are available on every subcommand:

``-v`` / ``--verbose``
   Enable verbose logging (INFO level). Without this flag only warnings and
   errors are printed.  Default: off.

   .. code-block:: bash

      ephemeris-tools ephemeris -v --planet saturn --start "2025-01-01" ...

.. _cli-ephemeris:

Ephemeris command
-----------------

Generate a time-series ephemeris table (planet/moon geometry at each time step).

.. code-block:: bash

   ephemeris-tools ephemeris [options]

Example:

.. code-block:: bash

   ephemeris-tools ephemeris --planet saturn --start "2025-01-01 00:00" \
       --stop "2025-01-02 00:00" --interval 1 --time-unit hour \
       --columns ymdhms radec phase --moons mimas enceladus \
       -o ephem.txt

**Planet and time range**

``--planet``
   Planet number (4-9) or case-insensitive name.
   Values: ``4`` / ``mars``, ``5`` / ``jupiter``, ``6`` / ``saturn``,
   ``7`` / ``uranus``, ``8`` / ``neptune``, ``9`` / ``pluto``.
   Default: ``6`` (Saturn).

   .. code-block:: bash

      --planet saturn
      --planet 5

``--start``
   Start time as a date/time string.
   Default: ``""`` (empty; required for a meaningful run).

   .. code-block:: bash

      --start "2025-01-01 00:00"

``--stop``
   Stop time as a date/time string.
   Default: ``""`` (empty; required for a meaningful run).

   .. code-block:: bash

      --stop "2025-01-03 00:00"

``--interval``
   Time step size (in units given by ``--time-unit``).
   Default: ``1.0``.

   .. code-block:: bash

      --interval 12

``--time-unit``
   Unit for ``--interval``.
   Values: ``sec``, ``min``, ``hour``, ``day``.
   Default: ``hour``.

   .. code-block:: bash

      --time-unit day

``--ephem``
   Ephemeris version number.  ``0`` selects the latest available version.
   Available versions are listed in ``SPICE_planets.txt`` under ``SPICE_PATH``.
   Default: ``0``.

   .. code-block:: bash

      --ephem 0

**Observer position**

``--observer``
   Convenience shortcut that sets the observer in one argument.  Accepts a
   single name (e.g. ``earth``, ``Cassini``), the keyword ``latlon`` followed
   by latitude, longitude, and optional altitude (e.g. ``19.82 -155.47 4205``),
   or a numeric latitude/longitude/altitude triple.  When given, ``--observer``
   takes precedence over ``--viewpoint``, ``--observatory``, ``--latitude``,
   ``--longitude``, and ``--altitude``.
   Default: not set.

   .. code-block:: bash

      --observer earth
      --observer Cassini
      --observer 19.82 -155.47 4205

``--viewpoint``
   Observer type.  Use ``observatory`` to observe from a named
   observatory or spacecraft (specified by ``--observatory``), or ``latlon``
   to observe from a geographic position on Earth (specified by
   ``--latitude`` / ``--longitude`` / ``--altitude``).
   Default: ``observatory``.

   .. code-block:: bash

      --viewpoint observatory
      --viewpoint latlon

``--observatory``
   Observatory or spacecraft name (used when ``--viewpoint`` is ``observatory``).
   Default: ``"Earth's center"``.
   Accepted spacecraft names (case-insensitive): ``Voyager 1`` (``VG1``),
   ``Voyager 2`` (``VG2``), ``Galileo`` (``GLL``), ``Cassini`` (``CAS``),
   ``New Horizons`` (``NH``), ``Juno`` (``JNO``), ``Europa Clipper`` (``EC``),
   ``JUICE`` (``JCE``), ``JWST``, ``HST``.
   See :ref:`reference` for the full table.

   .. code-block:: bash

      --observatory "Earth's center"
      --observatory Cassini

``--latitude``
   Observer latitude in degrees (used when ``--viewpoint`` is ``latlon``).
   Default: not set.

   .. code-block:: bash

      --viewpoint latlon --latitude 19.82

``--longitude``
   Observer longitude in degrees (used when ``--viewpoint`` is ``latlon``).
   Default: not set.

   .. code-block:: bash

      --viewpoint latlon --longitude -155.47

``--lon-dir``
   Whether ``--longitude`` is measured east or west of the prime meridian.
   Values: ``east``, ``west``.
   Default: ``east``.

   .. code-block:: bash

      --longitude 155.47 --lon-dir west

``--altitude``
   Observer altitude in metres above sea level (used when ``--viewpoint``
   is ``latlon``).
   Default: not set (treated as 0).

   .. code-block:: bash

      --viewpoint latlon --latitude 19.82 --longitude -155.47 --altitude 4205

``--sc-trajectory``
   Spacecraft trajectory file variant (used with spacecraft observers).
   Default: ``0``.

   .. code-block:: bash

      --observatory Cassini --sc-trajectory 1

**Columns and moons**

``--columns``
   Columns to include in the ephemeris table.  Accepts integer IDs, string
   names, or a mix.  See :ref:`reference` for the full list.
   Default: ``1 2 3 15 8`` (MJD, YMDHM, YMDHMS, RA/Dec, phase angle).

   .. code-block:: bash

      --columns 1 2 3 15 8
      --columns ymdhms radec phase

``--mooncols``
   Columns to include for each moon in the ephemeris table.  Accepts integer
   IDs, string names, or a mix.  See :ref:`reference` for the full list.
   Default: ``5 6 8 9`` (RA offset, Dec offset, distance, phase angle).

   .. code-block:: bash

      --mooncols 5 6 8 9
      --mooncols radec offset phase

``--moons``
   Moons to include.  Accepts 1-based indices, NAIF IDs (>=100), or
   case-insensitive names.  See :ref:`reference` for per-planet moon lists.
   Default: none.

   .. code-block:: bash

      --moons 1 2 3
      --moons mimas enceladus titan
      --moons 1 titan 603

**Output**

``-o`` / ``--output``
   Write the ephemeris table to a file.  If not given, output is written to
   stdout.
   Default: stdout.

   .. code-block:: bash

      -o saturn_ephem.txt

``--cgi``
   Read all parameters from environment variables (CGI mode) instead of the
   command line.  Used for web-server integration.
   Default: off.

   .. code-block:: bash

      --cgi

.. _cli-tracker:

Tracker command
---------------

Generate a moon tracker PostScript plot showing moon positions over time,
with an optional text table.

.. code-block:: bash

   ephemeris-tools tracker [options]

Example:

.. code-block:: bash

   ephemeris-tools tracker --planet saturn --start "2025-01-01 00:00" \
       --stop "2025-01-02 00:00" --interval 1 --time-unit hour \
       --moons mimas enceladus tethys dione rhea titan \
       --rings main ge --title "Saturn moons" \
       -o tracker.ps --output-txt tracker.txt

**Planet and time range**

``--planet``
   Same as :ref:`ephemeris <cli-ephemeris>`.  Default: ``6`` (Saturn).

``--start``
   Same as :ref:`ephemeris <cli-ephemeris>`.  Default: ``""`` (required).

``--stop``
   Same as :ref:`ephemeris <cli-ephemeris>`.  Default: ``""`` (required).

``--interval``
   Same as :ref:`ephemeris <cli-ephemeris>`.  Default: ``1.0``.

``--time-unit``
   Same as :ref:`ephemeris <cli-ephemeris>`.  Default: ``hour``.

``--ephem``
   Same as :ref:`ephemeris <cli-ephemeris>`.  Default: ``0``.

**Observer position**

The observer arguments ``--observer``, ``--viewpoint``, ``--observatory``,
``--latitude``, ``--longitude``, ``--lon-dir``, ``--altitude``, and
``--sc-trajectory`` are the same as :ref:`ephemeris <cli-ephemeris>` with
identical defaults.

**Moons and rings**

``--moons``
   Moons to plot.  Same format as :ref:`ephemeris <cli-ephemeris>`.
   Default: none (for Saturn, defaults to the standard set of 18 moons when
   not specified).

   .. code-block:: bash

      --moons mimas enceladus titan

``--rings``
   Ring option codes or case-insensitive names.  Integers and names can be
   mixed.  The available options depend on the planet; see :ref:`reference`
   for the full list.
   Default: none.

   .. code-block:: bash

      --rings main ge
      --rings 61 62

**Plot options**

``--xrange``
   Half-range of the x-axis in units given by ``--xunit``.
   Default: auto-calculated from the outermost moon's orbit.

   .. code-block:: bash

      --xrange 200

``--xunit``
   Units for the x-axis.
   Values: ``arcsec``, ``radii``.
   Default: ``arcsec``.

   .. code-block:: bash

      --xunit radii

``--title``
   Plot title string.
   Default: ``""`` (no title).

   .. code-block:: bash

      --title "Saturn moons Jan 2025"

**Output**

``-o`` / ``--output``
   Write the PostScript plot to a file.
   Default: none (no PS output).

   .. code-block:: bash

      -o tracker.ps

``--output-txt``
   Write an accompanying text table to a file.
   Default: none (no text output).

   .. code-block:: bash

      --output-txt tracker.txt

``--cgi``
   Read all parameters from environment variables (CGI mode) instead of the
   command line.  Same as :ref:`ephemeris <cli-ephemeris>`.
   Default: off.

.. _cli-viewer:

Viewer command
--------------

Generate a planet viewer PostScript diagram showing the planet, its moons,
rings, and optional stars.

.. code-block:: bash

   ephemeris-tools viewer [options]

Example:

.. code-block:: bash

   ephemeris-tools viewer --planet saturn --time "2025-01-01 12:00" \
       --fov 0.1 --fov-unit deg --moons mimas enceladus titan \
       --center body -o view.ps --output-txt fov_table.txt

**Planet and time**

``--planet``
   Same as :ref:`ephemeris <cli-ephemeris>`.  Default: ``6`` (Saturn).

``--time``
   Observation time as a date/time string.
   Default: ``""`` (required).

   .. code-block:: bash

      --time "2025-06-15 03:30"

``--ephem``
   Same as :ref:`ephemeris <cli-ephemeris>`.  Default: ``0``.

**Field of view**

``--fov``
   Field of view size (in units given by ``--fov-unit``).
   Default: ``1.0``.

   .. code-block:: bash

      --fov 0.05

``--fov-unit``
   Unit for ``--fov``.  Accepts angle units (``deg``, ``arcmin``, ``arcsec``,
   ``mrad``, ``urad``), ``km``, ``<planet> radii`` (e.g. ``Saturn radii``),
   or an instrument FOV name (e.g. ``Cassini ISS narrow``).
   See :ref:`reference` for the full list.
   Default: ``deg``.

   .. code-block:: bash

      --fov 30 --fov-unit arcmin

**Diagram center**

``--center``
   What the diagram is centered on.
   Values: ``body``, ``ansa``, ``J2000``, ``star``.
   Default: ``body``.

   .. code-block:: bash

      --center body
      --center ansa
      --center J2000

``--center-body``
   Body name when ``--center`` is ``body``.
   Default: ``""`` (the planet itself).

   .. code-block:: bash

      --center body --center-body titan

``--center-ansa``
   Ring ansa name when ``--center`` is ``ansa``.
   Default: ``""``.

   .. code-block:: bash

      --center ansa --center-ansa "A ring"

``--center-ew``
   East or west ansa when ``--center`` is ``ansa``.
   Default: ``east``.

   .. code-block:: bash

      --center ansa --center-ew west

``--center-ra``
   Right ascension in degrees for ``J2000`` centering.
   Default: ``0.0``.

   .. code-block:: bash

      --center J2000 --center-ra 180.0 --center-dec -20.0

``--center-dec``
   Declination in degrees for ``J2000`` centering.
   Default: ``0.0``.

``--center-ra-type``
   RA input format.
   Default: ``hours``.

   .. code-block:: bash

      --center-ra-type degrees

``--center-star``
   Star name when ``--center`` is ``star``.
   Default: ``""``.

   .. code-block:: bash

      --center star --center-star "Regulus"

**Observer position**

The observer arguments ``--observer``, ``--viewpoint``, ``--observatory``,
``--latitude``, ``--longitude``, ``--lon-dir``, ``--altitude``, and
``--sc-trajectory`` are the same as :ref:`ephemeris <cli-ephemeris>` with
identical defaults.

**Moons, rings, and stars**

``--moons``
   Moons to display.  Same format as :ref:`ephemeris <cli-ephemeris>`.
   Default: none (planet configuration default).

   .. code-block:: bash

      --moons mimas enceladus titan

``--moremoons``
   Additional moon selection string (planet-specific).
   Default: none.

``--rings``
   Ring display option codes or case-insensitive names (planet-specific).
   Integers and names can be mixed; see :ref:`reference` for the full list.
   Default: none.

   .. code-block:: bash

      --rings main ge
      --rings 61 62

``--standard``
   Standard star catalog to overlay.
   Default: none.

``--additional``
   Additional star catalog or identifier.
   Default: none.

``--extra-name``
   Name for a user-specified extra star.
   Default: none.

``--extra-ra``
   Right ascension for the extra star (string, parsed per ``--extra-ra-type``).
   Default: none.

``--extra-ra-type``
   RA format for the extra star (e.g. ``hours``, ``degrees``).
   Default: none.

``--extra-dec``
   Declination for the extra star.
   Default: none.

``--other``
   Other bodies to overlay (list of strings, e.g. additional asteroid names).
   Default: none.

**Plot options**

``--title``
   Diagram title string.
   Default: ``""`` (no title).

   .. code-block:: bash

      --title "Saturn Jan 2025"

``--labels``
   Moon label style.
   Default: none (planet default).

``--moonpts``
   Moon marker enlargement in points.
   Default: none (planet default).

``--blank``
   Whether to blank (white-out) planet/moon disks.
   Values: ``yes``, ``no`` (or ``y``/``n``/``true``/``false``/``1``/``0``).
   Default: ``no``.

   .. code-block:: bash

      --blank yes

``--opacity``
   Ring plot type (controls ring opacity rendering).
   Default: none (planet default).

``--peris``
   Pericenter markers.
   Default: none.

``--peripts``
   Pericenter marker size in points.
   Default: none.

``--meridians``
   Show prime meridians.
   Default: none.

``--arcmodel``
   Arc model for Neptune ring arcs.
   Default: none.

``--arcpts``
   Arc weight in points for Neptune ring arcs.
   Default: none.

**Output**

``-o`` / ``--output``
   Write the PostScript diagram to a file.
   Default: none (no PS output).

   .. code-block:: bash

      -o view.ps

``--output-txt``
   Write a field-of-view table to a file (body positions within the FOV).
   Default: none (no text output).

   .. code-block:: bash

      --output-txt fov_table.txt

**Io torus (Jupiter only)**

``--torus``
   Show the Io plasma torus.
   Values: ``yes``, ``no`` (or ``y``/``n``/``true``/``false``/``1``/``0``).
   Default: ``no``.

``--torus-inc``
   Io torus inclination in degrees.
   Default: ``6.8``.

``--torus-rad``
   Io torus radius in km.
   Default: ``422000.0``.

**Display-string overrides (CGI passthrough)**

``--ephem-display``
   Override the ephemeris description shown in the Input Parameters section
   (e.g. ``NEP095 + DE440``).
   Default: auto-generated.

``--moons-display``
   Override the moon selection description shown in the Input Parameters
   section (e.g. ``802 Triton & Nereid``).
   Default: auto-generated.

``--rings-display``
   Override the ring selection description shown in the Input Parameters
   section (e.g. ``LeVerrier, Arago``).
   Default: auto-generated.

``--cgi``
   Read all parameters from environment variables (CGI mode) instead of the
   command line.  Same as :ref:`ephemeris <cli-ephemeris>`.
   Default: off.

.. _cli-cgi:

Environment / CGI mode
-----------------------

When running behind a CGI web server, set ``REQUEST_METHOD=GET`` and pass
parameters via ``QUERY_STRING`` (or as individual environment variables).
Use ``--cgi`` on any subcommand so parameters are read from the
environment instead of the command line.

All CGI environment variables read by each tool:

**Ephemeris** (``ephemeris-tools ephemeris --cgi``): ``NPLANET``, ``start``,
``stop`` (or ``START_TIME``/``STOP_TIME``), ``interval``, ``time_unit``,
``ephem``, ``viewpoint``, ``observatory``, ``latitude``, ``longitude``,
``lon_dir``, ``altitude``, ``sc_trajectory``, ``columns``, ``mooncols``,
``moons``, ``EPHEM_FILE``.

**Tracker** (``ephemeris-tools tracker --cgi``): ``NPLANET``, ``start``,
``stop``, ``interval``, ``time_unit``, ``ephem``, ``viewpoint``,
``observatory``, ``latitude``, ``longitude``, ``lon_dir``, ``altitude``,
``sc_trajectory``, ``moons``, ``rings``, ``xrange``, ``xunit``, ``title``,
``TRACKER_POSTFILE``, ``TRACKER_TEXTFILE``.

**Viewer** (``ephemeris-tools viewer --cgi``): ``NPLANET``, ``time``,
``fov``, ``fov_unit``, ``center``, ``center_body``, ``center_ansa``,
``center_ew``, ``center_ra``, ``center_ra_type``, ``center_dec``,
``center_star``, ``viewpoint``, ``observatory``, ``latitude``,
``longitude``, ``lon_dir``, ``altitude``, ``moons`` (or ``moremoons``),
``rings``, ``blank``, ``meridians``, ``opacity``, ``peris``, ``peripts``,
``arcmodel``, ``arcpts``, ``other``, ``labels``, ``moonpts``, ``title``,
``standard``, ``additional``, ``extra_name``, ``extra_ra``,
``extra_ra_type``, ``extra_dec``, ``ephem``, ``torus``, ``torus_inc``,
``torus_rad``, ``VIEWER_POSTFILE``.

See the Developer's Guide :ref:`cgi_parameter_reference` for possible
values and per-tool details. See :ref:`reference` for column IDs, moon
names, and observatory/spacecraft names.
