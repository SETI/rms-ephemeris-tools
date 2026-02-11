c*******************************************************************************
c$ Component_name:
c       RSPK_BodyRaDec
c$ Abstract:
c       Returns the observed J2000 right ascension and declination of a body at
c       a specified time.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       subroutine RSPK_BodyRaDec(time, body_id, ra, dec)
c       double precision        time, ra, dec
c       integer                 body_id
c$ Inputs:
c       time            ephemeris time of the observation at Earth (as returned
c                       by SPICE routine UTC2ET).
c       body_id         body ID as used in the SPICE toolkit.
c$ Outputs:
c       ra              right ascension of the body's center (radians).
c       dec             declination of the body's center (radians).
c$ Returns:
c       none
c$ Side_effects:
c       none
c$ Detailed_description:
c       This subroutine returns the observed J2000 right ascension and
c       declination of a body in the Saturn system at a specified time.
c
c       Returned values apply to either the Earth's center or to an observatory,
c       depending on whether/how RSPK_SetObs() has been called first.
c
c       Note: Body coordinates are given in the Solar System barycenter frame;
c       they are not corrected for stellar aberration.  This means that
c       coordinates should be correct relative to the cataloged locations of
c       background stars.
c$ External_references:
c       SPICE Toolkit routines: RECRAD
c       RSPK Toolkit routines: RSPK_ObsLoc, RSPK_SPKAPP
c$ Examples:
c       This fragment of code prints out the RA and dec of Saturn in degrees:
c
c       call UTC2ET('1995-11-19 12:00:00', time)
c       call RSPK_BodyRaDec(time, 699, ra, dec)
c       write(*,*) ra * DPR, dec * DPR
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

        subroutine RSPK_BodyRaDec(time, body_id, ra, dec)

        implicit                none
        double precision        time, ra, dec
        integer                 body_id

        double precision        obs_pv(6), body_dpv(6), dt, range


c Calculate the instantaneous position of the observer
        call RSPK_ObsLoc(time, obs_pv)

c Calculate the back-dated position of the body (neglecting aberration)
        call RSPK_SPKAPP(body_id, time, 'J2000', obs_pv, 'LT',
     &          body_dpv, dt)

c Calculate the body RA/dec in the Solar System barycenter frame
        call RECRAD(body_dpv(1), range, ra, dec)

        return
        end

c*******************************************************************************
