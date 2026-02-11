/*<HTML><HEAD><TITLE> fortran.h </TITLE></HEAD><BODY><PRE>
********************************************************************************
* fortran.h -- Include file for all FORTRAN interface routines.
*
* Version 0.9: Original release.
*              Mark R. Showalter, PDS Rings Node, January 1994
* Version 1.0: Updated for better compatibility with RingLib.
*              Mark Showalter, January 1997
* Version 1.1: QUICK mode compile option added.
*              Mark Showalter, October 1999.
* Version 1.2: Modified for Macintosh OSX compatibility
*              Mark Showalter, August 2002.
*******************************************************************************/

#ifndef FORTRAN_INCLUDED
#define FORTRAN_INCLUDED

#include "ringlib.h"

/*******************************************************************************
* The macro FORTRAN_NAME converts a C function name to the form that is required
* when it is called by a FORTRAN program.  On many UNIX systems, subprograms
* called from FORTRAN have an implied underscore character at the ends of their
* names.  This macro takes care of this operating system quirk.
*******************************************************************************/

#ifdef VMS
#define FORTRAN_NAME(name)      name

#else

#ifdef __APPLE__
#define FORTRAN_NAME(name)      name##_

#else

#ifdef __STDC__
#define FORTRAN_NAME(name)      name##_

#else
#define FORTRAN_NAME(name)      name/**/_

#endif
#endif
#endif

/*******************************************************************************
* Define the FORTRAN logical constants .TRUE. and .FALSE.
*******************************************************************************/

#ifdef __APPLE__

#define FTRUE  ((RL_INT4) 1)
#define FFALSE ((RL_INT4) 0)

#else

#define FTRUE  ((RL_INT4)  1)
#define FFALSE ((RL_INT4)  0)

#endif

/*******************************************************************************
* FUNCTION PROTOTYPES
*******************************************************************************/

void        FORT_Init               RL_PROTO((void));
RL_INT4     FORT_AddPointer         RL_PROTO((RL_VOID *pointer));
RL_VOID     *FORT_FreePointer       RL_PROTO((RL_INT4 index));

#ifdef QUICK
RL_VOID     **ZFORT_Pointers        /* Pointer table, global in QUICK mode */
#define     FORT_GetPointer(index) (ZFORT_Pointers[(index)-1])
#else
RL_VOID     *FORT_GetPointer        RL_PROTO((RL_INT4 index));
#endif

#endif

/*******************************************************************************
</PRE></BODY></HTML>*/
