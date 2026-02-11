c This subroutine enables a calling program to set the file name used for
c ESCHER output.
c
c Mark Showalter 1/9/95
c Updated 5/16/01 to avoid initializations in commons.

	subroutine ESFILE(filename, creator1, fonts1)
	character*(*)	filename, creator1, fonts1

	include		'escomm.inc'

	outfil = filename
	creator = creator1
	fonts = fonts1

c Initialize other fields in common
	outuni = 0
	drawn = .FALSE.

	return
	end

