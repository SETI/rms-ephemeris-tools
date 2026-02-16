c*******************************************************************************
c logical function WWW_GetKeys(name, value)
c
c This FORTRAN-callable subroutine looks up the value of a keyword from a WWW
c form.  It returns a blank string if the keyword is undefined.  If the name
c matches the name from the previous call, it finds the value of the next
c keyword with the same name.
c
c Input:
c       name            keyword name.  If the name is blank, it simply resets
c                       and returns.
c
c Output:
c       value           next keyword value, or blank if the keyword was not
c                       found. 
c
c Return:               .TRUE. if the keyword was found; .FALSE. otherwise.
c*******************************************************************************

        logical function WWW_GetKeys(name, value)

        implicit        none
        character*(*)   name, value

        integer         index, WWW_Lookup

        character*256   prevname/' '/
        integer         start/0/
        save            prevname, start

c If the name is blank, initialize and return
        if (name .eq. ' ') then
            prevname = ' '
            start = 0
            WWW_GetKeys = .FALSE.
            value = ' '
            return
        end if

c If the name has changed, start at the beginning
        if (name .ne. prevname) then
            prevname = name
            start = 0
        end if

c Search for the next keyword with this name
        start = WWW_Lookup(name, start, value)

c If keyword was not found...
        if (start .eq. 0) then
            WWW_GetKeys = .FALSE.
            prevname = ' '
            start = 0
            return
        end if

c If keyword was found...
        WWW_GetKeys = .TRUE.
        return
        end

c*******************************************************************************
c logical function WWW_GetKey(name, value)
c
c This FORTRAN-callable subroutine looks up a single value of a keyword from a
c WWW form.  It returns a blank string if the keyword is undefined.
c
c Input:
c       name            keyword name
c
c Output:
c       value           keyword value, or blank if the sysmbol was not found.
c
c Return:               .TRUE. if the keyword was found; .FALSE. otherwise.
c*******************************************************************************

        logical function WWW_GetKey(name, value)

        implicit        none
        character*(*)   name, value

        logical         found, status, WWW_GetKeys
        character*256   test_value

c Return the _last_ value for this name
        found = .FALSE.
        value = ' '
        do while (.TRUE.)
            status = WWW_GetKeys(name, test_value)
            if (.not. status) then
                WWW_GetKey = found
                return
            end if

            found = .TRUE.
            value = test_value
        end do

        end

c*******************************************************************************
c logical function WWW_GetKeysUnsanitized(name, value)
c
c This FORTRAN-callable subroutine looks up the value of a keyword from a WWW
c form.  It returns a blank string if the keyword is undefined.  If the name
c matches the name from the previous call, it finds the value of the next
c keyword with the same name.
c
c Input:
c       name            keyword name.  If the name is blank, it simply resets
c                       and returns.
c
c Output:
c       value           next keyword value, or blank if the keyword was not
c                       found. 
c
c Return:               .TRUE. if the keyword was found; .FALSE. otherwise.
c*******************************************************************************

        logical function WWW_GetKeysUnsanitized(name, value)

        implicit        none
        character*(*)   name, value

        integer         index, WWW_LookupUnsanitized

        character*256   prevname/' '/
        integer         start/0/
        save            prevname, start

c If the name is blank, initialize and return
        if (name .eq. ' ') then
            prevname = ' '
            start = 0
            WWW_GetKeysUnsanitized = .FALSE.
            value = ' '
            return
        end if

c If the name has changed, start at the beginning
        if (name .ne. prevname) then
            prevname = name
            start = 0
        end if

c Search for the next keyword with this name
        start = WWW_LookupUnsanitized(name, start, value)

c If keyword was not found...
        if (start .eq. 0) then
            WWW_GetKeysUnsanitized = .FALSE.
            prevname = ' '
            start = 0
            return
        end if

c If keyword was found...
        WWW_GetKeysUnsanitized = .TRUE.
        return
        end

c*******************************************************************************
c logical function WWW_GetKeyUnsanitized(name, value)
c
c This FORTRAN-callable subroutine looks up a single value of a keyword from a
c WWW form.  It returns a blank string if the keyword is undefined.
c
c Input:
c       name            keyword name
c
c Output:
c       value           keyword value, or blank if the sysmbol was not found.
c
c Return:               .TRUE. if the keyword was found; .FALSE. otherwise.
c*******************************************************************************

        logical function WWW_GetKeyUnsanitized(name, value)

        implicit        none
        character*(*)   name, value

        logical         found, status, WWW_GetKeysUnsanitized
        character*256   test_value

c Return the _last_ value for this name
        found = .FALSE.
        value = ' '
        do while (.TRUE.)
            status = WWW_GetKeysUnsanitized(name, test_value)
            if (.not. status) then
                WWW_GetKeyUnsanitized = found
                return
            end if

            found = .TRUE.
            value = test_value
        end do

        end

c*******************************************************************************
