C$ Procedure

      SUBROUTINE ELIPLN ( NORMAL,  CONSTN, MAJOR, MINOR, NINTSC,
     .                    COSINS,  SINS                         )


C$ Abstract
C
C     Determines the intersection(s) of an ellipse centered about the
C     origin in 3-space with a plane.
C
C$ Required Reading
C
C     None.
C
C$ Keywords
C
C     GEOMETRY
C
C$ Declarations

      DOUBLE PRECISION NORMAL  ( 3 )
      DOUBLE PRECISION CONSTN
      DOUBLE PRECISION MAJOR   ( 3 )
      DOUBLE PRECISION MINOR   ( 3 )
      INTEGER          NINTSC
      DOUBLE PRECISION COSINS  ( 2 )
      DOUBLE PRECISION SINS    ( 2 )

C$ Brief_I/O
C
C     VARIABLE  I/O  DESCRIPTION
C     --------  ---  ---------------------------------------------------
C     NORMAL     I   Normal to the plane under consideration
C     CONSTN     I   Constant term in the equation of the plane.
C     MAJOR      I   Vector along semi-major axis of the ellipse
C     MINOR      I   Vector along semi-minor axis of the ellipse
C     NINTSC     O   Number of intersections of the plane and ellipse.
C     COSINS     O   Coefficient of MAJOR for intersection points.
C     SINS       O   Coefficient of MINOR for intersection points.
C
C$ Detailed_Input
C
C      NORMAL    Normal vector to the plane under consideration.  Points
C                X, in the plane satisfy <X,NORMAL> = CONSTN
C
C      CONSTN    Constant term in the equation of the plane under 
C                consideration (see above).
C
C      MAJOR     Vector pointing along the semi-major axis of the 
C                ellipse having length equal to the semi-major axis
C
C      MINOR     Vector pointing along the semi-minor axis of the 
C                ellipse having length equal to the semi-minor axis
C
C
C$ Detailed_Output
C
C      NINTSC    Number of intersections of the ellipse with the plane
C                (-1, 0, 1, or 2). NINTSC is returned as -1 if the
C                ellipse lies in the plane (in which case there are
C                infinitely many intersections
C
C      COSINS   The points of intersection of the ellipse with the 
C      SINS     can be represented as 
C      
C                   COSINS(I)*MAJOR + SINS(I)*MAJOR 
C                 
C                COSINS and SINS are these coefficients.
C                In the case where the ellipse lies in the plane the
C                values returned in the two arrays are
C                
C                   COSINS(1) = 1      SINS(1) = 0
C                   COSINS(2) = 0      SINS(2) = 1
C
C$ Parameters
C
C     None.
C
C$ Exceptions
C
C     Error free. 
C
C$ Files
C
C     None.
C
C$ Particulars
C
C     This routine finds the pairs 
C     (COSINS(1), SINS(1)), (COSINS(2),SINS(2)) such that
C
C        <COSINS(1)*MAJOR + SINS(1)*MINOR, NORMAL > = CNSTNT
C
C     and
C
C        <COSINS(2)*MAJOR + SINS(2)*MINOR, NORMAL > = CNSTNT
C
C     where COSINS(1), COSINS(2) and SINS(1), SINS(2) are 
C     legitimate values of Cosine and Sine respectively 
C     (provided such quantities exist). It also sets the value of 
C     NINTSC to the number of such pairs that exist.
C
C$ Examples
C
C     None.
C
C$ Restrictions
C
C     None.
C
C$ Literature_References
C
C     None.
C
C$ Author_and_Institution
C
C     W.L. Taber     (JPL)
C     I.M. Underwood (JPL)
C
C$ Version
C
C-    Beta Version 2.0.0, 11-JUN-1990 (WLT)
C
C-&


C
C   Spicelib functions
C
      DOUBLE PRECISION VDOT
C
C   Local Variables
C
      DOUBLE PRECISION A
      DOUBLE PRECISION B
      DOUBLE PRECISION AC
      DOUBLE PRECISION BC
      DOUBLE PRECISION A2
      DOUBLE PRECISION B2
      DOUBLE PRECISION C2
      DOUBLE PRECISION DISCRM
      DOUBLE PRECISION A2PB2
      DOUBLE PRECISION ROOT
      DOUBLE PRECISION AROOT
      DOUBLE PRECISION BROOT
      
C$ Method
C
C      Solve the simultaneous system of equations
C
C      COS*<MAJOR,NORMAL> + SIN*<MINOR,NORMAL> = CONSTN
C
C      COS**2 + SIN**2 = 1
C
C      If we simplify the above expression to 
C 
C      X<M,N> + Y<m,N> = C
C      and
C      X**2   + Y**2   = 1
C
C      The we see that we must solve the quadratic equation
C
C      (Y<m,N> - C)**2 = (1 - Y**2)(<M,N>**2)
C
C      This equation can be rewritten as:
C
C      Y**2[<m,N>**2 + <M,N>**2]- 2Y<m,N>C + (C**2 - <M,N>**2)  = 0
C
C      The solutions are:
C
C       <m,N>C    (+/-) <M,N> dsqrt{<m,N>**2 + <M,N>**2 - C**2}
C      -------------------------------------------------------
C                   [<m,N>**2 + <M,N>**2]
C                   
C                   
      A  = VDOT (MAJOR, NORMAL)
      B  = VDOT (MINOR, NORMAL)

      A2       = A*A
      B2       = B*B
      A2PB2    = A2 + B2
      BC       = B*CONSTN
      C2       = CONSTN*CONSTN
      DISCRM   = A2PB2 - C2

C
C     In order for a solution to yield legitimate SIN and COS,
C     the minimum of the quadratic expression must be between
C     0 and 1. (Refering to the Method described above ) this
C     holds only if    -1 <= BC/A2PB2 <= 1 .
C
      IF ( .NOT. (     ( - A2PB2 .LE. BC )
     .            .AND.(   A2PB2 .GE. BC ) ) ) THEN

         NINTSC = 0
         RETURN
      END IF

C
C     Check to make sure the quantity under the radical is positive
C
      IF ( DISCRM .LT. 0 ) THEN
         NINTSC = 0
         RETURN
      END IF
      
C
C     Make sure that the ellipse does not lie in the plane
C
      IF ( A2PB2 .EQ. 0 ) THEN
      
         COSINS(1) =  1
         SINS  (1) =  0
         COSINS(2) =  0
         SINS  (2) =  1
         NINTSC    = -1
         
         RETURN
      END IF
C
C     If the program has not already returned to the calling program
C     legitimate solutions exist.  We compute them now.
C
      IF (DISCRM .EQ. 0 ) THEN
      
         NINTSC    = 1
         A         = A / A2PB2
         B         = B / A2PB2
         SINS(1)   = B*CONSTN
         COSINS(1) = A*CONSTN
         
      ELSE
      
         NINTSC    = 2
         ROOT      = DSQRT( DISCRM )
         A         = A / A2PB2
         B         = B / A2PB2
         BC        = B*CONSTN
         AC        = A*CONSTN
         AROOT     = A*ROOT
         BROOT     = B*ROOT
         
         SINS  (1) = BC + AROOT
         COSINS(1) = AC - BROOT
         SINS  (2) = BC - AROOT
         COSINS(2) = AC + BROOT
         
      END IF


      RETURN
      END
