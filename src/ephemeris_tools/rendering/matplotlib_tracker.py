"""Matplotlib-based moon tracker (alternative to PostScript). Future-ready stub."""

from __future__ import annotations


def draw_moon_tracks_mpl(
    planet_num: int,
    times: list[float],
    moon_offsets: list[list[float]],
    limb_rad: float,
    output_path: str | None = None,
) -> None:
    """Render moon tracker plot using matplotlib."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        raise ImportError("matplotlib is required for draw_moon_tracks_mpl") from None
    fig, ax = plt.subplots()
    ax.set_title("Moon tracker (matplotlib stub)")
    if output_path:
        fig.savefig(output_path)
    plt.close(fig)
