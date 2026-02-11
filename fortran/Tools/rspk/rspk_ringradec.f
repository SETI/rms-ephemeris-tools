c*******************************************************************************
c$ Component_name:
c       RSPK_RingRaDec
c$ Abstract:
c       Returns the observed J2000 right ascension and declination of an
c       point on a ring at a specified time.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_RingRaDec(time, radius, lon, ra, dec)
c       double precision        time, radius, lon, ra, dec
c$ Inputs:
c       time            ephemeris time of the observation at Earth (as returned
c                       by SPICE routine UTC2ET).
c       radius          ring radius in km.
c       lon             longitude relative to sub-Earth longitude on ring, in
c                       radians.  Positive direction is the direction of ring
c                       rotation. 
c$ Outputs:
c       ra              right ascension of the ring point (radians).
c       dec             declination of the ring point (radians).
c$ Returns:
c       none
c$ Side_effects:
c       none
c$ Detailed_description:
c       This subroutine returns the observed J2000 right ascension and
c       declination of a point on an equatorial ring at a specified time.
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
c       call RSPK_RingRaDec(time, 100d3, 90.d0 * RPD(), ra, dec)
c       write(*,*) ra * DPR, dec * DPR
c$ Error_handling:
c       None.  The SPICE toolkit error handling is in effect.
c$ Limitations:
c       None.
c$ Author_and_institution:
c       Mark R. Showalter
c       PDS Rings Node, NASA/Ames Research Center
c$ Version_and_date:
c       1.0: September 1996
c$ Change_history:
c       none
c*******************************************************************************

        subroutine RSPK_RingRaDec(time, radius, lon, ra, dec)

        implicit                none
        double precision        time, radius, lon, ra, dec

        double precision        obs_pv(6), planet_dpv(6), dt,
     &                          rotmat(3,3), pole(3), vec(3),
     &                          ring_dp(3), range

        include                 'rspk_common.inc'

c Calculate the instantaneous position of the observer
        call RSPK_ObsLoc(time, obs_pv)

c Calculate the back-dated position of the body (neglecting aberration)
        call SPKAPP(planet_id, time, 'J2000', obs_pv, 'LT',
     &          planet_dpv, dt)

c Calculate right-hand rotation pole of planet
        call BODMAT(planet_id, time-dt, rotmat)
        call VPACK(rotmat(3,1), rotmat(3,2), rotmat(3,3), pole)

        if (planet_num .eq. 7) call VMINUS(pole, pole)

c Generate a rotation matrix J2000 --> planet frame
c This frame is defined by the Z axis along the planet pole and the XZ 
c plane including the direction from Earth to the planet.
        call TWOVEC(pole, 3, planet_dpv(1), 1, rotmat)

c Generate J2000 coordinates of ring point relative to Earth
        call VPACK(-radius * cos(lon), -radius * sin(lon), 0.d0, vec)
        call MTXV(rotmat, vec, vec)
        call VADD(planet_dpv(1), vec, ring_dp)

c Calculate the body RA/dec in the Solar System barycenter frame
        call RECRAD(ring_dp, range, ra, dec)

        return
        end

c*******************************************************************************
