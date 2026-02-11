c*******************************************************************************
c subroutine WWW_Tempfile(template, filename)
c
c This subroutine generates a temporary file name from the date and process ID.
c
c Input:
c       template        file name template containing "*". If the star is not
c                       found, it inserts the id string before the dot.
c
c Output:
c       filename        filename with date and process ID inserted. No check is
c                       made to confirm the output string has adequate length.
c
c Return:               none
c*******************************************************************************

        subroutine      www_tempfile(template, filename)

        implicit        none
        character*(*)   template, filename

        integer         istar, idot, last, i1, i2, dmy(3)
        integer         lastnb, GETPID
        character*11    string

c Figure out where to place insertion of date and process ID
        istar = index(template, '*')
        idot  = index(template, '.')
        last  = lastnb(template)

        if (istar .gt. 0) then
                i1 = istar - 1
                i2 = istar + 1
        else if (idot .gt. 0) then
                i1 = idot - 1
                i2 = idot
        else
                i1 = lastnb(template)
                i2 = i1 + 1
        end if

c Generate insertion string
        call IDATE(dmy)
        write(string,10) mod(dmy(3),100), dmy(2), dmy(1),
     &                   mod(GETPID(), 10000)
10      format(3i2.2, '_', i4.4)

c Combine the result
        filename = template(1:i1) // string // template(i2:)

        return
        end

c*******************************************************************************
