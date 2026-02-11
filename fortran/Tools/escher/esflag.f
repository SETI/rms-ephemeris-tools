c This returns the current value of the "drawn" flag and then clears it.  By
c calling this routine before and after EUBODY, a program can determine if any
c part of a particular moon is visible.
c
c Mark Showalter 12/10/96

	logical function ESFLAG(dummy)
	integer		dummy

	include		'escomm.inc'

	ESFLAG = drawn
	drawn = .FALSE.

	return
	end
