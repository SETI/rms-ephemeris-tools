c*******************************************************************************
c$ Component_name:
c       RSPK_Phase
c$ Abstract:
c       Returns the solar phase angle of the planet, as seen from the observer
c       at a specified time.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_Phase(time, phase)
c       double precision        time, phase
c$ Inputs:
c       time            ephemeris time of the observation, as returned by SPICE
c                       routine UTC2ET.
c$ Outputs:
c       phase           phase angle of planet, as seen from the observer
c                       (radians).
c$ Returns:
c       none
c$ Side_effects:
c       none
c$ Detailed_description:
c       This subroutine returns the solar phase angle of the planet, as seen
c       from the observer at a specified time.
c$ External_references:
c       SPICE Toolkit routines: SPKAPP, VMINUS, VSEP
c       RSPK Toolkit routines: RSPK_ObsLoc
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
c       1.0: August 1996
c$ Change_history:
c       January 1999: Updated comments to reflect the fact that this routine
c               works for arbitrary observers, not just Earth.
c*******************************************************************************

        subroutine RSPK_Phase(time, phase)

        implicit                none
        double precision        time, phase

        double precision        dt, planet_time, obs_pv(6), 
     &                          planet_dpv(6), planet_pv(6),
     &                          sun_dpv(6), obs_dp(3)
        double precision        VSEP
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
c Calculate the direction to the Sun at planet
c***********************************************************************

        call SPKAPP(SUN_ID, planet_time, 'J2000', planet_pv, 'LT',
     &          sun_dpv, dt)

c***********************************************************************
c Calculate the phase angle
c***********************************************************************

        call VMINUS(planet_dpv(1), obs_dp)
        phase = VSEP(sun_dpv(1), obs_dp)

        return
        end

c*******************************************************************************
