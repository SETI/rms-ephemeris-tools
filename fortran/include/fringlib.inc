c<HTML><HEAD><TITLE> fringlib.inc </TITLE></HEAD><BODY><PRE>
c*******************************************************************************
c fringlib.inc -- Include file for standard RingLib features, FORTRAN version
c
c Mark Showalter & Neil Heather, PDS Rings Node, January 1997
c*******************************************************************************

c Error type definitions
	integer*4	RL_IGNORE, RL_INFORM, RL_RECORD, RL_SIGNAL,
     &			RL_ABORT
	parameter	(RL_IGNORE = -1)
	parameter	(RL_INFORM =  1)
	parameter	(RL_RECORD = -2)
	parameter	(RL_SIGNAL =  2)
	parameter	(RL_ABORT  =  3)

c Error routines
	logical*4	FRL_TestError,  FRL_ClearError
	logical*4	FRL_TestError1, FRL_ClearError1
	integer*4	FRL_SetErrorType, FRL_GetErrorType

c*******************************************************************************
c</PRE></BODY></HTML>
