c*******************************************************************************
c$ Component_name:
c       RSPK_Conjunc
c$ Abstract:
c       Returns the angular distance between two bodies as seen from Earth.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_Conjunc(time, body1, body2, angle)
c       double precision        time, angle
c       integer                 body1, body2
c$ Inputs:
c       time            ephemeris time of the observation at Earth (as returned
c                       by SPICE routine UTC2ET).
c       body1_id, body2_id
c                       body IDs as used in the SPICE toolkit.
c$ Outputs:
c       angle           angular distance between the two bodies as seen from
c                       Earth, in radians.
c$ Returns:
c       none
c$ Side_effects:
c       none
c$ Detailed_description:
c       This subroutine returns the angular distance between two bodies as seen
c       from Earth at a given instant.
c$ External_references:
c       SPICE Toolkit routines: VSEP
c       RSPK Toolkit routines: RSPK_ObsLoc, RSPK_SPKAPP
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
c       none
c*******************************************************************************

        subroutine RSPK_Conjunc(time, body1_id, body2_id, angle)

        implicit                none
        double precision        time, angle
        integer                 body1_id, body2_id

        double precision        obs_pv(6), body1_dpv(6), body2_dpv(6),
     &                          dt, VSEP

c Calculate the instantaneous position of the observer
        call RSPK_ObsLoc(time, obs_pv)

c Calculate the back-dated position of body #1 (including aberration)
        call RSPK_SPKAPP(body1_id, time, 'J2000', obs_pv, 'LT+S',
     &          body1_dpv, dt)

c Calculate the back-dated position of body #2 (including aberration)
        call RSPK_SPKAPP(body2_id, time, 'J2000', obs_pv, 'LT+S',
     &          body2_dpv, dt)

c Calculate the angular separation of the vectors
        angle = VSEP(body1_dpv(1), body2_dpv(1))

        return
        end

c*******************************************************************************
