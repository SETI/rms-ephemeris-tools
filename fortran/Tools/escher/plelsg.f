C$ Procedure

      SUBROUTINE PLELSG (      P,      Q, 
     .                    NORMAL,  MAJOR,  MINOR,  CENTER,
     .                    REFPNT, 
     .                    BEGSUB, ENDSUB, INSIDE, INBACK, NSUB )       

C$ Abstract
C
C     Project a segment onto a plane and find the intersection of
C     the resulting segment with an ellipse in the plane.
C
C$ Keywords
C
C     UTILITY, ELLIPSE, AFFINE, GEOMETRY
C
C$ Declarations

      DOUBLE PRECISION P(3)
      DOUBLE PRECISION Q(3)
      DOUBLE PRECISION NORMAL(3)
      DOUBLE PRECISION MAJOR(3)
      DOUBLE PRECISION MINOR(3)
      DOUBLE PRECISION CENTER(3)
      DOUBLE PRECISION REFPNT(3)
      DOUBLE PRECISION BEGSUB(3,4)
      DOUBLE PRECISION ENDSUB(3,4)
      LOGICAL          INSIDE(4)
      LOGICAL          INBACK(4)
      INTEGER          NSUB
C$ Brief_I/O
C
C     VARIABLE  I/O  DESCRIPTION
C     --------  ---  ---------------------------------------------------
C     P          I   First point of the line segment.
C     Q          I   Second point of the line segment.
C     NORMAL     I   Normal to the plane under consideration.
C     MAJOR      I   Major axis of the ellipse in the plane.
C     MINOR      I   Minor axis of the ellipse in the plane.
C     CENTER     I   Center of the ellipse in the plane.
C     REFPNT     I   Point from which to project the segment.
C     BEGSUB     O   Array of first endpoints for subsegments.
C     ENDSUB     O   Array of second endpoints for subsegments.
C     INSIDE     O   Logicals telling if segments project into ellipse.
C     INBACK     O   Logicals telling if segments are in front of plane.
C     NSUB       O   Number of subsegments.
C
C$ Detailed_Input
C
C     P          First point of the line segment.
C
C     Q          Second point of the line segment.
C
C     NORMAL     Normal to the plane under consideration.
C
C     MAJOR      Major axis of the ellipse in the plane.
C
C     MINOR      Minor axis of the ellipse in the plane.
C
C     CENTER     Center of the ellipse in the plane.
C
C     REFPNT     Point from which to project the segment.  To project 
C                a point to the plane from the reference point, we find
C                the intersection of the line containing the point and
C                the reference point with the plane.  Thus by projecting
C                the two endpoints we find the endpoints of the 
C                projected segment.
C
C$ Detailed_Output
C
C     BEGSUB     Array of first endpoints for subsegments.
C     ENDSUB     Array of second endpoints for subsegments.
C     INSIDE     Logicals telling if segments project into ellipse.
C     INBACK     Logicals telling if segments are in front of plane.
C     NSUB       Number of subsegments.
C
C$ Detailed_Description
C
C      This utility subroutine :
C         1.) Finds the intersection (if any) of a line segment with
C             and input plane.
C         2.) Projects the resulting segment(s) from REFPNT radially 
C             onto the input plane.
C         3.) Finds the intersection of the projected segment(s) with 
C             an ellipse in the plane. These intersection points
C             when mapped back to the line segment make up the endpoints
C             of the subsegments of the original segment.
C         4.) Establishes arrays of logical flags to indicate if the 
C             resulting subsegments are on the same side of the plane
C             as is the projection center, and whether or not the 
C             subsegments project to segments inside or outside of the 
C             ellipse.
C
C$ Input_Files
C
C     None.
C
C$ Output_Files
C
C     None.
C
C$ Input_Common
C
C     None.
C
C$ Output_Common
C
C     None.
C
C$ Examples
C
C     None.
C
C$ External_References
C
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
C     Version 1, 14-JUL-1986
C
C-

C
C
C     SPICELIB Functions
C
      DOUBLE PRECISION VDOT
      DOUBLE PRECISION BRCKTD
      LOGICAL          SMSGND
      LOGICAL          OPSGND

C
C   Local Variables
C
      INTEGER          I,J,K
      INTEGER          SUBPNT    
      INTEGER          CANDS

      LOGICAL          INELIP(5) 
      LOGICAL          BEHIND


      DOUBLE PRECISION S(2)
      DOUBLE PRECISION TINT
      DOUBLE PRECISION TSUB
      DOUBLE PRECISION T(5) 

      DOUBLE PRECISION TL(6)
      DOUBLE PRECISION TU(6)

      DOUBLE PRECISION DISCRM 
      DOUBLE PRECISION GAMMA  
      DOUBLE PRECISION BETA   
      DOUBLE PRECISION ALPHA  
      DOUBLE PRECISION INSIDQ 
      DOUBLE PRECISION INSIDP 
      DOUBLE PRECISION MINORQ  
      DOUBLE PRECISION MINORP  
      DOUBLE PRECISION MAJORQ  
      DOUBLE PRECISION MAJORP  
      DOUBLE PRECISION INTSCT 
      DOUBLE PRECISION BQUAD    
      DOUBLE PRECISION AQUAD    

      DOUBLE PRECISION PREF(3)
      DOUBLE PRECISION QREF(3)
      DOUBLE PRECISION CREF(3)

      DOUBLE PRECISION PRJP(3)
      DOUBLE PRECISION PRJQ(3)

      DOUBLE PRECISION NUM
      DOUBLE PRECISION DENOMP
      DOUBLE PRECISION DENOMQ

      DOUBLE PRECISION TEMPQ 
      DOUBLE PRECISION TEMPP 

      DOUBLE PRECISION PC(3)
      DOUBLE PRECISION QC(3)

C
C     The next parameter is a "quantization" parameter.  It is used to
C     avoid roundoff problems when finding intersections of segments
C     with the plane or an ellipse.  The choice here is 2**27.  A power
C     of 2 has been chosen so that no bits will be lost when this number
C     is multiplied times or divided into a double precision number.  
C     The choice of power 27 was arbitrary.  It just seemed like a good
C     choice.
C
      DOUBLE PRECISION QUANTA
      PARAMETER      ( QUANTA = 134 217 728)

C
C  First translate everything so that the REFPNT can be regarded
C  as the origin
C
      CALL VSUB( P,      REFPNT, PREF)
      CALL VSUB( Q,      REFPNT, QREF)
      CALL VSUB( CENTER, REFPNT, CREF)

      NUM     = VDOT ( NORMAL, CREF)
      DENOMP  = VDOT ( NORMAL, PREF )
      DENOMQ  = VDOT ( NORMAL, QREF )

      AQUAD   = VDOT( MAJOR, MAJOR )
      AQUAD   = AQUAD*AQUAD

      BQUAD   = VDOT( MINOR, MINOR )
      BQUAD   = BQUAD*BQUAD
C
C     Determine whether or not P is on the same side of the plane
C     as the reference point.
C
      IF      ( NUM .NE. DENOMP ) THEN
         BEHIND  = OPSGND ( NUM - DENOMP, NUM )
         
      ELSE IF ( NUM .NE. DENOMQ ) THEN
         BEHIND  = OPSGND ( NUM - DENOMQ, NUM )
         
      ELSE
         BEHIND  = .FALSE.
      END IF

C
C     See if the two endpoints are on the same side of the plane
C
      IF ( OPSGND ( DENOMP-NUM, DENOMQ-NUM )  ) THEN
C
C        The endpoints are indeed on opposite sides of the plane.
C
         INTSCT = (NUM - DENOMP)/(DENOMQ - DENOMP)
         INTSCT = BRCKTD(INTSCT, 0.0D0, 1.0D0)

      ELSE
         INTSCT = 2
      END IF

      INELIP(1) = .FALSE.
      SUBPNT    = 1
C
      IF ( .NOT. SMSGND ( DENOMP, DENOMQ ) ) THEN
C         CALL VTDSPC( 1, 1, 'TROUBLE IN RIVER CITY', 'A')
C
C        Some point of the segment projects to infinity in the plane
C        of interest. Consequently, we select an intermediate endpoint
C        and project the appropriate subsegment to the plane.
C
         IF      ( .NOT. SMSGND(DENOMP,NUM) ) THEN
            IF   ( DENOMP     .EQ. 0) THEN
               TSUB = 0.5
            ELSE
               TINT = DENOMP / (DENOMQ - DENOMP)
               TSUB = (1 + TINT)*0.5
            END IF

            CALL VLCOM ( 1.0D0 - TSUB, PREF, TSUB, QREF, PREF )

            TEMPP = VDOT ( NORMAL, PREF ) 
            TEMPQ = DENOMQ

         ELSE IF ( .NOT. SMSGND(DENOMQ,NUM) ) THEN
            IF   ( DENOMQ     .EQ. 0) THEN
               TSUB = 0.5
            ELSE
               TINT = DENOMP / (DENOMQ - DENOMP)
               TSUB = TINT*0.5
            END IF

            CALL VLCOM ( 1.0D0 - TSUB, PREF, TSUB, QREF, QREF )

            TEMPP  = DENOMP
            TEMPQ  = VDOT ( NORMAL, QREF )

         END IF

C
C        Project the endpoints to the plane and reference then to
C        the ellipse center as well as its major and minor axes.
C
         CALL VSCL ( NUM/TEMPP, PREF, PRJP )
         CALL VSCL ( NUM/TEMPQ, QREF, PRJQ )

         CALL VSUB ( PRJP, CREF, PC )
         CALL VSUB ( PRJQ, CREF, QC )

         MAJORP  = VDOT( MAJOR, PC )
         MAJORQ  = VDOT( MAJOR, QC )

         MINORP  = VDOT( MINOR, PC )
         MINORQ  = VDOT( MINOR, QC )

         INSIDP = (MAJORP*MAJORP/AQUAD) + (MINORP*MINORP/BQUAD)
         INSIDQ = (MAJORQ*MAJORQ/AQUAD) + (MINORQ*MINORQ/BQUAD)

C
C        Compute temporary variables needed for determination of 
C        ellipse intersections.
C
         ALPHA      = (MAJORP - MAJORQ)*(MAJORP - MAJORQ)/AQUAD
     .              + (MINORP - MINORQ)*(MINORP - MINORQ)/BQUAD

         BETA       = MAJORP*(MAJORQ - MAJORP)/AQUAD
     .              + MINORP*(MINORQ - MINORP)/BQUAD

         GAMMA      = INSIDP - 1.0D0

         DISCRM     = BETA*BETA - ALPHA*GAMMA

         CANDS = 0

         IF  ( DISCRM .GT. 0  ) THEN

             DISCRM     = DSQRT(DISCRM)

             CANDS = 2
             S(1)       = ( -BETA - DISCRM) /ALPHA
             S(2)       = ( -BETA + DISCRM) /ALPHA

         END IF


         IF (CANDS .NE. 0) THEN
C
C           Map the projected points back to the original segment.
C
            DO I = 1, CANDS
               ALPHA = S(I)     * TEMPP
               BETA  = (1-S(I)) * TEMPQ
               S(I)  = ALPHA / (BETA + ALPHA)
            END DO

            IF      ( DENOMP .LE. 0 ) THEN
               DO I = 1, CANDS
                  T(I+1) = TSUB + (1-TSUB)*S(I)
               END DO

            ELSE IF ( DENOMQ .LE. 0 ) THEN
               DO I = 1, CANDS
                  T(I+1) = TSUB*S(I)
               END DO

            END IF
C
C           Order the values of T
C
            IF ( T(2) .GT. T(3) ) THEN
               ALPHA = T(3)
               T(3)  = T(2)
               T(2)  = T(3)
            END IF

C
C           We next determine which segments ( if any ) project into
C           the ellipse.  We initially assume that none do.
C
            INELIP(1) = .FALSE.

            IF     ( ( T(2) .GT. 0 ) .AND. (T(3) .LT. 1 ) ) THEN

               SUBPNT       = SUBPNT + 2
C
C              It must be the middle segment that projects into the 
C              ellipse
C
               INELIP(1) = .FALSE.
               INELIP(2) = .TRUE.
               INELIP(3) = .FALSE.

            ELSE IF ( T(2) .LE. 0 ) THEN

               IF ( ( T(3) .GT. 0 ) .AND. (T(3) .LT. 1 ) ) THEN
                  SUBPNT = SUBPNT + 1
                  T(2)   = T(3)

                  IF ( DENOMP*NUM .LE. 0 ) THEN
                     INELIP(1) = .FALSE.
                     INELIP(2) = .TRUE.
                  ELSE
                     INELIP(1) = .TRUE.
                     INELIP(2) = .FALSE.
                  END IF

               END IF

            ELSE IF ( T(3) .GE. 1 ) THEN

               IF ( ( T(2) .GT. 0 ) .AND. (T(2) .LT. 1 ) ) THEN

                  SUBPNT = SUBPNT + 1

                  IF ( DENOMP*NUM .LE. 0 ) THEN
                     INELIP(1) = .FALSE.
                     INELIP(2) = .TRUE.
                  ELSE
                     INELIP(1) = .TRUE.
                     INELIP(2) = .FALSE.
                  END IF

               END IF
            END IF                  
         ELSE
            INELIP(1) = .FALSE.
         END IF
C
      ELSE IF (      ( NUM/DENOMP .GT. 0 ) 
     .         .AND. ( NUM/DENOMQ .GT. 0 ) ) THEN
C
C        The entire segment projects normally into the plane of interest
C
         CALL VSCL ( NUM/DENOMP, PREF, PRJP )
         CALL VSCL ( NUM/DENOMQ, QREF, PRJQ )

         CALL VSUB ( PRJP, CREF, PC )
         CALL VSUB ( PRJQ, CREF, QC )

         MAJORP  = VDOT( MAJOR, PC )
         MAJORQ  = VDOT( MAJOR, QC )

         MINORP  = VDOT( MINOR, PC )
         MINORQ  = VDOT( MINOR, QC )

         INSIDP = (MAJORP*MAJORP/AQUAD) + (MINORP*MINORP / BQUAD)
         INSIDQ = (MAJORQ*MAJORQ/AQUAD) + (MINORQ*MINORQ / BQUAD)

         IF ( (INSIDQ .LE. 1) .AND. (INSIDP .LE. 1) ) THEN
C
C           The entire segment projects inside the ellipse.
C
            INELIP(1) = .TRUE.

         ELSE
C
C           Compute temporary variables needed for determination of 
C           ellipse intersections.
C
            ALPHA  = (MAJORP - MAJORQ)*(MAJORP - MAJORQ)/AQUAD
     .             + (MINORP - MINORQ)*(MINORP - MINORQ)/BQUAD

            BETA   = MAJORP*(MAJORQ - MAJORP)/AQUAD
     .             + MINORP*(MINORQ - MINORP)/BQUAD

            GAMMA  = INSIDP - 1.0D0

            DISCRM = BETA*BETA - ALPHA*GAMMA

            IF (( INSIDQ .LT. 1 ) .AND. (INSIDP .GT. 1 )) THEN

               SUBPNT       =  SUBPNT + 1
               T(SUBPNT)    = ( -BETA - DSQRT( DISCRM ) ) / ALPHA

               INELIP(1) = .FALSE.
               INELIP(2) = .TRUE.

            ELSE IF (( INSIDP .LT. 1 ) .AND. (INSIDQ .GT. 1 )) THEN

               SUBPNT       =  SUBPNT + 1
               T(SUBPNT)    = ( -BETA + DSQRT( DISCRM ) ) / ALPHA
               T(SUBPNT)    = T(SUBPNT) + (1.0 - T(SUBPNT))*.01
               INELIP(1) = .TRUE.
               INELIP(2) = .FALSE.

            ELSE IF (      ( DISCRM .GT. 0     ) 
     .               .AND. (  GAMMA .GE. 0     )
     .               .AND. (   BETA .LT. 0     )  
     .               .AND. ( - BETA .LT. ALPHA )
     .               .AND. (ALPHA + BETA + BETA + GAMMA .GE. 0 ) ) THEN

               IF ( GAMMA .EQ. 0 ) THEN

                  SUBPNT    =  SUBPNT + 1
                  INELIP(1) = .TRUE.
                  INELIP(2) = .FALSE.
                  T(SUBPNT) = -2*BETA / ALPHA

               ELSE IF ( ALPHA + BETA + BETA + GAMMA .EQ. 0 ) THEN

                  SUBPNT       =  SUBPNT + 1
                  INELIP(1) = .FALSE.
                  INELIP(2) = .TRUE.
                  T(SUBPNT)    = (-BETA - DSQRT(DISCRM)) / ALPHA

               ELSE

                  INELIP(1) = .FALSE.
                  INELIP(2) = .TRUE.
                  INELIP(3) = .FALSE.
                  DISCRM       = DSQRT(DISCRM)

                  SUBPNT       = SUBPNT + 1
                  T(SUBPNT)    = ( -BETA - DISCRM) /ALPHA

                  SUBPNT       = SUBPNT + 1
                  T(SUBPNT)    = ( -BETA + DISCRM) /ALPHA

               END IF
            ELSE
               INELIP(1) = .FALSE.
            END IF
         END IF

C
C        Get the corresponding values of T when the projected 
C        intermediate points are mapped back to the original segment
C
         DO I = 2, SUBPNT
            ALPHA = T(I)     * DENOMP
            BETA  = (1-T(I)) * DENOMQ
            T(I)  = ALPHA / (BETA + ALPHA)
         END DO

C
      ELSE
         CALL VEQU ( P, BEGSUB )
         CALL VEQU ( Q, ENDSUB )
         INBACK(1) = .FALSE.
         INSIDE(1) = .FALSE.
         NSUB      = 1
         RETURN
      END IF

      SUBPNT    = SUBPNT + 1
      T(1)      = 0
      T(SUBPNT) = 1

C
C     If the segment intersects the plane, insert the intersection value
C     into our list of points.
C
      IF ( 0 .LT. INTSCT .AND. INTSCT .LT. 1 ) THEN
         I = 1

         DO WHILE ( INTSCT .GT. T(I) )
            I = I + 1
         END DO

C
C        The array INELIP tells us which segments project inside the
C        ellipse.  The truth value of INELIP(I) is equal to the truth
C        value of the assertion:
C
C            The interior of the segment 
C
C                  P + T(I)*(Q-P) to P + T(I+1)*(Q-P)
C         
C            projects inside the ellipse.
C
C        INTSCT lies between T(I) and T(I+1)  thus the segments 
C
C                  P + T(I)*(Q-P)    to P + INTSCT*(Q-P)
C        and
C                  P + INTSCT*(Q-P) to P + T(I+1)*(Q-P) 
C
C        should have truth values for INELIP the same as the current
C        value of INELIP(I)
C
         

         J = SUBPNT + 1

         DO WHILE ( J .GT. I )
            T(J)         = T(J-1)
            INELIP(J) = INELIP(J-1)
            J            = J - 1
         END DO
C
C        Note: The above loop will create one extra INELIP element,
C              however, we will never actually look at the extra element
C              so it doesn't matter.
C

         T(I)    = INTSCT
         SUBPNT  = SUBPNT + 1

      END IF

      TL(1)      = 0.0D0
      TU(1)      = 0.0D0

      TL(SUBPNT) = 1.0D0
      TU(SUBPNT) = 1.0D0

      IF ( SUBPNT .GT. 2 ) THEN
C
C     Produce a list of "FAT" solution points or intervals.
C
         DO I = 2, SUBPNT - 1
            TL(I) = MAX( 0.0D0, ( DNINT(QUANTA*T(I)) - 1.0D0 )/QUANTA )
            TU(I) = MIN( 1.0D0, ( DNINT(QUANTA*T(I)) + 1.0D0 )/QUANTA )
         END DO


C
C        Next we merge any of the "FAT" interior points that overlap 
C        into globules.
C
         J = 2
         I = 2

         DO WHILE ( I .LT. SUBPNT )

C
C           Once globules have been constructed, we will take segments
C           to be from the edge of one globule to the next.  There
C           is a last T(I) in any globule  and a first in the next
C           globule.  The segment from the edge of the globule to the
C           next will be inside or outside of the ellipse in the
C           same way as the segment from T(I) to T(I+1). (where T(I)
C           is the last point in the first globule).
C
C           The truth value of INELIP(I) is equal to the truth
C           value of the assertion:
C
C           The interior of the segment FROM P + T(I  )*(Q-P) 
C                                       TO   P + T(I+1)*(Q-P)
C           projects inside the ellipse.
C
C           Thus if INELIP is to take on values for segments joining
C           globules, its value must be the same as the one for the 
C           last T(I) inside the globule.
C
            IF ( TU(J) .GE. TL(I) ) THEN

C
C              The left endpoint of the next interval is inside the current
C              interval.  Move the current interval's right endpoint over 
C              to the next intervals right endpoint.
C
               TU(J)        = TU(I)
               INELIP(J) = INELIP(I)

            ELSE

C   
C              The next interval is disjoint from the current one.  Start 
C              a new interval beginning at the left end point of the next 
C              interval.
C            
               J            = J + 1
               TL(J)        = TL(I)
               TU(J)        = TU(I)
               INELIP(J) = INELIP(I)

            END IF

            I = I + 1

         END DO

         J      = J + 1
         TL(J)  = 1.0D0
         TU(J)  = 1.0D0
         SUBPNT = J

      END IF

      NSUB = SUBPNT - 1

C
C     Now construct the segments that connect the globules.
C
      DO I = 1, NSUB


         CALL VLCOM ( 1 - TU(I),   P, TU(I),   Q, BEGSUB(1, I) )
         CALL VLCOM ( 1 - TL(I+1), P, TL(I+1), Q, ENDSUB(1, I) )

         INSIDE(I) = INELIP(I)

C
C        Determine which side of the ellipse plane the current segment 
C        lies.
C
         IF ( INTSCT .GT. TU(I) ) THEN

            INBACK(I) = BEHIND

         ELSE

            INBACK(I) = .NOT. BEHIND

         END IF

      END DO

      RETURN


      END
