C$ Procedure
 
      SUBROUTINE ECLPMD ( AXIS1,  AXIS2,   AXIS3,  CENTER,
     .                    SOURCE, RADIUS,
     .                    NORMAL, MAJOR,   MINOR,  MIDPNT,
     .                    VERTEX, CAXIS,   CANECL                   )
 
 
C$ Abstract
C
C     Compute the model for the eclipse cone resulting from an
C     illumination source at SOURCE and an opaque body at CENTER
C
C$ Required Reading
C
C     None.
C
C$ Keywords
C
C      ELLIPSOID
C      GEOMETRY
C      ECLIPSE
C
C$ Declarations
 
      DOUBLE PRECISION      AXIS1  (3)
      DOUBLE PRECISION      AXIS2  (3)
      DOUBLE PRECISION      AXIS3  (3)
      DOUBLE PRECISION      CENTER (3)
      DOUBLE PRECISION      SOURCE (3)
      DOUBLE PRECISION      RADIUS
      DOUBLE PRECISION      NORMAL (3)
      DOUBLE PRECISION      MAJOR  (3)
      DOUBLE PRECISION      MINOR  (3)
      DOUBLE PRECISION      MIDPNT (3)
      DOUBLE PRECISION      VERTEX (3)
      DOUBLE PRECISION      CAXIS(3)
      LOGICAL               CANECL
 
C$ Brief_I/O
C
C     VARIABLE  I/O  DESCRIPTION
C     --------  ---  ---------------------------------------------------
C      AXIS1     I   Priciple axis of the ellipsoid
C      AXIS2     I   Priciple axis of the ellipsoid
C      AXIS3     I   Priciple axis of the ellipsoid
C      CENTER    I   Center of the ellipsoid
C      SOURCE    I   Center of the illumination source
C      RADIUS    I   Radius of the illumination source
C      NORMAL    O   Normal to the plane of the terminator
C      MAJOR     O   Semi-major axis of the terminator ellipse
C      MINOR     O   Semi-minor axis of the terminator ellipse
C      MIDPNT    O   Center of the terminator ellipse
C      VERTEX    O   Vertex of the eclipse cone
C      CAXIS     O   Axis of the eclipse cone
C      CANECL    O   .TRUE. if light source is outside body.
C
C$ Detailed_Input
C
C      AXIS1     A vector pointing along the first principle axis of
C                the ellipsoid and having length equal to this axis.
C
C      AXIS2     A vector pointing along the second principle axis of
C                the ellipsoid and having length equal to this axis.
C
C      AXIS3     A vector pointing along the third principle axis of
C                the ellipsoid and having length equal to this axis.
C
C      CENTER    Center of the ellipsoid
C
C      SOURCE    Center of the illumination source
C
C      RADIUS    Radius of the illumination source (which is assumed to
C                be spherical
C
C$ Detailed_Output
C
C      NORMAL    Normal to the plane of the terminator, that points
C                towards the dark side of the body.
C
C      MAJOR     Vector that points in the direction of the Semi-major
C                axis of the terminator ellipse and has length equal to
C                the length of this semi-axis
C
C      MINOR     Vector that points in the direction of the Semi-minor
C                axis of the terminator ellipse and has length equal to
C                the length of this semi-axis
C
C      MIDPNT    Center of the terminator ellipse.
C
C      VERTEX    The region of eclipse is modelled as an elliptic cone.
C                VERTEX is the vertex of this eclipse cone.
C
C      CAXIS     Unit vector that points along the axis of the eclipse
C                cone.  From the center of the opaque body it points
C                towards the dark side of the body.
C
C      CANECL    Is .TRUE. if the light source is outside the
C                body.  Otherwise it is false.
C
C$ Parameters
C
C     None.
C
C$ Exceptions
C
C     Error free.
C
C     1) If any of the input axes have zero length, the body is defined
C        to cast no shadow.  CANECL will be set to false and no model
C        will be constructed.
C
C$ Files
C
C     None.
C
C$ Particulars
C
C      Determine the vertex of the eclipse cone.  Then use this
C      as the viewpoint in ELLIPS to find the terminator
C
C$ Examples
C
C     None.
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
C     Version 1, 18-JUN-1986
C
C-
 
C
C     Naiflib Functions
C
      DOUBLE PRECISION      VDOT
      DOUBLE PRECISION      VNORM
 
      LOGICAL               RETURN
C
C     Local Variables
C
      DOUBLE PRECISION      BIGONE
      DOUBLE PRECISION      DENOM
 
      DOUBLE PRECISION      R1SQR
      DOUBLE PRECISION      R2SQR
      DOUBLE PRECISION      R3SQR
 
      DOUBLE PRECISION      SIGHT(3)
      DOUBLE PRECISION      T
 
 
      IF ( RETURN() ) THEN
         RETURN
      END IF
 
C
C     Get the vector from the center of the light source to the
C     center of the body.
C
      CALL VSUB( CENTER, SOURCE, SIGHT )
 
C
C     Find the squared lengths of the semi-axes of the body
C
      R1SQR   =  VDOT(AXIS1, AXIS1)
      R2SQR   =  VDOT(AXIS2, AXIS2)
      R3SQR   =  VDOT(AXIS3, AXIS3)
 
      BIGONE = MAX ( DSQRT(R1SQR), DSQRT(R2SQR), DSQRT(R3SQR) )
 
C
C     Determine whether or not the light source can be eclipsed by this
C     body.  If the light source center is inside the body, the answer
C     is no.  Otherwise the answer is yes.
C
      IF (       ( R1SQR .GT. 0.0D0 )
     .     .AND. ( R2SQR .GT. 0.0D0 )
     .     .AND. ( R3SQR .GT. 0.0D0 ) ) THEN
 
         CANECL = (VDOT(AXIS1,SIGHT)**2)/(R1SQR**2)
     .          + (VDOT(AXIS2,SIGHT)**2)/(R2SQR**2)
     .          + (VDOT(AXIS3,SIGHT)**2)/(R3SQR**2) .GT. 1.0D0
     .     .AND.   VNORM(SIGHT)                     .GT. BIGONE+RADIUS
 
 
      ELSE
 
         CANECL = .FALSE.
 
      END IF
 
C
C     If this object cannot eclipse this light source, there is no
C     point in attempting to construct an eclipse model.
C
      IF ( .NOT. CANECL ) THEN
         RETURN
      END IF
 
C
C     If we reach this far we know that we can construct a limb model.
C
 
      DENOM = RADIUS - BIGONE
 
C
C     We ensure that the there will always be a vertex to the eclipse
C     cone within a reasonable distance of the either the source or
C     body
C
      IF ( ABS(DENOM) .LE. 0.0001 ) THEN
         T = BIGONE*10000.0D0
      ELSE
         T = BIGONE/DENOM
      END IF
 
C
C     Compute the vertex of the eclipse cone and the unit vector that
C     points down the axis of the eclipse cone, from the center of
C     the body toward its dark side.
C
      CALL VLCOM ( 1.0D0,   CENTER, T, SIGHT, VERTEX )
      CALL VHAT  ( SIGHT,   CAXIS                    )
 
C
C     Compute the terminator plane
C
 
      CALL ELLIPS  ( AXIS1,  AXIS2, AXIS3, CENTER, VERTEX,
     .               NORMAL, MAJOR, MINOR, MIDPNT, CANECL )
 
C
C     Adjust the normal to the terminator plane so that it
C     points towards the dark side of the body.
C
      IF ( VDOT(CAXIS,  NORMAL) .LT. 0 ) THEN
         NORMAL(1) = - NORMAL(1)
         NORMAL(2) = - NORMAL(2)
         NORMAL(3) = - NORMAL(3)
      END IF
 
      RETURN
 
      END
