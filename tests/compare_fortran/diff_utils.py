"""Compare table and PostScript outputs from Python vs FORTRAN."""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class CompareResult:
    """Result of comparing two files."""

    same: bool
    message: str = ''
    details: list[str] = field(default_factory=list)
    num_diffs: int = 0


def _normalize_table_line(line: str) -> str:
    """Normalize a table line for comparison: strip, collapse whitespace."""
    return ' '.join(line.strip().split())


def _normalize_table_content(text: str) -> list[str]:
    """Split into lines, normalize each, drop empty."""
    return [_normalize_table_line(ln) for ln in text.splitlines() if _normalize_table_line(ln)]


def compare_tables(
    path_a: Path | str,
    path_b: Path | str,
    ignore_blank: bool = True,
    float_tolerance: int | None = None,
) -> CompareResult:
    """Compare two table (text) files line-by-line.

    If float_tolerance is set (e.g. 6), numeric fields are compared only
    to that many significant digits. Otherwise exact string match after
    normalization (strip, collapse whitespace).
    """
    pa = Path(path_a)
    pb = Path(path_b)
    if not pa.exists():
        return CompareResult(False, f'File not found: {pa}', [], 0)
    if not pb.exists():
        return CompareResult(False, f'File not found: {pb}', [], 0)
    lines_a = _normalize_table_content(pa.read_text())
    lines_b = _normalize_table_content(pb.read_text())
    if ignore_blank:
        lines_a = [ln for ln in lines_a if ln.strip()]
        lines_b = [ln for ln in lines_b if ln.strip()]
    details: list[str] = []
    num_diffs = 0
    if len(lines_a) != len(lines_b):
        num_diffs += 1
        details.append(f'  Line count: Python {len(lines_a)}, FORTRAN {len(lines_b)}')
    else:
        for i, (la, lb) in enumerate(zip(lines_a, lines_b, strict=True)):
            if float_tolerance is not None and _lines_match_numeric(la, lb, float_tolerance):
                continue
            if la != lb:
                num_diffs += 1
                if len(details) < 50:
                    details.append(f'  Line {i + 1}:')
                    details.append(f'    Python:  {la[:100]}{"..." if len(la) > 100 else ""}')
                    details.append(f'    FORTRAN: {lb[:100]}{"..." if len(lb) > 100 else ""}')
    same = num_diffs == 0
    return CompareResult(
        same=same,
        message='Tables match' if same else f'Tables differ ({num_diffs} difference(s))',
        details=details,
        num_diffs=num_diffs,
    )


def _lines_match_numeric(line_a: str, line_b: str, sig: int) -> bool:
    """True if lines match when numeric fields are rounded to sig digits."""

    def replace_floats(s: str) -> str:
        def repl(m: re.Match[str]) -> str:
            try:
                f = float(m.group(0))
                return f'{f:.{sig}g}'
            except ValueError:
                return m.group(0)

        return re.sub(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?', repl, s)

    return replace_floats(line_a) == replace_floats(line_b)


def _normalize_postscript(text: str, normalize_creator_date: bool = True) -> list[str]:
    """Normalize PostScript for comparison: drop comments that vary, normalize whitespace."""
    out: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith('%%'):
            if normalize_creator_date and (
                s.startswith('%%Creator')
                or s.startswith('%%CreationDate')
                or s.startswith('%%Title')
            ):
                continue
            if s:
                out.append(s)
            continue
        out.append(' '.join(s.split()))
    return out


def compare_postscript(
    path_a: Path | str,
    path_b: Path | str,
    normalize_creator_date: bool = True,
) -> CompareResult:
    """Compare two PostScript files with optional normalization of variable headers.

    When normalize_creator_date is True, %%Creator, %%CreationDate, and
    %%Title are ignored so only structural and drawing differences are reported.
    """
    pa = Path(path_a)
    pb = Path(path_b)
    if not pa.exists():
        return CompareResult(False, f'File not found: {pa}', [], 0)
    if not pb.exists():
        return CompareResult(False, f'File not found: {pb}', [], 0)
    lines_a = _normalize_postscript(pa.read_text(), normalize_creator_date)
    lines_b = _normalize_postscript(pb.read_text(), normalize_creator_date)
    details: list[str] = []
    num_diffs = 0
    if len(lines_a) != len(lines_b):
        num_diffs += 1
        details.append(f'  Line count: Python {len(lines_a)}, FORTRAN {len(lines_b)}')
    else:
        for i, (la, lb) in enumerate(zip(lines_a, lines_b, strict=True)):
            if la != lb:
                num_diffs += 1
                if len(details) < 30:
                    details.append(f'  Line {i + 1}:')
                    details.append(f'    Python:  {la[:80]}{"..." if len(la) > 80 else ""}')
                    details.append(f'    FORTRAN: {lb[:80]}{"..." if len(lb) > 80 else ""}')
    same = num_diffs == 0
    return CompareResult(
        same=same,
        message='PostScript match' if same else f'PostScript differ ({num_diffs} difference(s))',
        details=details,
        num_diffs=num_diffs,
    )


def _render_ps_to_png(ps_path: Path, png_path: Path, *, dpi: int = 150) -> bool:
    """Render a PostScript file to PNG using Ghostscript.

    Returns True on success, False if Ghostscript is unavailable or fails.
    """
    gs_bin = shutil.which('gs')
    if gs_bin is None:
        logger.warning('Ghostscript (gs) not found on PATH; skipping image comparison')
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
        result = subprocess.run(cmd, capture_output=True, timeout=60)
    except subprocess.TimeoutExpired:
        logger.warning('Ghostscript timed out rendering %s', ps_path)
        return False
    if result.returncode != 0:
        stderr = result.stderr.decode('utf-8', errors='replace').strip()
        logger.warning('Ghostscript failed for %s: %s', ps_path, stderr[:200])
        return False
    return png_path.exists()


def compare_postscript_images(
    path_a: Path | str,
    path_b: Path | str,
    *,
    dpi: int = 150,
    diff_image_path: Path | str | None = None,
) -> CompareResult:
    """Render two PostScript files to PNG and pixel-compare the images.

    Uses Ghostscript to rasterize both files at the given DPI, then
    computes pixel-level similarity metrics. Optionally writes a diff
    image highlighting changed pixels.

    Parameters:
        path_a: Path to the first PostScript file (Python output).
        path_b: Path to the second PostScript file (FORTRAN output).
        dpi: Resolution for Ghostscript rendering.
        diff_image_path: If set, write a diff image to this path.

    Returns:
        CompareResult with similarity percentage and pixel statistics.
    """
    try:
        import numpy as np
        from PIL import Image
    except ImportError as exc:
        return CompareResult(
            same=False,
            message=f'Image comparison unavailable: {exc}',
        )

    pa = Path(path_a)
    pb = Path(path_b)
    if not pa.exists():
        return CompareResult(False, f'File not found: {pa}')
    if not pb.exists():
        return CompareResult(False, f'File not found: {pb}')

    # Render both PS files to temporary PNGs alongside the originals
    png_a = pa.with_suffix('.png')
    png_b = pb.with_suffix('.png')

    if not _render_ps_to_png(pa, png_a, dpi=dpi):
        return CompareResult(False, f'Failed to render {pa} to PNG (is Ghostscript installed?)')
    if not _render_ps_to_png(pb, png_b, dpi=dpi):
        return CompareResult(False, f'Failed to render {pb} to PNG (is Ghostscript installed?)')

    img_a = Image.open(png_a).convert('RGB')
    img_b = Image.open(png_b).convert('RGB')

    details: list[str] = []
    details.append(f'  Python image:  {img_a.size[0]}x{img_a.size[1]} px ({dpi} dpi)')
    details.append(f'  FORTRAN image: {img_b.size[0]}x{img_b.size[1]} px ({dpi} dpi)')

    # Pad smaller image to match dimensions if they differ
    w = max(img_a.size[0], img_b.size[0])
    h = max(img_a.size[1], img_b.size[1])
    if img_a.size != (w, h) or img_b.size != (w, h):
        details.append(f'  Images differ in size; padding to {w}x{h} for comparison')
        canvas_a = Image.new('RGB', (w, h), (255, 255, 255))
        canvas_b = Image.new('RGB', (w, h), (255, 255, 255))
        canvas_a.paste(img_a, (0, 0))
        canvas_b.paste(img_b, (0, 0))
        arr_a = np.array(canvas_a, dtype=np.int16)
        arr_b = np.array(canvas_b, dtype=np.int16)
    else:
        arr_a = np.array(img_a, dtype=np.int16)
        arr_b = np.array(img_b, dtype=np.int16)

    # Compute pixel-level differences
    diff = np.abs(arr_a - arr_b)  # shape (H, W, 3), values 0-255
    pixel_max_diff = diff.max(axis=2)  # max channel difference per pixel
    total_pixels = pixel_max_diff.size

    identical_pixels = int(np.sum(pixel_max_diff == 0))
    similarity_pct = 100.0 * identical_pixels / total_pixels
    mean_diff = float(diff.mean())
    max_diff = int(diff.max())

    # Count pixels by severity
    minor_pixels = int(np.sum((pixel_max_diff > 0) & (pixel_max_diff <= 10)))
    moderate_pixels = int(np.sum((pixel_max_diff > 10) & (pixel_max_diff <= 50)))
    major_pixels = int(np.sum(pixel_max_diff > 50))

    details.append(f'  Total pixels:    {total_pixels:,}')
    details.append(f'  Identical:       {identical_pixels:,} ({similarity_pct:.4f}%)')
    details.append(f'  Minor (1-10):    {minor_pixels:,}')
    details.append(f'  Moderate (11-50): {moderate_pixels:,}')
    details.append(f'  Major (>50):     {major_pixels:,}')
    details.append(f'  Mean diff:       {mean_diff:.4f} (per channel per pixel)')
    details.append(f'  Max diff:        {max_diff}')

    # Optionally write a diff image
    diff_path_use = Path(diff_image_path) if diff_image_path else None
    if diff_path_use is not None:
        # Scale differences to be visible: amplify by 4x, cap at 255
        diff_vis = np.minimum(diff * 4, 255).astype(np.uint8)
        # Make unchanged pixels white, changed pixels show in red channel
        diff_img = Image.new('RGB', (w, h), (255, 255, 255))
        diff_arr = np.array(diff_img)
        mask = pixel_max_diff > 0
        # Red channel = amplified diff, green/blue = 0 for changed pixels
        diff_arr[mask, 0] = 255
        diff_arr[mask, 1] = 255 - diff_vis[mask].max(axis=1)
        diff_arr[mask, 2] = 255 - diff_vis[mask].max(axis=1)
        Image.fromarray(diff_arr).save(diff_path_use)
        details.append(f'  Diff image:      {diff_path_use}')

    same = identical_pixels == total_pixels
    msg = (
        f'Images identical ({total_pixels:,} pixels)'
        if same
        else (
            f'Images {similarity_pct:.4f}% similar'
            f' ({total_pixels - identical_pixels:,} of {total_pixels:,} pixels differ)'
        )
    )
    return CompareResult(
        same=same,
        message=msg,
        details=details,
        num_diffs=total_pixels - identical_pixels,
    )
