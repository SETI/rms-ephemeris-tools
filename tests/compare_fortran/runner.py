"""Run Python and FORTRAN with the same RunSpec and capture outputs."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from tests.compare_fortran.spec import RunSpec


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
    cmd = [python_exe or sys.executable, '-m', 'ephemeris_tools.cli.main']
    cmd.extend(spec.cli_args_for_python())
    env = os.environ.copy()
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
