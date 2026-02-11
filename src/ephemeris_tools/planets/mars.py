"""Mars planet configuration (viewer3_mar.f)."""

from __future__ import annotations

from ephemeris_tools.planets.base import MoonSpec, PlanetConfig, RingSpec

MARS_CONFIG = PlanetConfig(
    planet_id=499,
    planet_num=4,
    equatorial_radius_km=3397.0,
    planet_name='Mars',
    starlist_file='starlist_mar.txt',
    longitude_direction='W',
    moons=[
        MoonSpec(499, 'Mars', 'Mars', False),
        MoonSpec(401, 'Phobos', 'Phobos', False),
        MoonSpec(402, 'Deimos', 'Deimos', False),
    ],
    rings=[
        RingSpec(outer_km=9378.0, inner_km=0.0, elev_km=-177.0, dashed=False),
        RingSpec(outer_km=9378.0, inner_km=9378.0, elev_km=177.0, dashed=False),
        RingSpec(
            outer_km=23459.0,
            inner_km=23459.0,
            elev_km=-2656.0,
            inc_rad=0.11346,
            dashed=True,
        ),
        RingSpec(
            outer_km=23459.0,
            inner_km=23459.0,
            elev_km=2656.0,
            inc_rad=0.11346,
            dashed=True,
        ),
    ],
    arcs=[],
    ring_offsets_km={0: -3398.0, 1: -3398.0, 2: 6796.0, 3: 6796.0},
)
