c*******************************************************************************
c$ Component_name:
c       RSPK_BodyLonLat
c$ Abstract:
c       Returns the sub-observer and sub-solar longitude and latitude on a
c       planet or moon.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_BodyLonLat(time, body_id, subobs_lon, subobs_lat,
c                                                 subsol_lon, subsol_lat)
c       double precision        time, subobs_lon, subobs_lat,
c                                     subobs_lon, subobs_lat
c       integer                 body_id
c$ Inputs:
c       time                ephemeris time of the observation, as returned by
c                           SPICE routine UTC2ET.
c$ Outputs:
c       subobs_lon          sub-observer longitude (radians).
c       subobs_lat          sub-observer latitude (radians).
c       subsol_lon          sub-solar longitude (radians).
c       subsol_lon          sub-solar latitude (radians).
c$ Returns:
c       none
c$ Side_effects:
c       none
c$ Detailed_description:
c       This subroutine returns the sub-observer and sub-solar latitude and
c       longitude on a planet or moon.  Longitudes are measured from the
c       body's prime meridian and are defined such that the longitude beneath
c       a fixed observer increases with time (east for the Uranus system, west
c       for the others.
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
c       2.0: July 2021
c$ Change_history:
c       1.1: Corrected bug in stellar aberration calculation.  Same as in
c            RSPK_RingOpen.
c*******************************************************************************

        subroutine RSPK_BodyLonLat(time, body_id,
     &                             subobs_lon, subobs_lat,
     &                             subsol_lon, subsol_lat)

        implicit                none
        integer                 body_id
        double precision        time, subobs_lon, subobs_lat,
     &                                subsol_lon, subsol_lat

        double precision        VNORM, CLIGHT, TWOPI

        logical*4               found
        integer*4               n, abs_method
        character*80            body_name, reporting
        double precision        radii(3), r_eq, r_pole, flattening
        double precision        obs_pv(6), body_center_dpv(6),
     &                          body_center_dt, body_time, body_pv(6),
     &                          sun_time
        double precision        obs_dpv(6), sun_dpv(6), dt, rotmat(3,3)
        double precision        obs_dp_in_body_frame(3),
     &                          sun_dp_in_body_frame(3),
     &                          radius

        include                 'rspk_common.inc'

c SPICE body id's
        integer                 SUN_ID
        parameter               (SUN_ID = 10)

c***********************************************************************
c Get info about the body: name, frame, shape
c***********************************************************************

        call BODC2N(body_id, body_name, found)

        call BODVRD(body_name, 'RADII', 3, n, radii)
        r_eq = radii(1)
        r_pole = radii(3)
        flattening = (r_eq - r_pole) / r_eq

c***********************************************************************
c Calculate the instantaneous position of the observer
c***********************************************************************

        call RSPK_ObsLoc(time, obs_pv)

c***********************************************************************
c Calculate the back-dated position of body
c***********************************************************************

        call RSPK_SPKAPP(body_id, time, 'J2000', obs_pv, 'CN',
     &                   body_center_dpv, body_center_dt)
        body_time = time - body_center_dt + r_eq/CLIGHT()
        call SPKSSB(body_id, body_time, 'J2000', body_pv)

c***********************************************************************
c Calculate the apparent directions to the Sun and observer
c***********************************************************************

        call SPKAPP(SUN_ID, body_time, 'J2000', body_pv, 'CN+S',
     &              sun_dpv, dt)

        call SPKAPP(obs_id, body_time, 'J2000', body_pv, 'XCN+S',
     &              obs_dpv, dt)

c***********************************************************************
c Get the rotation matix to the body equator/prime meridian frame
c***********************************************************************

c The matrix returned by BODMAT converts from J2000 to the body
c equator/prime meridian frame.
        call RSPK_BODMAT(body_id, body_time, rotmat)

c***********************************************************************
c Calculate sub-observer and sub-solar longitude and latitude
c***********************************************************************

c Convert planet-observer direction to planet coordinates
        call MXV(rotmat, obs_dpv, obs_dp_in_body_frame)
        call RECLAT(obs_dp_in_body_frame, radius,
     &              subobs_lon, subobs_lat)
        if (subobs_lon .lt. 0.d0)
     &          subobs_lon = subobs_lon + TWOPI()
        subobs_lon = TWOPI() - subobs_lon

        call MXV(rotmat, sun_dpv, sun_dp_in_body_frame)
        call RECLAT(sun_dp_in_body_frame, radius,
     &              subsol_lon, subsol_lat)
        if (subsol_lon .lt. 0.d0)
     &          subsol_lon = subsol_lon + TWOPI()
        subsol_lon = TWOPI() - subsol_lon

        return
        end

c*******************************************************************************
