c*******************************************************************************
c$ Component_name:
c       RSPK_AnsaRaDec
c$ Abstract:
c       Returns the observed J2000 right ascension and declination of a
c       ring ansa at a specified time.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_AnsaRaDec(time, radius, isright, ra, dec)
c       double precision        time, radius, ra, dec
c       logical                 isright
c$ Inputs:
c       time            ephemeris time of the observation at Earth (as returned
c                       by SPICE routine UTC2ET).
c       radius          ring radius in km.
c       isright         .TRUE. for the right ansa (near lon 90 degrees);
c                       .FALSE. for the left ansa (near long 270 degrees).
c$ Outputs:
c       ra              right ascension of the ring point (radians).
c       dec             declination of the ring point (radians).
c$ Returns:
c       none
c$ Side_effects:
c       none
c$ Detailed_description:
c       This subroutine returns the observed J2000 right ascension and
c       declination of a point on the ansa of an equatorial ring at a
c       specified time.
c
c       Returned values apply to either the Earth's center or to an observatory,
c       depending on whether/how RSPK_SetObs() has been called first.
c
c       Note: Coordinates are given in the Solar System barycenter frame; they
c       are not corrected for stellar aberration.  This means that coordinates
c       should be correct relative to the cataloged locations of background
c       stars.
c$ External_references:
c       SPICE Toolkit routines: BODMAT, MTXV, RECRAD, SPKAPP, TWOVEC, VADD,
c                               VMINUS, VPACK
c       RSPK Toolkit routines: RSPK_ObsLoc
c$ Examples:
c       This fragment of code prints out the RA and dec of the evening ansa of
c       a ring of radius 100,000 km:
c
c       call UTC2ET('1995-11-19 12:00:00', time)
c       call RSPK_AnsaRaDec(time, 100d3, .TRUE., ra, dec)
c       write(*,*) 'Right ansa: ', ra * DPR, dec * DPR
c$ Error_handling:
c       None.  The SPICE toolkit error handling is in effect.
c$ Limitations:
c       None.
c$ Author_and_institution:
c       Mark R. Showalter
c       PDS Rings Node, NASA/Ames Research Center
c$ Version_and_date:
c       1.0: July 2004
c$ Change_history:
c       none
c*******************************************************************************

        subroutine RSPK_AnsaRaDec(time, radius, isright, ra, dec)

        double precision        time, radius, ra, dec
        logical                 isright

        double precision        obs_dist, sun_dist, obs_b, sun_b,
     &                          sun_db, obs_long, sun_long, offset, lon,
     &                          PI
        logical                 isdark

c Calculate the observer distance and ring opening angle
        call RSPK_Ranges(time, sun_dist, obs_dist)
        call RSPK_RingOpen(time, obs_b, sun_b, sun_db, isdark,
     &                     obs_long, sun_long)

c Calculate the angular offset from 90 or 270 degrees to the ansa
        offset = asin(radius / (obs_dist * cos(obs_b)))

c Determine the longitude sought
        PI = 4.d0 * atan(1.d0)
        if (isright) then
                lon = 0.5d0 * PI - offset
        else
                lon = 1.5d0 * PI + offset
        end if

c Now calculate the RA and dec from the longitude
        call RSPK_RingRaDec(time, radius, lon, ra, dec)

        return
        end

c*******************************************************************************
