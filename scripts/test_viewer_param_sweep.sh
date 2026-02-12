#!/usr/bin/env bash
# Run ephemeris-tools viewer many times, varying one parameter (and some combinations).
# Writes PostScript then converts to PNG and removes PS. Outputs to obviously-named files.
# Usage: ./scripts/test_viewer_param_sweep.sh [OUTDIR]
# Requires: ephemeris-tools on PATH; ghostscript (gs) for PS->PNG.

set -euo pipefail

OUTDIR="${1:-./param_sweep_viewer}"
mkdir -p "$OUTDIR"
cd "$OUTDIR"
OUTDIR_ABS="$(pwd)"
cd - >/dev/null

CMD="${EPHEMERIS_TOOLS_CMD:-ephemeris-tools}"
if ! command -v "$CMD" &>/dev/null; then
    echo "Run from repo root with: pip install -e .  (or set EPHEMERIS_TOOLS_CMD)" >&2
    exit 1
fi
if ! command -v gs &>/dev/null; then
    echo "ghostscript (gs) required for PS->PNG. Install e.g. ghostscript." >&2
    exit 1
fi

BASE_TIME="2022-01-01 12:00"

run() {
    "$CMD" viewer --time "$BASE_TIME" "$@"
}

ps2png_rm() {
    local psfile="$1"
    local pngfile="${psfile%.ps}.png"
    gs -dSAFER -dNOPAUSE -dBATCH -sDEVICE=png16m -r150 -sOutputFile="$pngfile" "$psfile" >/dev/null 2>&1
    rm -f "$psfile"
}

echo "Viewer param sweep -> $OUTDIR_ABS (PS converted to PNG, PS removed)"

# ---- Planets ----
for planet in mars jupiter saturn uranus neptune pluto; do
    run --planet "$planet" -o "$OUTDIR_ABS/viewer_planet_${planet}.ps"
    ps2png_rm "$OUTDIR_ABS/viewer_planet_${planet}.ps"
done

# ---- Moons (one per planet) ----
run --planet saturn --moons mimas -o "$OUTDIR_ABS/viewer_saturn_moon_mimas.ps"
ps2png_rm "$OUTDIR_ABS/viewer_saturn_moon_mimas.ps"
run --planet saturn --moons enceladus tethys -o "$OUTDIR_ABS/viewer_saturn_moons_enceladus_tethys.ps"
ps2png_rm "$OUTDIR_ABS/viewer_saturn_moons_enceladus_tethys.ps"
run --planet jupiter --moons io europa -o "$OUTDIR_ABS/viewer_jupiter_moons_io_europa.ps"
ps2png_rm "$OUTDIR_ABS/viewer_jupiter_moons_io_europa.ps"
run --planet uranus --moons miranda umbriel -o "$OUTDIR_ABS/viewer_uranus_moons_miranda_umbriel.ps"
ps2png_rm "$OUTDIR_ABS/viewer_uranus_moons_miranda_umbriel.ps"
run --planet neptune --moons triton -o "$OUTDIR_ABS/viewer_neptune_moon_triton.ps"
ps2png_rm "$OUTDIR_ABS/viewer_neptune_moon_triton.ps"
run --planet mars --moons phobos deimos -o "$OUTDIR_ABS/viewer_mars_moons_phobos_deimos.ps"
ps2png_rm "$OUTDIR_ABS/viewer_mars_moons_phobos_deimos.ps"
run --planet pluto --moons charon -o "$OUTDIR_ABS/viewer_pluto_moon_charon.ps"
ps2png_rm "$OUTDIR_ABS/viewer_pluto_moon_charon.ps"

# ---- Rings: iterate through all ring options per planet ----
for ring in main gossamer; do
    run --planet jupiter --rings "$ring" -o "$OUTDIR_ABS/viewer_jupiter_rings_${ring}.ps"
    ps2png_rm "$OUTDIR_ABS/viewer_jupiter_rings_${ring}.ps"
done
for ring in main ge outer; do
    run --planet saturn --rings "$ring" --fov 0.01 -o "$OUTDIR_ABS/viewer_saturn_rings_${ring}.ps"
    ps2png_rm "$OUTDIR_ABS/viewer_saturn_rings_${ring}.ps"
done
for ring in alpha beta eta gamma delta epsilon; do
    run --planet uranus --rings "$ring" --fov 0.01 -o "$OUTDIR_ABS/viewer_uranus_rings_${ring}.ps"
    ps2png_rm "$OUTDIR_ABS/viewer_uranus_rings_${ring}.ps"
done
run --planet neptune --rings rings -o "$OUTDIR_ABS/viewer_neptune_rings_rings.ps"
ps2png_rm "$OUTDIR_ABS/viewer_neptune_rings_rings.ps"

# ---- FOV / fov-unit (1/25 of previous: 5x larger FOV = 1/25 the scale) ----
run --planet saturn --fov 0.1 -o "$OUTDIR_ABS/viewer_saturn_fov_0.1.ps"
ps2png_rm "$OUTDIR_ABS/viewer_saturn_fov_0.1.ps"
run --planet saturn --fov 0.4 -o "$OUTDIR_ABS/viewer_saturn_fov_0.4.ps"
ps2png_rm "$OUTDIR_ABS/viewer_saturn_fov_0.4.ps"
run --planet saturn --fov 6 --fov-unit arcmin -o "$OUTDIR_ABS/viewer_saturn_fov_6arcmin.ps"
ps2png_rm "$OUTDIR_ABS/viewer_saturn_fov_6arcmin.ps"
run --planet saturn --fov 0.1 --fov-unit deg -o "$OUTDIR_ABS/viewer_saturn_fov_0.1deg.ps"
ps2png_rm "$OUTDIR_ABS/viewer_saturn_fov_0.1deg.ps"

# ---- Combinations: planet + moons + rings ----
run --planet saturn --moons mimas enceladus --rings main -o "$OUTDIR_ABS/viewer_saturn_moons_rings.ps"
ps2png_rm "$OUTDIR_ABS/viewer_saturn_moons_rings.ps"
run --planet uranus --moons umbriel --rings alpha --fov 0.04 --fov-unit arcmin \
    -o "$OUTDIR_ABS/viewer_uranus_moon_umbriel_rings_alpha_fov_0.04arcmin.ps"
ps2png_rm "$OUTDIR_ABS/viewer_uranus_moon_umbriel_rings_alpha_fov_0.04arcmin.ps"
run --planet jupiter --moons io europa ganymede --rings main -o "$OUTDIR_ABS/viewer_jupiter_moons_rings.ps"
ps2png_rm "$OUTDIR_ABS/viewer_jupiter_moons_rings.ps"

echo "Done. PNGs in $OUTDIR_ABS"
