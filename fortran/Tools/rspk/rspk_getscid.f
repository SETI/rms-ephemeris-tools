c*******************************************************************************
c$ Component_name:
c       RSPK_GetSCID
c$ Abstract:
c       Returns the SPICE ID for a specified spacecraft.
c$ Keywords:
c       RSPK, SPICE
c       FORTRAN, PUBLIC, SUBROUTINE
c$ Declarations:
c       integer function RSPK_GetSCID(name)
c       character*(*)   name
c$ Inputs:
c       name            name or ID for given spacecraft. For example, 'VG1',
c                       'Voyager 1', 'VOYAGER 1'
c$ Outputs:
c       none
c$ Returns:
c       SPICE ID value.
c$ Side_effects:
c       none
c$ Detailed_description:
c       This subroutine returns the SPICE ID for a spacecraft based on its
c       name or ID.
c$ External_references:
c       None.
c$ Examples:
c       None.
c$ Error_handling:
c       None. 
c$ Limitations:
c       This needs to be updated with the names of the latest SPK files as they
c       become available.
c$ Author_and_institution:
c       Mark R. Showalter
c       PDS Rings Node, SETI Institute
c$ Version_and_date:
c       1.0: August 2005
c       1.1: January 2010: Europa Orbiter added
c       1.2: June 2021: Juno added, Europa Orbiter changed to Europa Clipper
c$ Change_history:
c*******************************************************************************

        integer function RSPK_GetSCID(name)

        implicit        none
        character*(*)   name

        include         'rspk_common.inc'
        integer         i
        character       upper*100, c*1

c Raise string to upper case
        do i = 1, min(len(name), len(upper))
            c = name(i:i)
            if (c .ge. 'a' .and. c .le. 'z') then
                upper(i:i) = char(ichar(c) + ichar('A') - ichar('a'))
            else
                upper(i:i) = c
            end if
        end do

c Voyager 1 and 2
        if (index(upper,'VG')  .gt. 0 .or.
     &      index(upper,'VOY') .gt. 0) then
                if (index(upper,'1') .gt. 0) then
                    RSPK_GetSCID = -31
                else
                    RSPK_GetSCID = -32
                end if

c Galileo
        else if (index(upper,'GAL') .gt. 0 .or.
     &           index(upper,'GLL') .gt. 0) then
                    RSPK_GetSCID = -77

c Cassini
        else if (index(upper,'CAS') .gt. 0 .or.
     &           index(upper,'CS')  .gt. 0) then
                        if (obs_id .eq. -90) then
                            RSPK_GetSCID = -90
                        else
                            RSPK_GetSCID = -82
                        end if          

c New Horizons
        else if (index(upper,'NEW') .gt. 0 .or.
     &           index(upper,'NH')  .gt. 0) then
                        RSPK_GetSCID = -98

c Europa Clipper
        else if (index(upper,'EUROPA') .gt. 0 .or.
     &           index(upper,'CLIPPER') .gt. 0 .or.
     &           upper .eq. 'EC') then
                        RSPK_GetSCID = -159


c Juno
        else if (upper .eq. 'JUNO') then
                RSPK_GetSCID = -61

        end if

        return
        end

c*******************************************************************************
