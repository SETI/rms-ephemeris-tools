c This subroutine enables a calling program to set the line width in
c points.
c
c Mark Showalter 11/15/96

	subroutine ESLWID(points)
	real*8		points

	integer		width

	integer		MINWIDTH
	parameter	(MINWIDTH = 5)

	integer		oldwidth/ MINWIDTH /
	save		oldwidth

	include		'escomm.inc'


	width = max(nint(points * 10.d0), MINWIDTH)

	if (width .eq. oldwidth) return

	write(outuni, 10) width
10	format(i3, ' setlinewidth')

	oldwidth = width

	return
	end
