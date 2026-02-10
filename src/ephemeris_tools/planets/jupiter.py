"""Jupiter planet configuration (viewer3_jup.f)."""

from __future__ import annotations

from ephemeris_tools.planets.base import MoonSpec, PlanetConfig, RingSpec

JUPITER_CONFIG = PlanetConfig(
    planet_id=599,
    planet_num=5,
    equatorial_radius_km=71492.0,
    planet_name="Jupiter",
    starlist_file="starlist_jup.txt",
    longitude_direction="W",
    moons=[
        MoonSpec(599, "Jupiter", "Jupiter", False),
        MoonSpec(501, "Io", "Io", False),
        MoonSpec(502, "Europa", "Europa", False),
        MoonSpec(503, "Ganymede", "Ganymede", False),
        MoonSpec(504, "Callisto", "Callisto", False),
        MoonSpec(505, "Amalthea", "Amalthea", False),
        MoonSpec(514, "Thebe", "Thebe", False),
        MoonSpec(515, "Adrastea", "Adrastea", False),
        MoonSpec(516, "Metis", "Metis", False),
        MoonSpec(506, "Himalia", "Himalia", True),
        MoonSpec(507, "Elara", "Elara", True),
    ],
    rings=[
        RingSpec(outer_km=122000.0, inner_km=0.0, dashed=False),
        RingSpec(outer_km=129000.0, inner_km=122000.0, dashed=False),
        RingSpec(outer_km=181350.0, inner_km=181350.0, elev_km=1160.0, dashed=True),
        RingSpec(outer_km=181350.0, inner_km=181350.0, elev_km=-1160.0, dashed=True),
        RingSpec(outer_km=221900.0, inner_km=221900.0, elev_km=4310.0, dashed=True),
        RingSpec(outer_km=221900.0, inner_km=221900.0, elev_km=-4310.0, dashed=True),
        RingSpec(outer_km=422000.0, inner_km=221900.0, dashed=True),
    ],
    arcs=[],
)
