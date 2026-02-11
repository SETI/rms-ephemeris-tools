c*******************************************************************************
c$ Component_name:
c       RSPK_SetObs
c$ Abstract:
c       Enables the user to specify the coordinates of an observatory;
c       subsequent calls to RSPK Libarary routines will be corrected for the
c       observatory's offset from the center of the Earth.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_SetObs(lat, lon, alt)
c       real*8          lat, lon, alt
c$ Inputs:
c       lat             geodetic latitude of observatory (degrees).  Passing a
c                       value outside the range [-90,90] disables the
c                       observatory offset, so calculation apply to a
c                       theoretical observer at the senter of the Earth.
c       lon             east geodetic longitude of observatory (degrees).
c       alt             altitude of observatory (m, relative to an
c                       oblate spheroid model of the Earth's shape).
c$ Outputs:
c       none
c$ Returns:
c       none
c$ Side_effects:
c       The values passed to this routine are saved in a common /RSPK_COMMON/.
c$ Detailed_description:
c       This subroutine enables the user to specify the coordinates of an
c       observatory; subsequent calls to RSPK Libarary routines will be
c       corrected for the observatory's offset from the center of the Earth.
c
c       If this routine is not called first, or if it is called with a latitude
c       outside the range [-90,90], then the observatory offset is disabled; in
c       this case, RSPK routines return information for a theoretical observer
c       at the Earth's center.
c$ External_references:
c       SPICE toolkit routines: RPD
c$ Examples:
c       This call specifies the Goldstone observatory:
c               call RSPK_SetObs(35.314745d0, -116.88822583d0, 0.d0)
c
c       This call disables the observatory offset:
c               call RSPK_SetObs(999.d0, 0.d0, 0.d0)
c       (One could achieve the same effect by never calling RSPK_SetObs at all.)
c$ Error_handling:
c       None.  The SPICE toolkit error handling is in effect.
c$ Limitations:
c       The reference spheroid for the Earth is that of GRS 80.
c       WARNING: RSPK_LoadFiles must be called before this routine.
c       RSPK_LoadFiles sets the observer location back to Earth's center.
c$ Author_and_institution:
c       Mark R. Showalter
c       PDS Rings Node, NASA/Ames Research Center
c$ Version_and_date:
c       1.0: August 1996
c       1.1: January 1999
c$ Change_history:
c       1.1: changed to allow for observers other than Earth.
c*******************************************************************************

        subroutine RSPK_SetObs(lat, lon, alt)

        implicit                none
        double precision        lat, lon, alt

        include                 'rspk_common.inc'
        double precision        RPD

c Save observatory state in common
        obs_id = 399
        obs_is_set = (abs(obs_lat) .le. 90.d0)

c Convert latitude and longitude to radians
        obs_lat = lat * RPD()
        obs_lon = lon * RPD()

c Convert altitude to km
        obs_alt = alt / 1000.d0

        return
        end

c*******************************************************************************
c$ Component_name:
c       RSPK_SetObsId
c$ Abstract:
c       Enables the user to specify central body of an observation.  Subsequent
c       calls to RSPK Libarary routines will use the specified body ID rather
c       than the Earth.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_SetObsId(id)
c       integer         id
c$ Inputs:
c       id              SPICE body ID of the new observation point.  Use zero
c                       to reset to Earth's center.
c$ Outputs:
c       none
c$ Returns:
c       none
c$ Side_effects:
c       Common /RSPK_COMMON/ is modified.
c$ Detailed_description:
c       This subroutine enables the user to specify central body of an
c       observation.  Subsequent calls to RSPK Libarary routines will use the
c       specified body ID rather than the Earth.
c$ External_references:
c       none
c$ Examples:
c       This call specifies the Galileo spacecraft
c               call RSPK_SetObsId(-77)
c
c       This call resets the observer to Earth
c               call RSPK_SetObsId(0)
c       (One could achieve the same effect by never calling RSPK_SetObsId at
c       all.)
c$ Error_handling:
c       None.  The SPICE toolkit error handling is in effect.
c$ Limitations:
c       The reference spheroid for the Earth is that of Clark 1966.
c$ Author_and_institution:
c       Mark R. Showalter
c       PDS Rings Node, NASA/Ames Research Center
c$ Version_and_date:
c       1.0: January 1999
c$ Change_history:
c       none
c*******************************************************************************

        subroutine RSPK_SetObsId(id)

        implicit                none
        integer                 id

        include                 'rspk_common.inc'

c Save observatory body in common
        if (id .eq. 0) then
                obs_id = 399
        else
                obs_id = id
        end if

        obs_is_set = .FALSE.

        return
        end

c*******************************************************************************
c subroutine RSPK_ObsLoc(time, obs_pv)
c
c This internal subroutine is used by other RSPK Library routines to calculate
c the state of the Earth observatory at a specified time.  It uses the values
c specified by the user in RSPK_SetObs().
c
c Input:
c       time            ephemeris time, as returned by SPICE Toolkit routine
c                       UTC2ET.
c
c Output:
c       obs_pv          state of the observer (position and velocity) as handled
c                       by the SPICE tools.
c
c Note: The velocity of the observer is not used for any RSPK calculations.
c Hence the velocity returned is that of the Earth without a correction for the
c Earth's rotation.
c*******************************************************************************

        subroutine RSPK_ObsLoc(time, obs_pv)

        implicit                none
        double precision        time, obs_pv(6)

        include                 'rspk_common.inc'
        double precision        obs_dp(3), earth_mat(3,3)

c Use the GRS 80 reference spheroid
        integer                 EARTH_ID/399/

        double precision        EARTH_RAD, EARTH_FLAT
        parameter               (EARTH_RAD = 6378.137d0)
        parameter               (EARTH_FLAT = 1.d0 / 298.257222d0)

c Calculate the instantaneous position of Earth
        call SPKSSB(obs_id, time, 'J2000', obs_pv)

c Without an observatory, we're done
        if (.not. obs_is_set) return

c Calculate the observatory offset location as a 3-vector
        call GEOREC(obs_lon, obs_lat, obs_alt, EARTH_RAD, EARTH_FLAT,
     &              obs_dp)

c Rotate the offset to J2000 coordinates
        call BODMAT(EARTH_ID, time, earth_mat)
        call MTXV(earth_mat, obs_dp, obs_dp)

c Add it to the Earth center location in the state vector (leaving the
c velocity unchanged)
        call VADD(obs_pv(1), obs_dp, obs_pv(1))

        return
        end

c*******************************************************************************
