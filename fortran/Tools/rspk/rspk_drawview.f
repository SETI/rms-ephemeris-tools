c*******************************************************************************
c$ Component_name:
c       RSPK_DrawView
c$ Abstract:
c       Generates a Postscript file showing the appearance of a planetary system
c       at a specified time.  This variant of RPSK_DrawView allows for vertical
c       offsets to rings.
c$ Keywords:
c       SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_DrawView(obs_time, fov, center_ra, center_dec,
c                       blank_disks, prime_pts,
c               nmoons, moon_flags, moon_ids, moon_names, moon_labelpts,
c                       moon_diampts,
c               nrings, ring_flags, ring_rads, ring_elevs, ring_eccs, ring_incs,
c                       ring_peris, ring_nodes, ring_offsets,
c                       ring_opaqs, ring_dashed, ring_method,
c               narcs, arc_flags, arc_rings, arc_minlons, arc_maxlons,
c                       arc_width,
c               nstars, star_ras, star_decs, star_names, star_labels,
c                       star_diampts,
c               title, ncaptions, lcaptions, rcaptions, align_loc,
c               filename)
c
c       double precision        obs_time, fov, center_ra, center_dec,
c                               prime_pts
c       logical                 blank_disks
c
c       integer                 nmoons, moon_ids(*)
c       logical                 moon_flags(*)
c       character*(*)           moon_names(*)
c       double precision        moon_labelpts, moon_diampts
c
c       integer                 nrings, ring_method
c       logical                 ring_flags(*), ring_opaqs(*),
c                               ring_dashed(*)
c       double precision        ring_rads(*), ring_elevs(*), ring_eccs(*), 
c                               ring_incs(*), ring_peris(*), ring_nodes(*),
c                               ring_offsets(3,*)
c
c       integer                 narcs, arc_rings(*)
c       logical                 arc_flags(*)
c       double precision        arc_minlons(*), arc_maxlons(*), arc_width
c
c       integer                 nstars
c       double precision        star_ras(*), star_decs(*)
c       character*(*)           star_names(*)
c       logical                 star_labels
c       double precision        star_diampts
c
c       integer                 ncaptions
c       character*(*)           title, lcaptions(*), rcaptions(*)
c       double precision        align_loc
c
c       character*(*)           filename
c$ Inputs:
c       obs_time                ephemeris time of the observation.
c       fov                     field of view in radians.
c       center_ra, center_dec   coordinates of center of field of view.
c       blank_disks             .TRUE. to leave disks blank; .FALSE. to
c                               include meridian lines.
c       prime_pts               weight in points for the prime meridian and
c                               anti-meridian.
c
c       nmoons                  number of moons in list.
c       moon_flags(*)           .TRUE. to include moon in plot; .FALSE.
c                               otherwise.
c       moon_ids(*)             body IDs of moons based on SPICE toolkit.
c       moon_names(*)           name of each moon, for optional labels.
c       moon_labelpts           size of moon labels (points); 0. to disable.
c       moon_diampts            minimum diameter of a plotted disk (points).
c
c       nrings                  number of rings in list.  Rings must be in order
c                               of increasing radius.
c       ring_flags(*)           .TRUE. to include ring in plot; .FALSE.
c                               otherwise.
c       ring_rads(*)            semimajor axis of each ring (km).
c       ring_elevs(*)           vertical offset of each ring (km north).
c       ring_eccs(*)            eccentricity of each ring.
c       ring_incs(*)            inclination of each ring (radians).
c       ring_peris(*)           pericenter longitude of each ring (radians, from
c                               equator's J2000 ascending node).
c       ring_nodes(*)           ascending node longitude of each ring (radians,
c                               from equator's J2000 ascending node).
c       ring_offsets(3,*)       vector offset of ring center from the middle
c                               of the planet, in J2000 coordinates.
c       ring_opaqs(*)           .TRUE. if interior ring is opaque; .FALSE. if it
c                               is transparent.
c       ring_dashed(*)          .TRUE. to plot ring as a dashed line; .FALSE.
c                               to plot it as solid. A dashed line is used for
c                               an optically thin ring.
c       ring_method             0  objects behind all rings are visible; rings
c                                  do not cast shadows.
c                               1  objects obscured by any ring interior to the
c                                  outermost opaque ring are gray; rings cast
c                                  shadows.
c                               2  objects obscured by any ring interior to the
c                                  outermost opaque ring are invisible; rings
c                                  cast shadows.
c                               Option 1 is the most realistic but the resultant
c                               Postscript file twice as large.
c
c       narcs                   number of ring arcs in list.
c       arc_flags(*)            .TRUE. to include arc in plot; .FALSE.
c                               otherwise.
c       arc_rings(*)            index of ring (1--nrings) where each arc falls.
c       arc_minlons(*)          lower longitude limit of each arc (radians, from
c                               equator's J2000 ascending node).
c       arc_maxlons(*)          upper longitude limit of each arc (radians, from
c                               equator's J2000 ascending node).  If the arc
c                               crosses the prime meridian, then
c                               arc_minlon(j) > arc_maxlon(j).
c       arc_width               width of plotted arc (points).
c
c       nstars                  number of stars in list.
c       star_ras(*)             right ascensions (rad).
c       star_decs(*)            declinations (rad).
c       star_names(*)           names of stars.
c       star_labels             .TRUE. to label stars.  Stars will be labeled
c                               at the same point size as moons.
c       star_diampts            plotted diameter of stars (points).
c
c       title                   title string to appear above diagram.
c       ncaptions               number of captions lines.
c       lcaptions(*)            left part of each caption line.
c       rcaptions(*)            right part of each caption line.
c       align_loc               alignment as distance from left edge (points).
c
c       filename                output Postscript filename.
c$ Outputs:
c       none
c$ Returns:
c       none
c$ Side_effects:
c       A Postscript file of the specified name is created.
c$ Detailed_description:
c       This subroutine generates a Postscript file showing the appearance of
c       a planetary system at a specified time.  All bodies are rendered with
c       terminators and shadows as appropriate.  This variant of RPSK_DrawView
c       allows for vertical offsets to rings.
c
c       The planet and moons are modeled as triaxial ellipsoids, and are drawn
c       with latitude and longitude contours at 15 degree intervals.
c       Illuminated regions are indicated with black lines; unilluminated
c       regions are shown as light gray.  In addition, terminators are drawn in
c       black.  Penumbral shadowing is not indicated.  A minimum size in points
c       places a lower limit on the drawn size of a moon, ensuring that
c       unresolved moons remain visible.  Each moon may be indicated by a text
c       label.  When the blank_disks parameter is .TRUE., latitude and longitude
c       contours are eliminated.
c
c       A set of (possibly eccentric or inclined) ring boundaries can also be
c       drawn.  Each ring may be either opaque or transparent, but only the
c       outermost opaque ring is significant.  Three methods for plotting rings
c       are supported.  When ring_method=0, opacity is ignored and all the rings
c       are effectively transparent; they do not cast shadows.  When ring_method
c       =2, the outermost opaque ring is treated as opaque all the way down to
c       the planet.  It does cast a shadow.  When ring_method=1, objects
c       obscured by the outermost opaque ring are rendered in gray.  Rings
c       themselves are bounded in black if the lit side is visible and gray if
c       the unlit side is visible or where a section of the ring is shadowed.
c       Rings may be drawn using either solid or dashed lines.  A set of ring
c       arcs can also be drawn; these are indicated by a heavier solid line.
c
c       The user may also specify an arbitrary set of stars.  Any of those stars
c       that fall inside the field of view will be plotted as a plus.  If moon
c       labeling is turned on, then stars will also be labeled by name at the
c       same font size.
c
c       The user may also specify a title and a set of captions.  The title
c       appears above the diagram and centered.  Captions appear below the
c       diagram.  Each caption takes the form of a left part and a right part;
c       the right part is aligned (left-justified) at a user-specified distance
c       from the left edge of the diagram; the left part appears right-justified
c       beginning two spaces to the left of the right part.
c
c       The picture is oriented with J2000 declination increasing upward and
c       with right ascension increasing to the left.  The frame has uniformly-
c       spaced tick marks.  The declination axis is labeled in degrees, minutes
c       and seconds; the right ascension axis is labeled in hours, minutes and
c       seconds.
c
c       The image rendering is carried out by the NAIF toolkit "Euclid", which
c       in turn calls the "Escher" toolkit for plotting lines.  The Escher
c       toolkit has been adapted slightly for this purpose.  The program is
c       hard-wired for Postscript output.
c$ External_references:
c       SPICE toolkit, Euclid toolkit, Escher toolkit, RSPK toolkit.
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
c       1.0: January 1999
c       1.1: April 2003
c       1.2: August 2005
c       1.3: June 2021
c$ Change_history:
c       1.0: Adapted from RSPK_DrawView(), v. 2.1, with the blank_disks, stars,
c            and vertically displaced ring options added.
c       1.1: Modified for compatibility with Absoft Fortran for Macintosh.
c       1.2: Merged features from RSPK_DrawViewJ and RSPK_DrawViewM to better
c            handle offset and optically thin rings.
c       1.3: Added prime_pts option for weighting the equator and prime
c            meridian.
c*******************************************************************************

        subroutine RSPK_DrawView(obs_time, fov, center_ra, center_dec,
     &                  blank_disks, prime_pts,
     &          nmoons, moon_flags, moon_ids, moon_names, moon_labelpts,
     &                  moon_diampts,
     &          nrings, ring_flags, ring_rads, ring_elevs, ring_eccs,
     &                  ring_incs, ring_peris, ring_nodes, ring_offsets,
     &                  ring_opaqs, ring_dashed, ring_method,
     &          narcs, arc_flags, arc_rings, arc_minlons, arc_maxlons,
     &                  arc_width,
     &          nstars, star_ras, star_decs, star_names, star_labels,
     &                  star_diampts,
     &          title, ncaptions, lcaptions, rcaptions, align_loc,
     &          filename)

        implicit                none
        double precision        obs_time, fov, center_ra, center_dec,
     &                          prime_pts
        logical                 blank_disks

        integer                 nmoons, moon_ids(*)
        logical                 moon_flags(*)
        character*(*)           moon_names(*)
        double precision        moon_labelpts, moon_diampts

        integer                 nrings, ring_method
        logical                 ring_flags(*), ring_opaqs(*),
     &                          ring_dashed(*)
        double precision        ring_rads(*), ring_elevs(*),
     &                          ring_eccs(*), ring_incs(*),
     &                          ring_peris(*), ring_nodes(*),
     &                          ring_offsets(3,*)
        integer                 TRANSPARENT_METHOD,
     &                          SEMI_TRANSPARENT_METHOD,
     &                          OPAQUE_METHOD
        parameter               (TRANSPARENT_METHOD = 0)
        parameter               (SEMI_TRANSPARENT_METHOD = 1)
        parameter               (OPAQUE_METHOD = 2)

        integer                 narcs, arc_rings(*)
        logical                 arc_flags(*)
        double precision        arc_minlons(*), arc_maxlons(*),
     &                          arc_width

        integer                 nstars
        double precision        star_ras(*), star_decs(*), star_diampts
        character*(*)           star_names(*)
        logical                 star_labels

        integer                 ncaptions
        character*(*)           title, lcaptions(*), rcaptions(*)
        double precision        align_loc

        character*(*)           filename

c******************************************************
c Parameters describing figure contents
c******************************************************

c System body id's
        integer                 EARTH_ID, SUN_ID
        parameter               (EARTH_ID  = 399)
        parameter               (SUN_ID    =  10)

c Effective ring thickness in km
        double precision        RING_THICKNESS
        parameter               (RING_THICKNESS = 1.d0)

c Upper limit on the minimum diameter of a moon in points
        double precision        MAX_MINSIZE
        parameter               (MAX_MINSIZE = 10.d0)

c Upper limit on the full width of an arc in points
        double precision        MAX_ARCPTS
        parameter               (MAX_ARCPTS = 10.d0)

c Radial width of the loops comprising an arc, in km
        double precision        LOOP_WIDTH
        parameter               (LOOP_WIDTH = 1.d0)

c Maximum longitudinal length of loops in radians
        double precision        LOOP_DLON
        parameter               (LOOP_DLON = 0.01d0)

c Number of meridians and latitude lines on the planet and moons
        integer                 PLANET_MERIDS, PLANET_LATS
        parameter               (PLANET_MERIDS = 12, PLANET_LATS = 11)

        integer                 MOON_MERIDS, MOON_LATS
        parameter               (MOON_MERIDS = 12, MOON_LATS = 11)

c Limits on number of figure components
        integer                 MAX_NMOONS, MAX_NRINGS, MAX_NLOOPS,
     &                          MAX_NBODIES
        parameter               (MAX_NMOONS = 40)
        parameter               (MAX_NRINGS = 40)
        parameter               (MAX_NLOOPS = 80)
        parameter               (MAX_NBODIES = 2+MAX_NMOONS+MAX_NRINGS)

c Planet names
        character*8             planet_names(4:8)/ 'Mars',
     &                                  'Jupiter', 'Saturn',
     &                                  'Uranus', 'Neptune' /

c Star font parameters
        integer                 STARFONTSIZE
        parameter               (STARFONTSIZE = 2)
        double precision        STARFONT(2,2,STARFONTSIZE)
     &                                  / 0,-1, 0,+1, -1,0, +1,0 /

c******************************************************
c Euclid parameters
c******************************************************

c Only Postscript output is supported
        integer                 DEVICE
        parameter               (DEVICE = 7)

c The vertical limits are inverted here to compensate for the inversion
c performed by Euclid.  These values produce a 7-inch square diagram
c with a 0.5 inch border at right, 1 inch at left, 0.75 inches above
c and 2.75 inches below.
        double precision        H1, H2, V1, V2
        parameter               (H1 = 0.066666667d0, H2 = 1.000000000d0)
        parameter               (V1 = 0.988888889d0, V2 = 0.055555556d0)

c The number of points in the full seven-inch field of view
        double precision        FOV_PTS
        parameter               (FOV_PTS = 7.d0 * 72.d0)

c Line types
        integer                 LIT_LINE, DARK_LINE, SHADOW_LINE,
     &                          AXIS_LINE, NO_LINE, STAR_LINE, term_line
        parameter               (LIT_LINE  =  1)
        parameter               (DARK_LINE =  7)
c       parameter               (TERM_LINE =  7)
        parameter               (AXIS_LINE =  1)
        parameter               (NO_LINE   = -1)
        parameter               (STAR_LINE =  1)
        parameter               (SHADOW_LINE = 10)

        double precision        STAR_WIDTH
        parameter               (STAR_WIDTH = 1.5d0)

c******************************************************
c Subroutine internal variables
c******************************************************

        include                 'rspk_common.inc'

        integer                 i, ltext, nradii, nbodies, lpname
        double precision        delta, radii(3), tempvec(3), vec1(3),
     &                          vec2(3), dt, tempmat(3,3), los(3)
        character*24            tempstr
        character*8             pname

        double precision        planet_dt, planet_time, obs_pv(6),
     &                          planet_dpv(6), planet_pv(6),
     &                          planet_mat(3,3)

        double precision        sun_dpv(6), sun_loc(3), sun_rad

        double precision        cmatrix(3,3), col1(3), col2(3), col3(3)
        equivalence             (cmatrix(1,1), col1(1))
        equivalence             (cmatrix(1,2), col2(1))
        equivalence             (cmatrix(1,3), col3(1))

        double precision        body_locs(3,MAX_NBODIES),
     &                          body_axes(3,3,MAX_NBODIES),
     &                          body_pts(MAX_NBODIES),
     &                          body_dist(MAX_NBODIES),
     &                          body_los(3,MAX_NBODIES)
        character*20            body_names(MAX_NBODIES)

        integer                 imoon, use_nmoons, moon_id
        double precision        moon_dpv(6)

        integer                 iring, use_nrings, last_opaq
        double precision        pole(3), ascnode(3), offset(3),
     &                          rad, ecc, ringnode(3), ringpole(3),
     &                          peri(3), dot1, dot2
        double precision        ring_locs(3,MAX_NRINGS),
     &                          ring_axes1(3,MAX_NRINGS),
     &                          ring_axes2(3,MAX_NRINGS),
     &                          ring_axes3(3,MAX_NRINGS)
        logical                 ring_dark(MAX_NRINGS)

        integer                 iarc, nsteps, nloops
        double precision        lon, lon1, lon2, dlon
        double precision        loop_locs(3,MAX_NLOOPS),
     &                          loop_axes1(3,MAX_NLOOPS),
     &                          loop_axes2(3,MAX_NLOOPS)
        integer                 loop_ring(MAX_NLOOPS)

        integer                 ibody
        double precision        use_diampts, use_arcpts
        integer                 pmerids, plats, mmerids, mlats

        integer                 LASTNB
        double precision        HALFPI, TWOPI, VNORM, VDOT
        logical                 BODFND, OPSGND

c***********************************************************************
c Initialize the Postscript file
c***********************************************************************

        pname = planet_names(planet_num)
        lpname = LASTNB(pname)

        call ESFILE(filename, pname(1:lpname) //
     &      ' Viewer, PDS Ring-Moon Systems Node',
     &      'Helvetica')

c This call actually opens the file and writes the Postscript header
        call ESDR07(0, 0)

c Define "MyFont", which includes "\260" for the degree symbol
        call ESWRIT('/MakeDegreeFont {')
        call ESWRIT('findfont dup /CharStrings get /degree known {')
        call ESWRIT('dup length dict /newdict exch def {')
        call ESWRIT('1 index /FID ne { newdict 3 1 roll put }')
        call ESWRIT('{ pop pop } ifelse } forall')
        call ESWRIT('newdict /Encoding get dup length array copy')
        call ESWRIT('newdict exch /Encoding exch put')
        call ESWRIT('newdict /CharStrings get /degree known {')
        call ESWRIT('newdict /Encoding get 8#260 /degree put } if')
        call ESWRIT('newdict true } { pop false } ifelse } def')
        call ESWRIT('/MyFont /Helvetica ' //
     &              ' MakeDegreeFont { definefont pop } if')

c Define the axis labeling macros
        call ESWRIT('/unscale {10 10 scale} def')

        call ESWRIT('/TextHeight {11} def')
        call ESWRIT('/MyFont findfont TextHeight scalefont setfont')

        call ESWRIT('/LabelBelow {gsave currentpoint translate')
        call ESWRIT('unscale')
        call ESWRIT('dup stringwidth pop -0.5 mul TextHeight -1.3 mul')
        call ESWRIT('moveto show grestore} def')

        call ESWRIT('/LabelLeft {gsave currentpoint translate')
        call ESWRIT('unscale 90 rotate')
        call ESWRIT('dup stringwidth pop -0.5 mul TextHeight 0.3 mul')
        call ESWRIT('moveto show grestore} def')

c Define the moon labeling macro if necessary
        if (moon_labelpts .gt. 0.d0) then
            call ESWRIT('/LabelBody {gsave currentpoint translate')
            call ESWRIT('unscale')
            write(tempstr, '(f5.3)') min(moon_labelpts/12.d0, 2.d0)
            call ESWRIT(tempstr(1:5) // ' ' // tempstr(1:5) // ' scale')
            call ESWRIT('TextHeight 0.2 mul dup')
            call ESWRIT('moveto show grestore} def')
        end if

c Mark end of prolog
        call ESWRIT('%%EndProlog')
        call ESWRIT('%')

c Write the title string if necessary
        if (title .ne. ' ') then
            call ESWRIT('gsave unscale 324 756 translate 1.4 1.4 scale')
            ltext = LASTNB(title)
            call RSPK_WriteString(title(1:ltext))
            call ESWRIT('dup stringwidth pop')
            call ESWRIT('-0.5 mul TextHeight neg moveto show grestore')
        end if

c Write the caption strings if necessary
        if (ncaptions .gt. 0) then
            call ESWRIT('gsave unscale')
            write(tempstr, '(i4)') nint(align_loc) + 72
            call ESWRIT(tempstr(1:4) // ' 162 translate')
            call ESWRIT('0 TextHeight 0.4 mul translate')
            do 50 i = 1, ncaptions
                call ESWRIT('0 TextHeight -1.25 mul translate')
                call ESWRIT('0 0 moveto')
                ltext = LASTNB(rcaptions(i))
                call RSPK_WriteString(rcaptions(i)(1:ltext))
                call ESWRIT('show')

                ltext = LASTNB(lcaptions(i))
                call RSPK_WriteString(lcaptions(i)(1:ltext) // '  ')
                call ESWRIT('dup stringwidth pop neg 0 moveto show')
50          continue
            call ESWRIT('grestore')
        end if

c Add the credit info along the bottom
        call ESWRIT('gsave unscale 72 36 translate 0.5 0.5 scale')
        call ESWRIT('0 0 moveto')
        call FDATE(tempstr)
        call ESWRIT('(Generated by the ' // pname(1:lpname) //
     &          ' Viewer Tool, PDS Ring-Moon Systems Node, ' //
     &          tempstr(1:24) // ')')
        call ESWRIT('show grestore')

c Label the axes
        call ESWRIT('gsave unscale')
        call ESWRIT('324 180 translate 1.2 1.2 scale')
        call ESWRIT('(Right Ascension (h m s)) dup stringwidth pop')
        call ESWRIT('-0.5 mul 0 moveto show grestore')

        call ESWRIT('gsave unscale')
        call ESWRIT('36 450 translate 1.2 1.2 scale 90 rotate')
        call ESWRIT('(Declination (d m s)) dup stringwidth pop')
        call ESWRIT('-0.5 mul TextHeight neg moveto show grestore')

c***********************************************************************
c Initialize the camera
c***********************************************************************

        call EUINIT

        delta = tan(fov/2.d0)
        call EUVIEW(DEVICE, H1, H2, V1, V2,
     &                  -delta, delta, -delta, delta)

c***********************************************************************
c Initialize the meridian and latitude count
c***********************************************************************

        if (blank_disks) then
                pmerids = 0
                plats   = 0
                mmerids = 0
                mlats   = 0
                term_line = LIT_LINE
        else
                pmerids = PLANET_MERIDS
                plats   = PLANET_LATS
                mmerids = MOON_MERIDS
                mlats   = MOON_LATS
                term_line = DARK_LINE
        end if

c***********************************************************************
c Set up observer and planet geometry
c***********************************************************************

c Calculate the instantaneous position of the observer
        call RSPK_ObsLoc(obs_time, obs_pv)

c Calculate the instantaneous state of the planet
        call SPKAPP(planet_id, obs_time, 'J2000', obs_pv, 'LT',
     &          planet_dpv, planet_dt)
        planet_time = obs_time - planet_dt
        call SPKSSB(planet_id, planet_time, 'J2000', planet_pv)

c Rotation matrix from J2000 to planet coordinates
        call BODMAT(planet_id, obs_time-planet_dt, planet_mat)

c***********************************************************************
c Calculate the apparent illumination of planet
c***********************************************************************

c Include stellar aberration in this calculation
        call SPKAPP(SUN_ID, planet_time, 'J2000', planet_pv, 'LT+S',
     &          sun_dpv, dt)
        call VADD(planet_pv(1), sun_dpv(1), sun_loc)

c Get the Sun radius
        call BODVAR(SUN_ID, 'RADII', nradii, radii)
        sun_rad = radii(1)

c***********************************************************************
c Generate the camera C-matrix
c***********************************************************************

c The camera z-axis is as passed to the subroutine
        call RADREC(1.d0, center_ra, center_dec, col3)

c The camera y-axis is the perpendicular projection of the J2000 z-axis
c (Up on the plot corresponds to increasing declination).
        call VPACK(0.d0, 0.d0, 1.d0, tempvec)
        call VPERP(tempvec, col3, col2)
        call VHAT(col2, col2)

c The camera x-axis is perpendicular in the right-handed sense
c (Left on the plot corresponds to increasing right ascension).
        call VCRSS(col2, col3, col1)

c (Note that vectors col1, col2, and col3 are equivalenced to the
c corresponding columns of cmatrix).

c***********************************************************************
c Put planet into the body list
c***********************************************************************

        nbodies = 1

        call VADD(obs_pv, planet_dpv, body_locs(1,nbodies))

c Note that the matrix returned by BODMAT converts from J2000 to the 
c body equator/prime meridian frame.  Its transpose does the reverse, 
c which means that its three columns are the body principal axes in
c J2000 coordinates.
        call XPOSE(planet_mat, body_axes(1,1,nbodies))

c Scale each axis by the planet's radius.
        call BODVAR(planet_id, 'RADII', nradii, radii)

        do 100 i = 1, 3
                call VSCL(radii(i), body_axes(1,i,nbodies),
     &                              body_axes(1,i,nbodies))
100     continue

c Never label the planet
        body_names(nbodies) = ' '

c***********************************************************************
c Add a small body at middle of field of view
c This seems to be needed to correct a bug in the toolkit that makes
c the ring lighting wrong if no bodies fall inside the field of view.
c***********************************************************************

        nbodies = 2

c Rescale the body to 1 km radius
        do 110 i = 1, 3
                call VHAT(body_axes(1,i,1), body_axes(1,i,nbodies))
110     continue

c Locate the body along the optic axis, twice as far away
        call VSUB(body_locs(1,1), obs_pv, tempvec)
        call VSCL(2.d0 * VNORM(tempvec), col3, tempvec)
        call VADD(obs_pv, tempvec, body_locs(1,nbodies))

        body_names(nbodies) = ' '

c***********************************************************************
c Put each moon into the body list
c***********************************************************************

c Ignore moons beyond the dimensioned limit
        use_nmoons = MIN(nmoons, MAX_NMOONS)

c Loop through moons...
        do 201 imoon = 1, use_nmoons
                if (.not. moon_flags(imoon)) goto 201
                nbodies = nbodies + 1
                moon_id = moon_ids(imoon)

c Calculate the body position
                call RSPK_SPKAPP(moon_id, obs_time, 'J2000',
     &                  obs_pv, 'LT', moon_dpv, dt)
                call VADD(obs_pv, moon_dpv, body_locs(1,nbodies))

c Save line-of-sight for optional moon label
                call VEQU(moon_dpv(1), body_los(1,nbodies))

c Get body axes and orientation
c If we have no model for the body pole, use planet instead.  (Note:
c Hyperion falls into this category)
                if (BODFND(moon_id, 'POLE_RA')) then
                        call RSPK_BODMAT(moon_id, obs_time-dt, tempmat)
                else
                        call MEQU(planet_mat, tempmat)
                end if

c See previous call to XPOSE for an explanation here
                call XPOSE(tempmat, body_axes(1,1,nbodies))

c Scale each axis by the body's radius.
                call BODVAR(moon_id, 'RADII', nradii, radii)

                do 200 i = 1, 3
                        call VSCL(radii(i), body_axes(1,i,nbodies),
     &                                      body_axes(1,i,nbodies))
200             continue

c Save the projected diameter of the moon in points
                body_pts(nbodies) = 2.d0*radii(1) * FOV_PTS /
     &                          (VNORM(moon_dpv(1)) * fov)

c Save the name of the moon
                body_names(nbodies) = moon_names(imoon)

c Save the distance from the planet (since we do not allow moons to
c be obscured by exterior rings.
                call VSUB(body_locs(1,nbodies), body_locs(1,1), tempvec)
                body_dist(nbodies) = VNORM(tempvec)
201     continue

c***********************************************************************
c Determine ring shapes and arc loop properties
c***********************************************************************

c Ignore rings beyond the dimensioned limit
        use_nrings = MIN(nrings, MAX_NRINGS)

c Save the planet pole vector (reversed for Uranus)
        call VHAT(body_axes(1,3,1), pole)
        if (planet_num .eq. 7) call VMINUS(pole, pole)

c Locate the pole and the equatorial plane's J2000 ascending node.
        call VPACK(0.d0, 0.d0, 1.d0, tempvec)
        call VCRSS(tempvec, pole, ascnode)

c Extrapolate planet's relative location at observer-received time
        call VSCL(planet_dt, planet_pv(4), offset)

c Loop through rings, saving ellipsoidal shape models and illuminations
        last_opaq = 0
        nloops = 0
        do 300 iring = 1, use_nrings
                if (.not. ring_flags(iring)) goto 300

                rad = ring_rads(iring)
                ecc = ring_eccs(iring)
                
c Save index of outermost opaque ring
                if (ring_opaqs(iring)) last_opaq = iring

c Locate the pole and ascending node of a given ring WRT to equator
                call VROTV(ascnode, pole, ring_nodes(iring), ringnode)
                call VROTV(pole, ringnode, ring_incs(iring), ringpole) 
                call VHAT(ringpole, ringpole)

c Generate ring origin and axis vectors
                call VSCL(RING_THICKNESS, ringpole, ring_axes3(1,iring))

                call VROTV(ringnode, ringpole,
     &                  ring_peris(iring) - ring_nodes(iring), peri)
                call VHAT(peri, peri)
                call VSCL(rad, peri, ring_axes1(1,iring))

                call VROTV(peri, ringpole, HALFPI(0.d0), tempvec)
                call VSCL(rad * sqrt(1.d0 - ecc**2), tempvec,
     &                          ring_axes2(1,iring))

                call VSCL(-ecc, ring_axes1(1,iring), tempvec)
                call VADD(tempvec, body_locs(1,1), ring_locs(1,iring))

                call VSCL(ring_elevs(iring), pole, tempvec)
                call VADD(tempvec, ring_locs(1,iring),
     &                             ring_locs(1,iring))

                call VADD(ring_locs(1,iring), ring_offsets(1,iring),
     &                             ring_locs(1,iring))

c Find observer photon direction relative to ring pole.  (Only the sign
c of the dot product matters).
                call VSUB(ring_locs(1,iring), obs_pv(1), tempvec)
                call VADD(tempvec, offset, tempvec)
                dot1 = -VDOT(ringpole, tempvec)

c Find Sun photon direction relative to planet pole
                call VHAT(sun_dpv(1), tempvec)
                dot2 = VDOT(ringpole, tempvec)

c If observer and Sun are on opposite sides of the equator, and the Sun
c is entirely on one side of the ring plane, then the rings are dark.
c However, dashed (i.e. faint) rings are never marked dark.
                if (ring_dashed(iring)) then
                    ring_dark(iring) = .FALSE.
                else
                    ring_dark(iring) = OPSGND(dot1, dot2) .and.
     &                  (abs(dot2) .gt. sun_rad/VNORM(sun_dpv(1)))
                end if

c Locate points along any relevant arcs
                do 311 iarc = 1, narcs
                    if (arc_rings(iarc) .ne. iring) goto 311
                    if (.not. arc_flags(iarc)) goto 311

c Determine mean anomaly range
                    lon1 = arc_minlons(iarc) - ring_peris(iring)
                    lon2 = arc_maxlons(iarc) - ring_peris(iring)
                    if (lon2 .lt. lon1) lon2 = lon2 + TWOPI(0.d0)

c Break arc up into discrete longitudinal steps
                    nsteps = max((lon2 - lon1) / LOOP_DLON, 1.d0)
                    dlon = (lon2 - lon1) / nsteps

c For each step...
                    lon = lon1 - dlon
                    do 310 i = 1, nsteps
                        lon = lon + dlon

c Increment loop counter
                        nloops = min(nloops+1, MAX_NLOOPS)

c Find vectors from ring center to longitudinal limits of loop
c (This gives longitudinal errors of order eccentricity)
                        call VLCOM(cos(lon), ring_axes1(1,iring),
     &                             sin(lon), ring_axes2(1,iring),
     &                             vec1)
                        call VLCOM(cos(lon+dlon), ring_axes1(1,iring),
     &                             sin(lon+dlon), ring_axes2(1,iring),
     &                             vec2)

c Generate center and axis vectors
                        call VLCOM(0.5d0, vec1, 0.5d0, vec2, tempvec)
                        call VSUB(vec1, tempvec, loop_axes1(1,nloops))
                        call VHAT(tempvec, loop_axes2(1,nloops))
                        call VSCL(LOOP_WIDTH, loop_axes2(1,nloops), 
     &                          loop_axes2(1,nloops))
                        call VADD(tempvec, ring_locs(1,iring),
     &                          loop_locs(1,nloops))

c Save ring index associated with loop
                        loop_ring(nloops) = iring
310                 continue
311             continue

300     continue

c***********************************************************************
c Case 0: TRANSPARENT_METHOD
c***********************************************************************

c Set the minimum moon size in points
        use_diampts = min(MAX_MINSIZE, moon_diampts)

c Set the arc width in points
        use_arcpts = min(MAX_ARCPTS, arc_width)

        if (ring_method .eq. TRANSPARENT_METHOD .or.
     &      last_opaq .eq. 0) then

c Define the picture geometry without any rings
            call EUGEOM(1, sun_loc, sun_rad, obs_pv(1), cmatrix,
     &          nbodies, body_locs, body_axes)

c Draw the planet and its moons, erasing names for invisible bodies
             call RSPK_DrawBodies(nbodies, body_pts, body_names,
     &          body_dist, use_diampts, .TRUE., 0.d0,
     &          pmerids, plats, mmerids, mlats,
     &          LIT_LINE, DARK_LINE, term_line,
     &          LIT_LINE, DARK_LINE, term_line, prime_pts)

c Draw the rings
            call RSPK_DrawRings(1, use_nrings, ring_flags,
     &          ring_locs, ring_axes1, ring_axes2, ring_dark,
     &          ring_dashed,
     &          nloops, loop_locs, loop_axes1, loop_axes2, loop_ring,
     &          use_arcpts, LIT_LINE, DARK_LINE, SHADOW_LINE, term_line)

c***********************************************************************
c Case 1: SEMI_TRANSPARENT_METHOD
c***********************************************************************

        else if (ring_method .eq. SEMI_TRANSPARENT_METHOD) then

c Define the picture geometry without any rings
            call EUGEOM(1, sun_loc, sun_rad, obs_pv(1), cmatrix,
     &          nbodies, body_locs, body_axes)

c Draw the planet and its moons as unlit, erasing names of invisible
c bodies.  However, use normal lighting for moons interior to the ring.
            call RSPK_DrawBodies(nbodies, body_pts, body_names,
     &          body_dist, use_diampts, .TRUE., ring_rads(last_opaq),
     &          pmerids, plats, mmerids, mlats,
     &          DARK_LINE, DARK_LINE, DARK_LINE,
     &          LIT_LINE,  DARK_LINE, term_line, prime_pts)

c Re-define the geometry with the outermost opaque ring as a very flat
c ellipsoid
            call VEQU(ring_locs(1,last_opaq),  body_locs(1,nbodies+1))
            call VEQU(ring_axes1(1,last_opaq), body_axes(1,1,nbodies+1))
            call VEQU(ring_axes2(1,last_opaq), body_axes(1,2,nbodies+1))
            call VEQU(ring_axes3(1,last_opaq), body_axes(1,3,nbodies+1))

            call EUGEOM(1, sun_loc, sun_rad, obs_pv(1), cmatrix,
     &                  nbodies+1, body_locs, body_axes)

c Re-draw the planet and its moons as lit, but do not draw moons
c interior to the ring
            call RSPK_DrawBodies(nbodies, body_pts, body_names,
     &          body_dist, use_diampts, .FALSE., ring_rads(last_opaq),
     &          pmerids, plats, mmerids, mlats,
     &          LIT_LINE, DARK_LINE, term_line,
     &          NO_LINE,  NO_LINE,   NO_LINE, prime_pts)

c Draw the opaque ring invisibly
            call EUBODY(nbodies+1, 0, 0, 1, NO_LINE, NO_LINE, NO_LINE)

c Draw the exterior rings
            call RSPK_DrawRings(last_opaq+1, use_nrings, ring_flags,
     &          ring_locs, ring_axes1, ring_axes2, ring_dark,
     &          ring_dashed,
     &          nloops, loop_locs, loop_axes1, loop_axes2, loop_ring,
     &          use_arcpts, LIT_LINE, DARK_LINE, SHADOW_LINE, term_line)

c Now re-define the picture geometry without any rings
            call EUGEOM(1, sun_loc, sun_rad, obs_pv(1), cmatrix,
     &          nbodies, body_locs, body_axes)

c Set up the bodies without drawing anything, for correct ring lighting
            call RSPK_DrawBodies(nbodies, body_pts, body_names,
     &          body_dist, use_diampts, .FALSE., 0.d0,
     &          pmerids, plats, mmerids, mlats,
     &          NO_LINE, NO_LINE, NO_LINE,
     &          NO_LINE, NO_LINE, NO_LINE, 0.d0)

c Draw the interior rings
            call RSPK_DrawRings(1, last_opaq, ring_flags,
     &          ring_locs, ring_axes1, ring_axes2, ring_dark,
     &          ring_dashed,
     &          nloops, loop_locs, loop_axes1, loop_axes2, loop_ring,
     &          use_arcpts, LIT_LINE, DARK_LINE, SHADOW_LINE, term_line)

c***********************************************************************
c Case 2: OPAQUE_METHOD
c***********************************************************************

        else

c Define the geometry with the outermost opaque ring as a very flat
c ellipsoid
            call VEQU(ring_locs(1,last_opaq),  body_locs(1,nbodies+1))
            call VEQU(ring_axes1(1,last_opaq), body_axes(1,1,nbodies+1))
            call VEQU(ring_axes2(1,last_opaq), body_axes(1,2,nbodies+1))
            call VEQU(ring_axes3(1,last_opaq), body_axes(1,3,nbodies+1))

            call EUGEOM(1, sun_loc, sun_rad, obs_pv(1), cmatrix,
     &                  nbodies+1, body_locs, body_axes)

c Draw the planet and all moons exterior to the rings
            call RSPK_DrawBodies(nbodies, body_pts, body_names,
     &          body_dist, use_diampts, .TRUE., ring_rads(last_opaq),
     &          pmerids, plats, mmerids, mlats,
     &          LIT_LINE, DARK_LINE, term_line,
     &          NO_LINE,  NO_LINE,   NO_LINE, prime_pts)

c Draw the opaque ring invisibly
            call EUBODY(nbodies+1, 0, 0, 1, NO_LINE, NO_LINE, NO_LINE)

c Draw the exterior rings
            call RSPK_DrawRings(last_opaq+1, use_nrings, ring_flags,
     &          ring_locs, ring_axes1, ring_axes2, ring_dark,
     &          ring_dashed,
     &          nloops, loop_locs, loop_axes1, loop_axes2, loop_ring,
     &          use_arcpts, LIT_LINE, DARK_LINE, SHADOW_LINE, term_line)

c Re-define the picture geometry without any rings
            call EUGEOM(1, sun_loc, sun_rad, obs_pv(1), cmatrix,
     &          nbodies, body_locs, body_axes)

c Re-draw the moons interior to the opaque ring
            call RSPK_DrawBodies(nbodies, body_pts, body_names,
     &          body_dist, use_diampts, .TRUE., ring_rads(last_opaq),
     &          pmerids, plats, mmerids, mlats,
     &          NO_LINE,  NO_LINE,   NO_LINE,
     &          LIT_LINE, DARK_LINE, term_line, prime_pts)

c Now draw the interior rings
            call RSPK_DrawRings(1, last_opaq, ring_flags,
     &          ring_locs, ring_axes1, ring_axes2, ring_dark,
     &          ring_dashed,
     &          nloops, loop_locs, loop_axes1, loop_axes2, loop_ring,
     &          use_arcpts, LIT_LINE, DARK_LINE, SHADOW_LINE, term_line)

        end if

c***********************************************************************
c Draw the box boundaries, tick marks and labels
c***********************************************************************

600     continue
        call ESWRIT('%Draw box...')

c Draw the border
        call EUTEMP(-delta, -delta, -delta,  delta, 1, AXIS_LINE)
        call EUTEMP(-delta,  delta,  delta,  delta, 1, AXIS_LINE)
        call EUTEMP( delta,  delta,  delta, -delta, 1, AXIS_LINE)
        call EUTEMP( delta, -delta, -delta, -delta, 1, AXIS_LINE)

c Draw the tick marks and labels
        call RSPK_Labels2(cmatrix, delta, AXIS_LINE)

c***********************************************************************
c Label the moons, if necessary
c***********************************************************************

        if (moon_labelpts .gt. 0.d0) then
                call ESWRIT('%Label moons...')

                do 700 ibody = 2, nbodies
                        if (body_names(ibody) .eq. ' ') goto 700
                        call RSPK_Annotate(body_names(ibody),
     &                          body_los(1,ibody),
     &                          max(body_pts(ibody), use_diampts)
     &                                  * 0.5d0 * fov/FOV_PTS,
     &                          cmatrix, delta)
700             continue
        end if

c***********************************************************************
c Draw stars, if necessary
c***********************************************************************

        if (nstars .gt. 0) then
            call ESWRIT('%Draw stars...')
            call ESLWID(STAR_WIDTH)
        end if

        do 800 i = 1, nstars
                call RADREC(1.d0, star_ras(i), star_decs(i), los)
                call EUSTAR(los, 1, STARFONT, STARFONTSIZE,
     &                  star_diampts/FOV_PTS, STAR_LINE)
                if (star_labels .and. star_names(i) .ne. ' ')
     &                  call RSPK_Annotate(star_names(i), los, 0.d0,
     &                          cmatrix, delta)
800     continue
        call ESLWID(0.d0)

c***********************************************************************
c Close the file and return
c***********************************************************************

        call EUCLR(DEVICE, 0.d0, 1.d0, 0.d0, 1.d0)

        return
        end

c*******************************************************************************
c subroutine RSPK_Labels2(cmatrix, delta, ltype)
c
c This internal subroutine plots tickmarks and numeric labels on the figure.
c
c Input:
c       cmatrix         transformation matrix for camera orientation.
c       delta           field of view size.
c       ltype           line type for ESCHER routines.
c
c*******************************************************************************

        subroutine RSPK_Labels2(cmatrix, delta, ltype)
        double precision        cmatrix(3,3), delta
        integer                 ltype

c******************************************************
c Subroutine internal variables
c******************************************************

        integer                 i, k, k1, k2, nsubs
        double precision        dummy, ra, dec, delta_ra, dtick1,
     &                          dtick2, spr, sdelta, s, ds, x, y,
     &                          length, DPR
        double precision        j2000_los(3), camera_los(3)
        logical                 ismajor

c*****************************************************
c Axis plotting parameters
c*****************************************************

        double precision        MINSTEPS
        parameter               (MINSTEPS = 3.)

        double precision        TICKSIZE1, TICKSIZE2
        parameter               (TICKSIZE1 = 0.05)
        parameter               (TICKSIZE2 = 0.02)

        integer          NCHOICES
        parameter        (NCHOICES = 24)
        double precision STEP1(NCHOICES)
        integer          SUBSTEPS(NCHOICES)
        data             STEP1/0.001, 0.002,  0.005,
     &                          0.01,  0.02,   0.05,
     &                           0.1,   0.2,    0.5,
     &                            1.,    2.,     5.,    10.,    30.,
     &                           60.,  120.,   300.,   600.,  1800.,
     &                         3600., 7200., 18000., 36000., 72000. /
        data             SUBSTEPS/ 5,     4,      5,
     &                             5,     4,      5,
     &                             5,     4,      5,
     &                             5,     4,      5,      5,      6,
     &                             6,     4,      5,      5,      6,
     &                             6,     4,      5,      5,      6 /

c***********************************************************************
c Get FOV parameters
c***********************************************************************

        call RECRAD(cmatrix(1,3), dummy, ra, dec)
        delta_ra = delta / cos(dec)

        dtick1 = TICKSIZE1 * delta
        dtick2 = TICKSIZE2 * delta

c***********************************************************************
c Plot RA tick marks along horizontal boundaries
c***********************************************************************

c Determine RA step size starting point (in seconds)
        spr = DPR() * 3600.d0/15.d0
        sdelta = delta_ra * spr
        do 100 i = NCHOICES, 2, -1
            if (2.*sdelta .ge. MINSTEPS*STEP1(i)) goto 101
100     continue
101     continue

        nsubs = SUBSTEPS(i)     
        ds = STEP1(i) / nsubs
        k1 = nint((ra*spr - sdelta) / ds + 0.5)
        k2 = nint((ra*spr + sdelta) / ds - 0.5)

c Plot RA tick marks
        do 110 k = k1, k2
            s = k * ds

            length = dtick2
            ismajor = (mod(k,nsubs) .eq. 0)
            if (ismajor) length = dtick1

            call RADREC(1.d0, s/spr, dec, j2000_los)
            call MTXV(cmatrix, j2000_los, camera_los)
            x = -camera_los(1) / camera_los(3)
c           y = -camera_los(2) / camera_los(3)

            if (abs(x) .le. delta) then
                call EUTEMP(x,  delta-length, x,  delta, 1, ltype)
                if (ismajor) call RSPK_WriteLabel(s, 'B')

                call EUTEMP(x, -delta+length, x, -delta, 1, ltype)
            end if

110     continue

c***********************************************************************
c Plot declination tick marks along vertical boundaries
c***********************************************************************

c Determine dec step size starting point (in seconds)
        spr = DPR() * 3600.d0
        sdelta = delta * spr
        do 200 i = NCHOICES, 2, -1
            if (2.*sdelta .ge. MINSTEPS*STEP1(i)) goto 201
200     continue
201     continue

        nsubs = SUBSTEPS(i)     
        ds = STEP1(i) / nsubs
        k1 = nint((dec*spr - sdelta) / ds + 0.5)
        k2 = nint((dec*spr + sdelta) / ds - 0.5)

c Plot dec tick marks
        do 210 k = k1, k2
            s = k * ds

            length = dtick2
            ismajor = (mod(k,nsubs) .eq. 0)
            if (ismajor) length = dtick1

            call RADREC(1.d0, ra, s/spr, j2000_los)
            call MTXV(cmatrix, j2000_los, camera_los)
c           x = -camera_los(1) / camera_los(3)
            y = -camera_los(2) / camera_los(3)

            if (abs(y) .le. delta) then
                call EUTEMP(-delta+length, y, -delta, y, 1, ltype)
                if (ismajor) call RSPK_WriteLabel(s, 'L')

                call EUTEMP( delta-length, y,  delta, y, 1, ltype)
            end if
210     continue

        return
        end

c***********************************************************************
c subroutine RSPK_DrawBodies(nbodies, body_pts, body_names, body_dist,
c       body_diampts, update_names, mindist,
c       planet_merids, planet_lats, moon_merids, moon_lats,
c       lit_line, dark_line, term_line,
c       lit_line2, dark_line2, term_line2,
c       prime_pts)
c
c This internal subroutine draws all planets and moons falling outside
c a specified radius.  Optionally, it also sets body_names to blank when
c the body is not visible.
c***********************************************************************

        subroutine RSPK_DrawBodies(nbodies, body_pts, body_names,
     &          body_dist, body_diampts, update_names, mindist,
     &          planet_merids, planet_lats, moon_merids, moon_lats,
     &          lit_line, dark_line, term_line,
     &          lit_line2, dark_line2, term_line2, prime_pts)

        implicit                none
        integer                 nbodies, 
     &                          planet_merids, planet_lats,
     &                          moon_merids, moon_lats,
     &                          lit_line, dark_line, term_line,
     &                          lit_line2, dark_line2, term_line2
        double precision        body_pts(*), body_diampts,
     &                          body_dist(*), mindist, prime_pts
        character*(*)           body_names(*)
        logical                 update_names

        integer                 ibody, l1, l2, l3, LASTNB
        logical                 isvis, inner, flagval, ignore, ESFLAG

        CHARACTER*80            COMMENT

c Draw planet
        l1 = lit_line
        l2 = dark_line
        l3 = term_line
        isvis = (l1 .ne. 0 .or. l2 .ne. 0 .or. l3 .ne. 0)

        if (isvis) call ESWRIT('%Draw planet...')

        if (isvis .and. prime_pts .gt. 0.d0) then
            call ESLWID(prime_pts)
            call EUBODY(1, 1, 0, 1, l1, l2, 0)
            call EUBODY(1, 0, 0, 1, 0, 0, 0)
        end if

        call ESLWID(0.d0)
        call EUBODY(1, planet_merids, planet_lats, 1, l1, l2, l3)

c Draw invisible object at middle of screen (to ensure correct lighting)
        call EUBODY(2, 2, 1, 1, 0, 0, 0)

c Draw the moons...
        ignore = ESFLAG(0)
        do 100 ibody = 3, nbodies
                inner = (body_dist(ibody) .lt. mindist)
                if (inner) then
                        l1 = lit_line2
                        l2 = dark_line2
                        l3 = term_line2
                else
                        l1 = lit_line
                        l2 = dark_line
                        l3 = term_line
                end if

                isvis = (l1 .ne. 0 .or. l2 .ne. 0 .or. l3 .ne. 0)
                if (isvis) call ESWRIT('%Draw ' //
     &                  body_names(ibody)(1:LASTNB(body_names(ibody)))//
     &                  '...')

c Re-initialize flag
                flagval = ESFLAG(0)

c Draw body
                if (isvis .and. prime_pts .gt. 0.d0
     &                    .and. body_diampts .eq. 0.d0
     &                    .and. body_pts(ibody) > body_diampts * 8) then
                    call ESLWID(prime_pts)
                    call EUBODY(ibody, 1, 0, 1, l1, l2, 0)
                    call EUBODY(ibody, 0, 0, 1,  0,  0, 0)
                end if

                call ESLWID(body_diampts - body_pts(ibody))
                call EUBODY(ibody, moon_merids, moon_lats,
     &                  1, l1, l2, l3)

c Check flag
                flagval = ESFLAG(0)

c Turn off the label if no part of body was drawn
                if (update_names .and. isvis .and. .not. flagval)
     &                  body_names(ibody) = ' '
100     continue
        call ESLWID(0.d0)

        return
        end

c***********************************************************************
c subroutine RSPK_DrawRings(iring1, iring2, ring_flags,
c       ring_locs, ring_axes1, ring_axes2, ring_dark, ring_dashed,
c       nloops, loop_locs, loop_axes1, loop_axes2, loop_ring,
c       arc_width, lit_line, dark_line, shadow_line, term_line)
c
c This internal subroutine draws all the rings and arcs.
c 2/18/01 modified from RSPK_DrawView.f/RSPK_DrawRings to differentiate
c between dark (unlit) rings and shadowed rings.
c***********************************************************************

        subroutine RSPK_DrawRings(iring1, iring2, ring_flags,
     &          ring_locs, ring_axes1, ring_axes2, ring_dark,
     &          ring_dashed,
     &          nloops, loop_locs, loop_axes1, loop_axes2, loop_ring,
     &          arc_width, lit_line, dark_line, shadow_line, term_line)

        implicit                none
        integer                 iring1, iring2, nloops, lit_line,
     &                          dark_line, shadow_line, term_line,
     &                          loop_ring(*)
        double precision        ring_locs(3,*), loop_locs(3,*),
     &                          ring_axes1(3,*), ring_axes2(3,*),
     &                          loop_axes1(3,*), loop_axes2(3,*),
     &                          arc_width
        logical                 ring_flags(*), ring_dark(*),
     &                          ring_dashed(*)

        integer                 iring, iloop, draw_line
        character*2             ringstr

c Draw the rings
        do iring = iring1, iring2
            if (ring_flags(iring)) then

                draw_line = lit_line
                if (ring_dark(iring)) draw_line = dark_line

                write(ringstr, '(i2)') iring
                call ESWRIT('%Draw ring #' // ringstr // '...')

                if (ring_dashed(iring)) call ESWRIT('[30 30] 0 setdash')

                call EURING(ring_locs(1,iring),
     &                  ring_axes1(1,iring), ring_axes2(1,iring),
     &                  1, draw_line, shadow_line)

                if (ring_dashed(iring)) call ESWRIT('[] 0 setdash')
            end if
        end do

c Draw the arcs as tiny loops
        if (nloops .gt. 0) call ESWRIT('%Draw arcs...')

        call ESLWID(arc_width)
        do iloop = 1, nloops
            iring = loop_ring(iloop)
            if (iring .ge. iring1 .and. iring .le. iring2) then

                draw_line = lit_line
                if (ring_dark(iring)) draw_line = dark_line

                call EURING(loop_locs(1,iloop),
     &                  loop_axes1(1,iloop), loop_axes2(1,iloop),
     &                  1, draw_line, shadow_line)
            end if
        end do

        call ESLWID(0.d0)

        return
        end

c***********************************************************************
c subroutine RSPK_Labels(cmatrix, delta, ltype)
c
c This internal subroutine plots tickmarks and numeric labels on the figure.
c
c Input:
c       cmatrix         transformation matrix for camera orientation.
c       delta           field of view size.
c       ltype           line type for ESCHER routines.
c
c***********************************************************************

        subroutine RSPK_Labels(cmatrix, delta, ltype)

        implicit                none
        double precision        cmatrix(3,3), delta
        integer                 ltype

c******************************************************
c Subroutine internal variables
c******************************************************

        integer                 i, k, k1, k2, nsubs
        double precision        dummy, ra, dec, delta_ra, dtick1,
     &                          dtick2, spr, sdelta, s, ds, x, y,
     &                          length, DPR
        double precision        j2000_los(3), camera_los(3)
        logical                 ismajor

c*****************************************************
c Axis plotting parameters
c*****************************************************

        double precision        MINSTEPS
        parameter               (MINSTEPS = 3.)

        double precision        TICKSIZE1, TICKSIZE2
        parameter               (TICKSIZE1 = 0.05)
        parameter               (TICKSIZE2 = 0.02)

        integer          NCHOICES
        parameter        (NCHOICES = 24)
        double precision STEP1(NCHOICES)
        integer          SUBSTEPS(NCHOICES)
        data             STEP1/0.001, 0.002,  0.005,
     &                          0.01,  0.02,   0.05,
     &                           0.1,   0.2,    0.5,
     &                            1.,    2.,     5.,    10.,    30.,
     &                           60.,  120.,   300.,   600.,  1800.,
     &                         3600., 7200., 18000., 36000., 72000. /
        data             SUBSTEPS/ 5,     4,      5,
     &                             5,     4,      5,
     &                             5,     4,      5,
     &                             5,     4,      5,      5,      6,
     &                             6,     4,      5,      5,      6,
     &                             6,     4,      5,      5,      6 /

c***********************************************************************
c Get FOV parameters
c***********************************************************************

        call RECRAD(cmatrix(1,3), dummy, ra, dec)
        delta_ra = delta / cos(dec)

        dtick1 = TICKSIZE1 * delta
        dtick2 = TICKSIZE2 * delta

c***********************************************************************
c Plot RA tick marks along horizontal boundaries
c***********************************************************************

c Determine RA step size starting point (in seconds)
        spr = DPR() * 3600.d0/15.d0
        sdelta = delta_ra * spr
        do 100 i = NCHOICES, 2, -1
                if (2.*sdelta .ge. MINSTEPS*STEP1(i)) goto 101
100     continue
101     continue

        nsubs = SUBSTEPS(i)     
        ds = STEP1(i) / nsubs
        k1 = nint((ra*spr - sdelta) / ds + 0.5)
        k2 = nint((ra*spr + sdelta) / ds - 0.5)

c Plot RA tick marks
        do 110 k = k1, k2
                s = k * ds

                length = dtick2
                ismajor = (mod(k,nsubs) .eq. 0)
                if (ismajor) length = dtick1

c Label lower axis
                call RADREC(1.d0, s/spr, dec-delta, j2000_los)
                call MTXV(cmatrix, j2000_los, camera_los)
                x = -camera_los(1) / camera_los(3)
                y = -camera_los(2) / camera_los(3)
                call EUTEMP(x, y-length, x, y, 1, ltype)
                if (ismajor) call RSPK_WriteLabel(s, 'B')

c Label upper axis
                call RADREC(1.d0, s/spr, dec+delta, j2000_los)
                call MTXV(cmatrix, j2000_los, camera_los)
                x = -camera_los(1) / camera_los(3)
                y = -camera_los(2) / camera_los(3)
                call EUTEMP(x, y+length, x, y, 1, ltype)

110     continue

c***********************************************************************
c Plot declination tick marks along vertical boundaries
c***********************************************************************

c Determine dec step size starting point (in seconds)
        spr = DPR() * 3600.d0
        sdelta = delta * spr
        do 200 i = NCHOICES, 2, -1
                if (2.*sdelta .ge. MINSTEPS*STEP1(i)) goto 201
200     continue
201     continue

        nsubs = SUBSTEPS(i)     
        ds = STEP1(i) / nsubs
        k1 = nint((dec*spr - sdelta) / ds + 0.5)
        k2 = nint((dec*spr + sdelta) / ds - 0.5)

c Plot dec tick marks
        do 210 k = k1, k2
                s = k * ds

                length = dtick2
                ismajor = (mod(k,nsubs) .eq. 0)
                if (ismajor) length = dtick1

c Label left axis
                call RADREC(1.d0, ra + delta_ra, s/spr, j2000_los)
                call MTXV(cmatrix, j2000_los, camera_los)
                x = -camera_los(1) / camera_los(3)
                y = -camera_los(2) / camera_los(3)
                call EUTEMP(x+length, y, x, y, 1, ltype)
                if (ismajor) call RSPK_WriteLabel(s, 'L')

c Label right axis
                call RADREC(1.d0, ra - delta_ra, s/spr, j2000_los)
                call MTXV(cmatrix, j2000_los, camera_los)
                x = -camera_los(1) / camera_los(3)
                y = -camera_los(2) / camera_los(3)
                call EUTEMP(x-length, y, x, y, 1, ltype)

210     continue

        return
        end

c***********************************************************************
c subroutine RSPK_WriteLabel(secs, offset)
c
c This internal subroutine writes a label at the current point, in
c degrees/minutes/seconds format.
c
c Input:
c       secs            number of seconds for numeric value of label.
c       offset          offset direction of label from point: 'B'=below;
c                       'L'=left.
c***********************************************************************

        subroutine RSPK_WriteLabel(secs, offset)

        implicit                none
        double precision        secs
        character*(*)           offset

c*****************************************************
c Subroutine internal variables
c*****************************************************

        character*16            string
        integer                 ims, isec, imin, ideg, lstr
        double precision        secs1, fsign, fsecs

        double precision        MAXSECS
        parameter               (MAXSECS = 86400.d0)

c***********************************************************************
c Format character string
c***********************************************************************

c Check for meridian crossings
        secs1 = secs
        if (offset .eq. 'B') then
            secs1 = mod(secs, MAXSECS)
            if (secs1 .lt. 0.d0) secs1 = secs1 + MAXSECS
        end if

c Interpret value as degrees, minutes and seconds
        fsign = sign(1.d0, secs1)
        fsecs = abs(secs1)

        ims  = nint(fsecs * 1000.d0)
        isec = ims / 1000
        ims  = ims - 1000*isec
        imin = isec / 60
        isec = isec - 60*imin
        ideg = imin / 60
        imin = imin - 60*ideg

c Write into character string
        write(string, 10) ideg, imin, isec, ims
10      format(i3, ' ', i2.2, ' ', i2.2, '.', i3.3)

c Strip trailing zeros and blanks
        do 100 lstr = len(string), 1, -1
                if (string(lstr:lstr) .ne. '0' .and.
     &              string(lstr:lstr) .ne. ' ') goto 101
100     continue
101     continue

c Strip trailing period, if present
        if (string(lstr:lstr) .eq. '.') lstr = lstr - 1

c Skip leading blanks
200     continue
                if (string(1:1) .ne. ' ') goto 201
                string = string(2:)
                lstr = lstr - 1
                goto 200
201     continue

c Insert sign if necessary
        if (fsign .lt. 0.d0) then
                string = '-' // string
                lstr = lstr + 1
        end if

c***********************************************************************
c Write string
c***********************************************************************

        call ESMOVE
        if (offset .eq. 'L') then
                call ESWRIT('('//string(1:lstr)//') LabelLeft')
        else
                call ESWRIT('('//string(1:lstr)//') LabelBelow')
        end if

        return
        end

c***********************************************************************
c subroutine RSPK_Annotate(name, los, radius, cmatrix, delta)
c
c This internal subroutine writes the name of a moon.
c
c Input:
c       name            name to write.
c       los             J2000 line of sight to the moon.
c       radius          sky radius of moon in radians.
c       cmatrix         transformation matrix for camera orientation.
c       delta           field of view size.
c
c***********************************************************************

        subroutine RSPK_Annotate(name, los, radius, cmatrix, delta)

        implicit                none
        character*(*)           name
        double precision        los(3), radius, cmatrix(3,3), delta

        double precision        camera_los(3), x, y
        integer                 LASTNB

c Locate the body in the field of view
        call MTXV(cmatrix, los, camera_los)
        if (camera_los(3) .le. 0.d0) return

        x = -camera_los(1) / camera_los(3)
        y = -camera_los(2) / camera_los(3)

c Offset upward and right by the moon's projected radius
        x = x + 0.7070d0 * radius
        y = y - 0.7070d0 * radius

c If it is inside, label it
        if (abs(x) .lt. delta .and. abs(y) .lt. delta) then
                call EUTEMP(x, y, x, y, 1, 1)
                call ESMOVE
                call ESWRIT('('//name(1:LASTNB(name))//') LabelBody')
        end if

        return
        end

c***********************************************************************
c subroutine RSPK_WriteString(string)
c
c This internal subroutine writes a Postscript-format string to the
c output file, properly parenthesized.  String lengths are limited.
c
c Input:
c       string          character string to output.
c***********************************************************************

        subroutine RSPK_WriteString(string)
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

        call ESWRIT('(' // temp(1:ltemp) // ')')

        return
        end

c*******************************************************************************
