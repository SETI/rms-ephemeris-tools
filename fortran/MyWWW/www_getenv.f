c*******************************************************************************
c logical function WWW_GetEnv(name, value)
c
c This subroutine returns the value of an environment variable.
c
c Input:
c       name            name of variable.
c
c Output:
c       value           value of environment variable. Blank if not found.
c
c Return:               .TRUE. if environment variable was found.
c*******************************************************************************

        logical function www_getenv(name, value)

        implicit        none
        character*(*)   name, value

        integer         MAXCHARS
        parameter       (MAXCHARS = 256)

        integer         i, parens
        character*1     c, test
        character*256   raw_value

        character*(*)   DIGITS, LOWER, UPPER, PUNC, VALIDATED
        parameter       (DIGITS = '0123456789')
        parameter       (LOWER  = 'abcdefghijklmnopqrstuvwxyz')
        parameter       (UPPER  = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
        parameter       (PUNC   = ' .,;:+\-*/=()_''&')
        parameter       (VALIDATED = DIGITS // LOWER // UPPER // PUNC)

c Generate insertion string
        call GETENV(name, raw_value)

c Sanitize
        parens = 0
        value = ''
        do i = 1, min(MAXCHARS, len(value))
            c = raw_value(i:i)

            if (index(VALIDATED,c) .eq. 0) c = '_'

            if (c .eq. '(') parens = parens + 1
            if (c .eq. ')') parens = parens - 1

            if (parens .lt. 0) then
                parens = 0
                c = '_'
            end if

c           An ampersand is only allowed if followed by a blank
            if (c .eq. '&' .and. i .ne. MAXCHARS) then
                test = raw_value(i+1:i+1)
                if (test .ne. ' ') c = '_'
            end if

            value(i:i) = c
        end do
201     continue

        www_getenv = (value .eq. ' ')

        return
        end

c*******************************************************************************
