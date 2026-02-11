ephem_tools_unit_tests.py contains the Ephemeris Tools Unit Tests.

These tests can perform two operations: the creation and storage of
"golden copies", and the comparison of current results against these golden
copy counterparts.

When no command-line arguments are given, this program will compare all three
tools (the Planet Viewer tool, the Moon Tracker tool, and the Ephemeris
Generator tool) in their current state on the production server to their
counterparts stored in the golden copies directory, reporting the results in
a log file.

The following command-line arguments are available:

--run-ephemeris-type: Takes 'test' or 'current' for either the test ephemeris
mode or the current ephemeris mode. SPICE kernels are frequently updated
on the tool servers. Changes in kernels may result in small changes in
tool output that does not indicate an actual bug in the tool. To solve this,
we provide the ability to use a "frozen" set of SPICE kernels so that test
results will not be affected by updates to the kernels. To select this frozen
set of kernels, use the 'test' mode. To select the most recent SPICE kernels
installed on the server, use the 'current' mode.

--replace_golden_copies: Switches to replacement mode, which will replace 
the golden copies of the specified tools (or all three by default). Use 
--test-file-paths to specify which tools to generate golden copies for. All 
golden copies are generated from the staging server.

--test-file-paths [filename ...]: Specifies the files containing the test URLs.
If not specified, the three default filenames (test_files/viewer-unit-tests.txt,
test_files/moon-tracker-unit-tests.txt, and
test_files/ephemeris-generator-unit-tests.txt) will be used.
If this option is specified, only the filenames specified will be used.

--golden-directory: Specifies the directory in which the golden copies are
stored. The default is "golden_copies" inside the current directory.

--limit-tests: Takes a range of tests separated by a colon (1:10 for the
first ten tests, for example). If this command is used, you must use
--tests-file-paths on the tool you wish to pull the subset from. This will
work on all tests determined by --test-file-paths.

--server: Server takes a keyword or a host name to determine which server to 
generate the test files from. If ‘staging’, ‘production’, ‘server1’ or 
‘server2’ are chosen, it will generate test files from these servers. If you 
wish to use a server that is not included in this list, you may either use the
host name or a URL prefix containing the server's name.

--logfile-filename: Takes a string that specifies the filename of the logfile.
The default is year_month_day_hour_minute_second.log

--save-failing-tests: Takes any tests that fail the comparison check
and puts them into a 'failed_tests' directory for later reference.

--hide-known-failures: Allows the user to exclude log messages for tests that
are known to fail. Takes one or more range of tests separated by a colon (1:10,
for example). This will work on all tests determined by --test-file-paths.

The 'golden copy' generation (invoked by the --replace option) takes the test
files and runs them on the staging server. Each test URL is run multiple times
to include all available outputs for that tool (HTML, PostScript, and tabular
files). The results are stored in the golden_copies directory. This feature
can either be run to replace old golden copies, or to generate new ones in a
new directory.

The comparison feature generates files from a requested server utilizing the
same method of generation as the golden files. The new version and the golden
copy are matched via hex name and cleaned of contents that are constant between
versions or are expected to change but have no impact on the final result. The
two cleaned files are then compared against one another in search of
discrepancy. The match results of all the files are noted in the logfile.