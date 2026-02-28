.. _quickstart:

Quick Start
===========

After installation and setting ``SPICE_PATH``, use the CLI entry point:

.. code-block:: bash

   ephemeris-tools <command> [options]

To install the bundled web forms and sample files (for CGI deployment), run:

.. code-block:: bash

   install_ephemeris_tools_files /path/to/your/tools/dir

Commands
--------

- **ephemeris** -- Generate time-series ephemeris tables (positions, geometry)
- **tracker** -- Generate moon tracker PostScript plots and optional text tables
- **viewer** -- Generate planet viewer PostScript diagrams (planet, moons, rings, stars)

Ephemeris table
---------------

.. code-block:: bash

   ephemeris-tools ephemeris --planet saturn --start "2025-01-01 00:00" \
       --stop "2025-01-01 02:00" --interval 1 --time-unit hour \
       -o ephem.txt

Key options (see :ref:`cli-ephemeris` for the full list):

- ``--planet``: Planet number or name. Default: ``6`` (saturn).
- ``--start``, ``--stop``: Start/stop time strings (required).
- ``--interval``: Time step size. Default: ``1.0``.
- ``--time-unit``: Unit for interval (``sec``/``min``/``hour``/``day``). Default: ``hour``.
- ``--ephem``: Ephemeris version index; available versions are listed in ``SPICE_planets.txt``. Default: ``0``.
- ``--columns``: Column IDs or names (e.g. ``ymdhms radec phase``). Default: ``1 2 3 15 8``.
- ``--moons``: Moon indices or names (e.g. ``mimas titan``). Default: none.
- ``-o``: Output file (default: stdout).
- ``-v`` / ``--verbose``: Set log level to INFO.

Moon tracker
------------

.. code-block:: bash

   ephemeris-tools tracker --planet saturn --start "2025-01-01 00:00" \
       --stop "2025-01-02 00:00" --moons mimas enceladus titan \
       -o tracker.ps

Key options (see :ref:`cli-tracker` for the full list):

- ``--planet``, ``--start``, ``--stop``, ``--interval``, ``--time-unit``: same as ephemeris.
- ``--moons``: Moons to plot. Default: standard set for the planet.
- ``--rings``: Ring option codes or names (e.g. ``main ge`` or ``61 62``). Default: none.
- ``--xrange``: X-axis half-range. Default: ``180.0``.
- ``--title``: Plot title. Default: none.
- ``-o``: PostScript output file.

Planet viewer
-------------

.. code-block:: bash

   ephemeris-tools viewer --planet saturn --time "2025-01-01 12:00" \
       --fov 0.1 --fov-unit deg -o view.ps

Key options (see :ref:`cli-viewer` for the full list):

- ``--planet``: same as ephemeris. Default: ``6`` (saturn).
- ``--time``: Observation time (required).
- ``--fov``: Field of view size. Default: ``1.0``.
- ``--fov-unit``: FOV unit (``deg``/``arcmin``/``arcsec``). Default: ``deg``.
- ``--center``: Diagram center (``body``/``ansa``/``J2000``/``star``). Default: ``body``.
- ``--moons``: Moon indices or names. Default: planet default.
- ``-o``: PostScript output file.
- ``--output-txt``: Field-of-view text table file.

Converting PostScript to PNG (Ghostscript):

.. code-block:: bash

   gs -dSAFER -dBATCH -dNOPAUSE -sDEVICE=png16m -r150 -sOutputFile=view.png view.ps

Use the same pattern for tracker output (e.g. ``tracker.ps`` → ``tracker.png``).

For detailed per-argument documentation, see :ref:`cli`.
For column IDs, moon names, and observatory names, see :ref:`reference`.
