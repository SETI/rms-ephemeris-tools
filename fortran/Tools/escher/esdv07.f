C$Procedure      ESDV07 ( Postscript---Portrait)
 
      SUBROUTINE ESDV07 ( TOP,   BOTTOM, LEFT, RIGHT,
     .                    HMIN,  HMAX,   VMIN, VMAX,
     .                    NSEGS, SEGS               )
 
 
C$ Abstract
C
C     This is an umbrella routine for the Postscript support
C     used by ESCHER.
C
C$ Required_Reading
C
C     ESCHER.
C
C$ Keywords
C
C     GRAPHICS
C
C$ Declarations
 
      INTEGER               TOP
      INTEGER               BOTTOM
      INTEGER               LEFT
      INTEGER               RIGHT
 
      INTEGER               NSEGS
      INTEGER               SEGS  ( * )
 
      INTEGER               HMIN
      INTEGER               HMAX
      INTEGER               VMIN
      INTEGER               VMAX
 
 
C$ Brief_I/O
C
C     Variable  I/O  Description
C     --------  ---  --------------------------------------------------
C     NSEGS      I   See ESDR07
C     SEGS       I   See ESDR07
C
C     HMIN       I   See ESCL07
C     HMAX       I   See ESCL07
C     VMIN       I   See ESCL07
C     VMAX       I   See ESCL07
C
C     TOP        O   See ESPL07
C     BOTTOM     O   See ESPL07
C     LEFT       O   See ESPL07
C     RIGHT      O   See ESPL07
C
C$ Detailed_Input
C
C     See the individual entry points.
C
C$ Detailed_Output
C
C     See the individual entry points.
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
C     This routine serves as an umbrella for ESHCER's Postscript
C     support --- portrait mode.
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
C
C      "Postscript Language, Tutorial and Cookbook" Addison-Wesley
C      Publishing Company, Reading Massachusetts. September 1987.
C
C      "Postscript Language Reference Manual" Addison-Wesley
C      Publishing Company, Reading Massachusetts. September 1987.
C
C$ Author_and_Institution
C
C     W.L. Taber     (JPL)
C     I.M. Underwood (JPL)
C
C$ Version
C
C-    Beta Version 1.0.0, 22-MAY-1990 (WLT) (IMU)
C-    output file name changed 9/7/94   (smr)
C-&
 
C
C
C     ESCHER Parameters
C
C
C     Boundaries of native pixel/line space.
C
C     The default unit size for Postscript output is 1/72 inches.
C     Often times we can do better than this.  We shall assume
C     change the scale in any output file so that 1 unit is 1/720
C     inches. Thus a single unit will represent an 0.1 points instead of
C     a point.  We will leave a border of 1/2 inch around each side.
C
C MRS modified margins to 1 inch above, 2.5 inches below

      INTEGER               MINX
      PARAMETER           ( MINX   =  360 )
 
      INTEGER               MAXX
      PARAMETER           ( MAXX   = 5760 )
 
      INTEGER               MINY
c      PARAMETER           ( MINY   = 360  )
      PARAMETER           ( MINY   = 1800 )
 
      INTEGER               MAXY
c      PARAMETER           ( MAXY   = 7560 )
      PARAMETER           ( MAXY   = 7200 )
 
 
 
C
C     Local variables
C
      INTEGER               BP
      INTEGER               BL
      INTEGER               EP
      INTEGER               EL
      INTEGER               COLOR
      INTEGER               OFFSET
      INTEGER               MAXDSP
 
      INTEGER               ZERO
      PARAMETER           ( ZERO = 0 )
 
      INTEGER               BUFSZ
      PARAMETER           ( BUFSZ   = 64 )
 
      INTEGER               XARRAY ( BUFSZ   )
      INTEGER               YARRAY ( BUFSZ   )
 
      INTEGER               COUNT
      INTEGER               LSTCOL
      INTEGER               LASTEP
      INTEGER               LASTEL
 
      INTEGER               I
      INTEGER               M
 
      CHARACTER*(40)        MOVETO
      CHARACTER*(40)        LINETO
      CHARACTER*(40)        LASTLN
C
C     Saved variables
C
      CHARACTER*(5)        GRAY   ( -1 : 10 )
     .                              / '1.0 G',
     .                                '1.0 G',
     .                                '0.0 G',
     .                                '0.1 G',
     .                                '0.2 G',
     .                                '0.3 G',
     .                                '0.4 G',
     .                                '0.5 G',
     .                                '0.6 G',
     .                                '0.7 G',
     .                                '0.8 G',
     .                                '0.9 G'  /
      SAVE                  GRAY
 
 
      INTEGER               UNIT
      SAVE                  UNIT
 
 
      LOGICAL               OPEN   / .FALSE. /
      SAVE                  OPEN

        integer         oldcol/ -9999 /
        save            oldcol

        integer         LASTNB

        integer         f1, f2
 
 
c File name as set by ESFILE()
        include         'escomm.inc'
 
C$Procedure ESPL07
 
      ENTRY ESPL07 ( LEFT, RIGHT, BOTTOM, TOP   )
 
C$ Abstract
C
C      Return the graphics boundaries to be used for a postscript
C      file written for a normal 8.5 by 11 inch page.
C
C$ Required_Reading
C
C      ESCHER and ESDO
C
C$ Keywords
C
C      ESCHER
C
C$ Declarations
C
C     INTEGER               LEFT
C     INTEGER               RIGHT
C     INTEGER               BOTTOM
C     INTEGER               TOP
C
C$ Brief_I/O
C
C      VARIABLE  I/O  DESCRIPTION
C      --------  ---  --------------------------------------------------
C
C      LEFT       O   The minimum x value to be used by postscript
C      RIGHT      O   The maximum x value to be used by postscript
C      BOTTOM     O   The minimum y value to be used by postscript
C      TOP        O   The maximum y value to be used by postscript
C
C$ Detailed_Input
C
C      None.
C
C$ Detailed_Output
C
C      LEFT       The minimum x value for the postscript file.
C
C      RIGHT      The maximum x value for the postscript file.
C
C      BOTTOM     The minimum y value for the postscript file.
C
C      TOP        The maximum y value for the postscript file.
C
C$ Parameters
C
C      None.
C
C$ Exceptions
C
C      None.
C
C$ Particulars
C
C      This routine is provided as a utility for programs that
C      need to determine the dimensions of the Postscript user
C      device.
C
C$ Examples
C
C      None.
C
C$ Restrictions
C
C      None.
C
C$ Files
C
C      None.
C
C$ Author_and_Institution
C
C      W. L. Taber     (JPL)
C      I. M. Underwood (JPL)
C
C$ Literature_References
C
C      "Postscript Language, Tutorial and Cookbook" Addison-Wesley
C      Publishing Company, Reading Massachusetts. September 1987.
C
C      "Postscript Language Reference Manual" Addison-Wesley
C      Publishing Company, Reading Massachusetts. September 1987.
C
C$ Version_and_Date
C
C      Version 1, 22-MAY-1990
C
C-&
C
      LEFT   = MINX
      RIGHT  = MAXX
      BOTTOM = MINY
      TOP    = MAXY
 
      RETURN
 
 
C$ Procedure ESDR07
 
      ENTRY ESDR07 ( NSEGS, SEGS )
 
C$ Abstract
C
C     Instruct POSTSCRIPT to draw a set of vectors.
C
C$ Required_Reading
C
C     ESCHER and ESDO
C
C$ Keywords
C
C     GRAPHICS
C
C$ Declarations
C
C      INTEGER               NSEGS
C      INTEGER               SEGS  ( * )
C
C$ Brief_I/O
C
C     VARIABLE  I/O  DESCRIPTION
C     --------  ---  ---------------------------------------------------
C     NSEGS      I   Number values stored in the segment buffer.
C     SEGS       I   The segment buffer.
C
C$ Detailed_Input
C
C     NSEGS      Number values stored in the segment buffer. NSEGS
C                must be a multiple of 5.
C
C     SEGS       The segment buffer.  The I'th segment is given
C                by:
C
C                SEGS(I*5-4) --- horizontal component of the
C                                beginning of the I'th segment.
C
C                SEGS(I*5-4) --- Vertical component of the
C                                beginning of the I'th segment.
C
C                SEGS(I*5-4) --- horizontal component of the
C                                ending of the I'th segment.
C
C                SEGS(I*5-4) --- vertical component of the
C                                ending of the I'th segment.
C
C                SEGS(I*5)   --- color (in this case the grayscale)
C                                of the I'th segment.
C
C$ Detailed_Output
C
C     None.
C
C$ Parameters
C
C     None.
C
C$ Exceptions
C
C     Error free.
C
C$ Files.
C
C     None.
C
C$ Particulars
C
C      This routine writes postscript commands for drawing vectors.
C
C$ Examples
C
C      None.
C
C$ Restrictions
C
C      None.
C
C$ Literature_References
C
C      "Postscript Language, Tutorial and Cookbook" Addison-Wesley
C      Publishing Company, Reading Massachusetts. September 1987.
C
C      "Postscript Language Reference Manual" Addison-Wesley
C      Publishing Company, Reading Massachusetts. September 1987.
C
C$ Author_and_Institution
C
C     W.L. Taber, I.M. Underwood (JPL)
C
C$ Version_and_Date
C
C     Version 1, 24-MAY-1990
C
C-
C

      IF ( .NOT. OPEN ) THEN
 
         OPEN = .TRUE.
 
         CALL GETLUN ( UNIT )
         outuni = UNIT
         if (outfil .eq. ' ') outfil = 'escher.ps'
         OPEN ( UNIT            = UNIT,
     &          FILE            = outfil,
     &          STATUS          = 'UNKNOWN')
 
        f2 = LASTNB(outfil)
        do 100 f1 = f2, 1, -1
                if (outfil(f1:f1) .eq. ']' .or.
     &              outfil(f1:f1) .eq. ':' .or.
     &              outfil(f1:f1) .eq. '/' ) goto 101
100     continue
101     continue
                
        write (unit, '(a)') '%!PS-Adobe-2.0 EPSF-2.0'
        write (unit, '(a)') '%%Title: ' // outfil(f1+1:f2)
        write (unit, '(a)') '%%Creator: ' // creator(1:LASTNB(creator))
        write (unit, '(a)') '%%BoundingBox: 0 0 612 792'
        write (unit, '(a)') '%%Pages: 1'
        write (unit, '(a)') '%%DocumentFonts: '// fonts(1:LASTNB(fonts))
        write (unit, '(a)') '%%EndComments'

         WRITE ( UNIT, FMT='(A)' ) '% '
         WRITE ( UNIT, FMT='(A)' ) '0.1 0.1 scale'
         WRITE ( UNIT, FMT='(A)' ) '8 setlinewidth'
         WRITE ( UNIT, FMT='(A)' ) '1 setlinecap'
         WRITE ( UNIT, FMT='(A)' ) '1 setlinejoin'
         WRITE ( UNIT, FMT='(A)' ) '/L {lineto} def'
         WRITE ( UNIT, FMT='(A)' ) '/M {moveto} def'
         WRITE ( UNIT, FMT='(A)' ) '/N {newpath} def'
         WRITE ( UNIT, FMT='(A)' ) '/G {setgray} def'
         WRITE ( UNIT, FMT='(A)' ) '/S {stroke} def'
 
      END IF
 
 
      IF ( NSEGS .LT. 5 ) THEN
         RETURN
      END IF
 
C
C     If still here we are going to draw something.
C     Load the segment endpoints into the integer arrays XARRAY and
C     YARRAY
C
      MOVETO          = ' '
      LINETO          = ' '
      LASTLN          = ' '
      OFFSET          = 0
 
      BP              = SEGS(OFFSET + 1)
      BL              = SEGS(OFFSET + 2)
      EP              = SEGS(OFFSET + 3)
      EL              = SEGS(OFFSET + 4)
      COLOR           = SEGS(OFFSET + 5)
 
      COUNT           = 1
      XARRAY( COUNT ) = BP
      YARRAY( COUNT ) = BL
 
      COUNT           = COUNT + 1
      XARRAY( COUNT ) = EP
      YARRAY( COUNT ) = EL
 
C
C     Save the current grayscale and endpoint
C
      LSTCOL          = SEGS(5)
      LASTEP          = EP
      LASTEL          = EL
 
C
C     Determine whether or not anything ever gets drawn.
C
      MAXDSP          = MAX( ABS(EP-BP), ABS(EL-BL) )
 
C
C     Now sift through the remaining segments
C
      DO I = 6, NSEGS, 5
C
C        Determine the beginning and ending points of the next segment
C
         OFFSET = I - 1
 
         BP     = SEGS(OFFSET + 1)
         BL     = SEGS(OFFSET + 2)
         EP     = SEGS(OFFSET + 3)
         EL     = SEGS(OFFSET + 4)
         COLOR  = SEGS(OFFSET + 5)
 
 
         IF (       (BP    .EQ. LASTEP )
     .        .AND. (BL    .EQ. LASTEL )
     .        .AND. (COLOR .EQ. LSTCOL )
     .        .AND. (COUNT .LT. BUFSZ  ) ) THEN
C
C            In this case the beginning of the current segment matches
C            the ending of the last segment AND the colors have not
C            changed AND there is still room MINX in the string buffer.
C
C            Save the current endpoint ...
C
             LASTEP          = EP
             LASTEL          = EL
 
 
C
C            See if there is any displacement between a beginning
C            and ending segment.
C
             MAXDSP           = MAX( MAXDSP,
     .                               MAX( ABS(EP-BP), ABS(EL-BL) )
     .                             )
 
C
C            ... and add this endpoint to the current string of segments
C
             COUNT           = COUNT + 1
 
             XARRAY( COUNT ) = EP
             YARRAY( COUNT ) = EL
 
         ELSE
C
C           In this case either the "color" changed, we ran out of room
C           or the beginning of the current segment did not match the
C           end of the last one.  In any case we have to dump the
C           current string of segments to the display device.
C
C           First however, if this polygonal path never left the
C           starting point, we are going to make it move at least
C           one pixel.
C
            IF ( MAXDSP .EQ. 0 ) THEN
 
               IF ( XARRAY(COUNT) .LT. MAXX ) THEN
                  XARRAY(COUNT) = XARRAY(COUNT)+1
               ELSE
                  XARRAY(COUNT) = XARRAY(COUNT)-1
               END IF
 
            END IF
 
C
C           If the thickness is zero, we don't have to draw anything.
C
ccc         IF ( LSTCOL .Ge. 0 ) THEN
 
C
C              Position the cursor.
C
C              We need to construct the postscript command for
C              positioning the pen used for drawing objects.
C              This command has the form:
C
C                 'X Y moveto'
C
C              where X and Y are integer strings giving the X and
C              Y coordinates to move to.
C
               CALL OPAIRI ( ' ', XARRAY(1),
     .                       ' ', YARRAY(1), ' M', MOVETO )
 
C
C              Now positioon the pen
C
               if (LSTCOL .Ge. 0) WRITE ( UNIT, FMT='(A)' ) 'N'
               if (LSTCOL .Ge. 0) WRITE ( UNIT, FMT='(A)' )  
     .                                  MOVETO(2:LASTNB(MOVETO))
               xsave = xarray(1)
               ysave = yarray(1)
 
               CALL OPAIRI ( ' ',        XARRAY(1),
     .                       ' ',        YARRAY(1),
     .                       ' L',  LASTLN )
 
C
C              Now we just draw the vectors one at a time.
C
               DO M = 2, COUNT
C
C                 We need to construct the commands for moving the
C                 pen so that a path is created. The form of the command
C                 is:
C
C                    'X Y lineto'
C
C                 where X and Y are integer strings giving the X and
C                 Y coordinates to move to.
C
                  CALL OPAIRI ( ' ',        XARRAY(M),
     .                          ' ',        YARRAY(M),
     .                          ' L',  LINETO     )
 
C
C                 Write the command.
C
                  IF ( LINETO .NE. LASTLN ) THEN
                     if (LSTCOL .Ge. 0) WRITE (UNIT,FMT='(A)')
     .                                  LINETO(2:LASTNB(LINETO))
                        xsave = xarray(m)
                        ysave = yarray(m)
                        drawn = .TRUE.
                  END IF
 
                  LASTLN = LINETO
 
               END DO
 
 
C
C              Finally, we need the lines to be filled with ink.
C
C              Since we have changed the scale facter, we need to
C              boost the linewidth by a factor of 10.
C
               IF ( LSTCOL .GT. 10 ) THEN
                  LSTCOL = 1
               END IF
 
               if (LSTCOL .ne. oldcol .and. LSTCOL .ge. 0) then
                  WRITE ( UNIT, FMT='(A)' ) GRAY(LSTCOL)
                  oldcol = LSTCOL
               end if
               if (LSTCOL .ge. 0) WRITE ( UNIT, FMT='(A)' ) 'S'
 
ccc         END IF
C
C           Now we start the string of segments all over again ...
C
            COUNT           = 1
            XARRAY( COUNT ) = BP
            YARRAY( COUNT ) = BL
 
            COUNT           = COUNT + 1
            XARRAY( COUNT ) = EP
            YARRAY( COUNT ) = EL
 
C
C           Start keeping track of this polygons displacement from
C           its starting point.
C
            MAXDSP          = MAX( ABS(EP-BP), ABS(EL-BL) )
C
C           ... and store the current endpoints.
C
            LSTCOL          = COLOR
            LASTEP          = EP
            LASTEL          = EL
 
         END IF
 
      END DO
 
C
C     If this polygonal path never left the starting point, we are
C     going to make it move at least one pixel.
C
      IF ( MAXDSP .EQ. 0 ) THEN
 
         IF ( XARRAY(COUNT) .LT. MAXX ) THEN
            XARRAY(COUNT) = XARRAY(COUNT)+1
         ELSE
            XARRAY(COUNT) = XARRAY(COUNT)-1
         END IF
 
      END IF
 
C
C     Write out all of the remaining segments. This is just like before.
C
C     If the color (line thickness) is zero, we don't have
C     to draw anything.
C
ccc   IF ( LSTCOL .Ge. 0 ) THEN
 
C
C        Position the pen.
C
         CALL OPAIRI ( ' ', XARRAY(1),
     .                 ' ', YARRAY(1), ' M', MOVETO )
 
         if (LSTCOL .ge. 0) WRITE ( UNIT, FMT='(A)' ) 'N'
         if (LSTCOL .ge. 0) WRITE ( UNIT, FMT='(A)' )
     .                                  MOVETO(2:LASTNB(MOVETO))
         xsave = xarray(1)
         ysave = yarray(1)
 
         CALL OPAIRI ( ' ', XARRAY(1),
     .                 ' ', YARRAY(1), ' L', LASTLN )
 
C
C        Now we just draw the vectors one at a time.
C
         DO M = 2, COUNT
 
            CALL OPAIRI ( ' ',        XARRAY(M),
     .                    ' ',        YARRAY(M),
     .                    ' L',  LINETO     )

 
C
C           Write the command.
C
            IF ( LINETO .NE. LASTLN ) THEN
                if (LSTCOL .ge. 0) WRITE (UNIT,FMT='(A)')
     .                                  LINETO(2:LASTNB(LINETO))
                xsave = xarray(m)
                ysave = yarray(m)
                drawn = .TRUE.
            END IF
 
            LASTLN = LINETO
 
         END DO
 
C
C        Finally, we need the lines to be filled with ink.
C
         IF ( LSTCOL .GT. 10 ) THEN
            LSTCOL = 1
         END IF
 
         if (LSTCOL .ne. oldcol .and. LSTCOL .ge. 0) then
               WRITE ( UNIT, FMT='(A)' ) GRAY(LSTCOL)
               oldcol = LSTCOL
         end if
         if (LSTCOL .ge. 0) WRITE ( UNIT, FMT='(A)' ) 'S'
 
ccc   END IF
 
      RETURN
 
C
C$ Procedure ESCL07
 
      ENTRY ESCL07 ( HMIN, HMAX, VMIN, VMAX )
 
C$ Abstract
C
C     Clear a region of the Postscript User Space.
C
C$ Required_reading
C
C     ESCHER, ESDO.
C
C$ Keywords
C
C     GRAPHICS
C
C$ Declarations
C
C     INTEGER               HMIN
C     INTEGER               HMAX
C     INTEGER               VMIN
C     INTEGER               VMAX
C
C$ Brief_I/O
C
C     VARIABLE  I/O  DESCRIPTION
C     --------  ---  ---------------------------------------------------
C     HMIN       I   Left horizontal boundary of region to clear.
C     HMAX       I   Right horizontal boundary of region to clear.
C     VMIN       I   Bottom vertical boundary of region to clear.
C     VMAX       I   Right vertical boundary of region to clear.
C
C$ Detailed_Input
C
C     HMIN       Left horizontal boundary of region to clear.
C
C     HMAX       Right horizontal boundary of region to clear.
C
C     VMIN       Bottom vertical boundary of region to clear.
C
C     VMAX       Right vertical boundary of region to clear.
C
C$ Detailed_Output
C
C     None.
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
C     Clear the region of Postscript User space, from
C     HMIN to HMAX horizontally and from VMIN to VMAX vertically.
C
C     If       ( HMIN .EQ. MINX )
C    .   .AND. ( HMAX .EQ. MAXX )
C    .   .AND. ( VMIN .EQ. MINY )
C    .   .AND. ( VMAX .EQ. MAXY )  THEN
C
C       We close the file with a 'showpage' command.
C
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
C      "Postscript Language, Tutorial and Cookbook" Addison-Wesley
C      Publishing Company, Reading Massachusetts. September 1987.
C
C      "Postscript Language Reference Manual" Addison-Wesley
C      Publishing Company, Reading Massachusetts. September 1987.
C
C$ Author_and_Institution
C
C     W.L. Taber, I.M. Underwood (JPL)
C
C$ Version_and_Date
C
C     Version 2, 11-MAY-1990
C     Version 1, 28-JUL-1986
C
C-
 
C
C     First make sure that a file is open.
C
      IF ( .NOT. OPEN ) THEN
         RETURN
      END IF
 
C
C     Next see if we should close the current file.
C
      IF (       ( HMIN .EQ. MINX )
     .     .AND. ( HMAX .EQ. MAXX )
     .     .AND. ( VMIN .EQ. MINY )
     .     .AND. ( VMAX .EQ. MAXY ) ) THEN
 
         WRITE ( UNIT, FMT='(A)' ) 'showpage'
         CLOSE ( UNIT = UNIT, status='KEEP' )
         outuni = 0
         OPEN = .FALSE.
        return 
      END IF
 
C
C     Position the pen
C
 
      WRITE ( UNIT, FMT='(A)' ) '% '
      WRITE ( UNIT, FMT='(A)' ) '% CLEAR PART OF THE PAGE'
      WRITE ( UNIT, FMT='(A)' ) '% '
      WRITE ( UNIT, FMT='(A)' ) 'N'
 
      CALL OPAIRI ( ' ', HMIN, ' ', VMIN, ' M', MOVETO )
      WRITE ( UNIT, FMT='(A)' )  MOVETO(2:LASTNB(MOVETO))
 
C
C     Now shade in the viewport in white.
C
      CALL OPAIRI ( ' ', HMIN, ' ', VMAX, ' L', LINETO )
      WRITE (UNIT, FMT='(A)') LINETO(2:LASTNB(LINETO))
 
      CALL OPAIRI ( ' ', HMAX, ' ', VMAX, ' L', LINETO )
      WRITE (UNIT, FMT='(A)') LINETO(2:LASTNB(LINETO))
 
      CALL OPAIRI ( ' ', HMAX, ' ', VMIN, ' L', LINETO )
      WRITE (UNIT, FMT='(A)') LINETO(2:LASTNB(LINETO))
 
      CALL OPAIRI ( ' ', HMIN, ' ', VMIN, ' L', LINETO )
      WRITE (UNIT, FMT='(A)') LINETO(2:LASTNB(LINETO))
 
      WRITE (UNIT, FMT='(A)') 'closepath'
      WRITE (UNIT, FMT='(A)') '1 G'
      WRITE (UNIT, FMT='(A)') 'fill'
      WRITE (UNIT, FMT='(A)') '0 G'
        oldcol = 1
 
      RETURN
 
C$ Procedure
 
      ENTRY ESIN07
 
C$ Abstract
C
C     Initialize the POSTSCRIPT mode
C
C$ Keywords
C
C     GRAPHICS
C
C$ Declarations
 
 
C$ Brief_I/O
C
C     None.
C
C$ Detailed_Input
C
C     None.
C
C$ Detailed_Output
C
C     None.
C
C$ Detailed_Description
C
C     This routine doesn't do anything but return.  It exists only for
C     compatibility reasons.
C
C$ Input_Files
C
C     None.
C
C$ Output_Files
C
C     None.
C
C$ Common
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
C     Version 1.0 1990-MAY-24
C
C-&
C
 
      RETURN
 
      END
