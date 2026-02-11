c*******************************************************************************
c$ Component_name:
c       RSPK_BodyLatLon
c$ Abstract:
c       Returns the sub-observer and sub-solar latitude and longitude on a
c       planet or moon.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_BodyLatLon(time, body_id, subobs_lat, subsol_lat,
c                               subobs_long, subsol_long)
c       double precision        time, subobs_lat, subsol_lat,
c                               subobs_long, subsol_long
c       integer                 body_id
c$ Inputs:
c       time            ephemeris time of the observation, as returned by SPICE
c                       routine UTC2ET.
c$ Outputs:
c       subobs_lat      sub-observer latitude on body (radians).
c       subsol_lat      sub-solar latitude on body (radians).
c       subobs_long     sub-observer longitude on body (radians).
c       subsol_long     sub-solar longitude on body (radians).
c$ Returns:
c       none
c$ Side_effects:
c       none
c$ Detailed_description:
c       This subroutine returns the sub-observer and sub-solar latitude and
c       longitude on a planet or moon.  Longitudes are measured from the
c       body's prime meridian and are defined such that the longitude beneath
c       a fixed observer increases with time.
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
c       1.0: December 1998
c       1.1: January 2002
c$ Change_history:
c       1.1: Corrected bug in stellar aberration calculation.  Same as in
c            RSPK_RingOpen.
c*******************************************************************************

        subroutine RSPK_BodyLatLon(time, body_id, subobs_lat,
     &                          subsol_lat, subobs_long, subsol_long)

        implicit                none
        double precision        time, subobs_lat, subsol_lat,
     &                          subobs_long, subsol_long
        integer                 body_id

        double precision        dt, body_time, rotmat(3,3),
     &                          obs_dp(3), norm_dp(3), tempvec(3)
        double precision        obs_pv(6), body_dpv(6), body_pv(6),
     &                          sun_dpv(6)
        double precision        VNORM, TWOPI, CLIGHT
        include                 'rspk_common.inc'

c SPICE body id's
        integer                 SUN_ID
        parameter               (SUN_ID = 10)

c***********************************************************************
c Calculate the instantaneous position of the observer
c***********************************************************************

        call RSPK_ObsLoc(time, obs_pv)

c***********************************************************************
c Calculate the back-dated position of body (neglecting aberration)
c***********************************************************************

        call RSPK_SPKAPP(body_id, time, 'J2000', obs_pv, 'LT',
     &                  body_dpv, dt)
        body_time = time - dt
        call SPKSSB(body_id, body_time, 'J2000', body_pv)

c***********************************************************************
c Calculate the apparent direction to the Sun at body
c***********************************************************************

c Include stellar aberration in this calculation
        call SPKAPP(SUN_ID, body_time, 'J2000', body_pv, 'LT+S',
     &          sun_dpv, dt)

c***********************************************************************
c Get the rotation matix to the body equator/prime meridian frame
c***********************************************************************

c The matrix returned by BODMAT converts from J2000 to the body
c equator/prime meridian frame.
        call RSPK_BODMAT(body_id, body_time, rotmat)

c***********************************************************************
c Calculate the sub-Earth latitude and longitude
c***********************************************************************

c Calculate vector from body to observer
        call VLCOM(1.d0, obs_pv(1), -1.d0, body_pv(1), obs_dp)

c Correct for aberration in planet frame
        call VHAT(obs_dp, norm_dp)
        call VLCOM(1.d0, norm_dp, -1.d0/CLIGHT(), body_pv(4), tempvec)

c Convert planet-observer direction to planet coordinates
        call MXV(rotmat, tempvec, tempvec)

c Derive angles
        subobs_lat  =  asin(tempvec(3) / VNORM(tempvec))
        subobs_long = -atan2(tempvec(2), tempvec(1))
        if (subobs_long .lt. 0.) subobs_long = subobs_long + TWOPI(0.d0)

c***********************************************************************
c Calculate the sub-Solar latitude and longitude
c***********************************************************************

c Convert body-Sun direction to body coordinates
        call MXV(rotmat, sun_dpv(1), tempvec)

c Derive angles
        subsol_lat  =  asin(tempvec(3) / VNORM(tempvec))
        subsol_long = -atan2(tempvec(2), tempvec(1))
        if (subsol_long .lt. 0.) subsol_long = subsol_long + TWOPI(0.d0)

c***********************************************************************
c Remember that Uranus and its moons are retrograde
c***********************************************************************

        if (planet_num .eq. 7) then
            if (subobs_long .gt. 0.d0)
     &          subobs_long = TWOPI(0.d0) - subobs_long
            if (subsol_long .gt. 0.d0)
     &          subsol_long = TWOPI(0.d0) - subsol_long
        end if

        return
        end

c*******************************************************************************
