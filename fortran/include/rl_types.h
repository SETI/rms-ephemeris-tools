/*******************************************************************************
* rl_types.h -- RingLib include file to define standard data types.
*
* This file may have to be changed for some C compilers.
*
* Mark R. Showalter, December 1995.
*******************************************************************************/

#ifndef RL_TYPES_DEFINED

#define RL_TYPES_DEFINED

/*******************************************************************************
* Define RingLib types
*******************************************************************************/

typedef long		RL_INT4;		/* 4-byte integer */
typedef long		RL_BOOL;		/* boolean */
typedef float		RL_FLT4;		/* single precision */
typedef double		RL_FLT8;		/* double precision */
typedef char		RL_CHAR;		/* 1-byte character */

/*******************************************************************************
* Define the void data type.  This is used exclusively in the context of
* "void *".  The ANSI C data type "void *" is not supported by the Sun C
* compiler.
*
* Note that this has to be done as a macro definition, because declaring a
* typedef to be void is not allowed (since void is not really a data type!)
*******************************************************************************/

#ifdef SUNC
#define RL_VOID		char
#else
#define RL_VOID		void
#endif

#endif

/******************************************************************************/
