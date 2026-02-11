C$ Procedure     EUSKIP ( Euclid---Skip segments )

      SUBROUTINE EUSKIP (MAJOR, CENTER, FOVRAD, SKIP )

C$ Abstract
C
C     Determines how many segments will be used to draw a circle.
C
C$ Required_Reading
C
C     None.
C
C$ Keywords
C
C   UTILITY
C
C$ Declarations

      DOUBLE PRECISION MAJOR
      DOUBLE PRECISION CENTER(3)
      DOUBLE PRECISION FOVRAD
      INTEGER          SKIP

C$ Brief_I/O
C
C     VARIABLE  I/O  DESCRIPTION
C     --------  ---  ---------------------------------------------------
C     MAJOR      I   Length of the major axis of the triaxial body.
C     CENTER     I   Position of the body center w.r.t the camera.
C     FOVRAD     I   Radius of the field of view about the fov center.
C     SKIP       O   Number of standard endpoints to skip.
C
C$ Detailed_Input
C
C     MAJOR      The length of the major axis of a triaxial body that
C                Euclid will draw.
C                
C     CENTER     The position of the center of the triaxial body 
C                with respect to the camera.
C                
C     FOVRAD     The field of view radius (a dimensionless quantity
C                the focal length of the camera is by definition 1.
C
C$ Detailed_Output
C
C     SKIP       is the number of standard endpoints to skip when
C                selecting segments to draw the body.  
C                
C$ Parameters
C
C     None.
C
C$ Exceptions
C
C     Error free. 
C
C$ Particulars
C
C     To draw an ellipse Euclid will normally use 96 points more or 
C     less evenly distributed around it and connects these points with 
C     line segments.  However, for bodies that will not fill up a 
C     significant portion of the field of view, this is overkill, the
C     number of segments can be reduced by a factor of 2,3,4, or 6.
C     This speeds up the drawing of "small" figures.
C     
C     Euclid will select the first point and then select the point
C     that occurs SKIP counts later as the other endpoint of the
C     segment used for rendering that part of the ellipse.  The next
C     segment is chosen in the same way using the endpoint of the
C     last segment as the startpoint of the next one.
C     
C     There are no "scientific" reasons for the selection of the SKIP
C     value.  The selection are simply what the author of this routine
C     thought would work well.
C
C$ Files
C
C     None.
C
C
C$ Examples
C
C     None.
C
C$ Restrictions
C
C     None.
C
C$ Author_and_Institution
C
C     W. L. Taber (JPL)
C
C$ Literature_References
C
C     None.
C
C$ Version_and_Date
C
C     Beta Version 1.1.0, 14-JUN-1990 (WLT)
C     
C        The routine was upgraded to comply with standard F77 fortran.
C        
C     Beta Version 1.0.0, 23-JUL-1986 (WLT)
C     
C-&

C
C     SPICE functions
C
      DOUBLE PRECISION      VNORM

C
C     Local Variables
C
      DOUBLE PRECISION      RATIO
      DOUBLE PRECISION      X

      X = VNORM (CENTER)

      IF ( (X .GT. 0) .AND. (FOVRAD .GT. 0) ) THEN
         RATIO = MAJOR/ (X*FOVRAD)
      ELSE
         RATIO = 1
      END IF
         
      IF ( RATIO .GT. 0.2D0 ) THEN
         SKIP = 1
      ELSE IF ( RATIO .GT. 0.1D0 ) THEN
         SKIP = 2
      ELSE IF ( RATIO .GT. 0.04  ) THEN
         SKIP = 3
      ELSE IF ( RATIO .GT. 0.01  ) THEN
         SKIP = 4
      ELSE
         SKIP = 6
      END IF

      RETURN
      END
