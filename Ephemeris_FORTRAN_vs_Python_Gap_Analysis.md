# Ephemeris: FORTRAN vs Python Gap Analysis

## Summary

The Python ephemeris table generator (`ephemeris.py`) produces **byte-identical
table output** to the FORTRAN `ephem3_xxx.bin` for all 22 general columns and
7 of 9 moon columns across all tested configurations.

The two remaining moon columns — `MCOL_ORBLON` (orbital longitude) and
`MCOL_ORBOPEN` (orbital opening angle) — differ due to a **FORTRAN bug** in
`RSPK_OrbitOpen` that computes the planet-to-observer vector incorrectly.
The Python implementation uses the correct formula.

Update (2026-02-16): the broader 74-URL FORTRAN regression corpus is now fully
converged. After iterative fixes in this document, the run improved from
**37 passed / 37 failed** to **74 passed / 0 failed**.

## Test Results

| # | Test Case                              | Result    | Notes                                  |
|---|----------------------------------------|-----------|----------------------------------------|
| 1 | Default columns (MJD, YMDHMS, RADEC, PHASE), 1 day 1h | **Match** | Baseline test |
| 2 | All 22 general columns, 1 day 1h      | **Match** | Every general column verified           |
| 3 | Moon cols 1-7 (dist through offdeg), 6 moons | **Match** | All non-orbit moon columns |
| 4 | 7-day range, daily steps, 8 columns   | **Match** | Multi-day, sparse steps                 |
| 5 | YDHM/YDHMS date formats               | **Match** | Day-of-year format verification         |
| 6 | 30-day range, 6h steps, 12 columns    | **Match** | Long range, dense output                |
| 7 | 6-hour range, 30-min steps            | **Match** | Fine time resolution                    |
| 8 | Moon cols 1-9 (including orbit), 6 moons | **Differ** | FORTRAN orbit bug (cols 8-9 only) |
| 9 | Single moon (Titan), all 9 moon cols  | **Differ** | Same FORTRAN orbit bug                  |

Tests 8 and 9 differ **only** in `MCOL_ORBLON` and `MCOL_ORBOPEN`; all other
fields in those tests match exactly.

## Bugs Fixed During Comparison

### 1. Planet phase angle calculation (geometry.py)

**Symptom**: Phase angle values differed by ~2.5 degrees (Python: ~5.47°,
FORTRAN: ~2.96°).

**Root cause**: `planet_phase()` computed `obs_dp = obs_pv - planet_dpv` where
`obs_pv` is the observer state in the SSB frame and `planet_dpv` is the planet
position relative to the observer. This produces `2 × observer_SSB - planet_SSB`,
an incorrect vector. The FORTRAN `RSPK_Phase` correctly uses
`VMINUS(planet_dpv)` — the negation of the planet-observer vector — to get the
direction from planet to observer.

**Fix**: Changed to `obs_dp = cspyce.vminus(planet_dpv[:3])`, matching the
FORTRAN and the already-correct `body_phase()` function.

**File**: `src/ephemeris_tools/spice/geometry.py`, `planet_phase()`

### 2. Observer distance format — FORTRAN f10.0 overflow (ephemeris.py)

**Symptom**: `COL_OBSDIST` column showed `1607653206` (Python) vs `1.6077E+09`
(FORTRAN) for Saturn's observer distance.

**Root cause**: FORTRAN's `f10.0` format always includes a trailing decimal
point, so values ≥ 10⁹ require 11+ characters (10 digits + period) and overflow
the 10-character field. FORTRAN detects the overflow (asterisks in the output)
and falls back to `(1p, e10.4)` scientific notation. Python's `:10.0f` omits
the trailing decimal point, so 10-digit values fit without triggering the
fallback.

**Fix**: Added a FORTRAN-compatible overflow check: if the formatted string
fills the entire 10-character field with no leading space (`s[0] != ' '`),
switch to scientific notation. This matches the FORTRAN behavior where the
mandatory decimal point would cause an overflow.

**File**: `src/ephemeris_tools/ephemeris.py`, `COL_OBSDIST` and `MCOL_OBSDIST`

### 3. Scientific notation case — lowercase e vs uppercase E (ephemeris.py)

**Symptom**: `sun_dist` and overflow-triggered `obs_dist` values used lowercase
`e` (Python: `1.4840e+09`) while FORTRAN uses uppercase `E` (`1.4840E+09`).

**Root cause**: Python's `:10.4e` format specifier produces lowercase `e`.
FORTRAN's `(1p, e10.4)` produces uppercase `E`.

**Fix**: Changed all scientific notation format specifiers from `:10.4e` to
`:10.4E` to match FORTRAN's output.

**File**: `src/ephemeris_tools/ephemeris.py`, `COL_OBSDIST`, `COL_SUNDIST`, and
`MCOL_OBSDIST`

### 4. ISO UTC `Z` timestamps rejected by Python parser (time_utils.py)

**Symptom**: Some CGI cases failed immediately with:
`Error: Invalid start or stop time` for ISO timestamps ending in `Z`
(for example `2022-08-18T00:01:47Z`).

**Root cause**: `julian.day_sec_from_string()` in the current stack does not
accept trailing `Z` UTC suffixes, while FORTRAN test inputs include them.

**Fix**: `parse_datetime()` now retries parsing with trailing `Z`/`z` removed.
This preserves UTC semantics and matches FORTRAN CGI behavior for those inputs.

**File**: `src/ephemeris_tools/time_utils.py`, `parse_datetime()`

### 5. Start-boundary second normalization for ephemeris stepping (ephemeris.py)

**Symptom**: Date/time columns showed systematic second-field mismatches
(`sc`, for example Python `8` vs FORTRAN `0`) and one-or-more line-count
differences in second-based and non-second-based runs.

**Root cause**: Python boundary handling did not consistently match FORTRAN's
time-grid initialization. FORTRAN rounds the **start** boundary seconds to
minute precision before building the stepped time grid.

**Fix**: Added start-boundary normalization and aligned stepping so the start
timestamp is minute-normalized with FORTRAN-compatible half-up rounding, while
the stop timestamp remains raw for sample-count calculations.

**File**: `src/ephemeris_tools/ephemeris.py`, `generate_ephemeris()`

## Known FORTRAN Bug — RSPK_OrbitOpen

**Location**: `original/tools-FORTRAN/Tools/rspk/rspk_orbitopen.f`, line 87

**Bug**: The subroutine computes the planet-to-observer vector as:

```fortran
c Calculate vector from planet to observer
      call VMINUS(planet_pv(1), obs_dp)
```

This computes `obs_dp = -planet_pv`, which is the vector from the planet to the
**solar system barycenter** (SSB), not from the planet to the **observer**.

**Correct code**: The companion routine `RSPK_RingOpen`
(`rspk_ringopen.f`, line 145) correctly computes:

```fortran
c Calculate vector from planet to observer
      call VLCOM(1.d0, obs_pv(1), -1.d0, planet_pv(1), obs_dp)
```

This computes `obs_dp = obs_pv - planet_pv` — the actual vector from planet to
observer.

**Impact**: For Saturn observed from Earth, the direction to Earth and the
direction to the SSB (near the Sun) differ by approximately the Sun-Saturn-Earth
angle (~3°). This causes `MCOL_ORBLON` (orbital longitude) errors of ~2.8° and
`MCOL_ORBOPEN` (orbital opening angle) errors of ~1.1°.

**Python implementation**: `orbit_opening()` in
`src/ephemeris_tools/spice/orbits.py` correctly uses
`obs_dp = obs_pv - planet_pv`, consistent with `RSPK_RingOpen` and physical
intent. This is the intended behavior.

## Verified Functions

| Column / Function       | Python Implementation       | FORTRAN Equivalent      | Status    |
|-------------------------|-----------------------------|-------------------------|-----------|
| COL_MJD                 | `ephemeris.py`              | `ephem3_xxx.f`          | **Match** |
| COL_YMDHM               | `ephemeris.py`              | `ephem3_xxx.f`          | **Match** |
| COL_YMDHMS              | `ephemeris.py`              | `ephem3_xxx.f`          | **Match** |
| COL_YDHM                | `ephemeris.py`              | `ephem3_xxx.f`          | **Match** |
| COL_YDHMS               | `ephemeris.py`              | `ephem3_xxx.f`          | **Match** |
| COL_OBSDIST             | `ephemeris.py`              | `ephem3_xxx.f`          | **Match** |
| COL_SUNDIST             | `ephemeris.py`              | `ephem3_xxx.f`          | **Match** |
| COL_PHASE               | `planet_phase()`            | `RSPK_Phase`            | **Match** |
| COL_OBSOPEN             | `ring_opening()`            | `RSPK_RingOpen`         | **Match** |
| COL_SUNOPEN             | `ring_opening()`            | `RSPK_RingOpen`         | **Match** |
| COL_OBSLON              | `ring_opening()`            | `RSPK_RingOpen`         | **Match** |
| COL_SUNLON              | `ring_opening()`            | `RSPK_RingOpen`         | **Match** |
| COL_SUBOBS              | `body_latlon()`             | `RSPK_LatLon`           | **Match** |
| COL_SUBSOL              | `body_latlon()`             | `RSPK_LatLon`           | **Match** |
| COL_RADEC               | `body_radec()`              | `RSPK_RADEC`            | **Match** |
| COL_EARTHRD             | `body_radec(Earth)`         | `RSPK_RADEC`            | **Match** |
| COL_SUNRD               | `body_radec(Sun)`           | `RSPK_RADEC`            | **Match** |
| COL_RADIUS              | `limb_radius()`             | `RSPK_LimbRad`          | **Match** |
| COL_RADDEG              | `limb_radius()`             | `RSPK_LimbRad`          | **Match** |
| COL_LPHASE              | `body_phase(Moon)`          | `RSPK_BodyPhase`        | **Match** |
| COL_SUNSEP              | `conjunction_angle(Sun)`    | `RSPK_ConjAngle`        | **Match** |
| COL_LSEP                | `conjunction_angle(Moon)`   | `RSPK_ConjAngle`        | **Match** |
| MCOL_OBSDIST            | `body_ranges()`             | `RSPK_BodyRanges`       | **Match** |
| MCOL_PHASE              | `body_phase()`              | `RSPK_BodyPhase`        | **Match** |
| MCOL_SUBOBS             | `body_latlon()`             | `RSPK_BodyLatLon`       | **Match** |
| MCOL_SUBSOL             | `body_latlon()`             | `RSPK_BodyLatLon`       | **Match** |
| MCOL_RADEC              | `body_radec()`              | `RSPK_BodyRADEC`        | **Match** |
| MCOL_OFFSET (arcsec)    | `body_radec()` + offset     | `ephem3_xxx.f` inline   | **Match** |
| MCOL_OFFDEG (degrees)   | `body_radec()` + offset     | `ephem3_xxx.f` inline   | **Match** |
| MCOL_ORBLON             | `orbit_opening()`           | `RSPK_OrbitOpen`        | **Differ** (FORTRAN bug) |
| MCOL_ORBOPEN            | `orbit_opening()`           | `RSPK_OrbitOpen`        | **Differ** (FORTRAN bug) |

## Conclusion

The Python ephemeris port is a faithful and byte-identical reproduction of the
FORTRAN `ephem3_xxx.bin` output for all 22 general columns and 7 of 9 moon
columns. Three Python bugs were fixed during this comparison:

1. **Phase angle**: incorrect planet-to-observer vector in `planet_phase()`
2. **obs_dist overflow**: Python did not trigger FORTRAN-compatible scientific
   notation for 10-digit values
3. **E notation case**: lowercase `e` instead of uppercase `E` in scientific
   notation

Additional fixes from broader CGI regression comparisons:

4. **ISO `Z` UTC parsing**: accept `...T...Z` timestamps in `parse_datetime()`
5. **Start boundary normalization**: round start boundary seconds to minute
   precision to match FORTRAN stepping
6. **Observatory coordinate parsing**: parse `(lat, lon, alt)` triplets from
   observatory display strings so topocentric geometry matches FORTRAN
7. **Minute rounding mode**: use FORTRAN half-up minute rounding (`int(x+0.5)`)
   instead of Python banker rounding
8. **Uranus longitude convention**: remove incorrect Uranus-only longitude
   inversion in `body_latlon()` to match FORTRAN output columns
9. **FORTRAN year-time parser form**: accept `YYYY HH:MM:SS` timestamps and map
   to `YYYY-01-01 HH:MM:SS`

The sole remaining difference — in `MCOL_ORBLON` and `MCOL_ORBOPEN` — is caused
by a FORTRAN bug in `RSPK_OrbitOpen` that uses `VMINUS(planet_pv)` instead of
`VLCOM(obs_pv, -planet_pv)`, computing the direction to the SSB rather than to
the observer. The Python implementation correctly uses `obs_pv - planet_pv`,
consistent with the FORTRAN `RSPK_RingOpen` routine and physical intent.

## Running Bug Fix Log

| Date | Change | Files | Verification / Impact |
|---|---|---|---|
| 2026-02-16 | Accept ISO UTC trailing `Z` in datetime parser | `src/ephemeris_tools/time_utils.py`, `tests/test_time_utils.py` | Removed parser failures for `...T...Z` inputs; targeted case moved from `python_failed` to numeric compare. Full 74-case run improved **37/37 -> 39/35**. |
| 2026-02-16 | Normalize boundary seconds to minute precision for ephemeris stepping | `src/ephemeris_tools/ephemeris.py`, `tests/test_ephemeris.py` | Fixed `sc` column drift (e.g. `8` vs `0`) in hour/day/min runs; former failing case 4 now matches. Full 74-case run improved **39/35 -> 44/30**. |
| 2026-02-16 | Align second-step boundary normalization with FORTRAN time grid | `src/ephemeris_tools/ephemeris.py`, `tests/test_ephemeris.py` | Fixed off-by-one/time-grid mismatch in 20-second case (former line 3, `2070 vs 2069`) to exact match. Full 74-case run improved **44/30 -> 45/29**. |
| 2026-02-16 | Parse observatory `(lat, lon, alt)` strings for observer location | `src/ephemeris_tools/ephemeris.py`, `tests/test_ephemeris.py` | Fixed large topocentric geometry drift (`obs_dist`, `moon_sep`, `sun_sep`) for named observatories. Full 74-case run improved **45/29 -> 65/9**. |
| 2026-02-16 | Switch minute rounding to FORTRAN half-up behavior | `src/ephemeris_tools/ephemeris.py`, `tests/test_ephemeris.py` | Fixed systematic minute-field drift at `:30` boundaries in YDHM/YMDHM output formats. Full 74-case run improved **65/9 -> 68/6**. |
| 2026-02-16 | Correct Uranus sub-observer/sub-solar longitude convention | `src/ephemeris_tools/spice/geometry.py` | Fixed Uranus moon/planet longitude complements (`x` vs `360-x`) in sub-observer/sub-solar moon columns. Full 74-case run improved **68/6 -> 71/3**. |
| 2026-02-16 | Accept FORTRAN-style `YYYY HH:MM:SS` timestamps | `src/ephemeris_tools/time_utils.py`, `tests/test_time_utils.py` | Removed parser failure for historical year-only inputs (for example `1700 01:01:01`). Full 74-case run improved **71/3 -> 72/2**. |
| 2026-02-16 | Match FORTRAN stepping with normalized start + raw stop boundary | `src/ephemeris_tools/ephemeris.py`, `tests/test_ephemeris.py` | Fixed final off-by-one line-count edge cases in long day-step and short second-step runs. Full 74-case run improved **72/2 -> 74/0**. |
