"""Matplotlib-based planet viewer (alternative to PostScript). Future-ready stub."""

from __future__ import annotations


def draw_planetary_view_mpl(
    planet_num: int,
    center_ra: float,
    center_dec: float,
    fov: float,
    bodies: list,
    rings: list,
    stars: list,
    output_path: str | None = None,
) -> None:
    """Render planet view using matplotlib. Requires matplotlib optional dependency."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib is required for draw_planetary_view_mpl") from None
    fig, ax = plt.subplots()
    ax.set_title("Planet view (matplotlib stub)")
    if output_path:
        fig.savefig(output_path)
    plt.close(fig)

