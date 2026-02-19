#!/usr/bin/env bash
# CGI wrapper: match output of web/old/cgi-bin/tools/ephem3_xxx.pl exactly.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/parse_cgi.sh"
trap cgi_error_trap EXIT

parse_query_string
abbrev="$(cgi_get abbrev | tr '[:upper:]' '[:lower:]')"
version="$(cgi_get version)"
output="$(cgi_get output)"
short="${abbrev:0:3}"

planet_num="$(abbrev_to_planet "$short")"
if [[ -z "$planet_num" ]]; then
    mark_headers_sent
    printf 'Content-Type: text/html\n\n'
    printf '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n'
    printf '<html>\n'
    printf '<title>Ephemeris Generator %s Configuration Failure</title>\n' "$version"
    printf '<body style="font-family:arial; font-size:medium">\n'
    printf '<h1>Ephemeris Generator %s Configuration Failure</h1>\n' "$version"
    printf '<p>\n'
    printf 'Please report this error to the RMS website administrator,\n'
    printf '<a href="mailto:pds-admin@seti.org">pds-admin@seti.org</a></p>\n'
    printf '</body>\n'
    printf '</html>\n'
    exit 0
fi

# Use page_title for HTML only; leave env "title" as form value for Python.
page_title="$(mission_title "$(abbrev_to_name "$short")" "${abbrev:3}")"
pid=$$
ephem_file="${WWW_WORK}/viewer3_${short}_${pid}.tab"
ephem_link="/work/viewer3_${short}_${pid}.tab"

export NPLANET="$planet_num"
export EPHEM_FILE="$ephem_file"
export SPICEPATH="${SPICEPATH:-/var/www/SPICE/}"
export REQUEST_METHOD="${REQUEST_METHOD:-GET}"

run_out=$(mktemp)
trap 'rm -f "$run_out"; cgi_error_trap' EXIT
"$PYTHON" -m ephemeris_tools.cli.main ephemeris --cgi > "$run_out"

exists=0
if [[ -f "$ephem_file" ]]; then
    # File with nothing but a header line doesn't count (match Perl)
    line2=$(sed -n '2p' "$ephem_file")
    [[ -n "$line2" ]] && exists=1
fi

if [[ "$output" == "TAB" && $exists -eq 1 ]]; then
    mark_headers_sent
    printf 'Content-Type: text/plain\n\n'
    cat "$ephem_file"
    exit 0
fi

mark_headers_sent
printf 'Content-Type: text/html\n\n'
printf '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n'
printf '<html>\n'
printf '<title>%s Ephemeris Generator %s Results</title>\n' "$page_title" "$version"
printf '<body style="font-family:arial; font-size:medium">\n'
printf '<h1>%s Ephemeris Generator %s Results</h1>\n' "$page_title" "$version"
printf '<p></p>\n'
printf '<pre>\n'
cat "$run_out"
printf '</pre>\n'

if [[ $exists -eq 1 ]]; then
    size=$(stat -c%s "$ephem_file" 2>/dev/null || stat -f%z "$ephem_file" 2>/dev/null)
    printf '<hr/>\n'
    printf 'Click <a href="%s">here</a>\n' "$ephem_link"
    printf 'to download table (ASCII format, %s bytes).\n' "$size"
else
    printf 'Request failed.\n'
fi

printf '<hr/>\n'
printf '<a href="/tools/ephem3_%s.shtml">%s Ephemeris Generator Form</a> |\n' "$abbrev" "$page_title"
printf '<a href="/tools/index.html">RMS Node Tools</a> |\n'
printf '<a href="/">Ring-Moon Systems Home</a>\n'
printf '</body>\n'
printf '</html>\n'
exit 0
