"""Contains the Ephemeris Tools Unit Tests."""
import argparse
from datetime import datetime
import logging
import os
import re
import requests
import sys
import urllib3
import uuid
import warnings


def compare_tests_against_golden(ephem, test_files, subtests, store_failures,
                                 known_failures, golden_location, server):
    """Compare test versions to golden copies of chosen tools.

    This function takes arguments for the ephemeris type ("current" or "test"),
    the paths to the tool test files you choose to compare, the range of tests
    within the tool test file, the range(s) of known failing tests to be
    excluded from the log, the path to the directory containing the golden
    copies, and the server from which you want to pull the test versions.
    A quality check is in place that ensures that test URLs generate HTML
    files before modifying the tests to create PostScript or TAB files; an
    error is thrown if an original test does not end with 'output=HTML'. The
    correct tools are generated, cleaned, then matched against their golden
    copy versions. Returns the results in the generated log file.
    """
    warnings.simplefilter('ignore', urllib3.exceptions.InsecureRequestWarning)
    tests_final = []

    for test_file in test_files:
        try:
            with open(test_file, 'r') as test_urls:
                test_urls = test_urls.readlines()
        except FileNotFoundError:
            logging.error(f'The {test_file} test file does not exist')
            print(f'A {test_file} test file does not exist')
            sys.exit(1)

        if 'viewer3' in test_urls[0]:
            viewer_urls = [url.strip() for url in test_urls]
            viewer_urls = [url.strip('https://staging.pds.seti.org/')
                           for url in viewer_urls]

            for url in viewer_urls:
                if not url.endswith('&output=HTML'):
                    # This check for HTML within the URLs is necessary to ensure
                    # that all tests will function as expected. If tests are
                    # derived from a format other than HTML, this program will
                    # end and return a logged error.
                    logging.error(f'The URL {url} within the planet viewer '
                                   'tool tests does not end with '
                                   '"&output=HTML".')
                    sys.exit(1)

            viewer_indices_ps = []

            for url in viewer_urls:
                tests_final.append(url)
                ps_url = url.replace('&output=HTML', '&output=PS')
                viewer_indices_ps.append(ps_url)
                tests_final.append(ps_url)

        if 'tracker3' in test_urls[0]:
            tracker_urls = [url.strip() for url in test_urls]
            tracker_urls = [url.strip('https://staging.pds.seti.org/')
                            for url in tracker_urls]

            for url in tracker_urls:
                if not url.endswith('&output=HTML'):
                    # This check for HTML within the URLs is necessary to ensure
                    # that all tests will function as expected. If tests are
                    # derived from a format other than HTML, this program will
                    # end and return a logged error.
                    logging.error(f'The URL {url} within the moon tracker tool '
                                   'tests does not end with "&output=HTML".')
                    sys.exit(1)

            # TAB files are currently paused until the tabular format
            # bug is fixed. See https://github.com/SETI/pds-webserver/issues/39

            tracker_indices_ps = []
            tracker_indices_tab = []

            for url in tracker_urls:
                tests_final.append(url)
                ps_url = url.replace('&output=HTML', '&output=PS')
                tracker_indices_ps.append(ps_url)
                tests_final.append(ps_url)
                tab_url = url.replace('&output=HTML', '&output=TAB')
                tracker_indices_tab.append(tab_url)
                tests_final.append(tab_url)

        if 'ephem3' in test_urls[0]:
            ephemeris_urls = [url.strip() for url in test_urls]
            ephemeris_urls = [url.strip('https://staging.pds.seti.org/')
                              for url in ephemeris_urls]

            for url in ephemeris_urls:
                if not url.endswith('&output=HTML'):
                    # This check for HTML within the URLs is necessary to ensure
                    # that all tests will function as expected. If tests are
                    # derived from a format other than HTML, this program will
                    # end and return a logged error.
                    logging.error(f'The URL {url} within the ephemeris tool '
                                   'tests does not end with "&output=HTML".')
                    sys.exit(1)

            ephemeris_indices_tab = []

            for url in ephemeris_urls:
                tests_final.append(url)
                tab_url = url.replace('&output=HTML', '&output=TAB')
                ephemeris_indices_tab.append(tab_url)
                tests_final.append(tab_url)

    logging.info(f'Using server: {server}')

    # Having a file_type variable ensures that the golden copy counterpart will
    # be cleaned with the correct cleaning code. Since the golden copy will
    # always be the same file type as the test copy, they will use the same
    # cleaning code.
    file_type = None
    tool_type = None

    logging.info('Beginning test file vs. golden copy comparison')

    if ephem == 'test':
        suffix = '&ephem=+-1+TEST&sc_trajectory=+-1+TEST'
    else:
        assert ephem == 'current'
        suffix = ''

    for test in tests_final:
        if 'viewer3' in test:
            tool_type = 'Planet Viewer test'
            if 'output=HTML' in test:
                index = viewer_urls.index(test) + 1
            else:
                assert 'output=PS' in test
                index = viewer_indices_ps.index(test) + 1

        if 'tracker3' in test:
            tool_type = 'Moon Tracker test'
            if 'output=HTML' in test:
                index = tracker_urls.index(test) + 1
            elif 'output=PS' in test:
                index = tracker_indices_ps.index(test) + 1
            else:
                assert 'output=TAB' in test
                index = tracker_indices_tab.index(test) + 1

        if 'ephem3' in test:
            tool_type = 'Ephemeris Generator test'
            if 'output=HTML' in test:
                index = ephemeris_urls.index(test) + 1
            else:
                assert 'output=TAB' in test
                index = ephemeris_indices_tab.index(test) + 1

        name = str(uuid.uuid5(uuid.NAMESPACE_URL, test))
        test = server + test + suffix

        if (subtests is not None and index in subtests) or (subtests is None):
            # This try/except that wraps this exception catching block is
            # required in order to exit the program without extraneous error
            # messages. os._exit(1) is not an option since it does not allow
            # for any printed error messages, instead restarting the kernel
            # and exiting the program without cleanup.
            try:
                try:
                    content = (requests.get(test, timeout=5.0, verify=False)
                               .content)
                except requests.exceptions.ConnectionError:
                    logging.error(f'Failed to connect to server {server} with '
                                  f'URL {test}')
                    print(f'Failed to connect to server {server} with '
                          f'URL {test}')
                    sys.exit(1)
                except requests.exceptions.ReadTimeout:
                    logging.error( 'Server timeout while attempting to '
                                  f'retrieve {test} corresponding to the '
                                  f'{tool_type} at line {index}')
                    print( 'Server timeout while attempting to '
                          f'retrieve {test} corresponding to the '
                          f'{tool_type} at line {index}')
                    sys.exit(1)
            except SystemExit:
                sys.exit(0)
        else:
            continue

        content = content.decode('utf8')
        if 'output=HTML' in test:
            test_version = html_file_cleaner(ephem, content)
            file_type = 'HTML'
        elif 'output=PS' in test:
            test_version = ps_file_cleaner(ephem, content)
            file_type = 'PS'
        else:
            assert 'output=TAB' in test
            test_version = tab_file_cleaner(ephem, content)
            file_type = 'TAB'

        try:
            with open(os.path.join(golden_location, name), 'r') as file:
                golden_file = file.read()
        except FileNotFoundError:
            logging.error(f'Filename {name} not found within {golden_location}')
            print(f'Golden directory {golden_location} does not contain '
                  f'the file {name}')
            sys.exit(1)

        if file_type == 'HTML':
            golden_version = html_file_cleaner(ephem, golden_file)
        elif file_type == 'PS':
            golden_version = ps_file_cleaner(ephem, golden_file)
        else:
            assert file_type == 'TAB'
            golden_version = tab_file_cleaner(ephem, golden_file)

        if golden_version != test_version:
            if known_failures is not None and index in known_failures:
                logging.warning(f'{file_type} {tool_type} {name} located at '
                                f'line {index} does not match - known failure '
                                 'skipped')
            else:
                logging.error(f'{file_type} {tool_type} {name} located at line '
                              f'{index} does not match. Test URL: {test}')
            if store_failures:
                with open(os.path.join('failed_tests', name), 'w') as failed:
                    failed.write(content)
        else:
            logging.info(f'{file_type} {tool_type} {name} at '
                         f'line {index} matches')


def html_file_cleaner(ephem, raw_content):
    """Clean HTML products of all material that is negligible between tests.

    Parameters are the chosen ephemeris type and content of a file
    generated from the test URL. This cleaning code covers all three tools.
    The return value is the cleaned version of the input string.
    """
    clean = re.sub('/></a><br/>',
                   '',
                   raw_content)
    clean = re.sub(r'<title>'
                   r'(Jupiter|Saturn|Uranus|Neptune|Pluto|Mars) '
                   r'(Viewer|Moon Tracker|Ephemeris Generator) \d.\d '
                   r'Results</title>',
                   '',
                   clean)
    clean = re.sub(r'<h1>(Jupiter|Saturn|Uranus|Neptune|Pluto|Mars) '
                   r'(Viewer|Moon Tracker|Ephemeris Generator) \d.\d '
                   r'Results</h1>',
                   '',
                   clean)
    clean = re.sub(r'<a target="blank" href="'
                   r'/work/(viewer|tracker|ephem)\d_'
                   r'(jup|sat|ura|nep|plu|mar)_\d{1,15}.pdf"><image '
                   r'src="/work/(viewer|tracker|ephem)\d_'
                   r'(jup|sat|ura|nep|plu|mar)_'
                   r'\d{1,10}tn.jpg"',
                   '',
                   clean)
    clean = re.sub(r'<a target="blank" href="/work/'
                   r'(viewer|tracker|ephem)\d_'
                   r'(jup|sat|ura|nep|plu|mar)_\d{1,15}.pdf\'><image '
                   r'src="/work/(viewer|tracker|ephem)\d_'
                   r'(jup|sat|ura|nep|plu|mar)_\d{1,10}tn.jpg"',
                   '',
                   clean)
    clean = re.sub(r'<p>Click <a target="blank" href="/work/'
                   r'(viewer|tracker|ephem)3_'
                   r'(jup|sat|ura|nep|plu|mar)_'
                   r'\d{1,15}.pdf">here</a>',
                   '',
                   clean)
    clean = re.sub(r'to download diagram \(PDF, \d{1,15} bytes\).</p>',
                   '',
                   clean)
    clean = re.sub(r'<p>Click <a target="blank" href="/work/'
                   r'(viewer|tracker|ephem)\d_'
                   r'(jup|sat|ura|nep|plu|mar)_'
                   r'(\d{1,15}|\d{1,15}\w).jpg">here</a>',
                   '',
                   clean)
    clean = re.sub(r'to download diagram \(JPEG format, '
                   r'\d{1,15} bytes\).</p>',
                   '',
                   clean)
    clean = re.sub(r'<p>Click <a target="blank" href="/work'
                   r'/(viewer|tracker|ephem)\d_'
                   r'(jup|sat|ura|nep|plu|mar)_'
                   r'\d{1,15}.ps">here</a>',
                   '',
                   clean)
    clean = re.sub(r'to download diagram \(PostScript format, \d{1,15} '
                   r'bytes\).</p>',
                   '',
                   clean)
    clean = re.sub(r'<p>Click <a target="blank" href="/work/'
                   r'(viewer|tracker|ephem)\d_'
                   r'(jup|sat|ura|nep|plu|mar)_'
                   r'\d{1,15}.tab">here</a>',
                   '',
                   clean)
    clean = re.sub(r'to download table \(ASCII format, '
                   r'\d{1,15} bytes\).</p>',
                   '',
                   clean)
    clean = re.sub(r'Click <a href="/work/(ephem|viewer)\d_'
                   r'(jup|sat|ura|nep|plu|mar)_\d{1,15}.tab">here</a>',
                   '',
                   clean)
    clean = re.sub(r'to download table \(ASCII format, '
                   r'\d{1,15} bytes\).',
                   '',
                   clean)
    if ephem == 'test':
        clean = re.sub(r'Ephemeris: .+',
                       '',
                       clean)
        clean = re.sub(r'Viewpoint: .+',
                       '',
                       clean)
    clean = re.sub(r'<a href=\'/tools/(viewer|tracker|ephem)'
                   r'\d_\w(jup|sat|ura|nep|plu|mar).shtml\'>'
                   r'(Jupiter|Saturn|Uranus|Neptune|Pluto|Mars) '
                   r'(Viewer|Moon Tracker|Ephemeris Generator) '
                   r'Form</a> \|',
                   '',
                   clean)

    return clean


def ps_file_cleaner(ephem, raw_content):
    """Clean PostScript products of negligible material between tests.

    Parameters are the chosen ephemeris mode and the UTF-8 content of a file
    generated from the test URL. This cleaning code covers all three tools.
    The return value is the cleaned version of the string.
    """
    clean = re.sub(r'\(Generated by .+\)', '', raw_content)
    if ephem == 'test':
        clean = re.sub(r'\((JUP|SAT|URA|NEP|PLU|MAR).+[0-9]\)',
                       '',
                       clean)
        clean = re.sub(r' \\\(TEST\\\)',
                       '',
                       clean)
        clean = re.sub(r'\(TEST\)',
                       '',
                       clean)
    clean = re.sub(r'%%Title: (viewer|tracker)\d_'
                   r'(jup|sat|ura|nep|plu|mar)_\d{1,10}.ps',
                   '',
                   clean)

    return clean


def tab_file_cleaner(ephem, raw_content):
    """Clean TAB products of negligible material between tests.

    Parameters are the chosen ephemeris mode and the UTF-8 content of a file
    generated from the test URL. This cleaning code covers all three tools.
    The return value is the cleaned version of the string.
    """
    # This removes the server name from a 500 Internal Server Error
    clean = re.sub(r'<address>(.+)</address>', '', raw_content)

    return clean


def replace_golden_copies(ephem, test_files, subtests, golden_copies_path):
    """Replace golden copies of tests within a chosen directory.

    Parameters are the test files according to args.test_file_paths. For each
    URL within those tests, the URLs are generated and saved as multiple
    filetypes according to the tool the URL test originates from. These files
    are saved within the golden_copies_location path.
    """
    for test_file in test_files:

        with open(test_file, 'r') as test_urls:
            test_urls = test_urls.readlines()
            test_urls = [url.strip() for url in test_urls]
            test_urls = [url.strip('https://staging.pds.seti.org/')
                              for url in test_urls]

        for url in test_urls:
            if not url.endswith('&output=HTML'):
                # This check for HTML within the URLs is necessary to ensure
                # that all tests will function as expected. If tests are
                # derived from a format other than HTML, this program will
                # end and return a logged error.
                logging.error('A URL within the test file does not end with '
                              '"&output=HTML"')
                sys.exit(1)

        logging.info('Test file is properly formatted')


        if 'viewer3' in test_urls[0]:
            ps_versions = []
            all_urls = list(test_urls)
            number_of_base_tests = str(len(test_urls))
            logging.info( 'Golden copies of the Planet Viewer Tool requested. '
                         f'Now generating {number_of_base_tests} HTML file '
                          'versions.')

            logging.info( 'HTML test versions generated. Now generating '
                         f'{number_of_base_tests} PostScript file versions.')

            for url in test_urls:
                url = url.replace('output=HTML', 'output=PS')
                ps_versions.append(url)
                all_urls.append(url)

        elif 'tracker3' in test_urls[0]:
            ps_versions = []
            tab_versions = []
            all_urls = list(test_urls[:])
            number_of_base_tests = len(all_urls)
            logging.info( 'Golden copies of the Moon Tracker Tool requested. '
                         f'Now generating {number_of_base_tests} golden '
                          'copies.')

            logging.info( 'HTML test versions generated. Now generating '
                         f'{number_of_base_tests} PostScript file versions.')
            for url in test_urls:
                url = url.replace('output=HTML', 'output=PS')
                ps_versions.append(url)
                all_urls.append(url)

            logging.info( 'Postscript test versions generated. Now generating '
                         f'{number_of_base_tests} TAB file versions.')
            for url in test_urls:
                url = url.replace('output=HTML', 'output=TAB')
                tab_versions.append(url)
                all_urls.append(url)

        else:
            assert 'ephem3' in test_urls[0]
            tab_versions = []
            all_urls = test_urls[:]
            number_of_base_tests = str(len(all_urls))
            logging.info( 'Golden copies of the Ephemeris Generator Tool '
                         f'requested. Now generating {number_of_base_tests} '
                          'golden copies.')

            logging.info( 'HTML test versions generated. Now generating '
                         f'{number_of_base_tests} TAB file versions.')
            for url in test_urls:
                url = url.replace('output=HTML', 'output=TAB')
                tab_versions.append(url)
                all_urls.append(url)


        for file in all_urls:
            if file.endswith('&output=HTML'):
                index = list(test_urls).index(file) + 1
            elif file.endswith('&output=PS'):
                index = ps_versions.index(file) + 1
            else:
                assert 'output=TAB' in file
                index = tab_versions.index(file) + 1

            if (subtests is not None
                and index in subtests) or (subtests is None):
                if ephem == 'test':
                    file += '&ephem=+-1+TEST&sc_trajectory=+-1+TEST'
                name = str(uuid.uuid5(uuid.NAMESPACE_URL, file))
                file = 'https://staging.pds.seti.org/' + file
                grab = requests.get(file, verify=False)
                content = grab.content
                content = content.decode('utf8')
                with open(os.path.join(golden_copies_path,
                                       name), 'w') as goldfile:
                    goldfile.write(content)
                    logging.info(f'File {name} at line {index} generated')

def range_of_tests(selected_tests):
    """Create set of indices for limiting tests or hiding known failures."""
    subtests = None
    if selected_tests is not None:
        subtests = set()
        for set_of_tests in selected_tests:
            set_of_tests = set_of_tests.split(':')
            if set_of_tests[0] == set_of_tests[-1]:
                subtests.add(int(set_of_tests[0]))
            else:
                subtests.update(range(int(set_of_tests[0]),
                                      int(set_of_tests[-1]) + 1))

    return subtests

def select_server(server):
    """Determine which server to use in tests."""
    if server == 'staging':
        selected_server = 'https://staging.pds.seti.org/'
    elif server == 'production':
        selected_server = 'https://pds-rings.seti.org/'
    elif server == 'server1':
        selected_server = 'https://server1.pds-rings.seti.org/'
    elif server == 'server2':
        selected_server = 'https://server2.pds-rings.seti.org/'
    else:
        selected_server = server
        if not selected_server.startswith('http'):
            selected_server = 'https://' + selected_server
        if not selected_server.endswith('/'):
            selected_server = selected_server + '/'

    return selected_server


warnings.simplefilter('ignore', urllib3.exceptions.InsecureRequestWarning)
logging.getLogger('urllib3').setLevel(logging.WARNING)

parser = argparse.ArgumentParser()
parser.add_argument('--run-ephemeris-type', type=str, choices=['test',
                                                               'current'],
                    default='current',
                    help='Select which SPICE kernels are being used on '
                         'the server. The "test" type will use the most recent '
                         'defaults. The "current" type will use what is '
                         'available on the chosen server. The default is '
                         '"current".')

parser.add_argument('--replace', action='store_true', default=False,
                    help='Replace stored versions of chosen ephemeris '
                         'tools. All versions stored are generated from the '
                         'current staging server.')

parser.add_argument('--test-file-paths', type=str, nargs='+',
                    default=[os.path.join('test_files',
                                          'viewer-unit-tests.txt'),
                             os.path.join('test_files',
                                          'moon-tracker-unit-tests.txt'),
                             os.path.join('test_files',
                                          'ephemeris-generator-unit-tests.txt')
                             ],
                    help='The files containing the URLs to test, one per tool.')

parser.add_argument('--golden-directory', type=str,
                    default='golden_copies',
                    help='Path to the directory containing the golden copies.')

parser.add_argument('--limit-tests', action='store',
                    nargs='+',
                    help='The indices to specify which subset of tests to run '
                         'within a set of URL tests. Use the format '
                         '"start:end". Refer to the indices within the log '
                         'file to determine which tests to rerun. Only one '
                         'test file can be specified to use this command.')

parser.set_defaults(testsubset=None)

parser.add_argument('--server', type=str, default='production',
                    help='The server you wish to generate the current tests '
                         'for comparison. If you choose "other", please enter '
                         'the URL prefix for the server you wish to use.')

parser.add_argument('--logfile-filename', type=str,
                    help='Allows for a custom logfile name.')

parser.add_argument('--save-failing-tests', action='store_true', default=False,
                    help='Saves failed test files that do not match to their '
                         'golden copy equivalents.')

parser.add_argument('--hide-known-failures', action='store',
                    nargs='+',
                    help='The indices to specify which known failure tests to '
                         'comment out of the logfile. Use the format '
                         '"start:end". Refer to the indices within the log '
                         'file to determine which tests to hide. Multiple sets '
                         'of indices are allowed. Only one test file can be '
                         'run at a time when using this feature.')

args = parser.parse_args()

if args.logfile_filename is None:
    current_time = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
    args.logfile_filename = f'ephem_tools_unit_test_{current_time}.log'
logging.basicConfig(filename=args.logfile_filename,
                    encoding='utf-8',
                    level=logging.DEBUG,
                    format='%(asctime)s.%(msecs)03d | %(levelname)s | '
                    '%(message)s',
                    datefmt='%y-%m-%d %H:%M:%S',
                    force=True)

if args.save_failing_tests:
    os.makedirs('failed_tests', exist_ok=True)

if args.replace:
    os.makedirs(args.golden_directory, exist_ok=True)
    replace_golden_copies(args.run_ephemeris_type,
            args.test_file_paths,
            range_of_tests(args.limit_tests),
            args.golden_directory)
else:
    compare_tests_against_golden(args.run_ephemeris_type,
            args.test_file_paths,
            range_of_tests(args.limit_tests),
            args.save_failing_tests,
            range_of_tests(args.hide_known_failures),
            args.golden_directory,
            select_server(args.server))
