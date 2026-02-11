C$ Procedure

            SUBROUTINE  OVRLAP (CENTR1, R1, CENTR2, R2, INTSCT)

C$ Abstract
C
C     Determine the degree of overlap between two disks, whose planes
C     are othogonal to the line of sight to there centers.
C
C$ Keywords
C
C     GEOMETRY, OCCULTATION, ECLIPSE
C
C$ Declarations

      DOUBLE PRECISION CENTR1(3)
      DOUBLE PRECISION R1
      DOUBLE PRECISION CENTR2(3)
      DOUBLE PRECISION R2
      INTEGER          INTSCT

C$ Brief_I/O
C
C     VARIABLE     I/O  DESCRIPTION
C     --------     ---  ------------------------------------------------
C     CENTR1        I   Position of the center of the first disk
C     R1            I   Radius of the first disk
C     CENTR2        I   Position of the center of the second disk
C     R2            I   Radius of the second disk
C     INTSCT        O   Flag indicating degree of overlap.
C
C$ Detailed_Input
C
C     CENTR1     Position of the center of the first disk.
C
C     R1         Radius of the first disk.
C
C     CENTR2     Position of the center of the  second disk.
C
C     R2         Radius of the  second disk.
C
C$ Detailed_Output
C
C
C     INTSCT     Integer flag indicating blockage by the second
C                disk.  Possible values: -1,0,1,2,3
C
C                If   INTSCT = -1 at least one of the disks is centered
C                                  at the origin.
C                If   INTSCT = 0, the two disks do not intersect.
C
C                If   INTSCT = 1, the first disk lies inside the 
C                                   second disk 
C
C                If   INTSCT = 2  the second disk lies inside the 
C                                  second 
C
C                If   INTSCT = 3, the two disks intersect in a proper
C                                  subset of both.
C
C$ Detailed Description
C
C
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
C$ Method
C
C
C$ Examples
C
C     None.
C
C$ External_References
C
C  VNORM, VDOT, VSCL
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
C     Version 1, 19-JUN-1986
C
C-

C
C   Optlib functions
C
      DOUBLE PRECISION VNORM
      DOUBLE PRECISION VDOT
      DOUBLE PRECISION VSEP
C
C     Let: ALPHA be the angle from the center of the first disk to
C          its edge
C
C          BETA  be the angle from the center of the  second
C          disk to its edge.
C
C          GAMMA be the angle between the centers of the two disks.
C
C     the disks of the two disks overlap iff
C
C              ALPHA + BETA > GAMMA   
C
C       <===>  cos(ALPHA + BETA) < cos(GAMMA)
C
C       <===>  cos(ALPHA)cos(BETA) - sin(ALPHA)sin(BETA) < cos(GAMMA)
C
C     If the two disks overlap, the disk of the first disk lies 
C     inside the disk of the second disk iff
C
C              ALPHA + GAMMA   < (or =)  BETA
C
C     <===> cos(ALPHA + GAMMA) > (or =) BETA
C
C     <===> cos(ALPHA)cos(GAMMA)-sin(ALPHA)sin(GAMMA) > (or =) cos(BETA)
C
C
C     If the two disks overlap, the disk of the second disk lies 
C     inside the disk of the first disk iff
C
C              BETA + GAMMA   < (or =)  ALPHA
C
C     <===> cos(BETA + GAMMA) > (or =) ALPHA
C
C     <===> cos(BETA)cos(GAMMA)-sin(BETA)sin(GAMMA) > (or =) cos(ALPHA)
C
C     Otherwise INTSCT = 0.
C

      DOUBLE PRECISION A
      DOUBLE PRECISION B
      DOUBLE PRECISION RECIPA
      DOUBLE PRECISION RECIPB
      DOUBLE PRECISION ALPHA
      DOUBLE PRECISION BETA
      DOUBLE PRECISION GAMMA
      DOUBLE PRECISION CALPHA
      DOUBLE PRECISION SALPHA
      DOUBLE PRECISION TALPHA
      DOUBLE PRECISION CBETA
      DOUBLE PRECISION SBETA
      DOUBLE PRECISION TBETA
      DOUBLE PRECISION CGAMMA
      DOUBLE PRECISION SGAMMA

      DOUBLE PRECISION UNITA(3)
      DOUBLE PRECISION UNITB(3)


C     Let : A be the range to the first disk
C
C           B be the range to the second disk
C

      A         = VNORM( CENTR1 )
      B         = VNORM( CENTR2 )

      IF ( (A.EQ.0) .OR. (B.EQ.0) ) THEN
         INTSCT = -1
         RETURN
      END IF

      TALPHA = R1/A
      TBETA  = R2/B

      CALPHA = 1/DSQRT( 1 + TALPHA * TALPHA )
      CBETA  = 1/DSQRT( 1 + TBETA  * TBETA  )

      SALPHA = TALPHA * CALPHA
      SBETA  = TBETA  * CBETA


      GAMMA  = VSEP(CENTR1, CENTR2)

      ALPHA  = DATAN2 ( SALPHA, CALPHA )
      BETA   = DATAN2 ( SBETA,  CBETA  )

C
C     Initially we assume that the disks of the two disks do not
C     intersect
C
      INTSCT    = 0

      IF ( ALPHA + BETA .GT. GAMMA ) THEN 
C     ! the two disks intersect

         IF ( ALPHA + GAMMA .LE. BETA ) THEN 
C        ! disk 1 is inside disk 2

            INTSCT =  1

         ELSE IF ( BETA + GAMMA .LE. ALPHA ) THEN 
C        ! disk 2 is inside disk 1

            INTSCT =  2

         ELSE 
C        ! the two disks intersect "properly"

            INTSCT = 3              

         END IF
      END IF

      RETURN
      END
