c This subroutine moves the current point to the end of the last line
c segment "stroked".
c
c Mark Showalter 2/24/95

	subroutine ESMOVE

	character*40	moveto
	integer		LASTNB

	include		'escomm.inc'

	call OPAIRI(' ', xsave, ' ', ysave, ' M', moveto)
	write(outuni, FMT='(A)') moveto(2:LASTNB(moveto))

	return
	end
