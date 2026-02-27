#!/usr/bin/env bash
#
# Generate random CGI queries and run Python-vs-FORTRAN comparisons
# for ephemeris, tracker, and viewer.
#
# Usage:
#   ./scripts/run-random-fortran-comparisons.sh <count> [--jobs N] [--dir DIR]
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

usage() {
    cat <<'EOF'
Usage:
  ./scripts/run-random-fortran-comparisons.sh <count> [--jobs N] [--dir DIR]

Arguments:
  <count>      Number of random queries per tool (positive integer).

Options:
  --jobs N     Parallel jobs passed to tests.compare_fortran (default: 1).
  --dir DIR    Top-level directory for output and query files (default: /tmp).
               Uses DIR/<tool>_out, DIR/<tool>_failed, DIR/random_queries_<tool>.txt.
  -h, --help   Show this help.
EOF
}

if [[ $# -lt 1 ]]; then
    usage
    exit 1
fi

COUNT=""
JOBS=1
BASE_DIR="/tmp"

while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            usage
            exit 0
            ;;
        --jobs)
            if [[ $# -lt 2 ]]; then
                echo "Error: --jobs requires a value." >&2
                exit 1
            fi
            JOBS="$2"
            shift 2
            ;;
        --dir)
            if [[ $# -lt 2 ]]; then
                echo "Error: --dir requires a value." >&2
                exit 1
            fi
            BASE_DIR="$2"
            shift 2
            ;;
        -*)
            echo "Error: unknown option: $1" >&2
            usage
            exit 1
            ;;
        *)
            if [[ -n "$COUNT" ]]; then
                echo "Error: unexpected extra argument: $1" >&2
                usage
                exit 1
            fi
            COUNT="$1"
            shift
            ;;
    esac
done

if ! [[ "$COUNT" =~ ^[0-9]+$ ]] || [[ "$COUNT" -le 0 ]]; then
    echo "Error: <count> must be a positive integer (got: $COUNT)." >&2
    exit 1
fi

if ! [[ "$JOBS" =~ ^[0-9]+$ ]] || [[ "$JOBS" -le 0 ]]; then
    echo "Error: --jobs must be a positive integer (got: $JOBS)." >&2
    exit 1
fi

BASE_DIR="$(cd "$BASE_DIR" && pwd)"
mkdir -p "$BASE_DIR"

rotate_if_exists() {
    local dir_path="$1"
    if [[ -e "$dir_path" ]]; then
        local base
        base="$(basename "$dir_path")"
        local rotated="${BASE_DIR}/${base}_${RUN_STAMP}"
        if [[ -e "$rotated" ]]; then
            rotated="${rotated}_$$"
        fi
        mv "$dir_path" "$rotated"
        echo "Rotated existing directory:"
        echo "  $dir_path -> $rotated"
    fi
}

TOOLS=(ephemeris tracker viewer)
EXIT_CODE=0
declare -A TOOL_STATUS
RUN_STAMP="$(date +"%Y%m%d_%H%M%S")"

for tool in "${TOOLS[@]}"; do
    out_dir="${BASE_DIR}/${tool}_out"
    failure_dir="${BASE_DIR}/${tool}_failed"
    query_file="${BASE_DIR}/random_queries_${tool}.txt"

    rotate_if_exists "$out_dir"
    rotate_if_exists "$failure_dir"
    rm -f "$query_file"

    echo
    echo "=== ${tool}: generating ${COUNT} random queries ==="
    if ! python "$PROJECT_ROOT/scripts/generate_random_query_urls.py" \
        -n "$COUNT" \
        -o "$query_file" \
        --tool "$tool"; then
        echo "Generation failed for ${tool}; skipping compare_fortran for this tool." >&2
        TOOL_STATUS["$tool"]="generation_failed"
        EXIT_CODE=1
        continue
    fi

    echo "=== ${tool}: running compare_fortran (jobs=${JOBS}) ==="
    if python -m tests.compare_fortran \
        --test-file "$query_file" \
        -o "$out_dir" \
        --collect-failed-to "$failure_dir" \
        -j "$JOBS"; then
        TOOL_STATUS["$tool"]="ok"
    else
        TOOL_STATUS["$tool"]="failed"
        EXIT_CODE=1
    fi

    echo "Completed ${tool}:"
    echo "  output:  $out_dir"
    echo "  failures: $failure_dir"
done

echo
echo "All comparisons finished. Directories (base: $BASE_DIR):"
for tool in "${TOOLS[@]}"; do
    echo "  ${tool}: ${BASE_DIR}/${tool}_out (status: ${TOOL_STATUS[$tool]:-not_run})"
    echo "  ${tool}: ${BASE_DIR}/${tool}_failed"
done

exit "$EXIT_CODE"
