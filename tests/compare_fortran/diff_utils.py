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
    max_abs_diff: float | None = None


def _normalize_table_line(line: str) -> str:
    """Normalize a table line for comparison: strip, collapse whitespace."""
    return ' '.join(line.strip().split())


def _normalize_table_content(text: str) -> list[str]:
    """Split into lines, normalize each, drop empty."""
    return [_normalize_table_line(ln) for ln in text.splitlines() if _normalize_table_line(ln)]


def _is_fortran_overflow_token(token: str) -> bool:
    """Return True when token is a FORTRAN fixed-width overflow marker."""

    return bool(token) and set(token) == {'*'}


def _lsd_from_printed(s: str) -> float:
    """Infer least-significant-digit magnitude from the printed form.

    E.g. "1.001" -> 0.001, "10.5" -> 0.1, "7" -> 1, "5.0523E+09" -> 100000.
    Used for LSD-based tolerance: values match if |a-b| <= lsd_units * lsd.
    """
    s = s.strip()
    sci = re.match(r'^([+-]?\d*\.?\d+)[eE]([+-]?\d+)$', s)
    if sci:
        mantissa = sci.group(1)
        exponent = int(sci.group(2))
        if '.' in mantissa:
            dec_places = len(mantissa.split('.')[1])
        else:
            dec_places = 0
        return 10.0 ** (exponent - dec_places)
    if '.' in s:
        dec_places = len(s.split('.')[1])
        return 10.0 ** (-dec_places)
    return 1.0


def _fields_match(
    field_a: str,
    field_b: str,
    *,
    float_tolerance: int | None,
    abs_tolerance: float | None,
    lsd_tolerance: float | None,
) -> bool:
    """Compare one normalized table field.

    The second field is treated as FORTRAN output. If it is an overflow token
    (all asterisks), the field is considered uncomparable and therefore ignored.

    When lsd_tolerance is set, values match if |a-b| <= lsd_tolerance * lsd, where
    lsd is inferred from the printed form (e.g. 1.001 -> lsd=0.001, 10.5 -> 0.1).
    """
    if _is_fortran_overflow_token(field_b):
        return True
    if field_a == field_b:
        return True
    try:
        fa = float(field_a)
        fb = float(field_b)
    except ValueError:
        return False
    if lsd_tolerance is not None:
        lsd = _lsd_from_printed(field_a)
        threshold = lsd_tolerance * lsd
        # Add tiny epsilon to absorb float representation noise (e.g. 12.27-12.269)
        if abs(fa - fb) <= threshold + 1e-12 * max(abs(fa), abs(fb), 1.0):
            return True
    if abs_tolerance is not None and abs(fa - fb) <= abs_tolerance:
        return True
    if float_tolerance is not None:
        return f'{fa:.{float_tolerance}g}' == f'{fb:.{float_tolerance}g}'
    return False


def _lines_match_fields(
    line_a: str,
    line_b: str,
    *,
    float_tolerance: int | None,
    abs_tolerance: float | None,
    lsd_tolerance: float | None = None,
) -> bool:
    """Compare normalized lines field-by-field with FORTRAN overflow handling."""

    fields_a = line_a.split()
    fields_b = line_b.split()
    if len(fields_a) != len(fields_b):
        return False
    for field_a, field_b in zip(fields_a, fields_b, strict=True):
        if not _fields_match(
            field_a,
            field_b,
            float_tolerance=float_tolerance,
            abs_tolerance=abs_tolerance,
            lsd_tolerance=lsd_tolerance,
        ):
            return False
    return True


def compare_tables(
    path_a: Path | str,
    path_b: Path | str,
    ignore_blank: bool = True,
    float_tolerance: int | None = None,
    abs_tolerance: float | None = None,
    lsd_tolerance: float | None = None,
    ignore_column_suffixes: tuple[str, ...] | None = None,
) -> CompareResult:
    """Compare two table (text) files line-by-line.

    If float_tolerance is set (e.g. 6), numeric fields are compared only
    to that many significant digits. Otherwise exact string match after
    normalization (strip, collapse whitespace).

    If lsd_tolerance is set (e.g. 1), numeric fields match when their
    difference is <= lsd_tolerance * lsd, where lsd is the magnitude of
    the least significant digit in the printed form. E.g. 1.001 with
    lsd_tolerance=1 allows ±0.001; 10.5 allows ±0.1; 7 allows ±1.

    If abs_tolerance is set (and lsd_tolerance is not), numeric fields
    match when |a-b| <= abs_tolerance. Kept for backward compatibility.

    If ignore_column_suffixes is set (e.g. ("_orbit", "_open")), the first
    line is treated as a header; when comparing data lines, fields whose
    header column name ends with any of these suffixes are ignored (known
    FORTRAN bugs). Use for ephemeris table comparison when moon columns
    include orbit/open.
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
    max_abs_diff: float | None = None

    if ignore_column_suffixes and lines_a and lines_b:
        # Column-aware: parse header, compare field-by-field skipping ignored columns.
        num_diffs, details, max_abs_diff = _compare_tables_column_aware(
            lines_a,
            lines_b,
            ignore_column_suffixes,
            float_tolerance,
            abs_tolerance,
            lsd_tolerance,
            details,
        )
    else:
        if len(lines_a) != len(lines_b):
            num_diffs += 1
            details.append(f'  Line count: Python {len(lines_a)}, FORTRAN {len(lines_b)}')
        else:
            for i, (la, lb) in enumerate(zip(lines_a, lines_b, strict=True)):
                line_max = _line_max_abs_diff(la, lb)
                if line_max is not None:
                    max_abs_diff = line_max if max_abs_diff is None else max(max_abs_diff, line_max)
                if _lines_match_fields(
                    la,
                    lb,
                    float_tolerance=float_tolerance,
                    abs_tolerance=abs_tolerance,
                    lsd_tolerance=lsd_tolerance,
                ):
                    continue
                if la != lb:
                    num_diffs += 1
                    if len(details) < 50:
                        details.append(f'  Line {i + 1}:')
                        details.append(f'    Python:  {la[:100]}{"..." if len(la) > 100 else ""}')
                        details.append(f'    FORTRAN: {lb[:100]}{"..." if len(lb) > 100 else ""}')
    same = num_diffs == 0
    message = 'Tables match' if same else f'Tables differ ({num_diffs} difference(s))'
    if max_abs_diff is not None:
        message = f'{message}; max_abs_diff={max_abs_diff:.6g}'
    return CompareResult(
        same=same,
        message=message,
        details=details,
        num_diffs=num_diffs,
        max_abs_diff=max_abs_diff,
    )


def _compare_tables_column_aware(
    lines_a: list[str],
    lines_b: list[str],
    ignore_suffixes: tuple[str, ...],
    float_tolerance: int | None,
    abs_tolerance: float | None,
    lsd_tolerance: float | None,
    details: list[str],
) -> tuple[int, list[str], float | None]:
    """Compare tables line-by-line, ignoring columns whose header ends with given suffixes."""
    num_diffs = 0
    max_abs_diff: float | None = None
    if len(lines_a) != len(lines_b):
        num_diffs += 1
        details.append(f'  Line count: Python {len(lines_a)}, FORTRAN {len(lines_b)}')
        return num_diffs, details, max_abs_diff
    header_a = lines_a[0].split()
    header_b = lines_b[0].split()
    if len(header_a) != len(header_b):
        num_diffs += 1
        details.append(f'  Column count: Python {len(header_a)}, FORTRAN {len(header_b)}')
        return num_diffs, details, max_abs_diff
    ignore_indexes = {
        i for i, name in enumerate(header_a) if any(name.endswith(s) for s in ignore_suffixes)
    }
    for i, (la, lb) in enumerate(zip(lines_a, lines_b, strict=True)):
        if i == 0:
            if la != lb:
                num_diffs += 1
                if len(details) < 50:
                    details.append('  Line 1 (header):')
                    details.append(f'    Python:  {la[:100]}{"..." if len(la) > 100 else ""}')
                    details.append(f'    FORTRAN: {lb[:100]}{"..." if len(lb) > 100 else ""}')
            continue
        fields_a = la.split()
        fields_b = lb.split()
        if len(fields_a) != len(header_a) or len(fields_b) != len(header_b):
            num_diffs += 1
            if len(details) < 50:
                details.append(f'  Line {i + 1}: field count mismatch')
            continue
        for j in range(len(fields_a)):
            if j in ignore_indexes:
                continue
            diff = _field_abs_diff(fields_a[j], fields_b[j])
            if diff is not None:
                max_abs_diff = diff if max_abs_diff is None else max(max_abs_diff, diff)
            if not _fields_match(
                fields_a[j],
                fields_b[j],
                float_tolerance=float_tolerance,
                abs_tolerance=abs_tolerance,
                lsd_tolerance=lsd_tolerance,
            ):
                num_diffs += 1
                if len(details) < 50:
                    details.append(f'  Line {i + 1} col {j + 1} ({header_a[j]}):')
                    details.append(f'    Python:  {fields_a[j]}, FORTRAN: {fields_b[j]}')
    return num_diffs, details, max_abs_diff


def _field_abs_diff(field_a: str, field_b: str) -> float | None:
    """Return absolute numeric difference for one field, or None if not numeric/comparable."""

    if _is_fortran_overflow_token(field_b):
        return None
    try:
        return abs(float(field_a) - float(field_b))
    except ValueError:
        return None


def _line_max_abs_diff(line_a: str, line_b: str) -> float | None:
    """Return max numeric field diff on a line, excluding FORTRAN overflow fields."""

    fields_a = line_a.split()
    fields_b = line_b.split()
    if len(fields_a) != len(fields_b):
        return None
    max_diff: float | None = None
    for field_a, field_b in zip(fields_a, fields_b, strict=True):
        diff = _field_abs_diff(field_a, field_b)
        if diff is not None:
            max_diff = diff if max_diff is None else max(max_diff, diff)
    return max_diff


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
    """Normalize PostScript for comparison: drop comments that vary, normalize whitespace.

    When normalize_creator_date is True, also strips body-level PostScript string
    tokens of the form "(Generated by the …)" (PS strings, not DSC comments);
    removal is silent and conditional on normalize_creator_date.
    """
    out: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if normalize_creator_date and s.startswith('(Generated by the ') and s.endswith(')'):
            continue
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


def _postscript_lines_match(
    la: str,
    lb: str,
    *,
    numeric_tolerance: float = 0.02,
    pixel_tolerance: float = 2.0,
) -> bool:
    """Compare two PostScript lines; numeric tokens may differ within tolerance.

    numeric_tolerance: for floating-point values (e.g. plot coordinates).
    pixel_tolerance: for integer-like values (pixel/position coords); allows
        differences of 1-2 pixels to be ignored.
    """
    if la == lb:
        return True
    tokens_a = la.split()
    tokens_b = lb.split()
    if len(tokens_a) != len(tokens_b):
        return False
    for ta, tb in zip(tokens_a, tokens_b, strict=True):
        if ta == tb:
            continue
        try:
            fa, fb = float(ta), float(tb)
            diff = abs(fa - fb)
            tol = numeric_tolerance
            # Integer-like values (e.g. pixel positions): allow 1-2 pixel drift
            if abs(fa - round(fa)) < 1e-6 and abs(fb - round(fb)) < 1e-6:
                tol = max(tol, pixel_tolerance)
            if diff <= tol:
                continue
        except ValueError:
            pass
        return False
    return True


def compare_postscript(
    path_a: Path | str,
    path_b: Path | str,
    normalize_creator_date: bool = True,
    numeric_tolerance: float = 0.05,
    pixel_tolerance: float = 2.0,
) -> CompareResult:
    """Compare two PostScript files with optional normalization of variable headers.

    When normalize_creator_date is True, the following are ignored so only
    structural and drawing differences are reported: %%Creator, %%CreationDate,
    %%Title, and body-level PostScript strings of the form "(Generated by the …)"
    (PS string tokens, not DSC comments). The removal is silent and conditional
    on normalize_creator_date.

    numeric_tolerance: numeric fields may differ by this amount (e.g. 0.05 for
    tracker plot coordinates and axis labels affected by time-library differences).
    pixel_tolerance: integer-like values (pixel positions) may differ by up to
    this amount; allows 1-2 pixel drift to be ignored.
    """
    pa = Path(path_a)
    pb = Path(path_b)
    if not pa.exists():
        return CompareResult(False, f'File not found: {pa}', [], 0)
    if not pb.exists():
        return CompareResult(False, f'File not found: {pb}', [], 0)

    def _read_ps(path: Path) -> str:
        return path.read_text(encoding='utf-8', errors='replace')

    lines_a = _normalize_postscript(_read_ps(pa), normalize_creator_date)
    lines_b = _normalize_postscript(_read_ps(pb), normalize_creator_date)
    details: list[str] = []
    num_diffs = 0
    if len(lines_a) != len(lines_b):
        num_diffs += 1
        details.append(f'  Line count: Python {len(lines_a)}, FORTRAN {len(lines_b)}')
    else:
        for i, (la, lb) in enumerate(zip(lines_a, lines_b, strict=True)):
            if not _postscript_lines_match(
                la,
                lb,
                numeric_tolerance=numeric_tolerance,
                pixel_tolerance=pixel_tolerance,
            ):
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
    ignore_axis_pixels: bool = False,
    min_similarity_pct: float | None = None,
) -> CompareResult:
    """Render two PostScript files to PNG and pixel-compare the images.

    Uses Ghostscript to rasterize both files at the given DPI, then
    computes pixel-level similarity metrics over the comparison region.
    When ignore_axis_pixels is True (e.g. viewer), only pixels outside
    the axis mask are used (axis anti-mask). Optionally writes a diff
    image highlighting changed pixels.

    Parameters:
        path_a: Path to the first PostScript file (Python output).
        path_b: Path to the second PostScript file (FORTRAN output).
        dpi: Resolution for Ghostscript rendering.
        diff_image_path: If set, write a diff image to this path.
        ignore_axis_pixels: If True, exclude axis/tick regions from the
            comparison; similarity is computed only over the content
            (anti-mask) pixels.
        min_similarity_pct: If set, pass when similarity >= this value
            (percent). Otherwise pass only when 100% identical.

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
    ignore_mask = np.zeros(pixel_max_diff.shape, dtype=bool)
    if ignore_axis_pixels:
        # Viewer-only relaxation: ignore differences around axis lines and tick marks.
        # Detect strong shared horizontal/vertical line features in both renderings.
        dark_a = np.all(arr_a <= 80, axis=2)
        dark_b = np.all(arr_b <= 80, axis=2)
        common_dark = dark_a & dark_b
        row_counts = common_dark.sum(axis=1)
        col_counts = common_dark.sum(axis=0)
        footer_search_start = round(0.92 * h)
        row_thresh = max(200, int(0.20 * w))
        col_thresh = max(200, int(0.20 * h))
        row_candidates = np.where(row_counts >= row_thresh)[0]
        col_candidates = np.where(col_counts >= col_thresh)[0]
        if row_candidates.size >= 2 and col_candidates.size >= 2:
            top = int(row_candidates[0])
            bottom = int(row_candidates[-1])
            left = int(col_candidates[0])
            right = int(col_candidates[-1])
            band = max(3, round(dpi / 24))  # ~6 px at 150 dpi
            tick_pad = max(8, round(dpi / 10))  # ~15 px at 150 dpi
            y0 = max(0, top - band - tick_pad)
            y1 = min(h, top + band + tick_pad + 1)
            y2 = max(0, bottom - band - tick_pad)
            y3 = min(h, bottom + band + tick_pad + 1)
            x0 = max(0, left - band - tick_pad)
            x1 = min(w, left + band + tick_pad + 1)
            x2 = max(0, right - band - tick_pad)
            x3 = min(w, right + band + tick_pad + 1)
            ignore_mask[y0:y1, :] = True
            ignore_mask[y2:y3, :] = True
            ignore_mask[:, x0:x1] = True
            ignore_mask[:, x2:x3] = True
            footer_search_start = max(
                footer_search_start,
                bottom + tick_pad + band + max(4, round(dpi / 8)),
            )
            details.append(
                '  Axis mask: enabled '
                f'(rows {top},{bottom}; cols {left},{right}; ~{int(ignore_mask.sum()):,} px)'
            )
        else:
            details.append('  Axis mask: enabled but axis lines not detected; no mask applied')
        # Ignore the "Generated by..." footer text band.
        # The footer is near the bottom but not at the very last rows, so detect
        # a common dark text band in the lower image region and mask that strip.
        footer_search_start = min(footer_search_start, h - 1)
        footer_row_counts = common_dark[footer_search_start:, :].sum(axis=1)
        footer_row_thresh = max(10, round(0.01 * w))
        footer_candidates = np.where(footer_row_counts >= footer_row_thresh)[0]
        if footer_candidates.size > 0:
            footer_top = footer_search_start + int(footer_candidates[0])
            footer_bottom = footer_search_start + int(footer_candidates[-1])
            footer_pad = max(4, round(dpi / 20))
            fy0 = max(0, footer_top - footer_pad)
            fy1 = min(h, footer_bottom + footer_pad + 1)
            ignore_mask[fy0:fy1, :] = True
            details.append(
                f'  Footer mask: rows {footer_top}-{footer_bottom} '
                f'(padded to {fy0}-{fy1 - 1}; Generated by...)'
            )
        else:
            footer_rows = max(25, round(dpi / 4))
            ignore_mask[h - footer_rows : h, :] = True
            details.append(f'  Footer mask: fallback bottom {footer_rows} rows (Generated by...)')

    valid_mask = ~ignore_mask
    total_pixels = int(np.sum(valid_mask))
    if total_pixels == 0:
        return CompareResult(
            False,
            'Image comparison failed: axis mask excluded all pixels',
            details,
        )

    identical_pixels = int(np.sum((pixel_max_diff == 0) & valid_mask))
    similarity_pct = 100.0 * identical_pixels / total_pixels
    mean_diff = float(diff[valid_mask].mean())
    max_diff = int(diff[valid_mask].max())

    # Count pixels by severity
    minor_pixels = int(np.sum((pixel_max_diff > 0) & (pixel_max_diff <= 10) & valid_mask))
    moderate_pixels = int(np.sum((pixel_max_diff > 10) & (pixel_max_diff <= 50) & valid_mask))
    major_pixels = int(np.sum((pixel_max_diff > 50) & valid_mask))

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

    if min_similarity_pct is not None:
        same = similarity_pct >= min_similarity_pct
    else:
        same = identical_pixels == total_pixels
    msg = (
        f'Images identical ({total_pixels:,} pixels)'
        if identical_pixels == total_pixels
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
