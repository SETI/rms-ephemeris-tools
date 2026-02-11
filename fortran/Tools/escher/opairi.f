 
 
C$Procedure      OPAIRI ( Ordered pair of integers )
 
      SUBROUTINE OPAIRI ( BEG, X, SEP, Y, END, PAIR )
 
C$ Abstract
C
C     Construct an character string representing and ordered pair
C     of integers.
C
C$ Required_Reading
C
C     None.
C
C$ Keywords
C
C     ALPHANUMERIC
C     UTILITY
C
C$ Declarations
 
      CHARACTER*(*)         BEG
      INTEGER               X
      CHARACTER*(*)         SEP
      INTEGER               Y
      CHARACTER*(*)         END
      CHARACTER*(*)         PAIR
 
C$ Brief_I/O
C
C     Variable  I/O  Description
C     --------  ---  --------------------------------------------------
C     BEG        I   Beginning marker for the ordered pair.
C     X          I   Integer to use for creating X portion of string.
C     SEP        I   Marker used to separate X and Y portions of string.
C     Y          I   Integer to use for creating Y portion of string.
C     END        I   Marker used for the end of the ordered pair.
C     PAIR       O   String containing the ordered pair.
C
C$ Detailed_Input
C
C     BEG        Marker used at the beginning of the ordered pair.
C                Often this will be a parenthesis '(' or bracket '['.
C
C     X          Integer that will be converted to yield the first
C                component of the ordered pair.
C
C     SEP        Marker used to separate X and Y portions of the pair.
C
C     Y          Integer that will be converted to yield the second
C                component of the ordered pair.
C
C     END        Marker used for the end of the ordered pair.
C                Often this will be a parenthesis ')' or bracket ']'.
C
C$ Detailed_Output
C
C      PAIR      Is a string representing the ordered pair of integers
C                X,Y.
C
C$ Parameters
C
C     None.
C
C$ Exceptions
C
C     Error free.
C
C     1) If sufficient room is not supplied to create the pair, it
C        will be truncated.
C
C$ Files
C
C     None.
C
C$ Particulars
C
C      This routine enables the creation of strings representing ordered
C      pairs of integers.  Such pairs are often required for graphics,
C      terminal applications or representing substrings.
C
C         V[12,189]
C         P[190,198]
C
C         <ESC>[12;45f
C
C         STRING(12:19)
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
C-    Beta Version 1.0.0, 17-MAY-1990 (WLT) (IMU)
C
C-&
C
 
C
C     SPICE FUNCTIONS
C
      INTEGER               LASTNB
C
C     Local variables
C
      CHARACTER*(16)        XSTR
      CHARACTER*(16)        YSTR
 
      INTEGER               LX
      INTEGER               LY
 
C
      CALL INTSTR ( X, XSTR )
      CALL INTSTR ( Y, YSTR )
 
      LX   = LASTNB(XSTR)
      LY   = LASTNB(YSTR)
 
      PAIR = BEG // XSTR(1:LX) // SEP // YSTR(1:LY) // END
 
      RETURN
      END
