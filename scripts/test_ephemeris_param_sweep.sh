#!/usr/bin/env bash
# Run ephemeris-tools ephemeris many times, varying one parameter (and some combinations).
# Writes tables to obviously-named files under OUTDIR for validation.
# Usage: ./scripts/test_ephemeris_param_sweep.sh [OUTDIR]
# Requires: ephemeris-tools on PATH (or run from repo root with pip install -e .)

set -euo pipefail

OUTDIR="${1:-./param_sweep_ephemeris}"
mkdir -p "$OUTDIR"
cd "$OUTDIR"
OUTDIR_ABS="$(pwd)"
cd - >/dev/null

CMD="${EPHEMERIS_TOOLS_CMD:-ephemeris-tools}"
if ! command -v "$CMD" &>/dev/null; then
    echo "Run from repo root with: pip install -e .  (or set EPHEMERIS_TOOLS_CMD)" >&2
    exit 1
fi

BASE_START="2022-01-01 00:00"
BASE_STOP="2022-01-02 00:00"

run() {
    "$CMD" ephemeris --start "$BASE_START" --stop "$BASE_STOP" "$@"
}

echo "Ephemeris param sweep -> $OUTDIR_ABS"

# ---- Planets ----
for planet in mars jupiter saturn uranus neptune pluto; do
    run --planet "$planet" -o "$OUTDIR_ABS/ephem_planet_${planet}.txt"
done

# ---- Single column IDs ----
for col in 1 2 3 5 6 8 15; do
    run --planet saturn --columns "$col" -o "$OUTDIR_ABS/ephem_column_${col}.txt"
done

# ---- Column names ----
for col in mjd ymdhms radec phase obsdist; do
    run --planet saturn --columns "$col" -o "$OUTDIR_ABS/ephem_column_${col}.txt"
done

# ---- Column combinations ----
run --planet saturn --columns 1 2 3 15 8 -o "$OUTDIR_ABS/ephem_columns_1_2_3_15_8.txt"
run --planet saturn --columns mjd ymdhms radec -o "$OUTDIR_ABS/ephem_columns_mjd_ymdhms_radec.txt"

# ---- Single moon column IDs (mooncols require at least one moon) ----
for mcol in 5 6 8 9; do
    run --planet saturn --moons mimas --mooncols "$mcol" -o "$OUTDIR_ABS/ephem_mooncol_${mcol}.txt"
done

# ---- Moon column names ----
for mcol in radec offset orblon orbopen; do
    run --planet saturn --moons mimas --mooncols "$mcol" -o "$OUTDIR_ABS/ephem_mooncol_${mcol}.txt"
done

# ---- Moon column combination ----
run --planet saturn --moons mimas --mooncols 5 6 8 9 -o "$OUTDIR_ABS/ephem_mooncols_5_6_8_9.txt"

# ---- Moons per planet (one moon) ----
run --planet saturn --moons mimas -o "$OUTDIR_ABS/ephem_saturn_moon_mimas.txt"
run --planet saturn --moons enceladus -o "$OUTDIR_ABS/ephem_saturn_moon_enceladus.txt"
run --planet jupiter --moons io -o "$OUTDIR_ABS/ephem_jupiter_moon_io.txt"
run --planet jupiter --moons europa -o "$OUTDIR_ABS/ephem_jupiter_moon_europa.txt"
run --planet uranus --moons miranda -o "$OUTDIR_ABS/ephem_uranus_moon_miranda.txt"
run --planet uranus --moons umbriel -o "$OUTDIR_ABS/ephem_uranus_moon_umbriel.txt"
run --planet neptune --moons triton -o "$OUTDIR_ABS/ephem_neptune_moon_triton.txt"
run --planet mars --moons phobos -o "$OUTDIR_ABS/ephem_mars_moon_phobos.txt"
run --planet pluto --moons charon -o "$OUTDIR_ABS/ephem_pluto_moon_charon.txt"

# ---- Moons per planet (two moons) ----
run --planet saturn --moons mimas enceladus -o "$OUTDIR_ABS/ephem_saturn_moons_mimas_enceladus.txt"
run --planet jupiter --moons io europa ganymede -o "$OUTDIR_ABS/ephem_jupiter_moons_io_europa_ganymede.txt"
run --planet uranus --moons miranda ariel umbriel -o "$OUTDIR_ABS/ephem_uranus_moons_miranda_ariel_umbriel.txt"

# ---- Combinations: planet + columns + mooncols + moons ----
run --planet saturn --columns 1 2 15 --mooncols 5 6 8 --moons mimas enceladus \
    -o "$OUTDIR_ABS/ephem_combination_saturn_cols_mooncols_moons.txt"
run --planet jupiter --columns mjd radec --mooncols radec offset --moons io europa \
    -o "$OUTDIR_ABS/ephem_combination_jupiter_cols_mooncols_moons.txt"
run --planet uranus --columns 1 3 8 --mooncols 5 9 --moons miranda \
    -o "$OUTDIR_ABS/ephem_combination_uranus_cols_mooncols_moon.txt"

echo "Done. Outputs in $OUTDIR_ABS"
