c*******************************************************************************
c$ Component_name:
c       RSPK_AntiSun
c$ Abstract:
c       Returns the anti-Sun RA and dec
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_AntiSun(time, body_id, ra, dec)
c       double precision        time, ra, dec
c       integer                 body_id
c$ Inputs:
c       time            ephemeris time of the observation, as returned by SPICE
c                       routine UTC2ET.
c       body_id         body ID as used in the SPICE toolkit.
c$ Outputs:
c       ra              right ascension of the body's center (radians).
c       dec             declination of the body's center (radians).
c$ Returns:
c       none
c$ Side_effects:
c       none
c$ Detailed_description:
c       This subroutine returns the anti-Sun RA and dec for observations of a
c       particular body.
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
c       PDS RMS Node, SETI Institute
c$ Version_and_date:
c       1.0: July 2021
c$ Change_history:
c       none
c*******************************************************************************

        subroutine RSPK_AntiSun(time, body_id, ra, dec)

        implicit                none
        double precision        time, ra, dec
        integer                 body_id

        double precision        dt, planet_time, obs_pv(6), range,
     &                          planet_dpv(6), planet_pv(6), sun_dpv(6)
        include                 'rspk_common.inc'

        integer                 i

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
c Return the anti-solar direction
c***********************************************************************

c Calculate the body RA/dec in the Solar System barycenter frame
        do i = 1, 6
            sun_dpv(i) = -sun_dpv(i)
        end do

        call RECRAD(sun_dpv(1), range, ra, dec)

        return
        end

c*******************************************************************************
