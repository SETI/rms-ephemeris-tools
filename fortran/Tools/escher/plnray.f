C$Procedure      PLNRAY

      SUBROUTINE PLNRAY ( REFPNT, NORMAL, DIRECT, INTRSC, POINT )

C$ Abstract
C
C      Given a ray from the origin and a plane, this routine determines
C      the intersection of that ray with the plane.
C
C$ Keywords
C
C
C
C$ Declarations

      DOUBLE PRECISION REFPNT (3)
      DOUBLE PRECISION NORMAL (3)
      DOUBLE PRECISION DIRECT (3)
      integer          INTRSC
      DOUBLE PRECISION POINT  (3)

C$ Brief_I/O
C
C      VARIABLE  I/O  DESCRIPTION
C      --------  ---  --------------------------------------------------
C      REFPNT     I   A point in the plane of interest
C      NORMAL     I   A vector orthogonal to the plane
C      DIRECT     I   The direction vector of the ray
C      INTRSC     O   A flag indicating that the ray and plane intersect
C      POINT      O   The point of intersection (if one exists)
C
C$ Detailed_Input
C
C      REFPNT     is a point in the plane of interest.
C
C      NORMAL     is a non-zero vector orthogonal to the plane of 
C                 interest.
C
C      DIRECT     is the direction vector of the ray emmanating from the
C                 origin.
C
C$ Detailed_Output
C
C      INTRSC     is a flag indicating whether the ray and plane of 
C                 interest intersect.  INTRSC is 0 if the ray and
C                 plane do not intersect; 1 if they intersect in a point
C                 and 2 if the ray lies in the plane.
C
C      POINT      is the unique point of intersection (if one exists).
C                 Other wise it is set to (0,0,0)
C
C$ Detailed_Description
C
C      This routine determines the intersection of the ray given by
C      t*DIRECT  ( t greater than zero ) with the plane given by
C      VDOT(NORMAL,REFPNT) = VDOT (NORMAL, (x,y,z))
C
C$ Examples
C
C
C$ Restrictions
C
C
C$ Input_Files
C
C      None.
C
C$ Output_Files
C
C      None.
C
C$ Common_Variables
C
C      None.
C
C$ Author_and_Institution
C
C      W. L. Taber (JPL)
C
C$ Literature_References
C
C      None.
C
C$ Version_and_Date
C
C      Version 1, dd-MMM-YYYY
C
C-&


C
C    Optlib functions
C
      DOUBLE PRECISION VDOT
C
C     Local variables
C
      DOUBLE PRECISION UNITV (3)
      DOUBLE PRECISION UNITN (3)
      DOUBLE PRECISION T

      DOUBLE PRECISION C
      DOUBLE PRECISION A


C
C     To help avoid overflows we normalize the direction and normal 
C     vectors.
C
      CALL UNORM ( DIRECT, UNITV, T )
      CALL UNORM ( NORMAL, UNITN, T )

      A = VDOT (UNITV, UNITN )
      C = VDOT (UNITN, REFPNT)

      IF ( ( A .EQ. 0 ) .AND. ( C .EQ. 0 ) ) THEN

C
C        The ray lies in the plane
C
         INTRSC   = 2

         POINT(1) = 0
         POINT(2) = 0
         POINT(3) = 0

      ELSE IF ( A .EQ. 0 ) THEN

C
C        The ray is parallel to the plane
C
         INTRSC   = 0
         POINT(1) = 0
         POINT(2) = 0
         POINT(3) = 0

      ELSE

C
C        The line containing the ray intersect the plane
C
         T        = C / A

         IF ( T .GE. 0 ) THEN

C
C           The ray points towards the plane
C
            CALL VSCL( T, UNITV, POINT )

            INTRSC   = 1

         ELSE

C
C           The ray points away from the plane.
C
            INTRSC   = 0
            POINT(1) = 0
            POINT(2) = 0
            POINT(3) = 0

         END IF

      END IF

      RETURN

      END
