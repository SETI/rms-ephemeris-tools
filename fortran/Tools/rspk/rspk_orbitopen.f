c*******************************************************************************
c$ Component_name:
c       RSPK_OrbitOpen
c$ Abstract:
c       Returns the observed opening angle of an orbital plane.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_RingOpen(time, moon_id, obs_b, obs_long)
c       double precision        time, obs_b, obs_long
c       integer                 moon_id
c$ Inputs:
c       time            ephemeris time of the observation, as returned by SPICE
c                       routine UTC2ET.
c       moon_id         ID of moon orbiting selected planet.
c$ Outputs:
c       obs_b           observed opening angle of the orbit (radians).
c       obs_long        longitude of observer relative to moon (radians).
c$ Returns:
c       none
c$ Side_effects:
c       none
c$ Detailed_description:
c       This subroutine returns the observed opening angle of an orbital plane
c       at a specified time.
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
c       1.0: February 2006
c$ Change_history:
c*******************************************************************************

        subroutine RSPK_OrbitOpen(time, moon_id, obs_b, obs_long)

        implicit                none
        double precision        time, obs_b, obs_long
        integer                 moon_id

        double precision        dt, planet_time, rotmat(3,3), obs_dp(3),
     &                          norm_dp(3), tempvec(3), light_time
        double precision        obs_pv(6), planet_dpv(6), planet_pv(6),
     &                          moon_dpv(6)
        double precision        VNORM, TWOPI, CLIGHT
        include                 'rspk_common.inc'

c***********************************************************************
c Calculate the instantaneous position of the observer
c***********************************************************************

        call RSPK_ObsLoc(time, obs_pv)

c***********************************************************************
c Calculate the back-dated position of planet (neglecting aberration)
c***********************************************************************

        call SPKAPP(planet_id, time, 'J2000', obs_pv, 'CN',
     &              planet_dpv, dt)
        planet_time = time - dt
        call SPKSSB(planet_id, planet_time, 'J2000', planet_pv)

c***********************************************************************
c Calculate the orbit pole
c***********************************************************************

c Calculate the instantaneous state of the moon WRT the planet
        call SPKEZ(moon_id, time, 'J2000', 'NONE', planet_id, moon_dpv,
     &             light_time)

c Create a rotation matrix to a frame where z is the pole
        call TWOVEC(moon_dpv(1), 1, moon_dpv(4), 2, rotmat)

c***********************************************************************
c Calculate the observer opening angle
c***********************************************************************

c Vector from planet to observer (match RSPK_RingOpen; was wrongly -planet_pv)
        call VLCOM(1.d0, obs_pv(1), -1.d0, planet_pv(1), obs_dp)

c Correct for aberration in planet frame
        call VHAT(obs_dp, norm_dp)
        call VLCOM(1.d0, norm_dp, -1.d0/CLIGHT(), planet_pv(4), tempvec)

c Convert planet-observer direction to planet coordinates
        call MXV(rotmat, tempvec, tempvec)

c Derive angles
        obs_b = asin(tempvec(3) / VNORM(tempvec))

        obs_long = atan2(-tempvec(2), tempvec(1))
        if (obs_long .lt. 0.d0) obs_long = obs_long + TWOPI()

        return
        end

c*******************************************************************************
