

C$ Procedure  ARDERD ( Angle order function )

      LOGICAL FUNCTION ARDERD ( X1, Y1, X2, Y2)

C$ Abstract
C
C     Determines whether or not two points in the plane are ordered
C     counter clockwise.
C
C$ Required Reading
C
C     None.
C
C$ Keywords
C
C     GEOMETRY 
C     ORDER 
C     ANGLE
C
C$ Declarations
      
      DOUBLE PRECISION      X1
      DOUBLE PRECISION      Y1

      DOUBLE PRECISION      X2
      DOUBLE PRECISION      Y2
      
C$ Brief_I/O
C
C     Variable  I/O  Description
C     --------  ---  --------------------------------------------------
C     X1         I   x-coordinate of the first point
C     Y1         I   y-coordinate of the first point
C     X2         I   x-coordinate of the second point
C     Y2         I   y-coordinate of the second point
C     ARDERD     O   Logical to indicate whether the points are ordered.
C
C$ Detailed_Input
C
C     X1         x-coordinate of the first point
C
C     Y1         y-coordinate of the first point
C
C     X2         x-coordinate of the second point
C
C     Y2         y-coordinate of the second point
C
C$ Detailed_Output
C
C     ARDERD     Logical to indicate whether the points are ordered. If
C                the conterclockwise angle from the positive x-axis of 
C                point 1 is as small or smaller than the 
C                counterclockwise angle from the positive x-axis of 
C                point 2 then ARDERD is TRUE, otherwise it is false.
C
C$ Parameters
C     
C     None.
C     
C$ Exceptions
C
C     Error free. 
C     
C     The point (0,0) has an angle of zero from the positive x-axis.
C     
C$ Files
C
C     None.
C
C$ Particulars
C
C     Each point in the plane can be assigned an angle as measured
C     counter clockwise from the positive x-axis.  Given two points
C     this routine determines whether the first has an angle smaller
C     than or equal to the angle of the second point.  If the first
C     angle is less than or equal to the second the function returns
C     TRUE, otherwise it returns FALSE.
C
C$ Examples
C
C     Point 1:   X    Y        Point 2:  X    Y         ARDERD
C              ---  ---                ---  ---         ------
C                0    0                  1    0         TRUE
C                1    0                  0    0         TRUE
C                0    0                 -1    0         TRUE
C               -1    0                  0    0         FALSE
C                1    2                  2    1         FALSE
C                2    1                  1    2         TRUE
C                1    3                  1    4         TRUE
C               -2    3                 -2   -3         TRUE
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
C     Version 1, 8-JUN-1990
C
C-

      INTEGER               QUAD1
      INTEGER               QUAD2

      IF ( Y1 .GE. 0 ) THEN
         IF ( X1 .GE. 0 ) THEN
            QUAD1  = 1
         ELSE
            QUAD1  = 2
         END IF
      ELSE
         IF ( X1 .LE. 0 ) THEN
            QUAD1  = 3
         ELSE
            QUAD1  = 4
         END IF      
      END IF

      IF ( Y2 .GE. 0 ) THEN
         IF ( X2 .GE. 0 ) THEN
            QUAD2  = 1
         ELSE
            QUAD2  = 2
         END IF
      ELSE
         IF ( X2 .LE. 0 ) THEN
            QUAD2  = 3
         ELSE
            QUAD2  = 4
         END IF      
      END IF


      IF ( QUAD1 .EQ. QUAD2 ) THEN         
         ARDERD = ( X2*Y1 .LE. X1*Y2 ) 
      ELSE 
         ARDERD = ( QUAD1 .LT. QUAD2 )
      END IF

      RETURN
      END
