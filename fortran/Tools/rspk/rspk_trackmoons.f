c*******************************************************************************
c$ Component_name:
c       RSPK_TrackMoons
c$ Abstract:
c       Generates a Postscript file and a table showing the east-west offset
c       of a set of moons from their planet.
c$ Keywords:
c       SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_TrackMoons(ntimes, time1, time2, xrange, xscaled,
c               nmoons, moon_ids, moon_names,
c               nrings, ring_flags, ring_rads, ring_grays, planet_gray,
c               title, ncaptions, lcaptions, rcaptions, align_loc,
c               filename,
c               maxmoons, moon_arcsec, limb_arcsec)
c
c       integer                 ntimes
c       double precision        time1, time2, xrange
c       logical                 xscaled
c
c       integer                 nmoons, moon_ids(*)
c       character*(*)           moon_names(*)
c
c       integer                 nrings
c       logical                 ring_flags(*)
c       double precision        ring_rads(*), ring_grays(*), planet_gray
c
c       integer                 ncaptions
c       character*(*)           title, lcaptions(*), rcaptions(*)
c       double precision        align_loc
c
c       character*(*)           filename
c
c       integer                 maxmoons
c       double precision        moon_arcsec, limb_arcsec
c$ Inputs:
c       ntimes                  number of time steps.
c       time1, time2            start and stop times of plot (sec, TAI).
c       xrange                  half-range of x-axis (arcsec or planet radii).
c       xscaled                 .TRUE. to use planet radii on x axis;
c                               .FALSE. to use arcsec.
c
c       nmoons                  number of moons in list.
c       moon_ids(*)             body IDs of moons based on SPICE toolkit.
c       moon_names(*)           name of each moon, for optional labels.
c
c       nrings                  number of rings in list.  Rings must be in order
c                               of increasing radius.
c       ring_flags(*)           .TRUE. to include ring in plot, .FALSE.
c                               otherwise
c       ring_rads(*)            semimajor axis of each ring (km).
c       ring_grays(*)           gray level to use inward from each ring:
c                               0=black; 1=white.
c       planet_gray             gray level to use for planet.
c
c       title                   title string to appear above diagram.
c       ncaptions               number of captions lines.
c       lcaptions(*)            left part of each caption line.
c       rcaptions(*)            right part of each caption line.
c       align_loc               alignment as distance from left edge (points).
c
c       filename                output Postscript filename.
c
c       maxmoons                dimensioned limit on number of moons.
c$ Outputs:
c       moon_arcsec(i,*)        table of offsets of moon #i from planet.
c                               Positive=east; negative=west.
c       limb_arcsec             offset of planetary limb from planet.
c$ Returns:
c       none
c$ Side_effects:
c       A Postscript file of the specified name is created.
c$ Detailed_description:
c       This subroutine generates a Postscript file and a table showing the
c       east-west offset of a set of moons from their planet.  Time increases
c       downward in the plot and west is toward the right.  Positions of moons
c       are shown in solid lines, which vary roughly sinusoidally down the
c       diagram.  Locations of rings and the planet are shown as gray zones
c       near the center of the diagram.
c
c       The user may also specify a title and a set of captions.  The title
c       appears above the diagram and centered.  Captions appear below the
c       diagram.  Each caption takes the form of a left part and a right part;
c       the right part is aligned (left-justified) at a user-specified distance
c       from the left edge of the diagram; the left part appears right-justified
c       beginning two spaces to the left of the right part.
c$ External_references:
c       SPICE toolkit, RSPK toolkit, Julian toolkit.
c$ Examples:
c       None.
c$ Error_handling:
c       None.  The SPICE toolkit error handling is in effect.
c$ Limitations:
c       None.
c$ Author_and_institution:
c       Mark R. Showalter
c       PDS Rings Node, NASA/Ames Research Center
c$ Version_and_date:
c       2.0: December 1996
c       2.1; April 2003
c$ Change_history:
c       2.0: Adapted from RPX_Tracker.f
c       2.1: Modified for compatibility with Absoft Fortran for Macintosh.
c*******************************************************************************

        subroutine RSPK_TrackMoons(ntimes, time1, time2,
     &          xrange, xscaled,
     &          nmoons, moon_ids, moon_names,
     &          nrings, ring_flags, ring_rads, ring_grays, planet_gray,
     &          title, ncaptions, lcaptions, rcaptions, align_loc,
     &          filename,
     &          maxmoons, moon_arcsec, limb_arcsec)

        implicit                none
        integer                 ntimes
        double precision        time1, time2, xrange
        logical                 xscaled

        integer                 nmoons, moon_ids(*)
        character*(*)           moon_names(*)

        integer                 nrings
        logical                 ring_flags(*)
        double precision        ring_rads(*), ring_grays(*), planet_gray

        integer                 ncaptions
        character*(*)           title, lcaptions(*), rcaptions(*)
        double precision        align_loc

        character*(*)           filename

        integer                 maxmoons
        double precision        moon_arcsec(maxmoons,*), limb_arcsec(*)

c Internal variables
        include                 'rspk_common.inc'

        integer                 i, j, i1, i2, nradii, irecband, ltext
        double precision        t, dt, et, SPR, rplanet, radii(3)

        integer                 MAXTIMES
        parameter               (MAXTIMES = 10000)
        logical                 excluded(MAXTIMES)

        integer                 LASTNB
        double precision        FJUL_ETofTAI, DPR

        integer                 lplanet
        character*8             planetstr
        character*24            tempstr

c Planet names
        character*8             planet_names(4:8)/ 'Mars', 'Jupiter',
     &                                  'Saturn', 'Uranus', 'Neptune' /

        double precision        PLOT_HEIGHT, BAND_WIDTH
        data                    PLOT_HEIGHT/612.d0/
        data                    BAND_WIDTH/16.d0/

c***********************************************************************
c Tabulate the limb and moon positions
c***********************************************************************

c Radians to seconds conversion factor
        SPR = DPR() * 3600.d0

c Look up radius of planet
        call BODVAR(planet_id, 'RADII', nradii, radii)
        rplanet = radii(1)

c Loop through times...
        dt = (time2 - time1) / dble(ntimes - 1)
        t = time1 - dt
        do 100 i = 1, ntimes
                t = t + dt

                et = FJUL_ETofTAI(t)

c Evaluate moon offsets
                call RSPK_MoonDist(et, nmoons, moon_ids,
     &                  moon_arcsec(1,i), limb_arcsec(i))

c Convert from radians to arcsec
                limb_arcsec(i) = limb_arcsec(i) * SPR
                do 110 j = 1, nmoons
                        moon_arcsec(j,i) = moon_arcsec(j,i) * SPR
110             continue

100     continue

c***********************************************************************
c Open the Postscript file and initialize
c***********************************************************************

        open(1, file=filename, status='unknown')

        write(1,1) '%!PS-Adobe-2.0 EPSF-2.0'

        i2 = LASTNB(filename)
        do 200 i1 = i2, 1, -1
                if (filename(i1:i1) .eq. '/' .or.
     &              filename(i1:i1) .eq. ']' .or.
     &              filename(i1:i1) .eq. ':') goto 201
200     continue
201     continue
        write(1,1) '%%Title: ' // filename(i1+1:i2)

        planetstr = planet_names(planet_num)
        lplanet = LASTNB(planetstr)
        write(1,1) '%%Creator: ' // planetstr(1:lplanet) //
     &             ' Moon Tracker, ' //
     &             'PDS Ring-Moon Systems Node'

        write(1,1) '%%BoundingBox: 0 0 612 792'
        write(1,1) '%%Pages: 1'
        write(1,1) '%%DocumentFonts: Helvetica'
        write(1,1) '%%EndComments'
        write(1,1) '%'
        write(1,1) '1 setlinewidth'
c       write(1,1) '0 setlinecap'
c       write(1,1) '1 setlinejoin'
        write(1,1) '/TextHeight 12 def'
        write(1,1) '/Helvetica findfont TextHeight scalefont setfont'
        write(1,1) '/in {72 mul} def'
        write(1,1) '/min {2 copy gt {exch} if pop} def'
        write(1,1) '/max {2 copy lt {exch} if pop} def'
        write(1,1) '/I1  2.0 in def'
        write(1,1) '/I2  7.5 in def'
        write(1,1) '/J1  2.0 in def'
        write(1,1) '/J2 10.0 in def'
        write(1,1) '/DI I2 I1 sub def'
        write(1,1) '/DJ J2 J1 sub def'
        write(1,1) '/Ticksize1 0.2 in def'
        write(1,1) '/Ticksize2 0.1 in def'
        write(1,1) '/DrawBox {newpath 0 0 moveto 0 DJ lineto'
        write(1,1) '  DI DJ lineto DI 0 lineto closepath stroke} def'
        write(1,1) '/ClipBox {newpath 0 0 moveto 0 DJ lineto'
        write(1,1) '  DI DJ lineto DI 0 lineto closepath clip} def'
        write(1,1) '/SetLimits {/Y2 exch def /Y1 exch def /X2 exch def'
        write(1,1) '  /X1 exch def'
        write(1,1) '  /DX X2 X1 sub def /XSCALE DI DX div def'
        write(1,1) '  /DY Y2 Y1 sub def /YSCALE DJ DY div def} def'
        write(1,1) '/Xcoord {X1 sub XSCALE mul} def'
        write(1,1) '/Ycoord {Y1 sub YSCALE mul} def'
        write(1,1) '/LabelBelow {dup stringwidth pop -0.5 mul'
        write(1,1) '  TextHeight -1.3 mul rmoveto show} def'
        write(1,1) '/LabelLeft {dup stringwidth pop TextHeight 0.3 mul'
        write(1,1) '  add neg TextHeight -0.5 mul rmoveto show} def'
        write(1,1) '/Xlabel {gsave DI 2 div TextHeight -3.0 mul'
        write(1,1) '  translate 1.2 1.2 scale dup stringwidth pop'
        write(1,1) '  -0.5 mul 0 moveto show grestore} def'
        write(1,1) '%'
        write(1,1) '% Macros for plotting ticks'
        write(1,1) '% Usage: x label XT1; x XT2; y label YT1; y YT2'
        write(1,1) '/XT1 {exch Xcoord dup DJ newpath moveto dup'
        write(1,1) '  DJ Ticksize1 sub lineto stroke dup 0 newpath'
        write(1,1) ' moveto dup Ticksize1 lineto stroke 0 moveto'
        write(1,1) '  LabelBelow} def'
        write(1,1) '/XT2 {Xcoord dup DJ newpath moveto dup'
        write(1,1) '  DJ Ticksize2 sub lineto stroke dup 0 newpath'
        write(1,1) '  moveto Ticksize2 lineto stroke} def'
        write(1,1) '/YT1 {exch Ycoord dup DI exch newpath moveto dup'
        write(1,1) '  DI Ticksize1 sub exch lineto stroke dup 0 exch'
        write(1,1) '  newpath moveto dup Ticksize1 exch lineto stroke'
        write(1,1) '  0 exch moveto LabelLeft} def'
        write(1,1) '/YT2 {Ycoord dup DI exch newpath moveto dup'
        write(1,1) '  DI Ticksize2 sub exch lineto stroke dup 0 exch'
        write(1,1) '  newpath moveto Ticksize2 exch lineto stroke} def'
        write(1,1) '%'
        write(1,1) '% Macro for labeling curves'
        write(1,1) '% Usage: y x label PutLab'
        write(1,1) '/PutLab {gsave 3 copy pop Xcoord exch Ycoord'
        write(1,1) '  translate 1 1 scale ( ) stringwidth pop'
        write(1,1) '  TextHeight -0.5 mul moveto show pop pop'
        write(1,1) '  grestore} def'
        write(1,1) '%'
        write(1,1) '% Macros for plotting curves downward'
        write(1,1) '% Usage: x1 F x2 N x3 N ... xn N D stroke'
        write(1,1) '/F {newpath Xcoord DJ moveto DJ YSCALE add dup} def'
        write(1,1) '/N {Xcoord exch lineto YSCALE add dup} def'
        write(1,1) '/D {pop pop} def'
        write(1,1) '%%EndProlog'
        write(1,1) '%'
        write(1,1) '% shift origin'
        write(1,1) 'gsave I1 J1 translate'

1       format(a)

c Establish geometric limits for plotting
c X-coordinates are as specified.
c Y-coordinates are index numbers
        write(1,10) xrange, -xrange, ntimes
10      format(f10.3, 1x, f10.3, 1x, i6, ' 1 SetLimits gsave ClipBox')

c***********************************************************************
c Draw planet and rings as gray bands
c***********************************************************************

c Draw the rings
        do 300 i = nrings, 1, -1
                if (ring_flags(i)) then
                    write(1,30) ring_grays(i)
                    call RSPK_PlotLimb(ntimes, limb_arcsec, xscaled,
     &                  ring_rads(i)/rplanet)
                end if
300     continue

c Draw the planet
        write(1,30) planet_gray
        call RSPK_PlotLimb(ntimes, limb_arcsec, xscaled, 1.d0)

c Reset to black
        write(1,30) 0.d0

30      format(f4.2, ' setgray')

c***********************************************************************
c Draw moon tracks and plan label locations
c***********************************************************************

c Determine width of a vertical band occupied by moon labels
        irecband = int(BAND_WIDTH/PLOT_HEIGHT/2 * ntimes)

c Initialize the exclusion table (including gaps at top and bottom)
        do 400 i = 1, ntimes
                excluded(i) = .FALSE.
400     continue

        do 401 i = 1, irecband+1
                excluded(i) = .TRUE.
401     continue

        do 402 i = ntimes-irecband, ntimes
                excluded(i) = .TRUE.
402     continue

c Plot and label moons
        write(1,1) 'ClipBox 1.5 setlinewidth'
        do 410 i = 1, nmoons
                call RSPK_PlotMoon(ntimes, i, maxmoons, moon_arcsec,
     &                  limb_arcsec, xrange, xscaled, moon_names(i),
     &                  excluded, irecband)
410     continue

c***********************************************************************
c Finish diagram
c***********************************************************************

        write(1,1) 'grestore DrawBox'

        call RSPK_LabelXAxis(xrange, xscaled, planetstr(1:lplanet))
        call RSPK_LabelYAxis(time1, time2, dt)

c***********************************************************************
c Add caption and title
c***********************************************************************

        write(1,1) 'grestore'

c Write the title string if necessary
        if (title .ne. ' ') then
            write(1,1) 'gsave 4.5 in 10.5 in translate'
            write(1,1) '1.4 1.4 scale'
            call RSPK_TrackString(title(1:LASTNB(title)))
            write(1,1) 'dup stringwidth pop'
            write(1,1) '-0.5 mul TextHeight neg moveto show grestore'
        end if

c Write the caption strings if necessary
        if (ncaptions .gt. 0) then
            write(1,1) 'gsave'
            write(tempstr, '(i4)') nint(align_loc) + 72
            write(1,1) tempstr(1:4) // ' 1.25 in translate'
            write(1,1) '0 TextHeight 0.4 mul translate'
            do 500 i = 1, ncaptions
                write(1,1) '0 TextHeight -1.4 mul translate'
                write(1,1) '0 0 moveto'

                ltext = LASTNB(rcaptions(i))
                call RSPK_TrackString(rcaptions(i)(1:ltext))
                write(1,1) 'show'

                ltext = LASTNB(lcaptions(i))
                call RSPK_TrackString(lcaptions(i)(1:ltext) // '  ')
                write(1,1) 'dup stringwidth pop neg 0 moveto show'
500         continue
            write(1,1) 'grestore'
        end if

c Add the credit info along the bottom
        write(1,1) 'gsave 1 in 0.5 in translate 0.5 0.5 scale'
        write(1,1) '0 0 moveto'

        call FDATE(tempstr)

        write(1,1) '(Generated by the ' // planetstr(1:lplanet) //
     &          ' Tracker Tool, PDS Ring-Moon Systems Node, ' //
     &          tempstr(1:24) // ')'
        write(1,1) 'show grestore'

        write(1,1) 'showpage'
        close(1)

        return
        end

c***********************************************************************
c Subroutine to plot limbs and rings
c***********************************************************************

        subroutine RSPK_PlotLimb(nrecs, limb_arcsec, xscaled, rp)
        integer                 nrecs
        double precision        limb_arcsec(*), rp
        logical                 xscaled

        integer                 sign, irec

c Loop through both halves
        do 200 sign = -1, 1, 2

c For scaled coordinates, area is a rectangle
            if (xscaled) then
                write(1,11) sign * rp,
     &                  'Xcoord dup DJ newpath moveto 0 lineto'

c Otherwise, it can be a little different
            else
                write(1,11) sign * rp * limb_arcsec(1), 'F'

                do 100 irec = 2, nrecs
                        write(1,11) sign * rp * limb_arcsec(irec), 'N'
100             continue
                write(1,10) 'D'
            end if

c Close and fill path
            write(1,10) '0 Xcoord dup 0 lineto DJ lineto closepath fill'

200     continue

        return

10      format(a)
11      format(f8.2, 1x, a)

        end

c***********************************************************************
c Subroutine to plot moon tracks
c***********************************************************************

        subroutine RSPK_PlotMoon(nrecs, imoon, maxmoons, moon_arcsec,
     &                          limb_arcsec, xrange, xscaled, name,
     &                          excluded, irecband)

        integer                 nrecs, imoon, maxmoons, irecband
        double precision        moon_arcsec(maxmoons,*), limb_arcsec(*),
     &                          xrange
        logical                 xscaled, excluded(*)
        character*(*)           name

        integer                 irec, imax, LASTNB
        logical                 first
        double precision        x, xmax
        character*1             char


c Loop through moon positions...
        first = .TRUE.
        xmax = -1.d37
        do 100 irec = 1, nrecs

c Determine next location
                x = moon_arcsec(imoon,irec)
                if (xscaled) x = x / limb_arcsec(irec)

c Plot it
                if (first) then
                        char = 'F'
                        first = .FALSE.
                else
                        char = 'N'
                end if

                write(1,11) x, char

c Keep track of leftmost un-excluded location
                if (x .lt. xrange .and. x .gt. xmax .and.
     &                          .not. excluded(irec)) then
                        imax = irec
                        xmax = x
                end if
100     continue

c Complete track
        write(1,10) 'D stroke'

c If a potential label location was not found, return
        if (xmax .le. -xrange) return

c Write label
        write(1,12) imax, xmax, '('//name(1:LASTNB(name))//') PutLab'

c Exclude future labels from this band
        do 200 irec = imax-irecband, imax+irecband
                excluded(irec) = .TRUE.
200     continue

        return

10      format(a)
11      format(f8.2, 1x, a)
12      format(i4, 1x, f8.2, 1x, a)

        end

c***********************************************************************
c Subroutine to draw x-axis labels and tick marks
c***********************************************************************

        subroutine RSPK_LabelXAxis(xrange, xscaled, planetstr)

        double precision        xrange
        logical                 xscaled
        character*(*)           planetstr

        integer                 i, j, mark, mark1, mark2
        double precision        max_xstep
        character*16            label

        double precision        MIN_MARK1_COUNT
        parameter               (MIN_MARK1_COUNT = 3.d0)

        integer                 NCHOICES
        parameter               (NCHOICES = 9)
        double precision        STEP1(NCHOICES), STEP2(NCHOICES)
        data                    STEP1/ 2, 5, 10, 20, 50, 100, 200,
     &                                  500, 1000 /
        data                    STEP2/ 1, 1,  2,  5, 10,  20,  50,
     &                                  100,  200 /

c Select the mark intervals
        max_xstep = 2.d0 * xrange / MIN_MARK1_COUNT
        do 100 i = NCHOICES, 2, -1
                if (STEP1(i) .le. max_xstep) goto 101
100     continue
101     continue

        mark1 = STEP1(i)
        mark2 = STEP2(i)

c Draw the center mark and label
        write(1,10) '0 (0) XT1'

c Draw the remaining marks and labels...
        do 200 mark = mark2, int(xrange), mark2

c Generate the label string asn skip leading blanks
                if (mod(mark,mark1) .eq. 0) then
                        write(label,'(i6)') mark
                        do 210 j = 1, 5
                                if (label(j:j) .ne. ' ') goto 211
210                     continue
211                     continue
                        write(1,11)  mark, '(' //label(j:6)//') XT1'
                        write(1,11) -mark, '(-'//label(j:6)//') XT1'
                else
                        write(1,11)  mark, 'XT2'
                        write(1,11) -mark, 'XT2'
                end if
200     continue

        if (xscaled) then
                write(1,10) '(' // planetstr // ' radii) Xlabel'
        else
                write(1,10) '(Arcsec) Xlabel'
        end if

        return

10      format(a)
11      format(i4, 1x, a)

        end

c***********************************************************************
c Subroutine to draw y-axis labels and tick marks
c***********************************************************************

        subroutine RSPK_LabelYAxis(tai1, tai2, dt)

        double precision        tai1, tai2, dt

c MIN_MARKS is the smallest number of big ticks allowed along the
c vertical axis.
        double precision        MIN_MARK1_COUNT
        parameter               (MIN_MARK1_COUNT = 4.)

        integer                 i, k1, k2, dutc, dutc_ref, y, m, d, h,
     &                          yprev, mprev, dprev, days
        integer                 mark1_imins,  mark2_imins, tick_imins,
     &                          iticks_per_mark1, iticks_per_mark2,
     &                          iticks_per_day, tick,
     &                          last_mark1_tick, last_mark2_tick
        logical                 qmark1, qmark2, first_mark1
        double precision        max_mark1_mins, secs_per_tick, secs, tai
        character*32            label

        integer                 MINS_PER_HOUR, MINS_PER_DAY
        parameter               (MINS_PER_HOUR = 60)
        parameter               (MINS_PER_DAY  = 60*24)

        integer                 FJUL_DUTCofTAI
        double precision        FJUL_TAIofDUTC

        character*(3)           MONTHNAMES(12)/
     &                                      'JAN', 'FEB', 'MAR',
     &                                      'APR', 'MAY', 'JUN',
     &                                      'JUL', 'AUG', 'SEP',
     &                                      'OCT', 'NOV', 'DEC'/

c***********************************************************************
c Table of choices for axis intervals, in units of minutes.
c STEP1_MINS lists the allowed intervals for big (i.e., labeled) ticks;
c STEP2_MINS lists the intervals for small ticks.
c Big ticks can fall at intervals of 1, 2, 6, or 12 hours or 1, 2, 5,
c 10, or 31 days.
c***********************************************************************

        integer                 NCHOICES
        parameter               (NCHOICES = 9)
        integer                 STEP1_MINS(NCHOICES),
     &                          STEP2_MINS(NCHOICES)
        data                    STEP1_MINS/    60,   120,   360,
     &                                        720,  1440,  2880,
     &                                       7200, 14400, 44640 /
        data                    STEP2_MINS/    15,    30,    60,
     &                                        120,   360,   720,
     &                                       1440,  2880,  7200 /

c Select mark intervals
        max_mark1_mins = (tai2 - tai1) / 60.d0 / MIN_MARK1_COUNT
        do 100 i = NCHOICES, 2, -1
                if (STEP1_MINS(i) .le. max_mark1_mins) goto 101
100     continue
101     continue

        mark1_imins = STEP1_MINS(i)
        mark2_imins = STEP2_MINS(i)

c Locate last needed character in labels (of form 'YYYY-MON-DD XX h')
        k2 = 16
        if (mark1_imins .ge.    MINS_PER_DAY) k2 = 11
        if (mark1_imins .ge. 31*MINS_PER_DAY) k2 = 8

c Determine the reference date.  This is the most recent day
c corresponding to a major mark.
        dutc_ref = FJUL_DUTCofTAI(tai1, secs)

        if (mark1_imins .gt. MINS_PER_DAY) then
                call FJUL_YMDofDUTC(dutc, y, m, d)
                dutc_ref = dutc_ref - mod(d-1, mark1_imins/MINS_PER_DAY)
        end if

c We will loop along the time axis in units of ticks.  A tick is the
c time interval between minor marks, but with an upper limit of one day.
c The upper limit is needed because marks cease to be uniformly spaced
c once they exceed one day; for larger mark intervals, the tick spacing
c becomes dependent on the calendar.  By checking every day, we ensure
c that a mark does not get skipped.

c Determine tick size and interval
        if (mark2_imins .gt. MINS_PER_DAY) then
                tick_imins = MINS_PER_DAY
        else
                tick_imins = mark2_imins
        end if

        iticks_per_day = MINS_PER_DAY / tick_imins
        secs_per_tick = 86400.d0 / iticks_per_day

        iticks_per_mark1 = mark1_imins / tick_imins
        iticks_per_mark2 = mark2_imins / tick_imins

c Initialize counters
        yprev = 0
        mprev = 0
        dprev = 0

        last_mark1_tick = -99999
        last_mark2_tick = -99999

c Loop through ticks
        first_mark1 = .TRUE.
        do 200 tick = 0, 99999

c Determine current date and time relative to reference day
                days = tick / iticks_per_day
                secs = (tick - days * iticks_per_day) * secs_per_tick

                dutc = dutc_ref + days
                call FJUL_YMDofDUTC(dutc, y, m, d)
                h = int(secs / 3600.d0)

c Convert to atomic time and check upper limit
                tai = FJUL_TAIofDUTC(dutc) + secs
                if (tai .gt. tai2) goto 201

c Decide what kind of mark this is, if any.  Also locate the start point
c in the label string (of the form 'YYYY-MON-DD XX h')
                if (y .ne. yprev) then
                        qmark1 = .TRUE.
                        k1 = 1
                else if (m .ne. mprev) then
                        qmark1 = .TRUE.
                        k1 = 6
                else 
                        qmark1 = (tick .ge. last_mark1_tick +
     &                                      iticks_per_mark1)
                        qmark2 = (tick .ge. last_mark2_tick +
     &                                      iticks_per_mark2)

                        if (d .ne. dprev) then
                                k1 = 10
                        else
                                k1 = 13
                        end if
                end if

c Update counters and check lower limit
                yprev = y
                mprev = m
                dprev = d

                if (qmark1) then
                        last_mark1_tick = tick
                        last_mark2_tick = tick
                else if (qmark2) then
                        last_mark2_tick = tick
                end if

                if (tai .lt. tai1) goto 200

c Write tick and/or label if necessary
                if (qmark1) then
                        if (first_mark1) then
                                k1 = 1
                                first_mark1 = .FALSE.
                        end if

                        write(label,10) y, MONTHNAMES(m), d, h
10                      format(i4, '-', a3, '-', i2.2, 1x, i2, 'h')
                        write(1,11) (tai - tai1)/dt + 1.d0,
     &                          '(' // label(k1:k2) // ') YT1'
                        last_mark1_tick = tick
                        last_mark2_tick = tick
                else if (qmark2) then
                        write(1,11) (tai - tai1)/dt + 1.d0, 'YT2'
                        last_mark2_tick = tick
                end if
11              format(f7.2, 1x, a)

200     continue
201     continue

        return
        end

c***********************************************************************
c subroutine RSPK_TrackString(string)
c
c This internal subroutine writes a Postscript-format string to the
c output file, properly parenthesized.  String lengths are limited.
c
c Input:
c       string          character string to output.
c***********************************************************************

        subroutine RSPK_TrackString(string)
        character*(*)           string

        integer                 i, ltemp
        character*256           temp

        temp = string
        ltemp = len(string)
        do 100 i = ltemp, 1, -1
                if (temp(i:i) .eq. '(' .or. temp(i:i) .eq. ')') then
                        temp(i:) = '\' // temp(i:)
                        ltemp = min(ltemp + 1, len(temp))
                end if
100     continue

        write(1,'(a)') '(' // temp(1:ltemp) // ')'

        return
        end

c***********************************************************************
