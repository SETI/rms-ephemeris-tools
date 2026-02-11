c*******************************************************************************
c$ Component_name:
c       RSPK_BODMAT
c$ Abstract:
c       Replaces the SPICE routine BODMAT but allows for time offsets in moon
c       orbits.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PRIVATE, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_BODMAT(body_id, time, matrix)
c       integer                 body_id
c       double precision        time, matrix(3,3)
c$ Inputs:
c       See SPICE routine BODMAT.
c$ Outputs:
c       See SPICE routine BODMAT.
c$ Returns:
c       none
c$ Side_effects:
c       none
c$ Detailed_description:
c       This subroutine replaces the SPICE routine BODMAT but allows for time
c       offsets in moon orbits.  See BODMAT for more details.  Time shifts can
c       be specified via routine RSPK_SetShift().
c$ External_references:
c       SPICE Toolkit routines: BODMAT
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
c$ Change_history:
c       none
c*******************************************************************************

        subroutine RSPK_BODMAT(body_id, time, matrix)

        implicit                none
        integer                 body_id
        double precision        time, matrix(3,3)

        integer                 ishift, i, j
        character*80            reporting
        logical*4               is_moon, success
        include                 'rspk_common.inc'

c Prep for missing frame, which happens a lot for small moons

        call ERRPRT('GET', reporting)

        is_moon = .FALSE.
        if (body_id .gt. 300 .and. body_id .lt. 999 .and.
     &      mod(body_id,100) .ne. 99) then
                is_moon = .TRUE.

                call ERRPRT('SET', 'NONE')
                call ERRACT('SET', 'RETURN')

                do i = 1, 3
                  do j = 1, 3
                    matrix(j,i) = 0.d0
                  end do
                end do
        end if

c Walk down list of time shifts
        do 100 ishift = 1, nshifts

c If body is found, apply time-shift and return
            if (body_id .eq. shift_id(ishift)) then
                call BODMAT(body_id, time + shift_dt(ishift), matrix)
                return
            end if
100     continue

c If the body is not found, call the SPICE routine directly

200     continue
        call BODMAT(body_id, time, matrix)

        if (.NOT. is_moon) return

c Reset error handling
        call RESET()
        call ERRPRT('SET', reporting)

c Check for success
        success = .FALSE.
        do i = 1, 3
          do j = 1, 3
            if (matrix(j,i) .ne. 0.d0) success = .TRUE.
          end do
        end do

        if (success) return

c At this point, we don't have a frame. If this is a moon, assume it is tidally
c locked and get the frame that way.

        call RSPK_BODMAT_from_orbit(body_id, time, matrix)
        return

        end

c*******************************************************************************

        subroutine RSPK_BODMAT_from_orbit(body_id, time, rotmat)

        implicit                none
        integer                 body_id
        double precision        time, rotmat(3,3)

        double precision        obs_pv(6), body_dpv(6), dt, body_time,
     &                          state(6)

        include                 'rspk_common.inc'

        call RSPK_ObsLoc(time, obs_pv)

c Calculate the time at the body
        call SPKAPP(body_id, time, 'J2000', obs_pv, 'LT',
     &              body_dpv, dt)
        body_time = time - dt

c The X-axis points toward the planet
c The Z-axis points toward the orbit pole, defined by X cross V, where V is the
c velocity of the planet relative to the moon.
c Uranus is reversed!

        call SPKEZ(planet_id, body_time, 'J2000', 'NONE', body_id,

     &             state, dt)

        if (planet_num .eq. 7) call VMINUS(state(4), state(4))

        call TWOVEC(state, 1, state(4), 2, rotmat)

        return
        end

c*******************************************************************************
