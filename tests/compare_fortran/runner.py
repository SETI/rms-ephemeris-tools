"""Run Python and FORTRAN with the same RunSpec and capture outputs."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs

from ephemeris_tools.config import get_spice_path
from tests.compare_fortran.spec import ABBREV_TO_PLANET, RunSpec


def _env_from_query_string(query_string: str) -> dict[str, str]:
    """Build CGI-style env from a query string to match parse_cgi.sh behavior.

    We do not run web/cgi-bin/tools/parse_cgi.sh; this replicates it so the
    test harness exercises the same env shape as real CGI.

    - Every param key from the query is present in env (do not skip empty
      values). Real CGI exports "$key"="$val" even when val is empty, so
      "present but empty" matches production and avoids bugs that depend on
      key in os.environ.
    - Multi-valued params (e.g. columns=1&columns=2) are stored as a single
      env var with values joined by '#' (e.g. columns=1#2), matching the
      second loop in parse_cgi.sh. Python params_env._get_keys_env() expects
      this #-joined form when reading multi-valued keys.
    - We do not set key#1, key#2, ... ; real CGI only exports the single
      key with #-joined value, so we match that to exercise the same code path.
    """
    parsed = parse_qs(query_string, keep_blank_values=True)
    env: dict[str, str] = {}
    for key, values in parsed.items():
        if not key:
            continue
        # Same as parse_cgi.sh: multi-valued params get #-joined; empty
        # values are still exported (use first value or '').
        env[key] = '#'.join(values) if values else ''
    return env


def run_python(
    spec: RunSpec,
    out_table: Path | None = None,
    out_ps: Path | None = None,
    out_txt: Path | None = None,
    python_exe: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run Python ephemeris-tools with the given spec; write table/PS to paths.

    Returns the CompletedProcess from subprocess.run. out_table used for
    ephemeris table; out_ps for tracker/viewer PostScript; out_txt for
    tracker text table or viewer FOV table when applicable.
    """
    env = os.environ.copy()
    env.setdefault('SPICE_PATH', get_spice_path())
    if spec.params.get('query_string'):
        query_string = str(spec.params['query_string'])
        env.update(_env_from_query_string(query_string))
        # FORTRAN requires xrange/xunit for tracker; inject defaults so both get same params.
        if spec.tool == 'tracker':
            if not (env.get('xrange') or '').strip():
                env['xrange'] = '180'
            if not (env.get('xunit') or '').strip():
                env['xunit'] = 'arcsec'

        # Match real CGI: shell scripts set NPLANET from abbrev (abbrev_to_planet)
        # and export it; the form sends abbrev=, not NPLANET. So when the query
        # contains abbrev, set NPLANET from it. spec.params['planet'] (e.g. from
        # spec_from_query_input) overrides when present.
        parsed = parse_qs(query_string, keep_blank_values=True)
        abbrev_vals = parsed.get('abbrev', [])
        abbrev_first = (abbrev_vals[0] or '').strip().lower()[:3] if abbrev_vals else ''
        if abbrev_first and abbrev_first in ABBREV_TO_PLANET:
            env['NPLANET'] = str(ABBREV_TO_PLANET[abbrev_first])
        if 'planet' in spec.params:
            try:
                env['NPLANET'] = str(int(spec.params['planet']))
            except (TypeError, ValueError) as e:
                raise ValueError(
                    f"spec.params['planet'] must be numeric, got {spec.params['planet']!r}"
                ) from e

        # Real CGI sets REQUEST_METHOD (e.g. GET); FORTRAN getcgivars and
        # Python may rely on it when comparing behavior.
        env.setdefault('REQUEST_METHOD', 'GET')

        if out_table and spec.tool == 'ephemeris':
            env['EPHEM_FILE'] = str(out_table)
        if out_ps and spec.tool == 'tracker':
            env['TRACKER_POSTFILE'] = str(out_ps)
        if out_txt and spec.tool == 'tracker':
            env['TRACKER_TEXTFILE'] = str(out_txt)
        if out_ps and spec.tool == 'viewer':
            env['VIEWER_POSTFILE'] = str(out_ps)
        if out_txt and spec.tool == 'viewer':
            env['VIEWER_TEXTFILE'] = str(out_txt)
        cmd = [python_exe or sys.executable, '-m', 'ephemeris_tools.cli.main', spec.tool, '--cgi']
    else:
        cmd = [python_exe or sys.executable, '-m', 'ephemeris_tools.cli.main']
        cmd.extend(spec.cli_args_for_python())
        if out_table and spec.tool == 'ephemeris':
            cmd.extend(['-o', str(out_table)])
        if out_ps and spec.tool == 'tracker':
            cmd.extend(['-o', str(out_ps)])
            if out_txt:
                cmd.extend(['--output-txt', str(out_txt)])
        if out_ps and spec.tool == 'viewer':
            cmd.extend(['-o', str(out_ps)])
            if out_txt:
                cmd.extend(['--output-txt', str(out_txt)])
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )


def run_fortran(
    spec: RunSpec,
    fortran_cmd: list[str] | str,
    out_table: Path | None = None,
    out_ps: Path | None = None,
    out_txt: Path | None = None,
    env_extra: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Run FORTRAN with env set from spec; output paths set in env.

    fortran_cmd: executable (and args) to run, e.g. ["/path/to/ephem3_xxx.bin"]
    or "EPHEM_FILE=/tmp/out.tab /path/to/ephem3_xxx.bin". If a list, env is
    set from spec and output paths. If a single string, it is run with sh -c
    after setting env (so you can use $EPHEM_FILE in the string).
    """
    env = os.environ.copy()
    # Ensure FORTRAN uses same SPICE_PATH as Python for identical kernel loading
    env.setdefault('SPICE_PATH', get_spice_path())
    table_path = str(out_table) if out_table else ''
    ps_path = str(out_ps) if out_ps else ''
    txt_path = str(out_txt) if out_txt else ''
    fortran_env = spec.env_for_fortran(table_path=table_path or None, ps_path=ps_path or None)
    if spec.tool == 'tracker' and txt_path:
        fortran_env['TRACKER_TEXTFILE'] = txt_path
    if spec.tool == 'viewer' and txt_path:
        fortran_env['VIEWER_TEXTFILE'] = txt_path
    env.update(fortran_env)
    if env_extra:
        env.update(env_extra)
    if isinstance(fortran_cmd, str):
        return subprocess.run(
            ['sh', '-c', fortran_cmd],
            capture_output=True,
            text=True,
            env=env,
            timeout=120,
        )
    return subprocess.run(
        fortran_cmd,
        capture_output=True,
        text=True,
        env=env,
        timeout=120,
    )
