"""Tests for query-string parsing in compare_fortran CLI."""

from __future__ import annotations

from pathlib import Path

from tests.compare_fortran.__main__ import _read_test_urls, spec_from_query_input


def test_spec_from_query_input_viewer_url() -> None:
    """Viewer CGI URL parses into viewer RunSpec with expected core fields."""
    url = (
        'https://example/cgi-bin/tools/viewer3_xxx.pl?abbrev=nep&time=2022-01-01+00%3A00%3A00'
        '&fov=3&fov_unit=Neptune+radii&center=body&center_body=Neptune'
        '&moons=802+Triton+%26+Nereid&rings=LeVerrier%2C+Adams'
    )
    spec = spec_from_query_input(url)
    assert spec.tool == 'viewer'
    assert spec.params['planet'] == 8
    assert spec.params['time'] == '2022-01-01 00:00:00'
    assert spec.params['fov'] == 3.0
    assert spec.params['fov_unit'] == 'Neptune radii'
    assert spec.params['moons'] == [802]


def test_spec_from_query_input_tracker_url() -> None:
    """Tracker CGI URL parses repeated moons and rings as numeric codes."""
    url = (
        'https://example/cgi-bin/tools/tracker3_xxx.pl?abbrev=sat&start=2022-01-01&stop=2022-01-02'
        '&interval=1&time_unit=hours&moons=001+Mimas+%28S1%29&moons=002+Enceladus+%28S2%29'
        '&rings=061+Main+Rings&rings=062+G+Ring&xrange=10&xunit=arcsec'
    )
    spec = spec_from_query_input(url)
    assert spec.tool == 'tracker'
    assert spec.params['planet'] == 6
    assert spec.params['moons'] == [1, 2]
    assert spec.params['rings'] == [61, 62]
    assert spec.params['xrange'] == 10.0


def test_spec_from_query_input_ephem_url() -> None:
    """Ephemeris CGI URL parses columns and mooncols IDs."""
    url = (
        'https://example/cgi-bin/tools/ephem3_xxx.pl?abbrev=jup&start=2022-01-01&stop=2022-01-02'
        '&columns=001+Modified+Julian+Date&columns=015+Jupiter+RA+%26+Dec'
        '&mooncols=005+RA+%26+Dec&moons=001+Io+%28J1%29'
    )
    spec = spec_from_query_input(url)
    assert spec.tool == 'ephemeris'
    assert spec.params['planet'] == 5
    assert spec.params['columns'] == [1, 15]
    assert spec.params['mooncols'] == [5]
    assert spec.params['moons'] == [1]


def test_read_test_urls_skips_empty_and_comments(tmp_path: Path) -> None:
    """Test-file reader ignores blanks and # comments."""
    test_file = tmp_path / 'input.txt'
    test_file.write_text('\n# comment\nhttps://example/one\n  \nhttps://example/two\n')
    urls = _read_test_urls(test_file)
    assert urls == ['https://example/one', 'https://example/two']
