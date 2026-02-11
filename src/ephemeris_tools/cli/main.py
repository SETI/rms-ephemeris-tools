"""CLI entry point: ephemeris-tools ephemeris|tracker|viewer subcommands."""

from __future__ import annotations

import argparse
import contextlib
import logging
import os
import sys
from typing import NoReturn, TextIO, cast

from ephemeris_tools.params import ephemeris_params_from_env


def _configure_logging(verbose: bool = False) -> None:
    """Configure logging so package warnings are visible. Call once at CLI startup."""
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
    """Run ephemeris generator. Params from CLI args or env (CGI)."""
    from ephemeris_tools.ephemeris import generate_ephemeris
    from ephemeris_tools.params import EphemerisParams

    if getattr(args, 'cgi', False):
        params = ephemeris_params_from_env()
        if params is None:
            print('Invalid or missing CGI parameters (e.g. NPLANET, start, stop).', file=sys.stderr)
            return 1
    else:
        moons_raw = args.moons or []
        moon_ids = [100 * args.planet + idx for idx in moons_raw] if moons_raw else []
        viewpoint = (args.viewpoint or 'observatory').strip() or 'observatory'
        observatory = (args.observatory or "Earth's Center").strip() or "Earth's Center"
        if viewpoint == 'latlon' and (args.latitude is not None or args.longitude is not None):
            lon = args.longitude
            if lon is not None and getattr(args, 'lon_dir', 'east') == 'west':
                lon = -lon
        else:
            lon = None
        params = EphemerisParams(
            planet_num=args.planet,
            start_time=args.start,
            stop_time=args.stop,
            interval=args.interval,
            time_unit=args.time_unit,
            ephem_version=getattr(args, 'ephem', 0),
            viewpoint=viewpoint,
            observatory=observatory,
            latitude_deg=args.latitude if viewpoint == 'latlon' else None,
            longitude_deg=lon if viewpoint == 'latlon' else None,
            lon_dir=getattr(args, 'lon_dir', 'east'),
            altitude_m=args.altitude if viewpoint == 'latlon' else None,
            sc_trajectory=getattr(args, 'sc_trajectory', 0),
            columns=args.columns or [1, 2, 3, 15, 8],
            mooncols=args.mooncols or [5, 6, 8, 9],
            moon_ids=moon_ids,
        )
        if viewpoint != 'latlon' and args.viewpoint and args.viewpoint != "Earth's Center":
            params.observatory = args.viewpoint or observatory

    from ephemeris_tools.input_params import write_input_parameters_ephemeris

    write_input_parameters_ephemeris(sys.stdout, params)

    out: TextIO = sys.stdout
    if getattr(args, 'output', None):
        with open(args.output, 'w') as f:
            generate_ephemeris(params, f)
        return 0
    try:
        generate_ephemeris(params, out)
        return 0
    except (ValueError, RuntimeError) as e:
        print(f'Error: {e}', file=sys.stderr)
        return 1


def main() -> int:
    """Entry point for ephemeris-tools CLI."""
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
        type=int,
        choices=[4, 5, 6, 7, 8, 9],
        default=6,
        help='Planet number (4=Mars..9=Pluto); env: NPLANET',
    )
    ephem_parser.add_argument(
        '--start', type=str, default='', help='Start time; env: start, START_TIME'
    )
    ephem_parser.add_argument(
        '--stop', type=str, default='', help='Stop time; env: stop, STOP_TIME'
    )
    ephem_parser.add_argument(
        '--interval', type=float, default=1.0, help='Time step; env: interval'
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
        '--columns', type=int, nargs='*', default=None, help='Column IDs; env: columns'
    )
    ephem_parser.add_argument(
        '--mooncols', type=int, nargs='*', default=None, help='Moon column IDs; env: mooncols'
    )
    ephem_parser.add_argument(
        '--moons', type=int, nargs='*', default=None, help='Moon indices (e.g. 1 2 3); env: moons'
    )
    ephem_parser.add_argument(
        '-o', '--output', type=str, default=None, help='Output file; env: EPHEM_FILE'
    )
    ephem_parser.add_argument('-v', '--verbose', action='store_true', help='Show INFO logs')
    ephem_parser.set_defaults(func=_ephemeris_cmd)

    track_parser = subparsers.add_parser('tracker', help='Moon tracker plot')
    track_parser.add_argument(
        '--planet', type=int, choices=[4, 5, 6, 7, 8, 9], default=6, help='Planet; env: NPLANET'
    )
    track_parser.add_argument('--start', type=str, default='', help='Start time; env: start')
    track_parser.add_argument('--stop', type=str, default='', help='Stop time; env: stop')
    track_parser.add_argument(
        '--interval', type=float, default=1.0, help='Time step; env: interval'
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
        '--moons', type=int, nargs='*', default=None, help='Moon indices (e.g. 1 2 3); env: moons'
    )
    track_parser.add_argument(
        '--rings',
        type=int,
        nargs='*',
        default=None,
        help='Ring options (e.g. 61 62 for Saturn); env: rings',
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
        '--planet', type=int, choices=[4, 5, 6, 7, 8, 9], default=6, help='Planet; env: NPLANET'
    )
    view_parser.add_argument('--time', type=str, default='', help='Observation time; env: time')
    view_parser.add_argument(
        '--ephem', type=int, default=0, help='Ephemeris version (0=latest); env: ephem'
    )
    view_parser.add_argument('--fov', type=float, default=1.0, help='Field of view; env: fov')
    view_parser.add_argument(
        '--fov-unit',
        type=str,
        default='deg',
        choices=['deg', 'arcmin', 'arcsec'],
        help='env: fov_unit',
    )
    view_parser.add_argument(
        '--center',
        type=str,
        default='body',
        choices=['body', 'ansa', 'J2000', 'star'],
        help='Diagram center; env: center',
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
        '--moons', type=int, nargs='*', default=None, help='Moon indices; env: moons'
    )
    view_parser.add_argument(
        '--moremoons', type=str, default=None, help='Additional moon selection; env: moremoons'
    )
    view_parser.add_argument(
        '--rings', type=int, nargs='*', default=None, help='Ring options; env: rings'
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
    _configure_logging(verbose=getattr(args, 'verbose', False))
    return cast(int, args.func(parser, args))


def _tracker_cmd(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    """Run moon tracker."""
    from ephemeris_tools.input_params import write_input_parameters_tracker
    from ephemeris_tools.tracker import run_tracker

    write_input_parameters_tracker(sys.stdout, args)

    moons_raw = args.moons or []
    moon_ids = [100 * args.planet + idx for idx in moons_raw] if moons_raw else []
    with contextlib.ExitStack() as stack:
        out_ps = (
            stack.enter_context(open(args.output, 'w')) if getattr(args, 'output', None) else None
        )
        out_txt = (
            stack.enter_context(open(args.output_txt, 'w'))
            if getattr(args, 'output_txt', None)
            else None
        )
        try:
            run_tracker(
                planet_num=args.planet,
                start_time=args.start or '2025-01-01 00:00',
                stop_time=args.stop or '2025-01-02 00:00',
                interval=getattr(args, 'interval', 1.0),
                time_unit=getattr(args, 'time_unit', 'hour'),
                viewpoint=(args.viewpoint or 'Earth').strip() or 'Earth',
                moon_ids=moon_ids,
                ephem_version=getattr(args, 'ephem', 0),
                xrange=getattr(args, 'xrange', None),
                xscaled=(getattr(args, 'xunit', 'arcsec') == 'radii'),
                title=(getattr(args, 'title', None) or '').strip(),
                ring_options=args.rings if getattr(args, 'rings', None) else None,
                output_ps=out_ps,
                output_txt=out_txt,
            )
        except (ValueError, RuntimeError) as e:
            print(f'Error: {e}', file=sys.stderr)
            return 1
    return 0


def _viewer_cmd(parser: argparse.ArgumentParser, args: argparse.Namespace) -> int:
    """Run planet viewer."""
    from ephemeris_tools.input_params import write_input_parameters_viewer
    from ephemeris_tools.viewer import run_viewer

    write_input_parameters_viewer(sys.stdout, args)

    with contextlib.ExitStack() as stack:
        out = stack.enter_context(open(args.output, 'w')) if getattr(args, 'output', None) else None
        out_txt = (
            stack.enter_context(open(args.output_txt, 'w'))
            if getattr(args, 'output_txt', None)
            else None
        )
        fov = getattr(args, 'fov', 1.0)
        fov_unit = getattr(args, 'fov_unit', 'deg')
        if fov_unit == 'arcmin':
            fov = fov / 60.0
        elif fov_unit == 'arcsec':
            fov = fov / 3600.0
        moon_ids = None
        if getattr(args, 'moons', None):
            moon_ids = [100 * args.planet + idx for idx in args.moons]
        blank = (getattr(args, 'blank', None) or '').strip().lower()
        blank_disks = blank in ('yes', 'y', 'true', '1')
        try:
            run_viewer(
                planet_num=args.planet,
                time_str=args.time or '2025-01-01 12:00',
                fov=fov,
                center_ra=getattr(args, 'center_ra', 0.0),
                center_dec=getattr(args, 'center_dec', 0.0),
                viewpoint=(args.viewpoint or 'Earth').strip() or 'Earth',
                ephem_version=getattr(args, 'ephem', 0),
                moon_ids=moon_ids,
                blank_disks=blank_disks,
                output_ps=out,
                output_txt=out_txt,
            )
        except (ValueError, RuntimeError) as e:
            print(f'Error: {e}', file=sys.stderr)
            return 1
        return 0


def cli_main() -> NoReturn:
    """Called from console_scripts; exits with return code."""
    sys.exit(main())


if __name__ == '__main__':
    sys.exit(main())
