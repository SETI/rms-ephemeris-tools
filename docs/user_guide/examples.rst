.. _examples:

Examples
========

Ephemeris to file
-----------------

.. code-block:: bash

   ephemeris-tools ephemeris --planet saturn --start "2025-01-01 00:00" --stop "2025-01-03 00:00" --interval 12 --time-unit hour -o saturn_ephem.txt

Planet names are case-insensitive; ``--planet 6`` and ``--planet Saturn`` are equivalent.

Ephemeris to stdout (pipe)
--------------------------

.. code-block:: bash

   ephemeris-tools ephemeris --planet 6 --start "2025-01-01 00:00" --stop "2025-01-01 06:00" --interval 1 --time-unit hour | head -50

Tracker with rings and title
-----------------------------

.. code-block:: bash

   ephemeris-tools tracker --planet saturn --start "2025-01-01 00:00" --stop "2025-01-02 00:00" --rings main ge --title "Saturn moons" -o tracker.ps

Viewer with FOV table
---------------------

.. code-block:: bash

   ephemeris-tools viewer --planet saturn --time "2025-01-01 12:00" --fov 0.1 --fov-unit deg -o view.ps --output-txt fov_table.txt

See :ref:`reference` for column IDs, planet names, and moon index-to-name mappings.

Programmatic use
----------------

You can call the core functions from Python instead of the CLI. SPICE kernels
are loaded automatically when you call these functions (no need to call
load functions first). Set ``SPICE_PATH`` so the code can find kernel files.

.. code-block:: python

   from ephemeris_tools.params import EphemerisParams
   from ephemeris_tools.ephemeris import generate_ephemeris

   params = EphemerisParams(
       planet_num=6,  # 6 = Saturn
       start_time="2025-01-01 00:00",
       stop_time="2025-01-02 00:00",
       interval=1.0,
       time_unit="hour",
       viewpoint="observatory",
       observatory="Earth's center",
       columns=[1, 2, 3, 15, 8],
       mooncols=[5, 6, 8, 9],
       moon_ids=[],
   )
   with open("ephem.txt", "w") as f:
       generate_ephemeris(params, f)

.. code-block:: python

   from ephemeris_tools.params import TrackerParams
   from ephemeris_tools.tracker import run_tracker

   params = TrackerParams(
       planet_num=6,  # 6 = Saturn
       start_time="2025-01-01 00:00",
       stop_time="2025-01-02 00:00",
       interval=1.0,
       time_unit="hour",
       moon_ids=[601, 602, 603],  # Mimas, Enceladus, Tethys
       output_ps=open("tracker.ps", "w"),
       output_txt=None,
   )
   run_tracker(params)

**Expected output:** ``run_tracker(params)`` writes a PostScript file named
``tracker.ps`` (via the ``output_ps`` parameter in ``TrackerParams``). The file
contains plotted ephemeris tracks for Saturn (``planet_num=6``) and labeled
moon positions for ``moon_ids=[601, 602, 603]`` (Mimas, Enceladus, Tethys). A
typical ``tracker.ps`` begins with a PostScript header (e.g. ``%!PS-Adobe-3.0``),
page size/comments, and then drawing commands for the trajectories and labels.

.. code-block:: python

   from ephemeris_tools.params import ViewerParams
   from ephemeris_tools.viewer import run_viewer

   params = ViewerParams(
       planet_num=6,  # 6 = Saturn
       time_str="2025-01-01 12:00",
       fov_value=1.0,
       output_ps=open("view.ps", "w"),
       output_txt=None,
   )
   run_viewer(params)

**Expected output:** ``run_viewer(ViewerParams(...))`` creates a PostScript file
named ``view.ps`` via the ``output_ps`` parameter. The file starts with a header
such as ``%!PS-Adobe-3.0`` and bounding box comments; it contains a sky projection
of Saturn at 2025-01-01 12:00 with the configured FOV (e.g. 1.0°). Readers can
expect ``view.ps`` to be a valid PostScript document suitable for conversion to
PDF or PNG.
