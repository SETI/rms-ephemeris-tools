.. _fortran_compatibility:

FORTRAN Compatibility Reference
===============================

This document is the canonical reference for differences between the Python
port and the original FORTRAN tools. Entries are grouped into: compatibility
fixes (Python changed to match FORTRAN), FORTRAN bugs that the Python port
does not replicate, and Python improvements over FORTRAN that are kept by
design. For porting methodology and detailed bug descriptions, see
:ref:`porting`.

Compatibility Fixes (Python Matches FORTRAN)
--------------------------------------------

These are cases where the Python implementation was changed so that output
or behavior matches the FORTRAN tools.

Ephemeris output format
^^^^^^^^^^^^^^^^^^^^^^^

- **Observer distance overflow** (``ephemeris.py``): FORTRAN ``f10.0``
  includes a trailing decimal point, so values ≥ 10⁹ overflow the 10-character
  field and FORTRAN falls back to scientific notation. Python detects the
  same overflow condition (no leading space in the formatted string) and
  uses scientific notation to match.

- **Scientific notation case** (``ephemeris.py``): FORTRAN uses uppercase
  ``E`` in scientific notation (e.g. ``1.4840E+09``). Python uses ``:E``
  instead of ``:e`` for ``sun_dist`` and overflow-triggered ``obs_dist``
  so output matches.

Time parsing and stepping
^^^^^^^^^^^^^^^^^^^^^^^^^^

- **ISO UTC ``Z`` suffix** (``time_utils.py``): FORTRAN CGI accepts
  timestamps ending in ``Z`` (e.g. ``2022-08-18T00:01:47Z``). Python
  ``parse_datetime()`` retries with ``Z``/``z`` stripped so those inputs
  are accepted with UTC semantics.

- **Year-time form ``YYYY HH:MM:SS``** (``time_utils.py``): FORTRAN-style
  timestamps without month/day are accepted and mapped to ``YYYY-01-01
  HH:MM:SS``.

- **Start-boundary second normalization** (``ephemeris.py``): FORTRAN
  rounds the *start* boundary seconds to minute precision before building
  the stepped time grid. Python applies the same minute-normalized start
  and half-up rounding so date/time columns and line counts match.

- **Minute rounding mode**: Python uses FORTRAN-compatible half-up rounding
  (e.g. ``int(x + 0.5)``) instead of Python’s default banker’s rounding
  where timestamps are aligned to FORTRAN.

- **Historical UTC model parity** (``time_utils.py``, leap-second
  initialization): The Julian library’s UT model is set to ``SPICE`` so that
  UTC↔TAI conversion matches SPICE/FORTRAN. This is required for tracker
  output parity, especially for historical-date runs.

Viewer FOV table
^^^^^^^^^^^^^^^^

- **RA/Dec offset units** (``viewer_helpers.py::_write_fov_table``):
  FORTRAN uses arcseconds for Earth observer and degrees for spacecraft.
  Python branches on ``obs_id == EARTH_ID`` and uses arcsec or degrees
  accordingly, with matching header labels (``dRA (")`` / ``dDec (")`` vs
  ``dRA (deg)`` / ``dDec (deg)``) and RA wraparound (arcsec vs 180°/360°).

FORTRAN Bugs Not Replicated in Python
-------------------------------------

The Python port implements the correct behavior in these cases; the FORTRAN
source contains a bug.

- **RSPK_OrbitOpen** (``rspk_orbitopen.f``): Computes planet-to-observer
  vector as ``-planet_pv`` (planet to SSB) instead of ``obs_pv - planet_pv``.
  Python ``ring_opening()`` in ``spice/rings.py`` uses the correct
  formula. See :ref:`porting` for details.

- **PLELSG** (``euclid/plelsg.f``): Incorrect swap of ``T(2)`` and ``T(3)``
  (assigns ``T(2) = T(3)`` after overwriting ``T(3)``, so both become the
  original ``T(2)``). Python ``_plelsg()`` in ``euclid/segment_plane.py``
  performs a correct swap. See :ref:`porting` for details.

- **RSPK_LabelYAxis** (tracker): Uninitialized variable in FORTRAN; Python
  ``_label_yaxis()`` in ``draw_tracker.py`` is correct. See :ref:`porting`.

- **SMSGND** (SPICELIB): FORTRAN uses strict inequality (zeros yield
  ``.FALSE.``); Python uses ``a * b >= 0``. See :ref:`porting`.

Python Improvements Over FORTRAN
---------------------------------

These behaviors were added in the Python port for robustness and are kept;
FORTRAN has no equivalent guard.

Epsilon and division-by-zero guards
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **ansa_radec** (``spice/rings.py``): Rejects ``abs(denom) < _EPS_ANSA``
  with ``ValueError``; clamps ratio to [-1, 1] before ``asin``. FORTRAN
  can divide by zero or pass an invalid argument to ``asin`` at edge-on
  ring geometry.

- **body_latlon** (``spice/geometry.py``): Raises if norm ``n < 1e-12``;
  clamps ``asin`` argument to [-1, 1]. FORTRAN has no check.

- **moon_distances** (``spice/orbits.py``): Uses ``eps_limb`` and
  ``min(1.0, ...)`` so limb radius and ``asin`` remain valid when
  planet distance is very small.

- **Vector utilities** (``vec_math.py``): ``_vhat`` returns zero vector
  when norm is zero instead of dividing by zero. ``_vsep`` clamps the dot
  product to [-1, 1] before ``acos`` to avoid domain errors from roundoff.

- **Multiple call sites** (e.g. ``bodmat.py``, ``geometry.py``, ``orbits.py``):
  Python checks vector norms (e.g. ``1e-10``, ``1e-12``) before division;
  FORTRAN has no such guards.

Rendering and ellipse
^^^^^^^^^^^^^^^^^^^^^

- **ESDRAW** (``escher/view.py::esdraw``): Uses ``_ESDRAW_EPS = 1e-12``
  so that near-zero z is replaced by a signed epsilon before projection,
  avoiding division by zero for points on the camera plane. FORTRAN has
  no protection.

- **Ellipse / _ellips** (``euclid/ellipse.py``, ``body.py``): For
  degenerate denominators Python uses a small epsilon (e.g. 1e-30)
  instead of signalling an error, giving graceful degradation. FORTRAN
  signals error.

Rounding
^^^^^^^^

- **NINT** (``escher/ps_output.py::_nint``): Python replicates FORTRAN
  ``IDNINT`` (round half away from zero). Python’s built-in ``round()``
  uses banker’s rounding and is not used for FORTRAN-compatible output.

Floating-Point Precision
-------------------------

FORTRAN was compiled with 80-bit extended precision for intermediates;
Python uses 64-bit doubles throughout. Small precision differences
accumulate through the viewer geometry pipeline (body/ring → camera →
limb/terminator ellipse → plane-ellipse intersection → visibility).
Borderline segments can therefore be visible in one implementation and
invisible in the other. See :ref:`porting` for the full pipeline and
degenerate-segment discussion.
