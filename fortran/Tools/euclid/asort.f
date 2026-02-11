C$Procedure      ASORT ( Sort and array of points by angle)
 
      SUBROUTINE ASORT ( XCOORD, YCOORD, N )
 
C$ Abstract
C
C      Sort an array of points in the plane by angle as measured
C      counter-clockwise from the positive x-axis.
C
C$ Required_Reading
C
C     None.
C
C$ Keywords
C
C      POINTS
C      SORT
C      ANGLE
C
C$ Declarations
 
      DOUBLE PRECISION      XCOORD(*)
      DOUBLE PRECISION      YCOORD(*)
      INTEGER               N
 
C$ Brief_I/O
C
C      VARIABLE  I/O  DESCRIPTION
C      --------  ---  --------------------------------------------------
C      XCOORD     I   Array of x-coordinates of the points.
C      YCOORD     I   Array of y-coordinates of the points.
C      N          I   Number of points.
C
C$ Detailed_Input
C
C      XCOORD      are the x- and y-coordinates of a collection of
C      YCOORD      points in the plane.  The i'th point is given
C                  by ( XCOORD(i), YCOORD(i) ).
C                  
C      N           is the number of points.
C
C$ Detailed_Output
C
C      XCOORD      on output, contains the same points but sorted
C      YCOORD      by increasing angle from the positive x-axis.
C                  The actual sorting is done in place.
C
C$ Parameters
C
C     None.
C
C$ Particulars
C
C      This routine uses the Shell Sort Algorithm to sort the points
C      by angle from the positive x-axis.
C
C$ Examples
C
C      Suppose the x- and y-coordinates are given as shown below:
C
C             1  99
C            33  -2
C            55  12
C            44  44
C             0   0
C
C      Then after a call to ASORT, the coordinate arrays array would 
C      be ordered as follows:
C
C             0   0
C            55  12
C            44  44
C             1   99
C            33  -2
C
C$ Restrictions
C
C      None.
C
C$ Exceptions
C
C      Error free.
C      
C      Note that the angle of (0,0) from the positive x-axis is defined
C      to be zero.
C
C$ Files
C
C      None.
C
C$ Author_and_Institution
C
C      W.L. Taber      (JPL)
C      I.M. Underwood  (JPL)
C
C$ Literature_References
C
C      None.
C
C$ Version
C
C-     Beta Version 1.0.0, 8-JUN-1990 (WLT) (IMU)
C
C-&

C     
C     Functions
C     
      LOGICAL               ARDERD

C     
C     Local Variables.
C     
      DOUBLE PRECISION      X
      DOUBLE PRECISION      Y

      INTEGER               GAP
      INTEGER               I
      INTEGER               J
      INTEGER               JG


      GAP = N / 2

C     
C     This is based on a Shell-Sort Algorithm.
C     
      DO WHILE ( GAP .GT. 0 ) 

         DO I = GAP+1, N

            J = I - GAP
            DO WHILE ( J .GT. 0 )
            
               JG = J + GAP

C
C              If point(J) precedes point(JG) leave things alone.
C
               IF ( ARDERD ( XCOORD(J),  YCOORD(J),
     .                       XCOORD(JG), YCOORD(JG) )    ) THEN
               
                  J          = 0
                  
C     
C              Otherwise, swap the points.
C     
               ELSE
                  
                  X          = XCOORD(J)
                  Y          = YCOORD(J)
                  
                  XCOORD(J)  = XCOORD(JG)
                  YCOORD(J)  = YCOORD(JG)

                  XCOORD(JG) = X
                  YCOORD(JG) = Y
                  
               END IF

               J = J - GAP
               
            END DO 

         END DO

         GAP = GAP / 2
         
      END DO 

      RETURN
      END
