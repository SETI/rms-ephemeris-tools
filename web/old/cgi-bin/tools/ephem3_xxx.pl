#!/usr/bin/perl -w
no warnings 'once';

###############################
# General Ephemeris Generator #
###############################

require "/var/www/cgi-bin/tools/newcgi.pm";

get_params();

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
    print "<title>Ephemeris Generator $version Configuration Failure</title>\n";
    print "<body style=\"font-family:arial; font-size:medium\">\n";
    print "<h1>Ephemeris Generator $version Configuration Failure</h1>\n";
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
# ! Make a unique file name
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

$pid = $$;
$ephem_file = "$WWW_WORK/viewer3_" . $short . "_" . $pid . ".tab";

$ENV{"EPHEM_FILE"} = $ephem_file;

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ! Execute Viewer program
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

$ENV{"SPICEPATH"} = "/var/www/SPICE/";
$run = `/var/www/cgi-bin/tools/ephem3_xxx.bin`;

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ! Make sure the file exists
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

$exists = (-e $ephem_file);
if ($exists) {  # A file with nothing but a header line doesn't count
    open (fh, "<$ephem_file") || die "Could not open $ephem_file: $!";
    $ignore = <fh>;
    $exists = (1 - eof(fh));
    close(fh);
}

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ! Return the file alone if appropriate
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

if ($output eq "TAB" and $exists) {
    print "Content-Type: text/plain\n\n";
    open (fh, "<$ephem_file");
    @data = <fh>;
    print @data;
    close(fh);
    exit(0);
}

print "Content-Type: text/html\n\n";
print "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.01 Transitional//EN\">\n";
print "<html>\n";
print "<title>$title Ephemeris Generator $version Results</title>\n";
print "<body style=\"font-family:arial; font-size:medium\">\n";
print "<h1>$title Ephemeris Generator $version Results</h1>\n";
print "<p></p>\n";
print "<pre>\n";
print "$run";
print "</pre>\n";

if ($exists) {

    $ephem_link = "/work/viewer3_" . $short . "_" . $pid . ".tab";
    $size = (-s $ephem_file);
    print "<hr/>\n";
    print "Click <a href=\"$ephem_link\">here</a>\n";
    print "to download table (ASCII format, $size bytes).\n";
} else {
    print "Request failed.\n";
}

# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# ! End of page
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

# Summarize all symbols (for debugging)
#   print "<hr/><pre>\n";
#   print_env();
#   print "</pre>\n";

print "<hr/>\n";
print "<a href=\"/tools/ephem3_$abbrev.shtml\">$title Ephemeris Generator Form</a> |\n";
print "<a href=\"/tools/index.html\">RMS Node Tools</a> |\n";
print "<a href=\"/\">Ring-Moon Systems Home</a>\n";
print "</body>\n";
print "</html>\n";
exit(0);

