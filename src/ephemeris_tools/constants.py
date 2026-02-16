"""Fixed constants: body IDs, spacecraft names/codes, planet number mapping (from tools.inc)."""

# Body IDs (NAIF)
SUN_ID = 10
EARTH_ID = 399
MOON_ID = 301

# String length constants (for compatibility with FORTRAN column widths)
EPHEM_ID_LEN = 4
MOON_ID_LEN = 4
SC_ID_LEN = 4
COL_ID_LEN = 8
FOV_LEN = 12

# Spacecraft: full name, abbreviation, NAIF code (from tools.inc)
SPACECRAFT_NAMES = (
    'Voyager 1',
    'Voyager 2',
    'Galileo',
    'Cassini',
    'New Horizons',
    'Juno',
    'Europa Clipper',
    'JUICE',
    'JWST',
    'HST',
)
SPACECRAFT_IDS = (
    'VG1',
    'VG2',
    'GLL',
    'CAS',
    'NH',
    'JNO',
    'EC',
    'JCE',
    'JWST',
    'HST',
)
SPACECRAFT_CODES = (-31, -32, -77, -82, -98, -61, -159, -28, -170, -48)

NSPACECRAFTS = 10

# Planet number (4=Mars .. 9=Pluto) -> NAIF planet ID
PLANET_NUM_TO_ID: dict[int, int] = {
    4: 499,  # Mars
    5: 599,  # Jupiter
    6: 699,  # Saturn
    7: 799,  # Uranus
    8: 899,  # Neptune
    9: 999,  # Pluto
}

# NAIF planet ID -> planet number
PLANET_ID_TO_NUM: dict[int, int] = {v: k for k, v in PLANET_NUM_TO_ID.items()}

# Planet number → ephemeris kernel description (right-hand side of "Ephemeris:" in plot).
# FORTRAN/web use "NNN DESCRIPTION"; we show DESCRIPTION. Matches web/tools/EPHEMERIS_INFO.shtml.
EPHEM_DESCRIPTIONS_BY_PLANET: dict[int, str] = {
    4: 'MAR097 + DE440',
    5: 'JUP365 + DE440',
    6: 'SAT415 + SAT441 + DE440',
    7: 'URA111 + URA115 + DE440',
    8: 'NEP095 + NEP097 + NEP101 + DE440',
    9: 'PLU058 + DE440',
}


def spacecraft_code_to_id(sc_code: int) -> str | None:
    """Return spacecraft abbreviation for NAIF code (port of RSPK_GetSCID inverse).

    Parameters:
        sc_code: NAIF spacecraft ID (e.g. -82 for Cassini).

    Returns:
        Abbreviation (e.g. 'CAS') or None if unknown.
    """
    for i, code in enumerate(SPACECRAFT_CODES):
        if code == sc_code:
            return SPACECRAFT_IDS[i]
    return None


def spacecraft_name_to_code(name: str) -> int | None:
    """Return NAIF ID for spacecraft by name or abbreviation (port of RSPK_GetSCID).

    Parameters:
        name: Full name or ID (e.g. 'VG1', 'Voyager 1', 'CASSINI').

    Returns:
        NAIF integer ID or None if not found.
    """
    name_upper = name.strip().upper()
    for i, abbr in enumerate(SPACECRAFT_IDS):
        if abbr == name_upper:
            return SPACECRAFT_CODES[i]
    for i, full_name in enumerate(SPACECRAFT_NAMES):
        if full_name.upper() == name_upper:
            return SPACECRAFT_CODES[i]
    return None
