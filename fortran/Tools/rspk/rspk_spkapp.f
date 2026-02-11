c*******************************************************************************
c$ Component_name:
c       RSPK_SPKAPP
c$ Abstract:
c       Replaces the SPICE routine SPKAPP but allows for time offsets in moon
c       orbits.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PRIVATE, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_SPKAPP(body_id, time, epoch, obs_pv, aberr, body_dpv,
c                               dt)
c       integer                 body_id
c       double precision        time, obs_pv(6), body_dpv(6), dt
c       character*(*)           epoch, aberr
c$ Inputs:
c       See SPICE routine SPKAPP.
c$ Outputs:
c       See SPICE routine SPKAPP.
c$ Returns:
c       none
c$ Side_effects:
c       none
c$ Detailed_description:
c       This subroutine replaces the SPICE routine SPKAPP but allows for time
c       offsets in moon orbits.  See SPKAPP for more details.  Time shifts can
c       be specified via routine RSPK_SetShift().
c$ External_references:
c       SPICE Toolkit routines: SPKAPP, VSUB, VADD
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

        subroutine RSPK_SPKAPP(body_id, time, epoch, obs_pv, aberr,
     &          body_dpv, dt)

        implicit                none
        integer                 body_id
        double precision        time, obs_pv(6), body_dpv(6), dt
        character*(*)           epoch, aberr

        integer                 ishift
        double precision        planet_dpv(6), planet_dt, temp_dpv(6),
     &                          temp_dt, body_dt

        include                 'rspk_common.inc'


c Walk down list of time shifts
        do 100 ishift = 1, nshifts

c If body is found, then do all the hard work
            if (body_id .eq. shift_id(ishift)) then

c ...but do the single call if the time-shift happens to be zero
                if (shift_dt(ishift) .eq. 0.d0) goto 200

                call SPKAPP(planet_id, time + shift_dt(ishift), epoch,
     &                  obs_pv, aberr, planet_dpv, planet_dt)
                call SPKAPP(body_id,   time + shift_dt(ishift), epoch,
     &                  obs_pv, aberr, body_dpv, body_dt)
                call VSUB(body_dpv(1), planet_dpv(1), temp_dpv(1))
                call VSUB(body_dpv(4), planet_dpv(4), temp_dpv(4))
                temp_dt = body_dt - planet_dt

                call SPKAPP(planet_id, time, epoch,
     &                  obs_pv, aberr, planet_dpv, planet_dt)
                call VADD(temp_dpv(1), planet_dpv(1), body_dpv(1))
                call VADD(temp_dpv(4), planet_dpv(4), body_dpv(4))
                dt = temp_dt + planet_dt
                return
            end if
100     continue

c If the body is not found on the list or if the time-shift is zero,
c call the SPICE routine directly

200     continue
        call SPKAPP(body_id, time, epoch, obs_pv, aberr, body_dpv, dt)

        return
        end

c*******************************************************************************
