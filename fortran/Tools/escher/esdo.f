C$Procedure      ESDO ( )
 
      SUBROUTINE ESDO ( ACTION, DEVICE, ASIZE, ARRAY, ERROR )
 
C$ Abstract
C
C     This routine is the device controller for ESCHER.  All device
C     specific actions are communicated through this routine.
C
C$ Required_Reading
C
C      ESCHER
C
C$ Keywords
C
C     GRAPHICS
C
C$ Declarations
 
 
      CHARACTER*(*)         ACTION
      INTEGER               DEVICE
      INTEGER               ASIZE
      INTEGER               ARRAY  ( * )
      CHARACTER*(*)         ERROR
 
C$ Brief_I/O
C
C     Variable  I/O  Description
C     --------  ---  --------------------------------------------------
C     ACTION     I   action to be performed.
C     DEVICE     I   device for which action is intended.
C     ASIZE     I/O  number of items in array.
C     ARRAY     I/O  data input/output from ESDO. depends upon ACTION
C     ERROR      O   Blank unless an error is detected.
C
C$ Detailed_Input
C
C     ACTION     is a string indicating one of four actions that the
C                program should perform:
C
C                'INITIATE'  the device defined by DEVICE should
C                            be prepared for writing vectors and
C                            clearing display regions.
C
C                'DRAW'      the buffer of segments should be written
C                            on the display device.  The segments
C                            and colors are stored in ARRAY.
C
C                'CLEAR'     a region of the display should be cleared.
C                            The region to be cleared is stored in
C                            ARRAY.
C
C                'BOUNDS'    return the pixel/line boundaries for the
C                            edges of the display device.
C
C     DEVICE     the device towards which the action is to be directed.
C
C     ARRAY      for the cases in which ACTION has one of the values
C                'CLEAR' or 'DRAW', ARRAY will contain the information
C                about what portion of the device to clear, or the
C                segments that should be drawn.  When ARRAY is an input
C                users are free to change its contents in anyway
C                that aids their programming task.
C
C                'CLEAR'  in this case the boundaries of the region to
C                         clear will be stored as:
C
C                         ARRAY(1) = left edge of region to clear
C                         ARRAY(2) = right edge of region to clear
C                         ARRAY(3) = bottom edge of region to clear
C                         ARRAY(4) = top edge of region to clear.
C
C                'DRAW'   in this case ARRAY contains the beginning
C                         and ending of line segments and colors
C                         of the line segments.
C
C                         ARRAY(5*I-4) is the pixel number of the
C                                      beginning endpoint of the
C                                      I'th segment to draw.
C
C                         ARRAY(5*I-3) is the line number of the
C                                      beginning endpoint of the
C                                      I'th segment to draw.
C
C                         ARRAY(5*I-2) is the pixel number of the
C                                      ending endpoint of the
C                                      I'th segment to draw.
C
C                         ARRAY(5*I-1) is the line number of the
C                                      ending endpoint of the
C                                      I'th segment to draw.
C
C                         ARRAY(5*I  ) is the color of the
C                                      I'th segment to draw.
C
C$ Detailed_Output
C
C     ARRAY      for the cases in which ACTION has the value 'BOUNDS'
C                ARRAY will be returned with the pixel/line boundaries
C                of the display device.
C
C                ARRAY(1) = left  boundary
C                ARRAY(2) = right boundary
C                ARRAY(3) = bottom boundary
C                ARRAY(4) = top boundary
C
C     ERROR      this will be blank unless DEVICE is not one of those
C                supported by ESDO or if the ACTION is unrecognized.
C                In that case ERROR will contain a message of the form:
C
C                'ESDO: The device requested, <device number>, is not
C                 supported in this version of ESDO.'
C
C                'ESDO: The action requested, <action>, is not
C                 recognized.'
C$ Parameters
C
C     None.
C
C$ Exceptions
C
C     1) If a device is input that is not supported, a message
C        indicating this problem will be returned through ERROR.
C
C     2) If an action is unrecognized, a message indicating
C        this will be returned through ERROR.
C
C$ Files
C
C     None.
C
C$ Particulars
C
C     This routine is the device interface routine used by ESCHER.
C     It is written so that with a minimum of effort users can
C     modify it and support new graphics devices.
C
C     To add a new device to the list supported, you must write
C     four (4) subroutines for interfacing with your device, and
C     select a device number for that device that is not already
C     one listed in this routine.  For the moment let us assume
C     that this routine does not already support a device with
C     device number xy where x and y are both digits
C     ( '0', '1', '2', '3', '4', '5', '6', '7', '8', '9' )
C
C     If you follow the naming conventions
C     suggested below, you can be assured of avoiding name
C     clashes with other software needed to support ESCHER and EUCLID.
C
C     The four routines you must write are:
C
C     ESINxy ()
C
C            This routine should be callable exactly once in order
C            to prepare your device for drawing vectors and for clearing
C            the screen.  You may need to enable certain modes for the
C            device, load color tables, etc.  Whatever it takes. After
C            one call to this routine, the device should be in a state
C            that when given a vector it can draw them without erasing
C            what is already displayed.
C
C     ESPLxy ( LEFT, RIGHT, BOTTOM, TOP )
C
C            This routine returns integers that correspond to the
C            LEFT, RIGHT, BOTTOM and TOP boundaries of your display
C            device.
C
C            Use whatever integers are convenient.  Often
C            this will be simply pixel and line numbers.  Whatever
C            you choose ABS(RIGHT - LEFT) should be equal to or exceed
C            the number of individual points that can be plotted
C            along a horizontal line from the left edge to the
C            right edge of your display device.  Similarly
C            ABS(TOP-BOTTOM) should equal or exceed the number of
C            individual points that can be plotted along a vertical
C            line from the top to bottom of your display device.
C
C            In addition you should be sure that the ratio
C            ABS ( (TOP-BOTTOM) / (RIGHT - LEFT) ) is the
C            physical ration of height/width of your display device.
C
C     ESCLxy ( HMIN, HMAX, VMIN, VMAX )
C
C            This routine must be able to clear a region of the screen
C            that extends from HMIN to HMAX horizontally and from
C            VMIN to VMAX vertically (where HMIN, HMAX, VMIN, VMAX are
C            all integers and are relative to the device boundaries
C            supplied through the routine ESPLxy
C
C     ESDRxy ( NSEGS, SEGS )
C
C            This routine must be able to draw a collection of vectors.
C            The beginning and endings of these vectors will be given
C            relative to the values returned by ESPLxy.
C
C            Note that if the values returned by ESPLxy does not give
C            the true pixel/line dimensions of your device, you will
C            be responsible for performing the appropriate mapping
C            between the endpoints supplied in ESDRxy and the
C            physical position at which they should be placed on your
C            display device.
C
C            NSEGS  is the number of values stored in SEGS.  In other
C                   words, the description of the segments is contained
C                   in SEGS(1) through SEGS(NSEGS).  NSEGS will always
C                   be a multiple of 5.
C
C            SEGS   is a collection of segments.  The I'th segment
C                   is described by the values:
C
C                   SEGS(I*5-4), SEGS(I*5-3),
C                   SEGS(I*5-2), SEGS(I*5-1),
C                   SEGS(I*5)
C
C                   The first two values are the horizontal and vertical
C                   positions, respectively of the beginning endpoint
C                   of the I'th segment.
C
C                   The second two values are the horizontal and
C                   vertical positions, respectively of the ending
C                   endpoint of the I'th segment.
C
C                   The last value is the color with which the I'th
C                   segment should be drawn.
C
C     Once these four routines have been written you simply need to
C     insert a new block of code immediately befor the marker
C
C     C  \\\\
C     C  ===============>>
C     C  ////
C
C     in the code below.
C
C     The block of code will look like:
C
C      ELSE IF ( DEVICE .EQ. xy ) THEN
C
C         IF      ( ACTION .EQ. 'INITIATE' ) THEN
C
C            CALL ESINxy
C
C         ELSE IF ( ACTION .EQ. 'INITIATE' ) THEN
C
C            CALL ESPLxy ( ARRAY(LEFT),   ARRAY(RIGHT),
C     .                    ARRAY(BOTTOM), ARRAY(TOP)  )
C
C         ELSE IF ( ACTION .EQ. 'INITIATE' ) THEN
C
C            CALL ESCLxy ( ARRAY(HMIN), ARRAY(HMAX),
C     .                    ARRAY(VMIN), ARRAY(VMAX)  )
C
C         ELSE IF ( ACTION .EQ. 'DRAW' ) THEN
C
C            CALL ESDRxy ( ASIZE, ARRAY  )
C
C         END IF
C
C     The calling sequences should be presented EXACTLY as shown.
C     All you need to do is replace xy by the actual digits
C     you choose for your device number.
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
C     None.
C
C$ Author_and_Institution
C
C     W.L. Taber     (JPL)
C     I.M. Underwood (JPL)
C
C$ Version
C
C-    Beta Version 1.0.0, 10-MAY-1990 (WLT) (IMU)
C-    modified 8/94 added device 61             SMR
C
C-&
 
C
C
C     Other functions
C
      INTEGER               CARDI
 
C
C     Parameters.
C
      INTEGER               HMIN
      PARAMETER           ( HMIN = 1 )
 
      INTEGER               HMAX
      PARAMETER           ( HMAX = 2 )
 
      INTEGER               VMIN
      PARAMETER           ( VMIN = 3 )
 
      INTEGER               VMAX
      PARAMETER           ( VMAX = 4 )
 
      INTEGER               BOTTOM
      PARAMETER           ( BOTTOM = 3 )
 
      INTEGER               LEFT
      PARAMETER           ( LEFT   = 1 )
 
      INTEGER               RIGHT
      PARAMETER           ( RIGHT  = 2 )
 
      INTEGER               TOP
      PARAMETER           ( TOP    = 4)
 
 
c This version hard-wired for Postscript
c
c      ELSE IF ( DEVICE .EQ. 07 ) THEN
c
C        This is the POSTSCRIPT portrait mode.
C
         IF      ( ACTION .EQ. 'INITIATE' ) THEN
 
            CALL ESIN07
 
         ELSE IF ( ACTION .EQ. 'BOUNDS'   ) THEN
 
            CALL ESPL07 ( ARRAY(LEFT),   ARRAY(RIGHT),
     .                    ARRAY(BOTTOM), ARRAY(TOP)  )
 
         ELSE IF ( ACTION .EQ. 'CLEAR'    ) THEN
 
            CALL ESCL07 ( ARRAY(HMIN),  ARRAY(HMAX),
     .                    ARRAY(VMIN),  ARRAY(VMAX)   )
 
         ELSE IF ( ACTION .EQ. 'DRAW'     ) THEN
 
            CALL ESDR07 ( ASIZE, ARRAY  )
 
         END IF
 
 
 
      RETURN
      END

