.. _install:

Installation
============

Requirements
------------

- **Python**: 3.10 or newer
- **SPICE kernels**: Required for ephemeris, tracker, and viewer. The package uses
  `cspyce` to load NAIF SPICE kernels; you must provide a kernel directory
  (see :ref:`spice_setup`).

Create a virtual environment (recommended); do not install into system Python.

.. code-block:: bash

   python3 -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   # or:  .venv\Scripts\activate   # Windows

Install from source
-------------------

1. Clone the repository:

   .. code-block:: bash

      git clone https://github.com/SETI/rms-ephemeris-tools.git
      cd rms-ephemeris-tools

2. Install the package in editable mode:

   .. code-block:: bash

      pip install -e .

   For development (tests, linting, type-checking, docs):

   .. code-block:: bash

      pip install -e ".[dev]"

   Optional rendering support (e.g. matplotlib):

   .. code-block:: bash

      pip install -e ".[render]"

Install from PyPI
-----------------

.. code-block:: bash

   pip install rms-ephemeris-tools

.. _spice_setup:

SPICE kernel setup
-------------------

Set the **SPICE_PATH** environment variable to the root directory containing
your SPICE config and kernel files.

Required under ``SPICE_PATH``:

- **SPICE_planets.txt** — Planet/ephemeris version and kernel filenames
- **SPICE_spacecraft.txt** — Spacecraft IDs and kernel filenames (for observer)
- **leapseconds.ker** (or equivalent) — Leap-second kernel
- Kernel files referenced in the config (e.g. planetary SPKs, LSK)

Example:

.. code-block:: bash

   export SPICE_PATH=/path/to/your/SPICE

Without a valid ``SPICE_PATH`` and the expected config/kernels, ephemeris,
tracker, and viewer runs will fail when loading kernels.

Environment variables
---------------------

- **SPICE_PATH** — Root directory for SPICE kernels and config (required for
  ephemeris/tracker/viewer).
- **TEMP_PATH** — Directory for temporary or output files (default:
  ``/var/www/work/``).
- **STARLIST_PATH** — Directory for star catalog files (e.g. ``starlist_sat.txt``).
- **JULIAN_LEAPSECS** — Path to a NAIF LSK leap-second file; if unset, the code
  searches under SPICE_PATH and rms-julian.
- **EPHEMERIS_TOOLS_LOG** — Logging level: ``DEBUG``, ``INFO``, ``WARNING``,
  ``ERROR``, or ``CRITICAL`` (default: WARNING).
