c This subroutine enables a calling program to write arbitrary
c text into the Postscript file.
c
c Mark Showalter 2/24/95

	subroutine ESWRIT(string)
	character*(*)	string

	include 	'escomm.inc'

	write(outuni, 10) string
10	format(a)

	return
	end
