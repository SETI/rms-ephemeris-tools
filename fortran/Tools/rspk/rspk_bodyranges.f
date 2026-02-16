c*******************************************************************************
c$ Component_name:
c       RSPK_BodyRanges
c$ Abstract:
c       Returns the Sun-body and observer-body distances.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_BodyRanges(time, body_id, sundist, earthdist)
c$ Inputs:
c       time            ephemeris time of the observation, as returned by SPICE
c                       routine UTC2ET.
c       body_id         body ID as used in the SPICE toolkit.
c$ Outputs:
c       sundist         Sun-body distance (km)
c       earthdist       Observer-body distance (km)
c$ Returns:
c       none
c$ Side_effects:
c       none
c$ Detailed_description:
c       This subroutine returns the Sun-body and Earth-body distances at
c       a specified time, in km.
c$ External_references:
c       SPICE Toolkit, RSPK_ObsLoc
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
c       1.0: December 2001
c$ Change_history:
c       none
c*******************************************************************************

        subroutine RSPK_BodyRanges(time, body_id, sundist, earthdist)

        implicit                none
        double precision        time, sundist, earthdist
        integer                 body_id

        double precision        dt, body_time, obs_pv(6),
     &                          body_dpv(6), body_pv(6), sun_dpv(6)
        double precision        VNORM
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

        call SPKAPP(body_id, time, 'J2000', obs_pv, 'LT', body_dpv, dt)
        body_time = time - dt
        call SPKSSB(body_id, body_time, 'J2000', body_pv)

c***********************************************************************
c Calculate the apparent direction to the Sun at body
c***********************************************************************

c Include stellar aberration in this calculation
        call SPKAPP(SUN_ID, body_time, 'J2000', body_pv, 'LT+S',
     &          sun_dpv, dt)

c***********************************************************************
c Calculate distances
c***********************************************************************

        earthdist = VNORM(body_dpv(1))
        sundist = VNORM(sun_dpv(1))

        return
        end

c*******************************************************************************
