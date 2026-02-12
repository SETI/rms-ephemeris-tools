#!/usr/bin/env bash
# tracker3_xxx.sh — CGI script for the Moon Tracker.
#
# Replaces the old Perl script tracker3_xxx.pl.
# Called by the HTML forms (TRACKER3_FORM.shtml via tracker3_*.shtml).
#
# The HTML form sends parameters including:
#   abbrev, version, output, start, stop, interval, time_unit,
#   viewpoint, observatory, latitude, longitude, lon_dir, altitude,
#   ephem, moons (multi-valued), rings (multi-valued),
#   xrange, xunit, title
#
# This script parses those parameters and calls:
#   ephemeris-tools tracker --planet <N> --start ... --stop ... [options]

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
    html_error_page "Moon Tracker ${version} Configuration Failure"
fi

title="$(mission_title "$planet_name" "$extra")"

# ---------------------------------------------------------------------------
# Unique work files
# ---------------------------------------------------------------------------
make_work_paths "tracker3" "$short"

# ---------------------------------------------------------------------------
# Build CLI arguments
# ---------------------------------------------------------------------------
cli_args=( tracker --planet "$planet_num" )

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

# Ephemeris version
ephem_raw="$(cgi_get ephem "0")"
ephem_num="$(extract_id "$ephem_raw")"
cli_args+=( --ephem "$ephem_num" )

# Moons (multi-valued, form sends "001 Mimas (S1)" etc.)
moons_list=()
while IFS= read -r val; do
    [[ -z "$val" ]] && continue
    moons_list+=( "$(extract_id "$val")" )
done < <(cgi_get_multi moons)
if [[ ${#moons_list[@]} -gt 0 ]]; then
    cli_args+=( --moons "${moons_list[@]}" )
fi

# Rings (multi-valued checkboxes, form sends "051 Main Ring", "061 Main Rings", etc.)
rings_list=()
while IFS= read -r val; do
    [[ -z "$val" ]] && continue
    rings_list+=( "$(extract_id "$val")" )
done < <(cgi_get_multi rings)
if [[ ${#rings_list[@]} -gt 0 ]]; then
    cli_args+=( --rings "${rings_list[@]}" )
fi

# Scale
xrange="$(cgi_get xrange "")"
xunit_raw="$(cgi_get xunit "")"
if [[ -n "$xrange" ]]; then
    cli_args+=( --xrange "$xrange" )
fi
case "$xunit_raw" in
    *arcsec*) cli_args+=( --xunit arcsec ) ;;
    *radii*)  cli_args+=( --xunit radii ) ;;
    *degree*) cli_args+=( --xunit arcsec ) ;;  # degrees: treat as arcsec for spacecraft
esac

# Title
plot_title="$(cgi_get title "")"
if [[ -n "$plot_title" ]]; then
    cli_args+=( --title "$plot_title" )
fi

# Output files
cli_args+=( -o "$PS_FILE" --output-txt "$TAB_FILE" )

# ---------------------------------------------------------------------------
# Execute the Python tool
# ---------------------------------------------------------------------------
export SPICEPATH="${SPICEPATH:-/var/www/SPICE/}"
run_output="$("$EPHEMERIS_TOOLS" "${cli_args[@]}" 2>&1)" || true

# ---------------------------------------------------------------------------
# Check result and handle output format
# ---------------------------------------------------------------------------
if [[ -f "$PS_FILE" ]]; then

    # PS-only output
    if [[ "$output" == "PS" ]]; then
        mark_headers_sent
        echo "Content-Type: application/postscript"
        echo ""
        cat "$PS_FILE"
        exit 0
    fi

    # TAB-only output
    if [[ "$output" == "TAB" ]] && [[ -f "$TAB_FILE" ]]; then
        mark_headers_sent
        echo "Content-Type: text/plain"
        echo ""
        cat "$TAB_FILE"
        exit 0
    fi

    # Create PDF
    ps_to_pdf "$PS_FILE" "$PDF_FILE"

    # PDF-only output
    if [[ "$output" == "PDF" ]] && [[ -f "$PDF_FILE" ]]; then
        mark_headers_sent
        echo "Content-Type: application/pdf"
        echo ""
        cat "$PDF_FILE"
        exit 0
    fi

    # Create JPEG
    jpg_root="${WORK_BASE}"
    pdf_to_jpeg "$PDF_FILE" "$jpg_root"

    # JPEG-only output
    if [[ "$output" == "JPEG" ]] && [[ -f "$JPG_FILE" ]]; then
        mark_headers_sent
        echo "Content-Type: image/jpeg"
        echo ""
        cat "$JPG_FILE"
        exit 0
    fi

    # Create thumbnail for HTML page
    thumb_root="${WORK_BASE}tn"
    pdf_to_thumb "$PDF_FILE" "$thumb_root"
fi

# ---------------------------------------------------------------------------
# HTML output (default): show program output and download links
# ---------------------------------------------------------------------------
mark_headers_sent
echo "Content-Type: text/html"
echo ""
cat <<HTMLEOF
<!DOCTYPE html>
<html>
<head><title>${title} Moon Tracker ${version} Results</title></head>
<body style="font-family:arial; font-size:medium">
<h1>${title} Moon Tracker ${version} Results</h1>
<p></p>
<pre>
${run_output}
</pre>
HTMLEOF

if [[ -f "$PS_FILE" ]]; then
    cat <<HTMLEOF
<hr/><b>Preview:</b><br/>
<a target="blank" href="${PDF_LINK}"><img src="${THUMB_LINK}"/></a><br/>
HTMLEOF

    if [[ -f "$PDF_FILE" ]]; then
        size="$(stat -c%s "$PDF_FILE" 2>/dev/null || stat -f%z "$PDF_FILE" 2>/dev/null || echo "?")"
        echo "<p>Click <a target=\"blank\" href=\"${PDF_LINK}\">here</a>"
        echo "to download diagram (PDF, ${size} bytes).</p>"
    fi
    if [[ -f "$JPG_FILE" ]]; then
        size="$(stat -c%s "$JPG_FILE" 2>/dev/null || stat -f%z "$JPG_FILE" 2>/dev/null || echo "?")"
        echo "<p>Click <a target=\"blank\" href=\"${JPG_LINK}\">here</a>"
        echo "to download diagram (JPEG format, ${size} bytes).</p>"
    fi
    size="$(stat -c%s "$PS_FILE" 2>/dev/null || stat -f%z "$PS_FILE" 2>/dev/null || echo "?")"
    echo "<p>Click <a target=\"blank\" href=\"${PS_LINK}\">here</a>"
    echo "to download diagram (PostScript format, ${size} bytes).</p>"

    if [[ -f "$TAB_FILE" ]]; then
        size="$(stat -c%s "$TAB_FILE" 2>/dev/null || stat -f%z "$TAB_FILE" 2>/dev/null || echo "?")"
        echo "<p>Click <a target=\"blank\" href=\"${TAB_LINK}\">here</a>"
        echo "to download table (ASCII format, ${size} bytes).</p>"
    fi
else
    echo "<p>No diagram generated.</p>"
fi

cat <<HTMLEOF
<hr/>
<a href="/tools/tracker3_${abbrev}.shtml">${title} Moon Tracker Form</a> |
<a href="/tools/index.html">RMS Node Tools</a> |
<a href="/">Ring-Moon Systems Home</a>
</body>
</html>
HTMLEOF
exit 0
