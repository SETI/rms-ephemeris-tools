"""Tests for MplCanvas projection, clipping, and group management.

Covers the SegmentSink protocol implementation in rendering/mpl/canvas.py,
including 3D-to-2D projection correctness, FOV clipping parity with _esclip,
and rendering-group bookkeeping.
"""

from __future__ import annotations

import math

import pytest

from ephemeris_tools.rendering.mpl.canvas import MplCanvas, _esclip


# ---------------------------------------------------------------------------
# _esclip: low-level 2D Cohen-Sutherland clipping
# ---------------------------------------------------------------------------


class TestEsclip:
    def test_fully_inside_returned_unchanged(self) -> None:
        """Segment entirely inside the FOV is returned as-is."""
        x1, y1, x2, y2, inside = _esclip(-1, 1, -1, 1, -0.5, -0.5, 0.5, 0.5)
        assert inside
        assert math.isclose(x1, -0.5)
        assert math.isclose(y1, -0.5)
        assert math.isclose(x2, 0.5)
        assert math.isclose(y2, 0.5)

    def test_fully_outside_returns_false(self) -> None:
        """Segment entirely outside the FOV reports not inside."""
        _, _, _, _, inside = _esclip(-1, 1, -1, 1, 2.0, 2.0, 3.0, 3.0)
        assert not inside

    def test_crosses_right_edge(self) -> None:
        """Horizontal segment crossing the right boundary is clipped to x=1."""
        x1, y1, x2, y2, inside = _esclip(-1, 1, -1, 1, 0.5, 0.0, 1.5, 0.0)
        assert inside
        assert math.isclose(x1, 0.5)
        assert math.isclose(y1, 0.0)
        assert math.isclose(x2, 1.0)
        assert math.isclose(y2, 0.0)

    def test_crosses_top_edge(self) -> None:
        """Vertical segment crossing the top boundary is clipped to y=1."""
        x1, y1, x2, y2, inside = _esclip(-1, 1, -1, 1, 0.0, 0.5, 0.0, 1.5)
        assert inside
        assert math.isclose(x1, 0.0)
        assert math.isclose(y1, 0.5)
        assert math.isclose(x2, 0.0)
        assert math.isclose(y2, 1.0)

    def test_diagonal_spanning_fov(self) -> None:
        """Diagonal segment entering and exiting through non-corner edges is clipped."""
        # From (-2, 0) to (2, 0) — horizontal through centre
        x1, y1, x2, y2, inside = _esclip(-1, 1, -1, 1, -2.0, 0.0, 2.0, 0.0)
        assert inside
        assert math.isclose(x1, -1.0)
        assert math.isclose(y1, 0.0)
        assert math.isclose(x2, 1.0)
        assert math.isclose(y2, 0.0)


# ---------------------------------------------------------------------------
# MplCanvas.draw: projection and clipping
# ---------------------------------------------------------------------------


class TestMplCanvasProjection:
    def test_simple_projection_z1(self) -> None:
        """Point at z=1 projects to (-x, -y) in FOV space."""
        canvas = MplCanvas(-1.0, 1.0, -1.0, 1.0)
        # 3D: begin=(-0.5, -0.3, 1.0), end=(0.3, 0.2, 1.0)
        # projected: (0.5, 0.3) and (-0.3, -0.2)
        canvas.draw((-0.5, -0.3, 1.0), (0.3, 0.2, 1.0), 1)
        assert canvas.has_segments
        x1, y1, x2, y2 = canvas._groups[0].segments[0]
        assert math.isclose(x1, 0.5, rel_tol=1e-9)
        assert math.isclose(y1, 0.3, rel_tol=1e-9)
        assert math.isclose(x2, -0.3, rel_tol=1e-9)
        assert math.isclose(y2, -0.2, rel_tol=1e-9)

    def test_projection_scales_with_z(self) -> None:
        """Projection at z=2 gives half the apparent offset of z=1."""
        canvas = MplCanvas(-1.0, 1.0, -1.0, 1.0)
        canvas.draw((-0.4, -0.4, 2.0), (0.4, 0.4, 2.0), 1)
        x1, y1, x2, y2 = canvas._groups[0].segments[0]
        assert math.isclose(x1, 0.2, rel_tol=1e-9)
        assert math.isclose(y1, 0.2, rel_tol=1e-9)
        assert math.isclose(x2, -0.2, rel_tol=1e-9)
        assert math.isclose(y2, -0.2, rel_tol=1e-9)

    def test_segment_at_zero_z_not_stored(self) -> None:
        """Segment with z=0 should be projected at epsilon (not cause a crash)."""
        canvas = MplCanvas(-1.0, 1.0, -1.0, 1.0)
        # z=0 is guarded by _EPS; both endpoints project far outside FOV → clipped out
        canvas.draw((100.0, 100.0, 0.0), (200.0, 200.0, 0.0), 1)
        assert not canvas.has_segments

    def test_segment_outside_fov_discarded(self) -> None:
        """Segment projecting entirely outside FOV bounds is not stored."""
        canvas = MplCanvas(-0.1, 0.1, -0.1, 0.1)
        canvas.draw((-5.0, 0.0, 1.0), (-4.0, 0.0, 1.0), 1)  # projects to (5, 0)-(4, 0)
        assert not canvas.has_segments

    def test_segment_clipped_to_fov(self) -> None:
        """Segment partially outside FOV is clipped; stored portion is inside."""
        canvas = MplCanvas(-1.0, 1.0, -1.0, 1.0)
        # projects to (0.5, 0.0)-(2.0, 0.0) → clipped to (0.5, 0.0)-(1.0, 0.0)
        canvas.draw((-0.5, 0.0, 1.0), (-2.0, 0.0, 1.0), 1)
        assert canvas.has_segments
        _, _, x2, _ = canvas._groups[0].segments[0]
        assert math.isclose(x2, 1.0, rel_tol=1e-9)


# ---------------------------------------------------------------------------
# MplCanvas color mapping
# ---------------------------------------------------------------------------


class TestMplCanvasColorCodes:
    @pytest.mark.parametrize(
        'code, expected_gray',
        [
            (0, 1.0),    # 0 → white
            (1, 0.0),    # 1 → black
            (2, 0.1),    # 2 → 0.1 gray
            (5, 0.4),    # 5 → 0.4 gray (indices: 0=white,1=black,2..11=0.1..0.9)
            (6, 0.5),    # 6 → 0.5 gray (mid-grey)
            (10, 0.9),   # 10 → 0.9 gray
        ],
    )
    def test_color_code_maps_to_gray(self, code: int, expected_gray: float) -> None:
        canvas = MplCanvas(-1.0, 1.0, -1.0, 1.0)
        canvas.draw((-0.1, 0.0, 1.0), (0.1, 0.0, 1.0), code)
        assert math.isclose(canvas._groups[0].gray, expected_gray)


# ---------------------------------------------------------------------------
# MplCanvas group management
# ---------------------------------------------------------------------------


class TestMplCanvasGroups:
    def test_same_attributes_share_group(self) -> None:
        """Two consecutive draws with identical style accumulate in one group."""
        canvas = MplCanvas(-1.0, 1.0, -1.0, 1.0)
        canvas.draw((-0.1, 0.0, 1.0), (0.1, 0.0, 1.0), 1)
        canvas.draw((-0.1, 0.1, 1.0), (0.1, 0.1, 1.0), 1)
        assert len(canvas._groups) == 1
        assert len(canvas._groups[0].segments) == 2

    def test_color_change_creates_new_group(self) -> None:
        """Changing colour creates a new group."""
        canvas = MplCanvas(-1.0, 1.0, -1.0, 1.0)
        canvas.draw((-0.1, 0.0, 1.0), (0.1, 0.0, 1.0), 1)   # black
        canvas.draw((-0.1, 0.1, 1.0), (0.1, 0.1, 1.0), 5)   # grey
        assert len(canvas._groups) == 2

    def test_set_linewidth_splits_group(self) -> None:
        """set_linewidth() causes next draw to open a new group."""
        canvas = MplCanvas(-1.0, 1.0, -1.0, 1.0)
        canvas.draw((-0.1, 0.0, 1.0), (0.1, 0.0, 1.0), 1)
        canvas.set_linewidth(2.5)
        canvas.draw((-0.1, 0.1, 1.0), (0.1, 0.1, 1.0), 1)
        assert len(canvas._groups) == 2
        assert math.isclose(canvas._groups[0].linewidth, 1.0)
        assert math.isclose(canvas._groups[1].linewidth, 2.5)

    def test_set_dashed_splits_group(self) -> None:
        """set_dashed(True) causes next draw to open a new group."""
        canvas = MplCanvas(-1.0, 1.0, -1.0, 1.0)
        canvas.draw((-0.1, 0.0, 1.0), (0.1, 0.0, 1.0), 1)
        canvas.set_dashed(True)
        canvas.draw((-0.1, 0.1, 1.0), (0.1, 0.1, 1.0), 1)
        assert len(canvas._groups) == 2
        assert canvas._groups[0].dashed is False
        assert canvas._groups[1].dashed is True

    def test_set_dashed_false_splits_group_again(self) -> None:
        """set_dashed(False) after True opens a third group."""
        canvas = MplCanvas(-1.0, 1.0, -1.0, 1.0)
        canvas.draw((-0.1, 0.0, 1.0), (0.1, 0.0, 1.0), 1)
        canvas.set_dashed(True)
        canvas.draw((-0.1, 0.1, 1.0), (0.1, 0.1, 1.0), 1)
        canvas.set_dashed(False)
        canvas.draw((-0.1, 0.2, 1.0), (0.1, 0.2, 1.0), 1)
        assert len(canvas._groups) == 3
        assert canvas._groups[2].dashed is False


# ---------------------------------------------------------------------------
# MplCanvas.dump and properties
# ---------------------------------------------------------------------------


class TestMplCanvasMisc:
    def test_dump_is_noop(self) -> None:
        """dump() must not add, remove, or modify any stored segments."""
        canvas = MplCanvas(-1.0, 1.0, -1.0, 1.0)
        canvas.draw((-0.1, 0.0, 1.0), (0.1, 0.0, 1.0), 1)
        before = len(canvas._groups[0].segments)
        canvas.dump()
        assert len(canvas._groups[0].segments) == before

    def test_fov_property(self) -> None:
        """fov property returns the bounds passed at construction."""
        canvas = MplCanvas(-2.0, 3.0, -1.5, 4.0)
        assert canvas.fov == (-2.0, 3.0, -1.5, 4.0)

    def test_has_segments_false_when_empty(self) -> None:
        canvas = MplCanvas(-1.0, 1.0, -1.0, 1.0)
        assert not canvas.has_segments

    def test_has_segments_true_after_draw(self) -> None:
        canvas = MplCanvas(-1.0, 1.0, -1.0, 1.0)
        canvas.draw((-0.1, 0.0, 1.0), (0.1, 0.0, 1.0), 1)
        assert canvas.has_segments


# ---------------------------------------------------------------------------
# MplCanvas.finalize: matplotlib integration
# ---------------------------------------------------------------------------


class TestMplCanvasFinalize:
    def test_finalize_sets_x_limits_to_fov(self) -> None:
        """finalize() sets x-limits to (xmin, xmax) matching PostScript esview."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        canvas = MplCanvas(-1.0, 1.0, -1.0, 1.0)
        canvas.draw((-0.1, 0.0, 1.0), (0.1, 0.0, 1.0), 1)
        fig, ax = plt.subplots()
        canvas.finalize(ax)
        xlim = ax.get_xlim()
        assert xlim[0] < xlim[1]
        assert math.isclose(xlim[0], -1.0)
        assert math.isclose(xlim[1], 1.0)
        plt.close(fig)

    def test_finalize_inverts_y_axis(self) -> None:
        """finalize() sets y-limits to (ymax, ymin) like PS (negative uy in esview)."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        canvas = MplCanvas(-2.0, 2.0, -3.0, 3.0)
        canvas.draw((-0.1, 0.0, 1.0), (0.1, 0.0, 1.0), 1)
        fig, ax = plt.subplots()
        canvas.finalize(ax)
        ylim = ax.get_ylim()
        assert math.isclose(ylim[0], 3.0)
        assert math.isclose(ylim[1], -3.0)
        plt.close(fig)

    def test_finalize_empty_canvas_does_not_raise(self) -> None:
        """finalize() on a canvas with no segments should complete without error."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt

        canvas = MplCanvas(-1.0, 1.0, -1.0, 1.0)
        fig, ax = plt.subplots()
        canvas.finalize(ax)
        plt.close(fig)

    def test_finalize_linewidth_scale_applied(self) -> None:
        """linewidth_scale multiplies the stored linewidth in the LineCollection."""
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from matplotlib.collections import LineCollection

        canvas = MplCanvas(-1.0, 1.0, -1.0, 1.0)
        canvas.set_linewidth(2.0)
        canvas.draw((-0.1, 0.0, 1.0), (0.1, 0.0, 1.0), 1)
        fig, ax = plt.subplots()
        canvas.finalize(ax, linewidth_scale=2.0)
        collections = [c for c in ax.collections if isinstance(c, LineCollection)]
        assert collections
        lws = collections[0].get_linewidths()
        # 2.0 (stored) * 2.0 (scale) = 4.0
        assert math.isclose(float(lws[0]), 4.0)
        plt.close(fig)
