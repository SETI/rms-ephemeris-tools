c*******************************************************************************
c$ Component_name:
c       RSPK_LoadSC
c$ Abstract:
c       Initializes the RSPK library by loading the necessary SPICE files for a
c       spacecraft and planet.  It also defines the observer as the spacecraft.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       logical function RSPK_LoadSC(lunit, scid, iplanet, iversion, setobs)
c       integer         lunit, iplanet, iversion
c       character*(*)   scid
c       logical         setobs
c$ Inputs:
c       lunit           logical unit to use temporarily.
c       scid            'VG1' for Voyager 1; 'VG2' for Voyager 2; 'GLL' for
c                       Galileo; 'CAS' for Cassini; NH for New Horizons.
c       iplanet         5=Jupiter, 6=Saturn, 7=Uranus, 8=Neptune.
c       iversion        ephemeris version number or 0 for latest.
c       setobs          .TRUE. to set this spacecraft as the observation point.
c$ Outputs:
c       none
c$ Returns:
c       .TRUE. if the ephemeris could be loaded; .FALSE. otherwise.
c$ Side_effects:
c       The SPICE files are loaded into memory.  Information is stored in common
c       /RSPK_COMMON/.
c$ Detailed_description:
c       This subroutine initializes the RSPK library by loading all of the
c       necessary SPICE files for RSPK geometry calculations of a given
c       spacecraft at a given planet.  It also defines that spacecraft as the
c       observer.  It must be called prior to any other RSPK library calls
c       (except perhaps RSPK_LoadFiles).  Subsequent calls do nothing.
c$ External_references:
c       SPICE toolkit routines: LASTNB, CLPOOL, LDPOOL, SPKLEF
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
c       1.0: December 2001
c       1.1: October 2003
c       1.2: August 2005
c       1.3: January 2010
c$ Change_history:
c       1.1: Added New Horizons
c       1.2: Revised to read from configuration file, option for setting
c            observation point.
c       1.3: Revised to use FURNSH instead of LDPOOL and SPKLEF.
c*******************************************************************************

        logical function RSPK_LoadSC(lunit, scid, iplanet, iversion,
     &                               setobs)

        implicit        none
        integer         lunit, iplanet, iversion
        character*(*)   scid
        logical         setobs

        include         'rspk_common.inc'

        integer         p, v, id, load_version
        logical         loaded
        character*4     name
        character*256   filename

c Anticipate failure
        RSPK_LoadSC = .FALSE.

c Make sure second and subsequent calls are compatible
        if (planet_num .ne. 0 .and. iplanet .ne. planet_num) return

c Load the kernel pool if necessary
        if (.not. pool_loaded) then
            call FURNSH(SPICE_PATH // 'leapseconds.ker')
            call FURNSH(SPICE_PATH // 'p_constants.ker')

            pool_loaded = .TRUE.
        end if

c Open the configuration file
        open (lunit, file=DATA_PATH // 'SPICE_spacecraft.txt',
     &        status='old')

c Find the matching spacecraft, planet and version
        load_version = iversion
        loaded = .FALSE.
100     continue
            read(lunit, *, end=101) name, p, v, id, filename

c       If version is zero, match whatever we find first
            if (name .eq. scid .and. p .eq. iplanet .and.
     &          load_version .eq. 0) then
                    load_version = v
            end if

c       Load spacecraft ephemeris files
            if (name .eq. scid .and. p .eq. iplanet .and.
     &          v .eq. load_version) then
                    call FURNSH(SPICE_PATH // filename)
                    loaded = .TRUE.

c               Save SPICE id of observer
                    if (setobs) obs_id = id
            end if

        goto 100
101     continue

        close(lunit)

c Make sure files have been loaded successfuly
        if (.not. loaded) return

c Save information about load
        planet_num = iplanet
        planet_id  = iplanet*100 + 99

        RSPK_LoadSC = .TRUE.

        return
        end

c*******************************************************************************
