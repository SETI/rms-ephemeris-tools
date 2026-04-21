"""Matplotlib theme defaults for ephemeris-tools figures.

All matplotlib imports are at function level so importing this module does not
load matplotlib when using the Escher backend.
"""

from __future__ import annotations


def _best_sans_serif() -> list[str]:
    """Return a font family list preferring Helvetica when installed."""
    import matplotlib.font_manager as fm  # noqa: PLC0415

    available = {f.name for f in fm.fontManager.ttflist}
    candidates = ['Helvetica', 'Arial', 'Liberation Sans', 'FreeSans', 'DejaVu Sans']
    ordered = [c for c in candidates if c in available]
    ordered.append('sans-serif')
    return ordered


def apply_theme() -> None:
    """Apply rcParams defaults for ephemeris-tools matplotlib figures.

    Sets a clean sans-serif font stack (best available on the current system),
    white figure background, and sensible defaults for line rendering.  Call
    once before creating figures; idempotent.
    """
    import matplotlib as mpl  # noqa: PLC0415

    mpl.rcParams.update(
        {
            'font.family': _best_sans_serif(),
            'font.size': 9,
            'axes.titlesize': 10,
            'axes.labelsize': 9,
            'xtick.labelsize': 8,
            'ytick.labelsize': 8,
            'figure.facecolor': 'white',
            'axes.facecolor': 'white',
            'figure.dpi': 150,
            'savefig.dpi': 150,
            'savefig.bbox': 'tight',
            'savefig.pad_inches': 0.15,
            'lines.linewidth': 1.0,
            'axes.linewidth': 0.8,
            'xtick.major.width': 0.8,
            'ytick.major.width': 0.8,
            'xtick.minor.width': 0.5,
            'ytick.minor.width': 0.5,
            'text.usetex': False,
        }
    )


def figure_and_axes(
    fig_width_in: float = 7.5,
    fig_height_in: float = 9.0,
    left: float = 0.12,
    right: float = 0.97,
    top: float = 0.92,
    bottom: float = 0.08,
) -> 'tuple[matplotlib.figure.Figure, matplotlib.axes.Axes]':
    """Create a figure and a single Axes with explicit inch dimensions.

    Avoids tight_layout to prevent matplotlib version-dependent layout drift.

    Parameters:
        fig_width_in, fig_height_in: Figure size in inches.
        left, right, top, bottom: Axes extent as fractions of figure size.

    Returns:
        (fig, ax) tuple.
    """
    import matplotlib  # noqa: PLC0415
    import matplotlib.pyplot as plt  # noqa: PLC0415

    apply_theme()
    fig = plt.figure(figsize=(fig_width_in, fig_height_in))
    ax = fig.add_axes([left, bottom, right - left, top - bottom])
    return fig, ax


def infer_format(path: str) -> str:
    """Infer matplotlib savefig format from the file extension.

    Falls back to 'png' for unrecognised extensions.

    Parameters:
        path: Output file path (e.g. 'out.pdf', 'out.svg', 'out.ps').

    Returns:
        Format string suitable for matplotlib savefig (e.g. 'pdf', 'svg', 'png').
    """
    import os  # noqa: PLC0415

    ext = os.path.splitext(path)[1].lower().lstrip('.')
    known = {'pdf', 'svg', 'ps', 'eps', 'png', 'jpg', 'jpeg', 'tif', 'tiff'}
    return ext if ext in known else 'png'
