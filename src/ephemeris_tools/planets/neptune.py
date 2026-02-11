"""Neptune planet configuration (viewer3_nep.f)."""

from __future__ import annotations

from ephemeris_tools.planets.base import ArcSpec, MoonSpec, PlanetConfig, RingSpec

NEPTUNE_CONFIG = PlanetConfig(
    planet_id=899,
    planet_num=8,
    equatorial_radius_km=24764.0,
    planet_name='Neptune',
    starlist_file='starlist_nep.txt',
    longitude_direction='W',
    moons=[
        MoonSpec(899, 'Neptune', 'Neptune', False),
        MoonSpec(801, 'Triton', 'Triton', False),
        MoonSpec(802, 'Nereid', 'Nereid', False),
        MoonSpec(803, 'Naiad', 'Naiad', False),
        MoonSpec(804, 'Thalassa', 'Thalassa', False),
        MoonSpec(805, 'Despina', 'Despina', False),
        MoonSpec(806, 'Galatea', 'Galatea', False),
        MoonSpec(807, 'Larissa', 'Larissa', False),
        MoonSpec(808, 'Proteus', 'Proteus', False),
        MoonSpec(814, 'Hippocamp', 'Hippocamp', False),
    ],
    rings=[
        RingSpec(outer_km=42000.0, inner_km=0.0, dashed=True),
        RingSpec(outer_km=53200.0, inner_km=42000.0, opaque=True, dashed=False),
        RingSpec(outer_km=57500.0, inner_km=53200.0, dashed=True),
        RingSpec(outer_km=62932.0, inner_km=57500.0, opaque=True, dashed=False),
    ],
    arcs=[
        ArcSpec(3, 247.1, 256.7, 'Fraternite', 820.1194),
        ArcSpec(3, 261.1, 264.1, 'Egalite B', 820.1118),
        ArcSpec(3, 264.9, 265.9, 'Egalite A', 820.1121),
        ArcSpec(3, 275.7, 279.8, 'Liberte', 820.1121),
        ArcSpec(3, 284.5, 285.5, 'Courage', 820.1121),
    ],
)
