"""Base planet configuration dataclass for viewer/ephemeris/tracker."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MoonSpec:
    """Moon identifier and display options."""

    id: int
    name: str
    label: str
    is_irregular: bool = False


@dataclass
class RingSpec:
    """Ring geometry and display (one radius = outer; inner from previous or 0)."""

    outer_km: float
    inner_km: float = 0.0
    elev_km: float = 0.0
    ecc: float = 0.0
    inc_rad: float = 0.0
    peri_rad: float = 0.0
    node_rad: float = 0.0
    opaque: bool = False
    opaque_unlit: bool | None = None
    dashed: bool = False
    grayscale: float = 1.0
    dperi_dt: float = 0.0
    dnode_dt: float = 0.0
    name: str | None = None


@dataclass
class ArcSpec:
    """Neptune arc: ring index and longitude range (degrees)."""

    ring_index: int
    minlon_deg: float
    maxlon_deg: float
    name: str = ""
    motion_deg_day: float = 0.0


@dataclass
class PlanetConfig:
    """Base planet configuration: IDs, radius, moons, rings, longitude direction."""

    planet_id: int
    planet_num: int
    equatorial_radius_km: float
    planet_name: str
    starlist_file: str
    longitude_direction: str  # "E" or "W"
    moons: list[MoonSpec] = field(default_factory=list)
    rings: list[RingSpec] = field(default_factory=list)
    arcs: list[ArcSpec] = field(default_factory=list)
    barycenter_id: int | None = None
    barycenter_offset_km: float = 0.0
    f_ring_index: int | None = None
    ring_offsets_km: dict[int, float] = field(default_factory=dict)

    def moon_ids(self) -> list[int]:
        """Ordered list of moon NAIF IDs (excluding planet at index 0)."""
        return [m.id for m in self.moons if m.id != self.planet_id]

    def moon_by_id(self, body_id: int) -> MoonSpec | None:
        """Return MoonSpec for given NAIF ID or None."""
        for m in self.moons:
            if m.id == body_id:
                return m
        return None
