c<HTML><HEAD><TITLE> fprofile.inc </TITLE></HEAD><BODY><PRE>
c*******************************************************************************
c fprofile.inc -- Master include file for the Profile Library, FORTRAN version.
c
c Version 1.0: Original release.
c              Mark Showalter & Neil Heather, PDS Rings Node, March 1998.
c Version 1.1: FPro_StatRange function added.
c              Mark Showalter, January 2000.
c*******************************************************************************

c Series flag definitions
        integer*4       PRO_MISSING_FLAG, PRO_INVALID_FLAG
        parameter       (PRO_MISSING_FLAG = 1)
        parameter       (PRO_INVALID_FLAG = 2)

c Character string size limits
        integer*4       PRO_NAMELEN, PRO_FILELEN
        parameter       (PRO_NAMELEN = 59)
        parameter       (PRO_FILELEN = 255)

c Object routines
        real*8          FPro_ObjectDomain, FPro_ObjectOverlap

c Series routines
        real*8          FPro_SeriesValue, FPro_SeriesSampling,
     &                  FPro_SeriesIndex, FPro_SeriesXValue
        integer*4       FPro_SeriesIndices
        integer*4       FPro_WindowSeries
        integer*4       FPro_ArraySeries
        integer*4       FPro_ColumnSeries

c Statistical series routines
        real*8          FPro_StatCovar
        integer*4       FPro_StatRange
        integer*4       FPro_BufferedStat
        integer*4       FPro_FixedStat
        integer*4       FPro_FilteredStat
        integer*4       FPro_ResampledStat, FPro_ResampledSize
        integer*4       FPro_PSFFilter

c Function routines
        real*8          FPro_FuncValue, FPro_FuncDomain
        integer*4       FPro_WindowFunc
        integer*4       FPro_LSplineFunc
        integer*4       FPro_SoftFunc, FPro_SoftFunc1, FPro_SoftFunc2
        integer*4       FPro_CompFunc
        integer*4       FPro_BoxcarFunc, FPro_TriangleFunc,
     &                  FPro_SincFunc
        logical*4       FPro_BoxcarInfo, FPro_TriangleInfo,
     &                  FPro_SincInfo

c Curve routines
        real*8          FPro_CurveValue, FPro_CurveInverse,
     &                  FPro_CurveExtremum
        integer*4       FPro_CurveSegments
        integer*4       FPro_SlopeFunc
        integer*4       FPro_SplineCurve
        integer*4       FPro_InverseCurve

c Label routines
        integer*4       FPro_OpenLabel, FPro_LabelCount, FPro_LabelFind,
     &                  FPro_LabelSampling
        integer*4       FPro_LabelInt
        real*8          FPro_LabelFloat

c*******************************************************************************
c</PRE></BODY></HTML>
