#!/usr/bin/env bash
# ephem3_xxx.sh — CGI script for the Ephemeris Generator.
#
# Replaces the old Perl script ephem3_xxx.pl.
# Called by the HTML forms (EPHEM3_FORM.shtml via ephem3_*.shtml).
#
# The HTML form sends parameters including:
#   abbrev, version, output, start, stop, interval, time_unit,
#   viewpoint, observatory, latitude, longitude, lon_dir, altitude,
#   ephem, columns (multi-valued), mooncols (multi-valued),
#   moons (multi-valued)
#
# This script parses those parameters and calls:
#   ephemeris-tools ephemeris --planet <N> --start ... --stop ... [options]

# NOTE: Do NOT use "set -euo pipefail" in CGI scripts — any failure before
# HTTP headers are printed causes Apache "End of script output before headers".
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/parse_cgi.sh"
trap cgi_error_trap EXIT

# ---------------------------------------------------------------------------
# Parse CGI parameters
# ---------------------------------------------------------------------------
parse_query_string

abbrev="$(cgi_get abbrev | tr '[:upper:]' '[:lower:]')"
version="$(cgi_get version "3.0")"
output="$(cgi_get output "HTML")"

short="${abbrev:0:3}"
extra="${abbrev:3}"

planet_num="$(abbrev_to_planet "$short")"
planet_name="$(abbrev_to_name "$short")"
if [[ -z "$planet_num" ]]; then
    html_error_page "Ephemeris Generator ${version} Configuration Failure"
fi

title="$(mission_title "$planet_name" "$extra")"

# ---------------------------------------------------------------------------
# Unique work file
# ---------------------------------------------------------------------------
make_work_paths "ephem3" "$short"

# ---------------------------------------------------------------------------
# Build CLI arguments
# ---------------------------------------------------------------------------
cli_args=( ephemeris --planet "$planet_num" )

start_time="$(cgi_get start "")"
stop_time="$(cgi_get stop "")"
interval="$(cgi_get interval "1")"
time_unit_raw="$(cgi_get time_unit "hours")"

# Map form time units to CLI units
time_unit="hour"
case "$time_unit_raw" in
    *second*) time_unit="sec" ;;
    *minute*) time_unit="min" ;;
    *hour*)   time_unit="hour" ;;
    *day*)    time_unit="day" ;;
esac

if [[ -n "$start_time" ]]; then cli_args+=( --start "$start_time" ); fi
if [[ -n "$stop_time" ]];  then cli_args+=( --stop "$stop_time" );   fi
cli_args+=( --interval "$interval" --time-unit "$time_unit" )

# Viewpoint
viewpoint="$(cgi_get viewpoint "observatory")"
observatory="$(cgi_get observatory "Earth's center")"
if [[ "$viewpoint" == "latlon" ]]; then
    cli_args+=( --viewpoint latlon )
    lat="$(cgi_get latitude "")"
    lon="$(cgi_get longitude "")"
    lon_dir="$(cgi_get lon_dir "east")"
    alt="$(cgi_get altitude "")"
    if [[ -n "$lat" ]]; then cli_args+=( --latitude "$lat" );                        fi
    if [[ -n "$lon" ]]; then cli_args+=( --longitude "$lon" --lon-dir "$lon_dir" );  fi
    if [[ -n "$alt" ]]; then cli_args+=( --altitude "$alt" );                        fi
else
    cli_args+=( --viewpoint observatory --observatory "$observatory" )
fi

# Ephemeris version — form sends "000 JUP365 + DE440"; extract leading number
ephem_raw="$(cgi_get ephem "0")"
ephem_num="$(extract_id "$ephem_raw")"
cli_args+=( --ephem "$ephem_num" )

# Columns (multi-valued checkboxes, form sends "001 Modified Julian Date" etc.)
columns_list=()
while IFS= read -r val; do
    [[ -z "$val" ]] && continue
    columns_list+=( "$(extract_id "$val")" )
done < <(cgi_get_multi columns)
if [[ ${#columns_list[@]} -gt 0 ]]; then
    cli_args+=( --columns "${columns_list[@]}" )
fi

# Moon columns (multi-valued)
mooncols_list=()
while IFS= read -r val; do
    [[ -z "$val" ]] && continue
    mooncols_list+=( "$(extract_id "$val")" )
done < <(cgi_get_multi mooncols)
if [[ ${#mooncols_list[@]} -gt 0 ]]; then
    cli_args+=( --mooncols "${mooncols_list[@]}" )
fi

# Moons (multi-valued, form sends "001 Mimas (S1)" etc.)
moons_list=()
while IFS= read -r val; do
    [[ -z "$val" ]] && continue
    moons_list+=( "$(extract_id "$val")" )
done < <(cgi_get_multi moons)
if [[ ${#moons_list[@]} -gt 0 ]]; then
    cli_args+=( --moons "${moons_list[@]}" )
fi

# Output file
cli_args+=( -o "$TAB_FILE" )

# ---------------------------------------------------------------------------
# Execute the Python tool
# ---------------------------------------------------------------------------
export SPICEPATH="${SPICEPATH:-/var/www/SPICE/}"
run_output="$("$EPHEMERIS_TOOLS" "${cli_args[@]}" 2>&1)" || true

# ---------------------------------------------------------------------------
# Check result
# ---------------------------------------------------------------------------
exists=false
if [[ -f "$TAB_FILE" ]]; then
    # A file with only a header line doesn't count
    line_count="$(wc -l < "$TAB_FILE")"
    if [[ "$line_count" -gt 1 ]]; then
        exists=true
    fi
fi

# ---------------------------------------------------------------------------
# Return the result in the requested format
# ---------------------------------------------------------------------------

# TAB-only output: return raw table
if [[ "$output" == "TAB" ]] && $exists; then
    mark_headers_sent
    echo "Content-Type: text/plain"
    echo ""
    cat "$TAB_FILE"
    exit 0
fi

# HTML output (default): show program output and download link
mark_headers_sent
echo "Content-Type: text/html"
echo ""
cat <<HTMLEOF
<!DOCTYPE html>
<html>
<head><title>${title} Ephemeris Generator ${version} Results</title></head>
<body style="font-family:arial; font-size:medium">
<h1>${title} Ephemeris Generator ${version} Results</h1>
<p></p>
<pre>
${run_output}
</pre>
HTMLEOF

if $exists; then
    size="$(stat -c%s "$TAB_FILE" 2>/dev/null || stat -f%z "$TAB_FILE" 2>/dev/null || echo "?")"
    cat <<HTMLEOF
<hr/>
Click <a href="${TAB_LINK}">here</a>
to download table (ASCII format, ${size} bytes).
HTMLEOF
else
    echo "Request failed."
fi

cat <<HTMLEOF
<hr/>
<a href="/tools/ephem3_${abbrev}.shtml">${title} Ephemeris Generator Form</a> |
<a href="/tools/index.html">RMS Node Tools</a> |
<a href="/">Ring-Moon Systems Home</a>
</body>
</html>
HTMLEOF
exit 0
