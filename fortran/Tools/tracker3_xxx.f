c***********************************************************************

        program TRACKER3_SAT

        implicit                none
        include                 'tools.inc'

        integer                 MAXRECS, MAXMOONS
        parameter               (MAXRECS = 10000)
        parameter               (MAXMOONS = 25)

        integer                 nplanet, planet_id
        integer                 i, j, irec
        integer                 ivalue, iparen, jparen, isc, obs_isc
        logical                 status, found
        character*255           string, string2
        character*40            keyword

        integer                 ntimes, dutc, ring_option
        double precision        dsec, time, time1, time2, sec,
     &                          shift
        integer                 nmoons, moon_ids(MAXMOONS)
        integer                 sc_trajectory
        character*16            moon_names(MAXMOONS)
        character*1             ch
        double precision        xrange, lat, lon, alt
        logical                 xscaled

        integer                 ncaptions, MAXCAPTIONS
        parameter               (MAXCAPTIONS = 4)
        character*80            title, lcaptions(MAXCAPTIONS),
     &                          rcaptions(MAXCAPTIONS), filename

        double precision        limb_loc(MAXRECS),
     &                          moon_loc(MAXMOONS,MAXRECS)

        integer                 year, month, day, hour, minute
        double precision        tai, test, mjd

c External function declarations
        logical                 RSPK_LoadFiles, RSPK_LoadSC,
     &                          FJUL_ParseDT, ParseAngle
        logical                 WWW_GetKey, WWW_GetKeys,
     &                          WWW_GetKeyUnsanitized
        integer                 FJUL_DUTCofTAI, LASTNB
        double precision        FJUL_TAIofDUTC, FJUL_MJDofTAI

c***********************************************************************
c Ring constants by planet
c***********************************************************************

        integer                 NRINGS_MAR
        parameter               (NRINGS_MAR = 0)
        logical                 mring_flags(1)/ .FALSE. /
        double precision        mring_rads(1)/ 0.d0 /
        double precision        mring_grays(1)/ 0.75d0 /

        integer                 NRINGS_JUP
        parameter               (NRINGS_JUP = 3)
        logical                 jring_flags(NRINGS_JUP)/ 3*.FALSE. /
        double precision        jring_rads(NRINGS_JUP)/
     &                                  129000.d0,
     &                                  181350.d0, 221900.d0 /
        double precision        jring_grays(NRINGS_JUP)/
     &                                  0.75d0,
     &                                  0.85d0, 0.90d0 /

        integer                 NRINGS_SAT
        parameter               (NRINGS_SAT = 5)
        logical                 sring_flags(NRINGS_SAT)/ 5*.FALSE. /
        double precision        sring_rads(NRINGS_SAT)/
     &                                  136780.d0,
     &                                  166000.d0, 173000.d0,
     &                                  180990.d0, 301650.d0/
        double precision        sring_grays(NRINGS_SAT)/
     &                                  0.75d0,
     &                                  1.00d0, 0.875d0,
     &                                  1.00d0, 0.875d0/

        integer                 NRINGS_URA
        parameter               (NRINGS_URA = 1)
        logical                 uring_flags(NRINGS_URA)/ .FALSE. /
        double precision        uring_rads(NRINGS_URA)/ 51149.32d0 /
        double precision        uring_grays(NRINGS_URA)/ 0.75d0 /

        integer                 NRINGS_NEP
        parameter               (NRINGS_NEP = 1)
        logical                 nring_flags(NRINGS_NEP)/ .FALSE. /
        double precision        nring_rads(NRINGS_NEP)/ 62932.d0 /
        double precision        nring_grays(NRINGS_NEP)/ 0.75d0 /

        integer                 NRINGS_PLU
        parameter               (NRINGS_PLU = 0)
        logical                 pring_flags(1)/ .FALSE. /
        double precision        pring_rads(1)/ 0.d0 /
        double precision        pring_grays(1)/ 0.75d0 /

        double precision        planet_gray/ 0.50d0 /

        integer                 NRINGS_MAX
        parameter               (NRINGS_MAX = 5)
        logical                 ring_flags(NRINGS_MAX)/ 5*.FALSE. /
        double precision        ring_rads(NRINGS_MAX)/ 5*0.d0 /
        double precision        ring_grays(NRINGS_MAX)/ 5*0.5d0 /
        integer                 nrings

c***********************************************************************
c Initialize
c***********************************************************************

c Reduce SPICE error messages
        call ERRPRT('SET', 'NONE, SHORT, LONG, EXPLAIN')

c Identify planet
        keyword = 'PLANET'
        call WWW_GetEnv('NPLANET', string)
        if (string .eq. '') goto 9999
        read(string, '(i1)', err=9999) nplanet
        if (nplanet .lt. 4 .or. nplanet .gt. 9) goto 9999

        planet_id = 100 * nplanet + 99

c***********************************************************************
c Summarize request
c***********************************************************************

10      format(a)
        write(*,10) 'Input Parameters'
        write(*,10) '----------------'
        write(*,10) ' '

c Tabulation parameters
        status = WWW_GetKey('start', string)
        write(*,10) '     Start time: ' // string(1:LASTNB(string))

        status = WWW_GetKey('stop', string)
        write(*,10) '      Stop time: ' // string(1:LASTNB(string))

        status = WWW_GetKey('interval', string)
        if (string .eq. ' ') string = '1'

        status = WWW_GetKey('time_unit', string2)
        write(*,10) '       Interval: ' // string(1:LASTNB(string))
     &                                  // ' '
     &                                  // string2(1:LASTNB(string2))

c Ephemeris
        status = WWW_GetKey('ephem', string)
        write(*,10) '      Ephemeris: ' // string(5:LASTNB(string))

c Viewpoint
        status = WWW_GetKey('viewpoint', string)
        if (.NOT. status) then
            write(*,10) '      Viewpoint: Earth''s Center'

        else if (string .eq. 'latlon') then
            status = WWW_GetKey('latitude',  string)
            write(*,10) '      Viewpoint: Lat = ' //
     &                  string(1:LASTNB(string))  // ' (deg)'
            status = WWW_GetKey('longitude', string)
            status = WWW_GetKey('lon_dir',   string2)
            write(*,10) '                 Lon = ' //
     &                  string(1:LASTNB(string))  // ' (deg ' //
     &                  string2(1:LASTNB(string2))  // ')'
            status = WWW_GetKey('altitude',  string)
            write(*,10) '                 Alt = ' //
     &                  string(1:LASTNB(string)) // ' (m)'
        else
            status = WWW_GetKey('observatory', string)
            status = WWW_GetKey('sc_trajectory', string2)
            if (status) then
                string(LASTNB(string)+1:) =
     &                  ' (' // string2(5:LASTNB(string2)) // ')'
            end if

            write(*,10) '      Viewpoint: ' //
     &                  string(1:LASTNB(string))
        end if

        write(*,10) ''

c Moon selection
        status = WWW_GetKeys('moons', string)
        if (status) then
          write(*,10) ' Moon selection: ' // string(5:LASTNB(string))

          do while (WWW_GetKeys('moons', string))
            write(*,10) '                 ' // string(5:LASTNB(string))
          end do
        else
          write(*,10) ' Moon selection:'
        end if

        write(*,10) ''

c Ring selection
        if (nplanet .ne. 4) then
         status = WWW_GetKeys('rings', string)
         if (status) then
          write(*,10) ' Ring selection: ' // string(5:LASTNB(string))

          do while (WWW_GetKeys('rings', string))
            write(*,10) '                 ' // string(5:LASTNB(string))
          end do
         else
          write(*,10) ' Ring selection:'
         end if
          write(*,10) ''
        end if

c Plot options
        status = WWW_GetKey('xrange', string)
        status = WWW_GetKey('xunit', string2)
        write(*,10) '     Plot scale: ' // string(1:LASTNB(string))
     &                                  // ' '
     &                                  // string2(1:LASTNB(string2))

c Title
        status = WWW_GetKey('title', string)
        write(*,10) '          Title: "' // string(1:LASTNB(string))
     &                                   // '"'
        write(*,10) ''

c***********************************************************************
c Load SPICE files
c***********************************************************************

c Gather ring parameters
        if (nplanet .eq. 4) then
            nrings = NRINGS_MAR
            do i = 1, nrings
                ring_flags(i) = mring_flags(i)
                ring_rads(i)  = mring_rads(i)
                ring_grays(i) = mring_grays(i)
            end do
        else if (nplanet .eq. 5) then
            nrings = NRINGS_JUP
            do i = 1, nrings
                ring_flags(i) = jring_flags(i)
                ring_rads(i)  = jring_rads(i)
                ring_grays(i) = jring_grays(i)
            end do
        else if (nplanet .eq. 6) then
            nrings = NRINGS_SAT
            do i = 1, nrings
                ring_flags(i) = sring_flags(i)
                ring_rads(i)  = sring_rads(i)
                ring_grays(i) = sring_grays(i)
            end do
        else if (nplanet .eq. 7) then
            nrings = NRINGS_URA
            do i = 1, nrings
                ring_flags(i) = uring_flags(i)
                ring_rads(i)  = uring_rads(i)
                ring_grays(i) = uring_grays(i)
            end do
        else if (nplanet .eq. 8) then
            nrings = NRINGS_NEP
            do i = 1, nrings
                ring_flags(i) = nring_flags(i)
                ring_rads(i)  = nring_rads(i)
                ring_grays(i) = nring_grays(i)
            end do
        else if (nplanet .eq. 9) then
            nrings = NRINGS_PLU
            do i = 1, nrings
                ring_flags(i) = pring_flags(i)
                ring_rads(i)  = pring_rads(i)
                ring_grays(i) = pring_grays(i)
            end do
        end if

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
        if (status .and. string .ne. '') then
            read(string(1:4),*,err=9999) sc_trajectory
        end if

c Load spacecraft ephemeris if necessary
        if (obs_isc .ne. 0) then
            status = RSPK_LoadSC(1, SC_IDS(obs_isc), nplanet,
     &                           sc_trajectory, .TRUE.)
            if (.not. status) goto 9999
        end if

c Read SPICE selection
        keyword = 'EPHEMERIS'
        status = WWW_GetKey('ephem', string)
        if (.not. status) goto 9999
        if (string .eq. '') goto 9999
        read(string, '(i3)', err=9999) ivalue

        status = RSPK_LoadFiles(1, nplanet, ivalue)
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
            if (.not. status) goto 9999
            if (string .eq. '') string = '0.'
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
c Generate the list of moon ids and names
c***********************************************************************

        keyword = 'MOON'
        do 100 i = 1, 9999
            status = WWW_GetKeys('moons', string)
            if (.not. status) goto 101

            read (string, *, err=9999) ivalue
            moon_ids(i) = ivalue + 100*nplanet

            iparen = index(string, '(')
            moon_names(i) = string(5:iparen-1)

            do j = 1, len(moon_names(i))
                ch = moon_names(i)(j:j)
                if (ch .ge. 'a' .and. ch .le. 'z') then
                    ch = char(ichar(ch) + ichar('A') - ichar('a'))
                    moon_names(i)(j:j) = ch
                end if
            end do
100     continue
101     continue
        nmoons = i - 1

        if (nmoons .eq. 0) then
            write(*,*)
            write(*,*) 'Error---No moons selected'
            stop
        end if

c***********************************************************************
c Ring selection
c***********************************************************************

        keyword = 'RING'
        do 110 i = 1, 9999
            status = WWW_GetKeys('rings', string)
            if (.not. status) goto 111
            read(string, *, err=9999) ring_option

c           Jupiter options (Main Ring, Gossamer Rings)
            if (ring_option .eq. 51) then
                ring_flags(1) = .TRUE.
            else if (ring_option .eq. 52) then
                ring_flags(2) = .TRUE.
                ring_flags(3) = .TRUE.

c           Saturn options (Main Rings, G Ring, E Ring)
            else if (ring_option .eq. 61) then
                ring_flags(1) = .TRUE.
            else if (ring_option .eq. 62) then
                ring_flags(2) = .TRUE.
                ring_flags(3) = .TRUE.
            else if (ring_option .eq. 63) then
                ring_flags(4) = .TRUE.
                ring_flags(5) = .TRUE.

c           Uranus option (Epsilon)
            else if (ring_option .eq. 71) then
                ring_flags(1) = .TRUE.

c           Neptune option (Adams)
            else if (ring_option .eq. 81) then
                ring_flags(1) = .TRUE.

            else
                goto 9999

            end if
110     continue
111     continue

c***********************************************************************
c Get the time interval
c***********************************************************************

        keyword = 'TIME_INTERVAL'
        status = WWW_GetKey('interval', string)
        if (.not. status) goto 9999
        if (string .eq. '') goto 9999
        read(string, *, err=9999) dsec

        keyword = 'TIME_UNIT'
        status = WWW_GetKey('time_unit', string)
        if (string(1:3) .eq. 'sec') then
                continue
        else if (string(1:3) .eq. 'min') then
                dsec = dsec * 60.d0
        else if (string(1:4) .eq. 'hour') then
                dsec = dsec * 60.d0 * 60.d0
        else if (string(1:3) .eq. 'day') then
                dsec = dsec * 60.d0 * 60.d0 * 24.d0
        else
                goto 9999
        end if

c Shortest valid time interval is one minute
        dsec = max(abs(dsec), 60.d0)
        dsec = 60.d0 * aint(dsec/60.d0 + 0.5d0)

c***********************************************************************
c Get the start and stop times
c***********************************************************************

c Initialize leap seconds table
        call FJUL_InitLeaps(JULIAN_LEAPSECS)

c Extract start time and round if necessary
        keyword = 'START_TIME'
        status = WWW_GetKey('start', string)

        status = FJUL_ParseDT(string, ' ', dutc, sec)
        if (.not. status) goto 9999

        sec = 60.d0 * aint(sec/60.d0 + 0.5d0)
        time1 = FJUL_TAIofDUTC(dutc) + sec

c Extract stop time and round upward if necessary
        keyword = 'STOP_TIME'
        status = WWW_GetKey('stop', string)

        status = FJUL_ParseDT(string, ' ', dutc, sec)
        if (.not. status) goto 9999

        time2 = FJUL_TAIofDUTC(dutc) + sec

c Check that range is within limits
        ntimes = int((time2 - time1) / dsec) + 1
        if (ntimes .le. 1) then
            write(*,*)
            write(*,*) 'Error---Number of time steps is less than 2'
            stop
        end if

        if (ntimes .gt. MAXRECS) then
            write(string,'(i6)') MAXRECS
            write(*,*)
            write(*,*) 'Error---Number of time steps exceeds limit ' //
     &                 'of ' // string(1:6)
            stop
        end if

c***********************************************************************
c Get the diagram parameters
c***********************************************************************

        keyword = 'PLOT_SCALE'
        status = WWW_GetKey('xrange', string)
        if (.not. status) goto 9999
        if (string .eq. '') goto 9999
        read(string, *, err=9999) xrange
        if (xrange .le. 0.) goto 9999

        keyword = 'PLOT_UNIT'
        status = WWW_GetKey('xunit', string)
        xscaled = (index(string,'radii') .gt. 0)

c***********************************************************************
c Set up plot title and captions
c***********************************************************************

        status = WWW_GetKeyUnsanitized('title', title)

        ncaptions = 1
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
            string(LASTNB(string)+1:) = ' '
            status = WWW_GetKey('lon_dir',   string(LASTNB(string)+2:))
            string(LASTNB(string)+1:) = ','
            status = WWW_GetKey('altitude', string(LASTNB(string)+2:))
            string(LASTNB(string)+1:) = ')'
            rcaptions(ncaptions) = string
        else
            status = WWW_GetKey('observatory', string)
            status = WWW_GetKey('sc_trajectory', string2)
            if (status) then
                string(LASTNB(string)+1:) =
     &                  ' (' // string2(5:LASTNB(string2)) // ')'
            end if
            rcaptions(ncaptions) = string
        end if

c***********************************************************************
c Generate plot
c This routine prints a message and aborts on error
c***********************************************************************

        call WWW_GetEnv('TRACKER_POSTFILE', filename)

        if (obs_isc .eq. 0 .or. SC_IDS(obs_isc) .eq. 'JWST'
     &                     .or. SC_IDS(obs_isc) .eq. 'HST') then
            call RSPK_TrackMoons(ntimes, time1, time2,
     &          xrange, xscaled,
     &          nmoons, moon_ids, moon_names,
     &          nrings, ring_flags, ring_rads,
     &          ring_grays, planet_gray,
     &          title, ncaptions, lcaptions, rcaptions, 180.d0,
     &          filename,
     &          MAXMOONS, moon_loc, limb_loc)
        else
            call RSPK_TrackMoonC(ntimes, time1, time2,
     &          xrange, xscaled,
     &          nmoons, moon_ids, moon_names,
     &          nrings, ring_flags, ring_rads,
     &          ring_grays, planet_gray,
     &          title, ncaptions, lcaptions, rcaptions, 90.d0,
     &          filename,
     &          MAXMOONS, moon_loc, limb_loc)
        end if

c***********************************************************************
c Write the table file
c***********************************************************************

c Open file
        call WWW_GetEnv('TRACKER_TEXTFILE', string)
        open(1, file=string, status='unknown')

c Write header
        write(1, 30) (moon_names(i)(1:LASTNB(moon_names(i))),
     &                          i=1,nmoons)

c Write table
        time = time1 - dsec
        do 300 irec = 1, ntimes
                time = time + dsec

c Calculate date and time, rounding (carefully!) to nearest minute
                tai = time
                dutc = FJUL_DUTCofTAI(tai, sec)
                call FJUL_HMSofSec(sec, hour, minute, test)
                if (test .ge. 30.d0) tai = tai + 30.d0

                dutc = FJUL_DUTCofTAI(tai, sec)
                call FJUL_HMSofSec(sec, hour, minute, test)

                call FJUL_YMDofDUTC(dutc, year, month, day)
                mjd = FJUL_MJDofTAI(tai, 0)
                write(1, 31) mjd, year, month, day, hour, minute,
     &                  limb_loc(irec),
     &                  (moon_loc(i,irec), i=1,nmoons)

300     continue

30      format(' mjd        year mo dy hr mi   limb', 25(1x,a9))
31      format(f11.4, i5, i3, i3, i3, i3, f7.3, 25f10.3)

        close(1)
        stop

c***********************************************************************
c Handle invalid input
c***********************************************************************

9999    continue
        write(*,90) 'Invalid value found for variable ',
     &                  keyword(1:LASTNB(keyword)),
     &                  string(1:LASTNB(string))
90      format(1x, a, a, ': ', a)
        stop

        end

c***********************************************************************
