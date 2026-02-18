"""PostScript output (ported from escher ESDV07, ESCLIP, ESMAP, ESMOVE, ESWRIT)."""

from __future__ import annotations


def clip_line(
    xmin: float,
    xmax: float,
    ymin: float,
    ymax: float,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
) -> tuple[float, float, float, float, bool]:
    """Clip line segment to axis-aligned rectangle (port of ESCLIP).

    Interior is strict: xmin < x < xmax, ymin < y < ymax.

    Parameters:
        xmin, xmax, ymin, ymax: Rectangle bounds.
        x1, y1: First endpoint of segment.
        x2, y2: Second endpoint of segment.

    Returns:
        Tuple (clipped_x1, clipped_y1, clipped_x2, clipped_y2, inside). inside is
        True if the (possibly clipped) segment has a portion inside the rectangle.
    """
    dx = x2 - x1
    dy = y2 - y1

    def in_rect(x: float, y: float) -> bool:
        """Return True if (x, y) lies inside the rectangle [xmin,xmax] x [ymin,ymax]."""
        return xmin < x < xmax and ymin < y < ymax

    p1_in = in_rect(x1, y1)
    p2_in = in_rect(x2, y2)
    if p1_in and p2_in:
        return (x1, y1, x2, y2, True)
    if not p1_in and not p2_in:
        if dx == 0 and dy == 0:
            return (x1, y1, x2, y2, False)
        hits: list[tuple[float, float]] = []
        for edge, (cx, cy, param) in [
            ('top', (0, ymax, (ymax - y1) / dy if dy != 0 else None)),
            ('bot', (0, ymin, (ymin - y1) / dy if dy != 0 else None)),
            ('right', (xmax, 0, (xmax - x1) / dx if dx != 0 else None)),
            ('left', (xmin, 0, (xmin - x1) / dx if dx != 0 else None)),
        ]:
            if param is None:
                continue
            if 0 <= param <= 1:
                if edge in ('top', 'bot'):
                    px = x1 + param * dx
                    if xmin <= px <= xmax:
                        hits.append((px, cy))
                else:
                    py = y1 + param * dy
                    if ymin <= py <= ymax:
                        hits.append((cx, py))
        if len(hits) >= 2:
            return (hits[0][0], hits[0][1], hits[1][0], hits[1][1], True)
        return (x1, y1, x2, y2, False)

    if not p1_in:
        x1, y1, x2, y2 = x2, y2, x1, y1
        dx, dy = -dx, -dy
    t = 1.0
    if dx != 0:
        if x2 >= xmax:
            tt = (xmax - x1) / dx
            if 0 <= tt < t:
                t = tt
        if x2 <= xmin:
            tt = (xmin - x1) / dx
            if 0 <= tt < t:
                t = tt
    if dy != 0:
        if y2 >= ymax:
            tt = (ymax - y1) / dy
            if 0 <= tt < t:
                t = tt
        if y2 <= ymin:
            tt = (ymin - y1) / dy
            if 0 <= tt < t:
                t = tt
    x2 = x1 + t * dx
    y2 = y1 + t * dy
    return (x1, y1, x2, y2, True)
