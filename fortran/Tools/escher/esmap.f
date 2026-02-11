 
C$ Procedure     ESMAP
 
      SUBROUTINE ESMAP ( VIEW, FOV,
     .                   PI0,  PI1,  LAM0,  LAM1,
     .                   X,    Y,    P,     L     )
 
C$ Abstract
C
C     Map vectors from projection space to the native pixel/line
C     space of an arbitrary graphics device. ESMAP should be called
C     only through its entry points, ESMAP1 and ESMAP2.
C
C$ Keywords
C
C     GRAPHICS
C
C$ Declarations
 
      DOUBLE PRECISION VIEW  (4)
      DOUBLE PRECISION FOV   (4)
      DOUBLE PRECISION PI0
      DOUBLE PRECISION PI1
      DOUBLE PRECISION LAM0
      DOUBLE PRECISION LAM1
      DOUBLE PRECISION X
      DOUBLE PRECISION Y
      INTEGER          P
      INTEGER          L
 
 
C$ Brief_I/O
C
C     VARIABLE  I/O  DESCRIPTION
C     --------  ---  ---------------------------------------------------
C     VIEW       I   See ESMAP1.
C     FOV        I   See ESMAP1.
C     PI0        I   See ESMAP1.
C     PI1        I   See ESMAP1.
C     LAM0       I   See ESMAP1.
C     LAM1       I   See ESMAP1.
C     X          I   See ESMAP2.
C     Y          I   See ESMAP2.
C     P          O   See ESMAP2.
C     L          O   See ESMAP2.
C
C$ Detailed_Input
C
C     Inputs are described in detail in the documentation for
C     the individual entry points, ESMAP1 and ESMAP2.
C
C$ Detailed_Output
C
C     Outputs are described in detail in the documentation for
C     the individual entry point ESMAP2.
C
C$ Input_Files
C
C     None.
C
C$ Output_Files
C
C     None.
C
C$ Input_Output_Common
C
C     None.
C
C$ Detailed_Description
C
C     ESMAP has two entry points, ESMAP1 and ESMAP2. The first entry
C     point computes the scaling factors necessary to convert individual
C     points in projection space to the native pixel/line space of the
C     graphics device. The second entry point does the actual conversion
C     for a single point.
C
C     ESMAP should never be called directly, but only through the
C     entry points described above.
C
C$ Examples
C
C     CALL ESMAP1 ( VIEW, FOV, PI_0,  PI_1, LAM_0, LAM1  )
C
C     DO I = 1, NPTS
C        CALL ESMAP2 ( X(I), Y(I), P, L )
C     END DO
C
C$ Restrictions
C
C     ESMAP is never called directly.
C
C$ Author_and_Institution
C
C     I.M. Underwood (JPL)
C
C$ Version_and_Date
C
C     Version 1, 27-OCT-1986
C
C-
 
C
C     Scratch stuff
C
      DOUBLE PRECISION HMIN
      DOUBLE PRECISION HMAX
      DOUBLE PRECISION VMIN
      DOUBLE PRECISION VMAX
 
      DOUBLE PRECISION XMIN
      DOUBLE PRECISION XMAX
      DOUBLE PRECISION YMIN
      DOUBLE PRECISION YMAX
 
      DOUBLE PRECISION XCEN
      DOUBLE PRECISION YCEN
 
      DOUBLE PRECISION UX
      DOUBLE PRECISION UY
      DOUBLE PRECISION U
 
      DOUBLE PRECISION PCEN
      DOUBLE PRECISION LCEN
 
C
C     Save everything between calls.
C
      SAVE
 
C
C     If ESMAP is called by accident, print an error message and
C     return without further ado.
C
      WRITE (6,*) '*******************************************'
      WRITE (6,*) 'You have called ESMAP. This must have been '
      WRITE (6,*) 'accidental. ESMAP is never called directly.'
      WRITE (6,*) '*******************************************'
 
      RETURN
 
 
 
C
C$ Procedure ESMAP1
 
      ENTRY  ESMAP1 ( VIEW,  FOV,
     .                PI0,   PI1,  LAM0,  LAM1  )
 
 
C$ Abstract
C
C     Set up the mapping from projection (x,y) space to the native
C     pixel/line space of an arbitrary graphics device, in preparation
C     for one or more calls to ESMAP2.
C
C$ Brief_I/O
C
C     VARIABLE  I/O  DESCRIPTION
C     --------  ---  ---------------------------------------------------
C     VIEW       I   The viewing area of the graphics device.
C     FOV        I   The field of view to be mapped onto REGION.
C     PI0        I   Pixel at the far left of the graphics device.
C     PI1        I   Pixel at the far right of the graphics device.
C     LAM0       I   Line at the bottom of the graphics device.
C     LAM1       I   Line at the top of the graphics device.
C
C$ Detailed_Input
C
C     VIEW       is the viewing area of the graphics device. Every
C                device, regardless of its shape, runs from zero to
C                one horizontally (from left to right), and from zero
C                to one vertically (from bottom to top). VIEW may be
C                be used to specify any part of the device.
C
C                The components of VIEW are: Hmin, Hmax, Vmin, Vmax.
C
C                The following examples illustrate the use of VIEW.
C
C                    (0.0, 1.0, 0.0, 1.0)     Entire device.
C                    (0.0, 0.5, 0.0, 1.0)     Left half.
C                    (0.0, 1.0, 0.0, 0.5)     Top half.
C                    (0.5, 1.0, 0.5, 1.0)     Upper right quarter.
C
C     FOV        is the field of view to be mapped onto the area
C                specified by VIEW. (Also called the Clipping Area.)
C
C                The components of FOV are: Xmin, Xmax, Ymin, Ymax.
C
C     PI0        is the pixel value corresponding to the far LEFT of
C                the device. (It may or may not be the minimum pixel
C                value.)
C
C     PI1        is the pixel value corresponding to the far RIGHT of
C                the device. (It may or may not be the maximum pixel
C                value.)
C
C     LAM0       is the line value corresponding to the BOTTOM of
C                the device. (It may or may not be the minimum line
C                value.)
C
C     LAM1       is the line value corresponding to the TOP of
C                the device. (It may or may not be the maximum line
C                value.)
C
C$ Detailed_Output
C
C     None.
C
C$ Input_Files
C
C     None.
C
C$ Output_Files
C
C     None.
C
C$ Input_Output_Common
C
C     None.
C
C$ Detailed_Description
C
C     ESMAP2 tries to map the largest possble clipping area onto the
C     viewing area provided by the user. This is done as follows.
C
C     Let Hmin, Hmax, Vmin, Vmax be the bounds of the viewing
C     area, and Pi0, Pi1, Lam0, Lam1 the bounds of the graphics
C     device. Let Xmin, Xmax, Ymin, Ymax be the bounds of the
C     clipping area.
C
C     The scaling factors Ux and Uy are computed as follows:
C
C           Ux = (Hmax - Hmin)(Pi1  - Pi0  ) / (Xmax - Xmin)
C           Uy = (Vmax - Vmin)(Lam1 - Lam0 ) / (Ymax - Ymin)
C
C     These tell us something. What is it? Anyway, we want to use
C     the smaller of the two, keeping the same signs as before.
C     (This means that we don't have to worry about the orientation
C     of the pixel/line coordinate system.)
C
C           U  = min ( |Ux|, |Uy| )
C
C           Ux = U * signum (Ux)
C           Uy = U * signum (Uy)
C
C     Given these scaling factors, points may be mapped from projection
C     space to pixel/line space as follows:
C
C           P = Pcen + Ux(X - Xcen)
C           L = Lcen + Uy(Y - Ycen)
C
C     where Pcen, Lcen, etc., are what?
C
C$ Examples
C
C     None.
C
C$ Restrictions
C
C     None.
C
C-
 
C
C     Save the contents of VIEW and FOV to local variables.
C
      HMIN = VIEW(1)
      HMAX = VIEW(2)
      VMIN = VIEW(3)
      VMAX = VIEW(4)
 
      XMIN = FOV(1)
      XMAX = FOV(2)
      YMIN = FOV(3)
      YMAX = FOV(4)
 
C
C     Determine the scaling factors.
C
      UX = (HMAX - HMIN) * (PI1   - PI0   ) / (XMAX - XMIN)
      UY = (VMAX - VMIN) * (LAM1  - LAM0  ) / (YMAX - YMIN)
 
      U  = MIN ( ABS (UX), ABS (UY) )
 
      UX = SIGN ( U, UX )
      UY = SIGN ( U, UY )
 
C
C     Determine the center of the clipping region, in both projection
C     and pixel/line spaces.
C
      XCEN = (XMIN + XMAX) / 2.D0
      YCEN = (YMIN + YMAX) / 2.D0
 
      PCEN = PI0   + (HMAX + HMIN) * (PI1   - PI0  ) / 2.D0
      LCEN = LAM0  + (VMAX + VMIN) * (LAM1  - LAM0 ) / 2.D0
 
      RETURN
 
 
C
C$ Procedure ESMAP2
 
      ENTRY  ESMAP2 ( X, Y, P, L )
 
C$ Abstract
C
C     Map a point in projection (x,y) space to the equivalent point
C     in the native pixel/line (p,l) space of the graphics device
C     defined by the latest previous call to ESMAP1.
C
C$ Brief_I/O
C
C     VARIABLE  I/O  DESCRIPTION
C     --------  ---  ---------------------------------------------------
C     X          I   X coordinate of the point in projection space.
C     Y          I   Y coordinate of the point in projection space.
C     P          O   Pixel location of the point.
C     L          O   Line location of the point.
C
C$ Detailed_Input
C
C     X,
C     Y       are the coordinates of a point in projection space.
C
C$ Detailed_Output
C
C     P,
C     L       are the pixel and line coordinates corresponding to
C             the point (x,y) in projection space, as defined below.
C
C$ Input_Files
C
C     None.
C
C$ Output_Files
C
C     None.
C
C$ Input_Output_Common
C
C     None.
C
C$ Detailed_Description
C
C     Let Ux and Uy be the scaling factors computed by ESMAP1.
C     Let (Xcen,Ycen) be the center of the clipping area, and
C     (Pcen,Lcen) the  corresponding pixel/line location.
C
C     Then the pixel line location (P,L) corresponding to the
C     point (X,Y) is given by
C
C           P = Pcen + Ux(X - Xcen)
C           L = Lcen + Uy(Y - Ycen)
C
C     P and L are rounded to the nearest integer.
C
C$ Examples
C
C     CALL ESMAP1 ()
C
C     DO I = 1, NPTS
C        CALL ESMAP2 ( X(I), Y(I), P, L )
C     END DO
C
C$ Restrictions
C
C     Calls to ESMAP2 must be preceded by at least one call to ESMAP1.
C-
 
C
C     Not much to say. Convert from (x,y) to (p,l), as described above.
C
      P = IDNINT ( PCEN + UX * (X - XCEN) )
      L = IDNINT ( LCEN + UY * (Y - YCEN) )
 
      RETURN
      END
