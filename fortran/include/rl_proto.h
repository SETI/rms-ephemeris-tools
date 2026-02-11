/*******************************************************************************
* rl_proto.h
*
* This include file defines the macro RL_PROTO(), which is used in function
* prototype declarations.
*
* Using this macro, a function prototype can be declared as follows:
*	type function_name RL_PROTO((arg1, arg2, ...))
* Note the use of double parentheses.  The RL_PROTO macro will eliminate the
* arguments for those C compilers (such as Sun's) on which prototypes are not
* supported.
*
* Mark Showalter, December 1995
*******************************************************************************/

/*******************************************************************************
* Only include file once
*******************************************************************************/

#ifndef RL_PROTO

/*******************************************************************************
* Define macro based on type of compiler
*******************************************************************************/

#if defined(__STDC__) || defined(VAXC)

#define RL_PROTO(arglist)	arglist

#else

#define RL_PROTO(arglist)	()

#endif

/*******************************************************************************
* End of main conditional
*******************************************************************************/

#endif

/******************************************************************************/
