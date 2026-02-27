#!/usr/bin/env bash
#
# Run Python-vs-FORTRAN comparisons using the predefined URL files
# in test_files/ (ephemeris-test-urls.txt, tracker-test-urls.txt,
# viewer-test-urls.txt).
#
# Usage:
#   ./scripts/run-fortran-comparison-test-files.sh [--jobs N]
#

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEST_FILES_DIR="$PROJECT_ROOT/test_files"

usage() {
    cat <<'EOF'
Usage:
  ./scripts/run-fortran-comparison-test-files.sh [--jobs N]

Options:
  --jobs N     Parallel jobs passed to tests.compare_fortran (default: 1).
  -h, --help   Show this help.
EOF
}

JOBS=1

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
        -*)
            echo "Error: unknown option: $1" >&2
            usage
            exit 1
            ;;
        *)
            echo "Error: unexpected argument: $1" >&2
            usage
            exit 1
            ;;
    esac
done

if ! [[ "$JOBS" =~ ^[0-9]+$ ]] || [[ "$JOBS" -le 0 ]]; then
    echo "Error: --jobs must be a positive integer (got: $JOBS)." >&2
    exit 1
fi

if [[ ! -d "$TEST_FILES_DIR" ]]; then
    echo "Error: test_files directory not found: $TEST_FILES_DIR" >&2
    exit 1
fi

EPHEM_FILE="$TEST_FILES_DIR/ephemeris-test-urls.txt"
TRACKER_FILE="$TEST_FILES_DIR/tracker-test-urls.txt"
VIEWER_FILE="$TEST_FILES_DIR/viewer-test-urls.txt"

for f in "$EPHEM_FILE" "$TRACKER_FILE" "$VIEWER_FILE"; do
    if [[ ! -f "$f" ]]; then
        echo "Error: required test file not found: $f" >&2
        exit 1
    fi
done

TOOLS=(ephemeris tracker viewer)
FILES=("$EPHEM_FILE" "$TRACKER_FILE" "$VIEWER_FILE")
EXIT_CODE=0
declare -A TOOL_STATUS
RUN_STAMP="$(date +"%Y%m%d_%H%M%S")"

rotate_if_exists() {
    local dir_path="$1"
    if [[ -e "$dir_path" ]]; then
        local base
        base="$(basename "$dir_path")"
        local rotated="/tmp/${base}_${RUN_STAMP}"
        if [[ -e "$rotated" ]]; then
            rotated="${rotated}_$$"
        fi
        mv "$dir_path" "$rotated"
        echo "Rotated existing directory:"
        echo "  $dir_path -> $rotated"
    fi
}

for i in "${!TOOLS[@]}"; do
    tool="${TOOLS[$i]}"
    test_file="${FILES[$i]}"
    out_dir="/tmp/${tool}_out"
    failure_dir="/tmp/${tool}_failed"

    rotate_if_exists "$out_dir"
    rotate_if_exists "$failure_dir"

    echo
    echo "=== ${tool}: running compare_fortran on $(wc -l < "$test_file") URLs (jobs=${JOBS}) ==="
    if python -m tests.compare_fortran \
        --test-file "$test_file" \
        -o "$out_dir" \
        --collect-failed-to "$failure_dir" \
        -j "$JOBS"; then
        TOOL_STATUS["$tool"]="ok"
    else
        TOOL_STATUS["$tool"]="failed"
        EXIT_CODE=1
    fi

    echo "Completed ${tool}:"
    echo "  output:   $out_dir"
    echo "  failures: $failure_dir"
done

echo
echo "All comparisons finished. Directories:"
for tool in "${TOOLS[@]}"; do
    echo "  ${tool}: /tmp/${tool}_out (status: ${TOOL_STATUS[$tool]:-not_run})"
    echo "  ${tool}: /tmp/${tool}_failed"
done

exit "$EXIT_CODE"
