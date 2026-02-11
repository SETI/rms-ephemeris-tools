C$ Procedure

      SUBROUTINE PLPNTS( MAJOR,   MINOR,      CENTER, 
     .                   NORMLS,  CONSTS,
     .                   N,       SOLVE,      
     .                   POINTX,  POINTY,     MEETNS)

C$ Abstract
C
C     Determines the intersections of an ellipse with a family of 
C     specified planes.
C
C$ Keywords
C
C     UTILITY, VECTOR, GEOMETRY, ELLIPSE
C
C$ Declarations

      INTEGER          N
      DOUBLE PRECISION MAJOR(3)
      DOUBLE PRECISION MINOR(3)
      DOUBLE PRECISION CENTER(3)
      DOUBLE PRECISION NORMLS(3,N)
      DOUBLE PRECISION CONSTS(N)
      LOGICAL          SOLVE(*)
      DOUBLE PRECISION POINTX(*)
      DOUBLE PRECISION POINTY(*)
      INTEGER          MEETNS
C$ Brief_I/O
C
C     VARIABLE  I/O  DESCRIPTION
C     --------  ---  ---------------------------------------------------
C     MAJOR      I   Vector representing semi-major axis of the ellipse
C     MINOR      I   Vector representing semi-minor axis of the ellipse
C     CENTER     I   Center of the ellipse
C     NORMLS     I   Array of normal vectors to the family of planes
C     CONSTS     I   Array of constant terms in equations of the planes
C     N          I   Number of planes 
C     SOLVE      I   Array of solve-for-intersection-with-plane flags
C     POINTX     O   Array of Xcoords of intersection points.
C     POINTY     O   Array of Ycoords of intersection points.
C     MEETNS   O   Number of intersection points found.
C$ Detailed_Input
C
C     MAJOR      Vector representing semi-major axis of the ellipse.  It
C                points along the semi-major axis and has length equal 
C                the length of the semi-major axis.
C
C     MINOR      Vector representing semi-minor axis of the ellipse.  It
C                points along the semi-minor axis and has length equal 
C                the length of the semi-minor axis.
C
C     CENTER     Center of the ellipse
C
C     NORMLS    Array of normal vectors to the family of planes.  The 
C                I'th member of the family of planes has equation:
C                <X,(NORMLS(1,I),NORMLS(2,I),NORMLS(3,I))> 
C                                                          = CONSTANT(I)
C
C     CONSTS  Array of constant terms in equations of the planes.
C                (See above)
C
C     N          Number of planes 
C
C     SOLVE      Logical array of solve-for-intersection-with-plane 
C                flags.  If SOLVE(I) is .TRUE. then find the 
C                intersection of the ellipse with plane I.  Otherwise 
C                go to the next plane.
C
C$ Detailed_Output
C
C     POINTX     An array of the x-component of the ordered pairs 
C                ( COS, SIN) where COS*MAJOR + SIN*MINOR is a point of
C                intersection of the ellipse with one of the planes
C                designated by the SOLVE array.  
C
C     POINTY     An array of the y-component of the ordered pairs 
C                ( COS, SIN) where COS*MAJOR + SIN*MINOR is a point of
C                intersection of the ellipse with one of the planes
C                designated by the SOLVE array.
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
C$ Detailed_Description
C
C      This routine accepts:
C
C      1.) An ellipse defined by a CENTER and vectors MAJOR and MINOR
C          which represent the semi-major and minor axes of the ellipse.
C
C      2.) An array of normal vectors and associated constant terms for
C          the equations of the ellipse
C
C      3.) An integer giving the number of planes
C
C      4.) An array of logicals (SOLVE).  SOLVE(I) = .TRUE. indicates 
C          that the routine should look for an intersection between the 
C          ellipse and plane(I).
C
C      It returns those points of intersection between the ellipse and
C      designated planes.
C
C$ Method
C
C      Check the flag SOLVE to see if we should look for an 
C      intersection.
C
C          If so call ELIPLN to obtain the intersection(s).
C          and load them into the POINTS
C
C      Continue these steps until each flag has been checked
C
C$ Examples
C
C     None.
C
C$ External_References
C
C     ELIPLN, VDOT
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
C     Version 1, 11-JUN-1986
C
C-

C
C   Optlib functions
C
      DOUBLE PRECISION VDOT

C
C   Local Stuff
C
      INTEGER          I,J,K
      INTEGER          FOUND

      DOUBLE PRECISION COSINS(2)
      DOUBLE PRECISION SINES(2)
      DOUBLE PRECISION C

      MEETNS = 0

      DO I = 1,N
         IF (SOLVE(I)) THEN

            C  = CONSTS(I) - VDOT(CENTER,NORMLS(1,I))

            CALL ELIPLN ( NORMLS(1,I), C,
     .                    MAJOR, MINOR, FOUND,
     .                    COSINS,       SINES        )

             DO J = 1,FOUND
                MEETNS         = MEETNS + 1
                POINTX(MEETNS) = COSINS(J)
                POINTY(MEETNS) = SINES(J)
             END DO
          END IF
      END DO

      RETURN
      END
