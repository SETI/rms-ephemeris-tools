c*******************************************************************************
c$ Component_name:
c       RSPK_Ranges
c$ Abstract:
c       Returns the Sun-planet and observer-planet distances.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_Ranges(time, sundist, earthdist)
c$ Inputs:
c       time            ephemeris time of the observation, as returned by SPICE
c                       routine UTC2ET.
c$ Outputs:
c       sundist         Sun-planet distance (km)
c       earthdist       Observer-planet distance (km)
c$ Returns:
c       none
c$ Side_effects:
c       none
c$ Detailed_description:
c       This subroutine returns the Sun-planet and Earth-planet distances at
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
c       1.0: January 1997
c$ Change_history:
c       none
c*******************************************************************************

        subroutine RSPK_Ranges(time, sundist, earthdist)

        implicit                none
        double precision        time, sundist, earthdist

        double precision        dt, planet_time, obs_pv(6),
     &                          planet_dpv(6), planet_pv(6), sun_dpv(6)
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
c Calculate the back-dated position of planet (neglecting aberration)
c***********************************************************************

        call SPKAPP(planet_id, time, 'J2000', obs_pv, 'LT',
     &                  planet_dpv, dt)
        planet_time = time - dt
        call SPKSSB(planet_id, planet_time, 'J2000', planet_pv)

c***********************************************************************
c Calculate the apparent direction to the Sun at planet
c***********************************************************************

c Include stellar aberration in this calculation
        call SPKAPP(SUN_ID, planet_time, 'J2000', planet_pv, 'LT+S',
     &          sun_dpv, dt)

c***********************************************************************
c Calculate distances
c***********************************************************************

        earthdist = VNORM(planet_dpv(1))
        sundist = VNORM(sun_dpv(1))

        return
        end

c*******************************************************************************
