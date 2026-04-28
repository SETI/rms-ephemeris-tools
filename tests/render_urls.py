"""Render CGI query URLs with both the MPL and Escher (PostScript) backends.

For each URL two PNG files are written to the output directory::

    NNN_<tool>_<planet>_<date>_mpl.png     – Matplotlib backend (direct PNG)
    NNN_<tool>_<planet>_<date>_escher.png  – PostScript backend → Ghostscript PNG

Intermediate ``.ps`` files are removed unless ``--keep-ps`` is given.

Only ``viewer`` and ``tracker`` URLs produce image output; ``ephemeris`` URLs
are skipped with a warning.

Usage examples::

    python tests/render_urls.py -o /tmp/renders \\
        "https://pds-rings.seti.org/cgi-bin/tools/viewer3_xxx.pl?abbrev=sat&time=2025-01-01+12:00"

    python tests/render_urls.py -f my_urls.txt -o /tmp/renders --dpi 200 --keep-ps

    # A path to an existing file is read like -f (URLs one per line):
    python tests/render_urls.py test_files/tracker-test-urls.txt -o /tmp/renders
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Re-use URL → RunSpec parsing from the compare_fortran harness.
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from tests.compare_fortran.__main__ import spec_from_query_input  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_PLANET_NAMES: dict[int, str] = {
    4: 'mars',
    5: 'jupiter',
    6: 'saturn',
    7: 'uranus',
    8: 'neptune',
    9: 'pluto',
}

_DPI_DEFAULT = 150


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _sanitize(text: str, maxlen: int = 20) -> str:
    """Replace non-alphanumeric characters with underscores; trim to *maxlen*."""
    return re.sub(r'[^a-zA-Z0-9]+', '_', text).strip('_')[:maxlen]


def _stem(index: int, spec: object) -> str:  # spec: RunSpec
    """Return a human-readable filename stem for *spec*."""
    p = spec.params  # type: ignore[attr-defined]
    tool = spec.tool  # type: ignore[attr-defined]
    planet = _PLANET_NAMES.get(int(p.get('planet', 6)), f"p{p.get('planet', 6)}")

    if tool == 'viewer':
        time_raw = str(p.get('time', '')).strip()
        date_part = _sanitize(time_raw[:16]) if time_raw else 'notime'
    else:
        start_raw = str(p.get('start', '')).strip()
        stop_raw = str(p.get('stop', '')).strip()
        if start_raw:
            date_part = _sanitize(start_raw[:10]) + '_' + _sanitize(stop_raw[:10])
        else:
            date_part = 'nodate'

    return f'{index:03d}_{tool}_{planet}_{date_part}'


def _render_ps_to_png(ps_path: Path, png_path: Path, *, dpi: int) -> bool:
    """Rasterize *ps_path* to *png_path* via Ghostscript.

    Returns ``True`` on success, ``False`` if Ghostscript is unavailable or
    the conversion fails.
    """
    gs_bin = shutil.which('gs')
    if gs_bin is None:
        print('  WARNING: Ghostscript (gs) not found on PATH; skipping Escher PNG.',
              file=sys.stderr)
        return False

    cmd = [
        gs_bin,
        '-dNOPAUSE',
        '-dBATCH',
        '-dQUIET',
        '-sDEVICE=png16m',
        f'-r{dpi}',
        f'-sOutputFile={png_path}',
        str(ps_path),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=120)
    except subprocess.TimeoutExpired:
        print(f'  WARNING: Ghostscript timed out rendering {ps_path.name}', file=sys.stderr)
        return False

    if result.returncode != 0:
        stderr = result.stderr.decode('utf-8', errors='replace').strip()
        print(f'  WARNING: Ghostscript failed for {ps_path.name}: {stderr[:300]}',
              file=sys.stderr)
        return False

    return png_path.exists()


def _run_tool(
    cli_args: list[str],
    *,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    """Invoke ``ephemeris_tools.cli.main`` as a subprocess."""
    cmd = [sys.executable, '-m', 'ephemeris_tools.cli.main'] + cli_args
    return subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        env=env if env is not None else os.environ.copy(),
        timeout=180,
    )


def _make_env() -> dict[str, str]:
    """Return an env dict with SPICE_PATH set if not already present."""
    env = os.environ.copy()
    try:
        from ephemeris_tools.config import get_spice_path  # noqa: PLC0415
        env.setdefault('SPICE_PATH', get_spice_path())
    except Exception:  # noqa: BLE001
        pass
    return env


# ---------------------------------------------------------------------------
# Per-URL renderer
# ---------------------------------------------------------------------------


def render_url(
    url: str,
    index: int,
    out_dir: Path,
    *,
    dpi: int,
    keep_ps: bool,
) -> tuple[bool, bool]:
    """Render *url* with both backends.

    Parameters:
        url: CGI query URL (viewer or tracker).
        index: 1-based position in the batch, used in the output filenames.
        out_dir: Directory where output files are written.
        dpi: Resolution for raster output.
        keep_ps: When ``True`` the intermediate ``.ps`` file is kept.

    Returns:
        ``(mpl_ok, escher_ok)`` — ``True`` for each backend that succeeded.
    """
    try:
        spec = spec_from_query_input(url)
    except Exception as exc:  # noqa: BLE001
        print(f'  ERROR: could not parse URL: {exc}', file=sys.stderr)
        return False, False

    if spec.tool == 'ephemeris':
        hint = ''
        u = url.strip()
        if u and not u.lower().startswith(('http://', 'https://')):
            hint = (
                ' If you meant a URL list file, pass -f FILE, or a path that '
                'exists (positional paths are read as URL lists).'
            )
        print(f'  SKIP: ephemeris tool produces no image output.{hint}', file=sys.stderr)
        return False, False

    stem = _stem(index, spec)
    base_args = spec.cli_args_for_python()
    env = _make_env()

    # --- MPL backend → PNG --------------------------------------------------
    mpl_png = out_dir / f'{stem}_mpl.png'
    mpl_args = base_args + ['--backend', 'mpl', '--dpi', str(dpi), '-o', str(mpl_png)]
    mpl_result = _run_tool(mpl_args, env=env)
    mpl_ok = mpl_result.returncode == 0 and mpl_png.exists()
    if mpl_ok:
        print(f'  mpl    → {mpl_png.name}')
    else:
        err = (mpl_result.stderr or '').strip()
        print(f'  ERROR mpl (rc={mpl_result.returncode}): {err[:2000]}', file=sys.stderr)

    # --- Escher backend → PS → Ghostscript → PNG ----------------------------
    escher_ps = out_dir / f'{stem}_escher.ps'
    escher_png = out_dir / f'{stem}_escher.png'
    escher_args = base_args + ['--backend', 'escher', '-o', str(escher_ps)]
    escher_result = _run_tool(escher_args, env=env)
    escher_ps_ok = escher_result.returncode == 0 and escher_ps.exists()

    if not escher_ps_ok:
        err = (escher_result.stderr or '').strip()
        print(f'  ERROR escher (rc={escher_result.returncode}): {err[:2000]}', file=sys.stderr)
        return mpl_ok, False

    escher_ok = _render_ps_to_png(escher_ps, escher_png, dpi=dpi)
    if escher_ok:
        print(f'  escher → {escher_png.name}')
        if not keep_ps:
            escher_ps.unlink(missing_ok=True)
    else:
        # Keep the .ps even without --keep-ps so the caller can inspect it.
        print(f'  NOTE: keeping {escher_ps.name} for inspection.', file=sys.stderr)

    return mpl_ok, escher_ok


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _read_url_file(path: Path) -> list[str]:
    """Return non-blank, non-comment lines from *path*."""
    lines: list[str] = []
    for raw in path.read_text(encoding='utf-8').splitlines():
        stripped = raw.strip()
        if stripped and not stripped.startswith('#'):
            lines.append(stripped)
    return lines


def _expand_positional_urls(tokens: list[str]) -> list[str]:
    """Expand positional tokens into URL strings.

    If a token is a path to an existing regular file, that file is read as a
    URL list (same format as ``-f``).  Otherwise the token is kept as a single
    URL string.  This matches the common invocation::

        python -m tests.render_urls path/to/urls.txt -o /tmp/out
    """
    out: list[str] = []
    for token in tokens:
        p = Path(token)
        if p.is_file():
            out.extend(_read_url_file(p))
        else:
            out.append(token)
    return out


def main(argv: list[str] | None = None) -> int:
    """Render CGI viewer and tracker URLs to image files for regression checks.

    Parses CLI arguments (positional URL tokens and/or ``-f``/``--url-file``,
    required ``-o``/``--outdir``, optional ``--dpi`` defaulting to ``_DPI_DEFAULT``,
    and ``--keep-ps``), expands positional paths that are files into URL lists,
    creates the output directory if missing, and for each URL writes MPL and
    Escher-derived PNGs (and optionally keeps intermediate PostScript).

    Parameters:
        argv: Command-line tokens without the program name; ``sys.argv[1:]``
            when ``None`` (handled by ``argparse``).

    Returns:
        Integer exit code (0 on success, non-zero when fatal errors occur).
    """
    parser = argparse.ArgumentParser(
        prog='render_urls',
        description='Render CGI viewer/tracker URLs with MPL and Escher (PS→PNG) backends.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        'urls',
        nargs='*',
        metavar='URL|FILE',
        help=(
            'CGI query URL(s), and/or path(s) to text files of URLs (one per line; '
            'same as -f when the path exists as a file).'
        ),
    )
    parser.add_argument(
        '-f', '--url-file',
        type=Path,
        metavar='FILE',
        help='File of URLs, one per line (# lines are comments).',
    )
    parser.add_argument(
        '-o', '--outdir',
        type=Path,
        required=True,
        metavar='DIR',
        help='Output directory; created if it does not exist.',
    )
    parser.add_argument(
        '--dpi',
        type=int,
        default=_DPI_DEFAULT,
        metavar='N',
        help=f'Resolution for raster output (default: {_DPI_DEFAULT}).',
    )
    parser.add_argument(
        '--keep-ps',
        action='store_true',
        help='Keep intermediate PostScript files alongside the PNGs.',
    )

    args = parser.parse_args(argv)

    urls: list[str] = _expand_positional_urls(list(args.urls))
    if args.url_file:
        urls.extend(_read_url_file(args.url_file))

    if not urls:
        parser.error('No URLs provided; pass them as positional arguments or use -f FILE.')

    args.outdir.mkdir(parents=True, exist_ok=True)

    n_mpl = n_escher = 0
    total = len(urls)

    for i, url in enumerate(urls, start=1):
        label = url if len(url) <= 120 else url[:117] + '...'
        print(f'[{i}/{total}] {label}')
        mpl_ok, escher_ok = render_url(
            url, i, args.outdir, dpi=args.dpi, keep_ps=args.keep_ps
        )
        if mpl_ok:
            n_mpl += 1
        if escher_ok:
            n_escher += 1

    print(
        f'\nDone: {total} URL(s) — '
        f'mpl {n_mpl}/{total} ok, escher {n_escher}/{total} ok.'
    )
    return 0 if (n_mpl == total and n_escher == total) else 1


if __name__ == '__main__':
    sys.exit(main())
