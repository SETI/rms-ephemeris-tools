#!/usr/bin/env bash
# Run ephemeris-tools tracker many times, varying one parameter (and some combinations).
# Writes PostScript and text table; converts PS to PNG and removes PS.
# Usage: ./scripts/test_tracker_param_sweep.sh [OUTDIR]
# Requires: ephemeris-tools on PATH; ghostscript (gs) for PS->PNG.

set -euo pipefail

OUTDIR="${1:-./param_sweep_tracker}"
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

BASE_START="2022-01-01 00:00"
BASE_STOP="2022-01-02 00:00"

run() {
    "$CMD" tracker --start "$BASE_START" --stop "$BASE_STOP" "$@"
}

ps2png_rm() {
    local psfile="$1"
    local pngfile="${psfile%.ps}.png"
    gs -dSAFER -dNOPAUSE -dBATCH -sDEVICE=png16m -r150 -sOutputFile="$pngfile" "$psfile" >/dev/null 2>&1
    rm -f "$psfile"
}

echo "Tracker param sweep -> $OUTDIR_ABS (PS converted to PNG, PS removed)"

# ---- Planets ----
for planet in mars jupiter saturn uranus neptune pluto; do
    run --planet "$planet" -o "$OUTDIR_ABS/tracker_planet_${planet}.ps" \
        --output-txt "$OUTDIR_ABS/tracker_planet_${planet}.txt"
    ps2png_rm "$OUTDIR_ABS/tracker_planet_${planet}.ps"
done

# ---- Moons (one or two per planet) ----
run --planet saturn --moons mimas -o "$OUTDIR_ABS/tracker_saturn_moon_mimas.ps" \
    --output-txt "$OUTDIR_ABS/tracker_saturn_moon_mimas.txt"
ps2png_rm "$OUTDIR_ABS/tracker_saturn_moon_mimas.ps"
run --planet saturn --moons mimas enceladus tethys -o "$OUTDIR_ABS/tracker_saturn_moons_mimas_enceladus_tethys.ps" \
    --output-txt "$OUTDIR_ABS/tracker_saturn_moons_mimas_enceladus_tethys.txt"
ps2png_rm "$OUTDIR_ABS/tracker_saturn_moons_mimas_enceladus_tethys.ps"
run --planet jupiter --moons io europa -o "$OUTDIR_ABS/tracker_jupiter_moons_io_europa.ps" \
    --output-txt "$OUTDIR_ABS/tracker_jupiter_moons_io_europa.txt"
ps2png_rm "$OUTDIR_ABS/tracker_jupiter_moons_io_europa.ps"
run --planet uranus --moons miranda ariel -o "$OUTDIR_ABS/tracker_uranus_moons_miranda_ariel.ps" \
    --output-txt "$OUTDIR_ABS/tracker_uranus_moons_miranda_ariel.txt"
ps2png_rm "$OUTDIR_ABS/tracker_uranus_moons_miranda_ariel.ps"
run --planet neptune --moons triton -o "$OUTDIR_ABS/tracker_neptune_moon_triton.ps" \
    --output-txt "$OUTDIR_ABS/tracker_neptune_moon_triton.txt"
ps2png_rm "$OUTDIR_ABS/tracker_neptune_moon_triton.ps"
run --planet mars --moons phobos deimos -o "$OUTDIR_ABS/tracker_mars_moons_phobos_deimos.ps" \
    --output-txt "$OUTDIR_ABS/tracker_mars_moons_phobos_deimos.txt"
ps2png_rm "$OUTDIR_ABS/tracker_mars_moons_phobos_deimos.ps"
run --planet pluto --moons charon nix -o "$OUTDIR_ABS/tracker_pluto_moons_charon_nix.ps" \
    --output-txt "$OUTDIR_ABS/tracker_pluto_moons_charon_nix.txt"
ps2png_rm "$OUTDIR_ABS/tracker_pluto_moons_charon_nix.ps"

# ---- Rings (planets that have rings) ----
run --planet jupiter --rings main -o "$OUTDIR_ABS/tracker_jupiter_rings_main.ps" \
    --output-txt "$OUTDIR_ABS/tracker_jupiter_rings_main.txt"
ps2png_rm "$OUTDIR_ABS/tracker_jupiter_rings_main.ps"
run --planet jupiter --rings main gossamer -o "$OUTDIR_ABS/tracker_jupiter_rings_main_gossamer.ps" \
    --output-txt "$OUTDIR_ABS/tracker_jupiter_rings_main_gossamer.txt"
ps2png_rm "$OUTDIR_ABS/tracker_jupiter_rings_main_gossamer.ps"
run --planet saturn --rings main -o "$OUTDIR_ABS/tracker_saturn_rings_main.ps" \
    --output-txt "$OUTDIR_ABS/tracker_saturn_rings_main.txt"
ps2png_rm "$OUTDIR_ABS/tracker_saturn_rings_main.ps"
run --planet saturn --rings main ge -o "$OUTDIR_ABS/tracker_saturn_rings_main_ge.ps" \
    --output-txt "$OUTDIR_ABS/tracker_saturn_rings_main_ge.txt"
ps2png_rm "$OUTDIR_ABS/tracker_saturn_rings_main_ge.ps"
run --planet saturn --rings outer -o "$OUTDIR_ABS/tracker_saturn_rings_outer.ps" \
    --output-txt "$OUTDIR_ABS/tracker_saturn_rings_outer.txt"
ps2png_rm "$OUTDIR_ABS/tracker_saturn_rings_outer.ps"
run --planet uranus --rings epsilon -o "$OUTDIR_ABS/tracker_uranus_rings_epsilon.ps" \
    --output-txt "$OUTDIR_ABS/tracker_uranus_rings_epsilon.txt"
ps2png_rm "$OUTDIR_ABS/tracker_uranus_rings_epsilon.ps"
run --planet neptune --rings rings -o "$OUTDIR_ABS/tracker_neptune_rings_rings.ps" \
    --output-txt "$OUTDIR_ABS/tracker_neptune_rings_rings.txt"
ps2png_rm "$OUTDIR_ABS/tracker_neptune_rings_rings.ps"

# ---- xrange / xunit ----
run --planet saturn --xrange 60 -o "$OUTDIR_ABS/tracker_saturn_xrange_60.ps" \
    --output-txt "$OUTDIR_ABS/tracker_saturn_xrange_60.txt"
ps2png_rm "$OUTDIR_ABS/tracker_saturn_xrange_60.ps"
run --planet saturn --xrange 2 --xunit radii -o "$OUTDIR_ABS/tracker_saturn_xrange_2radii.ps" \
    --output-txt "$OUTDIR_ABS/tracker_saturn_xrange_2radii.txt"
ps2png_rm "$OUTDIR_ABS/tracker_saturn_xrange_2radii.ps"

# ---- Combinations: planet + moons + rings ----
run --planet saturn --moons mimas enceladus --rings main -o "$OUTDIR_ABS/tracker_saturn_moons_rings.ps" \
    --output-txt "$OUTDIR_ABS/tracker_saturn_moons_rings.txt"
ps2png_rm "$OUTDIR_ABS/tracker_saturn_moons_rings.ps"
run --planet jupiter --moons io europa ganymede --rings main gossamer \
    -o "$OUTDIR_ABS/tracker_jupiter_moons_rings.ps" \
    --output-txt "$OUTDIR_ABS/tracker_jupiter_moons_rings.txt"
ps2png_rm "$OUTDIR_ABS/tracker_jupiter_moons_rings.ps"
run --planet uranus --moons miranda umbriel --rings alpha \
    -o "$OUTDIR_ABS/tracker_uranus_moons_rings.ps" \
    --output-txt "$OUTDIR_ABS/tracker_uranus_moons_rings.txt"
ps2png_rm "$OUTDIR_ABS/tracker_uranus_moons_rings.ps"

echo "Done. PNGs and .txt tables in $OUTDIR_ABS"
