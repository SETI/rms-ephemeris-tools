c*******************************************************************************
c$ Component_name:
c       RSPK_SetShift
c$ Abstract:
c       Applies a fixed time shift to the orbit of a moon.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_SetShift(body_id, dt)
c       integer                 body_id
c       double precision        dt
c$ Inputs:
c       body_id         id of moon as defined in SPICE toolkit.
c       dt              time shift to be applied, positive if the moon is to
c                       lead its ephemeris.
c$ Outputs:
c       none
c$ Returns:
c       none
c$ Side_effects:
c       Time shift information is stored in common /RSPK_COMMON/.
c$ Detailed_description:
c       This subroutine applies a fixed time shift to the orbit of a moon.
c$ External_references:
c       none
c$ Examples:
c       This call applies a 2778-second lag to the orbit of Prometheus:
c               call RSPK_SetShift(616, -2778.d0)
c$ Error_handling:
c       If the limit in the number of time-shifted bodies is reached, this
c       routine prints an error and aborts.  This is unlikely to happen since
c       the current limit exceeds the number of moons of any planet.
c$ Limitations:
c       Only 20 bodies may be time-shifted, unless the parameter MAXSHIFTS is
c       changed in file "rspk_common.inc".
c$ Author_and_institution:
c       Mark R. Showalter
c       PDS Rings Node, NASA/Ames Research Center
c$ Version_and_date:
c       1.0: August 1996
c$ Change_history:
c       none
c*******************************************************************************

        subroutine RSPK_SetShift(body_id, dt)

        implicit                none
        integer                 body_id
        double precision        dt

        integer                 ishift
        include                 'rspk_common.inc'

c Update time shift if body id is already in list
        do 100 ishift = 1, nshifts
                if (body_id .eq. shift_id(ishift)) then
                        shift_dt(ishift) = dt
                        return
                end if
100     continue

c Otherwise, add a new entry at end of list
        if (nshifts .ge. MAXSHIFTS) then
                write(*,*) 'Number of moon orbit time shifts ' //
     &                     'exceeded in RSPK_SetShift()'
                stop
        end if

        nshifts = nshifts + 1
        shift_id(nshifts) = body_id
        shift_dt(nshifts) = dt

        return
        end

c*******************************************************************************
