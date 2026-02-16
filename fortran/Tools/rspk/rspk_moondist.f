c*******************************************************************************
c$ Component_name:
c       RSPK_MoonDist
c$ Abstract:
c       Evaluates the projected angular offsets of a set of moons from the
c       planet axis as observed at a specified time.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       subroutine function RSPK_MoonDist(time, nmoons, moon_ids, offsets, limb)
c       double precision        time, offsets(*)
c       integer                 nmoons, moon_ids(*)
c$ Inputs:
c       time            ephemeris time of the observation at Earth (as returned
c                       by SPICE routine UTC2ET).
c       nmoons          number of moons for which to calculate offset angles.
c       moon_ids(1..nmoons) moon body IDs as used in the SPICE toolkit.
c$ Outputs:
c       offset(1..nmoons) offset angles in radians.
c       limb            distance of equatorial limb from center of planet in
c                       radians.
c$ Returns:
c       none
c$ Side_effects:
c       none
c$ Detailed_description:
c       This function evaluates the projected angular offsets of a set of moons
c       from the planet axis as observed at a specified time.  Positive offsets
c       are on the "morning" ansa (in general, higher right ascension) and
c       negative offsets are on the "evening" ansa.
c
c       Returned values apply to either the Earth's center or to an observatory,
c       depending on whether/how RSPK_SetObs() has been called first.
c$ External_references:
c       SPICE Toolkit routines: SPKAPP, RECRAD
c       RSPK Toolkit routines: RSPK_ObsLoc, RSPK_SPKAPP
c$ Examples:
c       This fragment of code prints out the offset of Mimas (601) from Saturn
c       in arcsec.
c
c       call UTC2ET('1995-11-19 12:00:00', time)
c       call RSPK_MoonDist(time, 1, 601, offset)
c       write(*,*) 'Mimas offset (arcsec) =', offset * DPR() * 3600.d0
c$ Error_handling:
c       None.  The SPICE toolkit error handling is in effect.
c$ Limitations:
c       None.
c$ Author_and_institution:
c       Mark R. Showalter
c       PDS Rings Node, NASA/Ames Research Center
c$ Version_and_date:
c       1.0: August 1996
c       1.1: May 2001
c       1.2: September 2002
c$ Change_history:
c       1.1: MRS corrected arcsin failure for argument > 1.
c       1.2: Corrected for observer point not infinitely far away.
c*******************************************************************************

        subroutine RSPK_MoonDist(time, nmoons, moon_ids, offsets, limb)

        implicit                none
        double precision        time, offsets(*), limb
        integer                 nmoons, moon_ids(*)

        integer                 i, nradii
        double precision        obs_pv(6), planet_dpv(6), dt,
     &                          rotmat(3,3), pole(3), moon_dpv(6),
     &                          vector(3), radii(3)
        double precision        VNORM
        include                 'rspk_common.inc'

c Calculate the instantaneous position of the observer
        call RSPK_ObsLoc(time, obs_pv)

c Calculate the back-dated position of planet (neglecting aberration)
        call SPKAPP(planet_id, time, 'J2000', obs_pv, 'LT',
     &                  planet_dpv, dt)

c Calculate pole of planet
        call BODMAT(planet_id, time-dt, rotmat)
        call VPACK(rotmat(3,1), rotmat(3,2), rotmat(3,3), pole)

        if (planet_num .eq. 7) call VMINUS(pole, pole)

c Generate a rotation matrix J2000 --> viewer frame
c The viewer frame is defined by an X-axis along the line of sight
c an XZ plane including the planet pole.
        call TWOVEC(planet_dpv(1), 1, pole, 3, rotmat)

c For each moon, evaluate the offset angle
        do 100 i = 1, nmoons
                call RSPK_SPKAPP(moon_ids(i), time, 'J2000', obs_pv,
     &                  'LT', moon_dpv, dt)
                call MXV(rotmat, moon_dpv(1), vector)
                offsets(i) = atan2(vector(2), vector(1))
100     continue

c Evaluate the limb
        call BODVAR(planet_id, 'RADII', nradii, radii)
        limb = asin(radii(1) / VNORM(planet_dpv(1)))

        return
        end

c*******************************************************************************
