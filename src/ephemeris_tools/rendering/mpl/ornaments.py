"""Ornament specification dataclasses for matplotlib rendering.

These dataclasses carry display metadata (title, captions, labels) that are
populated from the viewer/tracker call sites and consumed by the matplotlib
renderers to produce text overlays without any PostScript dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TitleSpec:
    """Title line displayed above the figure."""

    text: str = ''


@dataclass
class CaptionSpec:
    """A single key-value caption line below the figure.

    lcaption is the left-aligned label (e.g. "Time (UTC):") and rcaption is
    the right-aligned or left-aligned value (e.g. "2025-01-01 00:00 UTC").
    """

    lcaption: str = ''
    rcaption: str = ''


@dataclass
class FooterSpec:
    """Footer credit line (e.g. generator timestamp and tool name)."""

    text: str = ''


@dataclass
class AxisLabelSpec:
    """Labels for the horizontal (RA) and vertical (Dec) axes."""

    xlabel: str = 'Right Ascension'
    ylabel: str = 'Declination'
    xlabel_unit: str = 'h m s'
    ylabel_unit: str = '\u00b0'


@dataclass
class MoonLabelSpec:
    """Label for a single moon overlaid on the viewer scene."""

    name: str
    x: float  # FOV-plane x coordinate
    y: float  # FOV-plane y coordinate


@dataclass
class StarLabelSpec:
    """Label for a single star overlaid on the viewer scene."""

    name: str
    x: float
    y: float


@dataclass
class ViewerOrnaments:
    """All ornament specs for a single viewer (draw_planetary_view_mpl) call."""

    title: TitleSpec = field(default_factory=TitleSpec)
    captions: list[CaptionSpec] = field(default_factory=list)
    footer: FooterSpec = field(default_factory=FooterSpec)
    axis_labels: AxisLabelSpec = field(default_factory=AxisLabelSpec)
    moon_labels: list[MoonLabelSpec] = field(default_factory=list)
    star_labels: list[StarLabelSpec] = field(default_factory=list)


@dataclass
class TrackerOrnaments:
    """All ornament specs for a single tracker (draw_moon_tracks_mpl) call."""

    title: TitleSpec = field(default_factory=TitleSpec)
    captions: list[CaptionSpec] = field(default_factory=list)
    footer: FooterSpec = field(default_factory=FooterSpec)
    xlabel: str = 'Arcsec'
    ylabel: str = 'Time'
