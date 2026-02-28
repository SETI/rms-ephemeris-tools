#!/usr/bin/env python3
"""Generate random full CGI URLs for Viewer, Tracker, and Ephemeris tools.

Reads the parameter options from the CGI parameter reference (docs) and
produces valid full URLs (host pds-rings.seti.org, path e.g. /cgi-bin/tools/
ephem3_xxx.pl?) with mandatory fields always set and optional fields randomly
included with random valid values. Output is one URL per line to the given file.

Usage:
    python scripts/generate_random_query_urls.py -n 100 -o urls.txt
    python scripts/generate_random_query_urls.py -n 50 -o viewer.txt --tool viewer
"""

from __future__ import annotations

import argparse
import math
import random
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

# Repo root (script is in scripts/)
_REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Base URL and CGI script names (same pattern as fortran/Tools/tests/test_files)
# ---------------------------------------------------------------------------

BASE_URL = 'https://pds-rings.seti.org'
TOOL_CGI_SCRIPT = {
    'viewer': 'viewer3_xxx.pl',
    'tracker': 'tracker3_xxx.pl',
    'ephemeris': 'ephem3_xxx.pl',
}

# ---------------------------------------------------------------------------
# Tool / abbrev / planet / ephem mapping (from CGI parameter reference)
# ---------------------------------------------------------------------------

VIEWER_ABBREVS = [
    'mar',
    'jup',
    'sat',
    'ura',
    'nep',
    'plu',
    'satc',
    'jupc',
    'jupj',
    'jupjc',
    'jupnh',
    'jupec',
    'plunh',
]
TRACKER_ABBREVS = [
    'mar',
    'jup',
    'sat',
    'ura',
    'nep',
    'plu',
    'jupj',
    'jupjc',
    'jupec',
    'satc',
    'plunh',
]
# Ephemeris: Earth abbrevs use Earth-only observatory select; mission abbrevs use
# mission-specific forms (ephem3_jupnh.shtml, ephem3_satc.shtml, etc.) with hidden
# observatory. When abbrev is mission-specific, set observatory from mission_obs.
EPHEMERIS_ABBREVS = [
    'mar',
    'jup',
    'sat',
    'ura',
    'nep',
    'plu',
    'jupc',
    'jupj',
    'jupjc',
    'jupnh',
    'jupec',
    'satc',
    'plunh',
]


def _planet(abbrev: str) -> str:
    """Map abbrev to planet name for value lookups."""
    p = {
        'mar': 'Mars',
        'jup': 'Jupiter',
        'jupc': 'Jupiter',
        'jupj': 'Jupiter',
        'jupjc': 'Jupiter',
        'jupnh': 'Jupiter',
        'jupec': 'Jupiter',
        'sat': 'Saturn',
        'satc': 'Saturn',
        'ura': 'Uranus',
        'nep': 'Neptune',
        'plu': 'Pluto',
        'plunh': 'Pluto',
    }
    return p.get(abbrev, 'Jupiter')


def _prefix(abbrev: str) -> str:
    """Mission prefix for abbrev (empty for Earth-based)."""
    pre = {
        'satc': 'Cassini/',
        'jupc': 'Cassini/',
        'jupj': 'Juno/',
        'jupjc': 'JUICE/',
        'jupnh': 'New Horizons/',
        'jupec': 'Europa Clipper/',
        'plunh': 'New Horizons/',
    }
    return pre.get(abbrev, '')


# Mission date limits for SPICE kernel availability (from web/tools/EPHEMERIS_INFO.shtml).
# (min_date, max_date) inclusive.
MISSION_DATE_RANGES: dict[str, tuple[datetime, datetime]] = {
    'jupc': (datetime(2000, 6, 1, tzinfo=timezone.utc), datetime(2001, 6, 1, tzinfo=timezone.utc)),
    'jupj': (datetime(2016, 8, 15, tzinfo=timezone.utc), datetime(2025, 10, 31, tzinfo=timezone.utc)),
    'jupjc': (datetime(2023, 4, 5, tzinfo=timezone.utc), datetime(2035, 10, 5, tzinfo=timezone.utc)),
    'jupnh': (datetime(2007, 1, 1, tzinfo=timezone.utc), datetime(2007, 3, 15, tzinfo=timezone.utc)),
    'jupec': (datetime(2024, 12, 20, tzinfo=timezone.utc), datetime(2034, 9, 3, tzinfo=timezone.utc)),
    'satc': (datetime(2004, 1, 1, tzinfo=timezone.utc), datetime(2017, 9, 15, tzinfo=timezone.utc)),
    'plunh': (datetime(2015, 1, 1, tzinfo=timezone.utc), datetime(2015, 8, 31, tzinfo=timezone.utc)),
}

# Observatory date limits for SPICE kernel availability (when observatory is used).
# Spacecraft must have dates within SPK ephemeris coverage or FORTRAN fails with
# SPKINSUFFDATA. Ranges aligned with typical SPICE_spacecraft.txt kernel coverage.
OBSERVATORY_DATE_RANGES: dict[str, tuple[datetime, datetime]] = {
    'HST': (
        datetime(2020, 1, 1, tzinfo=timezone.utc),
        datetime(2025, 12, 31, tzinfo=timezone.utc),
    ),
    'JWST': (
        datetime(2022, 1, 1, tzinfo=timezone.utc),
        datetime(2025, 12, 31, tzinfo=timezone.utc),
    ),
    # Spacecraft: constrain to mission SPK coverage
    'New Horizons': (
        datetime(2006, 1, 19, tzinfo=timezone.utc),  # launch
        datetime(2016, 1, 1, tzinfo=timezone.utc),  # post-Pluto, extended mission
    ),
    'Juno': (
        datetime(2016, 8, 16, tzinfo=timezone.utc),  # Jupiter arrival
        datetime(2025, 10, 19, tzinfo=timezone.utc),
    ),
    'Europa Clipper': (
        datetime(2024, 12, 20, tzinfo=timezone.utc),  # nominal launch
        datetime(2034, 9, 3, tzinfo=timezone.utc),
    ),
    'JUICE': (
        datetime(2023, 4, 7, tzinfo=timezone.utc),  # launch
        datetime(2035, 10, 2, tzinfo=timezone.utc),
    ),
    'Cassini': (
        datetime(2004, 1, 1, tzinfo=timezone.utc),  # Saturn arrival
        datetime(2017, 9, 15, tzinfo=timezone.utc),  # end of mission
    ),
    'Voyager 1': (
        datetime(1977, 9, 5, tzinfo=timezone.utc),
        datetime(1990, 1, 1, tzinfo=timezone.utc),
    ),
    'Voyager 2': (
        datetime(1977, 8, 20, tzinfo=timezone.utc),
        datetime(1990, 1, 1, tzinfo=timezone.utc),
    ),
    'Galileo': (
        datetime(1995, 12, 7, tzinfo=timezone.utc),  # Jupiter arrival
        datetime(2003, 9, 21, tzinfo=timezone.utc),  # impact
    ),
}

# Override OBSERVATORY_DATE_RANGES when (abbrev, observatory) is constrained.
# New Horizons at Pluto (plunh) has SPK coverage for the encounter window.
OBSERVATORY_ABBREV_DATE_RANGES: dict[tuple[str, str], tuple[datetime, datetime]] = {
    ('jupc', 'Cassini'): (
        datetime(2000, 6, 1, tzinfo=timezone.utc),
        datetime(2001, 6, 1, tzinfo=timezone.utc),
    ),
    ('jupj', 'Juno'): (
        datetime(2016, 8, 15, tzinfo=timezone.utc),
        datetime(2025, 10, 19, tzinfo=timezone.utc),
    ),
    ('jupjc', 'JUICE'): (
        datetime(2023, 4, 5, tzinfo=timezone.utc),
        datetime(2035, 10, 5, tzinfo=timezone.utc),
    ),
    ('jupnh', 'New Horizons'): (
        datetime(2007, 1, 1, tzinfo=timezone.utc),
        datetime(2007, 3, 15, tzinfo=timezone.utc),
    ),
    ('jupec', 'Europa Clipper'): (
        datetime(2024, 12, 20, tzinfo=timezone.utc),
        datetime(2034, 9, 3, tzinfo=timezone.utc),
    ),
    ('satc', 'Cassini'): (
        datetime(2004, 1, 1, tzinfo=timezone.utc),
        datetime(2017, 9, 15, tzinfo=timezone.utc),
    ),
    ('plunh', 'New Horizons'): (
        datetime(2015, 1, 1, tzinfo=timezone.utc),
        datetime(2015, 8, 31, tzinfo=timezone.utc),
    ),
    ('jup', 'Voyager 2'): (
        datetime(1979, 6, 5, tzinfo=timezone.utc),
        datetime(1979, 7, 15, tzinfo=timezone.utc),
    ),
    ('sat', 'Voyager 2'): (
        datetime(1981, 6, 11, tzinfo=timezone.utc),
        datetime(1981, 9, 20, tzinfo=timezone.utc),
    ),
    ('ura', 'Voyager 2'): (
        datetime(1985, 11, 7, tzinfo=timezone.utc),
        datetime(1986, 2, 10, tzinfo=timezone.utc),
    ),
    ('nep', 'Voyager 2'): (
        datetime(1989, 7, 1, tzinfo=timezone.utc),
        datetime(1989, 9, 28, tzinfo=timezone.utc),
    ),
    ('jup', 'Voyager 1'): (
        datetime(1978, 12, 12, tzinfo=timezone.utc),
        datetime(1979, 3, 15, tzinfo=timezone.utc),
    ),
    ('sat', 'Voyager 1'): (
        datetime(1980, 8, 24, tzinfo=timezone.utc),
        datetime(1980, 11, 15, tzinfo=timezone.utc),
    ),
}

def _load_starlist(planet_abbrev: str) -> list[str]:
    """Load star names from web/tools/starlist_<planet>.txt.

    Returns names in the exact format the FORTRAN expects (used for center=star).
    Mars and Pluto starlists are empty; Jupiter/Saturn/Uranus/Neptune have entries.
    """
    # Map abbrev to starlist file suffix
    abbrev_to_suffix = {
        'mar': 'mar',
        'jup': 'jup',
        'jupc': 'jup',
        'jupj': 'jup',
        'jupjc': 'jup',
        'jupnh': 'jup',
        'jupec': 'jup',
        'sat': 'sat',
        'satc': 'sat',
        'ura': 'ura',
        'nep': 'nep',
        'plu': 'plu',
        'plunh': 'plu',
    }
    suffix = abbrev_to_suffix.get(planet_abbrev)
    if not suffix:
        return []
    path = _REPO_ROOT / 'web' / 'tools' / f'starlist_{suffix}.txt'
    if not path.exists():
        return []
    stars: list[str] = []
    lines = path.read_text().splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith('!'):
            i += 1
            continue
        # Star name line; next two should be RA and Dec (numeric)
        try:
            float(lines[i + 1].strip().split()[0])
            float(lines[i + 2].strip().split()[0])
        except (IndexError, ValueError):
            i += 1
            continue
        stars.append(line)
        i += 3
    return stars


EPHEM_BY_ABBREV = {
    'mar': '000 MAR097 + DE440',
    'jup': '000 JUP365 + DE440',
    'jupc': '000 JUP344 + JUP365 + DE440',
    'jupj': '000 JUP365 + DE440',
    'jupjc': '000 JUP365 + DE440',
    'jupnh': '000 JUP344 + JUP365 + DE440',
    'jupec': '000 JUP365 + DE440',
    'sat': '000 SAT415 + SAT441 + DE440',
    'satc': '000 SAT415 + SAT441 + DE440',
    'ura': '000 URA111 + URA115 + DE440',
    'nep': '000 NEP095 + NEP097 + NEP101 + DE440',
    'plu': '000 PLU058 + DE440',
    'plunh': '000 PLU058 + DE440',
}

# ---------------------------------------------------------------------------
# Shared option lists (values trimmed for URL)
# ---------------------------------------------------------------------------

# Match fortran/Tools/tests/test_files/ephemeris-generator-unit-tests.txt:
# observatory and lon_dir values without leading space (FORTRAN expects 'east'/'west').
# Ephemeris and tracker forms have NO spacecraft in the observatory select (VIEWPOINT.shtml
# is included with TOOL=ephem3/tracker3, so the spacecraft block is not rendered).
OBSERVATORIES_EARTH = [
    "Earth's center",
    'HST',
    'JWST',
    'Apache Point Observatory (32.780361, -105.820417, 2674.)',
    'Kitt Peak National Observatory (31.958833, -111.594694, 2058.4)',
    'Lowell Observatory (35.097, -111.537, 2200.)',
    'Mauna Kea Observatory (19.827, -155.472, 4215.)',
    'McDonald Observatory (30.671500, -104.022611, 2076.)',
    'Mt. Evans Observatory (39.587, -105.640, 4305.)',
    'NMSU Observatory (32.27631, -106.746556, 0.)',
    'Paranal Observatory/VLT (-24.625417, -70.402806, 2635.)',
    'Yerkes Observatory (42.57, -88.557, 334.)',
]

# Viewer only: spacecraft options per planet (from VIEWPOINT.shtml with TOOL=viewer3).
# Mars has no spacecraft; Pluto has New Horizons; Jupiter/Saturn/Uranus/Neptune have more.
VIEWER_OBSERVATORIES_JUPITER = OBSERVATORIES_EARTH + [
    'Voyager 1',
    'Voyager 2',
    'Galileo',
    'Cassini',
    'New Horizons',
    'Juno',
    'JUICE',
    'Europa Clipper',
]
VIEWER_OBSERVATORIES_SATURN = OBSERVATORIES_EARTH + ['Voyager 1', 'Voyager 2', 'Cassini']
VIEWER_OBSERVATORIES_URANUS = OBSERVATORIES_EARTH + ['Voyager 2']
VIEWER_OBSERVATORIES_NEPTUNE = OBSERVATORIES_EARTH + ['Voyager 2']
VIEWER_OBSERVATORIES_PLUTO = OBSERVATORIES_EARTH + ['New Horizons']

VIEWER_OBSERVATORIES_BY_PLANET: dict[str, list[str]] = {
    'Mars': OBSERVATORIES_EARTH,
    'Jupiter': VIEWER_OBSERVATORIES_JUPITER,
    'Saturn': VIEWER_OBSERVATORIES_SATURN,
    'Uranus': VIEWER_OBSERVATORIES_URANUS,
    'Neptune': VIEWER_OBSERVATORIES_NEPTUNE,
    'Pluto': VIEWER_OBSERVATORIES_PLUTO,
}

LON_DIR = ['east', 'west']
CENTER_EW = ['east', 'west']
# Submitted values for center_ra_type / extra_ra_type (no leading space; match form value=).
# Never use leading '+' (backend treats + as hours; would mislabel RA axis).
RA_TYPE = ['hours', 'degrees']
OUTPUT_VIEWER = ['HTML', 'PDF', 'JPEG', 'PS']
OUTPUT_TRACKER = ['HTML', 'PDF', 'JPEG', 'PS', 'TAB']
OUTPUT_EPHEM = ['HTML', 'TAB']
TIME_UNIT = ['seconds', 'minutes', 'hours', 'days']
LABELS = ['None', 'Small (6 points)', 'Medium (9 points)', 'Large (12 points)']
MERIDIANS = ['Yes', 'No']
BLANK = ['Yes', 'No']
OPACITY = ['Transparent', 'Semi-transparent (2x file size)', 'Opaque']

# Planet-specific: center_body, center_ansa, fov_unit, moons (viewer radio), rings, etc.
VIEWER_CENTER_BODY: dict[str, list[str]] = {
    'Mars': [' Mars', ' Phobos (M1)', ' Deimos (M2)'],
    'Jupiter': [
        ' Jupiter',
        ' Io (J1)',
        ' Europa (J2)',
        ' Ganymede (J3)',
        ' Callisto (J4)',
        ' Amalthea (J5)',
        ' Thebe (J14)',
        ' Adrastea (J15)',
        ' Metis (J16)',
    ],
    'Saturn': [
        ' Saturn',
        ' Mimas (S1)',
        ' Enceladus (S2)',
        ' Tethys (S3)',
        ' Dione (S4)',
        ' Rhea (S5)',
        ' Titan (S6)',
        ' Hyperion (S7)',
        ' Iapetus (S8)',
        ' Phoebe (S9)',
        ' Janus (S10)',
        ' Epimetheus (S11)',
        ' Helene (S12)',
        ' Telesto (S13)',
        ' Calypso (S14)',
        ' Atlas (S15)',
        ' Prometheus (S16)',
        ' Pandora (S17)',
        ' Pan (S18)',
        ' Methone (S32)',
        ' Pallene (S33)',
        ' Polydeuces (S34)',
        ' Daphnis (S35)',
        ' Anthe (S49)',
        ' Aegaeon (S53)',
    ],
    'Uranus': [
        ' Uranus',
        ' Miranda (U5)',
        ' Ariel (U1)',
        ' Umbriel (U2)',
        ' Titania (U3)',
        ' Oberon (U4)',
        ' Cordelia (U6)',
        ' Ophelia (U7)',
        ' Bianca (U8)',
        ' Cressida (U9)',
        ' Desdemona (U10)',
        ' Juliet (U11)',
        ' Portia (U12)',
        ' Rosalind (U13)',
        ' Belinda (U14)',
        ' Puck (U15)',
        ' Perdita (U25)',
        ' Mab (U26)',
        ' Cupid (U27)',
    ],
    'Neptune': [
        ' Neptune',
        ' Triton (N1)',
        ' Nereid (N2)',
        ' Naiad (N3)',
        ' Thalassa (N4)',
        ' Despina (N5)',
        ' Galatea (N6)',
        ' Larissa (N7)',
        ' Proteus (N8)',
        ' Hippocamp (N14)',
    ],
    'Pluto': [
        ' Barycenter',
        ' Pluto',
        ' Charon (P1)',
        ' Nix (P2)',
        ' Hydra (P3)',
        ' Kerberos (P4)',
        ' Styx (P5)',
    ],
}
VIEWER_CENTER_ANSA: dict[str, list[str]] = {
    'Mars': [' Phobos Ring', ' Deimos Ring'],
    'Jupiter': [' Halo', ' Main Ring', ' Amalthea Ring', ' Thebe Ring'],
    'Saturn': [' C Ring', ' B Ring', ' A Ring', ' F Ring', ' G Ring', ' E Ring core'],
    'Uranus': [
        ' 6 Ring',
        ' 5 Ring',
        ' 4 Ring',
        ' Alpha Ring',
        ' Beta Ring',
        ' Eta Ring',
        ' Gamma Ring',
        ' Delta Ring',
        ' Lambda Ring',
        ' Epsilon Ring',
        ' Nu Ring',
        ' Mu Ring',
    ],
    'Neptune': [' Galle Ring', ' LeVerrier Ring', ' Arago Ring', ' Adams Ring'],
    'Pluto': [' Styx', ' Nix', ' Kerberos', ' Hydra'],
}
FOV_UNIT_COMMON = [' seconds of arc', ' degrees', ' milliradians', ' microradians', ' kilometers']
FOV_UNIT_PLANET: dict[str, list[str]] = {
    'Mars': [' Mars radii'],
    'Jupiter': [' Jupiter radii'],
    'Saturn': [' Saturn radii'],
    'Uranus': [' Uranus radii'],
    'Neptune': [' Neptune radii'],
    'Pluto': [' Pluto radii (1153 km)', ' Pluto-Charon separations (19,571 km)'],
}
VIEWER_MOONS_RADIO: dict[str, list[str]] = {
    'Mars': ['402 Phobos, Deimos'],
    'Jupiter': [
        '504 Galilean satellites (J1-J4)',
        '505 Galilean satellites, Amalthea (J1-J5)',
        '516 All inner moons (J1-J5,J14-J16)',
    ],
    'Saturn': [
        '609 Classical satellites (S1-S9)',
        '618 Classicals, Voyager discoveries (S1-S18)',
        '653 All inner moons (S1-S18,S32-S35,S49,S53)',
    ],
    'Uranus': [
        '705 Classical satellites (U1-U5)',
        '715 Classicals, Voyager discoveries (U1-U15)',
        '727 All inner moons (U1-U15,U25-U27)',
    ],
    'Neptune': ['802 Triton & Nereid', '814 All inner moons (N1-N8,N14)'],
    'Pluto': ['901 Charon (P1)', '903 Charon, Nix, Hydra (P1-P3)', '905 All moons (P1-P5)'],
}
VIEWER_RINGS: dict[str, list[str]] = {
    'Mars': ['None', 'Phobos, Deimos'],
    'Jupiter': ['None', 'Main', 'Main & Gossamer'],
    'Saturn': ['A,B,C', 'A,B,C,F', 'A,B,C,F,E', 'A,B,C,F,G,E'],
    'Uranus': [
        'Alpha, Beta, Eta, Gamma, Delta, Epsilon',
        'Nine major rings',
        'All inner rings',
        'All rings',
    ],
    'Neptune': ['LeVerrier, Adams', 'LeVerrier, Arago, Adams', 'Galle, LeVerrier, Arago, Adams'],
    'Pluto': [
        'None',
        'Charon',
        'Charon, Nix, Hydra',
        'Charon, Styx, Nix, Kerberos, Hydra',
        'Nix, Hydra',
        'Styx, Nix, Kerberos, Hydra',
    ],
}
TRACKER_MOONS: dict[str, list[str]] = {
    'Mars': ['001 Phobos (M1)', '002 Deimos (M2)'],
    'Jupiter': [
        '001 Io (J1)',
        '002 Europa (J2)',
        '003 Ganymede (J3)',
        '004 Callisto (J4)',
        '005 Amalthea (J5)',
        '014 Thebe (J14)',
        '015 Adrastea (J15)',
        '016 Metis (J16)',
    ],
    'Saturn': [
        '001 Mimas (S1)',
        '002 Enceladus (S2)',
        '003 Tethys (S3)',
        '004 Dione (S4)',
        '005 Rhea (S5)',
        '006 Titan (S6)',
        '007 Hyperion (S7)',
        '008 Iapetus (S8)',
        '009 Phoebe (S9)',
        '010 Janus (S10)',
        '011 Epimetheus (S11)',
        '012 Helene (S12)',
        '013 Telesto (S13)',
        '014 Calypso (S14)',
        '015 Atlas (S15)',
        '016 Prometheus (S16)',
        '017 Pandora (S17)',
        '018 Pan (S18)',
        '032 Methone (S32)',
        '033 Pallene (S33)',
        '034 Polydeuces (S34)',
        '035 Daphnis (S35)',
        '049 Anthe (S49)',
        '053 Aegaeon (S53)',
    ],
    'Uranus': [
        '001 Ariel (U1)',
        '002 Umbriel (U2)',
        '003 Titania (U3)',
        '004 Oberon (U4)',
        '005 Miranda (U5)',
        '006 Cordelia (U6)',
        '007 Ophelia (U7)',
        '008 Bianca (U8)',
        '009 Cressida (U9)',
        '010 Desdemona (U10)',
        '011 Juliet (U11)',
        '012 Portia (U12)',
        '013 Rosalind (U13)',
        '014 Belinda (U14)',
        '015 Puck (U15)',
        '025 Perdita (U25)',
        '026 Mab (U26)',
        '027 Cupid (U27)',
    ],
    'Neptune': [
        '001 Triton (N1)',
        '002 Nereid (N2)',
        '003 Naiad (N3)',
        '004 Thalassa (N4)',
        '005 Despina (N5)',
        '006 Galatea (N6)',
        '007 Larissa (N7)',
        '008 Proteus (N8)',
        '014 Hippocamp (N14)',
    ],
    'Pluto': [
        '001 Charon (P1)',
        '005 Styx (P5)',
        '002 Nix (P2)',
        '004 Kerberos (P4)',
        '003 Hydra (P3)',
    ],
}
TRACKER_RINGS: dict[str, list[str]] = {
    'Jupiter': ['051 Main Ring', '052 Gossamer Rings'],
    'Saturn': ['061 Main Rings', '062 G Ring', '063 E Ring'],
    'Uranus': ['071 Epsilon Ring'],
    'Neptune': ['081 Adams Ring'],
}

# Tracker xunit (plot scale): per planet only arcsec and that planet's radii (no leading space).
TRACKER_XUNIT_BY_PLANET: dict[str, list[str]] = {
    'Mars': ['arcsec', 'Mars radii'],
    'Jupiter': ['arcsec', 'Jupiter radii'],
    'Saturn': ['arcsec', 'Saturn radii'],
    'Uranus': ['arcsec', 'Uranus radii'],
    'Neptune': ['arcsec', 'Neptune radii'],
    'Pluto': ['arcsec', 'Pluto radii'],
}

# Ephemeris columns (Earth-based; [Planet] replaced)
EPHEM_COLUMNS_EMPTY = [
    '001 Modified Julian Date',
    '002 Year, Month, Day, Hour, Minute',
    '003 Year, Month, Day, Hour, Minute, Second',
    '004 Year, DOY, Hour, Minute',
    '005 Year, DOY, Hour, Minute, Second',
    '006 Observer-{planet} distance',
    '007 Sun-{planet} distance',
    '008 {planet} phase angle',
    '009 Ring plane opening angle to observer',
    '010 Ring plane opening angle to Sun',
    '011 Sub-observer inertial longitude',
    '012 Sub-solar inertial longitude',
    '013 Sub-observer latitude & rotating longitude',
    '014 Sub-solar latitude & rotating longitude',
    '015 {planet} RA & Dec',
    '018 {planet} projected equatorial radius (arcsec)',
    '020 Lunar phase angle',
    '021 Sun-{planet} sky separation angle',
    '022 Lunar-{planet} sky separation angle',
]
EPHEM_COLUMNS_PREFIX = [
    '001 Modified Julian Date',
    '002 Year, Month, Day, Hour, Minute',
    '003 Year, Month, Day, Hour, Minute, Second',
    '004 Year, DOY, Hour, Minute',
    '005 Year, DOY, Hour, Minute, Second',
    '006 Observer-{planet} distance',
    '007 Sun-{planet} distance',
    '008 {planet} phase angle',
    '009 Ring plane opening angle to observer',
    '010 Ring plane opening angle to Sun',
    '011 Sub-observer inertial longitude',
    '012 Sub-solar inertial longitude',
    '013 Sub-observer latitude & rotating longitude',
    '014 Sub-solar latitude & rotating longitude',
    '015 {planet} RA & Dec',
    '016 Earth RA & Dec',
    '017 Sun RA & Dec',
    '019 {planet} projected equatorial radius (deg)',
]
EPHEM_MOONCOLS_EMPTY = [
    '003 Sub-observer latitude & rotating longitude',
    '004 Sub-solar latitude & rotating longitude',
    '005 RA & Dec',
    '006 Offset RA & Dec from the moon',
    '008 Orbital longitude relative to observer',
    '009 Orbit plane opening angle to observer',
]
EPHEM_MOONCOLS_PREFIX = [
    '001 Observer-moon distance',
    '002 Moon phase angle',
    '003 Sub-observer latitude & rotating longitude',
    '004 Sub-solar latitude & rotating longitude',
    '005 RA & Dec',
    '007 Offset RA & Dec from the moon',
    '008 Orbital longitude relative to observer',
    '009 Orbit plane opening angle to observer',
]

# ---------------------------------------------------------------------------
# Random value helpers
# ---------------------------------------------------------------------------


# Bounds for time range and interval: ensure 2 <= ntimes <= max_steps.
# Tracker limit 10000, ephemeris 100000.
_TRACKER_MAX_STEPS = 10000
_EPHEM_MAX_STEPS = 10000
_SECONDS_PER_DAY = 86400.0


def _random_datetime(
    min_dt: datetime | None = None,
    max_dt: datetime | None = None,
) -> str:
    """Return a random UTC datetime in yyyy-mm-dd hh:mm:ss form."""
    if min_dt is not None and max_dt is not None:
        delta = (max_dt - min_dt).days
        if delta < 0:
            delta = 0
        offset_days = random.randint(0, max(0, delta))
        dt = min_dt + timedelta(days=offset_days)
        dt = dt.replace(
            hour=random.randint(0, 23),
            minute=random.randint(0, 59),
            second=random.randint(0, 59),
        )
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    year = random.randint(1990, 2030)
    month = random.randint(1, 12)
    day = random.randint(1, 28)
    hour = random.randint(0, 23)
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return f'{year:04d}-{month:02d}-{day:02d} {hour:02d}:{minute:02d}:{second:02d}'


def _contextual_spacecraft_abbrev(*, abbrev: str, body_name: str) -> str | None:
    """Return mission abbrev for spacecraft in this planet context.

    This enforces that selecting a spacecraft in "other" uses the same SPICE
    window as if that spacecraft were selected as viewpoint for this planet.
    """
    planet_short = abbrev[:3].lower()
    if body_name == 'Cassini':
        if planet_short == 'jup':
            return 'jupc'
        if planet_short == 'sat':
            return 'satc'
    if body_name == 'New Horizons':
        if planet_short == 'jup':
            return 'jupnh'
        if planet_short == 'plu':
            return 'plunh'
    if body_name == 'Juno' and planet_short == 'jup':
        return 'jupj'
    if body_name == 'JUICE' and planet_short == 'jup':
        return 'jupjc'
    if body_name == 'Europa Clipper' and planet_short == 'jup':
        return 'jupec'
    # Voyager overrides are already keyed by planet short abbrev (jup/sat/ura/nep).
    if body_name in {'Voyager 1', 'Voyager 2'}:
        return planet_short
    return None


def _range_for_body(*, abbrev: str, body_name: str) -> tuple[datetime, datetime] | None:
    """Return date range for one observatory/body in the current abbrev context."""
    canonical_body_name = body_name.strip().rstrip('/')
    override = OBSERVATORY_ABBREV_DATE_RANGES.get((abbrev, canonical_body_name))
    if override is not None:
        return override
    contextual_abbrev = _contextual_spacecraft_abbrev(abbrev=abbrev, body_name=canonical_body_name)
    if contextual_abbrev is not None:
        contextual = OBSERVATORY_ABBREV_DATE_RANGES.get((contextual_abbrev, canonical_body_name))
        if contextual is not None:
            return contextual
    return OBSERVATORY_DATE_RANGES.get(canonical_body_name)


def _intersect_date_ranges(
    ranges: list[tuple[datetime, datetime]],
) -> tuple[datetime, datetime] | None:
    """Return the intersection of date ranges or None if empty."""
    if len(ranges) == 0:
        return None
    start = max(r[0] for r in ranges)
    stop = min(r[1] for r in ranges)
    if start > stop:
        return None
    return (start, stop)


def _combined_spice_range(
    *,
    abbrev: str,
    observatory: str | None,
    other_bodies: list[str] | None = None,
) -> tuple[datetime, datetime] | None:
    """Return combined SPICE-safe range from mission, observatory, and other bodies."""
    canonical_others = [str(body).strip().rstrip('/') for body in (other_bodies or [])]
    effective_abbrev = abbrev
    # Pluto + New Horizons (as "other") must use the Pluto encounter window.
    if abbrev[:3].lower() == 'plu' and 'New Horizons' in canonical_others:
        effective_abbrev = 'plunh'

    ranges: list[tuple[datetime, datetime]] = []
    mission_range = MISSION_DATE_RANGES.get(effective_abbrev)
    if mission_range is not None:
        ranges.append(mission_range)
    if observatory:
        obs_range = _range_for_body(abbrev=effective_abbrev, body_name=observatory)
        if obs_range is not None:
            ranges.append(obs_range)
    for body in canonical_others:
        body_range = _range_for_body(abbrev=effective_abbrev, body_name=body)
        if body_range is not None:
            ranges.append(body_range)
    return _intersect_date_ranges(ranges)


def _random_time_range_and_interval(
    abbrev: str = '',
    observatory: str | None = None,
    *,
    max_steps: int = _EPHEM_MAX_STEPS,
) -> tuple[str, str, str, str]:
    """Return (start_str, stop_str, interval_str, time_unit) with valid step count.

    Chooses delta_days, interval, and time_unit so that
    10 <= ntimes <= _MAX_STEPS, avoiding "too many steps" and
    "time range too short or interval too large" errors.
    When abbrev is a spacecraft (jupc, jupj, satc, etc.), constrains dates to
    mission SPICE kernel limits. When observatory has limited ephemeris (e.g.
    JWST), constrains to OBSERVATORY_DATE_RANGES.
    """
    mission_range = MISSION_DATE_RANGES.get(abbrev)
    obs_range = OBSERVATORY_ABBREV_DATE_RANGES.get((abbrev, observatory or ''))
    if not obs_range:
        obs_range = OBSERVATORY_DATE_RANGES.get(observatory or '') if observatory else None
    # Prefer observatory range when set (e.g. JWST, plunh+New Horizons); else mission.
    date_range = obs_range if obs_range else mission_range
    if date_range:
        min_dt, max_dt = date_range
        now = datetime.now(timezone.utc)
        if max_dt <= min_dt:
            # Mission not started yet or invalid range; use recent past.
            max_dt = now
            min_dt = now - timedelta(days=30)
    else:
        # No constrained range; use a broad recent span.
        max_dt = datetime.now(timezone.utc)
        min_dt = max_dt - timedelta(days=3650)

    span_sec_full = int((max_dt - min_dt).total_seconds())
    if span_sec_full < 60:
        # Ensure we can always draw two points at least one minute apart.
        min_dt = max_dt - timedelta(minutes=1)
        span_sec_full = 60

    # Pick two random timestamps in the available span; keep trying until they
    # are at least 60 seconds apart.
    start_dt = min_dt
    stop_dt = max_dt
    for _ in range(200):
        offset_a = random.randint(0, span_sec_full)
        offset_b = random.randint(0, span_sec_full)
        a = min_dt + timedelta(seconds=offset_a)
        b = min_dt + timedelta(seconds=offset_b)
        lo, hi = (a, b) if a <= b else (b, a)
        if (hi - lo).total_seconds() >= 60:
            start_dt, stop_dt = lo, hi
            break
    else:
        start_dt = min_dt
        stop_dt = min_dt + timedelta(seconds=60)

    total_sec = max(60.0, (stop_dt - start_dt).total_seconds())
    start_str = start_dt.strftime('%Y-%m-%d %H:%M:%S')
    stop_str = stop_dt.strftime('%Y-%m-%d %H:%M:%S')

    time_unit = _pick(TIME_UNIT)
    nsteps = random.randint(1, max_steps)
    interval_sec = total_sec / nsteps
    # Round up to whole minutes because this is what the tracker does
    interval_sec = math.ceil(interval_sec / 60.0) * 60.0
    if interval_sec <= 0:
        interval_sec = 60.0

    mult = {
        'seconds': 1.0,
        'minutes': 60.0,
        'hours': 3600.0,
        'days': _SECONDS_PER_DAY,
    }[time_unit]
    interval_val = interval_sec / mult

    if interval_val == int(interval_val):
        interval_str = str(int(interval_val))
    else:
        interval_str = f'{interval_val:.4f}'.rstrip('0').rstrip('.')

    return start_str, stop_str, interval_str, time_unit


def _random_numeric(low: float = 0.1, high: float = 100.0, decimals: int = 4) -> str:
    """Return a random numeric string."""
    v = random.uniform(low, high)
    if decimals == 0:
        return str(round(v))
    return f'{v:.{decimals}f}'.rstrip('0').rstrip('.')


def _maybe(p: float = 0.5) -> bool:
    """Return True with probability p."""
    return random.random() < p


def _pick(lst: list[str]) -> str:
    """Return a random element from a non-empty list."""
    return random.choice(lst)


def _pick_multi(lst: list[str], min_n: int = 0, max_n: int | None = None) -> list[str]:
    """Return a random subset; max_n defaults to len(lst)."""
    if max_n is None:
        max_n = len(lst)
    n = random.randint(min_n, min(max_n, len(lst)))
    return random.sample(lst, n)


# ---------------------------------------------------------------------------
# Query builders
# ---------------------------------------------------------------------------


def _build_viewer_query(abbrev: str) -> str:
    """Build URL-encoded viewer query parameters for a given body abbreviation.

    Viewpoint, observatory (or lat/lon), center, moons, rings, and diagram options
    are chosen via helpers (_planet, _prefix, _maybe, _pick, _pick_multi,
    _random_datetime, _load_starlist) and constants (EPHEM_BY_ABBREV, etc.).
    SPICE coverage is computed with _combined_spice_range; if the selected
    "other" bodies lack coverage, fallbacks omit or reselect them. Time is
    chosen within the combined SPICE range when available.

    Parameters:
        abbrev: Body abbreviation (e.g. 'sat', 'jup').

    Returns:
        URL-encoded query string via urlencode(params, doseq=True, encoding='utf-8').
    """
    planet = _planet(abbrev)
    pre = _prefix(abbrev)
    params: dict[str, Any] = {}

    def _val(raw: str) -> str:
        """Return value trimmed; no leading space (would encode as + in URL)."""
        return raw.strip()

    # Viewpoint/observatory first (needed to constrain time for JWST etc.)
    # Observatories: no leading space (FORTRAN/cgi expect exact match e.g. 'Voyager 1').
    if pre:
        params['viewpoint'] = 'observatory'
        mission_obs = {
            'Cassini/': 'Cassini',
            'New Horizons/': 'New Horizons',
            'Juno/': 'Juno',
            'JUICE/': 'JUICE',
            'Europa Clipper/': 'Europa Clipper',
        }
        params['observatory'] = mission_obs.get(pre, "Earth's center")
    else:
        if _maybe(0.8):
            params['viewpoint'] = 'observatory'
            obs_list = VIEWER_OBSERVATORIES_BY_PLANET.get(planet, OBSERVATORIES_EARTH)
            params['observatory'] = _pick(obs_list)
        else:
            params['viewpoint'] = 'latlon'
            params['latitude'] = _random_numeric(-90, 90, 4)
            params['longitude'] = _random_numeric(0, 360, 4)
            params['lon_dir'] = _val(_pick(LON_DIR))
            params['altitude'] = _random_numeric(0, 4500, 0)

    # Mandatory and always-included
    params['abbrev'] = abbrev
    params['version'] = '3.1'
    params['ephem'] = EPHEM_BY_ABBREV[abbrev]
    params['fov'] = _random_numeric(0.001, 50.0)
    fov_opts = FOV_UNIT_COMMON + FOV_UNIT_PLANET.get(planet, [' Jupiter radii'])
    # fov_unit: no leading space (FORTRAN expects e.g. 'degrees' not ' degrees').
    params['fov_unit'] = _pick(fov_opts).strip()
    params['output'] = 'HTML'

    # Center: always set to avoid FORTRAN defaulting to star with empty center_star (Mars/Pluto).
    # center=star: use only star names from the planet's starlist.
    center_opts = ['body', 'ansa', 'J2000']
    stars = _load_starlist(abbrev)
    if stars:
        center_opts.append('star')
    params['center'] = _pick(center_opts)
    if params['center'] == 'body':
        bodies = VIEWER_CENTER_BODY.get(planet, VIEWER_CENTER_BODY['Jupiter'])
        params['center_body'] = _val(_pick(bodies))
    elif params['center'] == 'ansa':
        ansas = VIEWER_CENTER_ANSA.get(planet, VIEWER_CENTER_ANSA['Jupiter'])
        params['center_ansa'] = _val(_pick(ansas))
        params['center_ew'] = _val(_pick(CENTER_EW))
    elif params['center'] == 'J2000':
        params['center_ra'] = _random_numeric(0, 24, 4)
        params['center_ra_type'] = _val(_pick(RA_TYPE))
        params['center_dec'] = _random_numeric(-90, 90, 4)
    elif params['center'] == 'star':
        params['center_star'] = _pick(stars)

    # Moons (viewer uses single radio value)
    if planet in VIEWER_MOONS_RADIO:
        params['moons'] = _pick(VIEWER_MOONS_RADIO[planet])

    # Rings: SHTML always submits one selected radio value.
    if planet in VIEWER_RINGS:
        params['rings'] = _pick(VIEWER_RINGS[planet])

    # Neptune arc model: FORTRAN requires it when Neptune has rings (default includes rings).
    if planet == 'Neptune':
        params['arcmodel'] = _pick(
            ['#1 (820.1194 deg/day)', '#2 (820.1118 deg/day)', '#3 (820.1121 deg/day)']
        )

    # Optional diagram options
    if _maybe(0.4):
        params['title'] = 'Test plot'
    params['labels'] = _val(_pick(LABELS) if _maybe(0.7) else 'Small (6 points)')
    # Moon enlargement and blank disks: always present (viewer/form requirement).
    params['moonpts'] = str(random.randint(0, 5))
    params['blank'] = _pick(BLANK)
    if planet == 'Saturn':
        # SHTML always sends ring_plot_type with default Transparent.
        params['opacity'] = _pick(OPACITY) if _maybe(0.3) else 'Transparent'
    if planet in ('Saturn', 'Uranus'):
        if _maybe(0.2):
            params['peris'] = _pick(
                ['None', 'F Ring']
                if planet == 'Saturn'
                else ['None', 'Epsilon Ring only', 'All rings']
            )
            params['peripts'] = str(random.randint(2, 8))
        else:
            # FORTRAN rejects blank PERICENTER_MARKERS/PERIPTS in some viewer modes.
            params['peris'] = 'None'
            params['peripts'] = '4'
    if _maybe(0.7):
        params['meridians'] = _pick(MERIDIANS)
    if planet == 'Neptune':
        # FORTRAN viewer requires ARC_WEIGHT to be present and positive.
        params['arcpts'] = str(random.randint(2, 8))

    # Jupiter torus
    if planet == 'Jupiter' and _maybe(0.2):
        params['torus'] = 'Yes'
        params['torus_inc'] = '6.8'
        params['torus_rad'] = '422000'

    # Background: standard stars, additional star, other
    if _maybe(0.3):
        params['standard'] = 'Yes'
    if _maybe(0.2):
        params['additional'] = 'Yes'
        params['extra_ra'] = _random_numeric(0, 24, 4)
        params['extra_ra_type'] = _val(_pick(RA_TYPE))
        params['extra_dec'] = _random_numeric(-90, 90, 4)
        params['extra_name'] = 'Star1'
    other_pool: list[str] | None = None
    if _maybe(0.4):
        others = ['Sun', 'Anti-Sun', 'Earth']
        if planet == 'Jupiter' and not pre:
            others += [
                'Voyager 1',
                'Voyager 2',
                'Galileo',
                'Cassini',
                'New Horizons',
                'Juno',
                'JUICE',
                'Europa Clipper',
            ]
        elif planet == 'Saturn' and not pre:
            others += ['Voyager 1', 'Voyager 2', 'Cassini']
        elif planet in ('Uranus', 'Neptune') and not pre:
            others += ['Voyager 2']
        elif planet == 'Pluto':
            others += ['Barycenter', 'New Horizons'] if not pre else ['Barycenter']
        other_pool = others
        # FORTRAN expects separate other= params; use list + doseq for multiple values.
        params['other'] = _pick_multi(others, 1, 3)

    # Observation time must satisfy all selected SPICE-constrained bodies.
    time_kw: dict[str, datetime] = {}
    combined_range = _combined_spice_range(
        abbrev=abbrev,
        observatory=str(params.get('observatory') or ''),
        other_bodies=[str(x) for x in params.get('other') or []],
    )
    # Keep random "other" bodies, but ensure selected combination has SPICE coverage.
    if combined_range is None and other_pool is not None:
        for _ in range(20):
            candidate_other = _pick_multi(other_pool, 1, 3)
            candidate_range = _combined_spice_range(
                abbrev=abbrev,
                observatory=str(params.get('observatory') or ''),
                other_bodies=[str(x) for x in candidate_other],
            )
            if candidate_range is not None:
                params['other'] = candidate_other
                combined_range = candidate_range
                break
        if combined_range is None:
            # Fallback: omit "other" rather than generating known-SPICE-invalid URLs.
            params.pop('other', None)
            combined_range = _combined_spice_range(
                abbrev=abbrev,
                observatory=str(params.get('observatory') or ''),
                other_bodies=[],
            )
    if combined_range is not None:
        min_dt, max_dt = combined_range
        now = datetime.now(timezone.utc)
        max_dt = min(max_dt, now)
        if min_dt <= max_dt:
            time_kw = {'min_dt': min_dt, 'max_dt': max_dt}
    params['time'] = _random_datetime(**time_kw)

    return urlencode(params, doseq=True, encoding='utf-8')


def _build_tracker_query(abbrev: str) -> str:
    """Build URL-encoded tracker query parameters for a given body abbreviation.

    Sets viewpoint, observatory or lat/lon, start/stop/interval via
    _random_time_range_and_interval, and optionally moons, rings, and xunit.
    Uses _planet, _prefix, _maybe, _pick and urlencode.

    Parameters:
        abbrev: Body abbreviation (e.g. 'sat', 'jup').

    Returns:
        URL-encoded query string.
    """
    planet = _planet(abbrev)
    pre = _prefix(abbrev)
    params: dict[str, Any] = {}

    params['abbrev'] = abbrev
    params['version'] = '3.0'
    params['ephem'] = EPHEM_BY_ABBREV[abbrev]

    if pre:
        params['viewpoint'] = 'observatory'
        mission_obs = {
            'Cassini/': 'Cassini',
            'New Horizons/': 'New Horizons',
            'Juno/': 'Juno',
            'JUICE/': 'JUICE',
            'Europa Clipper/': 'Europa Clipper',
        }
        params['observatory'] = mission_obs.get(pre, "Earth's center")
        params['latitude'] = ''
        params['longitude'] = ''
        params['lon_dir'] = 'east'
        params['altitude'] = ''
    else:
        if _maybe(0.8):
            params['viewpoint'] = 'observatory'
            params['observatory'] = _pick(OBSERVATORIES_EARTH)
            params['latitude'] = ''
            params['longitude'] = ''
            params['lon_dir'] = 'east'
            params['altitude'] = ''
        else:
            params['viewpoint'] = 'latlon'
            params['latitude'] = _random_numeric(-90, 90, 4)
            params['longitude'] = _random_numeric(0, 360, 4)
            params['lon_dir'] = _pick(LON_DIR)
            params['altitude'] = _random_numeric(0, 4500, 0)

    start_str, stop_str, interval_str, time_unit = _random_time_range_and_interval(
        abbrev, observatory=params.get('observatory'), max_steps=_TRACKER_MAX_STEPS
    )
    params['start'] = start_str
    params['stop'] = stop_str
    params['interval'] = interval_str
    params['time_unit'] = time_unit
    params['output'] = 'HTML'

    if planet in TRACKER_MOONS:
        moon_list = TRACKER_MOONS[planet]
        params['moons'] = _pick_multi(moon_list, min_n=1, max_n=min(4, len(moon_list)))

    if planet in TRACKER_RINGS and _maybe(0.6):
        rlist = TRACKER_RINGS[planet]
        params['rings'] = _pick_multi(rlist, min_n=1)

    # FORTRAN tracker requires xrange and xunit (plot_scale); xunit only arcsec or planet radii.
    params['xrange'] = _random_numeric(1, 50, 2)
    xunit_opts = (
        ['degrees', f'{planet} radii']
        if pre
        else TRACKER_XUNIT_BY_PLANET.get(planet, ['arcsec', 'Jupiter radii'])
    )
    params['xunit'] = _pick(xunit_opts)
    if _maybe(0.3):
        params['title'] = 'Tracker test'

    return urlencode(params, doseq=True, encoding='utf-8')


def _build_ephemeris_query(abbrev: str) -> str:
    """Build and return a URL-encoded ephemeris query string for a body abbreviation.

    Uses _planet, _prefix, _random_time_range_and_interval, EPHEM_BY_ABBREV,
    OBSERVATORIES_EARTH, TRACKER_MOONS; may set viewpoint, observatory, columns,
    mooncols, moons, start/stop/interval/time_unit and output. Requires at least
    one general column or both moons and mooncols for a valid query.

    Parameters:
        abbrev: Body abbreviation (str).

    Returns:
        URL-encoded query string (urlencode with doseq=True, encoding='utf-8').
    """
    planet = _planet(abbrev)
    pre = _prefix(abbrev)
    params: dict[str, Any] = {}

    params['abbrev'] = abbrev
    params['version'] = '3.0'
    params['ephem'] = EPHEM_BY_ABBREV[abbrev]

    if pre:
        params['viewpoint'] = 'observatory'
        mission_obs = {
            'Cassini/': 'Cassini',
            'New Horizons/': 'New Horizons',
            'Juno/': 'Juno',
            'JUICE/': 'JUICE',
            'Europa Clipper/': 'Europa Clipper',
        }
        params['observatory'] = mission_obs.get(pre, "Earth's center")
        params['latitude'] = ''
        params['longitude'] = ''
        params['lon_dir'] = 'east'
        params['altitude'] = ''
    else:
        if _maybe(0.8):
            params['viewpoint'] = 'observatory'
            params['observatory'] = _pick(OBSERVATORIES_EARTH)
            params['latitude'] = ''
            params['longitude'] = ''
            params['lon_dir'] = 'east'
            params['altitude'] = ''
        else:
            params['viewpoint'] = 'latlon'
            params['latitude'] = _random_numeric(-90, 90, 4)
            params['longitude'] = _random_numeric(0, 360, 4)
            params['lon_dir'] = _pick(LON_DIR)
            params['altitude'] = _random_numeric(0, 4500, 0)

    start_str, stop_str, interval_str, time_unit = _random_time_range_and_interval(
        abbrev, observatory=params.get('observatory')
    )
    params['start'] = start_str
    params['stop'] = stop_str
    params['interval'] = interval_str
    params['time_unit'] = time_unit
    params['output'] = 'HTML'

    if _maybe(0.9):
        template = EPHEM_COLUMNS_PREFIX if pre else EPHEM_COLUMNS_EMPTY
        cols = [c.format(planet=planet) for c in template]
        params['columns'] = _pick_multi(cols, min_n=1, max_n=8)

    if _maybe(0.6):
        template = EPHEM_MOONCOLS_PREFIX if pre else EPHEM_MOONCOLS_EMPTY
        params['mooncols'] = _pick_multi(template, min_n=1, max_n=5)

    if planet in TRACKER_MOONS and _maybe(0.8):
        moon_list = TRACKER_MOONS[planet]
        params['moons'] = _pick_multi(moon_list, min_n=1, max_n=min(4, len(moon_list)))

    # Valid ephemeris requires: at least one general column, OR (moons + mooncols).
    has_columns = len(params.get('columns', [])) > 0
    has_moons = len(params.get('moons', [])) > 0
    has_mooncols = len(params.get('mooncols', [])) > 0
    if not has_columns and not (has_moons and has_mooncols):
        if planet in TRACKER_MOONS and _maybe(0.5):
            template = EPHEM_MOONCOLS_PREFIX if pre else EPHEM_MOONCOLS_EMPTY
            params['mooncols'] = _pick_multi(template, min_n=1, max_n=5)
            moon_list = TRACKER_MOONS[planet]
            params['moons'] = _pick_multi(moon_list, min_n=1, max_n=min(4, len(moon_list)))
        else:
            cols = [c.format(planet=planet) for c in (EPHEM_COLUMNS_PREFIX if pre else EPHEM_COLUMNS_EMPTY)]
            params['columns'] = _pick_multi(cols, min_n=1, max_n=8)

    return urlencode(params, doseq=True, encoding='utf-8')


def generate_one_url(tool: str) -> str:
    """Generate a single random full URL for the given tool.

    Parameters:
        tool: One of "viewer", "tracker", "ephemeris".

    Returns:
        Full URL (e.g. https://pds-rings.seti.org/cgi-bin/tools/ephem3_xxx.pl?key=val&...).
    """
    if tool == 'viewer':
        abbrev = _pick(VIEWER_ABBREVS)
        query = _build_viewer_query(abbrev)
    elif tool == 'tracker':
        abbrev = _pick(TRACKER_ABBREVS)
        query = _build_tracker_query(abbrev)
    elif tool == 'ephemeris':
        abbrev = _pick(EPHEMERIS_ABBREVS)
        query = _build_ephemeris_query(abbrev)
    else:
        raise ValueError(f'Unknown tool: {tool}')
    script = TOOL_CGI_SCRIPT[tool]
    return f'{BASE_URL}/cgi-bin/tools/{script}?{query}'


def main() -> int:
    """Generate N random CGI query strings and write them to an output file.

    Uses argparse: --count (N), --output (file), --tool (viewer/tracker/ephemeris),
    --seed (optional). Sets random.seed when --seed is given. Writes one URL per
    line via generate_one_url. Returns 0 on success, 1 on I/O error.
    """
    parser = argparse.ArgumentParser(
        description='Generate random CGI query strings for Viewer, Tracker, and Ephemeris tools.',
    )
    parser.add_argument(
        '-n',
        '--count',
        type=int,
        required=True,
        metavar='N',
        help='Number of query strings to generate.',
    )
    parser.add_argument(
        '-o',
        '--output',
        type=str,
        required=True,
        metavar='FILE',
        help='Output file path (one query string per line).',
    )
    parser.add_argument(
        '--tool',
        type=str,
        choices=['viewer', 'tracker', 'ephemeris'],
        default=None,
        help='Restrict to one tool; default is to choose randomly among all three.',
    )
    parser.add_argument(
        '--seed',
        type=int,
        default=None,
        metavar='N',
        help='Random seed for reproducibility.',
    )
    args = parser.parse_args()

    if args.count < 1:
        parser.error('--count must be at least 1')
    if args.seed is not None:
        random.seed(args.seed)

    tools = [args.tool] if args.tool else ['viewer', 'tracker', 'ephemeris']

    try:
        with open(args.output, 'w', encoding='utf-8') as f:
            for _ in range(args.count):
                tool = random.choice(tools)
                url = generate_one_url(tool)
                f.write(url + '\n')
    except OSError as e:
        print(f'Error writing {args.output}: {e}', file=sys.stderr)
        return 1

    print(f'Wrote {args.count} URL(s) to {args.output}', file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
