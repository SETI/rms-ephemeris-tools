c***********************************************************************

        program EPHEM3_XXX

        implicit                none
        include                 'tools.inc'

        integer                 MAXRECS, MAXMOONS, MAXCOLS, MAXMCOLS
        parameter               (MAXRECS  = 100000)
        parameter               (MAXMOONS = 30)
        parameter               (MAXCOLS  = 22)
        parameter               (MAXMCOLS = 8)

        integer                 COL_MJD, COL_YMDHM, COL_YMDHMS,
     &                          COL_YDHM, COL_YDHMS, COL_OBSDIST,
     &                          COL_SUNDIST, COL_PHASE, COL_OBSOPEN,
     &                          COL_SUNOPEN, COL_OBSLON, COL_SUNLON,
     &                          COL_SUBOBS, COL_SUBSOL, COL_RADEC,
     &                          COL_EARTHRD, COL_SUNRD, COL_RADIUS,
     &                          COL_RADDEG, COL_LPHASE, COL_SUNSEP,
     &                          COL_LSEP
        parameter               (COL_MJD     = 1)
        parameter               (COL_YMDHM   = 2)
        parameter               (COL_YMDHMS  = 3)
        parameter               (COL_YDHM    = 4)
        parameter               (COL_YDHMS   = 5)
        parameter               (COL_OBSDIST = 6)
        parameter               (COL_SUNDIST = 7)
        parameter               (COL_PHASE   = 8)
        parameter               (COL_OBSOPEN = 9)
        parameter               (COL_SUNOPEN = 10)
        parameter               (COL_OBSLON  = 11)
        parameter               (COL_SUNLON  = 12)
        parameter               (COL_SUBOBS  = 13)
        parameter               (COL_SUBSOL  = 14)
        parameter               (COL_RADEC   = 15)
        parameter               (COL_EARTHRD = 16)
        parameter               (COL_SUNRD   = 17)
        parameter               (COL_RADIUS  = 18)
        parameter               (COL_RADDEG  = 19)
        parameter               (COL_LPHASE  = 20)
        parameter               (COL_SUNSEP  = 21)
        parameter               (COL_LSEP    = 22)

        integer                 MCOL_OBSDIST, MCOL_PHASE, MCOL_SUBOBS,
     &                          MCOL_SUBSOL, MCOL_RADEC, MCOL_OFFSET,
     &                          MCOL_OFFDEG, MCOL_ORBLON, MCOL_ORBOPEN
        parameter               (MCOL_OBSDIST = 1)
        parameter               (MCOL_PHASE   = 2)
        parameter               (MCOL_SUBOBS  = 3)
        parameter               (MCOL_SUBSOL  = 4)
        parameter               (MCOL_RADEC   = 5)
        parameter               (MCOL_OFFSET  = 6)
        parameter               (MCOL_OFFDEG  = 7)
        parameter               (MCOL_ORBLON  = 8)
        parameter               (MCOL_ORBOPEN = 9)

        double precision        DPR, HPR, SPR, MAXSECS
        parameter               (MAXSECS = 360.d0 * 60.d0 * 60.d0)

        integer                 nplanet, planet_id, i, j, ivalue, isc,
     &                          iparen, jparen, obs_isc, sc_trajectory,
     &                          ncolumns,  column_types(MAXCOLS),
     &                          nmooncols, nmooncol_types(MAXMCOLS),
     &                          nmoons, moon_ids(MAXMOONS), lname
        logical                 status, found, WWW_GetKey, WWW_GetKeys
        character*16            moon_names(MAXMOONS)
        character*255           string, string2
        character*40            keyword, sc_abbrev
        character*1             ch
        character*5             prefix

        integer                 ntimes, dutc, ios
        double precision        dsec, time, time1, time2, sec, ticks,
     &                          et, tai, mjd, value
        integer                 year, month, day, hour, minute
        double precision        planet_ra, planet_dec, cosdec,
     &                          phase, obs_b, sun_b, sun_db,
     &                          obs_lon, sun_lon, subobs_lat,
     &                          subobs_lon, subsol_lat, subsol_lon,
     &                          sun_dist, obs_dist, ra, dec, dra, ddec,
     &                          rkm, rradians, lat, lon, alt,
     &                          moon_phase, sun_sep, moon_sep
        logical                 isdark
        logical                 call_ringopen, call_latlon, call_ranges

        integer                 irec, icol, lrec, lstr, lstr2
        character*4096          record

c External function declarations
        logical                 RSPK_LoadFiles, RSPK_LoadSC,
     &                          FJUL_ParseDT, ParseAngle
        integer                 FJUL_DUTCofTAI, LASTNB
        double precision        FJUL_TAIofDUTC, FJUL_MJDofTAI,
     &                          FJUL_ETofTAI

c***********************************************************************
c Initialize
c***********************************************************************

c Reduce SPICE error messages
        call ERRPRT('SET', 'NONE, SHORT, LONG, EXPLAIN')

c Radian conversion factors
        DPR = 45.d0 / ATAN(1.d0)
        SPR = DPR * 3600.d0
        HPR = DPR / 15.d0

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
        lstr2 = LASTNB(string2)

        value = 0.d0
        read(string,*,iostat=ios) string
        if (value .eq. 1.d0) lstr2= lstr2 - 1

        write(*,10) '       Interval: ' // string(1:LASTNB(string))
     &                                  // ' '
     &                                  // string2(1:lstr2)

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

c General columns
        status = WWW_GetKeys('columns', string)
        if (status) then
          write(*,10) 'General columns: ' // string(5:LASTNB(string))

          do while (WWW_GetKeys('columns', string))
            write(*,10) '                 ' // string(5:LASTNB(string))
          end do

          write(*,10) ''
        else
          write(*,10) 'General columns:'
        end if

        write(*,10) ''

c Moon columns
        status = WWW_GetKeys('mooncols', string)
        if (status) then
          write(*,10) '   Moon columns: ' // string(5:LASTNB(string))

          do while (WWW_GetKeys('mooncols', string))
            write(*,10) '                 ' // string(5:LASTNB(string))
          end do

          write(*,10) ''
        else
          write(*,10) '   Moon columns:'
        end if

        write(*,10) ''

c Moon selection
        status = WWW_GetKeys('moons', string)
        if (status) then
          write(*,10) ' Moon selection: ' // string(5:LASTNB(string))

          do while (WWW_GetKeys('moons', string))
            write(*,10) '                 ' // string(5:LASTNB(string))
          end do

          write(*,10) ''
        else
          write(*,10) ' Moon selection:'
        end if

        write(*,10) ''

c***********************************************************************
c Load SPICE files
c***********************************************************************

c Identify planet
        keyword = 'PLANET'
        call WWW_GetEnv('NPLANET', string)
        read(string, '(i1)', err=9999) nplanet
        if (nplanet .lt. 4 .or. nplanet .gt. 9) goto 9999

        planet_id = 100 * nplanet + 99

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

c Load spacecraft ephemeris if necessary
        if (obs_isc .ne. 0) then
            status = RSPK_LoadSC(1, SC_IDS(obs_isc), nplanet,
     &                           sc_trajectory, .TRUE.)
            if (.not. status) goto 9999
        end if

c Read SPICE selection
        keyword = 'EPHEMERIS'
        status = WWW_GetKey('ephem', string)
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

c***********************************************************************
c Column selection
c***********************************************************************

        keyword = 'COLUMN'
        do 110 i = 1, 9999
            status = WWW_GetKeys('columns', string)
            if (.not. status) goto 111

            read(string, *, err=9999) column_types(i)
110     continue
111     continue
        ncolumns = i - 1

c***********************************************************************
c Moon column selection
c***********************************************************************

        keyword = 'MOON_COLUMN'
        do 120 i = 1, 9999
            status = WWW_GetKeys('mooncols', string)
            if (.not. status) goto 121

            read(string, *, err=9999) nmooncol_types(i)
120     continue
121     continue
        nmooncols = i - 1

c***********************************************************************
c Get the time interval
c***********************************************************************

        keyword = 'TIME_INTERVAL'
        status = WWW_GetKey('interval', string)
        if (string .eq. ' ') string = '1'
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

        dsec = max(abs(dsec), 1.d0)

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

c Extract stop time
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
c Write the table file
c***********************************************************************

c Open file
        keyword = "OUTPUT_FILE"
        call WWW_GetEnv('EPHEM_FILE', string)
        open(1, file=string, status='unknown', err=9999)

c Write table
        call Rec_Init(record, lrec)

c Initialize call flags
        call_ringopen = .FALSE.
        call_latlon   = .FALSE.
        call_ranges   = .FALSE.

c Loop through records
        time = time1 - 2*dsec
        do 320 irec = 0, ntimes
            time = time + dsec

c Always calculate planet location
            if (irec .ne. 0) then
                et = FJUL_ETofTAI(time)
                call RSPK_BodyRaDec(et, planet_id,
     &                              planet_ra, planet_dec)
                cosdec = cos(planet_dec)
            end if

c Calculate ring angles if necessary
            if (call_ringopen) then
                call RSPK_RingOpen(et, obs_b, sun_b, sun_db, isdark,
     &                  obs_lon, sun_lon)
            end if

c Calculate sub-sobserver and sub-solar angles if necessary
            if (call_latlon) then
                call RSPK_BodyLonLat(et, planet_id,
     &                  subobs_lon, subobs_lat, subsol_lon, subsol_lat)
            end if

c Calculate ranges if necessary
            if (call_ranges) then
                call RSPK_Ranges(et, sun_dist, obs_dist)
            end if

c***********************************************************************
c Loop through general columns
c***********************************************************************

        do 300 icol = 1, ncolumns

c Modified Julian Date
        if (column_types(icol) .eq. COL_MJD) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, ' mjd        ')
            else
                mjd = FJUL_MJDofTAI(time, 0)
                write(string,'(f12.5)') FJUL_MJDofTAI(time, 0)
                call Rec_Append(record, lrec, string(1:12))
            end if

c Year, Month, Day, Hour, Minute
        else if (column_types(icol) .eq. COL_YMDHM) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, 'year mo dy hr mi')
            else
c               Round to nearest minute
                dutc = FJUL_DUTCofTAI(time, ticks)
                ticks = 60.d0 * nint(ticks / 60.d0)
                if (ticks .eq. 86400.d0) then
                    dutc = dutc + 1
                    ticks = 0.d0
                end if

                call FJUL_YMDofDUTC(dutc, year, month, day)
                call FJUL_HMSofSec(ticks, hour, minute, sec)

                write(string, '(i4,4i3)')
     &                  year, month, day, hour, minute
                call Rec_Append(record, lrec, string(1:16))
            end if

c Year, Month, Day, Hour, Minute, Second
        else if (column_types(icol) .eq. COL_YMDHMS) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, 'year mo dy hr mi sc')
            else

c               Round to nearest second
                dutc = FJUL_DUTCofTAI(time, ticks)
                ticks = nint(ticks)
                if (ticks .eq. 86400.d0) then
                    dutc = dutc + 1
                    ticks = 0.d0
                end if

                call FJUL_YMDofDUTC(dutc, year, month, day)
                call FJUL_HMSofSec(ticks, hour, minute, sec)

                write(string, '(i4,5i3)')
     &                  year, month, day, hour, minute, nint(sec)
                call Rec_Append(record, lrec, string(1:19))
            end if

c Year, DOY, Hour, Minute
        else if (column_types(icol) .eq. COL_YDHM) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, 'year doy hr mi')
            else

c               Round to nearest minute
                dutc = FJUL_DUTCofTAI(time, ticks)
                ticks = 60.d0 * nint(ticks / 60.d0)
                if (ticks .eq. 86400.d0) then
                    dutc = dutc + 1
                    ticks = 0.d0
                end if

                call FJUL_YDofDUTC(dutc, year, day)
                call FJUL_HMSofSec(ticks, hour, minute, sec)

                write(string, '(2i4,2i3)')
     &                  year, day, hour, minute
                call Rec_Append(record, lrec, string(1:14))
            end if

c Year, DOY, Hour, Minute, Second
        else if (column_types(icol) .eq. COL_YDHMS) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, 'year doy hr mi sc')
            else

c               Round to nearest second
                dutc = FJUL_DUTCofTAI(time, ticks)
                ticks = nint(ticks)
                if (ticks .eq. 86400.d0) then
                    dutc = dutc + 1
                    ticks = 0.d0
                end if

                call FJUL_YDofDUTC(dutc, year, day)
                call FJUL_HMSofSec(ticks, hour, minute, sec)

                write(string, '(2i4,3i3)')
     &                  year, day, hour, minute, nint(sec)
                call Rec_Append(record, lrec, string(1:17))
            end if

c Observer-planet distance (km)
        else if (column_types(icol) .eq. COL_OBSDIST) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, '  obs_dist')
                call_ranges = .TRUE.
            else
                write(string,'(f10.0)') obs_dist
                if (string(1:1) .eq. '*') then
                    write(string,'(1p, e10.4)') obs_dist
                end if
                call Rec_Append(record, lrec, string(1:10))
            end if

c Sun-planet distance (km)
        else if (column_types(icol) .eq. COL_SUNDIST) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, '  sun_dist')
                call_ranges = .TRUE.
            else
                write(string,'(1p, e10.4)') sun_dist
                call Rec_Append(record, lrec, string(1:10))
            end if

c Phase angle (deg)
        else if (column_types(icol) .eq. COL_PHASE) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, '    phase')
            else
                call RSPK_Phase(et, phase)
                write(string,'(f9.5)') phase * DPR
                call Rec_Append(record, lrec, string(1:9))
            end if

c Ring opening angle to observer (deg)
        else if (column_types(icol) .eq. COL_OBSOPEN) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, ' obs_open')
                call_ringopen = .TRUE.
            else
                write(string,'(f9.5)') obs_b * DPR
                call Rec_Append(record, lrec, string(1:9))
            end if

c Ring opening angle to the Sun (deg)
        else if (column_types(icol) .eq. COL_SUNOPEN) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, ' sun_open')
                call_ringopen = .TRUE.
            else
                write(string,'(f9.5)') sun_b * DPR
                call Rec_Append(record, lrec, string(1:9))
            end if

c Sub-observer inertial longitude (deg, J2000)
        else if (column_types(icol) .eq. COL_OBSLON) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, '  obs_lon')
                call_ringopen = .TRUE.
            else
                write(string,'(f9.5)') obs_lon * DPR
                call Rec_Append(record, lrec, string(1:9))
            end if

c Sub-solar inertial longitude (deg, J2000)
        else if (column_types(icol) .eq. COL_SUNLON) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, '  sun_lon')
                call_ringopen = .TRUE.
            else
                write(string,'(f9.5)') sun_lon * DPR
                call Rec_Append(record, lrec, string(1:9))
            end if

c Sub-observer latitude and rotating longitude (deg)
        else if (column_types(icol) .eq. COL_SUBOBS) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, 'subobslat subobslon')
                call_latlon = .TRUE.
            else
                write(string,'(f9.5,f10.5)')
     &                  subobs_lat * DPR, subobs_lon * DPR
                call Rec_Append(record, lrec, string(1:19))
            end if

c Sub-solar latitude and rotating longitude (deg)
        else if (column_types(icol) .eq. COL_SUBSOL) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, 'subsollat subsollon')
                call_latlon = .TRUE.
            else
                write(string,'(f9.5,f10.5)')
     &                  subsol_lat * DPR, subsol_lon * DPR
                call Rec_Append(record, lrec, string(1:19))
            end if

c Planet RA and Dec (hours, deg)
        else if (column_types(icol) .eq. COL_RADEC) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, 'planet_ra planet_dec')
            else
                write(string,'(f9.6,f11.5)')
     &                  planet_ra * HPR, planet_dec * DPR
                call Rec_Append(record, lrec, string(1:20))
            end if

c Earth RA and Dec (hours, deg)
        else if (column_types(icol) .eq. COL_EARTHRD) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, ' earth_ra earth_dec')
            else
                call RSPK_BodyRaDec(et, EARTH_ID, ra, dec)
                write(string,'(f9.6,f10.5)') ra * HPR, dec * DPR
                call Rec_Append(record, lrec, string(1:19))
            end if

c Sun RA and Dec (hours, deg)
        else if (column_types(icol) .eq. COL_SUNRD) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, '   sun_ra   sun_dec')
            else
                call RSPK_BodyRaDec(et, SUN_ID, ra, dec)
                write(string,'(f9.6,f10.5)') ra * HPR, dec * DPR
                call Rec_Append(record, lrec, string(1:19))
            end if

c Projected equatorial radius (arcsec)
        else if (column_types(icol) .eq. COL_RADIUS) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, '  radius')
            else
                call RSPK_LimbRad(et, rkm, rradians)
                write(string,'(f8.3)') rradians * SPR
                call Rec_Append(record, lrec, string(1:8))
            end if

c Projected equatorial radius (deg)
        else if (column_types(icol) .eq. COL_RADDEG) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, '  r_deg')
            else
                call RSPK_LimbRad(et, rkm, rradians)
                write(string,'(f7.3)') rradians * DPR
                call Rec_Append(record, lrec, string(1:7))
            end if

c Lunar phase angle (deg)
        else if (column_types(icol) .eq. COL_LPHASE) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, 'lun_phase')
            else
                call RSPK_BodyPhase(et, MOON_ID, moon_phase)
                write(string,'(f9.5)') moon_phase * DPR
                call Rec_Append(record, lrec, string(1:9))
            end if

c Sun-planet separation angle (deg)
        else if (column_types(icol) .eq. COL_SUNSEP) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, '  sun_sep')
            else
                call RSPK_Conjunc(et, planet_id, SUN_ID, sun_sep)
                write(string,'(f9.5)') sun_sep * DPR
                call Rec_Append(record, lrec, string(1:9))
            end if

c Moon-planet separation angle (deg)
        else if (column_types(icol) .eq. COL_LSEP) then
            if (irec .eq. 0) then
                call Rec_Append(record, lrec, ' moon_sep')
            else
                call RSPK_Conjunc(et, planet_id, MOON_ID, moon_sep)
                write(string,'(f9.5)') moon_sep * DPR
                call Rec_Append(record, lrec, string(1:9))
            end if
        end if

300     continue

c***********************************************************************
c Info for each moon
c***********************************************************************

        do 310 i = 1, nmoons
            lname = LASTNB(moon_names(i))
            if (lname .ge. 4) then
                prefix = moon_names(i)(1:4) // '_'
            else
                prefix = moon_names(i)(1:lname) // '____'
            end if

        do 311 icol = 1, nmooncols

c Distance (km)
            if (nmooncol_types(icol) .eq. MCOL_OBSDIST) then
                if (irec .eq. 0) then
                    call Rec_Append(record, lrec, prefix // 'dist')
                else
                    call RSPK_BodyRanges(et, moon_ids(i), sun_dist,
     &                                   obs_dist)
                    write(string,'(f10.0)') obs_dist
                    if (string(1:1) .eq. '*') then
                        write(string,'(1p, e10.4)') obs_dist
                    end if
                    call Rec_Append(record, lrec, string(1:10))
                end if

c Phase angle (deg)
            else if (nmooncol_types(icol) .eq. MCOL_PHASE) then
                if (irec .eq. 0) then
                    call Rec_Append(record, lrec, prefix // 'phase')
                else
                    call RSPK_BodyPhase(et, moon_ids(i), phase)
                    write(string,'(f10.5)') phase * DPR
                    call Rec_Append(record, lrec, string(1:10))
                end if

c Sub-observer latitude and rotating longitude (deg)
            else if (nmooncol_types(icol) .eq. MCOL_SUBOBS) then
                if (irec .eq. 0) then
                    call Rec_Append(record, lrec,
     &                  prefix // 'olat ' // prefix // 'olon')
                else
                    call RSPK_BodyLonLat(et, moon_ids(i),
     &                  subobs_lon, subobs_lat, subsol_lon, subsol_lat)
                    write(string,'(f9.5,f10.5)')
     &                  subobs_lat * DPR, subobs_lon * DPR
                    call Rec_Append(record, lrec, string(1:19))
                end if

c Sub-solar latitude and rotating longitude (deg)
            else if (nmooncol_types(icol) .eq. MCOL_SUBSOL) then
                if (irec .eq. 0) then
                    call Rec_Append(record, lrec,
     &                  prefix // 'slat ' // prefix // 'slon')
                else
                    call RSPK_BodyLonLat(et, moon_ids(i),
     &                  subobs_lon, subobs_lat, subsol_lon, subsol_lat)
                    write(string,'(f9.5,f10.5)')
     &                  subsol_lat * DPR, subsol_lon * DPR
                    call Rec_Append(record, lrec, string(1:19))
                end if

c RA & Dec
            else if (nmooncol_types(icol) .eq. MCOL_RADEC) then
                if (irec .eq. 0) then
                    call Rec_Append(record, lrec,
     &                  '  ' // prefix // 'ra  ' // prefix // 'dec')
                else
                    call RSPK_BodyRaDec(et, moon_ids(i), ra, dec)
                    write(string,'(f9.6,f10.5)') ra * HPR, dec * DPR
                    call Rec_Append(record, lrec, string(1:19))
                end if

c Offset RA & Dec (arcsec)
            else if (nmooncol_types(icol) .eq. MCOL_OFFSET) then
                if (irec .eq. 0) then
                    call Rec_Append(record, lrec,
     &                  ' ' // prefix // 'dra ' // prefix // 'ddec')
                else
                    call RSPK_BodyRaDec(et, moon_ids(i), ra, dec)
                    ddec = SPR * (dec - planet_dec)
                    dra  = SPR * (ra  - planet_ra)
                    if (dra .lt. -0.5*MAXSECS) dra = dra + MAXSECS
                    if (dra .gt.  0.5*MAXSECS) dra = dra - MAXSECS
                    dra = dra * cosdec
                    write(string,'(f9.3,f10.3)') dra, ddec
                    call Rec_Append(record, lrec, string(1:19))
                end if

c Offset RA & Dec (deg)
            else if (nmooncol_types(icol) .eq. MCOL_OFFDEG) then
                if (irec .eq. 0) then
                    call Rec_Append(record, lrec,
     &                  ' ' // prefix // 'dra ' // prefix // 'ddec')
                else
                    call RSPK_BodyRaDec(et, moon_ids(i), ra, dec)
                    ddec = DPR * (dec - planet_dec)
                    dra  = DPR * (ra  - planet_ra)
                    if (dra .lt. -180.d0) dra = dra + 180.d0
                    if (dra .gt.  180.d0) dra = dra - 180.d0
                    dra = dra * cosdec
                    write(string,'(f9.5,f10.5)') dra, ddec
                    call Rec_Append(record, lrec, string(1:19))
                end if

c Orbit longitude
            else if (nmooncol_types(icol) .eq. MCOL_ORBLON) then
                if (irec .eq. 0) then
                    call Rec_Append(record, lrec, prefix // 'orbit')
                else
                    call RSPK_OrbitOpen(et, moon_ids(i), obs_b, obs_lon)
                    write(string,'(f10.5)') obs_lon * DPR
                    call Rec_Append(record, lrec, string(1:10))
                end if

c Orbit opening angle
            else if (nmooncol_types(icol) .eq. MCOL_ORBOPEN) then
                if (irec .eq. 0) then
                    call Rec_Append(record, lrec, prefix // 'open')
                else
                    call RSPK_OrbitOpen(et, moon_ids(i), obs_b, obs_lon)
                    write(string,'(f9.5)') obs_b * DPR
                    call Rec_Append(record, lrec, string(1:9))
                end if

            end if
311     continue
310     continue

c***********************************************************************
c End of column loops
c***********************************************************************

        call Rec_Write(1, record, lrec)

320     continue
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

        subroutine Rec_Init(record, lrec)
        character*(*)   record
        integer         lrec

        record = ' '
        lrec = -1

        return
        end

c***********************************************************************

        subroutine Rec_Append(record, lrec, string)
        character*(*)   record, string
        integer         lrec

        integer         lstring

c Skip one blank
        lrec = lrec + 1

c Calculate number of characters to append
        lstring = min(len(string), len(record) - lrec)
        if (lstring .le. 0) return

c Append string
        record(lrec+1:lrec+lstring) = string(1:lstring)

c Update length
        lrec = lrec + lstring

        return
        end

c***********************************************************************

        subroutine Rec_Write(unit, record, lrec)
        integer         unit, lrec
        character*(*)   record

        if (lrec .ge. 0) then
                write(unit, '(a)') record(1:lrec)
        end if

        call Rec_Init(record, lrec)

        return
        end

c***********************************************************************
