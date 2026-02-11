c*******************************************************************************
c integer function WWW_Lookup(name, index, value)
c
c This FORTRAN-callable subroutine looks up a symbol and returns its value as a
c character string.  It returns a blank string if the symbol is undefined.
c
c Input:
c       symbol          symbol name
c       start           starting index of value; 0 for first.
c
c Output:
c       value           symbol value, or blank if the symbol was not found.
c
c Return:               index to begin next search
c
c Modified 3/30/2013 to sanitize strings--MRS.
c Revised 8/15/2022--MRS.
c*******************************************************************************

        integer function WWW_Lookup(name, start, value)
        character*(*)   name, value
        integer         start

        integer         MAXCHARS
        parameter       (MAXCHARS = 256)

        integer         i, j, next, LASTNB, WWW_GetParam
        byte            cname(MAXCHARS), cvalue(MAXCHARS), temp
        character*1     c

c Copy the symbol name into a null-terminated byte string
        do i = 1, LASTNB(name)
                if (i .ge. MAXCHARS) goto 101
                cname(i) = ichar(name(i:i))
        end do
101     continue
        cname(i) = 0

c Look up the symbol via the C Library function getenv
        next = WWW_GetParam(cname, start, cvalue, MAXCHARS)

c Copy the returned string to the proper destination, while sanitizing
        j = 1
        do i = 1, MAXCHARS
            temp = cvalue(i)
            if (temp .eq. 0) goto 201
            if (i .gt. len(value)) goto 201
            if (j .gt. len(value)) goto 201

            c = char(temp)

            if (c .eq. '<') then
                value(j:j+3) = '&lt;'
                j = j + 4
            else if (c .eq. '>') then
                value(j:j+3) = '&gt;'
                j = j + 4
            else
                value(j:j) = c
                j = j + 1
            end if
        end do
201     continue
        if (j .le. len(value)) value(j:) = ' '

        WWW_Lookup = next
        return
        end

c*******************************************************************************
c integer function WWW_LookupUnsanitized(name, index, value)
c
c This FORTRAN-callable subroutine looks up a symbol and returns its value as a
c character string.  It returns a blank string if the symbol is undefined.
c
c Input:
c       symbol          symbol name
c       start           starting index of value; 0 for first.
c
c Output:
c       value           symbol value, or blank if the symbol was not found.
c
c Return:               index to begin next search
c*******************************************************************************

        integer function WWW_LookupUnsanitized(name, start, value)
        character*(*)   name, value
        integer         start

        integer         MAXCHARS
        parameter       (MAXCHARS = 256)

        integer         i, j, next, LASTNB, WWW_GetParam
        byte            cname(MAXCHARS), cvalue(MAXCHARS), temp
        character*1     c

c Copy the symbol name into a null-terminated byte string
        do i = 1, LASTNB(name)
                if (i .ge. MAXCHARS) goto 101
                cname(i) = ichar(name(i:i))
        end do
101     continue
        cname(i) = 0

c Look up the symbol via the C Library function getenv
        next = WWW_GetParam(cname, start, cvalue, MAXCHARS)

c Copy the returned string to the proper destination, while sanitizing
        j = 1
        do i = 1, MAXCHARS
            temp = cvalue(i)
            if (temp .eq. 0) goto 201
            if (i .gt. len(value)) goto 201
            if (j .gt. len(value)) goto 201

            c = char(temp)

C           if (c .eq. '<') then
C               value(j:j+3) = '&lt;'
C               j = j + 4
C           else if (c .eq. '>') then
C               value(j:j+3) = '&gt;'
C               j = j + 4
C           else
                value(j:j) = c
                j = j + 1
C            end if
        end do
201     continue
        if (j .le. len(value)) value(j:) = ' '

        WWW_LookupUnsanitized = next
        return
        end

c*******************************************************************************
