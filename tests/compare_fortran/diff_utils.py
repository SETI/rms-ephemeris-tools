"""Compare table and PostScript outputs from Python vs FORTRAN."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CompareResult:
    """Result of comparing two files."""

    same: bool
    message: str = ""
    details: list[str] = field(default_factory=list)
    num_diffs: int = 0


def _normalize_table_line(line: str) -> str:
    """Normalize a table line for comparison: strip, collapse whitespace."""
    return " ".join(line.strip().split())


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
        return CompareResult(False, f"File not found: {pa}", [], 0)
    if not pb.exists():
        return CompareResult(False, f"File not found: {pb}", [], 0)
    lines_a = _normalize_table_content(pa.read_text())
    lines_b = _normalize_table_content(pb.read_text())
    if ignore_blank:
        lines_a = [ln for ln in lines_a if ln.strip()]
        lines_b = [ln for ln in lines_b if ln.strip()]
    details: list[str] = []
    num_diffs = 0
    for i, (la, lb) in enumerate(zip(lines_a, lines_b)):
        if float_tolerance is not None and _lines_match_numeric(la, lb, float_tolerance):
            continue
        if la != lb:
            num_diffs += 1
            if len(details) < 50:
                details.append(f"  Line {i + 1}:")
                details.append(f"    Python:  {la[:100]}{'...' if len(la) > 100 else ''}")
                details.append(f"    FORTRAN: {lb[:100]}{'...' if len(lb) > 100 else ''}")
    if len(lines_a) != len(lines_b):
        num_diffs += 1
        details.append(f"  Line count: Python {len(lines_a)}, FORTRAN {len(lines_b)}")
    same = num_diffs == 0
    return CompareResult(
        same=same,
        message="Tables match" if same else f"Tables differ ({num_diffs} difference(s))",
        details=details,
        num_diffs=num_diffs,
    )


def _lines_match_numeric(line_a: str, line_b: str, sig: int) -> bool:
    """True if lines match when numeric fields are rounded to sig digits."""
    def replace_floats(s: str) -> str:
        def repl(m: re.Match[str]) -> str:
            try:
                f = float(m.group(0))
                return f"{f:.{sig}g}"
            except ValueError:
                return m.group(0)
        return re.sub(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?", repl, s)
    return replace_floats(line_a) == replace_floats(line_b)


def _normalize_postscript(text: str) -> list[str]:
    """Normalize PostScript for comparison: drop comments that vary, normalize whitespace."""
    out: list[str] = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.startswith("%%"):
            if s.startswith("%%Creator") or s.startswith("%%CreationDate") or s.startswith("%%Title"):
                continue
            if s == "%%EOF" or s.startswith("%%BoundingBox"):
                out.append(s)
            continue
        out.append(" ".join(s.split()))
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
        return CompareResult(False, f"File not found: {pa}", [], 0)
    if not pb.exists():
        return CompareResult(False, f"File not found: {pb}", [], 0)
    lines_a = _normalize_postscript(pa.read_text())
    lines_b = _normalize_postscript(pb.read_text())
    details: list[str] = []
    num_diffs = 0
    for i, (la, lb) in enumerate(zip(lines_a, lines_b)):
        if la != lb:
            num_diffs += 1
            if len(details) < 30:
                details.append(f"  Line {i + 1}:")
                details.append(f"    Python:  {la[:80]}{'...' if len(la) > 80 else ''}")
                details.append(f"    FORTRAN: {lb[:80]}{'...' if len(lb) > 80 else ''}")
    if len(lines_a) != len(lines_b):
        num_diffs += 1
        details.append(f"  Line count: Python {len(lines_a)}, FORTRAN {len(lines_b)}")
    same = num_diffs == 0
    return CompareResult(
        same=same,
        message="PostScript match" if same else f"PostScript differ ({num_diffs} difference(s))",
        details=details,
        num_diffs=num_diffs,
    )
