"""Star catalog reader (ported from viewer3_utils.f ReadStars)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

from ephemeris_tools.angle_utils import parse_angle


@dataclass
class Star:
    """A single star entry: name and J2000 RA/Dec in radians."""

    name: str
    ra: float
    dec: float


def read_stars(filepath: str | Path, max_stars: int = 100) -> list[Star]:
    """Read star list from file. Format: name, RA (hours or h m s), Dec (deg or d m s); repeat.

    Lines starting with '!' are skipped. Returns list of Star with ra/dec in radians.
    """
    path = Path(filepath)
    stars: list[Star] = []
    with path.open() as f:
        while len(stars) < max_stars:
            line = f.readline()
            if not line:
                break
            line = line.rstrip()
            if not line or line.startswith('!'):
                continue
            name = line.strip()
            ra_line = f.readline()
            if not ra_line:
                break
            ra_line = ra_line.strip()
            if ra_line.startswith('!'):
                continue
            dec_line = f.readline()
            if not dec_line:
                break
            dec_line = dec_line.strip()
            if dec_line.startswith('!'):
                continue
            ra_val = parse_angle(ra_line)
            dec_val = parse_angle(dec_line)
            if ra_val is None or dec_val is None:
                continue
            ra_rad = math.radians(ra_val * 15.0)
            dec_rad = math.radians(dec_val)
            stars.append(Star(name=name, ra=ra_rad, dec=dec_rad))
    return stars
