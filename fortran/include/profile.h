/*<HTML><HEAD><TITLE> profile.h </TITLE></HEAD><BODY><PRE>
********************************************************************************
* profile.h -- Master include file for the Profile Library
*
* Version 1.0: Original version.
*              Mark Showalter & Neil Heather, PDS Rings Node, March 1998.
* Version 1.1: QUICK compilation mode and Pro_StatRange() function added.
*              Mark Showalter, January 2000.
*******************************************************************************/

#include "ringlib.h"

/*******************************************************************************
* SYMBOL DEFINITIONS
*******************************************************************************/

/* Object class identifiers */

#define XPRO_OBJECT_CLASS		   0

#define   XPRO_SERIES_CLASS		1000
#define     XPRO_ARRAY_CLASS		1100
#define     XPRO_COLUMN_CLASS		1200
#define     XPRO_STAT_CLASS		1300
#define       XPRO_BUFFERED_CLASS	1310
#define       XPRO_FIXED_CLASS		1320
#define       XPRO_WEIGHTED_CLASS	1330

#define   XPRO_FUNCTION_CLASS		2000
#define     XPRO_LSPLINE_CLASS		2100
#define     XPRO_SOFTFUNC_CLASS		2200
#define     XPRO_COMPFUNC_CLASS		2300
#define     XPRO_SLOPEFUNC_CLASS	2400
#define     XPRO_CURVE_CLASS		2500
#define       XPRO_SPLINE_CLASS		2510
#define       XPRO_INVERSE_CLASS	2520

#define   XPRO_LABEL_CLASS              3000

/* Series flag values */

#define PRO_MISSING_FLAG		 1
#define PRO_INVALID_FLAG		 2

/*******************************************************************************
* TYPE DEFINITIONS
*******************************************************************************/

#define PRO_NAMELEN	59	/* limit on lengths of names */
#define PRO_FILELEN	255	/* limit on lengths of file names */

typedef struct XPRO_CLASS_STRUCT {
    RL_INT4		id;
    RL_CHAR		name[PRO_NAMELEN+1];
    RL_VOID		*pointer;
} XPRO_CLASS;

typedef struct XPRO_OBJECT_STRUCT {
    XPRO_CLASS		class;
    RL_CHAR		name[PRO_NAMELEN+1];
    RL_CHAR		xname[PRO_NAMELEN+1], yname[PRO_NAMELEN+1];
    RL_FLT8		x1, x2;
    void		(*freefunc)  RL_PROTO((RL_VOID *pointer));
    void		(*printfunc) RL_PROTO((RL_VOID *pointer));

    RL_BOOL		isfreed;
    struct XPRO_LINK_STRUCT {
	struct XPRO_LINK_STRUCT		*next;
	struct XPRO_OBJECT_STRUCT	*object;
    }			owners, slaves;
} PRO_OBJECT;

typedef struct XPRO_LINK_STRUCT XPRO_LINK;

/*******************************************************************************
* DECLARATIONS
*******************************************************************************/

/* A large limit for lengths of error messages */
#define	XPRO_MESSAGE_LEN		1023

/* A non-external declaration is found in errors.c */
extern RL_CHAR	xpro_message[XPRO_MESSAGE_LEN+1];

/*******************************************************************************
* MACROS used for QUICK mode compilation
*******************************************************************************/

#ifdef QUICK

#define XPro_Ptr1(object) (((XPRO_CLASS *) object)->pointer)
#define XPro_Ptr2(object) (((XPRO_CLASS *) XPro_Ptr1(object))->pointer)
#define XPro_Ptr3(object) (((XPRO_CLASS *) XPro_Ptr2(object))->pointer)

#endif

/*******************************************************************************
* FUNCTION PROTOTYPES
*******************************************************************************/

/*<A NAME="object"></A>
 ***************************************
 * object.c -- Generic object routines *
 ***************************************/

void        Pro_FreeObject     RL_PROTO((PRO_OBJECT *object));
void        Pro_PrintObject    RL_PROTO((PRO_OBJECT *object));
RL_CHAR    *Pro_ObjectName     RL_PROTO((PRO_OBJECT *object, RL_INT4 coord));
void        Pro_RenameObject   RL_PROTO((PRO_OBJECT *object, RL_INT4 coord,
                                         RL_CHAR *name));
RL_FLT8     Pro_ObjectDomain   RL_PROTO((PRO_OBJECT *object,
                                         RL_FLT8 *x1, RL_FLT8 *x2));
RL_FLT8     Pro_ObjectOverlap  RL_PROTO((PRO_OBJECT *object, PRO_OBJECT *refobj,
                                         RL_FLT8 *x1, RL_FLT8 *x2));

RL_CHAR    *XPro_ObjectName    RL_PROTO((PRO_OBJECT *object, RL_INT4 coord));
PRO_OBJECT *XPro_MakeObject    RL_PROTO((RL_FLT8 x1, RL_FLT8 x2,
                                         void (*freefunc) (RL_VOID *pointer),
                                         void (*printfunc)(RL_VOID *pointer),
                                         RL_VOID *pointer));
RL_BOOL     XPro_EnslaveObject RL_PROTO((PRO_OBJECT *object,
		                              PRO_OBJECT *slave));
void        XPro_PrintInfo     RL_PROTO((PRO_OBJECT *object));
void        XPro_PrintClass    RL_PROTO((XPRO_CLASS *class));

#ifdef QUICK
#define     XPro_ObjectPtr(ob) XPro_Ptr1(ob)
#else
RL_VOID    *XPro_ObjectPtr     RL_PROTO((PRO_OBJECT *object));
#endif

/*<A NAME="series"></A>
 *******************************
 * series.c -- Series routines *
 *******************************/

RL_FLT8     Pro_SeriesValue    RL_PROTO((PRO_OBJECT *object, RL_INT4 k,
                                                             RL_INT4 *flag));
RL_INT4     Pro_SeriesIndices  RL_PROTO((PRO_OBJECT *object, RL_INT4 *k1,
                                                             RL_INT4 *k2));
RL_FLT8     Pro_SeriesSampling RL_PROTO((PRO_OBJECT *object, RL_FLT8 *x1,
                                                             RL_FLT8 *x2,
                                                             RL_FLT8 *dx));
RL_FLT8     Pro_SeriesIndex    RL_PROTO((PRO_OBJECT *object, RL_FLT8 x));
RL_FLT8     Pro_SeriesXValue   RL_PROTO((PRO_OBJECT *object, RL_FLT8 kRL_FLT8));
PRO_OBJECT *Pro_WindowSeries   RL_PROTO((PRO_OBJECT *object, RL_INT4 k1,
                                                             RL_INT4 k2));

PRO_OBJECT *XPro_MakeSeries    RL_PROTO((RL_INT4 k1, RL_INT4 k2,
                                 RL_FLT8 x1, RL_FLT8 dx,
                                 RL_FLT8 (*evalfunc)  (RL_VOID *pointer,
                                                       RL_INT4 k,
                                                       RL_INT4 *flag),
                                 void    (*printfunc) (RL_VOID *pointer),
                                 void    (*freefunc)  (RL_VOID *pointer),
                                 RL_VOID *pointer));
#ifdef QUICK
#define     XPro_SeriesPtr(ob) XPro_Ptr2(ob)
#else
RL_VOID	   *XPro_SeriesPtr     RL_PROTO((PRO_OBJECT *object));
#endif

/*<A NAME="array"></A>
 * array.c -- Array series routines */

PRO_OBJECT *Pro_ArraySeries    RL_PROTO((RL_VOID *table,
                                 RL_INT4 k1, RL_INT4 nsamples,
                                 RL_FLT8 x1, RL_FLT8 dx,
                                 RL_FLT8 missing, RL_FLT8 invalid,
                                 RL_BOOL isdouble, RL_BOOL dupe));

/*<A NAME="column"></A>
 * column.c -- PDS column series routines */

PRO_OBJECT *Pro_ColumnSeries RL_PROTO((PRO_OBJECT *label, RL_INT4 table,
                                       RL_INT4 column, RL_INT4 item,
                                       RL_INT4 row1, RL_INT4 row2, RL_INT4 k1,
                                       RL_INT4 buffersize, RL_BOOL usedouble));

/*<A NAME="stat"></A>
 *****************************************
 * stat.c -- Statistical series routines *
 *****************************************/

RL_FLT8     Pro_StatCovar RL_PROTO((PRO_OBJECT *object,
                                    RL_INT4 k1, RL_INT4 k2));

RL_INT4     Pro_StatRange RL_PROTO((PRO_OBJECT *object, RL_INT4 k,
                                    RL_INT4 *k1, RL_INT4 *k2));

PRO_OBJECT *XPro_MakeStat RL_PROTO((RL_INT4 k1, RL_INT4 k2,
                                    RL_FLT8 x1, RL_FLT8 dx,
                                    RL_FLT8 (*evalfunc)  (RL_VOID *pointer,
                                                          RL_INT4 k,
                                                          RL_INT4 *flag),
                                    RL_FLT8 (*covarfunc) (RL_VOID *pointer,
                                                          RL_INT4 k1,
                                                          RL_INT4 k2),
                                    void (*rangefunc)    (RL_VOID *pointer,
                                                          RL_INT4 k,
                                                          RL_INT4 *k1,
                                                          RL_INT4 *k2),
                                    void (*freefunc)  (RL_VOID *pointer),
                                    void (*printfunc) (RL_VOID *pointer),
                                    RL_VOID *pointer));

#ifdef QUICK
#define  XPro_StatPtr(ob) XPro_Ptr3(ob)
#else
RL_VOID *XPro_StatPtr RL_PROTO((PRO_OBJECT *object));
#endif

/*<A NAME="fixed"></A>
 * fixed.c -- fixed statistical series routines */

PRO_OBJECT  *Pro_FixedStat RL_PROTO((PRO_OBJECT *series,
                                     RL_INT4 span, RL_FLT8 *covars));

/*<A NAME="weighted"></A>
 * weighted.c -- weighted statistical series routines */

PRO_OBJECT  *Pro_WeightedStat RL_PROTO((PRO_OBJECT *stat,
                                        RL_INT4 k1, RL_INT4 k2,
                                        RL_FLT8 x1, RL_FLT8 dx,
                                        void    (*krange)  (RL_INT4 knew,
                                                            RL_INT4 *k1,
                                                            RL_INT4 *k2,
                                                            RL_VOID *params),
                                        RL_FLT8 (*weights) (RL_INT4 knew,
                                                            RL_INT4 k,
                                                            RL_VOID *params),
                                        RL_VOID *params, RL_SIZE paramsize,
                                        RL_BOOL dupe,
                                        void (*printmore) (RL_VOID *params)));

/*<A NAME="filtered"></A>
 * filtered.c -- filtered weighted statistical series routines */

PRO_OBJECT  *Pro_FilteredStat RL_PROTO((PRO_OBJECT *stat, RL_FLT8 *filter,
                                        RL_INT4 df1, RL_INT4 df2));

/*<A NAME="resample"></A>
 * resample.c -- resampled weighted statistical series routines */

PRO_OBJECT  *Pro_ResampledStat RL_PROTO((PRO_OBJECT *stat,
                                         PRO_OBJECT *oldpsf,
                                         PRO_OBJECT *newpsf,
                                         PRO_OBJECT *curve, RL_INT4 segment,
                                         RL_FLT8 x1, RL_FLT8 dx,
                                         RL_INT4 k1, RL_INT4 k2));
RL_INT4      Pro_ResampledSize RL_PROTO((PRO_OBJECT *series,
                                         PRO_OBJECT *oldpsf,
                                         PRO_OBJECT *newpsf,
                                         PRO_OBJECT *curve, RL_INT4 segment,
                                         RL_FLT8 r1, RL_FLT8 r2, RL_FLT8 dr));

/*<A NAME="psffilt"></A>
 * psffilt.c -- support routines for statistical series filters */

RL_INT4 Pro_PSFFilter RL_PROTO((PRO_OBJECT *oldpsf, PRO_OBJECT *newpsf,
                                RL_FLT8 center, RL_FLT8 expand,
                                RL_FLT8 *filter, RL_INT4 nfilter,
                                RL_INT4 *f1, RL_INT4 *f2));

RL_INT4 XPro_PSFInfo  RL_PROTO((PRO_OBJECT *psf,
                                RL_FLT8 *halfwidth, RL_FLT8 *param));

RL_FLT8	XPro_PSFInteg RL_PROTO((RL_INT4 type1, RL_INT4 type2,
                                RL_FLT8 a, RL_FLT8 b,
                                RL_FLT8 par1, RL_FLT8 par2));

/*<A NAME="function"></A>
 *******************************************
 * function.c -- Generic function routines *
 *******************************************/

RL_FLT8     Pro_FuncValue    RL_PROTO((PRO_OBJECT *object, RL_FLT8 x));
PRO_OBJECT *Pro_WindowFunc   RL_PROTO((PRO_OBJECT *object, RL_FLT8 x1,
                                                           RL_FLT8 x2));

PRO_OBJECT *XPro_MakeFunc    RL_PROTO((RL_FLT8 x1, RL_FLT8 x2,
                              RL_FLT8 (*evalfunc) (RL_VOID *pointer, RL_FLT8 x),
                              void    (*freefunc) (RL_VOID *pointer),
                              void    (*printfunc)(RL_VOID *pointer),
                              RL_VOID *pointer));

#ifdef QUICK
#define     XPro_FuncPtr(ob) XPro_Ptr2(ob)
#else
RL_VOID    *XPro_FuncPtr     RL_PROTO((PRO_OBJECT *object));
#endif

/*<A NAME="lspline"></A>
 * lspline.c -- Linear spline function routines */

PRO_OBJECT *Pro_LSplineFunc RL_PROTO((PRO_OBJECT *series));

/*<A NAME="software"></A>
 * software.c -- Software function routines */

PRO_OBJECT *Pro_SoftFunc  RL_PROTO((
                              RL_FLT8 (*calc) (RL_FLT8 x, RL_VOID *params),
                              RL_FLT8 x1, RL_FLT8 x2,
                              RL_VOID *params, RL_SIZE paramsize,
                              RL_BOOL dupe,
                              void    (*printmore) (RL_VOID *params)));
PRO_OBJECT *Pro_SoftFunc1 RL_PROTO((PRO_OBJECT *object,
                              RL_FLT8 (*calc) (RL_FLT8 y, RL_VOID *params),
                              RL_VOID *params, RL_SIZE paramsize,
                              RL_BOOL dupe,
                              void    (*printmore) (RL_VOID *params)));
PRO_OBJECT *Pro_SoftFunc2 RL_PROTO((PRO_OBJECT *object1, PRO_OBJECT *object2,
                              RL_FLT8 (*calc) (RL_FLT8 y1, RL_FLT8 y2,
                                               RL_VOID *params),
                              RL_VOID *params, RL_SIZE paramsize,
                              RL_BOOL dupe,
                              void    (*printmore) (RL_VOID *params)));

RL_VOID    *XPro_SoftParams RL_PROTO((PRO_OBJECT *object));

/*<A NAME="composit"></A>
 * composit.c -- Composite function routines */

PRO_OBJECT *Pro_CompFunc      RL_PROTO((PRO_OBJECT *inner, PRO_OBJECT *outer));

/*<A NAME="slope"></A>
 * slope.c -- Slope function routines */

PRO_OBJECT *Pro_SlopeFunc     RL_PROTO((PRO_OBJECT *object));

/*<A NAME="boxcar"></A>
 * boxcar.c -- Boxcar function routines */

PRO_OBJECT *Pro_BoxcarFunc    RL_PROTO((RL_FLT8 height, RL_FLT8 halfwidth));
RL_BOOL     Pro_BoxcarInfo    RL_PROTO((PRO_OBJECT *object,
                                        RL_FLT8 *height, RL_FLT8 *halfwidth));

/*<A NAME="sinc"></A>
 * sinc.c -- Sinc function routines */

PRO_OBJECT *Pro_SincFunc      RL_PROTO((RL_FLT8 height, RL_FLT8 step,
                                        RL_FLT8 halfwidth, RL_FLT8 shoulder));
RL_BOOL     Pro_SincInfo      RL_PROTO((PRO_OBJECT *object,
                                        RL_FLT8 *height, RL_FLT8 *step,
                                        RL_FLT8 *halfwidth, RL_FLT8 *shoulder));

/*<A NAME="triangle"></A>
 * triangle.c -- Triangle function routines */

PRO_OBJECT *Pro_TriangleFunc  RL_PROTO((RL_FLT8 height, RL_FLT8 halfwidth));
RL_BOOL     Pro_TriangleInfo  RL_PROTO((PRO_OBJECT *object,
                                        RL_FLT8 *height, RL_FLT8 *halfwidth));

/*<A NAME="curve"></A>
 ***************************
 * Curve function routines *
 ***************************/

RL_FLT8     Pro_CurveValue    RL_PROTO((PRO_OBJECT *object, RL_FLT8 x,
                                        RL_FLT8 *slope));
RL_FLT8     Pro_CurveInverse  RL_PROTO((PRO_OBJECT *object, RL_INT4 segment,
                                        RL_FLT8 y));
RL_INT4     Pro_CurveSegments RL_PROTO((PRO_OBJECT *object));
RL_FLT8     Pro_CurveExtremum RL_PROTO((PRO_OBJECT *object, RL_INT4 segment,
                                        RL_FLT8 *value, RL_INT4 *type));

PRO_OBJECT *XPro_MakeCurve    RL_PROTO((RL_FLT8 x1, RL_FLT8 x2,
                                RL_INT4 nextrema, RL_FLT8 *xextrema,
                                RL_FLT8 (*evalfunc) (RL_VOID *pointer,
                                                     RL_FLT8 x, RL_FLT8 *slope),
                                RL_FLT8 (*invfunc)  (RL_VOID *pointer,
                                                     RL_FLT8 y,
                                                     RL_FLT8 x1, RL_FLT8 x2),
                                void    (*freefunc) (RL_VOID *pointer),
                                void    (*printfunc)(RL_VOID *pointer),
                                RL_VOID *pointer));

#ifdef QUICK
#define     XPro_CurvePtr(ob) XPro_Ptr3(ob)
#else
RL_VOID    *XPro_CurvePtr     RL_PROTO((PRO_OBJECT *object));
#endif

/*<A NAME="spline"></A>
 * spline.c -- Cubic spline curve routines */

PRO_OBJECT *Pro_SplineCurve   RL_PROTO((PRO_OBJECT *series));

/*<A NAME="inverse"></A>
 * inverse.c -- Inverse curve routines */

PRO_OBJECT *Pro_InverseCurve  RL_PROTO((PRO_OBJECT *curve, RL_INT4 segment));

/*<A NAME="label"></A>
 **********************
 * PDS label routines *
 **********************/

PRO_OBJECT *Pro_OpenLabel     RL_PROTO((RL_CHAR *labelfile));
RL_INT4     Pro_LabelCount    RL_PROTO((PRO_OBJECT *object,
                                        RL_INT4 ntable, RL_INT4 ncolumn));
RL_CHAR    *Pro_LabelName     RL_PROTO((PRO_OBJECT *object,
                                        RL_INT4 ntable, RL_INT4 ncolumn));
RL_CHAR    *Pro_LabelXName    RL_PROTO((PRO_OBJECT *object, RL_INT4 ntable));
RL_INT4     Pro_LabelFind     RL_PROTO((PRO_OBJECT *object, RL_INT4 ntable,
                                        RL_CHAR *name));
RL_INT4     Pro_LabelSampling RL_PROTO((PRO_OBJECT *object, RL_INT4 ntable,
                                        RL_INT4 ncolumn, RL_INT4 nitem,
                                        RL_FLT8 *x1, RL_FLT8 *x2, RL_FLT8 *dx));

RL_INT4	    Pro_LabelInt      RL_PROTO((PRO_OBJECT *object, RL_INT4 ntable,
                                        RL_INT4 ncolumn, RL_CHAR *keyword,
                                        RL_INT4 dfault, RL_BOOL raise_error));
RL_FLT8	    Pro_LabelFloat    RL_PROTO((PRO_OBJECT *object, RL_INT4 ntable,
                                        RL_INT4 ncolumn, RL_CHAR *keyword,
                                        RL_FLT8 dfault, RL_BOOL raise_error));
RL_CHAR    *Pro_LabelString   RL_PROTO((PRO_OBJECT *object, RL_INT4 ntable,
                                        RL_INT4 ncolumn, RL_CHAR *keyword,
                                        RL_CHAR *dfault, RL_BOOL raise_error));

RL_BOOL     XPro_LabelInfo    RL_PROTO((PRO_OBJECT *object, RL_INT4 ntable,
                                        RL_INT4 ncolumn,
                                        RL_VOID **tabletree,
                                        RL_VOID **columntree,
                                        RL_INT4 *rows, RL_INT4 *items,
                                        RL_FLT8 *x1, RL_FLT8 *x2, RL_FLT8 *dx,
                                        RL_CHAR **xname, RL_CHAR **yname,
                                        RL_FLT8 *missing, RL_FLT8 *invalid,
                                        RL_FLT8 *offset, RL_FLT8 *scale));

/*<A NAME="error"></A>
 **************************
 * Special error routines *
 **************************/

void XPro_NullError     RL_PROTO((RL_CHAR *info, PRO_OBJECT *object));
void XPro_ClassError    RL_PROTO((RL_CHAR *info, PRO_OBJECT *object));

void XPro_DomainError   RL_PROTO((RL_CHAR *info, PRO_OBJECT *object,
                                 RL_FLT8 x1, RL_FLT8 x2, RL_FLT8 x));
void XPro_IDomainError  RL_PROTO((RL_CHAR *info, PRO_OBJECT *object,
                                 RL_INT4 k1, RL_INT4 k2, RL_INT4 k));
void XPro_EmptyDomain   RL_PROTO((RL_CHAR *info,
                                 PRO_OBJECT *object1, PRO_OBJECT *object2,
                                 RL_FLT8 x1,  RL_FLT8 x2,
                                 RL_FLT8 x1a, RL_FLT8 x2a));
void XPro_IEmptyDomain  RL_PROTO((RL_CHAR *info,
                                 PRO_OBJECT *object1, PRO_OBJECT *object2,
                                 RL_INT4 k1,  RL_INT4 k2,
                                 RL_INT4 k1a, RL_INT4 k2a));

void XPro_CoordMismatch RL_PROTO((RL_CHAR *info,
                                 PRO_OBJECT *object1, PRO_OBJECT *object2,
                                 RL_CHAR *name1, RL_CHAR *name2));

/*******************************************************************************
</PRE></BODY></HTML>*/
