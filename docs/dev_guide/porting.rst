.. _porting:

Porting from FORTRAN
====================

rms-ephemeris-tools is a Python port of the PDS Ring-Moon Systems Node FORTRAN
tools (``ephem3_xxx``, ``tracker3_xxx``, ``viewer3_xxx``).  This chapter
documents the structure of the porting process, bugs discovered in the original
FORTRAN code, and inherent differences between the FORTRAN and Python
implementations.

For a categorized reference of compatibility fixes, FORTRAN bugs not replicated
in Python, and Python improvements over FORTRAN, see :ref:`fortran_compatibility`.

Porting methodology
-------------------

The port was carried out tool by tool.  For each tool the same process was
followed:

1. **Function-by-function translation** — Every FORTRAN subroutine was matched
   to a Python function.  Naming, parameter order, and control flow were kept
   as close to the original as practical so that reviewers can hold the two
   implementations side by side.

2. **Byte-identical output comparison** — A test harness drove both the FORTRAN
   binary and the Python CLI with identical parameters and diffed the output
   character by character.

   - For the **ephemeris generator**, the comparison target was the tab-delimited
     text table produced by ``ephem3_xxx.bin``.  All 22 general columns and 9
     moon columns were compared across multiple time ranges, step sizes, and
     moon selections.
   - For the **moon tracker**, both the text table and the PostScript diagram
     were compared.  Tracker tests covered 1-day to 3-month ranges, hourly and
     multi-hour steps, single and multiple ring overlays, and filtered moon
     subsets.
   - For the **planet viewer**, the PostScript output was compared.  In addition
     to whole-file diffing, a structured analysis compared PostScript command
     counts, per-section line counts, and extracted coordinate sets so that
     every coordinate in the FORTRAN output could be accounted for in the
     Python output.

3. **Section-by-section analysis (viewer)** — The viewer PostScript contains
   ``%Draw <name>`` comment markers that delimit each rendered object (planet,
   rings, individual moons, border box).  These markers allowed each section to
   be compared independently and its line-count difference classified as
   "identical", "explained by degenerate segments", or "unexplained residual".

4. **Verified-function tables** — After each round of comparison, a table was
   compiled mapping every Python function to its FORTRAN counterpart with a
   match status.  This table was reviewed to confirm complete coverage.

FORTRAN bugs
------------

Several bugs were discovered in the original FORTRAN source code during the
porting comparison.  In each case the Python port implements the *correct*
behaviour.

RSPK_OrbitOpen — wrong planet-to-observer vector (ephemeris)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Location**: ``rspk_orbitopen.f``, line 87.

The subroutine computes the planet-to-observer vector as:

.. code-block:: fortran

   c Calculate vector from planet to observer
         call VMINUS(planet_pv(1), obs_dp)

``VMINUS(planet_pv)`` yields ``-planet_pv``, which is the vector from the
planet to the **solar system barycentre** (SSB), not from the planet to the
**observer**.  The companion routine ``RSPK_RingOpen`` correctly computes:

.. code-block:: fortran

   call VLCOM(1.d0, obs_pv(1), -1.d0, planet_pv(1), obs_dp)

which gives ``obs_pv - planet_pv``, the actual planet-to-observer vector.

**Impact**: For Saturn observed from Earth, the direction to Earth and the
direction to the SSB (near the Sun) differ by roughly the Sun–Saturn–Earth
angle (~3\ |deg|).  This causes errors of ~2.8\ |deg| in the orbital longitude
moon column (``MCOL_ORBLON``) and ~1.1\ |deg| in the orbital opening angle
moon column (``MCOL_ORBOPEN``).

**Python**: ``orbit_opening()`` in ``ephemeris_tools.spice.orbits`` correctly
uses ``obs_pv - planet_pv``.

RSPK_LabelYAxis — uninitialized variable (tracker)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Location**: ``rspk_trackmoons.f``, lines 659–663 (inside ``RSPK_LabelYAxis``).

.. code-block:: fortran

   dutc_ref = FJUL_DUTCofTAI(tai1, secs)

   if (mark1_imins .gt. MINS_PER_DAY) then
           call FJUL_YMDofDUTC(dutc, y, m, d)     ! BUG: dutc, not dutc_ref
           dutc_ref = dutc_ref - mod(d-1, mark1_imins/MINS_PER_DAY)
   end if

The local variable ``dutc`` is declared but never initialized.  The intended
variable is ``dutc_ref``, which was set on the preceding line.

**Impact**: Triggered when the time range is long enough that major Y-axis
ticks are spaced more than one day apart (roughly > 4 days with default tick
settings).  The reference date ``dutc_ref`` is adjusted by an unpredictable
amount based on whatever value ``dutc`` holds in memory, causing Y-axis tick
labels to start at a wrong date.

**Python**: ``_label_yaxis()`` in ``draw_tracker.py`` correctly uses
``day1`` (derived from ``tai1``).

PLELSG — incorrect swap (viewer, Euclid library)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Location**: ``euclid/plelsg.f``, line 362.

.. code-block:: fortran

   IF ( T(2) .GT. T(3) ) THEN
       ALPHA = T(3)
       T(3)  = T(2)
       T(2)  = T(3)       ! BUG: should be  T(2) = ALPHA
   END IF

The intent is to swap ``T(2)`` and ``T(3)``, but the last assignment reads the
already-overwritten ``T(3)`` instead of the saved value ``ALPHA``.  Both
elements end up with the original ``T(2)`` value.

**Impact**: Dormant in all tested configurations — the branch condition
``T(2) > T(3)`` was never observed to be true.  It could affect other viewing
geometries where the plane-ellipse intersection points are generated in a
different order.

**Python**: ``_plelsg()`` performs a correct swap.

SMSGND — strict inequality (viewer, SPICELIB)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Location**: ``SMSGND`` function in SPICELIB.

FORTRAN uses strict inequalities (``X .GT. 0 .AND. Y .GT. 0``), returning
``.FALSE.`` when either argument is exactly zero.  The Python implementation
uses ``a * b >= 0.0``, returning ``True`` for zero.

**Impact**: Dormant in all tested configurations — the affected code path was
never triggered.

Python-vs-FORTRAN differences
------------------------------

Even with a correct and faithful port, the Python and FORTRAN implementations
produce output that is not always bit-identical.  The differences fall into the
categories below.

Floating-point precision (viewer)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The FORTRAN binaries were compiled for x86 with a compiler that uses **80-bit
extended precision** for intermediate floating-point calculations.  Python uses
IEEE 754 **64-bit doubles** exclusively.  This 16-bit precision gap affects the
accumulation of rounding errors through the multi-step geometry pipeline:

.. code-block:: text

   Body/ring geometry
     → Camera frame transformation (matrix multiply)
       → Limb/terminator ellipse computation
         → Plane-ellipse intersection (PLELSG)
           → Visibility determination at each segment boundary
             → Degenerate segment: visible or not?

At each stage, small precision differences accumulate.  At the final visibility
decision, a borderline segment may be classified as visible in one
implementation but invisible in the other.

Additionally, the ``sqrt``, ``sin``, and ``cos`` implementations in the FORTRAN
runtime library may differ from Python's ``math`` module at the last few bits,
and the FORTRAN compiler may evaluate expressions in a different order than
Python, affecting intermediate rounding.

Degenerate segments (viewer)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A *degenerate segment* is a rendered segment whose move-to and line-to
coordinates differ by at most one pixel in each axis — effectively a one-pixel
line.  These appear at the terminator–limb intersection, where the boundary
between lit and dark surface meets the body's visible edge.

Due to the floating-point precision difference described above, the two
implementations disagree on the visibility of some of these borderline
segments.  The disagreement goes both directions: some bodies have more
degenerate segments in Python, others have more in FORTRAN.  In the Saturn
viewer reference case this accounts for the entire structural difference
between the two PostScript files (199 lines, or 3.2%).

Every coordinate produced by the FORTRAN binary also appears in the Python
output.  The Python output contains a small number of additional coordinate
pairs (11 in the reference case), all near the planet/ring overlap region at
the shadow edge.

Character-width formatting (ephemeris)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

FORTRAN's ``f10.0`` format always includes a trailing decimal point, so values
that fill all ten character positions overflow the field and FORTRAN silently
switches to scientific notation (``1p, e10.4``).  Python's equivalent
``:10.0f`` omits the trailing decimal point, so the same value fits.  The
Python implementation detects this case and applies the same scientific-notation
fallback to maintain byte-identical output.

FORTRAN scientific notation uses uppercase ``E`` (e.g. ``1.4840E+09``).
Python's ``:e`` format produces lowercase ``e``.  The Python implementation
uses ``:E`` to match.

Credit-line timestamps (tracker)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Tracker PostScript output includes a credit line with the generation timestamp.
Since the FORTRAN and Python runs execute at slightly different times, this
line always differs between the two and is excluded from comparison.

Summary of match status by tool
-------------------------------

Ephemeris generator
^^^^^^^^^^^^^^^^^^^

Byte-identical output for all 22 general columns and 7 of 9 moon columns.  The
two differing moon columns (``MCOL_ORBLON`` and ``MCOL_ORBOPEN``) differ
because of the FORTRAN ``RSPK_OrbitOpen`` bug; the Python values are correct.

Moon tracker
^^^^^^^^^^^^

Byte-identical PostScript and text-table output for all test configurations
where the time range is short enough to avoid the FORTRAN ``RSPK_LabelYAxis``
uninitialized-variable bug.  For longer ranges the Python produces correct
Y-axis tick positions while the FORTRAN output is indeterminate.

Planet viewer
^^^^^^^^^^^^^

The Python output is **structurally identical** to the FORTRAN: same header,
same sections, same drawing order, same labels, same captions, same footer.
The line-count difference (3.2% in the reference case) is entirely attributable
to floating-point precision at visibility boundaries.  No FORTRAN coordinate is
missing from the Python output.

.. |deg| unicode:: U+000B0
