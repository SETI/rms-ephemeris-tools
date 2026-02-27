.. _install:

Installation
============

Install
-------

Create a virtual environment and install the package into it (do not install
into system Python):

.. code-block:: bash

   python3 -m venv .venv
   source .venv/bin/activate
   pip install rms-ephemeris-tools

This provides the ``ephemeris-tools`` command.

.. _install_env:

Environment variables
---------------------

| Variable | Purpose | Default |
|----------|---------|---------|
| **SPICE_PATH** | Root directory for SPICE kernels. Must contain ``SPICE_planets.txt``, ``SPICE_spacecraft.txt``, and kernel files (e.g. ``leapseconds.ker``, planet/moon SPKs). | ``/var/www/SPICE/`` |
| TEMP_PATH | Directory for temporary or output files. | ``/var/www/work/`` |
| STARLIST_PATH | Directory for star catalog files (e.g. ``starlist_sat.txt``). | ``/var/www/documents/tools/`` |
| JULIAN_LEAPSECS | Path to a NAIF LSK leap-second file. If unset, the code looks under ``SPICE_PATH``, then ``leapsecs.txt``; if missing or not LSK format, rms-julian's bundled LSK is used. | (see above) |
| EPHEMERIS_TOOLS_LOG_LEVEL | Logging level: ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, or ``CRITICAL``. | ``WARNING`` |

Ensure ``SPICE_PATH`` contains (or points to) the expected config and kernel
files. Without these, ephemeris/tracker/viewer runs will fail when loading
kernels.

Running the tools
-----------------

Use the ``ephemeris-tools`` command:

.. code-block:: bash

   ephemeris-tools <command> [options]

See :ref:`cli` and :ref:`examples` for command examples (ephemeris, tracker,
viewer).
