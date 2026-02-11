c***********************************************************************
c This internal function reads in the list of stars
c***********************************************************************

        logical function ReadStars(lunit, filename,
     &                             nstars, MAX_NSTARS,
     &                             star_ras, star_decs, star_names)
        character*(*)           filename
        integer                 lunit, nstars, MAX_NSTARS
        double precision        star_ras(MAX_NSTARS+10),
     &                          star_decs(MAX_NSTARS+10)
        character*20            star_names(MAX_NSTARS+10)

        integer                 i
        real*8                  angle, RPD
        character*80            string
        logical                 status, ParseAngle

        open(lunit, file=filename, status='old', err=9999)

        do i = 1, MAX_NSTARS

c       Read next line, skipping comments
310         continue
                read(lunit, '(a)', err=9999, end=399) string
                if (string(1:1) .eq. '!') goto 310

c       Read name
            star_names(i) = string

c       Read RA
            read(lunit, '(a)', err=9999, end=9999) string
            status = ParseAngle(string, angle)
            if (.not. status) goto 9999
            star_ras(i) = angle * 15.d0 * RPD()

c       Read Dec
            read(lunit, '(a)', err=9999, end=9999) string
            status = ParseAngle(string, angle)
            if (.not. status) goto 9999
            star_decs(i) = angle * RPD()

        end do
399     continue
        nstars = i - 1
        close(lunit)

        ReadStars = .TRUE.
        return

9999    continue
        ReadStars = .FALSE.
        return

        end

c***********************************************************************
c This internal function parses an angle as a set of three values,
c assumed to be hours/degrees, minutes and seconds.  It returns the
c value as a floating-point number in hours/degrees.
c***********************************************************************

        logical function ParseAngle(string, angle)
        character*(*)           string
        double precision        angle

        double precision        value1, value2, value3
        integer                 i

c Try to read three values
        read(string, *, err=101, end=101)  value1, value2, value3
        goto 200

c If that fails, try to read two values
101     continue
        read(string, *, err=102, end=102)  value1, value2
        value3 = 0.d0
        goto 200

c If that fails, try to read a single value
102     continue
        read(string, *, err=9999, end=9999) value1
        value2 = 0.d0
        value3 = 0.d0

200     continue

c Interpret as degrees/hours, minutes, seconds, neglecting sign
        if (value2 .lt. 0.d0) goto 9999
        if (value3 .lt. 0.d0) goto 9999
        angle = abs(value1) + value2/60.d0 + value3/3600.d0

c Check for minus sign as first non-blank character
c Note: we do it this way because if value1 is zero, its sign gets
c lost.
        do 300 i = 1, len(string)
            if (string(i:i) .ne. ' ') goto 301
300     continue
301     continue
        if (string(i:i) .eq. '-') angle = -angle

        ParseAngle = .TRUE.
        return

9999    continue
        ParseAngle = .FALSE.
        angle = 0.d0
        return

        end

c***********************************************************************

        subroutine DMS_string(value, seps, ndecimal, string)
        real*8          value
        character*(*)   seps, string
        integer         ndecimal

        real*8          secs
        integer         isign, ntens, ims, isec, imin, ideg

        isign = nint(sign(1.d0, value))
        secs = abs(value * 3600.d0)

        ntens = 10**ndecimal

        ims = nint(secs * ntens)
        isec = ims / ntens
        ims = ims - ntens*isec

        imin = isec / 60
        isec = isec - 60*imin

        ideg = imin / 60
        imin = imin - 60*ideg

        ideg = ideg * isign

c Old code, incompatible with Absoft FORTRAN
c       write(string, 10) ideg, seps(1:1), imin, seps(2:2),
c     &                 isec, ims, seps(3:3)
c10     format(i3, a1, 1x, i2.2, a1, 1x, i2.2, '.',
c     &         i<ndecimal>.<ndecimal>, a1)

c New code, only handles case of ndecimal = 3 or 4. In practice, this
c is fine.
        if (ndecimal .eq. 3) then
            write(string, 13) ideg, seps(1:1), imin, seps(2:2),
     &                        isec, ims, seps(3:3)
        else
            write(string, 14) ideg, seps(1:1), imin, seps(2:2),
     &                        isec, ims, seps(3:3)
        end if
13      format(i3, a1, 1x, i2.2, a1, 1x, i2.2, '.', i3.3, a1)
14      format(i3, a1, 1x, i2.2, a1, 1x, i2.2, '.', i4.4, a1)

        if (isign .lt. 0 .and. ideg .eq. 0) string(2:2) = '-'

        return
        end

c***********************************************************************
