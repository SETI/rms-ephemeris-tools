      SUBROUTINE ELLIPS  ( AXIS1,  AXIS2,  AXIS3,
     .                     CENTER, VUFROM, 
     .                     NORMAL, MAJOR,  MINOR, MIDPNT, CANSEE )


C$ Abstract
C
C      Determines the principle axes, center and normal to the plane of
C      the ellipse that makes up the observed limb of a triaxial body.
C
C$ Required Reading
C
C      None.
C
C$ Keywords
C
C      GEOMETRY
C      ALGEBRA
C      ELLIPSE
C      ELLIPSOID
C
C$ Declarations

      DOUBLE PRECISION      AXIS1  ( 3 )
      DOUBLE PRECISION      AXIS2  ( 3 )
      DOUBLE PRECISION      AXIS3  ( 3 )
      DOUBLE PRECISION      CENTER ( 3 )
      DOUBLE PRECISION      VUFROM ( 3 )
      DOUBLE PRECISION      NORMAL ( 3 )
      DOUBLE PRECISION      MAJOR  ( 3 )
      DOUBLE PRECISION      MINOR  ( 3 )
      DOUBLE PRECISION      MIDPNT ( 3 )
      LOGICAL               CANSEE

C$ Brief_I/O
C
C      Variable      I/O      Description
C      --------      ---      ------------------------------------------
C      AXIS1           I       First principle axis of the body
C      AXIS2           I       Second principle axis of the body
C      AXIS3           I       Third principle axis of the body
C      CENTER          I       Center of the ellipsoid
C      VUFROM          I       Position from which the object is viewed.
C      NORMAL          O       A normal to the plane of the ellipsoid.
C      MAJOR           O       Vector of the major axis of the limb.
C      MINOR           O       Vector of the minor axis of the limb.
C      MIDPNT          O       Position of the center of the limb.
C      CANSEE          O       .TRUE. if observer is outside body
C
C$ Detailed_Input
C
C      AXIS1      3 vector giving the first principle axes of the 
C                 ellipsoid.  The vector points from the center 
C                 of the ellipsoid along first principle axis and has 
C                 length equal to the length of this axis. 
C              
C      AXIS2      3 vector giving the second principle axes of the 
C                 ellipsoid.  The vector points from the center 
C                 of the ellipsoid along second principle axis and has 
C                 length equal to the length of this axis. 
C              
C      AXIS3      3 vector giving the third principle axes of the 
C                 ellipsoid.  The vector points from the center 
C                 of the ellipsoid along third principle axis and has 
C                 length equal to the length of this axis. 
C              
C      CENTER     Position of the center of the ellipsoid to be 
C                 observed.
C
C      VUFROM  Position from which the ellipsoid is to be observed.
C
C$ Detailed_Output
C
C      NORMAL     A unit vector normal to the plane that contains the 
C                 set of observed limb points.  Moreover, an arbitrary 
C                 point X is in the limb plane if and only if 
C                 
C                    <NORMAL, X - MIDPNT> = 0 
C                    
C                 (where < , > denotes dot product). 
C                 
C                 Furthermore, X lies on the same side of the limb plane
C                 as the observer if and only if 
C                 
C                    <NORMAL, X - MIDPNT> > 0
C                 
C                 Otherwise X lies on the side of the plane opposite
C                 the observer.  )In otherwords, NORMAL points into 
C                 the half space bounded by the limb plane that 
C                 contains the observer. This proves useful when 
C                 attempting to remove hidden lines. 
C
C      MAJOR      This vector points in the direction of the major
C                 axis of the ellipse that makes up the limb.  This
C                 vector has length equal to the length of the semi-
C                 major axis.
C
C      MINOR      This vector points in the direction of the minor
C                 axis of the ellipse that makes up the limb.  This
C                 vector has length equal to the length of the semi-
C                 minor axis.
C
C      MIDPNT     Center (both observed and geometric) of the ellipse
C                 of the observed limb.
C                 
C      CANSEE     Is true as long as the observer is outside of the
C                 body for which one is trying to find the limb.
C                 False otherwise.
C
C$ Parameters
C
C     None.
C
C$ Exceptions
C
C     1) If any of the axes are have zero length an error message
C        will be set and signalled indicating the problem.
C        
C     2) If the input axes are not linearly indenpendent, it is
C        possible that the message EUCLID(DEPENDENTAXESLAMBDA) or 
C        EUCLID(DEPENDENTAXESALPHGAM) will be signalled and a
C        message indicating what the input axes were will be
C        set.  HOWEVER, an explicit test for linear independence
C        is NOT performed.  
C
C     3) No check are performed to see if the input axes are mutually
C        orthogonal.
C
C$ Particulars
C
C      The set of points that make up the observed limb of a triaxial 
C      body (ellipsoid) is an ellipse.  This program computes a set
C      of vectors needed to fully describe this ellipse and the plane
C      in which it lies.  Given the outputs MIDPNT, MINOR, MAJOR, and
C      the set of points lying on the limb is given by
C
C      {cos(t)*MAJOR + sin(t)*MINOR + MIDPNT | t belonging to [0,2*PI]
C
C      The equation of the plane of the limb is given by
C
C      < NORMAL , (x,y,z) - CENTER > = 1.
C
C      Points (x,y,z) on the same side of this plane as the observer 
C      satisfy
C
C      < NORMAL , (x,y,z) - CENTER >   > 1.
C
C      Points (x,y,z) on the side of this plane opposite the observer 
C      satisfy
C
C      < NORMAL , (x,y,z) - CENTER >   < 1.
C
C$ Files
C
C        None.
C
C$ Examples
C
C        None.
C
C$ Restrictions
C
C        None.
C
C$ Literature_References
C
C     None.
C
C$ Author_and_Institution
C
C     W.L. Taber     (JPL)
C
C$ Version and Date
C
C  Version 1.00 --  1986
C  Version 1.10 --  June 12, 1990
C  
C-&

C
C   SPICE functions
C
      DOUBLE PRECISION      VNORM
      DOUBLE PRECISION      VTMV 
      DOUBLE PRECISION      VDOT
      
      LOGICAL               RETURN
C
C     Local variables
C

      INTEGER               I,J,K

      DOUBLE PRECISION      AXES   ( 3, 3 )
      DOUBLE PRECISION      CTHETA   
      DOUBLE PRECISION      C2THTA  
      DOUBLE PRECISION      STHETA   


      DOUBLE PRECISION      LAMBDA   
      DOUBLE PRECISION      ALPHA    
      DOUBLE PRECISION      BETA     
      DOUBLE PRECISION      GAMMA    

      DOUBLE PRECISION      MIDDLE   
      DOUBLE PRECISION      RADIUS   

      DOUBLE PRECISION      TEMPV (    3 ) 
      DOUBLE PRECISION      E     ( 3, 3 )
      DOUBLE PRECISION      SIGHT (    3 )
      DOUBLE PRECISION      UNITN (    3 )
      DOUBLE PRECISION      U     (    3 )
      DOUBLE PRECISION      V     (    3 )
      DOUBLE PRECISION      REFX  (    3 )
      
      DOUBLE PRECISION      R1SQR
      DOUBLE PRECISION      R2SQR
      DOUBLE PRECISION      R3SQR

C
C     Lengths of the semi-major and -minor axes
C
      DOUBLE PRECISION      A
      DOUBLE PRECISION      B

C
C     Find the squared lengths of the semi-axes of the body
C

      R1SQR  =  VDOT(AXIS1, AXIS1)
      R2SQR  =  VDOT(AXIS2, AXIS2)
      R3SQR  =  VDOT(AXIS3, AXIS3)

      IF (      ( R1SQR .EQ. 0.0D0 ) 
     .     .OR. ( R2SQR .EQ. 0.0D0 ) 
     .     .OR. ( R3SQR .EQ. 0.0D0 ) ) THEN
     
         CALL CHKIN  ( 'ELLIPS' )
         
         CALL SETMSG ( 'At least one of the axes input had zero '     //
     .                 'length. The lengths of the axes supplied '    //
     .                 'were: 1, 2, 3. '  )
     
         CALL ERRDP  ( '1', DSQRT(R1SQR) )
         CALL ERRDP  ( '2', DSQRT(R2SQR) )
         CALL ERRDP  ( '3', DSQRT(R3SQR) )
         
         CALL SIGERR ( 'EUCLID(BADAXES)' )
         CALL CHKOUT ( 'ECLPMD'          )         
         
         RETURN
         
      END IF


C
C     Compute the line of sight between the VUFROM and the ellipsoid
C     center.
C
      CALL VSUB  ( VUFROM, CENTER,  SIGHT )
      

C     
C     Determine whether or not the observer can see this object. 
C     That is whether or not the observer is outside the object --
C     inside implies the observer cannot see the object; outside
C     implies the observer can see the object.
C     
C     
      CANSEE = (VDOT(AXIS1, SIGHT)**2)/(R1SQR**2)
     .       + (VDOT(AXIS2, SIGHT)**2)/(R2SQR**2)
     .       + (VDOT(AXIS3, SIGHT)**2)/(R3SQR**2) .GT. 1.0D0
      
      IF ( .NOT. CANSEE ) THEN
         RETURN
      END IF
      

      CALL CLEARD ( 9, E )

      E(1,1) = 1/R1SQR
      E(2,2) = 1/R2SQR
      E(3,3) = 1/R3SQR      

      DO I = 1,3
         AXES(I,1) = AXIS1(I)
         AXES(I,2) = AXIS2(I)
         AXES(I,3) = AXIS3(I)
      END DO
      
      
C
C     Compute the symmetrix matrix that represents the surface of the
C     ellipsoid
C
      CALL MXMT  ( E,   AXES,    E      )
      CALL MTXM  ( E,   E,       E      )
C
C     Compute the normal to the plane of the limb
C
      CALL MXV   ( E,   SIGHT,   NORMAL )
C
C     Obtain an orthonormal frame for which the first vector is parallel
C     to NORMAL.
C
      CALL VHAT  ( NORMAL, UNITN  )
      CALL VEQU  ( UNITN,  NORMAL )
      CALL FRAME ( UNITN,  U, V   )

C
C     Compute the constants needed for determining the length of the
C     axes of the limb ellipse, and for computing the the directions
C     of these axes.
C
      TEMPV(1) = VTMV ( SIGHT, E, SIGHT )  
      
      IF ( TEMPV(1) .NE.  0 ) THEN
      
         LAMBDA   = 1.0D0 / TEMPV(1)
         
      ELSE
      
         CALL CHKIN  ( 'ELLIPS' )
         CALL SETMSG ( 'The input axes are not mutually orthogonal ' //
     .                 'The axes are: (1, 2, 3), (1, 2, 3), (1, 2, 3).')
     
         CALL ERRDP  ( '1', AXIS1(1) )
         CALL ERRDP  ( '2', AXIS1(2) )
         CALL ERRDP  ( '3', AXIS1(3) )

         CALL ERRDP  ( '1', AXIS2(1) )
         CALL ERRDP  ( '2', AXIS2(2) )
         CALL ERRDP  ( '3', AXIS2(3) )

         CALL ERRDP  ( '1', AXIS3(1) )
         CALL ERRDP  ( '2', AXIS3(2) )
         CALL ERRDP  ( '3', AXIS3(3) )

         CALL SIGERR ( 'EUCLID(DEPENDENTAXESLAMBDA)' )
         CALL CHKOUT ( 'ELLIPS'                )
         RETURN
         
      END IF
C
C   Find the center of the limb ellipse
C
      CALL VSCL( LAMBDA, SIGHT,  MIDPNT )
      CALL VADD( CENTER, MIDPNT, MIDPNT )

C
C   Compute the constants needed for finding the principle axes
C   of the limb ellipse
C
      ALPHA    = VTMV (U, E, U)
      BETA     = VTMV (V, E, U)
      GAMMA    = VTMV (V, E, V)


C
C  Make sure nothing dumb has been entered for the ellipsoid definition
C
      IF (( ALPHA .LE. 0 ) .OR. (GAMMA .LE. 0)) THEN
         CALL CHKIN  ( 'ELLIPS' )
         CALL SETMSG ( 'The input axes are not mutually orthogonal ' //
     .                 'The axes are: (1, 2, 3), (1, 2, 3), (1, 2, 3).')
     
         CALL ERRDP  ( '1', AXIS1(1) )
         CALL ERRDP  ( '2', AXIS1(2) )
         CALL ERRDP  ( '3', AXIS1(3) )

         CALL ERRDP  ( '1', AXIS2(1) )
         CALL ERRDP  ( '2', AXIS2(2) )
         CALL ERRDP  ( '3', AXIS2(3) )

         CALL ERRDP  ( '1', AXIS3(1) )
         CALL ERRDP  ( '2', AXIS3(2) )
         CALL ERRDP  ( '3', AXIS3(3) )

         CALL SIGERR ( 'EUCLID(DEPENDENTAXESALPHGAM)' )
         CALL CHKOUT ( 'ELLIPS'                       )
         RETURN
         
      END IF         

      MIDDLE   = (ALPHA + GAMMA) * 0.5

      TEMPV(1) = (ALPHA - GAMMA) * 0.5
      TEMPV(2) = BETA
      TEMPV(3) = 0

      RADIUS   = VNORM( TEMPV )

      A        = DSQRT ((1 - LAMBDA) / (MIDDLE - RADIUS))
      B        = DSQRT ((1 - LAMBDA) / (MIDDLE + RADIUS))

      IF (RADIUS .EQ. 0) THEN
         CTHETA   = 1.0
         STHETA   = 0.0
      ELSE
         C2THTA  = TEMPV(1) /RADIUS
         CTHETA   =        DSQRT( (1 + C2THTA)*0.5 )
         STHETA   = DSIGN( DSQRT( (1 - C2THTA)*0.5 ), BETA )
      END IF

C
C   Obtain the principle axes
C

      CALL VLCOM( -STHETA, U,  CTHETA, V, MAJOR )
      CALL VLCOM(  CTHETA, U,  STHETA, V, MINOR )

      CALL VSCL( A, MAJOR, MAJOR )
      CALL VSCL( B, MINOR, MINOR )

      RETURN
      END
