#!/usr/bin/perl -w
no warnings 'once';

########################
# General Moon Tracker #
########################

require "/var/www/cgi-bin/tools/newcgi.pm";

get_params();

$is_mac = ($ENV{"CONTEXT_DOCUMENT_ROOT"} eq "/Library/WebServer/CGI-Executables/");

$abbrev = lc($ENV{"abbrev"});
$version = $ENV{"version"};
$output = $ENV{"output"};

$short  = substr($abbrev,0,3);
$extra  = substr($abbrev,3);

if ($short eq "mar") {
    $planet = "Mars";
    $ENV{"NPLANET"} = "4";
}
elsif ($short eq "jup") {
    $planet = "Jupiter";
    $ENV{"NPLANET"} = "5";
}
elsif ($short eq "sat") {
    $planet = "Saturn";
    $ENV{"NPLANET"} = "6";
}
elsif ($short eq "ura") {
    $planet = "Uranus";
    $ENV{"NPLANET"} = "7";
}
elsif ($short eq "nep") {
    $planet = "Neptune";
    $ENV{"NPLANET"} = "8";
}
elsif ($short eq "plu") {
    $planet = "Pluto";
    $ENV{"NPLANET"} = "9";
}
else {
    print "Content-Type: text/html\n\n";
    print "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\">\n";
    print "<html>\n";
    print "<title>Moon Tracker $version Configuration Failure</title>\n";
    print "<body style=\"font-family:arial; font-size:medium\">\n";
    print "<h1>Moon Tracker $version Configuration Failure</h1>\n";
    print "<p>\n";
    print "Please report this error to the RMS website administrator,\n";
    print "<a href=\"mailto:pds-admin\@seti.org\">pds-admin\@seti.org</a></p>\n";
    print "</body>\n";
    print "</html>\n";
    exit(0);
}

if ($extra eq "c") {
    $title = "Cassini/$planet";
}
elsif ($extra eq "j") {
    $title = "Juno/$planet";
}
elsif ($extra eq "nh") {
    $title = "New Horizons/$planet";
}
elsif ($extra eq "ec") {
    $title = "Europa Clipper/$planet";
}
elsif ($extra eq "jc") {
    $title = "JUICE/$planet";
}
else {
    $title = $planet;
}

$WWW_WORK = "/var/www/work";

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ! Make a unique set of file names
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

$pid = $$;
$ps_file    = "$WWW_WORK/tracker3_" . $short . "_" . $pid . ".ps";
$pdf_file   = "$WWW_WORK/tracker3_" . $short . "_" . $pid . ".pdf";
$jpg_root   = "$WWW_WORK/tracker3_" . $short . "_" . $pid;
$thumb_root = "$WWW_WORK/tracker3_" . $short . "_" . $pid . "tn";
$jpg_file   = "$WWW_WORK/tracker3_" . $short . "_" . $pid . ".jpg";
$thumb_file = "$WWW_WORK/tracker3_" . $short . "_" . $pid . "tn.jpg";
$tab_file   = "$WWW_WORK/tracker3_" . $short . "_" . $pid . ".tab";

$ENV{"TRACKER_POSTFILE"} = $ps_file;
$ENV{"TRACKER_TEXTFILE"} = $tab_file;

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ! Execute Tracker program
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

$ENV{"SPICEPATH"} = "/var/www/SPICE/";
$run = `/var/www/cgi-bin/tools/tracker3_xxx.bin`;

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ! Return the result
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

$exists = (-e $ps_file);
if ($exists) {

    if ($output eq "PS") {
        open (FH, "<$ps_file") || die "Could not open $ps_file: $!";
        @data = <FH>;
        print "Content-type: application/postscript\n\n";
        print @data;
        close(FH);
        exit 0;
    }

    if ($output eq "TAB") {
        open (FH, "<$tab_file") || die "Could not open $tab_file: $!";
        @data = <FH>;
        print "Content-type: text/plain\n\n";
        print @data;
        close(FH);
        exit 0;
    }

    # Create PDF file
    if ($is_mac) {
        $ignore = `/usr/local/bin/gs -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile=$pdf_file $ps_file`;
    } else {
        $ignore = `/usr/bin/gs -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -sOutputFile=$pdf_file $ps_file`;
    }

    if ($output eq "PDF") {
        open (FH, "<$pdf_file") || die "Could not open $pdf_file: $!";
        @data = <FH>;
        print "Content-type: application/pdf\n\n";
        print @data;
        close(FH);
        exit 0;
    }

    # Create JPEG file
    if ($is_mac) {
        $ignore = `/usr/bin/sips -s format jpeg $pdf_file --out $jpg_file`;
    } else {
        $ignore = `/usr/bin/pdftoppm -jpeg -singlefile $pdf_file $jpg_root`;
    }

    if ($output eq "JPEG") {
        open (FH, "<$jpg_file") || die "Could not open $jpg_file: $!";
        @data = <FH>;
        print "Content-type: image/jpeg\n\n";
        print @data;
        close(FH);
        exit 0;
    }

    if ($is_mac) {
        $ignore = `/usr/bin/sips -s format jpeg -Z 396 $pdf_file --out $thumb_file`;
    } else {
        $ignore = `/usr/bin/pdftoppm -jpeg -singlefile -r 36 $pdf_file $thumb_root`;
    }
}

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ! Otherwise, construct the webpage
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

print "Content-Type: text/html\n\n";
print "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\">\n";
print "<html>\n";
print "<title>$title Moon Tracker $version Results</title>\n";
print "<body style=\"font-family:arial; font-size:medium\">\n";
print "<h1>$title Moon Tracker $version Results</h1>\n";
print "<p></p>\n";
print "<pre>\n";
print "$run";
print "</pre>\n";

if ($exists) {
    $ps_link    = "/work/tracker3_" . $short . "_" . $pid . ".ps";
    $pdf_link   = "/work/tracker3_" . $short . "_" . $pid . ".pdf";
    $jpg_link   = "/work/tracker3_" . $short . "_" . $pid . ".jpg";
    $thumb_link = "/work/tracker3_" . $short . "_" . $pid . "tn.jpg";
    $tab_link   = "/work/tracker3_" . $short . "_" . $pid . ".tab";

    print "<hr/><b>Preview:</b><br/>\n";
    print "<a target=\"blank\" href=\"$pdf_link\"><image src=\"$thumb_link\"/></a><br/>\n";

    $size = (-s $pdf_file);
    print "<p>Click <a target=\"blank\" href=\"$pdf_link\">here</a>\n";
    print "to download diagram (PDF, $size bytes).</p>\n";

    $size = (-s $jpg_file);
    print "<p>Click <a target=\"blank\" href=\"$jpg_link\">here</a>\n";
    print "to download diagram (JPEG format, $size bytes).</p>\n";

    $size = (-s $ps_file);
    print "<p>Click <a target=\"blank\" href=\"$ps_link\">here</a>\n";
    print "to download diagram (PostScript format, $size bytes).</p>\n";

    $size = (-s $tab_file);
    print "<p>Click <a target=\"blank\" href=\"$tab_link\">here</a>\n";
    print "to download table (ASCII format, $size bytes).</p>\n";
}
else {
    print "<p>No diagram generated.</p>\n";
}

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ! End of page
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# Summarize all symbols (for debugging)
#   print "<hr/><pre>\n";
#   print_env();
#   print "</pre>\n";

print "<hr/>\n";
print "<a href=\"/tools/tracker3_$abbrev.shtml\">$title Moon Tracker Form</a> |\n";
print "<a href=\"/tools/index.html\">RMS Node Tools</a> |\n";
print "<a href=\"/\">Ring-Moon Systems Home</a>\n";
print "</body>\n";
print "</html>\n";
exit(0);
