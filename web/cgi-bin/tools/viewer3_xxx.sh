#!/usr/bin/env bash
# viewer3_xxx.sh — CGI script for the Planet Viewer.
#
# Replaces the old Perl script viewer3_xxx.pl.
# Called by the HTML forms (VIEWER3_FORM_*.shtml via viewer3_*.shtml).
#
# The HTML form sends parameters including:
#   abbrev, version, output, time, fov, fov_unit,
#   center, center_body, center_ansa, center_ew, center_ra, center_dec,
#   center_ra_type, center_star,
#   viewpoint, observatory, latitude, longitude, lon_dir, altitude,
#   ephem, moons, rings, standard, additional, extra_ra, extra_ra_type,
#   extra_dec, extra_name, other (multi-valued),
#   title, labels, moonpts, blank, opacity, peris, peripts, meridians
#
# This script parses those parameters and calls:
#   ephemeris-tools viewer --planet <N> --time ... --fov ... [options]

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
version="$(cgi_get version "3.1")"
output="$(cgi_get output "HTML")"

short="${abbrev:0:3}"
extra="${abbrev:3}"

planet_num="$(abbrev_to_planet "$short")"
planet_name="$(abbrev_to_name "$short")"
if [[ -z "$planet_num" ]]; then
    html_error_page "Planet Viewer ${version} Configuration Failure"
fi

title="$(mission_title "$planet_name" "$extra")"

# ---------------------------------------------------------------------------
# Unique work files
# ---------------------------------------------------------------------------
make_work_paths "viewer3" "$short"

# ---------------------------------------------------------------------------
# Build CLI arguments
# ---------------------------------------------------------------------------
cli_args=( viewer --planet "$planet_num" )

# Observation time
obs_time="$(cgi_get time "")"
if [[ -n "$obs_time" ]]; then cli_args+=( --time "$obs_time" ); fi

# Field of view
fov="$(cgi_get fov "")"
fov_unit_raw="$(cgi_get fov_unit "")"
if [[ -n "$fov" ]]; then
    cli_args+=( --fov "$fov" )
fi

# Map the form's FOV units to CLI units
# Form values: "seconds of arc", "degrees", "milliradians", "microradians",
#              "<Planet> radii", "kilometers", "Voyager ISS wide angle FOVs", etc.
case "$fov_unit_raw" in
    *"seconds of arc"*)     cli_args+=( --fov-unit arcsec ) ;;
    *degree*)               cli_args+=( --fov-unit deg ) ;;
    # The Python CLI handles these via fov_unit string matching in viewer.py;
    # pass them through as-is for now (the CLI accepts the raw string)
    *)
        if [[ -n "$fov_unit_raw" ]]; then
            cli_args+=( --fov-unit "$fov_unit_raw" )
        fi
        ;;
esac

# Diagram center
center="$(cgi_get center "body")"
cli_args+=( --center "$center" )
case "$center" in
    body)
        center_body="$(cgi_get center_body "$planet_name")"
        cli_args+=( --center-body "$center_body" )
        ;;
    ansa)
        center_ansa="$(cgi_get center_ansa "A Ring")"
        center_ew="$(cgi_get center_ew "east")"
        cli_args+=( --center-ansa "$center_ansa" --center-ew "$center_ew" )
        ;;
    J2000)
        center_ra="$(cgi_get center_ra "")"
        center_dec="$(cgi_get center_dec "")"
        center_ra_type="$(cgi_get center_ra_type "hours")"
        if [[ -n "$center_ra" ]];  then cli_args+=( --center-ra "$center_ra" --center-ra-type "$center_ra_type" ); fi
        if [[ -n "$center_dec" ]]; then cli_args+=( --center-dec "$center_dec" ); fi
        ;;
    star)
        center_star="$(cgi_get center_star "")"
        if [[ -n "$center_star" ]]; then cli_args+=( --center-star "$center_star" ); fi
        ;;
esac

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

# Ephemeris version (numeric for SPICE; full string for Input Parameters display)
ephem_raw="$(cgi_get ephem "0")"
ephem_num="$(extract_id "$ephem_raw")"
cli_args+=( --ephem "$ephem_num" )
# Strip leading "NNN " for display (e.g. "000 NEP095 + ..." -> "NEP095 + ...")
ephem_display="${ephem_raw#* }"
if [[ -n "$ephem_display" ]]; then
    cli_args+=( --ephem-display "$ephem_display" )
fi

# Moon selection — viewer form uses radio buttons with values like
# "653 All inner moons (S1-S18,S32-S35,S49,S53)" or checkbox values
# like "001 Mimas (S1)".
# For the viewer, the form value format varies by planet:
#   Saturn viewer: radio "609 ...", "618 ...", "653 ..." → pass the number
#   Other planets: checkboxes "001 Io (J1)" etc. → pass individual IDs
moons_raw="$(cgi_get moons "")"
if [[ -n "$moons_raw" ]]; then
    # Pass raw value for Input Parameters display (e.g. "802 Triton & Nereid")
    cli_args+=( --moons-display "$moons_raw" )
    # Multi-valued moons (checkboxes)
    moons_list=()
    while IFS= read -r val; do
        [[ -z "$val" ]] && continue
        moons_list+=( "$(extract_id "$val")" )
    done < <(cgi_get_multi moons)
    if [[ ${#moons_list[@]} -gt 0 ]]; then
        cli_args+=( --moons "${moons_list[@]}" )
    fi
fi

# Ring selection — viewer form uses radio buttons with values like
# "A,B,C" or "A,B,C,F,G,E" (Saturn) or individual ring names.
# Pass raw to the viewer CLI which resolves names/codes.
rings_raw="$(cgi_get rings "")"
if [[ -n "$rings_raw" ]]; then
    # Pass raw value for Input Parameters display (e.g. "LeVerrier, Arago, Adams")
    cli_args+=( --rings-display "$rings_raw" )
    # Split comma-separated ring values into separate tokens
    IFS=',' read -ra ring_tokens <<< "$rings_raw"
    ring_args=()
    for tok in "${ring_tokens[@]}"; do
        tok="$(echo "$tok" | xargs)"  # trim whitespace
        if [[ -n "$tok" ]]; then ring_args+=( "$tok" ); fi
    done
    if [[ ${#ring_args[@]} -gt 0 ]]; then
        cli_args+=( --rings "${ring_args[@]}" )
    fi
fi

# Background objects
standard="$(cgi_get standard "")"
if [[ -n "$standard" ]]; then cli_args+=( --standard "$standard" ); fi

additional="$(cgi_get additional "")"
if [[ -n "$additional" ]]; then
    cli_args+=( --additional "$additional" )
    extra_name="$(cgi_get extra_name "")"
    extra_ra="$(cgi_get extra_ra "")"
    extra_ra_type="$(cgi_get extra_ra_type "hours")"
    extra_dec="$(cgi_get extra_dec "")"
    if [[ -n "$extra_name" ]]; then cli_args+=( --extra-name "$extra_name" ); fi
    if [[ -n "$extra_ra" ]];   then cli_args+=( --extra-ra "$extra_ra" --extra-ra-type "$extra_ra_type" ); fi
    if [[ -n "$extra_dec" ]];  then cli_args+=( --extra-dec "$extra_dec" ); fi
fi

# Other bodies (multi-valued checkboxes: Sun, Anti-Sun, Earth, spacecraft)
other_list=()
while IFS= read -r val; do
    [[ -z "$val" ]] && continue
    other_list+=( "$val" )
done < <(cgi_get_multi other)
if [[ ${#other_list[@]} -gt 0 ]]; then
    cli_args+=( --other "${other_list[@]}" )
fi

# Diagram options
plot_title="$(cgi_get title "")"
if [[ -n "$plot_title" ]]; then cli_args+=( --title "$plot_title" ); fi

labels="$(cgi_get labels "")"
if [[ -n "$labels" ]]; then cli_args+=( --labels "$labels" ); fi

moonpts="$(cgi_get moonpts "")"
if [[ -n "$moonpts" ]]; then cli_args+=( --moonpts "$moonpts" ); fi

blank="$(cgi_get blank "")"
if [[ -n "$blank" ]]; then cli_args+=( --blank "$blank" ); fi

opacity="$(cgi_get opacity "")"
if [[ -n "$opacity" ]]; then cli_args+=( --opacity "$opacity" ); fi

peris="$(cgi_get peris "")"
if [[ -n "$peris" ]]; then cli_args+=( --peris "$peris" ); fi

peripts="$(cgi_get peripts "")"
if [[ -n "$peripts" ]]; then cli_args+=( --peripts "$peripts" ); fi

meridians="$(cgi_get meridians "")"
if [[ -n "$meridians" ]]; then cli_args+=( --meridians "$meridians" ); fi

# Arc model and arc weight (Neptune)
arcmodel="$(cgi_get arcmodel "")"
if [[ -n "$arcmodel" ]]; then cli_args+=( --arcmodel "$arcmodel" ); fi
arcpts="$(cgi_get arcpts "")"
if [[ -n "$arcpts" ]]; then cli_args+=( --arcpts "$arcpts" ); fi

# Output files
cli_args+=( -o "$PS_FILE" )

# FOV table to text file too
cli_args+=( --output-txt "$TAB_FILE" )

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
<head><title>${title} Viewer ${version} Results</title></head>
<body style="font-family:arial; font-size:medium">
<h1>${title} Viewer ${version} Results</h1>
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
else
    echo "<p>No diagram generated.</p>"
fi

cat <<HTMLEOF
<hr/>
<a href="/tools/viewer3_${abbrev}.shtml">${title} Viewer Form</a> |
<a href="/tools/index.html">RMS Node Tools</a> |
<a href="/">Ring-Moon Systems Home</a>
</body>
</html>
HTMLEOF
exit 0
