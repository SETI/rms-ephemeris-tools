c*******************************************************************************
c$ Component_name:
c       RSPK_LimbRad
c$ Abstract:
c       Calculates the radius and projected angular radius of a planet.
c$ Keywords:
c       SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_LimbRad(time, rkm, rradians)
c       double precision        time, rkm, rradians
c$ Inputs:
c       time            ephemeris time of the observation, as returned by SPICE
c                       routine UTC2ET.
c$ Outputs:
c       rkm             planet radius (km).
c       rradians        projected planet radius (radians).
c$ Returns:
c       none
c$ Side_effects:
c       none
c$ Detailed_description:
c       This subroutine returns radius and projected angular radius of a planet.
c$ External_references:
c       SPICE toolkit, RSPK toolkit.
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

        subroutine RSPK_LimbRad(time, rkm, rradians)

        implicit                none
        double precision        time, rkm, rradians

        include                 'rspk_common.inc'

        integer                 nradii
        double precision        dt, planet_time, obs_pv(6),
     &                          planet_dpv(6), planet_pv(6), radii(3)
        double precision        VNORM

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
c Calculate radii
c***********************************************************************

c Look up radius of planet
        call BODVAR(planet_id, 'RADII', nradii, radii)

        rkm = radii(1)
        rradians = radii(1) / VNORM(planet_dpv(1))

        return
        end

c*******************************************************************************
