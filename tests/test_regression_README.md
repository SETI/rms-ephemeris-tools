# Regression Tests (222 test URLs)

To validate Python output against FORTRAN:

1. Build and run the FORTRAN tools to generate golden outputs for each of the 75 ephemeris, 62 tracker, and 85 viewer test URLs.
2. Run the Python equivalents with the same parameters (via env vars or CLI).
3. Compare: tabular output numerically (within machine epsilon); PostScript output normalized (e.g. strip comments/dates).

Test URL lists and parameter sets are maintained alongside the FORTRAN test suite.
