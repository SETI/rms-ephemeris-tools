"""Uranus planet configuration (viewer3_ura.f)."""

from __future__ import annotations

import math

from ephemeris_tools.planets.base import MoonSpec, PlanetConfig, RingSpec

def _deg(x: float) -> float:
    return x * math.pi / 180.0

# Uranus ring elements: peri/node in degrees; dperi_dt/dnode_dt in deg/day (convert to rad/s in use)
URANUS_RING_DPERI = [
    2.76156, 2.67151, 2.59816, 2.18574, 2.03083, 0.0,
    1.75075, 0.0, 0.0, 1.36325, 1.36325,
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
]
URANUS_RING_DNODE = [
    -2.75629, -2.66604, -2.59271, -2.18326, -2.02835, 0.0,
    -1.74828, 0.0, 0.0, -1.36118, -1.36118,
    0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
]

URANUS_CONFIG = PlanetConfig(
    planet_id=799,
    planet_num=7,
    equatorial_radius_km=25559.0,
    planet_name="Uranus",
    starlist_file="starlist_ura.txt",
    longitude_direction="E",
    moons=[
        MoonSpec(799, "Uranus", "Uranus", False),
        MoonSpec(701, "Ariel", "Ariel", False),
        MoonSpec(702, "Umbriel", "Umbriel", False),
        MoonSpec(703, "Titania", "Titania", False),
        MoonSpec(704, "Oberon", "Oberon", False),
        MoonSpec(705, "Miranda", "Miranda", False),
        MoonSpec(706, "Cordelia", "Cordelia", False),
        MoonSpec(707, "Ophelia", "Ophelia", False),
        MoonSpec(708, "Bianca", "Bianca", False),
        MoonSpec(709, "Cressida", "Cressida", False),
        MoonSpec(710, "Desdemona", "Desdemona", False),
        MoonSpec(711, "Juliet", "Juliet", False),
        MoonSpec(712, "Portia", "Portia", False),
        MoonSpec(713, "Rosalind", "Rosalind", False),
        MoonSpec(714, "Belinda", "Belinda", False),
        MoonSpec(715, "Puck", "Puck", False),
        MoonSpec(725, "Perdita", "Perdita", False),
        MoonSpec(726, "Mab", "Mab", False),
        MoonSpec(727, "Cupid", "Cupid", False),
    ],
    rings=[
        RingSpec(41837.15, 0.0, 0.0, 1.013e-3, _deg(0.0616), _deg(242.80), _deg(12.12), name="Six"),
        RingSpec(42234.82, 41837.15, 0.0, 1.899e-3, _deg(0.0536), _deg(170.31), _deg(286.57), name="Five"),
        RingSpec(42570.91, 42234.82, 0.0, 1.059e-3, _deg(0.0323), _deg(127.28), _deg(89.26), name="Four"),
        RingSpec(44718.45, 42570.91, 0.0, 0.761e-3, _deg(0.0152), _deg(333.24), _deg(63.08), name="Alpha"),
        RingSpec(45661.03, 44718.45, 0.0, 0.442e-3, _deg(0.0051), _deg(224.88), _deg(310.05), name="Beta"),
        RingSpec(47175.91, 45661.03, 0.0, 0.0, 0.0, 0.0, 0.0, name="Eta"),
        RingSpec(47626.87, 47175.91, 0.0, 0.109e-3, 0.0, _deg(132.10), 0.0, name="Gamma"),
        RingSpec(48300.12, 47626.87, 0.0, 0.0, 0.0, 0.0, 0.0, name="Delta"),
        RingSpec(50023.94, 48300.12, 0.0, 0.0, 0.0, 0.0, 0.0, name="Lambda"),
        RingSpec(51091.32, 50023.94, 0.0, 7.193e-3, 0.0, _deg(214.97), 0.0, name="Epsilon"),
        RingSpec(51207.32, 51091.32, 0.0, 8.679e-3, 0.0, _deg(214.97), 0.0, name="Epsilon"),
        RingSpec(66100.0, 51207.32, 0.0, 0.0, 0.0, 0.0, 0.0, dashed=True, name="Nu"),
        RingSpec(67300.0, 66100.0, 0.0, 0.0, 0.0, 0.0, 0.0, name="Nu"),
        RingSpec(69900.0, 67300.0, 0.0, 0.0, 0.0, 0.0, 0.0, dashed=True, name="Nu"),
        RingSpec(86000.0, 69900.0, 0.0, 0.0, 0.0, 0.0, 0.0, dashed=True, name="Mu"),
        RingSpec(97700.0, 86000.0, 0.0, 0.0, 0.0, 0.0, 0.0, name="Mu"),
        RingSpec(103000.0, 97700.0, 0.0, 0.0, 0.0, 0.0, 0.0, dashed=True, name="Mu"),
    ],
    arcs=[],
)
