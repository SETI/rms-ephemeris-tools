C$ Procedure

      SUBROUTINE FOVCLP ( P, Q, COSFOV)

C$ Abstract
C
C     A utility subroutine that clips off the ends of segments that lie
C     outside of a cone about the z-axis.
C
C$ Required_Reading
C
C     None.
C
C$ Keywords
C
C     UTILITY
C
C$ Declarations

      DOUBLE PRECISION P(3)
      DOUBLE PRECISION Q(3)
      DOUBLE PRECISION COSFOV

C$ Brief_I/O
C
C     VARIABLE  I/O  DESCRIPTION
C     --------  ---  ---------------------------------------------------
C     P         I/O  First end of the segment that might need clipping.
C     Q         I/O  Second end of the segment that might need clipping.
C     COSFOV     I   Cosine of the field of view.
C
C$ Detailed_Input
C
C     P         Are the endpoints of a segment in 3-space.
C     Q
C
C     COSFOV    Is the cosine of the angle between the z-axis and 
C               any line lying in a right circular cone that 
C               makes up a circular field of view.
C               
C$ Detailed_Output
C
C     P         The endpoints of the segment after any clipping
C     Q         has been performed.
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
C     This routine finds that portion of a segment that lies
C     entirely within a cone of a given angle from its axis
C     of symmetry.  
C
C$ Files
C
C     None.
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
C     Version 1, 17-JUL-1986
C     Version 2, 14-JUN-1990
C     
C-

C
C     SPICE functions
C
      DOUBLE PRECISION       VDOT
C
C   Local Variables
C
      DOUBLE PRECISION      A       
      DOUBLE PRECISION      B       
      DOUBLE PRECISION      C       
      DOUBLE PRECISION      COSSQR 
      DOUBLE PRECISION      DISCRM 
      DOUBLE PRECISION      QSUBP ( 3 ) 
      DOUBLE PRECISION      S 
      DOUBLE PRECISION      T     ( 2 ) 
      DOUBLE PRECISION      Y     ( 3 ) 
      DOUBLE PRECISION      X     ( 3 ) 

      INTEGER               I
      INTEGER               J
      INTEGER               K
      INTEGER               NSUB    

      LOGICAL               DUMP



C     
C     Get the unit vectors parallel to P and Q.
C     
      CALL VHAT( P, X )
      CALL VHAT( Q, Y )

C     
C     If the segment lies entirely within the cone the cosine of the
C     angle from the z-axis to X and Y will be greater than the cosine
C     of the angle between the z-axis and an edge of the cone.
C     
      IF (       ( X(3) .GE. COSFOV ) 
     .     .AND. ( Y(3) .GE. COSFOV)) THEN 
     
         RETURN
         
      END IF

C     
C     At least one of the endpoints of the segment lies outside the
C     cone, we are going to need to do some algebra to find 
C     where the segment crosses the cone.
C     
C     Here's what needs to be done.
C     
C        We need to find that value of T such that
C        
C           t*X + (1-t)*Y 
C                             2                  2      2
C         < k, t*X + (1-t)*Y >  = |t*X + (1-t)*Y| COSFOV
C         
C         
C         But this equation is the same as:
C                           2                    2      2
C         < k, t*(X-Y) + Y >    = | t*(X-Y) + Y | COSFOV
C         
C         
C         So we need to find t such that
C                       
C                           2              2            2
C         0    =   [(X-Y)(3)       - COSFOV <X-Y,X-Y>]*t
C               
C                                          2
C              +  2[(X-Y)(3)*Y(3)  - COSFOV <X-Y,Y>]*t
C              
C                       2                  2
C              +   [Y(3)           - COSFOV <Y,Y> ] 
C        
C     
C     
      COSSQR = COSFOV*COSFOV

      CALL VSUB ( Q, P, QSUBP )
      
      C       = P(3)     * P(3)       -   COSSQR * VDOT(P,    P    )
      B       = P(3)     * QSUBP(3)   -   COSSQR * VDOT(P,    QSUBP)
      A       = QSUBP(3) * QSUBP(3)   -   COSSQR * VDOT(QSUBP,QSUBP)

      DISCRM  = B*B - A*C
      DUMP    = .FALSE.

      IF      (DISCRM .LE. 0) THEN
      
         DUMP = .TRUE.

      ELSE IF ( A .EQ. 0 ) THEN
          
         IF ( B .NE. 0)    THEN
            NSUB    = NSUB + 1
            T(NSUB) = -C/B
         ELSE
            DUMP = .TRUE.
         END IF

      ELSE
         DISCRM  = DSQRT( DISCRM )
         NSUB    = NSUB + 1
         T(NSUB) = (-B + DISCRM) / A
         NSUB    = NSUB + 1
         T(NSUB) = (-B - DISCRM) / A
      END IF

      J = 0
      
      DO I = 1,NSUB
         IF (( T(I) .GT. 0 ) .AND. (T(I) .LT. 1) ) THEN
            J    = J + 1
            T(J) = T(I)
         END IF
      
      END DO

      IF ( J .EQ. 0) THEN
         DUMP = .TRUE.
      ELSE
         NSUB = J
      END IF

      IF (DUMP) THEN
         
         P(1) = DSQRT( 1 - COSSQR )
         P(2) = 0
         P(3) = COSFOV

         DO I = 1,3
            Q(I) = P(I)
         END DO
         
         RETURN
         
      END IF
      
      IF ( (X(3) .GE. COSFOV) .AND. (Y(3) .LT. COSFOV) ) THEN
         IF (NSUB .GT. 1) THEN
            S = MIN( T(1), T(2) )
         ELSE
            S = T(1)
         END IF
         CALL VLCOM ( 1-S, P, S, Q, Q )
      ELSE IF ( (X(3) .LT. COSFOV) .AND. (Y(3) .GE. COSFOV) ) THEN
         IF (NSUB .GT. 1) THEN
            S = MAX( T(1), T(2) )
         ELSE
            S = T(1)
         END IF
         
         CALL VLCOM ( 1-S, P, S, Q, P )
         
      ELSE IF ((P(3) .GT. 0) .AND. (Q(3) .GT. 0 )) THEN
         
         CALL VLCOM ( 1-T(1), P, T(1), Q, P )
         CALL VLCOM ( 1-T(2), P, T(2), Q, Q )
         
      ELSE 
      
         P(1) = DSQRT( 1 - COSSQR )
         P(2) = 0
         P(3) = COSFOV

         DO I = 1,3
            Q(I) = P(I)
         END DO
         
      END IF

      RETURN
      END 
