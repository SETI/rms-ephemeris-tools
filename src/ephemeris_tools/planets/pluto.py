"""Pluto planet configuration (viewer3_plu.f)."""

from __future__ import annotations

from ephemeris_tools.planets.base import MoonSpec, PlanetConfig, RingSpec

# Pluto-Charon barycenter offset km (BARYCENTER_OFFSET)
BARYCENTER_OFFSET_KM = 2035.0

PLUTO_CONFIG = PlanetConfig(
    planet_id=999,
    planet_num=9,
    equatorial_radius_km=1153.0,
    planet_name="Pluto",
    starlist_file="starlist_plu.txt",
    longitude_direction="W",
    moons=[
        MoonSpec(999, "Pluto", "Pluto", False),
        MoonSpec(901, "Charon", "Charon", False),
        MoonSpec(902, "Nix", "Nix", False),
        MoonSpec(903, "Hydra", "Hydra", False),
        MoonSpec(904, "Kerberos", "Kerberos", False),
        MoonSpec(905, "Styx", "Styx", False),
    ],
    rings=[
        RingSpec(outer_km=19571.0, inner_km=0.0, dashed=True),
        RingSpec(outer_km=48703.0, inner_km=19571.0, dashed=True),
        RingSpec(outer_km=64754.0, inner_km=48703.0, dashed=True),
        RingSpec(outer_km=64754.0, inner_km=57771.0, dashed=True),
        RingSpec(outer_km=57771.0, inner_km=42608.0, dashed=True),
    ],
    arcs=[],
    barycenter_id=9,
    barycenter_offset_km=BARYCENTER_OFFSET_KM,
)
