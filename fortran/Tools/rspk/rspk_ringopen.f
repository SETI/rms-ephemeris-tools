c*******************************************************************************
c$ Component_name:
c       RSPK_RingOpen
c$ Abstract:
c       Returns the observed opening angle of the ring system.  It also returns
c       the subsolar latitude at the planet, plus information about whether
c       the visible ring side is lit.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_RingOpen(time, obs_b, sun_b, sun_db, isdark,
c                               obs_long, sun_long)
c       double precision        time, obs_b, sun_b, sun_db, obs_long, sun_long
c       logical                 isdark
c$ Inputs:
c       time            ephemeris time of the observation, as returned by SPICE
c                       routine UTC2ET.
c$ Outputs:
c       obs_b           observed opening angle of the rings (radians).
c       sun_b           subsolar latitude of the Sun as observed at planet
c                       (radians).
c       sun_db          radius of the Sun as observed at planet (radians).
c       isdark          .TRUE. if the observer sees the unlit side of the rings;
c                       .FALSE. if the observer sees the lit side.  Note that
c                       both sides of the rings are assumed to be lit while the
c                       Sun is crossing the ring plane.
c       obs_long        sub-Observer longitude measured from equatorial plane
c                       ascending node (radians).
c       sun_long        sub-solar longitude measured from equatorial plane
c                       ascending node (radians).
c$ Returns:
c       none
c$ Side_effects:
c       none
c$ Detailed_description:
c       This subroutine returns the observed opening angle of ring system at a
c       specified time.  It also returns the sub-obnserver longitude and the 
c       subsolar latitude and longitude at the planet, along with information
c       about whether the visible side is lit.  Longitudes are measured from
c       the equatorial plane's J2000 ascending node.
c
c       Note that both sides of the rings are assumed to be lit while the Sun
c       is crossing the ring plane.
c$ External_references:
c       SPICE Toolkit, RSPK Toolkit
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
c       1.0: January 1995
c       1.1: February 1997
c$ Change_history:
c       1.1: Updated to return longitudes in addition to latitudes.
c       January 1999: Updated to comments to reflect the fact that this routine
c               handles arbitrary observers, not just Earth.
c       1.2: Corrected to handle aberration in planet frame correctly.
c*******************************************************************************

        subroutine RSPK_RingOpen(time, obs_b, sun_b, sun_db, isdark,
     &                          obs_long, sun_long)

        implicit                none
        double precision        time, obs_b, sun_b, sun_db,
     &                          obs_long, sun_long
        logical                 isdark

        integer                 nradii
        double precision        dt, planet_time, radii(3), rotmat(3,3),
     &                          pole(3), obs_dp(3), norm_dp(3),
     &                          tempvec(3), ascnode(3)
        double precision        obs_pv(6), planet_dpv(6), planet_pv(6),
     &                          sun_dpv(6)
        double precision        VNORM, TWOPI, CLIGHT
        logical                 OPSGND
        include                 'rspk_common.inc'

c SPICE body id's
        integer                 SUN_ID
        parameter               (SUN_ID = 10)

c***********************************************************************
c Calculate the instantaneous position of the observer
c***********************************************************************

        call RSPK_ObsLoc(time, obs_pv)

c***********************************************************************
c Calculate the back-dated position of planet (neglecting aberration)
c***********************************************************************

        call SPKAPP(planet_id, time, 'J2000', obs_pv, 'CN',
     &                  planet_dpv, dt)
        planet_time = time - dt
        call SPKSSB(planet_id, planet_time, 'J2000', planet_pv)

c***********************************************************************
c Calculate the apparent direction to the Sun at planet
c***********************************************************************

c Include stellar aberration in this calculation
        call SPKAPP(SUN_ID, planet_time, 'J2000', planet_pv, 'LT+S',
     &          sun_dpv, dt)

c Get the Sun radius in radians
        call BODVAR(SUN_ID, 'RADII', nradii, radii)
        sun_db = radii(1) / VNORM(sun_dpv(1))

c***********************************************************************
c Calculate the planet pole
c***********************************************************************

c Note that the matrix returned by BODMAT converts from J2000 to the 
c body equator/prime meridian frame.  Its transpose does the reverse, 
c which means that its three columns are the body principal axes in
c J2000 coordinates.
        call BODMAT(planet_id, planet_time, rotmat)

c Save the planet pole vector (reversed for Uranus)
        call VPACK(rotmat(3,1), rotmat(3,2), rotmat(3,3), pole)
        if (planet_num .eq. 7) call VMINUS(pole, pole)

c Locate the equatorial plane's J2000 ascending node.
        call VPACK(0.d0, 0.d0, 1.d0, tempvec)
        call VCRSS(tempvec, pole, ascnode)

        call TWOVEC(pole, 3, ascnode, 1, rotmat)
c This rotation matrix now converts from J2000 to planet coords, where
c the z-axis is the planet pole and the x-axis is the ascending node.

c This fixes a bug in TWOVEC()
c       rotmat(3,1) = pole(1)

c***********************************************************************
c Calculate the observer opening angle
c***********************************************************************

c Calculate vector from planet to observer
        call VLCOM(1.d0, obs_pv(1), -1.d0, planet_pv(1), obs_dp)

c Correct for aberration in planet frame
        call VHAT(obs_dp, norm_dp)
        call VLCOM(1.d0, norm_dp, -1.d0/CLIGHT(), planet_pv(4), tempvec)

c Convert planet-observer direction to planet coordinates
        call MXV(rotmat, tempvec, tempvec)

c Derive angles
        obs_b = asin(tempvec(3) / VNORM(tempvec))

        obs_long = atan2(tempvec(2), tempvec(1))
        if (obs_long .lt. 0.d0) obs_long = obs_long + TWOPI()

c Calculate obs_b more accurately (not really needed)
c       call VHAT(planet_dp, tempvec)
c       obs_b = asin(-VDOT(pole, tempvec))

c***********************************************************************
c Calculate the Sun opening angle
c***********************************************************************

c Convert planet-Sun direction to planet coordinates
        call MXV(rotmat, sun_dpv(1), tempvec)

c Derive angles
        sun_b = asin(tempvec(3) / VNORM(tempvec))

        sun_long = atan2(tempvec(2), tempvec(1))
        if (sun_long .lt. 0.d0) sun_long = sun_long + TWOPI()

c Calculate sun_b more accurately (not really needed)
c       call VHAT(sun_dpv(1), tempvec)
c       sun_b = asin(VDOT(pole, tempvec))

c***********************************************************************
c Determine whether the rings are dark
c***********************************************************************

c If observer and Sun are on opposite sides of the equator, and the Sun
c is entirely on one side of the ring plane, then the rings are dark
        isdark = (OPSGND(obs_b, sun_b) .and. abs(sun_b) .gt. sun_db)

        return
        end

c*******************************************************************************
