C$ Procedure
 
      SUBROUTINE ESCLIP (XMIN, XMAX, YMIN, YMAX,
     >                   X1,   Y1,   X2,   Y2,
     >                   INSIDE )
 
C$ Abstract
C
C     Given the boundaries of a rectangle in the plane and the endpoints
C     of a segment, this routine returns that portion of the segement
C     within the interior of the rectangle.
C
C$ Keywords
C
C     GEOMETRY, UTILITY, GRAPHICS
C
C$ Declarations
 
      DOUBLE PRECISION XMIN
      DOUBLE PRECISION XMAX
      DOUBLE PRECISION YMIN
      DOUBLE PRECISION YMAX
      DOUBLE PRECISION X1
      DOUBLE PRECISION Y1
      DOUBLE PRECISION X2
      DOUBLE PRECISION Y2
      LOGICAL          INSIDE
 
C$ Brief_I/O
C
C     VARIABLE  I/O  DESCRIPTION
C     --------  ---  ---------------------------------------------------
C
C     XMIN       I   X value of left edge of the rectangle
C     XMAX       I   X value of right edge of the rectangle
C     YMIN       I   Y value of bottom edge of the rectangle
C     YMAX       I   Y value of the top edge of the rectangle
C     X1        I/O  X-coordinate of first endpoint of the segment
C     Y1        I/O  Y-coordinate of first endpoint of the segment
C     X2        I/O  X-coordinate of the second endpoint of the segment
C     Y2        I/O  Y-coordinate of the second endpoint of the segment
C     INSIDE     O   Indicates if the segment intersects the rectangle
C
C$ Detailed_Input
C
C     XMIN    X value of left edge of the rectangle. All points (x,y)
C             inside the rectangle satisfy x > XMIN
C
C     XMAX    X value of right edge of the rectangle. All points (x,y)
C             inside the rectangle satisfy x < XMAX.
C
C     YMIN    Y value of bottom edge of the rectangle. All points (x,y)
C             inside the rectangle satisfy y > YMIN
C
C     YMAX    Y value of top edge of the rectangle. All points (x,y)
C             inside the rectangle satisfy y <  YMAX
C
C     X1      X-coordinate of first endpoint of the segment
C
C     Y1      Y-coordinate of first endpoint of the segment
C
C     X2      X-coordinate of the second endpoint of the segment
C
C     Y2      Y-coordinate of the second endpoint of the segment
C
C$ Detailed_Output
C
C     If the input segment intersects the rectangle, then X1,Y1,X2,Y2
C     are the coordinates of the the endpoints of the segment of
C     intersection with the rectangle
C
C     X1      X-coordinate of first endpoint of the segment
C
C     Y1      Y-coordinate of first endpoint of the segment
C
C     X2      X-coordinate of the second endpoint of the segment
C
C     Y2      Y-coordinate of the second endpoint of the segment
C
C     INSIDE  If the returned segment lies inside the rectangle
C             INSIDE is set to .TRUE.  Otherwise it is .FALSE.
C
C$ Detailed_Description
C
C     This routine determines whether or not an input segment intersects
C     the rectangle defined by XMIN, XMAX, YMIN, and YMAX.  If it does
C     it sets the logical flag INSIDE to .TRUE.  and overwrites the
C     input endpoints with the endpoints of the intersection segment.
C     Otherwise INSIDE is set to .FALSE. and the subroutine returns;
C     the endpoints are not modified.
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
C     Version 1, 3-JULY-1986
C
C-
 
C
C   Local Variables
C
      LOGICAL          ONENSD
      LOGICAL          TWONSD
      LOGICAL          CHECK
 
      DOUBLE PRECISION X
      DOUBLE PRECISION Y
      DOUBLE PRECISION DX
      DOUBLE PRECISION DY
      DOUBLE PRECISION XMINX1
      DOUBLE PRECISION XMAXX1
      DOUBLE PRECISION YMINY1
      DOUBLE PRECISION YMAXY1
      DOUBLE PRECISION S
      DOUBLE PRECISION XEND (2)
      DOUBLE PRECISION YEND (2)
 
      INTEGER          POSSBL
      INTEGER          START
      INTEGER          NWPNTS
 
C     First we see if the endpoints lie in a region such that
C     Clipping in necessary
C
C                           5   |    4   |    3
C                               |        |
C                        -------+--------+--------
C                               |        |
C                           6   |    9   |    2
C                               |        |
C                        -------+--------+--------
C                               |        |
C                           7   |    8   |    1
C
 
      ONENSD      = .FALSE.
      TWONSD      = .FALSE.
 
      IF ( X1 .GT. XMAX ) THEN
         IF ( Y1 .GT. YMAX ) THEN
C           the first endpoint in in region 3
            CHECK = (X2 .LT. XMAX ) .AND. ( Y2 .LT. YMAX )
         ELSE IF ( Y1 .LT. YMIN ) THEN
C           the first endpoint in in region 1
            CHECK = (X2 .LT. XMAX ) .AND. ( Y2 .GT. YMIN )
         ELSE
C           the first endpoint in in region 2
            CHECK = (X2 .LT. XMAX )
         END IF
 
      ELSE IF ( X1 .LT. XMIN ) THEN
         IF ( Y1 .GT. YMAX ) THEN
C           the first endpoint in in region 5
            CHECK = (X2 .GT. XMIN ) .AND. ( Y2 .LT. YMAX )
         ELSE IF ( Y1 .LT. YMIN ) THEN
C           the first endpoint in in region 7
            CHECK = (X2 .GT. XMIN ) .AND. ( Y2 .GT. YMIN )
         ELSE
C           the first endpoint in in region 6
            CHECK = (X2 .GT. XMIN )
         END IF
      ELSE
         IF ( Y1 .GT. YMAX ) THEN
C           the first endpoint in in region 4
            CHECK = ( Y2 .LT. YMAX )
         ELSE IF ( Y1 .LT. YMIN ) THEN
C           the first endpoint in in region 8
            CHECK = ( Y2 .GT. YMIN )
         ELSE
C           the first endpoint in in region 9
            CHECK =      ( X2 .GT. XMAX )
     >              .OR. ( X2 .LT. XMIN )
     >              .OR. ( Y2 .GT. YMAX )
     >              .OR. ( Y2 .LT. YMIN )
            INSIDE = .TRUE.
 
            IF ( .NOT. CHECK ) THEN
               RETURN
            END IF
 
            ONENSD     = .TRUE.
         END IF
      END IF
 
 
      IF (CHECK) THEN
 
         IF ( ONENSD     ) THEN
            POSSBL      = 1
         ELSE
            TWONSD      =       ( X2 .LE. XMAX )
     >                    .AND. ( X2 .GE. XMIN )
     >                    .AND. ( Y2 .LE. YMAX )
     >                    .AND. ( Y2 .GE. YMIN )
            IF ( TWONSD     ) THEN
               POSSBL    = 1
            ELSE
               POSSBL    = 2
            END IF
         END IF
 
         NWPNTS          = 0
 
         DX              = X2   - X1
         DY              = Y2   - Y1
 
C
C        First check to see it the input segment is horizontal.
C
         IF ( DY .EQ. 0 ) THEN
            IF      (( X1 .LT. XMIN ) .AND. (X2 .GT. XMAX) ) THEN
               X1     = XMIN
               X2     = XMAX
               INSIDE = .TRUE.
               RETURN
            ELSE IF (( X1 .LT. XMIN ) .AND. (X2 .GT. XMIN) ) THEN
               X1     = XMIN
               INSIDE = .TRUE.
               RETURN
 
            ELSE IF (( X2 .LT. XMIN ) .AND. ( X1 .GT. XMAX )) THEN
               X1     = XMAX
               X2     = XMIN
               INSIDE = .TRUE.
               RETURN
 
            ELSE IF (( X2 .LT. XMIN ) .AND. ( X1 .GT. XMIN )) THEN
               X2     = XMIN
               INSIDE = .TRUE.
               RETURN
 
            END IF
         END IF
 
 
C
C        Next check to see it the input segment is vertical.
C
         IF ( DX .EQ. 0 ) THEN
            IF      (( Y1 .LT. YMIN ) .AND. (Y2 .GT. YMAX) ) THEN
               Y1     = YMIN
               Y2     = YMAX
               INSIDE = .TRUE.
               RETURN
            ELSE IF (( Y1 .LT. YMIN ) .AND. (Y2 .GT. YMIN) ) THEN
               Y1     = YMIN
               INSIDE = .TRUE.
               RETURN
 
            ELSE IF (( Y2 .LT. YMIN ) .AND. ( Y1 .GT. YMAX )) THEN
               Y1     = YMAX
               Y2     = YMIN
               INSIDE = .TRUE.
               RETURN
 
            ELSE IF (( Y2 .LT. YMIN ) .AND. ( Y1 .GT. YMIN )) THEN
               Y2     = YMIN
               INSIDE = .TRUE.
               RETURN
 
            END IF
         END IF
 
C
C        If the segment is not horizontal OR vertical then check for an
C        with:
C             the top    edge of the rectangle
C             the bottom edge of the rectangle
C             the right  edge of the rectangle
C             the left   edge of the rectangle
C
C
C       check for an intersection with the top edge of the rectangle
C
 
         YMAXY1        = YMAX - Y1
 
         IF (       (     NWPNTS             .LT.  POSSBL            )
     >        .AND. (     (( 0 .LT. YMAXY1 ) .AND. (YMAXY1 .LT. DY))
     >               .OR. (( 0 .GT. YMAXY1 ) .AND. (YMAXY1 .GT. DY)))  )
     >   THEN
 
            S   =   YMAXY1/DY
            X   =   S*DX + X1
 
            IF ((X .LT. XMAX) .AND. (X .GT. XMIN)) THEN
               NWPNTS            = NWPNTS    + 1
               XEND (NWPNTS    ) = X
               YEND (NWPNTS    ) = YMAX
            END IF
         END IF
 
C
C       check for an intersection with the bottom edge of the rectangle
C
         YMINY1        = YMIN - Y1
 
         IF (       (     NWPNTS             .LT.  POSSBL            )
     >        .AND. (     (( 0 .LT. YMINY1 ) .AND. (YMINY1 .LT. DY))
     >               .OR. (( 0 .GT. YMINY1 ) .AND. (YMINY1 .GT. DY)))  )
     >   THEN
 
            S   =   YMINY1/DY
            X   =   S*DX + X1
 
            IF ((X .LT. XMAX) .AND. (X .GT. XMIN)) THEN
               NWPNTS            = NWPNTS    + 1
               XEND (NWPNTS    ) = X
               YEND (NWPNTS    ) = YMIN
            END IF
         END IF
 
C
C       check for an intersection with the right edge of the rectangle
C
 
         XMAXX1        = XMAX - X1
 
         IF (       (     NWPNTS             .LT.  POSSBL            )
     >        .AND. (     (( 0 .LT. XMAXX1 ) .AND. (XMAXX1 .LT. DX))
     >               .OR. (( 0 .GT. XMAXX1 ) .AND. (XMAXX1 .GT. DX)))  )
     >   THEN
 
            S   =   XMAXX1/DX
            Y   =   S*DY + Y1
 
            IF ((Y .LT. YMAX) .AND. (Y .GT. YMIN)) THEN
               NWPNTS            = NWPNTS     + 1
               XEND (NWPNTS    ) = XMAX
               YEND (NWPNTS    ) = Y
            END IF
         END IF
 
C
C       check for an intersection with the left edge of the rectangle
C
         XMINX1        = XMIN - X1
 
         IF (       (     NWPNTS             .LT.  POSSBL            )
     >        .AND. (     (( 0 .LT. XMINX1 ) .AND. (XMINX1 .LT. DX))
     >               .OR. (( 0 .GT. XMINX1 ) .AND. (XMINX1 .GT. DX)))  )
     >   THEN
 
            S   =   XMINX1/DX
            Y   =   S*DY + Y1
 
            IF ((Y .LT. YMAX) .AND. (Y .GT. YMIN)) THEN
               NWPNTS            = NWPNTS     + 1
               XEND (NWPNTS    ) = XMIN
               YEND (NWPNTS    ) = Y
            END IF
         END IF
 
         IF ( NWPNTS     .EQ. POSSBL  ) THEN
            INSIDE  = .TRUE.
            START   = 1
 
            IF ( .NOT. ONENSD     ) THEN
              X1    = XEND (START)
              Y1    = YEND (START)
              START = START + 1
            END IF
 
            IF ( .NOT. TWONSD     ) THEN
              X2    = XEND (START)
              Y2    = YEND (START)
            END IF
 
         ELSE
            INSIDE = .FALSE.
         END IF
 
      ELSE
         INSIDE = .FALSE.
      END IF
 
 
      RETURN
 
      END
 
