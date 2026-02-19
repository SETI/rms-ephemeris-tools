#!/usr/bin/env bash
# CGI wrapper: match output of web/old/cgi-bin/tools/viewer3_xxx.pl exactly.
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
    printf '<title>Planet Viewer %s Configuration Failure</title>\n' "$version"
    printf '<body style="font-family:arial; font-size:medium">\n'
    printf '<h1>Planet Viewer %s Configuration Failure</h1>\n' "$version"
    printf '<p>\n'
    printf 'Please report this error to the RMS website administrator,\n'
    printf '<a href="mailto:pds-admin@seti.org">pds-admin@seti.org</a></p>\n'
    printf '</body>\n'
    printf '</html>\n'
    exit 0
fi

# Env "title" is left as-is from query string so Python uses it for the diagram only.
# HTML page title/heading always use planet name (e.g. "Uranus Viewer 3.1").
page_title="$(mission_title "$(abbrev_to_name "$short")" "${abbrev:3}")"
make_work_paths "viewer3" "$short"

export NPLANET="$planet_num"
export VIEWER_POSTFILE="$PS_FILE"
export SPICEPATH="${SPICEPATH:-/var/www/SPICE/}"
export REQUEST_METHOD="${REQUEST_METHOD:-GET}"

run_out=$(mktemp)
trap 'rm -f "$run_out"; cgi_error_trap' EXIT
"$PYTHON" -m ephemeris_tools.cli.main viewer --cgi > "$run_out"

exists=0
[[ -f "$PS_FILE" ]] && exists=1

if [[ $exists -eq 1 ]]; then
    if [[ "$output" == "PS" ]]; then
        mark_headers_sent
        printf 'Content-type: application/postscript\n\n'
        cat "$PS_FILE"
        exit 0
    fi

    "$GS" -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile="$PDF_FILE" "$PS_FILE" >/dev/null 2>&1 || true

    if [[ "$output" == "PDF" ]]; then
        mark_headers_sent
        printf 'Content-type: application/pdf\n\n'
        cat "$PDF_FILE"
        exit 0
    fi

    "$PDFTOPPM" -jpeg -singlefile "$PDF_FILE" "${WORK_BASE}" >/dev/null 2>&1 || true
    [[ -f "${WORK_BASE}-1.jpg" ]] && mv "${WORK_BASE}-1.jpg" "$JPG_FILE"

    if [[ "$output" == "JPEG" ]]; then
        mark_headers_sent
        printf 'Content-type: image/jpeg\n\n'
        cat "$JPG_FILE" 2>/dev/null || true
        exit 0
    fi

    "$PDFTOPPM" -jpeg -singlefile -r 36 "$PDF_FILE" "${WORK_BASE}tn" >/dev/null 2>&1 || true
    [[ -f "${WORK_BASE}tn-1.jpg" ]] && mv "${WORK_BASE}tn-1.jpg" "$THUMB_FILE"
fi

mark_headers_sent
printf 'Content-Type: text/html\n\n'
printf '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">\n'
printf '<html>\n'
printf '<title>%s Viewer %s Results</title>\n' "$page_title" "$version"
printf '<body style="font-family:arial; font-size:medium">\n'
printf '<h1>%s Viewer %s Results</h1>\n' "$page_title" "$version"
printf '<p></p>\n'
printf '<pre>\n'
cat "$run_out"
printf '</pre>\n'

if [[ $exists -eq 1 ]]; then
    printf '<hr/><b>Preview:</b><br/>\n'
    printf '<a target="blank" href="%s"><image src="%s"/></a><br/>\n' "$PDF_LINK" "$THUMB_LINK"
    size=$(stat -c%s "$PDF_FILE" 2>/dev/null || stat -f%z "$PDF_FILE" 2>/dev/null)
    printf '<p>Click <a target="blank" href="%s">here</a>\n' "$PDF_LINK"
    printf 'to download diagram (PDF, %s bytes).</p>\n' "$size"
    size=$(stat -c%s "$JPG_FILE" 2>/dev/null || stat -f%z "$JPG_FILE" 2>/dev/null)
    printf '<p>Click <a target="blank" href="%s">here</a>\n' "$JPG_LINK"
    printf 'to download diagram (JPEG format, %s bytes).</p>\n' "$size"
    size=$(stat -c%s "$PS_FILE" 2>/dev/null || stat -f%z "$PS_FILE" 2>/dev/null)
    printf '<p>Click <a target="blank" href="%s">here</a>\n' "$PS_LINK"
    printf 'to download diagram (PostScript format, %s bytes).</p>\n' "$size"
else
    printf '<p>No diagram generated.</p>\n'
fi

printf '<hr/>\n'
printf '<a href="/tools/viewer3_%s.shtml">%s Viewer Form</a> |\n' "$abbrev" "$page_title"
printf '<a href="/tools/index.html">RMS Node Tools</a> |\n'
printf '<a href="/">Ring-Moon Systems Home</a>\n'
printf '</body>\n'
printf '</html>\n'
exit 0
