#!/usr/bin/env bash
# Thin CGI wrapper: parse env vars, then invoke Python --cgi mode directly.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/parse_cgi.sh"
trap cgi_error_trap EXIT

parse_query_string
abbrev="$(cgi_get abbrev | tr '[:upper:]' '[:lower:]')"
short="${abbrev:0:3}"
planet_num="$(abbrev_to_planet "$short")"
if [[ -z "$planet_num" ]]; then
    html_error_page "Ephemeris Generator Configuration Failure"
fi
make_work_paths "ephem3" "$short"

export NPLANET="$planet_num"
export EPHEM_FILE="$TAB_FILE"
export SPICEPATH="${SPICEPATH:-/var/www/SPICE/}"
exec "$EPHEMERIS_TOOLS" ephemeris --cgi
