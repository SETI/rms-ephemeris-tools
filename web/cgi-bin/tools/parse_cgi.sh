#!/usr/bin/env bash
# parse_cgi.sh — Shared CGI parameter parsing for ephemeris-tools CGI scripts.
#
# Source this file to get:
#   parse_query_string  — parse GET/POST query string into CGI_* variables
#   url_decode          — percent-decode a string
#   cgi_get             — get a single CGI parameter value
#   cgi_get_multi       — get a multi-valued CGI parameter (# separated)
#   abbrev_to_planet    — map 3-letter abbreviation to planet number
#   abbrev_to_name      — map 3-letter abbreviation to planet name
#   mission_title       — build title string with optional mission prefix
#   html_error_page     — emit an HTML error page and exit
#   cgi_error_trap      — trap handler that emits headers before dying
#   make_work_paths     — create unique temporary file paths in WWW_WORK
#
# IMPORTANT: Do NOT use "set -eu" in CGI scripts.  Any failure before HTTP
# headers are printed causes Apache to report "End of script output before
# headers".  Instead, we install a trap that prints a minimal error page.

# ---------------------------------------------------------------------------
# Configuration (override before sourcing if needed)
# ---------------------------------------------------------------------------
: "${WWW_WORK:=/var/www/work}"
export PATH="/var/www/cgi-bin/tools/venv/bin:${PATH}"
: "${EPHEMERIS_TOOLS:=ephemeris-tools}"
: "${GS:=/usr/bin/gs}"
: "${PDFTOPPM:=/usr/bin/pdftoppm}"

# ---------------------------------------------------------------------------
# Error trap — ensures HTTP headers are emitted even on unexpected failure.
# Install in each CGI script with:  trap cgi_error_trap ERR EXIT
# ---------------------------------------------------------------------------
_CGI_HEADERS_SENT=0

cgi_error_trap() {
    local rc=$?
    if [[ $rc -ne 0 ]] && [[ $_CGI_HEADERS_SENT -eq 0 ]]; then
        echo "Content-Type: text/html"
        echo ""
        echo "<html><body><h1>Internal Error</h1>"
        echo "<p>The CGI script encountered an unexpected error (exit code $rc).</p>"
        echo "<p>Contact <a href=\"mailto:pds-admin@seti.org\">pds-admin@seti.org</a></p>"
        echo "</body></html>"
    fi
}

# Mark that headers have been sent (call before first "Content-Type" line)
mark_headers_sent() {
    _CGI_HEADERS_SENT=1
}

# ---------------------------------------------------------------------------
# URL-decode a string (percent encoding + plus-as-space)
# ---------------------------------------------------------------------------
url_decode() {
    local encoded="${1:-}"
    encoded="${encoded//+/ }"
    # Use printf to decode %XX sequences
    printf '%b' "${encoded//%/\\x}"
}

# ---------------------------------------------------------------------------
# Parse QUERY_STRING (GET/PUT) or stdin (POST) into associative array
# CGI_PARAMS.  Multi-valued params are joined with '#' (matching old Perl
# newcgi.pm).  Each param is also exported as an environment variable.
#
# HTML forms with method="PUT" are treated as GET by browsers, so the
# params arrive in QUERY_STRING.
# ---------------------------------------------------------------------------
declare -A CGI_PARAMS=()

parse_query_string() {
    local qs=""
    local method="${REQUEST_METHOD:-GET}"

    if [[ "$method" == "POST" ]]; then
        read -r -n "${CONTENT_LENGTH:-0}" qs || true
    else
        # GET, PUT, or anything else — params are in QUERY_STRING
        qs="${QUERY_STRING:-}"
    fi

    [[ -z "$qs" ]] && return 0

    # Split on &
    local saved_IFS="$IFS"
    IFS='&'
    local -a pairs
    read -ra pairs <<< "$qs" || true
    IFS="$saved_IFS"

    local pair key val
    for pair in "${pairs[@]}"; do
        [[ -z "$pair" ]] && continue
        key="${pair%%=*}"
        val="${pair#*=}"
        key="$(url_decode "$key")"
        val="$(url_decode "$val")"
        if [[ -n "${CGI_PARAMS[$key]+isset}" ]]; then
            CGI_PARAMS["$key"]="${CGI_PARAMS[$key]}#${val}"
        else
            CGI_PARAMS["$key"]="$val"
        fi
        export "$key"="$val" 2>/dev/null || true
    done
    return 0
}

# ---------------------------------------------------------------------------
# Get a single CGI parameter (first value if multi-valued)
# Uses ${array[key]+isset} pattern to avoid "unbound variable" on bash < 4.4.
# ---------------------------------------------------------------------------
cgi_get() {
    local key="${1:-}"
    local default="${2:-}"
    local val
    if [[ -n "${CGI_PARAMS[$key]+isset}" ]]; then
        val="${CGI_PARAMS[$key]}"
    else
        val="$default"
    fi
    # Return only the first value (before any #)
    echo "${val%%#*}"
}

# ---------------------------------------------------------------------------
# Get all values for a multi-valued CGI parameter as a newline-separated list
# ---------------------------------------------------------------------------
cgi_get_multi() {
    local key="${1:-}"
    if [[ -z "${CGI_PARAMS[$key]+isset}" ]]; then
        return 0
    fi
    local val="${CGI_PARAMS[$key]}"
    [[ -z "$val" ]] && return 0
    echo "$val" | tr '#' '\n'
}

# ---------------------------------------------------------------------------
# Map 3-letter abbreviation to planet number
# ---------------------------------------------------------------------------
abbrev_to_planet() {
    case "${1:-}" in
        mar) echo 4 ;;
        jup) echo 5 ;;
        sat) echo 6 ;;
        ura) echo 7 ;;
        nep) echo 8 ;;
        plu) echo 9 ;;
        *)   echo "" ;;
    esac
}

# ---------------------------------------------------------------------------
# Map 3-letter abbreviation to planet name
# ---------------------------------------------------------------------------
abbrev_to_name() {
    case "${1:-}" in
        mar) echo "Mars" ;;
        jup) echo "Jupiter" ;;
        sat) echo "Saturn" ;;
        ura) echo "Uranus" ;;
        nep) echo "Neptune" ;;
        plu) echo "Pluto" ;;
        *)   echo "Unknown" ;;
    esac
}

# ---------------------------------------------------------------------------
# Build a title string with optional mission prefix
# ---------------------------------------------------------------------------
mission_title() {
    local planet_name="${1:-}"
    local extra="${2:-}"
    case "$extra" in
        c)  echo "Cassini/${planet_name}" ;;
        j)  echo "Juno/${planet_name}" ;;
        nh) echo "New Horizons/${planet_name}" ;;
        ec) echo "Europa Clipper/${planet_name}" ;;
        jc) echo "JUICE/${planet_name}" ;;
        *)  echo "${planet_name}" ;;
    esac
}

# ---------------------------------------------------------------------------
# Emit an HTML error page and exit
# ---------------------------------------------------------------------------
html_error_page() {
    local title="${1:-Error}"
    local message="${2:-Please report this error to the RMS website administrator.}"
    mark_headers_sent
    echo "Content-Type: text/html"
    echo ""
    cat <<HTMLEOF
<!DOCTYPE html>
<html>
<head><title>${title}</title></head>
<body style="font-family:arial; font-size:medium">
<h1>${title}</h1>
<p>${message}</p>
<p>Contact <a href="mailto:pds-admin@seti.org">pds-admin@seti.org</a></p>
</body>
</html>
HTMLEOF
    exit 0
}

# ---------------------------------------------------------------------------
# Create unique work paths.  Sets global variables:
#   WORK_BASE, PS_FILE, PDF_FILE, JPG_FILE, THUMB_FILE, TAB_FILE
#   PS_LINK,   PDF_LINK, JPG_LINK, THUMB_LINK, TAB_LINK
# ---------------------------------------------------------------------------
make_work_paths() {
    local tool="${1:-tool}"
    local short="${2:-xxx}"
    local pid="$$"

    WORK_BASE="${WWW_WORK}/${tool}_${short}_${pid}"
    PS_FILE="${WORK_BASE}.ps"
    PDF_FILE="${WORK_BASE}.pdf"
    JPG_FILE="${WORK_BASE}.jpg"
    THUMB_FILE="${WORK_BASE}tn.jpg"
    TAB_FILE="${WORK_BASE}.tab"

    local link_base="/work/${tool}_${short}_${pid}"
    PS_LINK="${link_base}.ps"
    PDF_LINK="${link_base}.pdf"
    JPG_LINK="${link_base}.jpg"
    THUMB_LINK="${link_base}tn.jpg"
    TAB_LINK="${link_base}.tab"
}

# ---------------------------------------------------------------------------
# Convert PostScript to PDF using Ghostscript
# ---------------------------------------------------------------------------
ps_to_pdf() {
    local ps="${1:-}" pdf="${2:-}"
    "$GS" -dNOPAUSE -dBATCH -dQUIET -sDEVICE=pdfwrite \
        -sOutputFile="$pdf" "$ps" 2>/dev/null || true
}

# ---------------------------------------------------------------------------
# Convert PDF to JPEG using pdftoppm
# ---------------------------------------------------------------------------
pdf_to_jpeg() {
    local pdf="${1:-}" jpg_root="${2:-}"
    "$PDFTOPPM" -jpeg -singlefile "$pdf" "$jpg_root" 2>/dev/null || true
}

# ---------------------------------------------------------------------------
# Convert PDF to JPEG thumbnail using pdftoppm at low resolution
# ---------------------------------------------------------------------------
pdf_to_thumb() {
    local pdf="${1:-}" thumb_root="${2:-}"
    "$PDFTOPPM" -jpeg -singlefile -r 36 "$pdf" "$thumb_root" 2>/dev/null || true
}

# ---------------------------------------------------------------------------
# Extract the leading numeric ID from a form value like "001 Mimas (S1)"
# ---------------------------------------------------------------------------
extract_id() {
    local val="${1:-}"
    # Strip leading whitespace and grab the first token (numeric)
    val="${val#"${val%%[! ]*}"}"  # trim leading spaces
    echo "${val%% *}"
}
