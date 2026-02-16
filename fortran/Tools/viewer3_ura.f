c***********************************************************************
c***********************************************************************

        program VIEWER3_URA

        implicit                none
        include                 'tools.inc'

        integer                 NPLANET, PLANET_ID
        parameter               (NPLANET = 7)
        parameter               (PLANET_ID = 100 * NPLANET + 99)

        character*(*)           PLANET_NAME, STARLIST, LONDIR
        parameter               (PLANET_NAME = 'Uranus')
        parameter               (STARLIST = 'starlist_ura.txt')
        parameter               (LONDIR = 'E')

        double precision        RPLANET
        parameter               (RPLANET = 25559.d0)

c Moon parameters
        integer                 NMOONS
        parameter               (NMOONS = 18)
        integer                 MOON_IDS(0:NMOONS)/
     &                                  799,
     &                                  701, 702,
     &                                  703, 704, 705,
     &                                  706, 707,
     &                                  708, 709,
     &                                  710, 711, 712,
     &                                  713, 714, 715,
     &                                  725, 726, 727 /
        character*10            MOON_NAMES(0:NMOONS)/ 'Uranus',
     &                                  'Ariel', 'Umbriel',
     &                                  'Titania', 'Oberon', 'Miranda',
     &                                  'Cordelia', 'Ophelia',
     &                                  'Bianca', 'Cressida',
     &                                  'Desdemona', 'Juliet', 'Portia',
     &                                  'Rosalind', 'Belinda', 'Puck',
     &                                  'Perdita', 'Mab', 'Cupid' /
        logical                 MOON_IS_IRREGULAR(0:NMOONS)
     &                                  / .FALSE., NMOONS*.FALSE. /

c Ring constants
        integer                 NRINGS
        parameter               (NRINGS = 17)

        character*10            ring_names(NRINGS)/
     &                                  'Six', 'Five', 'Four',
     &                                  'Alpha', 'Beta', 'Eta',
     &                                  'Gamma', 'Delta', 'Lambda',
     &                                  'Epsilon', 'Epsilon',
     &                                  'Nu', 'Nu', 'Nu',
     &                                  'Mu', 'Mu', 'Mu'  /

        double precision        ring_rads(NRINGS)/
     &                                  41837.15d0,
     &                                  42234.82d0,
     &                                  42570.91d0, 44718.45d0,
     &                                  45661.03d0, 47175.91d0,
     &                                  47626.87d0, 48300.12d0,
     &                                  50023.94d0,
     &                                  51091.32d0, 51207.32d0,
     &                                  66100.d0, 67300.d0, 69900.d0,
     &                                  86000.d0, 97700.d0, 103000.d0 /
        double precision        ring_elevs(NRINGS)/ 17*0.d0 /
        double precision        ring_eccs(NRINGS)/
     &                                  1.013d-3, 1.899d-3,
     &                                  1.059d-3, 0.761d-3,
     &                                  0.442d-3, 0.000d-3,
     &                                  0.109d-3, 0.000d-3,
     &                                  0.000d-3,
     &                                  7.193d-3, 8.679d-3,
     &                                  0.d0, 0.d0, 0.d0,
     &                                  0.d0, 0.d0, 0.d0 /
        double precision        ring_incs(NRINGS)/
     &                                  0.0616d0, 0.0536d0,
     &                                  0.0323d0, 0.0152d0,
     &                                  0.0051d0, 0.0000d0,
     &                                  0.0000d0, 0.0000d0,
     &                                  0.0000d0,
     &                                  0.0000d0, 0.0000d0,
     &                                  0.d0, 0.d0, 0.d0,
     &                                  0.d0, 0.d0, 0.d0 /
        double precision        ring_peris(NRINGS)/
     &                                  242.80d0, 170.31d0,
     &                                  127.28d0, 333.24d0,
     &                                  224.88d0,   0.00d0,
     &                                  132.10d0,   0.00d0,
     &                                    0.00d0,
     &                                  214.97d0,   214.97d0,
     &                                  0.d0, 0.d0, 0.d0,
     &                                  0.d0, 0.d0, 0.d0 /
        double precision        ring_nodes(NRINGS)/
     &                                   12.12d0, 286.57d0,
     &                                   89.26d0,  63.08d0,
     &                                  310.05d0,   0.00d0,
     &                                    0.00d0,   0.00d0,
     &                                    0.00d0,
     &                                    0.00d0,   0.00d0,
     &                                    0.d0, 0.d0, 0.d0,
     &                                    0.d0, 0.d0, 0.d0 /
        double precision        ring_offsets(3,NRINGS)/
     &                                  NRINGS*0.d0, NRINGS*0.d0,
     &                                  NRINGS*0.d0 /

        logical                 ring_flags(NRINGS)/ 3*.FALSE.,
     &                                  5*.TRUE., .FALSE., 2*.TRUE.,
     &                                  6*.FALSE. /

        logical                 ring_opaqs(NRINGS)/ 10*.FALSE., .TRUE.,
     &                                               6*.FALSE. /

        logical                 ring_dashed(NRINGS)/ 8*.FALSE., .TRUE.,
     &                                               2*.FALSE.,
     &                                  .TRUE., .FALSE., .TRUE.,
     &                                  .TRUE., .FALSE., .TRUE. /

        double precision        ring_dperi_dt(NRINGS)/
     &                                  2.76156d0,
     &                                  2.67151d0,
     &                                  2.59816d0,  2.18574d0,
     &                                  2.03083d0,  0.00000d0,
     &                                  1.75075d0,  0.00000d0,
     &                                  0.00000d0,
     &                                  1.36325d0,  1.36325d0,
     &                                  0.d0, 0.d0, 0.d0,
     &                                  0.d0, 0.d0, 0.d0 /
        double precision        ring_dnode_dt(NRINGS)/
     &                                  -2.75629d0,
     &                                  -2.66604d0,
     &                                  -2.59271d0, -2.18326d0,
     &                                  -2.02778d0,  0.00000d0,
     &                                   0.00000d0,  0.00000d0,
     &                                   0.00000d0,
     &                                   0.00000d0,  0.00000d0,
     &                                   0.d0, 0.d0, 0.d0,
     &                                   0.d0, 0.d0, 0.d0 /

        integer                 NARCS
        parameter               (NARCS = 7)
        integer                 arc_rings(NARCS)/1, 2, 3, 4, 5, 10, 11/
        double precision        arc_minlons(NARCS), arc_maxlons(NARCS)
        double precision        arc_widthpts
        logical                 arc_flags(NARCS)/ 7*.FALSE. /

        double precision        ref_time, ddays

c Planet-specific declarations
        double precision        peri, node
        integer                 FJUL_DUTCofYMD

c***********************************************************************

c Parameter parsing variables
        character*256           string, string2, time_string
        character*40            keyword
        integer                 i, isc, obs_isc, ivalue, iparen, jparen,
     &                          dutc
        double precision        secs, radius, lat, lon, alt, angle,
     &                          sun_range, obs_range, value
        logical                 status, found, blank_disks, isright

c Geometry variables
        double precision        planet_ra, planet_dec, ra, dec, dra,
     &                          ddec, cosdec, phase, obs_b, sun_b,
     &                          sun_db, obs_long, sun_long, obs_dist,
     &                          sun_dist, obs_pv(6), planet_dpv(6), dt,
     &                          subobs_lon, subobs_lat,
     &                          subsol_lon, subsol_lat
        character*18            ra_string, dec_string, litstr
        logical                 isdark

c Function declarations
        integer                 LASTNB
        double precision        RPD, DPR, CLIGHT, PI,
     &                          FJUL_ETofTAI, FJUL_TAIofDUTC
        logical                 RSPK_LoadFiles, RSPK_LoadSC,
     &                          FJUL_ParseDT, WWW_GetKey, WWW_GetKeys,
     &                          WWW_GetKeyUnsanitized,
     &                          ParseAngle, ReadStars

c Useful constants
        double precision        MAXSECS, AU
        parameter               (MAXSECS = 360.d0 * 60.d0 * 60.d0)
        parameter               (AU = 149597870.7d0)

c General plot parameters
        double precision        obs_time, fov, center_ra, center_dec
        integer                 center_body_id
        character*80            center_body_name, title, filename

        integer                 ncaptions, MAXCAPTIONS
        parameter               (MAXCAPTIONS = 8)
        character*80            lcaptions(MAXCAPTIONS)
        character*80            rcaptions(MAXCAPTIONS)

        logical                 moon_flags(0:NMOONS)
        double precision        moon_labelpts, moon_diampts,
     &                          meridian_pts
        integer                 sc_trajectory
        integer                 ring_method/0/

c Star parameters
        integer                 MAX_NSTARS
        parameter               (MAX_NSTARS = 200)

        integer                 nstars
        double precision        star_ras(MAX_NSTARS+10),
     &                          star_decs(MAX_NSTARS+10)
        character*20            star_names(MAX_NSTARS+10)

        logical                 star_labels
        double precision        STAR_DIAMPTS
        parameter               (STAR_DIAMPTS = 24.d0)

c***********************************************************************
c Initialize
c***********************************************************************

c Reduce SPICE error messages
        call ERRPRT('SET', 'NONE, SHORT, LONG, EXPLAIN')

c Disable tracing
        call TRCOFF

c***********************************************************************
c Summarize request
c***********************************************************************

10      format(a)
        write(*,10) 'Input Parameters'
        write(*,10) '----------------'
        write(*,10) ' '

c Observation time
        status = WWW_GetKey('time', string)
        write(*,10) '  Observation time: ' // string(1:LASTNB(string))

c Ephemeris selection
        status = WWW_GetKey('ephem', string)
        write(*,10) '         Ephemeris: ' // string(5:LASTNB(string))

c Field of view
        status = WWW_GetKey('fov', string)
        status = WWW_GetKey('fov_unit', string2)
        if (string .eq. ' ' .and. index(string2,'FOV') .gt. 0)
     &          string = '1'
        write(*,10) '     Field of view: ' //
     &              string(1:LASTNB(string)) //
     &              ' (' // string2(1:LASTNB(string2)) // ')'

c Diagram center
        status = WWW_GetKey('center', string)
        if (string .eq. 'body') then
            status = WWW_GetKey('center_body', string)
            write(*,10) '    Diagram center: ' //
     &                  string(1:LASTNB(string))
        else if (string .eq. 'ansa') then
            status = WWW_GetKey('center_ansa', string)
            status = WWW_GetKey('center_ew',   string2)
            write(*,10) '    Diagram center: ' //
     &                  string(1:LASTNB(string)) // ' ' //
     &                  string2(1:LASTNB(string2)) // ' ansa'
        else if (string .eq. 'J2000') then
            status = WWW_GetKey('center_ra', string)
            status = WWW_GetKey('center_ra_type', string2)
            write(*,10) '    Diagram center: RA  = ' //
     &                  string(1:LASTNB(string)) // ' ' //
     &                  string2(1:LASTNB(string2))
            status = WWW_GetKey('center_dec', string)
            write(*,10) '                    Dec = ' //
     &                  string(1:LASTNB(string))
        else
            status = WWW_GetKey('center_star', string)
            write(*,10) '    Diagram center: Star = ' //
     &                  string(1:LASTNB(string))
        end if

c Viewpoint
        status = WWW_GetKey('viewpoint', string)
        if (string .eq. 'latlon') then
            status = WWW_GetKey('latitude',  string)
            write(*,10) '         Viewpoint: Lat = ' //
     &                  string(1:LASTNB(string))  // ' (deg)'
            status = WWW_GetKey('longitude', string)
            status = WWW_GetKey('lon_dir',   string2)
            write(*,10) '                    Lon = ' //
     &                  string(1:LASTNB(string))  // ' (deg ' //
     &                  string2(1:LASTNB(string2))  // ')'
            status = WWW_GetKey('altitude',  string)
            write(*,10) '                    Alt = ' //
     &                  string(1:LASTNB(string)) // ' (m)'
        else
            status = WWW_GetKey('observatory', string)
            status = WWW_GetKey('sc_trajectory', string2)
            if (status) then
                string(LASTNB(string)+1:) =
     &                  ' (' // string2(5:LASTNB(string2)) // ')'
            end if

            write(*,10) '         Viewpoint: ' //
     &                  string(1:LASTNB(string))
        end if

c Moon selection
        status = WWW_GetKey('moons', string)
        write(*,10) '    Moon selection: ' // string(5:LASTNB(string))

        status = WWW_GetKey('moremoons', string)
        if (status) then
            write(*,10) '                    ' //
     &                  string(1:LASTNB(string))
        end if

c Ring selection
        status = WWW_GetKey('rings', string)
        write(*,10) '    Ring selection: ' // string(1:LASTNB(string))

c Standard stars
        status = WWW_GetKey('standard', string)
        if (.not. status) string = 'No'
        write(*,10) '    Standard stars: ' // string(1:LASTNB(string))

c Additional star
        status = WWW_GetKey('additional', string)
        if (.not. status) then
            write(*,10) '   Additional star: No'
        else
            status = WWW_GetKey('extra_name', string)
            write(*,10) '   Additional star: ' //
     &                  string(1:LASTNB(string))
            status = WWW_GetKey('extra_ra', string)
            status = WWW_GetKey('extra_ra_type', string2)
            write(*,10) '                    RA  = ' //
     &                  string(1:LASTNB(string)) // ' ' //
     &                  string2(1:LASTNB(string2))
            status = WWW_GetKey('extra_dec', string)
            write(*,10) '                    Dec = ' //
     &                  string(1:LASTNB(string))
        end if

c Other bodies
        status = WWW_GetKeys('other', string)
        if (.not. status) then
            write(*,10) '      Other bodies: None'
        else
            write(*,10) '      Other bodies: ' //
     &                  string(1:LASTNB(string))
            do 50 i = 1, 9999
                status = WWW_GetKeys('other', string)
                if (.not. status) goto 51
                write(*,10) '                    ' //
     &                  string(1:LASTNB(string))
50          continue
51          continue
        end if

c Title
        status = WWW_GetKey('title', string)
        write(*,10) '             Title: "' // string(1:LASTNB(string))
     &                                      // '"'

c Moon labels
        status = WWW_GetKey('labels', string)
        write(*,10) '       Moon labels: ' // string(1:LASTNB(string))

c Moon enlargement
        status = WWW_GetKey('moonpts', string)
        write(*,10) '  Moon enlargement: ' // string(1:LASTNB(string))
     &                  // ' (points)'

c Blank disks
        status = WWW_GetKey('blank', string)
        write(*,10) '       Blank disks: ' // string(1:LASTNB(string))

c Pericenter markers
        status = WWW_GetKey('peris', string)
        write(*,10) 'Pericenter markers: ' // string(1:LASTNB(string))

        status = WWW_GetKey('peripts', string)
        write(*,10) '       Marker size: ' // string(1:LASTNB(string))
     &                  // ' (points)'

c Highlight prime meridians
        status = WWW_GetKey('meridians', string)
        write(*,10) '   Prime meridians: ' // string(1:LASTNB(string))

        write(*,10) ' '

c***********************************************************************
c Get time
c***********************************************************************

c Initialize leap seconds table
        call FJUL_InitLeaps(JULIAN_LEAPSECS)

c Extract time value
        keyword = 'OBSERVATION_TIME'
        status = WWW_GetKey('time', string)
        time_string = string

c Parse and convert to UTC
        status = FJUL_ParseDT(string, ' ', dutc, secs)
        if (.not. status) goto 9999

c Convert to ephemeris time
        obs_time = FJUL_ETofTAI(FJUL_TAIofDUTC(dutc) + secs)

c***********************************************************************
c Check need for spacecraft ephemerides
c
c This must be done BEFORE calling RSPK_LoadFiles(), because otherwise
c a spacecraft ephemeris will take precedence over the user's selection.
c***********************************************************************

c Check the observatory
        keyword = 'VIEWPOINT'
        status = WWW_GetKey('observatory', string)
        obs_isc = 0
        do isc = 1, NSPACECRAFTS
            if (string .eq. SC_NAMES(isc)) then
                obs_isc = isc
            end if
        end do

        keyword = 'SPACECRAFT_TRAJECTORY'
        sc_trajectory = 0
        status = WWW_GetKey('sc_trajectory', string)
        if (status) then
            read(string(1:4),*,err=9999) sc_trajectory
        end if

c Check the other bodies
        do 60 i = 1, 9999
            status = WWW_GetKeys('other', string)
            if (.not. status) goto 61

            do isc = 1, NSPACECRAFTS
              if (string .eq. SC_NAMES(isc) .and.
     &            isc .ne. obs_isc) then
                    status = RSPK_LoadSC(1, SC_IDS(isc), NPLANET,
     &                                   0, .FALSE.)
                    if (.not. status) goto 9999
              end if
            end do
60      continue
61      continue

c Load spacecraft ephemeris if necessary
        if (obs_isc .ne. 0) then
            status = RSPK_LoadSC(1, SC_IDS(obs_isc), NPLANET,
     &                           sc_trajectory, .TRUE.)
            if (.not. status) goto 9999
        end if

c***********************************************************************
c Set up ephemeris
c***********************************************************************

c Load SPICE files
        keyword = 'EPHEMERIS'
        status = WWW_GetKey('ephem', string)
        read(string(1:4), *, err=9999) ivalue

        status = RSPK_LoadFiles(1, NPLANET, ivalue)
        if (.not. status) goto 9999

c***********************************************************************
c Set viewpoint
c***********************************************************************

        keyword = 'VIEWPOINT'
        status = WWW_GetKey('viewpoint', string)

        if (.not. status) then
            call RSPK_SetObsId(EARTH_ID)
        else if (string .eq. 'observatory') then
            keyword = 'OBSERVATORY'
            status = WWW_GetKey('observatory', string)
            if (.not. status) goto 9999

            found = .FALSE.
            do isc = 1, NSPACECRAFTS
                if (string .eq. SC_NAMES(isc)) then
                    call RSPK_SetObsId(SC_CODES(isc))
                    found = .TRUE.
                end if
            end do

            if (.not. found) then
                if (string(1:5) .eq. 'Earth') then
                    call RSPK_SetObsId(EARTH_ID)
                else
                    iparen = index(string, '(')
                    jparen = index(string, ')')
                    read(string(iparen+1:jparen-1), *, err=9999)
     &                                              lat, lon, alt
                    call RSPK_SetObsId(EARTH_ID)
                    call RSPK_SetObs(lat, lon, alt)
                end if
            end if
        else if (string .eq. 'latlon') then
            keyword = 'LATITUDE'
            status = WWW_GetKey('latitude', string)
            status = ParseAngle(string, lat)
            if (.not. status) goto 9999

            keyword = 'LONGITUDE'
            status = WWW_GetKey('longitude', string)
            status = ParseAngle(string, lon)
            if (.not. status) goto 9999

            keyword = 'ALTITUDE'
            status = WWW_GetKey('altitude', string)
            read(string,*,err=9999) alt

            keyword = 'LONGITUDE_EW'
            status = WWW_GetKey('lon_dir', string)
            if (string .eq. 'east') then
                continue
            else if (string .eq. 'west') then
                lon = -lon
            else
                goto 9999
            end if

            call RSPK_SetObsId(EARTH_ID)
            call RSPK_SetObs(lat, lon, alt)
        else
            goto 9999
        end if

c***********************************************************************
c Set the field of view
c
c This must be handled after the ephemeris time is established and after
c RSPK_LoadFiles has been called, because it might have to determine
c the distance to the planet.
c***********************************************************************

c Get the field of view
        keyword = 'FIELD_OF_VIEW'
        status = WWW_GetKey('fov', string)
        status = WWW_GetKey('fov_unit', string2)
        if (string .eq. ' ' .and. index(string2,'FOV') .gt. 0)
     &          string = '1'
        if (string .eq. ' ') goto 9999
        read(string, *, err=9999) fov
        if (fov .le. 0.) goto 9999

c Get the field of view units
        keyword = 'FIELD_OF_VIEW_UNIT'
        status = WWW_GetKey('fov_unit', string)

        if (string(1:3) .eq. 'sec') then
            fov = fov/3600.d0 * RPD()
        else if (string .eq. 'degrees') then
            fov = fov * RPD()
        else if (string(1:8) .eq. 'millirad' .or.
     &           string(1:4) .eq. 'mrad') then
            fov = fov * 1.d-3
        else if (string(1:8) .eq. 'microrad' .or.
     &           string(1:4) .eq. 'urad') then
            fov = fov * 1.d-6
        else if (index(string, 'radi') .gt. 0) then
            call RSPK_Ranges(obs_time, sun_range, obs_range)
            fov = fov * asin(RPLANET / obs_range)
        else if (string(1:9) .eq. 'kilometer' .or.
     &           string(1:2) .eq. 'km') then
            call RSPK_Ranges(obs_time, sun_range, obs_range)
            fov = fov * asin(1.d0 / obs_range)
        else if (index(string, 'Voyager ISS wide') .gt. 0) then
            fov = fov * 5.463d-2
        else if (index(string, 'Voyager ISS narrow') .gt. 0) then
            fov = fov * 7.292d-3
        else
            goto 9999
        end if

        fov = min(fov, PI()/2.d0)

c***********************************************************************
c Locate center of diagram
c***********************************************************************

c Get the central body ID
        center_body_id = PLANET_ID
        center_body_name = PLANET_NAME

        keyword = 'DIAGRAM_CENTER'
        status = WWW_GetKey('center', string)

c***************************************
c Case #1: A body
c***************************************

        if (string .eq. 'body') then
            keyword = 'CENTER_BODY'
            status = WWW_GetKey('center_body', string)

            if (string .eq. PLANET_NAME) then
                center_body_id = PLANET_ID
                center_body_name = PLANET_NAME
            else
                iparen = index(string,'(')
                jparen = index(string,')')
                if (iparen .gt. 0) then
                    read(string(iparen+2:jparen-1), *, end=9999) ivalue
                    if (ivalue .le. 0) goto 9999
                    center_body_id = ivalue + 100 * NPLANET
                    center_body_name = string(:iparen-2)
                else
                    goto 9999
                end if
            end if

            call RSPK_BodyRaDec(obs_time, center_body_id,
     &                          center_ra, center_dec)

c***************************************
c Case #2: A ring ansa
c***************************************

c Check for a ring
        else if (string .eq. 'ansa') then
            keyword = 'CENTER_ANSA'
            status = WWW_GetKey('center_ansa', string)

            if (string(1:1) .eq. '6') then
                radius = ring_rads(1)
            else if (string(1:1) .eq. '5') then
                radius = ring_rads(2)
            else if (string(1:1) .eq. '4') then
                radius = ring_rads(3)
            else if (index(string,'Alpha') .gt. 0) then
                radius = ring_rads(4)
            else if (index(string,'Beta') .gt. 0) then
                radius = ring_rads(5)
            else if (index(string,'Eta') .gt. 0) then
                radius = ring_rads(6)
            else if (index(string,'Gamma') .gt. 0) then
                radius = ring_rads(7)
            else if (index(string,'Delta') .gt. 0) then
                radius = ring_rads(8)
            else if (index(string,'Lambda') .gt. 0) then
                radius = ring_rads(9)
            else if (index(string,'Epsilon') .gt. 0) then
                radius = 0.5d0 * (ring_rads(10) + ring_rads(11))
            else if (index(string,'Nu') .gt. 0) then
                radius = ring_rads(13)
            else if (index(string,'Mu') .gt. 0) then
                radius = ring_rads(16)
            else
                goto 9999
            end if

            keyword = 'CENTER_EAST_WEST'
            status = WWW_GetKey('center_ew', string)

            if (string .eq. 'west') then
                isright = .TRUE.
            else if (string .eq. 'east') then
                isright = .FALSE.
            else
                goto 9999
            end if

            call RSPK_AnsaRaDec(obs_time, radius, isright,
     &                  center_ra, center_dec)

c***************************************
c Case #3: J2000 coordinates
c***************************************

c Check for a J2000 ra & dec pair
        else if (string .eq. 'J2000') then

c Read three RA values
            keyword = 'RIGHT_ASCENSION'
            status = WWW_GetKey('center_ra', string)
            status = ParseAngle(string, angle)
            if (.not. status) goto 9999

            status = WWW_GetKey('center_ra_type', string)
            if (string(1:1) .eq. 'd' .or. string(1:1) .eq. 'D')
     &          angle = angle / 15.d0

            center_ra = angle * 15.d0 * RPD()

c Read three Dec values
            keyword = 'DECLINATION'
            status = WWW_GetKey('center_dec', string)
            status = ParseAngle(string, angle)
            if (.not. status) goto 9999
            center_dec = angle * RPD()

c***************************************
c Case #4: A Named star
c***************************************

        else if (string .eq. 'star') then
            keyword = 'STANDARD_STARLIST'
            status = ReadStars(1, STARLIST_PATH // STARLIST,
     &                            nstars, MAX_NSTARS,
     &                            star_ras, star_decs, star_names)
            if (.not. status) goto 9999

            keyword = 'CENTER_STAR'
            status = WWW_GetKey('center_star', string)
            do i = 1, nstars
                if (star_names(i) .eq. string) then
                    center_ra = star_ras(i)
                    center_dec = star_decs(i)
                    goto 71
                end if
            end do
            goto 9999

71          continue

c Unrecognized option
        else
                goto 9999
        end if

c***********************************************************************
c Moon selection
c***********************************************************************

        keyword = 'MOON_SELECTION'
        status = WWW_GetKey('moons', string)
        if (status) then
            read(string(1:3),*,err=9999) ivalue
            if (ivalue .le. 0) goto 9999
        else
            ivalue = PLANET_ID - 1
        end if

        moon_flags(0) = .TRUE.
        do i = 1, NMOONS
            moon_flags(i) = (MOON_IDS(i) .le. ivalue .and.
     &                       .not. MOON_IS_IRREGULAR(i))
        end do

c Select Irregulars
        status = WWW_GetKey('moremoons', string)
        if (string .ne. ' ') then
            do i = 1, NMOONS
                if (MOON_IS_IRREGULAR(i)) moon_flags(i) = .TRUE.
            end do
        end if

c***********************************************************************
c Ring selection
c***********************************************************************

        keyword = 'RING_SELECTION'
        status = WWW_GetKey('rings', string)

c Alpha-Epsilon Rings are always selected by default

        if (string(:5) .eq. 'Alpha') then
                continue
        else if (string(:4) .eq. 'Nine') then
                ring_flags(1) = .TRUE.
                ring_flags(2) = .TRUE.
                ring_flags(3) = .TRUE.
        else if (index(string,'inner') .gt. 0) then
                ring_flags(1) = .TRUE.
                ring_flags(2) = .TRUE.
                ring_flags(3) = .TRUE.
                ring_flags(9) = .TRUE.
        else if (string(:3) .eq. 'All') then
                ring_flags(1) = .TRUE.
                ring_flags(2) = .TRUE.
                ring_flags(3) = .TRUE.
                ring_flags(9) = .TRUE.
                ring_flags(12) = .TRUE.
                ring_flags(13) = .TRUE.
                ring_flags(14) = .TRUE.
                ring_flags(15) = .TRUE.
                ring_flags(16) = .TRUE.
                ring_flags(17) = .TRUE.
        else
                goto 9999
        end if

c Reference date is 20:00 UTC on 10 March 1977
        ref_time = FJUL_ETofTAI(20.d0*60.d0*60.d0 +
     &                  FJUL_TAIofDUTC(FJUL_DUTCofYMD(1977,3,10)))

        call RSPK_ObsLoc(obs_time, obs_pv)
        call SPKAPP(PLANET_ID, obs_time, 'J2000', obs_pv, 'LT',
     &                  planet_dpv, dt)

        ddays = (obs_time - ref_time - dt) / 86400.d0

c Update all ring elements (convert from deg B1950 to rad J2000)
        do 300 i = 1, NRINGS
            ring_peris(i) = ring_peris(i) + ring_dperi_dt(i) * ddays
            ring_nodes(i) = ring_nodes(i) + ring_dnode_dt(i) * ddays

            ring_peris(i) = RPD() * (ring_peris(i) - 0.280977d0)
            ring_nodes(i) = RPD() * (ring_nodes(i) - 0.280977d0)
            ring_incs(i)  = RPD() * ring_incs(i)
300     continue

c***********************************************************************
c Background objects
c***********************************************************************

c Standard stars
        status = WWW_GetKey('standard', string)
        if (string .eq. 'Yes') then
            keyword = 'STANDARD_STARLIST'
            status = ReadStars(1, STARLIST_PATH // STARLIST,
     &                            nstars, MAX_NSTARS,
     &                            star_ras, star_decs, star_names)
                if (.not. status) goto 9999
        else
            nstars = 0
        end if

c Additional star
        status = WWW_GetKey('additional', string)
        if (string .eq. 'Yes') then
            nstars = nstars + 1

            status = WWW_GetKey('extra_name', star_names(nstars))

            keyword = 'STAR_RA'
            status = WWW_GetKey('extra_ra', string)
            status = ParseAngle(string, angle)
            if (.not. status) goto 9999

            status = WWW_GetKey('extra_ra_type', string)
            if (string(1:1) .eq. 'd' .or. string(1:1) .eq. 'D')
     &          angle = angle / 15.d0
            star_ras(nstars) = angle * 15.d0 * RPD()

            keyword = 'STAR_DEC'
            status = WWW_GetKey('extra_dec', string)
            status = ParseAngle(string, angle)
            if (.not. status) goto 9999
            star_decs(nstars) = angle * RPD()
        end if

c Other bodies
        keyword = 'OTHER_BODIES'
        do 500 i = 1, 9999
            status = WWW_GetKeys('other', string)
            if (.not. status) goto 501

            nstars = nstars + 1
            if (string .eq. 'Sun') then
                call RSPK_BodyRaDec(obs_time, SUN_ID,
     &                  star_ras(nstars), star_decs(nstars))
                star_names(nstars) = 'Sun'
            else if (string .eq. 'Anti-Sun') then
                call RSPK_AntiSun(obs_time, PLANET_ID,
     &                  star_ras(nstars), star_decs(nstars))
                star_names(nstars) = 'Anti-Sun'
            else if (string .eq. 'Earth') then
                call RSPK_BodyRaDec(obs_time, EARTH_ID,
     &                  star_ras(nstars), star_decs(nstars))
                star_names(nstars) = 'Earth'
            else
                found = .FALSE.
                do isc = 1, NSPACECRAFTS
                    if (string .eq. SC_NAMES(isc)) then
                        call RSPK_BodyRaDec(obs_time, SC_CODES(isc),
     &                      star_ras(nstars), star_decs(nstars))
                        star_names(nstars) = string
                        found = .TRUE.
                    end if
                end do

                if (.not. found) goto 9999
            end if
500     continue
501     continue

c***********************************************************************
c Get size of labels
c***********************************************************************

        keyword = 'MOON_LABELS'
        status = WWW_GetKey('labels', string)

        moon_labelpts = 0.d0
        if (status) then
          iparen = index(string, '(')
          if (iparen .gt. 0) then
            jparen = index(string, ' points)')
            read(string(iparen+1:jparen-1), *, err=9999) moon_labelpts
            if (moon_labelpts .lt. 0.) goto 9999
          end if
        end if

c Label stars only if we're also labeling moons
        star_labels = (moon_labelpts .gt. 0.d0)

c***********************************************************************
c Get minimum disk size
c***********************************************************************

        keyword = 'MOON_ENLARGEMENT'
        status = WWW_GetKey('moonpts', string)
        if (status) then
            read(string, *, err=9999) moon_diampts
            if (moon_diampts .lt. 0.) goto 9999
        else
            moon_diampts = 0.d0
        end if

c***********************************************************************
c Determine whether disks should be blank
c***********************************************************************

        keyword = 'BLANK_DISKS'
        status = WWW_GetKey('blank', string)
        if (string .eq. 'Yes') then
            blank_disks = .TRUE.
        else if (string .eq. 'No' .or. string .eq. '') then
            blank_disks = .FALSE.
        else
            goto 9999
        end if

c***********************************************************************
c Get pericenter marker info
c***********************************************************************

        keyword = 'PERICENTER_MARKERS'
        status = WWW_GetKey('peris', string)

c Turn on arc flags as needed
        if (string .eq. 'None') goto 350

        arc_flags(6) = .TRUE.
        arc_flags(7) = .TRUE.
        if (string(1:4) .eq. 'Epsi') goto 350

        if (ring_flags(1)) arc_flags(1) = .TRUE.
        if (ring_flags(2)) arc_flags(2) = .TRUE.
        if (ring_flags(3)) arc_flags(3) = .TRUE.
        arc_flags(4) = .TRUE.
        arc_flags(5) = .TRUE.
        if (string(1:3) .eq. 'All') goto 350

        goto 9999
350     continue

c Read pericenter marker sizes
        keyword = 'PERICENTER_MARKER_PTS'
        status = WWW_GetKey('peripts', string)
        read(string, *, err=9999) arc_widthpts
        if (arc_widthpts .le. 0.) goto 9999

        do 360 i = 1, NARCS
            arc_minlons(i) = ring_peris(arc_rings(i))
            arc_maxlons(i) = ring_peris(arc_rings(i))
360     continue

c***********************************************************************
c Determine whether meridians should be highlighted
c***********************************************************************

        keyword = 'HIGHLIGHTED_MERIDIANS'
        status = WWW_GetKey('meridians', string)
        if (string .eq. 'Yes') then
            meridian_pts = 1.3d0
        else if (string .eq. 'No' .or. string .eq. '') then
            meridian_pts = 0.d0
        else
            goto 9999
        end if

c***********************************************************************
c Generate output table of body positions
c***********************************************************************

c Locate planet
        call RSPK_BodyRaDec(obs_time, PLANET_ID, planet_ra, planet_dec)
        cosdec = cos(planet_dec)

c Write RA/dec table
        write(*,10) ' '
        write(*,10) 'Field of View Description (J2000)'
        write(*,10) '---------------------------------'
        write(*,10) ' '
        if (obs_isc .eq. 0) then
            write(*,11)
11          format(1x, 4x, 'Body', 10x, 'RA', 18x, 'Dec',
     &             18x, 'RA (deg)', 3x, 'Dec (deg)',
     &             4x, 'dRA (")', 3x, 'dDec (")')
        else
            write(*,12)
12          format(1x, 4x, 'Body', 10x, 'RA', 18x, 'Dec',
     &          18x, 'RA (deg)', 3x, 'Dec (deg)',
     &          3x, 'dRA (deg)', 2x, 'dDec (deg)')
        end if

        do 400 i = 0, NMOONS
            if (.not. moon_flags(i)) goto 400

            call RSPK_BodyRaDec(obs_time, MOON_IDS(i), ra, dec)
            if (obs_isc .eq. 0) then
                ddec = DPR() * 3600.d0 * (dec - planet_dec)
                dra  = DPR() * 3600.d0 * (ra  - planet_ra)
                if (dra .lt. -0.5*MAXSECS) dra = dra + MAXSECS
                if (dra .gt.  0.5*MAXSECS) dra = dra - MAXSECS
            else
                ddec = DPR() * (dec - planet_dec)
                dra  = DPR() * (ra  - planet_ra)
                if (dra .lt. -180.) dra = dra + 360.
                if (dra .gt.  180.) dra = dra - 360.
            end if
            dra = dra * cosdec

            ra = ra * DPR()
            dec = dec * DPR()
            call DMS_string(ra/15.d0,  'hms', 4, ra_string)
            call DMS_string(dec, 'dms', 3, dec_string)

            if (obs_isc .eq. 0) then
                write(*,13,err=400) MOON_IDS(i), MOON_NAMES(i),
     &                              ra_string, dec_string,
     &                              ra, dec, dra, ddec
13              format(1x, i3, 1x, a10, 3x, a18, 2x, a18,
     &                 2x, f10.6, f12.6, 1x, f10.4, 1x, f10.4)
            else
                write(*,14,err=400) MOON_IDS(i), MOON_NAMES(i),
     &                              ra_string, dec_string,
     &                              ra, dec, dra, ddec
14              format(1x, i3, 1x, a10, 3x, a18, 2x, a18,
     &                 2x, f10.6, f12.6, 1x, f11.6, 1x, f11.6)
            end if
400     continue

c Write body geometry table
        write(*,10) ' '
        write(*,22)
        write(*,23) LONDIR, LONDIR
22      format(19x,'Sub-Observer  ',7x,'Sub-Solar     ')
23      format(5x,'Body',10x,
     &         2('Lon(deg',a1,') Lat(deg)',3x),
     &         'Phase(deg)',3x,'Distance(10^6 km)')
        do 401 i = 0, NMOONS
            if (.not. moon_flags(i)) goto 401

            call RSPK_BodyLonLat(obs_time, MOON_IDS(i),
     &                           subobs_lon, subobs_lat,
     &                           subsol_lon, subsol_lat)
            call RSPK_BodyRanges(obs_time, MOON_IDS(i), sun_dist,
     &                                                  obs_dist)
            call RSPK_BodyPhase(obs_time, MOON_IDS(i), phase)

            write(*,24) MOON_IDS(i), MOON_NAMES(i),
     &                      subobs_lon * DPR(), subobs_lat * DPR(),
     &                      subsol_lon * DPR(), subsol_lat * DPR(),
     &                      phase * DPR(), obs_dist/1.d6
401     continue
24      format(1x, i3, 1x, a10,
     &         1x,f10.3,f10.3,1x,f10.3,f10.3,f13.5,f15.6)

c Write ring table
        write(*,35)
35      format(/1x, 4x, 'Ring', 10x, 'Pericenter', 3x,
     &         'Ascending Node (deg, from ring plane ascending node)')

        do 410 i = 1, 10
                if (.not. ring_flags(i)) goto 410

                peri = mod(ring_peris(i) / RPD(), 360.d0)
                if (peri .lt. 0.d0) peri = peri + 360.d0
                if (ring_eccs(i) .eq. 0.d0) peri = 0.d0

                node = mod(ring_nodes(i) / RPD(), 360.d0)
                if (node .lt. 0.d0) node = node + 360.d0
                if (ring_incs(i) .eq. 0.d0) node = 0.d0

                write(*,36) ring_names(i), peri, node
36              format(5x, a10, 3x, f8.3, 5x, f8.3)
410     continue

c Write ring geometry values
        write(*,10) ' '

        call RSPK_RingOpen(obs_time, obs_b, sun_b, sun_db, isdark,
     &          obs_long, sun_long)
        call RSPK_Phase(obs_time, phase)
        call RSPK_Ranges(obs_time, sun_dist, obs_dist)
        litstr = '(lit)'
        if (isdark) litstr = '(unlit)'

        write(*,31) '  Ring sub-solar latitude (deg): ',
     &          DPR() * sun_b,
     &          DPR() * (sun_b-sun_db),
     &          DPR() * (sun_b+sun_db)
        write(*,32) ' Ring plane opening angle (deg): ',
     &          DPR() * obs_b,
     &          litstr(1:LASTNB(litstr))
        write(*,32) '  Ring center phase angle (deg): ',
     &          phase * DPR()
        write(*,32) '      Sub-solar longitude (deg): ',
     &          DPR() * sun_long,
     &          'from ring plane ascending node'
        write(*,32) '   Sub-observer longitude (deg): ',
     &          DPR() * obs_long
        write(*,*)
        write(*,32) '       Sun-planet distance (AU): ',
     &          sun_dist/AU
        write(*,32) '  Observer-planet distance (AU): ',
     &          obs_dist/AU
        write(*,33) '       Sun-planet distance (km): ',
     &          sun_dist/1.d6,
     &          'x 10^6'
        write(*,33) '  Observer-planet distance (km): ',
     &          obs_dist/1.d6,
     &          'x 10^6'
        write(*,33) '        Light travel time (sec): ',
     &          obs_dist/CLIGHT(0.d0)
        write(*,*)
31      format(1x, a, f9.5, '  (', f9.5, '  to ', f9.5, ')')
32      format(1x, a, f9.5, 2x, a)
33      format(1x, a, f12.6, 1x, a)

c***********************************************************************
c Set up plot title and captions
c***********************************************************************

        status = WWW_GetKeyUnsanitized('title', title)

        ncaptions = 1
        lcaptions(ncaptions) = 'Time (UTC):'
        status = WWW_GetKey('time', rcaptions(ncaptions))

        ncaptions = ncaptions + 1
        lcaptions(ncaptions) = 'Ephemeris:'
        status = WWW_GetKey('ephem', rcaptions(ncaptions))
        rcaptions(ncaptions) = rcaptions(ncaptions)(5:)

        ncaptions = ncaptions + 1
        lcaptions(ncaptions) = 'Viewpoint:'
        status = WWW_GetKey('viewpoint', string)
        if (string .eq. 'latlon') then
            string = '('
            status = WWW_GetKey('latitude', string(2:))
            string(LASTNB(string)+1:) = ','
            status = WWW_GetKey('longitude', string(LASTNB(string)+2:))
            status = WWW_GetKey('lon_dir',   string(LASTNB(string)+2:))
            string(LASTNB(string)+1:) = ','
            status = WWW_GetKey('altitude', string(LASTNB(string)+2:))
            string(LASTNB(string)+1:) = ')'
            rcaptions(3) = string
        else
            status = WWW_GetKey('observatory', string)
            status = WWW_GetKey('sc_trajectory', string2)
            if (status) then
                string(LASTNB(string)+1:) =
     &                  ' (' // string2(5:LASTNB(string2)) // ')'
            end if
            rcaptions(ncaptions) = string
        end if

        ncaptions = ncaptions + 1
        lcaptions(ncaptions) = 'Moon selection:'
        status = WWW_GetKey('moons', string)
        rcaptions(ncaptions) = string(5:)

        status = WWW_GetKey('moremoons', string2)
        if (status) then
            rcaptions(ncaptions) = string(5:LASTNB(string)) //
     &                             ' + ' // string2
        end if

        ncaptions = ncaptions + 1
        lcaptions(ncaptions) = 'Ring selection:'
        status = WWW_GetKey('rings', rcaptions(ncaptions))

        ncaptions = ncaptions + 1
        call RSPK_BodyLonLat(obs_time, center_body_id,
     &                       subobs_lon, subobs_lat,
     &                       subsol_lon, subsol_lat)
        lcaptions(ncaptions) =
     &          center_body_name(1:LASTNB(center_body_name)) //
     &          ' center (lon,lat):'
        write(rcaptions(ncaptions),80) subobs_lon * DPR(), LONDIR,
     &                                 subobs_lat * DPR()
80      format('(',f7.3,'\260 ',a1,',',f7.3,'\260)')

        ncaptions = ncaptions + 1
        call RSPK_BodyPhase(obs_time, center_body_id, phase)
        lcaptions(ncaptions) =
     &          center_body_name(1:LASTNB(center_body_name)) //
     &          ' phase angle: '
        write(rcaptions(ncaptions),81) phase * DPR()
81      format(f7.3,'\260')

c***********************************************************************
c Write Postscript file
c***********************************************************************

c Get Postscript filename
        call WWW_GetEnv('VIEWER_POSTFILE', filename)

c Planet is not a moon for this purpose
        moon_flags(0) = .FALSE.

        call RSPK_DrawView(obs_time, fov, center_ra, center_dec,
     &                  blank_disks, meridian_pts,
     &          NMOONS+1, moon_flags, MOON_IDS, MOON_NAMES,
     &                  moon_labelpts, moon_diampts,
     &          NRINGS, ring_flags, ring_rads, ring_elevs,
     &                  ring_eccs, ring_incs, ring_peris, ring_nodes,
     &                  ring_offsets,
     &                  ring_opaqs, ring_dashed, ring_method,
     &          NARCS, arc_flags, arc_rings, arc_minlons, arc_maxlons,
     &                  arc_widthpts,
     &          nstars, star_ras, star_decs, star_names, star_labels,
     &                  STAR_DIAMPTS,
     &          title, ncaptions, lcaptions, rcaptions, 108.d0,
     &          filename)

        call exit

c***********************************************************************
c Handle invalid input
c***********************************************************************

9999    continue
        write(*,90) 'Invalid value found for variable ',
     &                  keyword(1:LASTNB(keyword)),
     &                  string(1:LASTNB(string))
90      format(1x, a, a, ': ', a)
        call exit

        end

c***********************************************************************
