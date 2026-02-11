c*******************************************************************************
c$ Component_name:
c       RSPK_BodyPhase
c$ Abstract:
c       Returns the solar phase angle of a body, as seen from the observer at a
c       specified time.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_BodyPhase(time, body_id, phase)
c       double precision        time, phase
c       integer         body_id
c$ Inputs:
c       time            ephemeris time of the observation, as returned by SPICE
c                       routine UTC2ET.
c       body_id         body ID as used in the SPICE toolkit.
c$ Outputs:
c       phase           phase angle of body, as seen from the observer
c                       (radians).
c$ Returns:
c       none
c$ Side_effects:
c       none
c$ Detailed_description:
c       This subroutine returns the solar phase angle of a vody, as seen from
c       the observer at a specified time.
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
c       1.0: December 2001
c$ Change_history:
c       None.
c*******************************************************************************

        subroutine RSPK_BodyPhase(time, body_id, phase)

        implicit                none
        double precision        time, phase
        integer                 body_id

        double precision        dt, body_time, obs_pv(6), 
     &                          body_dpv(6), body_pv(6),
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
c Calculate the back-dated position of body (neglecting aberration)
c***********************************************************************

        call SPKAPP(body_id, time, 'J2000', obs_pv, 'LT', body_dpv, dt)
        body_time = time - dt
        call SPKSSB(body_id, body_time, 'J2000', body_pv)

c***********************************************************************
c Calculate the direction to the Sun at body
c***********************************************************************

        call SPKAPP(SUN_ID, body_time, 'J2000', body_pv, 'LT',
     &          sun_dpv, dt)

c***********************************************************************
c Calculate the phase angle
c***********************************************************************

        call VMINUS(body_dpv(1), obs_dp)
        phase = VSEP(sun_dpv(1), obs_dp)

        return
        end

c*******************************************************************************
