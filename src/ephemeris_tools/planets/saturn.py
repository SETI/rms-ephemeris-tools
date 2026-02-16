"""Saturn planet configuration (viewer3_sat.f)."""

from __future__ import annotations

from ephemeris_tools.planets.base import MoonSpec, PlanetConfig, RingSpec

# F ring precession rad/sec (FORTRAN FRING_DPERI_DT, FRING_DNODE_DT)
FRING_DPERI_DT = 5.45435592e-7
FRING_DNODE_DT = -5.42910521e-7

SATURN_CONFIG = PlanetConfig(
    planet_id=699,
    planet_num=6,
    equatorial_radius_km=60268.0,
    planet_name='Saturn',
    starlist_file='starlist_sat.txt',
    longitude_direction='W',
    moons=[
        MoonSpec(699, 'Saturn', 'Saturn', False),
        MoonSpec(601, 'Mimas', 'Mimas', False),
        MoonSpec(602, 'Enceladus', 'Enceladus', False),
        MoonSpec(603, 'Tethys', 'Tethys', False),
        MoonSpec(604, 'Dione', 'Dione', False),
        MoonSpec(605, 'Rhea', 'Rhea', False),
        MoonSpec(606, 'Titan', 'Titan', False),
        MoonSpec(607, 'Hyperion', 'Hyperion', False),
        MoonSpec(608, 'Iapetus', 'Iapetus', False),
        MoonSpec(609, 'Phoebe', 'Phoebe', False),
        MoonSpec(610, 'Janus', 'Janus', False),
        MoonSpec(611, 'Epimetheus', 'Epimetheus', False),
        MoonSpec(612, 'Helene', 'Helene', False),
        MoonSpec(613, 'Telesto', 'Telesto', False),
        MoonSpec(614, 'Calypso', 'Calypso', False),
        MoonSpec(615, 'Atlas', 'Atlas', False),
        MoonSpec(616, 'Prometheus', 'Prometheus', False),
        MoonSpec(617, 'Pandora', 'Pandora', False),
        MoonSpec(618, 'Pan', 'Pan', False),
        MoonSpec(632, 'Methone', 'Methone', False),
        MoonSpec(633, 'Pallene', 'Pallene', False),
        MoonSpec(634, 'Polydeuces', 'Polydeuces', False),
        MoonSpec(635, 'Daphnis', 'Daphnis', False),
        MoonSpec(649, 'Anthe', 'Anthe', False),
        MoonSpec(653, 'Aegaeon', 'Aegaeon', False),
    ],
    rings=[
        RingSpec(outer_km=74490.0, inner_km=0.0, opaque=False, opaque_unlit=True),
        RingSpec(outer_km=92050.0, inner_km=74490.0, opaque=True, opaque_unlit=True),
        RingSpec(outer_km=117540.0, inner_km=92050.0, opaque=True, opaque_unlit=True),
        RingSpec(outer_km=122060.0, inner_km=117540.0, opaque=True, opaque_unlit=False),
        RingSpec(outer_km=136780.0, inner_km=122060.0, opaque=True, opaque_unlit=True),
        RingSpec(
            outer_km=140223.7,
            inner_km=136780.0,
            ecc=0.00254,
            inc_rad=0.00011,
            peri_rad=0.42062,
            node_rad=0.28100,
            opaque=False,
            dashed=True,
            dperi_dt=FRING_DPERI_DT,
            dnode_dt=FRING_DNODE_DT,
        ),
        RingSpec(outer_km=166000.0, inner_km=140223.7, dashed=True),
        RingSpec(outer_km=173000.0, inner_km=166000.0, dashed=True),
        RingSpec(outer_km=238040.0, inner_km=173000.0, dashed=True),
    ],
    arcs=[],
    f_ring_index=5,
)
