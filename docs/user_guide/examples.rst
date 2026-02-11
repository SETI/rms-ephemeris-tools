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

   ephemeris-tools viewer --planet saturn --time "2025-01-01 12:00" --fov 1 --fov-unit deg -o view.ps --output-txt fov_table.txt

See :ref:`reference` for column IDs, planet names, and moon index-to-name mappings.

Programmatic use
----------------

You can call the core functions from Python instead of the CLI:

.. code-block:: python

   from ephemeris_tools.params import EphemerisParams
   from ephemeris_tools.ephemeris import generate_ephemeris

   params = EphemerisParams(
       planet_num=6,
       start_time="2025-01-01 00:00",
       stop_time="2025-01-02 00:00",
       interval=1.0,
       time_unit="hour",
       viewpoint="observatory",
       observatory="Earth's Center",
       columns=[1, 2, 3, 15, 8],
       mooncols=[5, 6, 8, 9],
       moon_ids=[],
   )
   with open("ephem.txt", "w") as f:
       generate_ephemeris(params, f)

.. code-block:: python

   from ephemeris_tools.tracker import run_tracker

   run_tracker(
       planet_num=6,
       start_time="2025-01-01 00:00",
       stop_time="2025-01-02 00:00",
       interval=1.0,
       time_unit="hour",
       viewpoint="Earth",
       moon_ids=[601, 602, 603],
       output_ps=open("tracker.ps", "w"),
       output_txt=None,
   )

.. code-block:: python

   from ephemeris_tools.viewer import run_viewer

   run_viewer(
       planet_num=6,
       time_str="2025-01-01 12:00",
       fov=1.0,
       center_ra=0.0,
       center_dec=0.0,
       viewpoint="Earth",
       output_ps=open("view.ps", "w"),
       output_txt=None,
   )

Ensure SPICE kernels are loaded (e.g. via :py:func:`ephemeris_tools.spice.load.load_spice_files`)
before calling these functions.
