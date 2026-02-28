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

Web tools (CGI forms and samples)
---------------------------------

To deploy the bundled web forms and sample files (e.g. for a CGI-capable server),
run the ``install_ephemeris_tools_files`` command with a target directory:

.. code-block:: bash

   install_ephemeris_tools_files /path/to/htdocs/tools

All files from the package's ``web/tools`` tree are copied into the given
directory (subdirectories such as ``samples/`` are preserved). This works when
the package is installed from PyPI or from source. Use ``-v`` for verbose
(log) output.

.. _install_env:

Environment variables
---------------------

.. list-table:: Environment variables
   :header-rows: 1
   :widths: 25 40 20

   * - Variable
     - Purpose
     - Default
   * - **SPICE_PATH**
     - Root directory for SPICE kernels. Must contain ``SPICE_planets.txt``,
       ``SPICE_spacecraft.txt``, and kernel files (e.g. ``leapseconds.ker``,
       planet/moon SPKs).
     - ``/var/www/SPICE/``
   * - TEMP_PATH
     - Directory for temporary or output files.
     - ``/var/www/work/``
   * - STARLIST_PATH
     - Directory for star catalog files (e.g. ``starlist_sat.txt``).
     - ``/var/www/documents/tools/``
   * - JULIAN_LEAPSECS
     - Path to a NAIF LSK leap-second file. If unset, the code looks under
       ``SPICE_PATH``, then ``leapsecs.txt``; if missing or not LSK format,
       rms-julian's bundled LSK is used.
     - (see above)
   * - EPHEMERIS_TOOLS_LOG_LEVEL
     - Logging level: ``DEBUG``, ``INFO``, ``WARNING``, ``ERROR``, or
       ``CRITICAL``.
     - ``WARNING``

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
