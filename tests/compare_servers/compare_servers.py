"""Contains the Ephemeris Tools Unit Tests."""

import argparse
import logging
import os
import re
import sys
import uuid
import warnings
from collections.abc import Iterable, Sequence
from datetime import datetime

import requests
import urllib3

_TEST_FILES_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'test_files'
)

_STAGING_URL_PREFIX = 'https://staging.pds.seti.org/'


def compare_tests_against_golden(
    ephem: str,
    test_files: Sequence[str],
    subtests: set[int] | None,
    *,
    store_failures: bool = False,
    known_failures: set[int] | None = None,
    golden_location: str = '',
    server: str = '',
) -> None:
    """Compare test versions to golden copies of chosen tools.

    Parameters:
        ephem: Ephemeris type ("current" or "test").
        test_files: Paths to tool test files (one URL per line).
        subtests: Optional set of test indices to run; None means all.
        store_failures: If True, write failing test content to failed_tests/.
        known_failures: Optional set of indices to treat as known failures (log only).
        golden_location: Directory containing golden copy files.
        server: Base URL of the server to fetch test output from.

    Returns:
        None. Results are written to the log via the logging module.

    Raises:
        SystemExit: On missing test file, URL not ending with 'output=HTML',
            connection/timeout errors, or missing golden file.
    """
    warnings.simplefilter('ignore', urllib3.exceptions.InsecureRequestWarning)
    tests_final = []

    for test_file in test_files:
        try:
            with open(test_file) as test_urls:
                test_urls = test_urls.readlines()
        except FileNotFoundError:
            logging.error(f'The {test_file} test file does not exist')
            print(f'A {test_file} test file does not exist')
            sys.exit(1)

        if len(test_urls) == 0:
            continue
        if 'viewer3' in test_urls[0]:
            viewer_urls = [url.strip() for url in test_urls]
            viewer_urls = [url.removeprefix(_STAGING_URL_PREFIX) for url in viewer_urls]

            for url in viewer_urls:
                if not url.endswith('&output=HTML'):
                    # This check for HTML within the URLs is necessary to ensure
                    # that all tests will function as expected. If tests are
                    # derived from a format other than HTML, this program will
                    # end and return a logged error.
                    logging.error(
                        f'The URL {url} within the planet viewer '
                        'tool tests does not end with '
                        '"&output=HTML".'
                    )
                    sys.exit(1)

            viewer_indices_ps = []

            for url in viewer_urls:
                tests_final.append(url)
                ps_url = url.replace('&output=HTML', '&output=PS')
                viewer_indices_ps.append(ps_url)
                tests_final.append(ps_url)

        if 'tracker3' in test_urls[0]:
            tracker_urls = [url.strip() for url in test_urls]
            tracker_urls = [url.removeprefix(_STAGING_URL_PREFIX) for url in tracker_urls]

            for url in tracker_urls:
                if not url.endswith('&output=HTML'):
                    # This check for HTML within the URLs is necessary to ensure
                    # that all tests will function as expected. If tests are
                    # derived from a format other than HTML, this program will
                    # end and return a logged error.
                    logging.error(
                        f'The URL {url} within the moon tracker tool '
                        'tests does not end with "&output=HTML".'
                    )
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
            ephemeris_urls = [url.removeprefix(_STAGING_URL_PREFIX) for url in ephemeris_urls]

            for url in ephemeris_urls:
                if not url.endswith('&output=HTML'):
                    # This check for HTML within the URLs is necessary to ensure
                    # that all tests will function as expected. If tests are
                    # derived from a format other than HTML, this program will
                    # end and return a logged error.
                    logging.error(
                        f'The URL {url} within the ephemeris tool '
                        'tests does not end with "&output=HTML".'
                    )
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
    elif ephem == 'current':
        suffix = ''
    else:
        raise ValueError(f"ephem must be 'test' or 'current', got: {ephem!r}")

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
                    content = requests.get(test, timeout=5.0, verify=False).content
                except requests.exceptions.ConnectionError:
                    logging.error(f'Failed to connect to server {server} with URL {test}')
                    print(f'Failed to connect to server {server} with URL {test}')
                    sys.exit(1)
                except requests.exceptions.ReadTimeout:
                    logging.error(
                        'Server timeout while attempting to '
                        f'retrieve {test} corresponding to the '
                        f'{tool_type} at line {index}'
                    )
                    print(
                        'Server timeout while attempting to '
                        f'retrieve {test} corresponding to the '
                        f'{tool_type} at line {index}'
                    )
                    sys.exit(1)
            except SystemExit as e:
                if e.code is not None:
                    sys.exit(e.code)
                raise
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
            with open(os.path.join(golden_location, name)) as file:
                golden_file = file.read()
        except FileNotFoundError:
            logging.error(f'Filename {name} not found within {golden_location}')
            print(f'Golden directory {golden_location} does not contain the file {name}')
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
                logging.warning(
                    f'{file_type} {tool_type} {name} located at '
                    f'line {index} does not match - known failure '
                    'skipped'
                )
            else:
                logging.error(
                    f'{file_type} {tool_type} {name} located at line '
                    f'{index} does not match. Test URL: {test}'
                )
            if store_failures:
                with open(os.path.join('failed_tests', name), 'w') as failed:
                    failed.write(content)
        else:
            logging.info(f'{file_type} {tool_type} {name} at line {index} matches')


def html_file_cleaner(ephem: str, raw_content: str) -> str:
    """Clean HTML output by removing material that varies between test runs.

    Parameters:
        ephem: Ephemeris type ("current" or "test"); used for tool-specific logic.
        raw_content: Raw UTF-8 HTML string from the test URL.

    Returns:
        Cleaned HTML string with titles, links, and variable content stripped.
    """
    clean = re.sub('/></a><br/>', '', raw_content)
    clean = re.sub(
        r'<title>'
        r'(Jupiter|Saturn|Uranus|Neptune|Pluto|Mars) '
        r'(Viewer|Moon Tracker|Ephemeris Generator) \d.\d '
        r'Results</title>',
        '',
        clean,
    )
    clean = re.sub(
        r'<h1>(Jupiter|Saturn|Uranus|Neptune|Pluto|Mars) '
        r'(Viewer|Moon Tracker|Ephemeris Generator) \d.\d '
        r'Results</h1>',
        '',
        clean,
    )
    clean = re.sub(
        r'<a target="blank" href="'
        r'/work/(viewer|tracker|ephem)\d_'
        r'(jup|sat|ura|nep|plu|mar)_\d{1,15}.pdf"><image '
        r'src="/work/(viewer|tracker|ephem)\d_'
        r'(jup|sat|ura|nep|plu|mar)_'
        r'\d{1,10}tn.jpg"',
        '',
        clean,
    )
    clean = re.sub(
        r'<a target="blank" href="/work/'
        r'(viewer|tracker|ephem)\d_'
        r'(jup|sat|ura|nep|plu|mar)_\d{1,15}.pdf\'><image '
        r'src="/work/(viewer|tracker|ephem)\d_'
        r'(jup|sat|ura|nep|plu|mar)_\d{1,10}tn.jpg"',
        '',
        clean,
    )
    clean = re.sub(
        r'<p>Click <a target="blank" href="/work/'
        r'(viewer|tracker|ephem)3_'
        r'(jup|sat|ura|nep|plu|mar)_'
        r'\d{1,15}.pdf">here</a>',
        '',
        clean,
    )
    clean = re.sub(r'to download diagram \(PDF, \d{1,15} bytes\).</p>', '', clean)
    clean = re.sub(
        r'<p>Click <a target="blank" href="/work/'
        r'(viewer|tracker|ephem)\d_'
        r'(jup|sat|ura|nep|plu|mar)_'
        r'(\d{1,15}|\d{1,15}\w).jpg">here</a>',
        '',
        clean,
    )
    clean = re.sub(
        r'to download diagram \(JPEG format, '
        r'\d{1,15} bytes\).</p>',
        '',
        clean,
    )
    clean = re.sub(
        r'<p>Click <a target="blank" href="/work'
        r'/(viewer|tracker|ephem)\d_'
        r'(jup|sat|ura|nep|plu|mar)_'
        r'\d{1,15}.ps">here</a>',
        '',
        clean,
    )
    clean = re.sub(
        r'to download diagram \(PostScript format, \d{1,15} '
        r'bytes\).</p>',
        '',
        clean,
    )
    clean = re.sub(
        r'<p>Click <a target="blank" href="/work/'
        r'(viewer|tracker|ephem)\d_'
        r'(jup|sat|ura|nep|plu|mar)_'
        r'\d{1,15}.tab">here</a>',
        '',
        clean,
    )
    clean = re.sub(
        r'to download table \(ASCII format, '
        r'\d{1,15} bytes\).</p>',
        '',
        clean,
    )
    clean = re.sub(
        r'Click <a href="/work/(ephem|viewer)\d_'
        r'(jup|sat|ura|nep|plu|mar)_\d{1,15}.tab">here</a>',
        '',
        clean,
    )
    clean = re.sub(
        r'to download table \(ASCII format, '
        r'\d{1,15} bytes\).',
        '',
        clean,
    )
    if ephem == 'test':
        clean = re.sub(r'Ephemeris: .+', '', clean)
        clean = re.sub(r'Viewpoint: .+', '', clean)
    clean = re.sub(
        r'<a href=\'/tools/(viewer|tracker|ephem)'
        r'\d_\w(jup|sat|ura|nep|plu|mar).shtml\'>'
        r'(Jupiter|Saturn|Uranus|Neptune|Pluto|Mars) '
        r'(Viewer|Moon Tracker|Ephemeris Generator) '
        r'Form</a> \|',
        '',
        clean,
    )

    return clean


def ps_file_cleaner(ephem: str, raw_content: str) -> str:
    """Clean PostScript output by removing variable headers and titles.

    Parameters:
        ephem: Ephemeris type ("current" or "test"); test mode strips TEST markers.
        raw_content: Raw UTF-8 PostScript content from the test URL.

    Returns:
        Cleaned PostScript string with generator text and titles removed.
    """
    clean = re.sub(r'\(Generated by .+\)', '', raw_content)
    if ephem == 'test':
        clean = re.sub(r'\((JUP|SAT|URA|NEP|PLU|MAR).+[0-9]\)', '', clean)
        clean = re.sub(r' \\\(TEST\\\)', '', clean)
        clean = re.sub(r'\(TEST\)', '', clean)
    clean = re.sub(
        r'%%Title: (viewer|tracker)\d_'
        r'(jup|sat|ura|nep|plu|mar)_\d{1,10}.ps',
        '',
        clean,
    )

    return clean


def tab_file_cleaner(_ephem: str, raw_content: str) -> str:
    """Clean TAB output by removing variable content (e.g. server address in errors).

    Parameters:
        _ephem: Ephemeris type; unused for TAB cleaning, kept for API consistency.
        raw_content: Raw UTF-8 tabular content from the test URL.

    Returns:
        Cleaned string with address and other variable parts removed.
    """
    # This removes the server name from a 500 Internal Server Error
    clean = re.sub(r'<address>(.+)</address>', '', raw_content)

    return clean


def replace_golden_copies(
    ephem: str,
    test_files: Sequence[str],
    subtests: set[int] | None,
    golden_copies_path: str,
) -> None:
    """Replace golden copies of tests within a chosen directory.

    For each test file, reads URLs (one per line), generates HTML/PS/TAB
    variants per tool, fetches content from the staging server, and writes
    files into golden_copies_path. Only URLs in subtests (if set) are used.

    Parameters:
        ephem: Ephemeris type ("test" or "current"); appended to URLs when "test".
        test_files: Paths to test URL list files.
        subtests: Optional set of test indices to include; None means all.
        golden_copies_path: Directory where golden files are written.

    Returns:
        None.

    Raises:
        SystemExit: If a URL does not end with '&output=HTML' or on I/O error.
    """
    for test_file in test_files:
        try:
            with open(test_file) as f:
                test_urls = f.readlines()
        except FileNotFoundError:
            logging.error(f'Test file not found: {test_file}')
            continue
        test_urls = [url.strip() for url in test_urls]
        test_urls = [url.removeprefix(_STAGING_URL_PREFIX) for url in test_urls]

        for url in test_urls:
            if not url.endswith('&output=HTML'):
                # This check for HTML within the URLs is necessary to ensure
                # that all tests will function as expected. If tests are
                # derived from a format other than HTML, this program will
                # end and return a logged error.
                logging.error('A URL within the test file does not end with "&output=HTML"')
                sys.exit(1)

        logging.info('Test file is properly formatted')

        if 'viewer3' in test_urls[0]:
            ps_versions = []
            all_urls = list(test_urls)
            number_of_base_tests = str(len(test_urls))
            logging.info(
                'Golden copies of the Planet Viewer Tool requested. '
                f'Now generating {number_of_base_tests} HTML file '
                'versions.'
            )

            logging.info(
                'HTML test versions generated. Now generating '
                f'{number_of_base_tests} PostScript file versions.'
            )

            for url in test_urls:
                url = url.replace('output=HTML', 'output=PS')
                ps_versions.append(url)
                all_urls.append(url)

        elif 'tracker3' in test_urls[0]:
            ps_versions = []
            tab_versions = []
            all_urls = list(test_urls[:])
            number_of_base_tests = len(all_urls)
            logging.info(
                'Golden copies of the Moon Tracker Tool requested. '
                f'Now generating {number_of_base_tests} golden '
                'copies.'
            )

            logging.info(
                'HTML test versions generated. Now generating '
                f'{number_of_base_tests} PostScript file versions.'
            )
            for url in test_urls:
                url = url.replace('output=HTML', 'output=PS')
                ps_versions.append(url)
                all_urls.append(url)

            logging.info(
                'Postscript test versions generated. Now generating '
                f'{number_of_base_tests} TAB file versions.'
            )
            for url in test_urls:
                url = url.replace('output=HTML', 'output=TAB')
                tab_versions.append(url)
                all_urls.append(url)

        else:
            assert 'ephem3' in test_urls[0]
            tab_versions = []
            all_urls = test_urls[:]
            number_of_base_tests = str(len(all_urls))
            logging.info(
                'Golden copies of the Ephemeris Generator Tool '
                f'requested. Now generating {number_of_base_tests} '
                'golden copies.'
            )

            logging.info(
                'HTML test versions generated. Now generating '
                f'{number_of_base_tests} TAB file versions.'
            )
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

            if (subtests is not None and index in subtests) or (subtests is None):
                if ephem == 'test':
                    file += '&ephem=+-1+TEST&sc_trajectory=+-1+TEST'
                name = str(uuid.uuid5(uuid.NAMESPACE_URL, file))
                file = 'https://staging.pds.seti.org/' + file
                grab = requests.get(file, verify=False, timeout=5.0)
                content = grab.content
                content = content.decode('utf8')
                with open(os.path.join(golden_copies_path, name), 'w') as goldfile:
                    goldfile.write(content)
                    logging.info(f'File {name} at line {index} generated')


def range_of_tests(
    selected_tests: Iterable[str] | None,
) -> set[int] | None:
    """Create set of indices for limiting tests or hiding known failures.

    Parameters:
        selected_tests: Optional iterable of "start:end" range strings or
            single-index strings (e.g. "3:7" or "2"). Empty/None returns None.

    Returns:
        Set of test indices, or None if selected_tests is None/empty (meaning no filter).
    """
    subtests = None
    if selected_tests is not None:
        subtests = set()
        for set_of_tests in selected_tests:
            set_of_tests = set_of_tests.split(':')
            if set_of_tests[0] == set_of_tests[-1]:
                subtests.add(int(set_of_tests[0]))
            else:
                subtests.update(range(int(set_of_tests[0]), int(set_of_tests[-1]) + 1))

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


def main() -> None:
    """Parse command-line arguments and run comparison or golden-copy replacement."""
    warnings.simplefilter('ignore', urllib3.exceptions.InsecureRequestWarning)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        '--run-ephemeris-type',
        type=str,
        choices=['test', 'current'],
        default='current',
        help='Select which SPICE kernels are being used on '
        'the server. The "test" type will use the most recent '
        'defaults. The "current" type will use what is '
        'available on the chosen server. The default is '
        '"current".',
    )

    parser.add_argument(
        '--replace',
        action='store_true',
        default=False,
        help='Replace stored versions of chosen ephemeris '
        'tools. All versions stored are generated from the '
        'current staging server.',
    )

    parser.add_argument(
        '--test-file-paths',
        type=str,
        nargs='+',
        default=[
            os.path.join(_TEST_FILES_DIR, 'viewer-test-urls.txt'),
            os.path.join(_TEST_FILES_DIR, 'tracker-test-urls.txt'),
            os.path.join(_TEST_FILES_DIR, 'ephemeris-test-urls.txt'),
        ],
        help='The files containing the URLs to test, one per tool.',
    )

    parser.add_argument(
        '--golden-directory',
        type=str,
        default='golden_copies',
        help='Path to the directory containing the golden copies.',
    )

    parser.add_argument(
        '--limit-tests',
        action='store',
        nargs='+',
        help='The indices to specify which subset of tests to run '
        'within a set of URL tests. Use the format '
        '"start:end". Refer to the indices within the log '
        'file to determine which tests to rerun. Only one '
        'test file can be specified to use this command.',
    )

    parser.add_argument(
        '--server',
        type=str,
        default='production',
        help='The server you wish to generate the current tests '
        'for comparison. If you choose "other", please enter '
        'the URL prefix for the server you wish to use.',
    )

    parser.add_argument('--logfile-filename', type=str, help='Allows for a custom logfile name.')

    parser.add_argument(
        '--save-failing-tests',
        action='store_true',
        default=False,
        help='Saves failed test files that do not match to their golden copy equivalents.',
    )

    parser.add_argument(
        '--hide-known-failures',
        action='store',
        nargs='+',
        help='The indices to specify which known failure tests to '
        'comment out of the logfile. Use the format '
        '"start:end". Refer to the indices within the log '
        'file to determine which tests to hide. Multiple sets '
        'of indices are allowed. Only one test file can be '
        'run at a time when using this feature.',
    )

    args = parser.parse_args()

    if args.logfile_filename is None:
        current_time = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        args.logfile_filename = f'ephem_tools_unit_test_{current_time}.log'
    logging.basicConfig(
        filename=args.logfile_filename,
        encoding='utf-8',
        level=logging.DEBUG,
        format='%(asctime)s.%(msecs)03d | %(levelname)s | %(message)s',
        datefmt='%y-%m-%d %H:%M:%S',
        force=True,
    )

    if args.save_failing_tests:
        os.makedirs('failed_tests', exist_ok=True)

    if args.replace:
        os.makedirs(args.golden_directory, exist_ok=True)
        replace_golden_copies(
            args.run_ephemeris_type,
            args.test_file_paths,
            range_of_tests(args.limit_tests),
            args.golden_directory,
        )
    else:
        compare_tests_against_golden(
            args.run_ephemeris_type,
            args.test_file_paths,
            range_of_tests(args.limit_tests),
            store_failures=args.save_failing_tests,
            known_failures=range_of_tests(args.hide_known_failures),
            golden_location=args.golden_directory,
            server=select_server(args.server),
        )


if __name__ == '__main__':
    main()
