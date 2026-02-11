c*******************************************************************************
c$ Component_name:
c       RSPK_LoadFiles
c$ Abstract:
c       Initializes the RSPK library by loading the necessary SPICE files.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       logical function RSPK_LoadFiles(lunit, iplanet, iversion)
c       integer         lunit, iplanet, iversion
c       character*(*)   path
c$ Inputs:
c       lunit           logical unit to use temporarily.
c       iplanet         4=Mars, 5=Jupiter, 6=Saturn, 7=Uranus, 8=Neptune.
c       iversion        ephemeris version number or 0 for latest.
c$ Outputs:
c       none
c$ Returns:
c       .TRUE. if the ephemeris could be loaded; .FALSE. otherwise.
c$ Side_effects:
c       The SPICE files are loaded into memory.  Information is stored in common
c       /RSPK_COMMON/.
c$ Detailed_description:
c       This subroutine initializes the RSPK library by loading all of the
c       necessary SPICE files for RSPK geometry calculations of a given planet. 
c       It must be called prior to any other RSPK library calls (except perhaps
c       RSPK_SetObs).  Subsequent calls do nothing.
c$ External_references:
c       SPICE toolkit routines: CLPOOL, LDPOOL, SPKLEF
c$ Examples:
c       None.
c$ Error_handling:
c       None.  The SPICE toolkit error handling is in effect.
c$ Limitations:
c       This needs to be updated with the names of the latest SPK files as they
c       become available.
c$ Author_and_institution:
c       Mark R. Showalter
c       PDS Rings Node, NASA/Ames Research Center
c$ Version_and_date:
c       1.0: September 1996
c       1.1: February 1997
c       1.2: January 1999
c       1.3: August 1999
c       1.4: January 2003
c       1.5: August 2005
c       1.6: January 2010
c$ Change_history:
c       1.1: Added Uranus and Neptune kernels.
c       1.2: Added new ephemeris options and expanded date ranges.
c       1.3: Added Mars options.
c       1.4: Added Phoebe ephemeris.
c       1.5: Revised to read from configuration file.
c       1.6: Revised to user FURNSH instead of LDPOOL and SPKLEF.
c*******************************************************************************

        logical function RSPK_LoadFiles(lunit, iplanet, iversion)

        implicit        none
        integer         lunit, iplanet, iversion

        include         'rspk_common.inc'

        integer         p, v, load_version
        logical         loaded
        character*256   filename

c Anticipate failure
        RSPK_LoadFiles = .FALSE.

c Make sure second and subsequent calls are compatible
        if (planet_num .ne. 0 .and. iplanet .ne. planet_num) return

c Load the kernel pool if necessary
        if (.not. pool_loaded) then
            call FURNSH(SPICE_PATH // 'leapseconds.ker')
            call FURNSH(SPICE_PATH // 'p_constants.ker')

            pool_loaded = .TRUE.
        end if

c Open the configuration file
        open (lunit, file=DATA_PATH // 'SPICE_planets.txt',
     &        status='old')

c Find the matching planet and version
        load_version = iversion
        loaded = .FALSE.
100     continue
            read(lunit, *, end=101) p, v, filename

c       If version is zero, match whatever we find first
            if (load_version .eq. 0 .and. p .eq. iplanet) then
                load_version = v
            end if

c       Load planet ephemeris files
            if (p .eq. iplanet .and. v .eq. load_version) then
                call FURNSH(SPICE_PATH // filename)
                loaded = .TRUE.
            end if

        goto 100
101     continue

        close(lunit)

c Make sure files have been loaded successfuly
        if (.not. loaded) return

c Save information about load
        planet_num = iplanet
        planet_id  = iplanet*100 + 99

        RSPK_LoadFiles = .TRUE.

        nshifts = 0

        return
        end

c*******************************************************************************

        block data RSPK_common_init_block

        include 'rspk_common.inc'

        data planet_num    /       0 /
        data planet_id     /       0 /
        data pool_loaded   / .FALSE. /

        data obs_id        /     399 /
        data obs_is_set    / .FALSE. /

        data nshifts       /       0 /

        end

c*******************************************************************************

