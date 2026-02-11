c***********************************************************************
c tools.inc
c
c Fixed parameters for ephemeris tools.
c***********************************************************************

        character*(*)   JULIAN_LEAPSECS
        parameter       (JULIAN_LEAPSECS =
     &                  '/var/www/SPICE/leapsecs.txt')

        character*(*)   TEMP_PATH
        parameter       (TEMP_PATH =
     &                  '/var/www/work/')

        character*(*)   STARLIST_PATH
        parameter       (STARLIST_PATH =
     &                  '/var/www/documents/tools/')

        integer         EPHEM_ID_LEN, MOON_ID_LEN, SC_ID_LEN, COL_ID_LEN
        integer         FOV_LEN
        parameter       (EPHEM_ID_LEN =  4)
        parameter       (MOON_ID_LEN  =  4)
        parameter       (SC_ID_LEN    =  4)
        parameter       (COL_ID_LEN   =  8)
        parameter       (FOV_LEN      = 12)

        integer         SUN_ID, EARTH_ID, MOON_ID
        parameter       (SUN_ID   =  10)
        parameter       (EARTH_ID = 399)
        parameter       (MOON_ID  = 301)

c Spacecraft parameters
        integer                 NSPACECRAFTS
        parameter               (NSPACECRAFTS = 10)
        character*20            SC_NAMES(NSPACECRAFTS) /
     &                                  'Voyager 1',
     &                                  'Voyager 2',
     &                                  'Galileo',
     &                                  'Cassini',
     &                                  'New Horizons',
     &                                  'Juno',
     &                                  'Europa Clipper',
     &                                  'JUICE',
     &                                  'JWST',
     &                                  'HST' /
        character*4             SC_IDS(NSPACECRAFTS) /
     &                                  'VG1', 'VG2', 'GLL',
     &                                  'CAS', 'NH', 'JNO', 'EC', 'JCE',
     &                                  'JWST', 'HST' /
        integer                 SC_CODES(NSPACECRAFTS) /
     &                                  -31, -32, -77,
     &                                  -82, -98, -61, -159, -28,
     &                                  -170, -48 /

c***********************************************************************
