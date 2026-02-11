C$ Procedure
      LOGICAL FUNCTION SMSIDE ( P, Q, NORMAL, CENTER, REFPNT )

C$ Abstract
C
C     Determine if the segment determined by P and Q lies on the same
C     side of the plane orthogonal to containing CENTER as does REFPNT
C
C$ Keywords
C
C  UTILITY, AFFINE, GEOMETRY, 
C
C$ Declarations

      DOUBLE PRECISION P(3)
      DOUBLE PRECISION Q(3)
      DOUBLE PRECISION NORMAL(3)
      DOUBLE PRECISION CENTER(3)
      DOUBLE PRECISION REFPNT(3)

C$ Brief_I/O
C
C     VARIABLE  I/O  DESCRIPTION
C     --------  ---  ---------------------------------------------------
C     P          I   First end point of the segment.
C     Q          I   Second endpoint of the segment.
C     NORMAL     I   Normal to the plane under consideration.
C     CENTER     I   A point in the plane under consideration.
C     REFPNT     I   Reference point.
C     SMSIDE     O   .TRUE. if  the segment and REFPNT are on same side.
C
C
C$ Detailed_Input
C
C     P          First end point of a segment that lies in one of
C                the two closed half spaces bounded by the plane
C                under consideration.
C
C     Q          Second endpoint of a segment that lies in one of the
C                two closed half spaces bounded by the plane under
C                consideration
C
C     NORMAL     Normal to the plane under consideration.
C
C     CENTER     A point in the plane under consideration.
C
C     REFPNT     A reference point.
C
C$ Detailed_Output
C
C     SMSIDE     .TRUE. if  the segment and REFPNT lie in the
C                same closed half space bounded by the plane.
C                .FALSE. otherwise.
C
C$ Detailed_Description
C
C     This routine computes the DOT product of the vectors joining
C     the center to the other three input points, with the normal to
C     the plane.  If the reference point and segment lie in the
C     same closed half space determined by the plane then these
C     dot products will lie in the same ray with endpoint 0 on the real
C     line.  Otherwise the segment and referenc point lie on opposite
C     sides of the plane.
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
C  VSUB, VDOT
C
C$ Restrictions
C
C  It is assumed that the line segment bounded by P and Q does not
C  intersect the plane at a unique interior point of the segment from
C  P to Q.
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
C     SPICELIB functions
C
      DOUBLE PRECISION VDOT
C
C     Local Variables
C
      DOUBLE PRECISION C

      DOUBLE PRECISION RFSIDE
      DOUBLE PRECISION PSIDE
      DOUBLE PRECISION QSIDE
      DOUBLE PRECISION TESTP
      DOUBLE PRECISION TESTQ

      DOUBLE PRECISION SMALL

      C       =  VDOT ( CENTER, NORMAL ) 

      RFSIDE  = VDOT ( REFPNT, NORMAL ) - C
      PSIDE   = VDOT ( P,      NORMAL ) - C
      QSIDE   = VDOT ( Q,      NORMAL ) - C

      TESTP   =  RFSIDE*PSIDE
      TESTQ   =  RFSIDE*QSIDE

      IF      ( ( TESTP .GE. 0 ) .AND. ( TESTQ .GE. 0 ) )THEN

         SMSIDE = .TRUE.

      ELSE IF ( ( TESTP .LE. 0 ) .AND. ( TESTQ .LE. 0 ) ) THEN

         SMSIDE = .FALSE.

      ELSE  

         SMALL  = MIN ( ABS(TESTP), ABS(TESTQ) )

         IF ( SMALL .EQ. ABS(TESTP) ) THEN
            SMSIDE = ( TESTQ .GE. 0 )
         ELSE
            SMSIDE = ( TESTP .GE. 0 )
         END IF

      END IF

      RETURN
      END
