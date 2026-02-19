"""CLI entry point: ephemeris-tools ephemeris|tracker|viewer subcommands."""

from __future__ import annotations

import argparse
import contextlib
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import NoReturn, TextIO, cast

from ephemeris_tools.constants import DEFAULT_INTERVAL
from ephemeris_tools.ephemeris import generate_ephemeris
from ephemeris_tools.input_params import (
    write_input_parameters_ephemeris,
    write_input_parameters_tracker,
    write_input_parameters_viewer,
)
from ephemeris_tools.params import (
    EphemerisParams,
    ExtraStar,
    Observer,
    TrackerParams,
    ViewerParams,
    _parse_sexagesimal_to_degrees,
    ephemeris_params_from_env,
    parse_center,
    parse_column_spec,
    parse_fov,
    parse_mooncol_spec,
    parse_observer,
    parse_planet,
    tracker_params_from_env,
    viewer_params_from_env,
)
from ephemeris_tools.planets import parse_moon_spec
from ephemeris_tools.tracker import run_tracker
from ephemeris_tools.viewer import run_viewer

logger = logging.getLogger(__name__)


def _configure_logging(verbose: bool = False) -> None:
    """Configure logging for CLI (stderr, level from --verbose or EPHEMERIS_TOOLS_LOG)."""
    level = logging.DEBUG if verbose else logging.WARNING
    env_level = os.environ.get('EPHEMERIS_TOOLS_LOG', '').upper()
    if env_level in ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'):
        level = getattr(logging, env_level)
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(name)s: %(message)s',
        stream=sys.stderr,
    )
    # Suppress noisy third-party DEBUG (OpenTelemetry, google.cloud.storage, etc.).
    for name in (
        'google',
        'google.cloud',
        'google.cloud.storage',
        'opentelemetry',
        'opentelemetry.sdk',
    ):
        logging.getLogger(name).setLevel(logging.WARNING)


def _ephemeris_cmd(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    """Run ephemeris generator (ephemeris subcommand).

    Parameters:
        parser: Argument parser (unused).
        args: Parsed args or CGI env; planet, start, stop, columns, etc.

    Returns:
        Exit code 0 on success, 1 on error.
    """
    if args.cgi:
        params = ephemeris_params_from_env()
        if params is None:
            print('Invalid or missing CGI parameters (e.g. NPLANET, start, stop).', file=sys.stderr)
            return 1
        if not args.output:
            args.output = os.environ.get('EPHEM_FILE', None)
    else:
        moons_raw = args.moons or []
        moon_ids = parse_moon_spec(args.planet, [str(x) for x in moons_raw])
        observer = Observer(name="Earth's Center")
        if args.observer is not None:
            observer = parse_observer(args.observer)
        viewpoint = (args.viewpoint or 'observatory').strip() or 'observatory'
        observatory = (args.observatory or "Earth's Center").strip() or "Earth's Center"
        if viewpoint == 'latlon' and (args.latitude is not None or args.longitude is not None):
            lon = args.longitude
            if lon is not None and args.lon_dir == 'west':
                lon = -lon
        else:
            lon = None
            if args.observer is None:
                observer = parse_observer([observatory])
        params = EphemerisParams(
            planet_num=args.planet,
            start_time=args.start,
            stop_time=args.stop,
            interval=args.interval,
            time_unit=args.time_unit,
            ephem_version=args.ephem,
            observer=observer,
            viewpoint=viewpoint,
            observatory=observatory,
            latitude_deg=args.latitude if viewpoint == 'latlon' else None,
            longitude_deg=lon if viewpoint == 'latlon' else None,
            lon_dir=args.lon_dir,
            altitude_m=args.altitude if viewpoint == 'latlon' else None,
            sc_trajectory=args.sc_trajectory,
            columns=parse_column_spec([str(x) for x in (args.columns or [])]) or [1, 2, 3, 15, 8],
            mooncols=parse_mooncol_spec([str(x) for x in (args.mooncols or [])]) or [5, 6, 8, 9],
            moon_ids=moon_ids,
        )
        if viewpoint != 'latlon' and args.viewpoint and args.viewpoint != "Earth's Center":
            params.observatory = args.viewpoint or observatory

    write_input_parameters_ephemeris(sys.stdout, params)

    out: TextIO = sys.stdout
    if args.output is not None:
        try:
            with open(args.output, 'w') as f:
                generate_ephemeris(params, f)
            return 0
        except (ValueError, RuntimeError) as e:
            print(f'Error: {e}', file=sys.stderr)
            return 1
    try:
        generate_ephemeris(params, out)
        return 0
    except (ValueError, RuntimeError) as e:
        print(f'Error: {e}', file=sys.stderr)
        return 1


def main() -> int:
    """Entry point for ephemeris-tools CLI (ephemeris | tracker | viewer).

    Returns:
        Exit code 0 on success, 1 on failure.
    """
    parser = argparse.ArgumentParser(
        prog='ephemeris-tools',
        description='Planetary ephemeris, moon tracker, and planet viewer.',
    )
    subparsers = parser.add_subparsers(dest='command', required=True)

    ephem_parser = subparsers.add_parser('ephemeris', help='Generate ephemeris table')
    ephem_parser.add_argument(
        '--cgi', action='store_true', help='Read parameters from environment (CGI)'
    )
    ephem_parser.add_argument(
        '--planet',
        type=parse_planet,
        default=6,
        help='Planet number or name (4=mars..9=pluto); env: NPLANET',
    )
    ephem_parser.add_argument(
        '--start', type=str, default='', help='Start time; env: start, START_TIME'
    )
    ephem_parser.add_argument(
        '--stop', type=str, default='', help='Stop time; env: stop, STOP_TIME'
    )
    ephem_parser.add_argument(
        '--interval', type=float, default=DEFAULT_INTERVAL, help='Time step; env: interval'
    )
    ephem_parser.add_argument(
        '--time-unit',
        type=str,
        default='hour',
        choices=['sec', 'min', 'hour', 'day'],
        help='env: time_unit',
    )
    ephem_parser.add_argument(
        '--ephem', type=int, default=0, help='Ephemeris version (0=latest); env: ephem'
    )
    ephem_parser.add_argument(
        '--viewpoint',
        type=str,
        default='',
        help="observatory, latlon, or Earth's Center; env: viewpoint",
    )
    ephem_parser.add_argument(
        '--observer',
        type=str,
        nargs='+',
        default=None,
        help='Observer shortcut: name or "lat lon alt"',
    )
    ephem_parser.add_argument(
        '--observatory',
        type=str,
        default='',
        help='Observatory name when viewpoint=observatory; env: observatory',
    )
    ephem_parser.add_argument(
        '--latitude',
        type=float,
        default=None,
        help='Latitude (deg) when viewpoint=latlon; env: latitude',
    )
    ephem_parser.add_argument(
        '--longitude', type=float, default=None, help='Longitude (deg); env: longitude'
    )
    ephem_parser.add_argument(
        '--lon-dir', type=str, default='east', choices=['east', 'west'], help='env: lon_dir'
    )
    ephem_parser.add_argument(
        '--altitude',
        type=float,
        default=None,
        help='Altitude (m) when viewpoint=latlon; env: altitude',
    )
    ephem_parser.add_argument(
        '--sc-trajectory',
        type=int,
        default=0,
        help='Spacecraft trajectory version; env: sc_trajectory',
    )
    ephem_parser.add_argument(
        '--columns',
        type=str,
        nargs='*',
        default=None,
        help='Column IDs or names (e.g. 1 2 ymdhms radec); env: columns',
    )
    ephem_parser.add_argument(
        '--mooncols',
        type=str,
        nargs='*',
        default=None,
        help='Moon column IDs or names (e.g. 5 6 radec offset); env: mooncols',
    )
    ephem_parser.add_argument(
        '--moons',
        type=str,
        nargs='*',
        default=None,
        help='Moon indices or names (e.g. 1 2 io europa); env: moons',
    )
    ephem_parser.add_argument(
        '-o', '--output', type=str, default=None, help='Output file; env: EPHEM_FILE'
    )
    ephem_parser.add_argument('-v', '--verbose', action='store_true', help='Show INFO logs')
    ephem_parser.set_defaults(func=_ephemeris_cmd)

    track_parser = subparsers.add_parser('tracker', help='Moon tracker plot')
    track_parser.add_argument(
        '--cgi', action='store_true', help='Read parameters from environment (CGI)'
    )
    track_parser.add_argument(
        '--planet', type=parse_planet, default=6, help='Planet number or name; env: NPLANET'
    )
    track_parser.add_argument('--start', type=str, default='', help='Start time; env: start')
    track_parser.add_argument('--stop', type=str, default='', help='Stop time; env: stop')
    track_parser.add_argument(
        '--interval', type=float, default=DEFAULT_INTERVAL, help='Time step; env: interval'
    )
    track_parser.add_argument(
        '--time-unit',
        type=str,
        default='hour',
        choices=['sec', 'min', 'hour', 'day'],
        help='env: time_unit',
    )
    track_parser.add_argument(
        '--ephem', type=int, default=0, help='Ephemeris version (0=latest); env: ephem'
    )
    track_parser.add_argument(
        '--observer',
        type=str,
        nargs='+',
        default=None,
        help='Observer shortcut: name or "lat lon alt"',
    )
    track_parser.add_argument(
        '--viewpoint',
        type=str,
        default='',
        help="observatory, latlon, or Earth's Center; env: viewpoint",
    )
    track_parser.add_argument(
        '--observatory',
        type=str,
        default='',
        help='Observatory when viewpoint=observatory; env: observatory',
    )
    track_parser.add_argument(
        '--latitude', type=float, default=None, help='Latitude (deg); env: latitude'
    )
    track_parser.add_argument(
        '--longitude', type=float, default=None, help='Longitude (deg); env: longitude'
    )
    track_parser.add_argument(
        '--lon-dir', type=str, default='east', choices=['east', 'west'], help='env: lon_dir'
    )
    track_parser.add_argument(
        '--altitude', type=float, default=None, help='Altitude (m); env: altitude'
    )
    track_parser.add_argument(
        '--sc-trajectory', type=int, default=0, help='Spacecraft trajectory; env: sc_trajectory'
    )
    track_parser.add_argument(
        '--moons',
        type=str,
        nargs='*',
        default=None,
        help='Moon indices or names (e.g. 1 2 io europa); env: moons',
    )
    track_parser.add_argument(
        '--rings',
        type=str,
        nargs='*',
        default=None,
        help='Ring option codes or names (e.g. 61 62, main ge); env: rings',
    )
    track_parser.add_argument(
        '--xrange',
        type=float,
        default=None,
        help='Half-range of x-axis (arcsec or radii); env: xrange',
    )
    track_parser.add_argument(
        '--xunit',
        type=str,
        default='arcsec',
        choices=['arcsec', 'radii'],
        help='x-axis units; env: xunit',
    )
    track_parser.add_argument('--title', type=str, default='', help='Plot title; env: title')
    track_parser.add_argument(
        '-o', '--output', type=str, default=None, help='PostScript file; env: TRACKER_POSTFILE'
    )
    track_parser.add_argument(
        '--output-txt', type=str, default=None, help='Text table file; env: TRACKER_TEXTFILE'
    )
    track_parser.add_argument('-v', '--verbose', action='store_true', help='Show INFO logs')
    track_parser.set_defaults(func=_tracker_cmd)

    view_parser = subparsers.add_parser('viewer', help='Planet viewer diagram')
    view_parser.add_argument(
        '--cgi', action='store_true', help='Read parameters from environment (CGI)'
    )
    view_parser.add_argument(
        '--planet', type=parse_planet, default=6, help='Planet number or name; env: NPLANET'
    )
    view_parser.add_argument('--time', type=str, default='', help='Observation time; env: time')
    view_parser.add_argument(
        '--ephem', type=int, default=0, help='Ephemeris version (0=latest); env: ephem'
    )
    view_parser.add_argument(
        '--fov',
        type=str,
        nargs='+',
        default=None,
        help='Field of view as value + unit tokens (e.g. 3 Neptune radii)',
    )
    view_parser.add_argument(
        '--fov-unit',
        type=str,
        default='deg',
        help=(
            'FOV unit: deg, arcmin, arcsec, or instrument name '
            '(e.g. Voyager ISS narrow angle FOVs); env: fov_unit'
        ),
    )
    view_parser.add_argument(
        '--center',
        type=str,
        nargs='+',
        default=None,
        help='Diagram center tokens (e.g. neptune, leverrier west, 12.5 -30.2)',
    )
    view_parser.add_argument(
        '--center-body', type=str, default='', help='Body name when center=body; env: center_body'
    )
    view_parser.add_argument(
        '--center-ansa', type=str, default='', help='Ring ansa when center=ansa; env: center_ansa'
    )
    view_parser.add_argument(
        '--center-ew', type=str, default='east', help='East/west when center=ansa; env: center_ew'
    )
    view_parser.add_argument(
        '--center-ra', type=float, default=0.0, help='Center RA (deg); env: center_ra'
    )
    view_parser.add_argument(
        '--center-dec', type=float, default=0.0, help='Center Dec (deg); env: center_dec'
    )
    view_parser.add_argument(
        '--center-ra-type', type=str, default='hours', help='RA units; env: center_ra_type'
    )
    view_parser.add_argument(
        '--center-star', type=str, default='', help='Star name when center=star; env: center_star'
    )
    view_parser.add_argument(
        '--viewpoint',
        type=str,
        default='',
        help="observatory, latlon, or Earth's Center; env: viewpoint",
    )
    view_parser.add_argument(
        '--observer',
        type=str,
        nargs='+',
        default=None,
        help='Observer shortcut: name or "lat lon alt"',
    )
    view_parser.add_argument(
        '--observatory', type=str, default='', help='Observatory name; env: observatory'
    )
    view_parser.add_argument(
        '--latitude', type=float, default=None, help='Latitude (deg); env: latitude'
    )
    view_parser.add_argument(
        '--longitude', type=float, default=None, help='Longitude (deg); env: longitude'
    )
    view_parser.add_argument(
        '--lon-dir', type=str, default='east', choices=['east', 'west'], help='env: lon_dir'
    )
    view_parser.add_argument(
        '--altitude', type=float, default=None, help='Altitude (m); env: altitude'
    )
    view_parser.add_argument(
        '--sc-trajectory', type=int, default=0, help='Spacecraft trajectory; env: sc_trajectory'
    )
    view_parser.add_argument(
        '--moons',
        type=str,
        nargs='*',
        default=None,
        help='Moon indices or names (e.g. 1 2 io europa); env: moons',
    )
    view_parser.add_argument(
        '--moremoons', type=str, default=None, help='Additional moon selection; env: moremoons'
    )
    view_parser.add_argument(
        '--rings', type=str, nargs='*', default=None, help='Ring option codes or names; env: rings'
    )
    view_parser.add_argument('--torus', type=str, default=None, help='Show Io torus; env: torus')
    view_parser.add_argument(
        '--torus-inc', type=float, default=6.8, help='Io torus inclination (deg); env: torus_inc'
    )
    view_parser.add_argument(
        '--torus-rad', type=float, default=422000.0, help='Io torus radius (km); env: torus_rad'
    )
    view_parser.add_argument(
        '--ephem-display',
        type=str,
        default=None,
        help='Ephemeris string for Input Parameters (e.g. NEP095 + DE440); env: ephem_display',
    )
    view_parser.add_argument(
        '--moons-display',
        type=str,
        default=None,
        help=(
            'Moon selection string for Input Parameters '
            '(e.g. 802 Triton & Nereid); env: moons_display'
        ),
    )
    view_parser.add_argument(
        '--rings-display',
        type=str,
        default=None,
        help=(
            'Ring selection string for Input Parameters (e.g. LeVerrier, Arago); env: rings_display'
        ),
    )
    view_parser.add_argument(
        '--standard', type=str, default=None, help='Standard stars; env: standard'
    )
    view_parser.add_argument(
        '--additional', type=str, default=None, help='Additional star; env: additional'
    )
    view_parser.add_argument(
        '--extra-name', type=str, default=None, help='Additional star name; env: extra_name'
    )
    view_parser.add_argument(
        '--extra-ra', type=str, default=None, help='Additional star RA; env: extra_ra'
    )
    view_parser.add_argument(
        '--extra-ra-type',
        type=str,
        default=None,
        help='Additional star RA type; env: extra_ra_type',
    )
    view_parser.add_argument(
        '--extra-dec', type=str, default=None, help='Additional star Dec; env: extra_dec'
    )
    view_parser.add_argument(
        '--other', type=str, nargs='*', default=None, help='Other bodies; env: other'
    )
    view_parser.add_argument('--title', type=str, default='', help='Diagram title; env: title')
    view_parser.add_argument('--labels', type=str, default=None, help='Moon labels; env: labels')
    view_parser.add_argument(
        '--moonpts', type=str, default=None, help='Moon enlargement (points); env: moonpts'
    )
    view_parser.add_argument('--blank', type=str, default=None, help='Blank disks; env: blank')
    view_parser.add_argument(
        '--opacity', type=str, default=None, help='Ring plot type; env: opacity'
    )
    view_parser.add_argument(
        '--peris', type=str, default=None, help='Pericenter markers; env: peris'
    )
    view_parser.add_argument(
        '--peripts', type=str, default=None, help='Pericenter marker size; env: peripts'
    )
    view_parser.add_argument(
        '--meridians', type=str, default=None, help='Prime meridians; env: meridians'
    )
    view_parser.add_argument(
        '--arcmodel', type=str, default=None, help='Arc model (Neptune); env: arcmodel'
    )
    view_parser.add_argument(
        '--arcpts', type=str, default=None, help='Arc weight points (Neptune); env: arcpts'
    )
    view_parser.add_argument(
        '-o', '--output', type=str, default=None, help='PostScript file; env: VIEWER_POSTFILE'
    )
    view_parser.add_argument(
        '--output-txt', type=str, default=None, help='Field of View table file'
    )
    view_parser.add_argument('-v', '--verbose', action='store_true', help='Show INFO logs')
    view_parser.set_defaults(func=_viewer_cmd)

    args = parser.parse_args()
    _configure_logging(verbose=args.verbose)
    return cast(int, args.func(parser, args))


def _tracker_cmd(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    """Run moon tracker (tracker subcommand).

    Parameters:
        parser: Argument parser (unused).
        args: Parsed args; planet, start, stop, moons, rings, output, etc.

    Returns:
        Exit code 0 on success, 1 on error.
    """
    if args.cgi:
        params = tracker_params_from_env()
        if params is None:
            print('Invalid or missing CGI tracker parameters.', file=sys.stderr)
            return 1
        write_input_parameters_tracker(sys.stdout, params)
        with contextlib.ExitStack() as stack:
            post_path = os.environ.get('TRACKER_POSTFILE')
            txt_path = os.environ.get('TRACKER_TEXTFILE')
            if post_path:
                params.output_ps = stack.enter_context(open(post_path, 'w'))
            if txt_path:
                params.output_txt = stack.enter_context(open(txt_path, 'w'))
            try:
                run_tracker(params)
                return 0
            except (ValueError, RuntimeError) as e:
                print(f'Error: {e}', file=sys.stderr)
                return 1

    moons_raw = args.moons or []
    moon_ids = parse_moon_spec(args.planet, [str(x) for x in moons_raw])
    if args.observer is not None:
        observer = parse_observer(args.observer)
    else:
        observer_name = (args.observatory or "Earth's Center").strip() or "Earth's Center"
        observer = parse_observer([observer_name])
    _now = datetime.now(timezone.utc)
    _default_start = _now.strftime('%Y-%m-%d %H:%M')
    _default_stop = (_now + timedelta(days=1)).strftime('%Y-%m-%d %H:%M')
    if args.start and not args.stop:
        try:
            parsed_start = datetime.strptime(args.start, '%Y-%m-%d %H:%M').replace(
                tzinfo=timezone.utc
            )
            _computed_stop = (parsed_start + timedelta(days=1)).strftime('%Y-%m-%d %H:%M')
        except ValueError:
            _computed_stop = _default_stop
    else:
        _computed_stop = _default_stop
    start_time = args.start or _default_start
    stop_time = args.stop or _computed_stop
    tracker_params = TrackerParams(
        planet_num=args.planet,
        start_time=start_time,
        stop_time=stop_time,
        interval=args.interval,
        time_unit=args.time_unit,
        observer=observer,
        ephem_version=args.ephem,
        moon_ids=moon_ids,
        ring_names=(args.rings or None),
        xrange=args.xrange,
        xunit=args.xunit,
        title=(args.title or '').strip(),
    )
    write_input_parameters_tracker(sys.stdout, tracker_params)
    with contextlib.ExitStack() as stack:
        out_ps = stack.enter_context(open(args.output, 'w')) if args.output is not None else None
        out_txt = (
            stack.enter_context(open(args.output_txt, 'w')) if args.output_txt is not None else None
        )
        try:
            tracker_params.output_ps = out_ps
            tracker_params.output_txt = out_txt
            run_tracker(tracker_params)
        except (ValueError, RuntimeError) as e:
            print(f'Error: {e}', file=sys.stderr)
            return 1
    return 0


def _viewer_cmd(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    """Run planet viewer (viewer subcommand).

    Parameters:
        parser: Argument parser (unused).
        args: Parsed args; planet, time, fov, center, output, etc.

    Returns:
        Exit code 0 on success, 1 on error.
    """
    if args.cgi:
        params = viewer_params_from_env()
        if params is None:
            print('Invalid or missing CGI viewer parameters.', file=sys.stderr)
            return 1
        write_input_parameters_viewer(sys.stdout, params)
        with contextlib.ExitStack() as stack:
            post_path = os.environ.get('VIEWER_POSTFILE')
            txt_path = os.environ.get('VIEWER_TEXTFILE')
            if post_path:
                params.output_ps = stack.enter_context(open(post_path, 'w'))
            if txt_path:
                params.output_txt = stack.enter_context(open(txt_path, 'w'))
            try:
                run_viewer(params)
                return 0
            except (ValueError, RuntimeError) as e:
                print(f'Error: {e}', file=sys.stderr)
                return 1

    with contextlib.ExitStack() as stack:
        out = stack.enter_context(open(args.output, 'w')) if args.output is not None else None
        out_txt = (
            stack.enter_context(open(args.output_txt, 'w')) if args.output_txt is not None else None
        )
        fov_tokens = args.fov
        if fov_tokens:
            if len(fov_tokens) == 1 and args.fov_unit:
                fov_tokens = [fov_tokens[0], args.fov_unit]
            fov_value, fov_unit = parse_fov(fov_tokens)
        else:
            fov_value, fov_unit = (1.0, 'degrees')
        if args.observer is not None:
            observer = parse_observer(args.observer)
        elif (args.viewpoint or '').strip().lower() == 'latlon':
            lon_dir = (args.lon_dir or 'east').strip().lower()
            lat = args.latitude
            lon = args.longitude
            alt = args.altitude
            if lon is not None and lon_dir == 'west':
                lon = -lon
            observer = Observer(
                latitude_deg=lat,
                longitude_deg=lon,
                lon_dir=lon_dir,
                altitude_m=alt,
            )
        else:
            observer_name = (args.observatory or "Earth's Center").strip() or "Earth's Center"
            observer = parse_observer([observer_name])
        center_tokens = args.center
        if center_tokens:
            first = center_tokens[0].lower()
            if first == 'body' and args.center_body is not None:
                center = parse_center(args.planet, [str(args.center_body)])
            elif first == 'j2000':
                center = parse_center(
                    args.planet,
                    [str(args.center_ra), str(args.center_dec)],
                )
            elif first == 'ansa':
                center = parse_center(
                    args.planet,
                    [
                        str(args.center_ansa),
                        str(args.center_ew),
                    ],
                )
            elif first == 'star':
                center = parse_center(args.planet, [str(args.center_star)])
            else:
                center = parse_center(args.planet, [str(x) for x in center_tokens])
        else:
            center = parse_center(args.planet, [])
        moon_ids = None
        if args.moons:
            moon_ids = parse_moon_spec(args.planet, [str(x) for x in args.moons])
        rings_raw = [str(r) for r in (args.rings or [])]
        ring_names: list[str] | None = None
        if rings_raw:
            ring_names = []
            for token in rings_raw:
                for comma_part in token.split(','):
                    for amp_part in comma_part.split('&'):
                        part = amp_part.strip()
                        if part:
                            ring_names.append(part)
        blank = (args.blank or '').strip().lower()
        opacity = (args.opacity or 'Transparent').strip() or 'Transparent'
        peris = (args.peris or 'None').strip() or 'None'
        peripts_raw = (args.peripts or '4').strip()
        try:
            peripts = float(peripts_raw)
        except ValueError:
            peripts = 4.0
        meridians = (args.meridians or '').strip().lower()
        arcmodel = (args.arcmodel or '').strip() or None
        arcpts_raw = (args.arcpts or '4').strip()
        try:
            arcpts = float(arcpts_raw)
        except ValueError:
            arcpts = 4.0
        torus = (args.torus or '').strip().lower()
        labels = (args.labels or 'Small (6 points)').strip()
        moonpts_raw = (args.moonpts or '0').strip()
        try:
            moonpts = float(moonpts_raw)
        except ValueError:
            moonpts = 0.0
        standard = (args.standard or '').strip().lower()
        show_standard_stars = standard in {'yes', 'y', 'true', '1'}
        additional = (args.additional or '').strip().lower()
        extra_star: ExtraStar | None = None
        extra_ra = (args.extra_ra or '').strip()
        extra_dec = (args.extra_dec or '').strip()
        if additional in {'yes', 'y', 'true', '1'} and extra_ra and extra_dec:
            ra_type = (args.extra_ra_type or 'hours').strip().lower()
            is_hours = not ra_type.startswith('d')
            try:
                extra_star = ExtraStar(
                    name=(args.extra_name or '').strip(),
                    ra_deg=_parse_sexagesimal_to_degrees(extra_ra, is_ra_hours=is_hours),
                    dec_deg=_parse_sexagesimal_to_degrees(extra_dec, is_ra_hours=False),
                )
            except ValueError as e:
                logger.warning(
                    'Invalid extra star input (extra_name=%r, extra_ra=%r, extra_dec=%r, '
                    'is_hours=%s): %s',
                    args.extra_name,
                    extra_ra,
                    extra_dec,
                    is_hours,
                    e,
                )
                extra_star = None
        viewer_params = ViewerParams(
            planet_num=args.planet,
            time_str=args.time or '2025-01-01 12:00',
            fov_value=fov_value,
            fov_unit=fov_unit,
            center=center,
            observer=observer,
            ephem_version=args.ephem,
            moon_ids=moon_ids,
            ring_names=ring_names,
            blank_disks=blank in ('yes', 'y', 'true', '1'),
            opacity=opacity,
            labels=labels,
            moonpts=moonpts,
            peris=peris,
            peripts=peripts,
            meridians=meridians in ('yes', 'y', 'true', '1'),
            arcmodel=arcmodel,
            arcpts=arcpts,
            torus=torus in ('yes', 'y', 'true', '1'),
            torus_inc=float(args.torus_inc),
            torus_rad=float(args.torus_rad),
            show_standard_stars=show_standard_stars,
            extra_star=extra_star,
            other_bodies=[str(o) for o in (args.other or [])] or None,
            title=(args.title or '').strip(),
            output_ps=out,
            output_txt=out_txt,
        )
        write_input_parameters_viewer(sys.stdout, viewer_params)
        try:
            run_viewer(viewer_params)
        except (ValueError, RuntimeError) as e:
            print(f'Error: {e}', file=sys.stderr)
            return 1
        return 0


def cli_main() -> NoReturn:
    """Entry point for console_scripts; calls main() and exits with its return code."""
    sys.exit(main())


if __name__ == '__main__':
    sys.exit(main())
