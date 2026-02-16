C  

C Introduction
C ===========================================================================
C  

C      Euclid is a subroutine used to render the appearance of a collection
C      of solid ellipsoids illuminated by a number of light sources. The
C      scene produced is realistic in that bodies partially or completely
C      behind other bodies are properly obscured in the picture. Shadows cast
C      by bodies onto other bodies are portrayed accurately. In addition to
C      ellipsoids, Euclid can draw elliptical rings, ``stars'' and figures
C      overlayed onto the image plane.
C  

C      To use Euclid you must have a working copy of ESCHER ---a subroutine
C      package that ``knows'' how to draw vectors on the display device you
C      plan to use.
C  

C  

C An overview of Euclid
C ===========================================================================
C  

C      Euclid is actually an umbrella subroutine for a collection of entry
C      points that give you great freedom in the composition of pictures. We
C      can form a loose analogy between these entry points and the process of
C      composing a still photograph with a pin-hole camera. The most
C      important entry points are:
C  

C            EUINIT   This entry point corresponds to turning on the camera.
C                     You need only do it once in your program.
C  

C            EUVIEW   This entry point corresponds to choosing a lens (or
C                     zoom setting) and film for the camera.
C  

C            EUGEOM   This entry point corresponds to placing the camera,
C                     subjects and lighting.
C  

C            EUCLR    This entry point corresponds to advancing the film.
C  

C            EUBODY   This entry point corresponds to shooting the photograph
C                     and developing it (although it is developed one body at
C                     a time).
C  

C      There are three other entry points EUSTAR, EURING, EUTEMP. They will
C      be discussed later, but basically they correspond to refinements in
C      the development process---they allow other features to appear in the
C      image.
C  

C      To help you get you started with the protocol required for producing a
C      picture, here's a bit of pseudo-code that illustrates how the entry
C      points of Euclid can be combined to draw a picture.
C  

C         Initialize Euclid
C  

C         CALL EUINIT
C  

C         FOR EACH PICTURE
C  

C              ...establish the field of view, the device to draw the picture
C                 and the region of the device to use for the picture
C  

C              CALL EUVIEW ( display parameters )
C  

C              ...clear the region where the image will be drawn
C  

C              CALL EUCLR  ( display parameters )
C  

C              ...define the geometry of the scene to be drawn
C  

C              CALL EUGEOM ( number, position, and radii of illumination sour
C                            position, pointing, and orientation of the camer
C                            number, position, size, and orientation of ellip
C  

C              FOR EACH BODY
C  

C                   ... draw it
C  

C                   CALL EUBODY ( id and appearance attributes for the body )
C  

C      In the example above, we allow for the possibility that between
C      consecutive pictures you may want to change the lens and film and
C      reposition the lighting and subjects. However, for many cases one lens
C      and film type are sufficient. Thus the call to EUVIEW could be placed
C      immediately following EUINIT.
C  

C         CALL EUINIT
C         CALL EUVIEW ( display parameters )
C  

C         FOR EACH PICTURE
C  

C              ...clear the region where the image will be drawn
C  

C              CALL EUCLR ( display parameters )
C  

C              ...define the geometry of the scene to be drawn
C  

C              CALL EUGEOM ( lighting, camera, and subject geometry )
C              .
C              .
C              .
C  

C      If you wished to compose a multiple exposure photo sequence, you would
C      take several pictures without advancing the film.
C  

C         CALL EUINIT
C         CALL EUVIEW ( ... )
C         CALL EUCLR  ( ... )
C  

C         FOR EACH EXPOSURE
C  

C              CALL EUGEOM ( lighting, camera and subject geometry for this e
C  

C              FOR EACH SUBJECT
C  

C                   CALL EUBODY ( id and appearance attributes for subject )
C  

C      Finally if you wanted the various bodies in the scene to ``show
C      through'' one another you could set up the camera, place the subjects
C      and shoot them one at a time without advancing the film.
C  

C         CALL EUINIT
C         CALL EUVIEW ( ... )
C  

C         FOR EACH PICTURE
C  

C              CALL EUCLR  ( ... )
C  

C              FOR EACH BODY
C  

C                   CALL EUGEOM ( lighting, camera and this body's geometry )
C  

C                   CALL EUBODY ( appearance attributes for this body )
C  

C  

C Initializing Euclid---EUINIT
C ===========================================================================
C  

C      Before calling any of the other entry points to Euclid, you must call
C      Euclid's initialization entry point, EUINIT. It has no arguments.
C  

C         CALL EUINIT
C  

C      This entry point computes tables of values to be used by the other
C      entry points. You need only call this entry point once during the
C      execution of your program. Repeated calls have no effect.
C  

C  

C Picture Geometry---EUGEOM
C ===========================================================================
C  

C      EUGEOM is the routine used to describe the geometry of a scene to be
C      photographed with the pin-hole camera. The calling sequence for EUGEOM
C      is:
C  

C          CALL EUGEOM ( NLITES, LITPOS, LITRAD,
C         .              CAMPOS, CMATRX,
C         .              NBODS,  BODPOS, AXES    )
C  

C  

C Illumination Sources: NLITES, LITPOS, LITRAD
C  

C      Euclid allows you to model the illumination of the scene by a
C      collection of up to 4 spherical illumination sources. (Actually you
C      can reconfigure Euclid to allow any number of illumination sources.
C      See the chapter on fine points for more information.) To illuminate a
C      scene you need to tell Euclid how many light sources you have, where
C      they are located and their radii. The variables for supplying this
C      information are NLITES, LITPOS and LITRAD.
C  

C            NLITES    INT         This is the number of light sources you
C                                  are going to use to illuminate the scene.
C  

C            LITPOS    DP(3,*)     This is an array of position vectors for
C                                  the light sources. The position of the
C                                  i'th light sources is given by
C                                  LITPOS(1-3,i).
C  

C            LITRAD    DP(*)       This is an array of radii for the light
C                                  sources. The radius of the i'th light
C                                  source is given by LITRAD(i).
C  

C  

C The Camera: CAMPOS, CMATRX
C  

C      The camera model used by Euclid is a simple pin-hole camera. Subjects
C      are projected through the pin-hole to an image plane at distance 1
C      from the pinhole. To produce a picture Euclid needs to know where the
C      camera is, its pointing and its orientation. This information is
C      supplied through the variables CAMPOS and CMATRX
C  

C            CAMPOS    DP(3)       This is a vector giving the position of
C                                  the pin-hole of the camera.
C  

C            CMATRX    DP(3,3)     This is an orthogonal matrix describing
C                                  the camera pointing and orientation. The
C                                  first and second columns of this matrix
C                                  contain the inertial pointing of the the
C                                  camera frame x- and y-axes, respectively.
C                                  They lie in the plane of the film. The
C                                  third column contains the z-axis of the
C                                  camera frame. It points toward the scene
C                                  being photographed. (Note that although
C                                  the camera axes should be unit vectors and
C                                  mutually orthogonal, they may form either
C                                  a left- or right-handed frame. Use
C                                  whatever frame is most convenient.)
C  

C  

C The subject bodies: NBODS, BODPOS, AXES
C  

C      Euclid can draw any collection of up to 100 ellipsoidal bodies.
C      (Euclid can be reconfigured to allow for more or fewer than 100
C      bodies. See the chapter on fine points for more information.) You need
C      to tell Euclid how many there are, where they are located, and the
C      length and orientation of their principal axes. These items are
C      supplied through the variables NBODS, BODPOS and AXES respectively.
C  

C            NBODS     INT         This is the number of bodies that are
C                                  going to be potential subjects of the
C                                  picture.
C  

C            BODPOS    DP(3,*)     This is an array of position vectors for
C                                  the centers of the ellipsoids. The
C                                  position of the center of the i'th body is
C                                  given by the vector BODPOS(1-3,i).
C  

C            AXES      DP(3,3,*)   This array is used to store the
C                                  orientation and lengths of the principal
C                                  axes of the bodies. The vector
C                                  AXES(1-3,1,i) points along the x-principal
C                                  semiaxis of the i'th body and has length
C                                  equal to it. The vector AXES(1-3,2,i)
C                                  points along the y-principal semiaxis of
C                                  the i'th body and has length equal to it.
C                                  Finally the vector AXES(1-3,3,i) points
C                                  along the z-principal semiaxis of the i'th
C                                  body and has length equal to it. The x-
C                                  and y-principal axes are assumed to define
C                                  the equator of the body. Latitude circles
C                                  will be drawn parallel to the equator.
C                                  Meridians will be drawn so that they pass
C                                  through the ends of the z-principal axis.
C  

C  

C Describing the camera---EUVIEW
C ===========================================================================
C  

C      EUVIEW is the routine used to describe what portion of the scene
C      composed with EUGEOM you wish to see and how and where to display it.
C      The calling sequence to EUVIEW is:
C  

C          CALL EUVIEW ( DEVICE, H1, H2, V1, V2,
C         .                      X1, X2, Y1, Y2 )
C  

C  

C Where the image goes: DEVICE
C  

C      Euclid allows for the possibility that your version of ESCHER may
C      support several display devices. Thus you need to tell Euclid the
C      device number on which you want the picture displayed.
C  

C            DEVICE    INT         This variable points to a number
C                                  recognized by ESCHER as a valid device. At
C                                  various times 5 different devices have
C                                  been supported by ESCHER. You will need to
C                                  examine your version of ESCHER to
C                                  determine what values of DEVICE are
C                                  legitimate.
C  

C  

C How much of the device to use: H1, H2, V1, V2
C  

C      It is quite possible that you don't want to use the entire screen of
C      your display device for a picture. You may want to put up a matrix of
C      pictures that shows the evolution of a scene in time or to leave some
C      part of the device free for text. Euclid has made allowances for these
C      scenarios. Using the variables H1, H2, V1, and V2 you can specify what
C      part of the device to use for a picture.
C  

C      For the purposes of Euclid every display device has a horizontal and
C      vertical scale. Both range from 0 to 1. The 0 point on the horizontal
C      scale is at the left edge of the display, 1 is at the right edge. The
C      0 point of the vertical scale is at the bottom of the display, 1 is at
C      the top.
C  

C            H1,H2     DP          These specify the horizontal limits of the
C                                  region to use for display of the image. H1
C                                  and H2 must be different and both must be
C                                  between 0 and 1 inclusive. There is no
C                                  order requirement for H1 and H2.
C  

C            V1,V2     DP          These specify the vertical limits of the
C                                  region to use for display of the image. V1
C                                  and V2 must be different and both must be
C                                  between 0 and 1 inclusive. There is no
C                                  order requirement for V1 and V2.
C  

C      The illustration below shows how the display rectangle looks when the
C      display device is twice as wide as it is high and when H1 through V2
C      are chosen as described.
C  

C         H1 = 0.6
C         H2 = 0.1
C         V1 = 0.9
C         V2 = 0.4
C  

C  

C          1 +---------------------------------------+
C            | +===================+  <-- V1 edge    |
C            | |                   |                 |
C            | |    Display        |                 |
C            | |    Rectangle      |                 |
C            | |                   |                 |
C            | +===================+  <-- V2 edge    |
C            | ^                   ^                 |
C            | H2  edge            H1 edge           |
C            |                                       | <=== Display Device
C          0 +---------------------------------------+
C            0                                       1
C  

C      When the display is twice as tall as it is wide we get the picture
C      shown below.
C  

C                            +----------+
C         H1 = 0.6           |+====+ V1 |
C         H2 = 0.1           ||    |    |
C         V1 = 0.9           ||    |    |
C         V2 = 0.4           ||    |    |
C                            ||    |    |
C                            |+====+ V2 |
C                            |H2   H1   |
C                            |          |<=== Display Device
C                            |          |
C                            +----------+
C  

C  

C The part of the image that gets developed: X1, X2, Y1, Y2
C  

C      The image plane of our pinhole camera is infinite in extent.
C      Mathematically, one can easily form the pinhole projection of
C      everything that lies in front of the camera. However, the image plane
C      has to be mapped onto a rectangular region of the display device. It's
C      not possible to map the entire image plane onto a rectangle and
C      preserve relative scales. You must decide what portion of the camera
C      image plane you will display. This is done by specifying the
C      boundaries of a rectangle in the image plane that will be mapped to
C      the rectangular display region.
C  

C            X1,X2     DP          These are the x-coordinate boundaries of
C                                  the rectangle in the image plane that will
C                                  be mapped onto the display device. X1 and
C                                  X2 must have different values.
C  

C            Y1,Y2     DP          These are the y-coordinate boundaries of
C                                  the rectangle in the image plane that will
C                                  be mapped onto the display device. Y1 and
C                                  Y2 must have different values.
C  

C  

C Measuring the image plane
C  

C      By definition the distance from the pinhole to the image plane is 1.
C      From this it follows that a point R units from the origin in the image
C      plane, is the projection of a point that is ARCTAN(R) radians away
C      from the camera axis. To specify a rectangle in the image plane
C      centered about the camera axis that is A radians across set
C  

C         X1 = -TAN(A/2)
C         X2 =  TAN(A/2)
C         Y1 = -TAN(A/2)
C         Y2 =  TAN(A/2)
C  

C  

C Mapping from the image plane to the display
C  

C      The mapping from the image plane to the rectangle on the device is
C      performed so that relative scales in the image plane are preserved.
C      (Squares in the image plane will look like squares on your display
C      device). Since the physical shape of the display rectangle may not be
C      the same as the shape of the image plane rectangle, the mapping of the
C      image plane rectangle may not fill the display rectangle. However, the
C      mapping carries the the center of the image plane rectangle to the
C      center of the display device rectangle. The X1, X2, Y1, and Y2 edges
C      of the image plane rectangle are mapped so that the lie on or next to
C      the H1, H2, V1 and V2 edges of the device rectangle, respectively.
C  

C      Continuing the example above in which the display is twice as wide as
C      tall, a square image plane rectangle would map into the display
C      rectangle as shown below.
C  

C          1 +---------------------------------------+
C            | +====::::::::::=====+                 |
C            | |    :mapping::     |                 |
C            | |    ::of::::::     |<--Display       |
C            | |    :::image::     |   Rectangle     |
C            | |    ::::box:::     |                 |
C            | +====::::::::::=====+                 |
C            |                                       |
C            |                                       |
C            |                                       | <=== Display Device
C          0 +---------------------------------------+
C            0                                       1
C  

C      When the display is twice as tall as it is wide we get the picture
C      shown below.
C  

C                    +------------+
C                    | +====+     |
C                    | |    |     |
C                    | ::::::     |
C                    | ::::::     |
C                    | ::::::     |
C                    | |    |     |
C                    | +====+     |
C                    |            |
C                    |            |<=== Display Device
C                    |            |
C                    |            |
C                    +------------+
C  

C  

C Getting the display you want
C  

C      As already mentioned there is no order requirement on the pairs
C      (H1,H2), (V1,V2), (X1,X2), and (Y1,Y2). However, the ordering of each
C      pair does have an effect on the image you will see. If the display
C      rectangle is physically a square and the image plane rectangle is
C      square then the X1, X2, Y1, and Y2 image plane edges map to the H1,
C      H2, V1, and V2 display edges. Thus by swapping the values of H1 and H2
C      while leaving all other values unchanged, the image will be reflected
C      about a vertical line passing through the center of the display
C      rectangle.
C  

C      To illustrate all possible cases, suppose that a trapezoid as shown
C      below, is on a plane perpendicular to the camera's optical axis in
C      front of the camera and that the camera matrix is right handed. (In
C      other words, if you were at the camera location, looking in the
C      direction the camera is pointed, with the top of your head pointing in
C      the direction of the positive y-axis and your left hand pointing along
C      the positive x-axis, you would see the trapezoid drawn below.)
C  

C  

C            |\
C            | \
C            |  \
C            |   |
C            |   |
C            |___|
C  

C  

C      If we project the trapezoid to the image plane and set the values of
C      (X1,X2) and (Y1,Y2) so that the second component of each pair is
C      greater than the first, then the possible displays of the trapezoid
C      are shown below.
C  

C            (negative)                 (print rotated 1/2 revolution)
C  

C              +---+                      +---+
C              |   |                      |   |
C              |   |                      |   |
C              |  /                        \  |
C              | /                          \ |
C              |/                            \|
C  

C              H1 < H2                    H1 > H2
C              Y1 < Y2                    Y1 < Y2
C  

C  

C  

C  

C             (print)                   (negative rotated 1/2 revolution)
C  

C              |\                            /|
C              | \                          / |
C              |  \                        /  |
C              |   |                      |   |
C              |   |                      |   |
C              +---+                      +---+
C  

C              H1 < H2                    H1 > H2
C              Y1 > Y2                    Y1 > Y2
C  

C  

C  

C Erasing the display---EUCLR
C ===========================================================================
C  

C      Euclid lets you decide when to clear the display device and how much
C      of it to clear. By giving you the freedom to decide how much and when
C      to clear the display, you can produce multiple exposure images, insert
C      smaller images in the corners of larger images, etc. You clear the
C      display by calling EUCLR. The calling sequence is:
C  

C         CALL EUCLR ( DEVICE, H1, H2, V1, V2 )
C  

C      The meanings of the arguments are the same as they are in EUVIEW.
C  

C            DEVICE    INT         This variable points to a number
C                                  recognized by ESCHER as a valid device. At
C                                  various times 5 different devices have
C                                  been supported by ESCHER. You will need to
C                                  examine your version of ESCHER to
C                                  determine what values of DEVICE are
C                                  legitimate.
C  

C            H1,H2     DP          These specify the horizontal limits of the
C                                  region to use for display of the image. H1
C                                  and H2 must be different and both must be
C                                  between 0 and 1 inclusive.
C  

C            V1,V2     DP          These specify the vertical limits of the
C                                  region to use for display of the image. V1
C                                  and V2 must be different and both must be
C                                  between 0 and 1 inclusive.
C  

C  

C Drawing a body---EUBODY
C ===========================================================================
C  

C      Once you have set up the picture geometry and camera parameters, you
C      are ready to draw the picture. You do this by calling the entry point
C      EUBODY once for each body you want to appear in the image (that was
C      also supplied as one of the bodies to EUGEOM). The calling sequence to
C      EUBODY is:
C  

C          CALL EUBODY ( NUMBER, MERIDS, LATS, SRCREQ, LIT, DARK, TERM )
C  

C  

C The body to draw: NUMBER
C  

C      You can only draw one of the bodies that were supplied to EUGEOM
C      through the arrays BODPOS and AXES. To draw the i'th body ( body with
C      position BODPOS(1-3,i) ) set NUMBER equal to i.
C  

C            NUMBER    INT         This is number of the body to draw. This
C                                  must be between 1 and NBODS inclusive
C                                  (where NBODS was the number to EUGEOM on
C                                  the last call to EUGEOM).
C  

C  

C Coordinate grids on the body: MERIDS, LATS
C  

C      Each body you draw can have a coordinate grid imposed on it. This
C      often helps you visualize the shape of the body you are drawing. The
C      coordinate curves are called meridian and latitude ``circles.''
C      Meridian circles are formed by slicing the body with a plane that
C      contains the z-principal axis (as specified for the body in the array
C      AXES on the last call to EUGEOM). The latitude circles are formed by
C      slicing the body with a plane perpendicular to the z-principal axis.
C      The number of meridian and latitude circles are specified with the
C      variables MERIDS and LATS respectively. Meridian circles will be
C      equally spaced in angle with one contained in the x-z plane of the
C      body. Latitude circles will be equally spaced in planetographic
C      latitude as determined by the meridian contained in the x-z plane. The
C      maximum number of meridian or latitude circles is 18. (This number can
C      be modified if needed. See the chapter on find points.)
C  

C            MERIDS    INT         This is the number of meridian circles to
C                                  form for the body.
C  

C            LATS      INT         This is the number of latitude circles to
C                                  form for the body.
C  

C  

C Deciding what's lit and what's not: SRCREQ
C  

C      Euclid allows you to illuminate a scene with any number of
C      illumination sources. In addition, you can specify for each body, how
C      many of these sources must illuminate a region of the body for it to
C      be considered lit. For example you might want to ``illuminate'' the
C      earth from a set of communication satellites and only wish to consider
C      a region lit if two or more satellites illuminate it. In such a case
C      you would set SRCREQ (the sources required for illumination) equal to
C      2. If only one satellite needs to illuminate the region for it to be
C      considered lit, set SRCREQ to 1.
C  

C            SRCREQ    INT         This is the number of light sources that
C                                  must illuminate a point for it to be
C                                  considered lit. Any integer value from 0
C                                  to NLITES+1 (as specified in by the last
C                                  call to EUGEOM) is allowed.
C  

C  

C Colors depend upon lighting: LIT, DARK, TERM
C  

C      You can assign different ``colors'' to each of the differently lit
C      regions of a body. The portions that are illuminated by at least
C      SRCREQ light sources will be drawn with the color specified in LIT.
C      The portions that are not illuminated by at least SRCREQ light sources
C      will be drawn with the color specified in DARK. The boundary between
C      the lit and dark regions (the terminator) of the body will be drawn
C      with the color specified in TERM. The actual color mapping depends
C      upon the device on which you display the picture. You will need to
C      consult your version of ESCHER to determine what numbers correspond to
C      the colors you wish to use.
C  

C            LIT       INT         The integer corresponding to the color
C                                  with which you wish to portray illuminated
C                                  portions of the body.
C  

C            DARK      INT         The integer corresponding to the color
C                                  with which you wish to portray dark
C                                  regions of the body.
C  

C            TERM      INT         The integer corresponding to the color
C                                  with which you wish to portray the
C                                  terminator of the body.
C  

C      Note that the terminator of a body is what would be seen if only that
C      body and the light sources existed. The edges of shadows cast by other
C      bodies are not drawn, but any grid lines that pass through the shadow
C      are drawn according to the number of light sources that illuminate
C      them.
C  

C  

C Beyond Ellipsoids
C ===========================================================================
C  

C      Euclid's main task is the rendering of collections of ellipsoids
C      illuminated by a collection of light sources. However, for
C      astronomical simulations one is also interested in stars, planetary
C      rings, and orbits of bodies. In addition it is often useful to be able
C      to place overlays on images so that the scale of an image can be
C      grasped more easily. The entry points EUSTAR, EURING, and EUTEMP
C      provide these capabilities.
C  

C            EUSTAR   This entry point allows you to mark points in an image
C                     with characters that will not change in appearance as
C                     the image plane rectangle is altered.
C  

C            EURING   This entry point provides a mechanism for sketching
C                     planetary rings and the orbits of bodies.
C  

C            EUTEMP   This entry point allows you to place overlays on the
C                     image plane. In this way you can mark reference points,
C                     such as the location of aperture boundaries.
C  

C      You may call these entry points in any order. However, to render
C      scenes as they would appear to the eye you should call them in the
C      order they have been listed, and after all calls to EUBODY have been
C      completed.
C  

C         CALL EUINIT
C  

C         FOR EACH PICTURE
C  

C             CALL EUVIEW ( display parameters )
C             CALL EUCLR  ( display parameters )
C             CALL EUGEOM ( camera, lighting and subject geometry )
C  

C             FOR EACH BODY
C                 CALL EUBODY ( id and appearance attributes for the body )
C  

C  

C             ...draw any stars that might appear
C  

C             CALL EUSTAR ( positions, appearance attributes )
C  

C  

C             ...draw any rings that might appear---one ring at at time.
C  

C             FOR EACH RING
C                 CALL EURING ( ring definition and appearance attributes )
C  

C  

C             ...draw the overlays on top of everything else.
C  

C             CALL EUTEMP ( overlay description and appearance attributes )
C  

C  

C Drawing stars and other characters---EUSTAR
C ===========================================================================
C  

C      Occasionally we want to draw points (such as the locations of stars)
C      that lie in same direction as do the bodies specified by EUGEOM. This
C      could be done by simply putting small bodies at the points, passing
C      them to Euclid through EUGEOM and reserving one color to use only for
C      these ``point bodies.'' However, this scheme has a drawback. The size
C      of the drawing of a body body changes depending upon the size of the
C      image plane rectangle. Of course, a point isn't magnified no matter
C      how much we change the image plane rectangle. For this reason it's
C      often desirable to mark the position of a point with a character that
C      will not change size when the size of the image plane rectangle
C      changes. The entry point EUSTAR gives you this capability. Characters
C      marking the position of points are always drawn the same size
C      regardless of the size of the image plane rectangle. The calling
C      sequence to EUSTAR is:
C  

C         CALL EUSTAR ( POINTS, NPTS, FONT, FSIZE, FSCALE, COLOR )
C  

C  

C Where the points are: POINTS, NPTS
C  

C      As mentioned earlier Euclid was designed with the problem of
C      displaying astronomical images in mind. As a result you can mark the
C      position of several points at once. To mark them you need to supply
C      the number of points and their positions via NPTS and POINTS
C      respectively.
C  

C            POINTS    DP(3,*)     This array contains the positions of the
C                                  points to be marked. The position of the
C                                  i'th point is given by the vector (
C                                  POINTS(1-3,i) ).
C  

C            NPTS      INT         This is the number of points to mark.
C  

C  

C The character marking the points: FONT, FSIZE, FSCALE
C  

C      To mark a point you must create a character or font to mark it.
C  

C      To create a font all you have to do is draw the character on graph
C      paper using straight-line segments, count off the locations of the
C      vertices, and load the endpoints of each segment in the array FONT.
C      For example, to draw the cube
C  

C             (-1,3)  .------. (4,3)
C                    /      /|
C                   /      / |
C         (-3,0)   '------'  |
C                  |      |  . (4,0)
C                  |      | /
C                  |      |/
C                  '------' (2,-3)
C         (-3,-3)
C  

C      you would create the following array :
C  

C              DOUBLE PRECISION FONT (2,2,9)
C              DOUBLE PRECISION FSCALE
C              INTEGER          FSIZE
C  

C  

C              DATA             FSIZE    /  9     /
C              DATA             FSCALE   / 0.01D0 /
C  

C              DATA             FONT     / -3.0D0, -3.0D0,  2.0D0,  3.0D0,
C             .                             2.0D0, -3.0D0,  4.0D0,  0.0D0,
C             .                             4.0D0,  0.0D0,  4.0D0,  3.0D0,
C             .                             4.0D0,  3.0D0, -1.0D0,  3.0D0,
C             .                            -1.0D0,  3.0D0, -3.0D0,  0.0D0,
C             .                            -3.0D0,  0.0D0, -3.0D0,  3.0D0,
C             .                            -3.0D0,  0.0D0,  2.0D0,  0.0D0,
C             .                             2.0D0,  0.0D0,  4.0D0,  3.0D0,
C             .                             2.0D0,  0.0D0,  2.0D0, -3.0D0   /
C  

C      Note that because each segment is completely specified, you are not
C      restricted to drawing arcs or closed curves.
C  

C      Each character is scaled to FSCALE times the size of the current
C      display rectangle. Thus if we set FSCALE to 0.01 each character will
C      be one percent as wide or tall (whichever is smaller) as the current
C      display rectangle. One hundred characters, drawn end to end, would
C      stretch across the rectangle.
C  

C      The center the coordinate system used to define your segments, maps to
C      the position of the point.
C  

C            FONT      DP(2,2,*)   This array contains a description of the
C                                  segments that make up the character used
C                                  to mark the location of points. The
C                                  beginning endpoint of the i'th segment
C                                  making up the character is given by
C                                  FONT(1-2,1,i). The terminating endpoint is
C                                  given by FONT(1-2,2,i).
C  

C            FSIZE     INT         This is the number of segments used to
C                                  create the character. The limit on the
C                                  number of segments is slightly more than
C                                  1600 segments. (This limit can be
C                                  adjusted. See the chapter on fine points
C                                  of Euclid.)
C  

C            FSCALE    DP          This is a number between 0 and 1 that
C                                  tells Euclid how large the character
C                                  should appear on the display device. The
C                                  height and width will be FSCALE times the
C                                  minimum of the height and width of the
C                                  display rectangle.
C  

C  

C The color to draw the font: COLOR
C  

C      As with everything else you can specify the color in which the font
C      should be drawn. You need to check your version of ESCHER to determine
C      what integers are valid color descriptors for the device you are
C      using.
C  

C            COLOR     INT         The integer code for the color to use when
C                                  drawing the image plane overlay.
C  

C  

C Drawing rings---EURING
C ===========================================================================
C  

C      Euclid was originally written so that it could simulate scenes viewed
C      by planetary spacecraft. It was very desirable to be able to draw
C      planetary rings. Elliptical rings can be drawn using the entry point
C      EURING. These rings are simply curves. They do not cast shadows. The
C      calling sequence for EURING is:
C  

C         CALL EURING ( CENTER, MAJOR, MINOR, SRCREQ, LIT, DARK )
C  

C  

C The ring description: CENTER, MAJOR, MINOR
C  

C      To specify an elliptical ring you need to specify the center of the
C      ring and the axes the vectors that point along the principal semi-axes
C      having length equal to them. The vectors are supplied to EURING
C      through CENTER, MAJOR and MINOR.
C  

C            CENTER    DP(3)       This is a vector giving the center of the
C                                  ring. Typically, this will be at the
C                                  center of one of the bodies supplied
C                                  through EUGEOM, but it doesn't have to be.
C                                  For example, you might supply a ring that
C                                  models the instantaneous orbit of a planet
C                                  in which case the center might be the
C                                  center of the sun or the solar system
C                                  barycenter.
C  

C            MAJOR     DP(3)       This is a vector pointing in the direction
C                                  of the semimajor axis of the ring and
C                                  having length equal to it.
C  

C            MINOR     DP(3)       This is a vector pointing in the direction
C                                  of the semi-minor axis of the ring and
C                                  having length equal to it.
C  

C      Note that MAJOR and MINOR are assumed to be orthogonal. However, if
C      they are nearly orthogonal there will be no degradation in the quality
C      of the picture.
C  

C  

C What's lit and what's not: SRCREQ
C  

C      As with each body, you can decide how many light sources must
C      illuminate the ring to make it lit. Specify the number of sources
C      required with SRCREQ.
C  

C            SRCREQ    INT         This is the number of light sources that
C                                  must illuminate a point for it to be
C                                  considered lit. Any integer value from 0
C                                  to NLITES+1 (as specified in by the last
C                                  call to EUGEOM) is allowed.
C  

C  

C Colors depend upon lighting: LIT, DARK
C  

C      As with each body, you can decide the color to draw the lit and dark
C      portions of the ring. You supply this information through the
C      variables LIT and DARK. Unlike bodies, rings do not have modeled
C      terminators. As in the case of EUBODY, you need to check your version
C      of ESCHER to determine what are legitimate numbers for describing the
C      lit and dark portions of the ring.
C  

C            LIT       INT         The integer corresponding to the color
C                                  with which you wish to portray illuminated
C                                  portions of the ring.
C  

C            DARK      INT         The integer corresponding to the color
C                                  with which you wish to portray dark
C                                  regions of the ring.
C  

C  

C Overlays on the image plane---EUTEMP
C ===========================================================================
C  

C      It is sometimes useful to have reference points overlayed on the image
C      plane. For example it may be useful to have an angle scale marked out
C      on the image plane. These markings can be displayed along with the
C      rest of your image by passing them to the entry point EUTEMP. The
C      calling sequence for EUTEMP is:
C  

C          CALL EUTEMP ( XBEGIN, YBEGIN,
C         .              XEND,   YEND,
C         .              NSEGS,  COLOR )
C  

C  

C Describing the overlay: XBEGIN, YBEGIN, XEND, YEND, NSEGS
C  

C      Any figure that can be described by a series of line segments can be
C      overlayed on the image plane. You simply need to supply the
C      coordinates of the line segments.
C  

C            XBEGIN    DP(*)       This is an array of numbers that gives the
C                                  x-coordinate of the beginnings of line
C                                  segments in the image plane. The
C                                  x-coordinate of the beginning endpoint of
C                                  the i'th segment is given by XBEGIN(i).
C  

C            YBEGIN    DP(*)       This is an array of numbers that gives the
C                                  y-coordinate of the beginnings of line
C                                  segments in the image plane. The
C                                  y-coordinate of the beginning endpoint of
C                                  the i'th segment is given by YBEGIN(i).
C  

C            XEND      DP(*)       This is an array of numbers that gives the
C                                  x-coordinate of the ends of line segments
C                                  in the image plane. The x-coordinate of
C                                  the ending endpoint of the i'th segment is
C                                  given by XEND(i).
C  

C            YEND      DP(*)       This is an array of numbers that gives the
C                                  y-coordinate of the ends of line segments
C                                  in the image plane. The y-coordinate of
C                                  the ending endpoint of the i'th segment is
C                                  given by YEND(i).
C  

C            NSEGS     INT         This is the number of segments that are in
C                                  the overlay.
C  

C  

C Coloring the overlay: COLOR
C  

C      As with everything else you can specify the color in which the image
C      plane overlay should be drawn. Again you need to check your version of
C      ESCHER to determine what integers are valid color descriptors for the
C      device you are using.
C  

C            COLOR     INT         The integer code for the color to use when
C                                  drawing the image plane overlay.
C  

C  

C Fine Points of Euclid
C ===========================================================================
C  

C      This chapter points out some of the subtler details of Euclid and
C      outlines the size limits and how to adjust them.
C  

C  

C Putting the camera inside a body.
C --------------------------------------------------------
C  

C      Suppose you wanted to simulate an eclipse of the moon as it would be
C      seen from the center of the earth, (if the earth wasn't in the way).
C      How do you describe the scene to Euclid?
C  

C      First you should remember, that for a body to cast a shadow it must be
C      listed in the list of bodies supplied to EUGEOM. Thus you would need
C      to supply the earth and moon as bodies to EUGEOM. You also need to
C      supply the description of the sun. Now simply put the camera at the
C      center of the earth and point it at the moon.
C  

C  

C Doesn't the earth get in the way?
C  

C      Whenever the camera is inside a body, that body becomes invisible to
C      the camera. The body will still cast shadows but it can no longer
C      obstruct the view of any of the other bodies supplied to EUGEOM.
C  

C  

C Looking at illumination sources.
C --------------------------------------------------------
C  

C      Euclid can only draw bodies that are listed among the body
C      descriptions of EUGEOM. To make an illumination source visible, you
C      need to put it in the list of bodies as well as in the list of
C      illumination sources. Euclid determines how to draw such an object by
C      assuming that if the center of a light source lies inside a body, the
C      body is completely illuminated by that light source. However such a
C      body can still cast shadows if there are other light sources and more
C      than two light sources are required to illuminate a point. The body
C      just can't block the light source it contains.
C  

C  

C Limits
C --------------------------------------------------------
C  

C      Euclid requires internal storage in order to compute the appearance of
C      a scene. Since it is written in FORTRAN, this internal storage can not
C      be allocated at run-time. Rather it must be allocated when Euclid is
C      compiled. Should you determine that the limits described elsewhere are
C      not appropriate for your application you can change them by modifying
C      a handful of parameters in Euclid's source code. (Make a backup copy
C      of your version of Euclid before you start down this path.)
C  

C            MAX_SOURCES    This parameter controls the maximum number of
C                           light sources that can be modeled by Euclid. It
C                           is nominally set to 4. For many applications this
C                           can be set to 1.
C  

C                           Changing this parameter will alter MAX_SEGS.
C                            (See below.)
C  

C  

C Changing the maximum number of bodies
C  

C            MAX_BODS       This parameter controls the maximum number of
C                           bodies that can be modelled by Euclid. It is
C                           nominally set to 100. For most applications a
C                           value of 40 is more than sufficient.
C  

C                           Changing this parameter will alter MAX_SEGS.
C                            (See below.)
C  

C  

C Changing the maximum number of meridian circles
C  

C            MAX_MERIDS     This parameter determines the maximum number of
C                           meridian circles that can be drawn on a body. It
C                           is nominally set to 50. Most applications can get
C                           by with 18 or fewer.
C  

C                           Changing this parameter will alter MAX_SEGS.
C                            (See below.)
C  

C  

C Changing the maximum number of latitudes circles
C  

C            MAX_LATCIR     This parameter determines the maximum number of
C                           latitude circles that can be drawn on a body. It
C                           is nominally set to 50. Again, most applications
C                           can get by with 18 or fewer.
C  

C                           Changing this parameter will alter MAX_SEGS.
C                            (See below.)
C  

C  

C Changing the maximum number of font segments
C  

C            MAX_SEGS       This parameter controls the maximum number of
C                           font segments that can be used by the entry point
C                           EUSTAR. It is defined in terms of the other
C                           parameters listed above. The nominal value is:
C  

C                                MAX_SEGS = 99
C                                         + 3*MAX_SOURCES*MAX_BODS
C                                         + 3*MAX_SOURCES
C                                         + 3*MAX_MERIDS
C                                         + 3*MAX_LATCIR
C  

C                           MAX_SEGS  may be altered provided that it is
C                           given a value larger than the nominal value
C                           described above.
C  

C-&

      SUBROUTINE EUCLID ( XBEGIN, YBEGIN, XEND, YEND )

C
C  Arguments for ENTRY EUGEOM
C

      INTEGER               NLITES


      DOUBLE PRECISION      SOURCE(3,*)
      DOUBLE PRECISION      SRCRAD(  *)
      DOUBLE PRECISION      OBSRVE(3)
      DOUBLE PRECISION      CAMFRM(3,3)
      INTEGER               NBODS
      DOUBLE PRECISION      BODIES(3,*)
      DOUBLE PRECISION      AXES(3,3,*)

C
C     Arguments for ENTRY EUVIEW
C
      INTEGER               DEVICE
      DOUBLE PRECISION      XMIN
      DOUBLE PRECISION      XMAX
      DOUBLE PRECISION      YMIN
      DOUBLE PRECISION      YMAX
      DOUBLE PRECISION      HMIN
      DOUBLE PRECISION      HMAX
      DOUBLE PRECISION      VMIN
      DOUBLE PRECISION      VMAX

C
C     Arguments for ENTRY EUBODY
C
      INTEGER               BODY
      INTEGER               MERIDS
      INTEGER               LATCIR
      INTEGER               SRCREQ
      INTEGER               BRIGHT
      INTEGER               DARK
      INTEGER               TRMNTR
C
C     Arguments for ENTRY EURING
C
      DOUBLE PRECISION      MINOR(3) 

      DOUBLE PRECISION      MAJOR(3) 

      DOUBLE PRECISION      RING(3) 

C     INTEGER               SRCREQ
C     INTEGER               BRIGHT
C     INTEGER               DARK

C
C     Arguments for ENTRY EUTEMP
C
      DOUBLE PRECISION      XBEGIN(*)
      DOUBLE PRECISION      YBEGIN(*)
      DOUBLE PRECISION      XEND  (*)
      DOUBLE PRECISION      YEND  (*)
      INTEGER               NSEGS
      INTEGER               COLOR

C
C     Arguments for ENTRY EULAND
C
      DOUBLE PRECISION      SEGBEG ( 3, *)
      DOUBLE PRECISION      SEGEND ( 3, *)

C
C     Arguements for ENTRY EUSTAR
C
      INTEGER               NSTARS
      DOUBLE PRECISION      STRPOS   (    3, * )
      DOUBLE PRECISION      FONT     ( 2, 2, * )
      INTEGER               FNTSIZ
      DOUBLE PRECISION      FNTSCL
C
C     SPICELIB functions
C

      LOGICAL               ARDERD
      DOUBLE PRECISION      VNORM
      DOUBLE PRECISION      VDOT
      LOGICAL               SMSIDE
      LOGICAL               OPSGND
      

C
C     ESCHER Error Flag
C
      CHARACTER*80     ERROR

C
C   Parameters
C
      INTEGER               MXSRCS
      PARAMETER            (MXSRCS = 4)

      INTEGER               MXBODS
      PARAMETER            (MXBODS = 100 )

      INTEGER               MAXMER
      PARAMETER            (MAXMER = 50 )

      INTEGER               MAXLAT
      PARAMETER            (MAXLAT = 50 )

      INTEGER               MAXBLP
      PARAMETER            (MAXBLP = 1 + MXSRCS 

     .                                 + MAXMER
     .                                 + MAXLAT  )

      INTEGER               STDSEG
      PARAMETER            (STDSEG = 96)

      INTEGER               MXSEGS 

      PARAMETER            (MXSEGS = STDSEG + 3*MAXBLP
     .                                      + 3*MXSRCS*MXBODS )

      DOUBLE PRECISION      PI
      PARAMETER           ( PI     = 3.14159 26535 89793 23846 D0 )


      DOUBLE PRECISION      LIMFOV
      PARAMETER            (LIMFOV = PI*5.0/12.0)

C
C   Variables used for "global Euclid" storage of geometry information
C
C     !
C     ! Initialized by call to EUGEOM
C     !

      INTEGER               NBODY
      INTEGER               NLIGHT


      DOUBLE PRECISION      RADII    (      MXSRCS )
      DOUBLE PRECISION      LIGHTS   ( 3,   MXSRCS )

      DOUBLE PRECISION      OBSRVR   ( 3 )
      DOUBLE PRECISION      CAMERA   ( 3,3)


      DOUBLE PRECISION      A        ( 3,    MXBODS )
      DOUBLE PRECISION      BIGA     (       MXBODS )
      DOUBLE PRECISION      SMALLA   (       MXBODS )
      DOUBLE PRECISION      CENTRS   ( 3,    MXBODS )
      DOUBLE PRECISION      LCENTR   ( 3,    MXBODS )
      DOUBLE PRECISION      LMINOR   ( 3,    MXBODS )
      DOUBLE PRECISION      LMAJOR   ( 3,    MXBODS )   

      DOUBLE PRECISION      LNORML   ( 3,    MXBODS )   

      DOUBLE PRECISION      PRNPLS   ( 3, 3, MXBODS )

      DOUBLE PRECISION      TNORML   ( 3, MXBODS, MXSRCS ) 

      DOUBLE PRECISION      TMAJOR   ( 3, MXBODS, MXSRCS ) 

      DOUBLE PRECISION      TMINOR   ( 3, MXBODS, MXSRCS )
      DOUBLE PRECISION      TCENTR   ( 3, MXBODS, MXSRCS ) 

      DOUBLE PRECISION      VERTEX   ( 3, MXBODS, MXSRCS ) 

      DOUBLE PRECISION      ECAXIS   ( 3, MXBODS, MXSRCS )
      

      LOGICAL               CANSEE   (    MXBODS         )
      LOGICAL               CANECL   (    MXBODS, MXSRCS )
      

C     !
C     ! Initialized by call to EUVIEW
C     !

      DOUBLE PRECISION      FOVRAD      

      DOUBLE PRECISION      FOVCEN ( 3 ) 

      DOUBLE PRECISION      FOV    ( 4 )
      DOUBLE PRECISION      VIEW   ( 4 )
      INTEGER               DSPDEV

C     ! 

C     ! Initialized by call to EUINIT
C     ! 


      DOUBLE PRECISION      STDCOS ( STDSEG )
      DOUBLE PRECISION      STDSIN ( STDSEG )

C     !
C     ! The cosine of the limiting field of view.
C     !

      DOUBLE PRECISION      COSFOV
      DOUBLE PRECISION      KAXIS  ( 3 )
C
C Variables that are constant while the same body is under consideration
C for drawing.
C
C    The following variables are assigned in EUBODY and are available to
C    other entry points (in particular EUMARK).  They are dependent upon
C    the body last input to EUBODY.  Furthermore, if OCCULTED is true,
C    the other variables are not meaningful (they are not computed if
C    the body cannot be seen).
C
C     !
C     ! Flag to indicate that the body under consideration is occulted
C     ! THIS  FLAG IS RESERVED for use by other entry points and should 

C     ! be assigned a value only in the loop of EUBODY that looks for
C     ! possible occulting bodies.  

C     !

      LOGICAL               OCCLTD

C     !
C     ! Array of possible partially occulting bodies
C     !

      INTEGER               OCANDS ( MXBODS )
      INTEGER               NOCAND

C     !
C     ! Array of possible eclipsing bodies for each light source
C     ! 


      INTEGER               ECANDS ( MXBODS, MXSRCS )
      INTEGER               NECAND (         MXSRCS )        


C     !
C     ! Number of illumination sources definately eclipsed, or posibly
C     ! eclipsed
C     !

      INTEGER               NDFECL 

      INTEGER               NPSECL 


C     !
C     ! Array of LOGICAL flags. ECLIPSED(J) = .true. indicates that
C     ! light source J can not be seen by the current body.
C     !

      LOGICAL               ECLPSD ( MXSRCS )       


C     !
C     ! Array of points on the limb
C     !

      DOUBLE PRECISION      LMBCOS ( MXSEGS )
      DOUBLE PRECISION      LMBSIN ( MXSEGS )
      INTEGER               LMBPTS


C
C  Variables used by ENTRY EUVIEW
C

      DOUBLE PRECISION      CORNER ( 3, 4 ) 


      DOUBLE PRECISION      MINCOS

C
C  Variables used by ENTRY EUCLR
C
      DOUBLE PRECISION      REGION (    4 )


C
C  Variables used first by ENTRY EUBODY
C

C     !
C     ! LOGICAL table used to indicate desired plane-ellipse intersects
C     !
      

      LOGICAL               SOLVE ( MAXBLP )
C     !
C     ! Flag to indicate that more segments need to be condidered
C     !

      LOGICAL               MORESG


C     !
C     ! Flag to indicate that some portion of the body to be drawn
C     ! might lie behind the image plane
C     !

      LOGICAL               NOVIEW

C     !
C     ! Flags to indicate whether or not endpoints of a segment 

C     ! can be viewed

      LOGICAL               BEGVIS
      LOGICAL               ENDVIS

      LOGICAL               INSIDE ( 4 )
      LOGICAL               INBACK ( 4 )

C     

C     An array that ties terminator planes to the sources that
C     determine them
C     

      INTEGER               TSRCE  ( MAXBLP )
      

C     !
C     ! Flag to indicate knowledge of darkness of a segment
C     !

      LOGICAL               UNKNWN
      LOGICAL               NOTECL
      LOGICAL               NOTLIT

C     !
C     ! Descriptive loop counters
C     !
      INTEGER               ELLPSE
      INTEGER               LSRCE

      INTEGER               SEGNO
      INTEGER               SUB

      INTEGER               NXTSTD
      INTEGER               NXTAUX

      INTEGER               SEGPTR


      INTEGER               LS
      INTEGER               CURDRK
      INTEGER               DRKREQ
      INTEGER               NDARK
      INTEGER               NILLUM

C     !
C     ! Loop increments
C     !

      INTEGER               SKIP

C     !
C     ! End of valid data in arrays are specified by the next variables
C     !

      INTEGER               MEETNS
      INTEGER               NUMSEG
      INTEGER               PLANES
      INTEGER               FPLANS
      INTEGER               NSUBS

C     !
C     ! Unit vectors pointing along body principle axes
C     !

      DOUBLE PRECISION      TEMPV1 ( 3 )
      DOUBLE PRECISION      TEMPV2 ( 3 )
      DOUBLE PRECISION      TEMPV3 ( 3 )

C     !
C     ! Angle variables
C     !

      DOUBLE PRECISION      BASESN
      DOUBLE PRECISION      BASECS

      DOUBLE PRECISION      SINANG
      DOUBLE PRECISION      COSANG
      DOUBLE PRECISION      TANANG

C     !
C     ! vector scaling variables
C     !

      DOUBLE PRECISION      T
      DOUBLE PRECISION      X
      DOUBLE PRECISION      Y
      DOUBLE PRECISION      Z

C     !
C     ! Body PLANE variables
C     !

      DOUBLE PRECISION      PNORML ( 3, MAXBLP )
      DOUBLE PRECISION      PMAJOR ( 3, MAXBLP )
      DOUBLE PRECISION      PMINOR ( 3, MAXBLP )
      DOUBLE PRECISION      PCENTR ( 3, MAXBLP )
      DOUBLE PRECISION      PCONST (    MAXBLP )


      DOUBLE PRECISION      ECLBOD ( 3 )
      DOUBLE PRECISION      CANBOD ( 3 ) 

      DOUBLE PRECISION      SRCBOD ( 3 )


C     !
C     ! Variables used by for construction of image segments
C     !

      DOUBLE PRECISION      COEFFX (    MXSEGS )
      DOUBLE PRECISION      COEFFY (    MXSEGS )

      DOUBLE PRECISION      BEGSUB ( 3, 4)
      DOUBLE PRECISION      ENDSUB ( 3, 4)

      DOUBLE PRECISION      BEGCAN ( 3 )
      DOUBLE PRECISION      ENDCAN ( 3 )

      DOUBLE PRECISION      BEGSEG ( 3, MXSEGS )
      DOUBLE PRECISION      ENDSEG ( 3, MXSEGS )


      DOUBLE PRECISION      VUSIDE
      LOGICAL               SAVSEG

C
C  Variables used by ENTRY EURING
C
      DOUBLE PRECISION      RCENTR ( 3 )  

      DOUBLE PRECISION      RMAJOR ( 3 ) 

      DOUBLE PRECISION      RMINOR ( 3 ) 

      DOUBLE PRECISION      LARGST 


      DOUBLE PRECISION      RINGD      

      DOUBLE PRECISION      NRINGD 

      DOUBLE PRECISION      FRINGD  


      DOUBLE PRECISION      OCCRNG ( 3 ) 

      DOUBLE PRECISION      ECLRNG ( 3 )  

      DOUBLE PRECISION      SRCRNG ( 3 ) 


C
C  Variables used by ENTRY EUSTAR
C

      DOUBLE PRECISION      STAR   ( 3 )
      DOUBLE PRECISION      STARAD
      DOUBLE PRECISION      SDTEST ( 3 )
C
C   Local variables
C
      INTEGER               I
      INTEGER               J
      INTEGER               K
      INTEGER               INTSEC

      DOUBLE PRECISION      A2
      DOUBLE PRECISION      AB
      DOUBLE PRECISION      B2
      DOUBLE PRECISION      C2
      DOUBLE PRECISION      DENOM
      DOUBLE PRECISION      FACTOR
      DOUBLE PRECISION      NEAR
      DOUBLE PRECISION      NUM

      DOUBLE PRECISION      VUPNT ( 3 ) 


      DOUBLE PRECISION      ANGLE
      DOUBLE PRECISION      BODYD
      DOUBLE PRECISION      NBODYD
      DOUBLE PRECISION      FBODYD


      SAVE
C
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
      ENTRY EUINIT
C
C   Establish all global constants.
C

      ANGLE              =  2.0D0 * PI / DFLOAT(STDSEG)
      STDCOS (STDSEG/4)  =  0.0D0
      STDSIN (STDSEG/4)  =  1.0D0

C
C  Compute the cosines and sines for the standard angles from PI/48
C  to PI/4.
C
      DO I = 1, (STDSEG/8)
         STDCOS(I) = DCOS ( DFLOAT(I) * ANGLE )
         STDSIN(I) = DSIN ( DFLOAT(I) * ANGLE )
      END DO

C
C  Obtain the next set of standard cosines and sines ( PI/4 to PI/2) by
C  reflection about the line y = x.
C
      DO I = (STDSEG/8) + 1,   (STDSEG/4) - 1
         STDSIN(I) = STDCOS ( (STDSEG/4) - I )
         STDCOS(I) = STDSIN ( (STDSEG/4) - I )
      END DO

C
C  Obtain the remaining cosines and sines by rotation
C
      J = 1

      DO I = (STDSEG/4) + 1, STDSEG
         STDCOS(I) = - STDSIN(J)
         STDSIN(I) =   STDCOS(J)
         J         = J + 1
      END DO

      KAXIS( 1 ) = 0.0
      KAXIS( 2 ) = 0.0
      KAXIS( 3 ) = 1.0

      COSFOV     = DCOS(LIMFOV)

      RETURN

C
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC

      ENTRY EUGEOM ( NLITES,   SOURCE, SRCRAD,
     .               OBSRVE,   CAMFRM,
     .               NBODS,    BODIES, AXES    )


C
C  Store all of the needed parameters
C
      NLIGHT = NLITES
      NBODY  = NBODS

      DO I = 1,NLIGHT
         RADII(I) = SRCRAD(I)
      END DO

      CALL VEQU ( OBSRVE,   OBSRVR           )
      CALL MOVED( CAMFRM,   9,        CAMERA )

C
C  Translate all objects to the camera centered frame.
C
      DO I = 1, NBODY
         CALL VSUB ( BODIES(1,I), OBSRVE, CENTRS(1,I) )
      END DO

      DO I = 1, NLIGHT
         CALL VSUB ( SOURCE(1,I), OBSRVE, LIGHTS (1,I) )
      END DO

C
C  Rotate all objects and axes to the camera frame.
C
      DO I = 1, NBODY
         CALL MTXV ( CAMFRM, CENTRS(1,I),  CENTRS(1,I)   )
         CALL MTXM ( CAMFRM, AXES(1,1,I),  PRNPLS(1,1,I) )
      END DO

      DO I = 1,NLIGHT
         CALL MTXV ( CAMFRM, LIGHTS(1,I),  LIGHTS(1,I)   )
      END DO

C
C  Get the lengths of the semi-major axes of each body.
C
      DO I = 1, NBODY
      

         A(1,I)    = VNORM( PRNPLS(1,1,I) )
         A(2,I)    = VNORM( PRNPLS(1,2,I) )
         A(3,I)    = VNORM( PRNPLS(1,3,I) )
         

         BIGA(I)   = MAX  ( A(1,I), A(2,I), A(3,I) )
         SMALLA(I) = MIN  ( A(1,I), A(2,I), A(3,I) )
         

      END DO

C
C  Compute the limb plane and ellipse for each body
C
      VUPNT(1) = 0
      VUPNT(2) = 0
      VUPNT(3) = 0

      DO I = 1, NBODY

         CALL ELLIPS  ( PRNPLS(1,1,I), PRNPLS(1,2,I), PRNPLS(1,3,I),
     .                  CENTRS(1,I),   VUPNT,
     .                  LNORML(1,I),   LMAJOR(1,I),   LMINOR(1,I),
     .                  LCENTR(1,I),   CANSEE(I)
     .                )

      END DO


C
C  Compute the terminator planeS, ellipseS, and eclipse coneS for each
C  body
C
      DO J = 1, NLIGHT
         DO I = 1, NBODY
         

            CALL ECLPMD   ( PRNPLS(1,1,I), 

     .                      PRNPLS(1,2,I), 

     .                      PRNPLS(1,3,I),
     .                      CENTRS(1,I), LIGHTS(1,J), 

     .                      SRCRAD(J),
     .                      TNORML(1,I,J), 

     .                      TMAJOR(1,I,J), 

     .                      TMINOR(1,I,J),
     .                      TCENTR(1,I,J), 

     .                      VERTEX(1,I,J),  ECAXIS(1,I,J),
     .                      CANECL(  I,J)
     .                    )
     

         END DO
      END DO

      RETURN
C
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC

      ENTRY EUVIEW ( DEVICE, HMIN, HMAX, VMIN, VMAX,
     .                       XMIN, XMAX, YMIN, YMAX )



C$ Abstract
C
C     Determines a vector and a disk centered about the end of that
C     vector which contains the field of view.  This pair describes
C     the decision cone.  If an object does not intersect the interior
C     of this cone it is not drawn.
C
C$ Keywords
C
C   GRAPHICS, GEOMETRY, ANGLE
C
C-

C
C      Compute the direction vectors that point to the corners of the 

C      Field of View.
C


      CORNER(1,1)    = -XMIN
      CORNER(2,1)    = -YMIN

      CORNER(1,2)    = -XMIN
      CORNER(2,2)    = -YMAX

      CORNER(1,3)    = -XMAX
      CORNER(2,3)    = -YMIN

      CORNER(1,4)    = -XMAX
      CORNER(2,4)    = -YMAX

      FOV (1)        = XMIN
      FOV (2)        = XMAX
      FOV (3)        = YMIN
      FOV (4)        = YMAX

      VIEW(1)        = HMIN
      VIEW(2)        = HMAX
      VIEW(3)        = VMIN
      VIEW(4)        = VMAX

      DO J = 1,4
         CORNER(3,J) = 1.0D0
      END DO

      DO J = 1,4
         CALL VHAT( CORNER(1,J), CORNER(1,J) )
      END DO

C
C     Unless an extreme geometry has been selected we will take the 

C     direction vector from the center of the FOV to be the axis
C     of the "decision" cone.  

C
      FOVCEN(1)  =  -0.5D0*( XMIN + XMAX )
      FOVCEN(2)  =  -0.5D0*( YMIN + YMAX )
      FOVCEN(3)  =   1.0D0

      CALL VHAT (FOVCEN, FOVCEN)
      

      MINCOS = 2.0D0      


C
C     Find the minimum cosine betweeen the current axis and the 

C     direction vectors to the corners of the FOV
C
      DO I = 1,4
         COSANG = VDOT( CORNER(1,I), FOVCEN )

         IF (COSANG .LT. MINCOS) THEN
            MINCOS = COSANG
         END IF

      END DO

C
C     If the minimum cosine is less than 0.001 we consider this
C     to be a case of extreme geometry.  We will simply take the
C     optical axis to be the axis of the "decision" cone.
C
      IF ( COSANG .LE. 0.001 ) THEN
         MINCOS = 2.0D0
         DO I = 1,4
            IF ( CORNER(3,I) .LT. MINCOS ) THEN
               MINCOS = CORNER(3,I)
            END IF
         END DO

         FOVCEN(1) = 0
         FOVCEN(2) = 0
         FOVCEN(3) = 1.0D0
      END IF

      FOVRAD = (DSQRT ( 1 - MINCOS*MINCOS )) / MINCOS
      DSPDEV = DEVICE
C
C     Initialize Escher.
C
      CALL ESVIEW( DEVICE, VIEW, FOV, ERROR )


      RETURN

C
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
C
C   Clear the current default area of the image device.
C
      ENTRY EUCLR ( DEVICE, HMIN, HMAX, VMIN, VMAX )

      REGION(1) = HMIN
      REGION(2) = HMAX
      REGION(3) = VMIN
      REGION(4) = VMAX

      CALL ESCLR ( DEVICE, REGION, ERROR )

      RETURN

C
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC

      ENTRY  EUBODY ( BODY, 

     .                MERIDS, 

     .                LATCIR, 

     .                SRCREQ,
     .                BRIGHT,
     .                DARK,
     .                TRMNTR )


C     

C     Is this an object we can actually see?
C     

      IF ( .NOT. CANSEE(BODY) ) THEN
         RETURN
      END IF
      

C
C     See if any of the candidate body lies within the FOV
C
      CALL OVRLAP ( LCENTR(1,BODY), BIGA(BODY),
     .              FOVCEN,         FOVRAD, INTSEC )

      IF ( INTSEC .EQ. 0 ) THEN
C
C        None of the body lies within the Field of View, bag this.
C
         RETURN
      END IF


C
C     Find the list of candidate occulting bodies
C

      OCCLTD = .FALSE.
      BODYD  = VNORM(CENTRS(1,BODY))
      FBODYD = BODYD + BIGA(BODY)
      NBODYD = BODYD - BIGA(BODY)

      I      = 0
      NOCAND = 0

      DO WHILE (     (I .LT. NBODY)
     .          .AND.( .NOT. OCCLTD) )
         I = I + 1
         

         IF ( I .NE. BODY .AND. CANSEE(I) ) THEN
C
C           First check to be sure that some portion of the candidate
C           body is closer to the OBSRVR than the farthest point
C           on the body to be drawn
C
            NEAR = VNORM(CENTRS(1,I)) - BIGA(I)

            IF ( NEAR .LT. FBODYD ) THEN
C
C           See if the envelope disks of these bodies (centered about
C           their limb midpoints) overlap
C
               CALL OVRLAP ( LCENTR(1,BODY), BIGA(BODY),
     .                       LCENTR(1,I   ), BIGA(I)    , INTSEC )

               IF ( INTSEC .GT. 1 ) THEN

                  NOCAND         = NOCAND + 1
                  OCANDS(NOCAND) = I

               ELSE IF ( INTSEC .EQ. 1 ) THEN
C
C              In this case the envelope disk of the body to be
C              drawn fell completely within the envelope disk of
C              the candidate body. It might be completely OCCLTD.
C              We put a new candidate envelope disk at the
C              center of the candidate body with radius equal to the
C              smallest axis of the candidate body.  If the envelope
C              disk of the body to be drawn still falls within
C              the new candidate disk, and the near point of body
C              to be drawn lies further than the center of the
C              candidate body, then it is entirely OCCLTD.

                  NOCAND         = NOCAND + 1
                  OCANDS(NOCAND) = I

                  IF ( VNORM(CENTRS(1,I)) .LT. NBODYD ) THEN

                     CALL OVRLAP ( LCENTR(1,BODY), BIGA(BODY),
     .                             CENTRS(1,I   ), SMALLA(I) , 

     .                             INTSEC                      )

                     OCCLTD = (INTSEC .EQ. 1)
                  END IF
               END IF
            END IF
         END IF
      END DO

C
C     If the body is OCCLTD there is nothing to draw. RETURN
C
      IF (OCCLTD) THEN 

         RETURN
      END IF

C
C     Determine whether or not some of this body might lie beyond the
C     global limit of the field of view from the optical axis.
C
      CALL OVRLAP ( LCENTR(1,BODY), BIGA(BODY),
     .              KAXIS,          DTAN(LIMFOV), INTSEC )

      NOVIEW = ( INTSEC .NE. 1 )

C
C     Determine the unit vectors pointing along the axes of the
C     equator of this body
C
      CALL VHAT ( PRNPLS(1,1,BODY), TEMPV1 )
      CALL VHAT ( PRNPLS(1,2,BODY), TEMPV2 )
      CALL VHAT ( PRNPLS(1,3,BODY), TEMPV3 )

C
C  Set up the array of planes (in body-centered coordinates)
C
C      The first plane will be the observed limb plane
C      The next NLIGHT planes will be the various terminator planes
C      The planes beginning with FPLANS + 1 will be "grid" planes.
C
C  First the limb.....


      PLANES        = 1
      FPLANS        = 1
      TSRCE(PLANES) = 0
      

      CALL VEQU (LNORML(1,BODY), PNORML(1,PLANES))
      CALL VEQU (LMAJOR(1,BODY), PMAJOR(1,PLANES))
      CALL VEQU (LMINOR(1,BODY), PMINOR(1,PLANES))
      CALL VEQU (LCENTR(1,BODY), PCENTR(1,PLANES))

C
C  Next the terminators
C
      DO LSRCE = 1,NLIGHT

C     

C        We have to check to make sure that this body can have
C        a terminator due to this light source.
C     

         IF ( CANECL(BODY,LSRCE) ) THEN

            PLANES        = PLANES  + 1
            FPLANS        = FPLANS + 1
            TSRCE(PLANES) = LSRCE
            

            CALL VEQU ( TNORML(1,BODY,LSRCE), PNORML(1,PLANES) )
            CALL VEQU ( TMAJOR(1,BODY,LSRCE), PMAJOR(1,PLANES) )
            CALL VEQU ( TMINOR(1,BODY,LSRCE), PMINOR(1,PLANES) )
            CALL VEQU ( TCENTR(1,BODY,LSRCE), PCENTR(1,PLANES) )
            

         END IF
         

      END DO


C
C  Compute the meridian planes and semi-major and -minor axes.
C
      IF ( MERIDS .GT. 0 ) THEN
C
C        Get the sin and cosine of the longitude of the first
C        meridian "east" of the prime meridian (these will be
C        used to algebraically compute sines and cosines
C        of succeeding longitudes
C           

         BASESN = DSIN( PI/DFLOAT(MERIDS) )
         BASECS = DCOS( PI/DFLOAT(MERIDS) )
C
C        COSANG and SINANG represent the sine and cosine of the
C        meridian "under construction"
C
         COSANG   = 1
         SINANG   = 0
C
C        Compute some of the constants needed for finding the
C        semi-major axis of a longitude ellipse:
C      

C           The length of the major axis of the meridian at angle
C           theta from the prime meridian is
C
C              SQRT{ a**2 b**2 / [(asin(theta))**2 + (bcos(theta))**2] }
C
C           where a is the length of the principle axis passing 

C           through the the prime meridian at the equator, and b is 

C           the length of the principle axis passing through the 90 

C           degree meridian at the equator.
C
C           Below we compute a**2, b**2, a**2*b**2, and the first 

C           denominator ( A2, B2, NUM, and DENOM respectively).
C
C
         A2       = A(1,BODY)*A(1,BODY)
         B2       = A(2,BODY)*A(2,BODY)

         NUM      = A2*B2

         DENOM    = A2*SINANG*SINANG + B2*COSANG*COSANG
C
C        Compute the normal to each meridian plane, the major and
C        minor axes, and the constant for each plane.
C
         DO I = 1,MERIDS
         

            PLANES        = PLANES + 1
            TSRCE(PLANES) = 0
            

            CALL VLCOM ( -SINANG, TEMPV1, 

     .                    COSANG, TEMPV2, PNORML(1,PLANES) )

            CALL VLCOM (  COSANG, TEMPV1, 

     .                    SINANG, TEMPV2, PMAJOR(1,PLANES) )


            T = DSQRT ( NUM/DENOM )
            

            CALL VSCL ( T, PMAJOR(1,PLANES), PMAJOR(1,PLANES) )

C
C           The minor axis of a longitude ellipse is always the 

C           3rd principle axis of the parent body
C
            CALL VEQU ( PRNPLS(1,3,BODY), PMINOR( 1, PLANES) )
            CALL VEQU ( CENTRS(1,  BODY), PCENTR( 1, PLANES) )
C
C           Compute the next longitude sine and cosine
C
            X      = COSANG
            Y      = SINANG
            SINANG = Y*BASECS  + X*BASESN
            COSANG = X*BASECS  - Y*BASESN
C
C           Get the next denominator for axis scaling
C
            DENOM  = A2*SINANG*SINANG + B2*COSANG*COSANG
         END DO
      END IF

C
C  Compute all "latitude" planes and semi-major and -minor axes
C
      IF (LATCIR .GT. 0 ) THEN
C
C        First: note that the normal to each latitude plane is the 

C        same namely PRNPLS(i,3,body) where i = 1,3 and body is the
C        body number.
C
C        Second: We define latitude to be the geodetic latitude of
C        the prime meridian
C
         BASESN =  DSIN( PI / DFLOAT( LATCIR + 1) )
         BASECS =  DCOS( PI / DFLOAT( LATCIR + 1) )

C
C        Use the identities COS(- pi/2 + theta ) =   SIN(theta) and
C                           SIN(- pi/2 + theta ) = - COS(theta) 

C        to obtain cosine and sine of the initial geodetic latitude
C        

         COSANG =  BASESN
         SINANG = -BASECS

C
C   Next establish constants that will be used repetitively
C
C        Recall that at a point (x,0,z) on the surface of the ellipsoid
C        given by :
C
C              (x/a)**2 + (y/b)**2 + (z/c)**2 = 1
C        

C        the normal vector is given by ( x/a**2, 0, z/c**2 ).
C
C        the tangent of the geodetic latitude at this point is given by
C
C        tan(L) = z*a**2 / x*c**2  

C
C               = (z*a**2)/c**2{a*sqrt[ 1 - (z/c)**2]}
C
C               = az / c [sqrt{c**2 - z**2}]
C
C         Solving this equation for z we find
C
C         z     = c**2 tan(L) / [sqrt{a**2 + (c tan(L))**2}]
C
C         Moreover for this value of z, we find that
C
C         x     = a**2 / [sqrt{a**2 + (c tan(L))**2}]
C
C         Finally, for this value of z, the value of y . 0 such that
C         the point (0,y,z) is on the ellipsoid (y . 0) is given by :
C
C         y     = a*b / [sqrt{a**2 + (c tan(L))**2}]
C
C         Below we compute a**2, a*b, c**2 (A2, AB, C2 respectively)
C

         A2      =  A(1,BODY)*A(1,BODY)
         C2      =  A(3,BODY)*A(3,BODY)
         AB      =  A(1,BODY)*A(2,BODY)

         DO I =  1, LATCIR
            PLANES        = PLANES + 1
            TSRCE(PLANES) = 0
            TANANG        = SINANG/COSANG
            NUM           = C2*TANANG
            FACTOR        = 1 / DSQRT( A2 + NUM*TANANG )
            Z             = NUM * FACTOR
            X             = A2  * FACTOR
            Y             = AB  * FACTOR
            

            CALL VSCL   ( X, TEMPV1,       PMAJOR(1, PLANES) )
            CALL VSCL   ( Y, TEMPV2,       PMINOR(1, PLANES) )
            CALL VSCL   ( Z, TEMPV3,       PCENTR(1, PLANES) )
            CALL VADD   ( CENTRS(1,BODY), PCENTR(1, PLANES),
     .                                     PCENTR(1, PLANES) )
            CALL VEQU   ( TEMPV3,          PNORML(1, PLANES) )

            X             = COSANG
            Y             = SINANG
            SINANG        = Y*BASECS  + X*BASESN
            COSANG        = X*BASECS  - Y*BASESN

         END DO
      END IF


C
C     compute all of the plane constants ( i.e. <CENTER, NORMAL> ).
C

      DO I = 1,PLANES
         PCONST(I) = VDOT( PCENTR(1,I), PNORML(1,I) )
      END DO

C
C     Find the list of candidate eclipsing bodies
C
C        We let NPSECL be the number of illumination sources that
C               may possibly be eclipsed
C
C        We let NDFECL be the number of illumination sources that
C               are definately eclipsed
C
C

      NPSECL = 0
      NDFECL = 0

      DO J = 1, NLIGHT
C
C        Get the vector from the center of the light source to
C        the body center
C
         CALL VSUB ( CENTRS(1,BODY), LIGHTS(1,J), SRCBOD )

         BODYD     = VNORM(SRCBOD)
         FBODYD    = BODYD + BIGA(BODY)
         NBODYD    = BODYD - BIGA(BODY)

         I         = 0
         NECAND(J) = 0
         ECLPSD(J) = .FALSE.
C
C        Search through all other bodies to find possible eclipsing
C        bodies for this light source.
C
         DO WHILE (      ( I .LT. NBODY   )
     .             .AND. ( .NOT. ECLPSD(J) ) )
            I = I + 1
            

C     

C           We are only interested in looking at bodies different
C           from the one we are trying to draw and that can actually
C           eclipse light source J.
C     

            IF ( I .NE. BODY .AND. CANECL(I,J) ) THEN

               CALL VSUB ( CENTRS(1,I), LIGHTS(1,J), CANBOD )
C
C              First see if some portion of the candidate eclipsing body
C              is closer to the light source than is the body we are 

C              trying to draw.
C
               IF ( VNORM(CANBOD) - BIGA(I) .LT. FBODYD ) THEN
C
C                 Next view the candidate body and current body from
C                 the vertex of the eclipse cone.  And see if the
C                 "envelope" disks overlap.
C
C                 For the envelope disk of the candidate body we
C                 take a disk with radius equal to the longest axis
C                 of the body and center it at the terminator center.
C
C                 For the envelope disk of the body under consideration,
C                 we choose a disk with radius equal to the largest
C                 axis of the body, and center it about the line
C                 of sight from the eclipse cone vertex to the body 

C                 in the plane where a limb would be viewed for a sphere
C                 of this radius centered about the body center.
C                 If such a sphere would contain the vertex we just 

C                 bag this and the candidate body will be regarded as
C                 a possible eclipsing body
C
                  CALL VSUB ( TCENTR(1,I,J),  VERTEX(1,I,J), CANBOD)
                  CALL VSUB ( CENTRS(1,BODY), VERTEX(1,I,J), ECLBOD )
C
C                 compute the scaling factor needed for centering the 

C                 envelope disk.
C
                  X = BIGA(BODY) / VNORM(ECLBOD)                  

                  X = 1 - X*X

                  IF ( X .LE. 0) THEN
                        NECAND(J)           = NECAND(J) + 1
                        ECANDS(NECAND(J),J) = I
                  ELSE
                     CALL VSCL   ( X, ECLBOD, ECLBOD )
                     CALL OVRLAP (    ECLBOD, BIGA(BODY),
     .                                CANBOD, BIGA(I),    INTSEC )

                     IF ( INTSEC .GT. 1 ) THEN
                        NECAND(J)           = NECAND(J) + 1
                        ECANDS(NECAND(J),J) = I

                     ELSE IF ( INTSEC .EQ. 1 ) THEN
C
C                       Check for total eclipse from this illumination
C                       source from this body
C
                        NECAND(J)           = NECAND(J) + 1
                        ECANDS(NECAND(J),J) = I
      

                        CALL VSUB ( CENTRS(1,I),  LIGHTS(1,J), 

     .                              CANBOD                     )

                        IF (     VNORM(CANBOD) + SMALLA(I) 

     .                      .LT. NBODYD ) THEN
   

                           CALL VSUB ( CENTRS(1,I),  VERTEX(1,I,J),
     .                                 CANBOD)

                           CALL OVRLAP ( ECLBOD, BIGA(BODY),
     .                                   CANBOD, SMALLA(I) , INTSEC )

                           ECLPSD(J) = (INTSEC .EQ. 1)
                        END IF
                     END IF
                  END IF
               END IF
            END IF
         END DO

C
C        Keep track of the number of illumination sources that are
C        possibly eclipsed and the number that are definitely eclipsed.
C
         IF (NECAND(J) .GT. 0) THEN
            NPSECL = NPSECL + 1
         END IF

         IF ( ECLPSD(J) ) THEN
            NDFECL = NDFECL + 1
         END IF

      END DO


C
C     Determine the segments to be drawn for every ellipse associated
C     with this body.
C

      CALL EUSKIP ( BIGA(BODY), CENTRS(1,BODY), FOVRAD, SKIP )
C
C     Set up the solution request array.
C
      DO J = 1, PLANES 

         SOLVE(J) = .TRUE.
      END DO

      ELLPSE  =  0
      

      DO WHILE ( ELLPSE .LT. PLANES)
         ELLPSE        = ELLPSE + 1

         SOLVE(ELLPSE) = .FALSE.

C
C        Find the collection of intersections of the "next ellipse"
C        with the limb,terminators, and "grid" ellipses.
C
         CALL PLPNTS ( PMAJOR(1,ELLPSE), 

     .                 PMINOR(1,ELLPSE),
     .                 PCENTR(1,ELLPSE),
     .                 PNORML,  PCONST,  PLANES, SOLVE,
     .                 COEFFX,  COEFFY,  MEETNS )
      


C
C        Modify the solution request array according to where we are
C        in the family of ellipses
C
         IF ( ELLPSE .LT. FPLANS ) THEN

C     

C           We are working with a terminator or limb ellipse.
C              

            SOLVE(ELLPSE)   = .TRUE.
            

         ELSE IF ( ELLPSE .EQ. FPLANS ) THEN
C     

C           We are working with the last terminator ellipse.
C           

            SOLVE(ELLPSE)   = .TRUE.

            DO I = ELLPSE+1, PLANES
               SOLVE(I)     = .FALSE.
            END DO
            

         ELSE
C         

C           We are working with a meridian/latitude ellipse
C           (the solution array does not need modification).
C            

         END IF

C
C        Order the intersection points.
C
         CALL ASORT ( COEFFX, COEFFY, MEETNS )
C
C        Prepare for merging of the endpoints and determination of 

C        occultation by the parent body.
C
         SEGNO  = 0
         NXTSTD = SKIP
         NXTAUX = 1
         
         CALL VADD (PMAJOR(1,ELLPSE), PCENTR(1,ELLPSE), BEGCAN)


C
C        Determine Occultations with the "parent" body
C
C           The parent body occults a segment if the viewer and the
C           the segment lie on different sides of the limb plane.
C           That is:
C
C              <cos(a)*MAJOR + sin(a)*MINOR + CENTER , NORMAL. - CONST
C
C           has a different sign from 

C
C               < VUPNT, NORMAL > - CONST.

         IF (ELLPSE .GT. 1) THEN
            VUSIDE  = - PCONST(1)
            X       = - PCONST(1) + VDOT(BEGCAN, PNORML)
            BEGVIS  =  .NOT. OPSGND (X,VUSIDE)
         ELSE
            BEGVIS  = .TRUE.
            ENDVIS  = .TRUE.
         END IF

C
C        Form the segments, one pair of endpoints at a time
C
         DO WHILE (      (NXTSTD .LE. STDSEG - 1)
     .             .AND. (NXTAUX  .LE. MEETNS ) )

C
C           First see if the current pair of candidate endpoints
C           are ordered
C
            IF ( ARDERD( STDCOS(NXTSTD), STDSIN(NXTSTD),
     .                   COEFFX  (NXTAUX) , COEFFY  (NXTAUX ) ) )
     .      THEN
               COSANG = STDCOS(NXTSTD)
               SINANG = STDSIN(NXTSTD)
               NXTSTD = NXTSTD + SKIP
            ELSE
               COSANG = COEFFX(NXTAUX)
               SINANG = COEFFY(NXTAUX)
               NXTAUX = NXTAUX + 1
            END IF

C
C           Compute the endpoint for this candidate segment.
C
            CALL VLCOM ( COSANG, PMAJOR(1,ELLPSE),
     .                    SINANG, PMINOR(1,ELLPSE), ENDCAN)

            CALL VADD (ENDCAN, PCENTR(1,ELLPSE), ENDCAN)

C
C           Determine if the endpoint is visible.
C
            IF (ELLPSE .GT. 1) THEN
               X      = VDOT( ENDCAN, LNORML(1,BODY)) 

     .                - PCONST(1)
               ENDVIS = .NOT. OPSGND(X,VUSIDE)
            END IF

            IF ( ENDVIS .AND. BEGVIS ) THEN
               SEGNO  = SEGNO + 1
               

               CALL VEQU ( BEGCAN, BEGSEG(1,SEGNO))
               CALL VEQU ( ENDCAN, ENDSEG(1,SEGNO))
               

            END IF

C
C           If this is a limb point we save it for use with landmarks,
C           and keep track of the number of such points.
C           

            IF (ELLPSE .EQ. 1) THEN
               LMBCOS( SEGNO ) = COSANG
               LMBSIN( SEGNO ) = SINANG
               LMBPTS          = LMBPTS + 1
            END IF

C
C           The current end candidate now becomes the next beginning
C           candidate.
C
            CALL VEQU ( ENDCAN, BEGCAN )
            BEGVIS = ENDVIS

         END DO

C
C        Now fill in the remaining segments
C

         MORESG = .TRUE.

         DO WHILE ( MORESG )
            IF ( NXTSTD .LE. STDSEG - 1 ) THEN
            

               COSANG = STDCOS(NXTSTD)
               SINANG = STDSIN(NXTSTD)
               NXTSTD = NXTSTD + SKIP
               

            ELSE IF ( NXTAUX .LE. MEETNS) THEN
            

               COSANG = COEFFX(NXTAUX)
               SINANG = COEFFY(NXTAUX)
               NXTAUX = NXTAUX + 1
               

            ELSE
            

               COSANG = 1
               SINANG = 0
               MORESG = .FALSE.
               

            END IF
C
C           Compute the endpoint for this candidate segment.
C
            CALL VLCOM ( COSANG, PMAJOR(1,ELLPSE),
     .                   SINANG, PMINOR(1,ELLPSE), ENDCAN)

            CALL VADD (ENDCAN, PCENTR(1,ELLPSE), ENDCAN)
C
C           Determine if the endpoint is visible.
C
            IF (ELLPSE .GT. 1) THEN
            

               X      = VDOT( ENDCAN, LNORML(1,BODY)) 

     .                - PCONST(1)
               ENDVIS = .NOT. OPSGND(X,VUSIDE)
               

            END IF

            IF ( ENDVIS .AND. BEGVIS ) THEN
            

               SEGNO      = SEGNO + 1
               CALL VEQU ( BEGCAN, BEGSEG(1,SEGNO))
               CALL VEQU ( ENDCAN, ENDSEG(1,SEGNO))
               

            END IF
C
C        The current end candidate now becomes the next beginning
C        candidate.
C
            CALL VEQU ( ENDCAN, BEGCAN )
            BEGVIS = ENDVIS
         END DO


         NUMSEG  = SEGNO


C
C        Determine which segments are OCCLTD by some other body.
C
         SEGNO  = 0
         SEGPTR = 0

         DO I = 1,3
            VUPNT(I) = 0.0D0
         END DO

         DO WHILE (SEGNO .LT. NUMSEG)
            SEGNO = SEGNO + 1
C
C           load the endpoints into the temporary points BEGCAN, _END
C
            CALL VEQU ( BEGSEG(1,SEGNO), BEGCAN)
            CALL VEQU ( ENDSEG(1,SEGNO), ENDCAN)

C
C           We begin by assuming this segment should be saved.
C
            SAVSEG = .TRUE.
C
C           Check candidate bodies for occultation for each body 

C           until occultation detected or all bodies have been checked.
C
            I          = 0
            DO WHILE ((I .LT. NOCAND) .AND. (SAVSEG))
               I = I + 1
               J = OCANDS(I)

               CALL PLELSG ( BEGCAN,       ENDCAN,
     .                       LNORML(1,J),  LMAJOR(1,J),
     .                       LMINOR(1,J),  LCENTR(1,J),
     .                       VUPNT,
     .                       BEGSUB(1,1),  ENDSUB(1,1),
     .                       INSIDE(1),    INBACK(1),
     .                       NSUBS                     )

               

C
C              find the first sub_segment not lying inside the ellipse
C              and not behind the candidate limb plane
C
               SUB       = 1
               DO WHILE (      INBACK(SUB)
     .                   .AND. INSIDE(SUB) 

     .                   .AND. (SUB .LE. NSUBS) )
                  SUB    = SUB + 1
               END DO

               IF ( SUB .LE. NSUBS) THEN
C
C                 This becomes the new test case.
C
                  CALL VEQU( BEGSUB(1,SUB), BEGCAN )
                  CALL VEQU( ENDSUB(1,SUB), ENDCAN )
                  SUB        = SUB + 1
                  

               ELSE
C
C              ...otherwise the current test segment has been
C                 OCCLTD. We drop the current test segment and
C                 the loop structure will pick out the next one.
C                     

                  SAVSEG = .FALSE.
                  

               END IF

               DO WHILE ( SUB .LE. NSUBS )
C
C                 Load any left over pieces onto the segment stack for
C                 checking later.
C
                  IF ( .NOT. (INBACK(SUB) .AND. INSIDE(SUB)) ) THEN
                  

                     NUMSEG = NUMSEG + 1
                     J      = NUMSEG 

                     

                     CALL VEQU( BEGSUB(1,SUB), BEGSEG(1,J) )
                     CALL VEQU( ENDSUB(1,SUB), ENDSEG(1,J) )
                     

                  END IF
                  

                  SUB = SUB + 1
                  

               END DO !WHILE ( SUB .LE. NSUBS )

            END DO !WHILE ((I .LT. NOCAND) .AND. (SAVSEG))
C
C           If a segment has passed this far, it is NOT OCCLTD. Load
C           it into the front end of the segment stack.
C
            IF ( SAVSEG ) THEN
            

               SEGPTR = SEGPTR + 1
               CALL VEQU ( BEGCAN, BEGSEG(1,SEGPTR) )
               CALL VEQU ( ENDCAN, ENDSEG(1,SEGPTR) )
               

            END IF
            

         END DO !WHILE (SEGNO .LT. NUMSEG)

         NUMSEG = SEGPTR

C
C        Determine which segments are in the shadow of the parent body
C

         SEGNO  = 0
         SEGPTR = 0

         DO WHILE ( SEGNO .LT. NUMSEG )
            

            SEGNO = SEGNO + 1

            CALL VEQU( BEGSEG(1,SEGNO), BEGCAN )
            CALL VEQU( ENDSEG(1,SEGNO), ENDCAN )

            NDARK  = 0
            NILLUM = 0
            DRKREQ = 1 + NLIGHT - SRCREQ


C           We check this candidate segment until
C                  1.) it is illuminated by the required number of 

C                      sources
C                  or 

C
C                  2.) it is dark for enough sources that it can't be 

C                      illuminated by the remaining sources.

            LS     =  0
            UNKNWN = (LS .LT. NLIGHT)

            DO WHILE ( UNKNWN )

               LS = LS + 1

C     

C              If this is NOT a terminator segment for the current
C              light source, we need to check to see if it
C              is dark with respect to the current light source.
C     

               IF ( TSRCE(ELLPSE) .NE. LS ) THEN 


                  IF (    SMSIDE( BEGCAN, ENDCAN,
     .                            TNORML (1,BODY,LS), 

     .                            TCENTR (1,BODY,LS), 

     .                            LIGHTS  (1,LS)      ) ) THEN
     

                     NILLUM = NILLUM + 1
                     

                  ELSE
                  

                     NDARK  = NDARK + 1
                     

                  END IF

               ELSE
C
C                 This is a terminator segment for the current light 

C                 source and is hence regarded as dark.
C
                  NDARK = NDARK + 1
                  

               END IF

               IF ( (ELLPSE .EQ. 1) .OR. (ELLPSE .GT. FPLANS ) )
     .         THEN
     

                  UNKNWN =      ( NILLUM .LT. SRCREQ  )
     .                     .AND.( NDARK   .LT. DRKREQ )  

               ELSE
               

                  UNKNWN =      ( NILLUM .LT. SRCREQ  )
     .                     .AND.( LS     .LT. NLIGHT  )

               END IF

            END DO !WHILE (  UNKNWN )


            IF (( ELLPSE .EQ. 1 ) .OR. (ELLPSE .GT. FPLANS) ) 

     .      THEN

C              If the current segment is not a terminator segment
C              we draw it if its dark
C              otherwise we load it onto the array of segments

               IF ( NDARK   .EQ. DRKREQ )  THEN

                  IF ( NOVIEW ) THEN
                  
                     CALL FOVCLP ( BEGCAN, ENDCAN, COSFOV       )
                     CALL ESDRAW ( BEGCAN, ENDCAN, DARK,  ERROR )
                     

                  ELSE
                  

                     CALL ESDRAW ( BEGCAN, ENDCAN, DARK, ERROR )
                     

                  END IF
                  

               ELSE
               

                  SEGPTR = SEGPTR + 1
                  

                  CALL VEQU( BEGCAN, BEGSEG(1,SEGPTR) )
                  CALL VEQU( ENDCAN, ENDSEG(1,SEGPTR) )
                  

               END IF
               

            ELSE

C
C              If the current segment is a terminator segment we
C              draw it only if it is a true boundary of illumination
C              otherwise we drop it from the list of segments to draw.
C              NOTE: since SEGPTR will never be incremented, it
C              will remain zero.  Thus there will be NO segments on the
C              list of segments to check for eclipse. The loop
C              of eclipse checks will not be executed for terminator 

C              segments.
C              

               IF (     ( NDARK   .EQ. DRKREQ   )  

     .             .AND.( NILLUM  .EQ. SRCREQ - 1) ) THEN

                  IF ( NOVIEW ) THEN
                  

                     CALL FOVCLP ( BEGCAN, ENDCAN, COSFOV        )
                     CALL ESDRAW ( BEGCAN, ENDCAN, TRMNTR, ERROR )
                     

                  ELSE
                  

                     CALL ESDRAW ( BEGCAN, ENDCAN, TRMNTR, ERROR )
                     

                  END IF
                  

               END IF
               

            END IF


         END DO ! WHILE ( SEGNO .LT. NUMSEG )


         NUMSEG = SEGPTR

C
C        Check remaining segments for eclipse.
C

C
C        If the entire body is eclipsed, ship out all segments in dark.
C 

         IF ( NDFECL .GE. DRKREQ ) THEN

            DO SEGNO = 1, NUMSEG

               IF ( NOVIEW ) THEN
                  CALL FOVCLP ( BEGSEG(1,SEGNO), 

     .                          ENDSEG(1,SEGNO), COSFOV )
                  CALL ESDRAW ( BEGSEG(1,SEGNO), 

     .                          ENDSEG(1,SEGNO) , DARK, ERROR )
               ELSE
                  CALL ESDRAW ( BEGSEG(1,SEGNO), 

     .                          ENDSEG(1,SEGNO) , DARK, ERROR )
               END IF
            END DO
            

            NUMSEG = 0
            

         END IF

C
C        If there is no possibility of eclipse, ship out all segments 

C        in bright.
C 

         IF ( NPSECL .EQ. 0 ) THEN
            DO SEGNO = 1, NUMSEG

               IF ( NOVIEW ) THEN
                  CALL FOVCLP ( BEGSEG(1,SEGNO), 

     .                          ENDSEG(1,SEGNO), COSFOV )
                  CALL ESDRAW ( BEGSEG(1,SEGNO), 

     .                          ENDSEG(1,SEGNO),
     .                          BRIGHT, ERROR )
               ELSE
                  CALL ESDRAW ( BEGSEG(1,SEGNO), 

     .                          ENDSEG(1,SEGNO),
     .                          BRIGHT, ERROR )
               END IF
            END DO
            

            NUMSEG = 0
            

         END IF
C
C        If the program reaches this point we check each segment for 

C        eclipse.
C

         SEGNO = 0

         DO WHILE ( SEGNO .LT. NUMSEG )

            SEGNO       = SEGNO + 1
C
C           Get the next segment.
C
            CALL VEQU ( BEGSEG(1,SEGNO), BEGCAN )
            CALL VEQU ( ENDSEG(1,SEGNO), ENDCAN )


C
C           Initialize counters and status for this segment
C
            LSRCE  = 0
            NILLUM = 0
            NDARK  = 0
            NOTECL = ( NDARK  .LT. DRKREQ )
            NOTLIT = ( NILLUM .LT. SRCREQ )

C
C           Examine each light source until one of the following occurs
C                  1.) all have been examined
C                  2.) we know of an eclipse
C                  3.) we know the segment is lit
C
            DO WHILE (      (LSRCE .LT. NLIGHT) 

     .                .AND. (     NOTECL      ) 

     .                .AND. (     NOTLIT      ) )

               LSRCE  = LSRCE + 1
               CURDRK = NDARK
               UNKNWN = .TRUE.



C              Check to see if this segment is eclipsed by the
C              "parent" body.
C              

               IF ( CANECL( BODY, LSRCE ) ) THEN 



                  IF ( .NOT. SMSIDE( BEGCAN, ENDCAN,
     .                               TNORML (1,BODY,LSRCE), 

     .                               TCENTR (1,BODY,LSRCE), 

     .                               LIGHTS  (1,     LSRCE)  ) ) 

     .            THEN
C   

C                    if the body is between the source and the segment 

C                    we increment our "darkness" counter
C   

                     NDARK  = NDARK + 1
                     UNKNWN = .FALSE.
                  END IF
                  

               END IF
C
C              For this light source we now examine all bodies that
C              have a chance of eclipsing this segment.  First 

C              initialize our counters and update status flags
C
               J      = 0
               NOTECL = ( NDARK  .LT. DRKREQ ) 

               NOTLIT = ( NILLUM .LT. SRCREQ )
               

               UNKNWN =       UNKNWN 

     .                  .AND. NOTECL 

     .                  .AND. NOTLIT 

     .                  .AND. (J .LT. NECAND(LSRCE))
C
C              We now examine each candidate eclipsing body until
C              we know our segment is eclipsed or all have been tested
C
               DO WHILE ( UNKNWN )
               

                  J = J + 1
                  K = ECANDS (J,LSRCE)               

                  

C
C                 Find out if the segment passes behind the terminator
C                 ellipse for this candidate body and source.
C

                  CALL PLELSG( BEGCAN,   ENDCAN,
     .                         TNORML(1,K,LSRCE),   

     .                         TMAJOR(1,K,LSRCE),   

     .                         TMINOR(1,K,LSRCE),
     .                         TCENTR(1,K,LSRCE),   

     .                         VERTEX(1,K,LSRCE),
     .                         BEGSUB(1,1),   ENDSUB(1,1),
     .                         INSIDE(1),     INBACK(1),
     .                         NSUBS              )

                  IF ( NSUBS .GT. 1 ) THEN
C
C                    If multiple crossings were determined, the 

C                    current segment becomes the first sub-segment 

C                    and the rest are loaded onto the segment list
C
                     CALL VEQU( BEGSUB(1,1), BEGCAN )
                     CALL VEQU( ENDSUB(1,1), ENDCAN )
                     DO SUB = 2,NSUBS
                        NUMSEG = NUMSEG + 1
                        I      = NUMSEG 

                        CALL VEQU( BEGSUB(1,SUB), BEGSEG(1,I) )
                        CALL VEQU( ENDSUB(1,SUB), ENDSEG(1,I) )
                     END DO
                  END IF

                  IF ( INSIDE(1) ) THEN
C
C                    if the segment lies in the ellipse of the
C                    terminator, find out if it is between the
C                    terminator plane and the light source.
C
                     IF ( .NOT.  SMSIDE( BEGCAN,     ENDCAN,
     .                                   TNORML(1, K, LSRCE), 

     .                                   TCENTR(1, K, LSRCE), 

     .                                   LIGHTS (1,    LSRCE)  )
     .                  ) THEN
C
C                       if it is increment our darkness counter
C                       and set darkness undecided to .FALSE.
C
                        NDARK  = NDARK + 1
                        UNKNWN = .FALSE.
                     END IF
                  END IF

                  UNKNWN = ((J .LT. NECAND(LSRCE))  

     .                                 .AND. UNKNWN     )
                  NOTECL = ( NDARK .LT. DRKREQ )

               END DO !WHILE ( UNKNWN )

               IF (CURDRK .EQ. NDARK ) THEN
                  NILLUM = NILLUM + 1
               END IF

               NOTLIT    = (NILLUM .LT. SRCREQ)

            END DO ! WHILE (      (LSRCE .LT. NLIGHT) 

C     .                     .AND. (     NOTECL     ) 

C     .                     .AND. (     NOTLIT          ) )


            IF ( NOTECL ) THEN
               IF ( NOVIEW ) THEN
                  CALL FOVCLP( BEGCAN, ENDCAN, COSFOV )
                  CALL ESDRAW ( BEGCAN, ENDCAN, BRIGHT, ERROR )
               ELSE   

                  CALL ESDRAW ( BEGCAN, ENDCAN, BRIGHT, ERROR )
               END IF

            ELSE

               IF ( NOVIEW ) THEN
                  CALL FOVCLP( BEGCAN, ENDCAN, COSFOV )
                  CALL ESDRAW ( BEGCAN, ENDCAN, BRIGHT, ERROR )
               ELSE   

                  CALL ESDRAW ( BEGCAN, ENDCAN, DARK,   ERROR )
               END IF
            END IF

          END DO ! WHILE (SEGNO .LT. NUMSEG)

      END DO


C
C   clear the segment buffer of Escher
C

      CALL ESDUMP ( ERROR )
      RETURN


C
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC

      ENTRY EURING ( RING,
     .               MAJOR, 

     .               MINOR, 

     .               SRCREQ,
     .               BRIGHT,
     .               DARK      )

C
C   Translate the ring center to the OBSRVR centered frame.
C
      CALL VSUB( RING, OBSRVR, RCENTR)

C
C   Rotate everything into the OBSRVR centered frame.
C
      CALL MTXV ( CAMERA, RCENTR, RCENTR)
      CALL MTXV ( CAMERA, MAJOR,   RMAJOR)
      CALL MTXV ( CAMERA, MINOR,   RMINOR)

C
C     See if any of the ring lies within the FOV
C
      LARGST = VNORM(RMAJOR)

      CALL OVRLAP ( RCENTR, LARGST,
     .              FOVCEN, FOVRAD, INTSEC )

      IF ( INTSEC .EQ. 0 ) THEN
C
C        None of the ring lies within the Field of View, bag this.
C
         RETURN
      END IF

C
C     Find the list of candidate occulting bodies
C

      OCCLTD = .FALSE.
      RINGD  = VNORM(RCENTR)
      FRINGD = RINGD + LARGST
      NRINGD = RINGD - LARGST

      I      = 0
      NOCAND = 0
      

C
C     For the envelope disk of the ring under consideration,
C     we choose a disk with radius equal to the largest
C     axis of the ring and center it about the line
C     of sight from the OBSRVR to the ring center
C     in the plane where a limb would be viewed for a sphere
C     of this radius centered about the ring center.
C     If such a sphere would contain the OBSRVR we just 

C     bag this and the candidate body will be regarded as
C     a possible occulting body
C
C     compute the scaling factor needed for centering the 

C     envelope disk.
C
      X = LARGST / VNORM(RCENTR)                  

      X = 1 - X*X

      CALL VSCL   ( X,    RCENTR,   OCCRNG )


      DO WHILE (     (I .LT. NBODY)
     .          .AND.( .NOT. OCCLTD) )
         I   = I + 1
C
C        First check to be sure that some portion of the candidate
C        body is closer to the OBSRVR than the farthest point
C        on the ring to be drawn
C
         NEAR = VNORM(CENTRS(1,I)) - BIGA(I)
         

         IF (         CANSEE(I) 

     .        .AND. ( NEAR .LT. FRINGD ) ) 

     .   THEN
C
C           See if the envelope disks of these bodies (centered about
C           their limb midpoints) overlap
C

            IF ( X .LE. 0) THEN
               NOCAND         = NOCAND + 1
               OCANDS(NOCAND) = I
            ELSE

               CALL OVRLAP ( OCCRNG,        LARGST,
     .                       LCENTR(1,I   ), BIGA(I)    , INTSEC )

               IF ( INTSEC .GT. 1 ) THEN

                  NOCAND         = NOCAND + 1
                  OCANDS(NOCAND) = I

               ELSE IF ( INTSEC .EQ. 1 ) THEN
C
C              In this case the envelope disk of the ring to be
C              drawn fell completely within the envelope disk of
C              the candidate body. It might be completely OCCLTD.
C              We put a new candidate envelope disk at the
C              center of the candidate body with radius equal to the
C              smallest axis of the candidate body.  If the envelope
C              disk of the ring to be drawn still falls within
C              the new candidate disk, and the near point of ring 

C              to be drawn lies further than the center of the
C              candidate body, then it is entirely OCCLTD.

                  NOCAND         = NOCAND + 1
                  OCANDS(NOCAND) = I

                  IF ( VNORM(CENTRS(1,I)) + SMALLA(I) .LT. 

     .                 NRINGD ) THEN

                     CALL OVRLAP ( OCCRNG,        LARGST, 

     .                             CENTRS(1,I   ), SMALLA(I) , 

     .                             INTSEC                      )

                     OCCLTD = (INTSEC .EQ. 1)
                  END IF
               END IF
            END IF
         END IF
      END DO

C
C     If the ring is OCCLTD there is nothing to draw. RETURN
C
      IF (OCCLTD) THEN 

         RETURN
      END IF

C
C     Determine whether or not some of this ring might lie beyond the
C     global limit of the field of view from the optical axis.
C
      IF ( X .LT. 0 ) THEN 

         NOVIEW = .TRUE.
      ELSE
         CALL OVRLAP ( RCENTR,      LARGST,
     .                 KAXIS,      DTAN(LIMFOV), INTSEC )

         NOVIEW = ( INTSEC .NE. 1 )
      END IF
C
C     Find the list of candidate eclipsing bodies
C
C        We let NPSECL be the number of illumination sources that
C               may possibly be eclipsed
C
C        We let NDFECL be the number of illumination sources that
C               are definately eclipsed
C
C

      NPSECL = 0
      NDFECL = 0

      DO J = 1, NLIGHT
C
C        Get the vector from the center of the light source to
C        the ring center
C
         CALL VSUB ( RCENTR, LIGHTS(1,J), SRCRNG )

         RINGD     = VNORM(SRCRNG)
         FRINGD    = RINGD + LARGST
         NRINGD    = RINGD - LARGST

         I         = 0
         NECAND(J) = 0
         ECLPSD(J) = .FALSE.
C
C        Search through all bodies to find possible eclipsing
C        bodies for this light source.
C
         DO WHILE (      ( I .LT. NBODY   )
     .             .AND. ( .NOT. ECLPSD(J) ) )
            I = I + 1

            CALL VSUB ( CENTRS(1,I), LIGHTS(1,J), CANBOD )
C
C           

C           See if this body can eclipse this light source.  

C           and if so is some portion of the candidate eclipsing body
C           closer to the light source than is the ring we are 

C           trying to draw ?
C
            IF (         CANECL(I,J) 

     .           .AND. ( VNORM(CANBOD) - BIGA(I) .LT. FRINGD ))
     .      THEN
     

C
C              Next view the candidate body and ring from
C              the vertex of the eclipse cone.  And see if the
C              "envelope" disks overlap.
C
C              For the envelope disk of the candidate body we
C              take a disk with radius equal to the longest axis
C              of the body and center it at the terminator center.
C
C              For the envelope disk of the ring under consideration,
C              we choose a disk with radius equal to the largest
C              axis of the ring and center it about the line
C              of sight from the eclipse cone vertex to the ring
C              in the plane where a limb would be viewed for a sphere
C              of this radius centered about the ring center.
C              If such a sphere would contain the vertex we just 

C              bag this and the candidate body will be regarded as
C              a possible eclipsing body
C
               CALL VSUB ( TCENTR(1,I,J),  VERTEX(1,I,J), CANBOD)
               CALL VSUB ( RCENTR,         VERTEX(1,I,J), ECLRNG )
C
C              compute the scaling factor needed for centering the 

C              envelope disk.
C
               X = LARGST / VNORM(ECLRNG)                  

               X = 1 - X*X

               IF ( X .LE. 0) THEN
                  NECAND(J)           = NECAND(J) + 1
                  ECANDS(NECAND(J),J) = I
               ELSE
                  CALL VSCL   ( X, ECLRNG,       ECLRNG )
                  CALL OVRLAP ( ECLRNG,          LARGST,
     .                          CANBOD,         BIGA(I),  INTSEC )

                  IF ( INTSEC .GT. 1 ) THEN
                     NECAND(J)           = NECAND(J) + 1
                     ECANDS(NECAND(J),J) = I

                  ELSE IF ( INTSEC .EQ. 1 ) THEN
C
C                    Check for total eclipse from this illumination
C                    source from this body
C
                     NECAND(J)           = NECAND(J) + 1
                     ECANDS(NECAND(J),J) = I
      

                     CALL VSUB ( CENTRS(1,I),  LIGHTS(1,J), 

     .                           CANBOD                     )

                     IF (     VNORM(CANBOD) + SMALLA(I) 

     .                   .LT. NRINGD ) THEN
   

                        CALL VSUB ( CENTRS(1,I),  VERTEX(1,I,J),
     .                              CANBOD)

                        CALL OVRLAP ( ECLRNG,  LARGST, 

     .                                CANBOD, SMALLA(I) , INTSEC )

                        ECLPSD(J) = (INTSEC .EQ. 1)
                     END IF
                  END IF
               END IF
            END IF
         END DO

C
C        Keep track of the number of illumination sources that are
C        possibly eclipsed and the number that are definitely eclipsed.
C
         IF (NECAND(J) .GT. 0) THEN
            NPSECL = NPSECL + 1
         END IF

         IF ( ECLPSD(J) ) THEN
            NDFECL = NDFECL + 1
         END IF

      END DO

C
C     Determine the segments to be drawn for this ring.
C
      CALL EUSKIP ( LARGST, RCENTR, FOVRAD, SKIP )

      CALL VADD ( RCENTR, RMAJOR, BEGSEG(1,1) )

      SEGNO  = 0
      NXTSTD = SKIP
      

      DO WHILE (NXTSTD .LT. STDSEG)
      

         SEGNO  = SEGNO + 1
         COSANG = STDCOS(NXTSTD)
         SINANG = STDSIN(NXTSTD)
         

         CALL VLCOM ( COSANG, RMAJOR, SINANG, RMINOR, 

     .                ENDSEG(1,SEGNO)                 )

         CALL VADD   ( RCENTR, ENDSEG(1,SEGNO),
     .                          ENDSEG(1,SEGNO) )

         CALL VEQU   ( ENDSEG(1,SEGNO), BEGSEG(1,SEGNO + 1 ) )
         

         NXTSTD = NXTSTD + SKIP
         

      END DO

      SEGNO = SEGNO + 1

      CALL VADD ( RCENTR, RMAJOR, ENDSEG(1,SEGNO) )
      NUMSEG  = SEGNO
C
C  Determine which segments are OCCLTD by some body.
C
      SEGNO  = 0
      SEGPTR = 0

      DO I = 1,3
         VUPNT(I) = 0
      END DO

      DO WHILE (SEGNO .LT. NUMSEG)
         SEGNO = SEGNO + 1
C
C        load the endpoints into the temporary points BEGCAN, _END
C
         CALL VEQU ( BEGSEG(1,SEGNO), BEGCAN)
         CALL VEQU ( ENDSEG(1,SEGNO), ENDCAN)

C
C        We begin by assuming this segment should be saved.
C
         SAVSEG = .TRUE.
C
C        Check candidate bodies for occultation for each body 

C        until occultation detected or all bodies have been checked.
C
         I      = 0
         DO WHILE ((I .LT. NOCAND) .AND. (SAVSEG))
            I = I + 1
            J = OCANDS(I)

            CALL PLELSG ( BEGCAN,            ENDCAN,
     .                    LNORML  (1,J),      LMAJOR  (1,J),
     .                    LMINOR(1,J),        LCENTR  (1,J),
     .                    VUPNT,
     .                    BEGSUB  (1,1),      ENDSUB(1,1),
     .                    INSIDE(1),        INBACK(1),
     .                    NSUBS              )

               

C
C           find the first sub_segment not lying inside the ellipse
C           and not behind the candidate limb plane
C
            SUB    = 1
            DO WHILE (      INBACK(SUB)
     .                .AND. INSIDE(SUB) 

     .                .AND. (SUB .LE. NSUBS) )
               SUB = SUB + 1
            END DO

            IF ( SUB .LE. NSUBS) THEN
C
C              This becomes the new test case.
C
               CALL VEQU( BEGSUB(1,SUB), BEGCAN )
               CALL VEQU( ENDSUB(1,SUB), ENDCAN )
               SUB = SUB + 1
            ELSE
C
C           ...otherwise the current test segment has been
C              OCCLTD. We drop the current test segment and
C              the loop structure will pick out the next one.
C                  

               SAVSEG = .FALSE.
            END IF

            DO WHILE ( SUB .LE. NSUBS )
C
C              Load any left over pieces onto the segment stack for
C              checking later.
C
               IF ( .NOT. (INBACK(SUB) .AND. INSIDE(SUB)) ) THEN
                  NUMSEG = NUMSEG + 1
                  J                  = NUMSEG 

                  CALL VEQU( BEGSUB(1,SUB), BEGSEG(1,J) )
                  CALL VEQU( ENDSUB(1,SUB), ENDSEG(1,J) )
               END IF
               SUB = SUB + 1
            END DO !WHILE ( SUB .LE. NSUBS )

         END DO !WHILE ((I .LT. NOCAND) .AND. (SAVSEG))
C
C        If a segment has passed this far, it is NOT OCCLTD. Load
C        it into the front end of the segment stack.
C
         IF ( SAVSEG ) THEN
            SEGPTR = SEGPTR + 1
            CALL VEQU ( BEGCAN, BEGSEG(1,SEGPTR) )
            CALL VEQU ( ENDCAN, ENDSEG(1,SEGPTR) )
         END IF
      END DO !WHILE (SEGNO .LT. NUMSEG)

      NUMSEG = SEGPTR

C
C  Check segments for eclipse.
C

C
C     If the entire ring is eclipsed, ship out all segments in dark.
C 

      IF ( NDFECL .GE. DRKREQ ) THEN

         DO SEGNO = 1, NUMSEG

            IF ( NOVIEW ) THEN
               CALL FOVCLP ( BEGSEG(1,SEGNO), 

     .                       ENDSEG(1,SEGNO), COSFOV )
               CALL ESDRAW ( BEGSEG(1,SEGNO), 

     .                       ENDSEG(1,SEGNO) , DARK, ERROR )
            ELSE
               CALL ESDRAW ( BEGSEG(1,SEGNO), 

     .                       ENDSEG(1,SEGNO) , DARK, ERROR )
            END IF
         END DO
         

         NUMSEG = 0
         

      END IF

C
C     If there is no possibility of eclipse, ship out all segments 

C     in bright.
C 

      IF ( NPSECL .EQ. 0 ) THEN
      

         DO SEGNO = 1, NUMSEG

            IF ( NOVIEW ) THEN
               CALL FOVCLP ( BEGSEG(1,SEGNO), 

     .                       ENDSEG(1,SEGNO), COSFOV )
               CALL ESDRAW ( BEGSEG(1,SEGNO), 

     .                       ENDSEG(1,SEGNO),
     .                       BRIGHT, ERROR )
            ELSE
               CALL ESDRAW ( BEGSEG(1,SEGNO), 

     .                       ENDSEG(1,SEGNO),
     .                       BRIGHT, ERROR )
            END IF
         END DO
         

         NUMSEG = 0
         

      END IF
C
C     If the program reaches this point we check each segment for 

C     eclipse.
C

      SEGNO = 0

      DO WHILE ( SEGNO .LT. NUMSEG )

         SEGNO = SEGNO + 1

C
C        Get the next segment.
C
         CALL VEQU ( BEGSEG(1,SEGNO), BEGCAN )
         CALL VEQU ( ENDSEG(1,SEGNO), ENDCAN )


C
C        Initialize counters and status for this segment
C
         LSRCE  = 0
         NILLUM = 0
         NDARK  = 0
         NOTECL = ( NDARK  .LT. DRKREQ )
         NOTLIT = ( NILLUM .LT. SRCREQ )

C
C        Examine each light source until one of the following occurs
C            1.) all have been examined
C            2.) we know of an eclipse
C            3.) we know the segment is lit
C
         DO WHILE (      ( LSRCE .LT. NLIGHT) 

     .             .AND. (      NOTECL      ) 

     .             .AND. (      NOTLIT      ) )

            LSRCE  = LSRCE + 1
            CURDRK = NDARK
            UNKNWN = .TRUE.

C
C           For this light source we now examine all bodies that
C           have a chance of eclipsing this segment.  First 

C           initialize our counters and update status flags
C
            J      = 0
            NOTECL = ( NDARK  .LT. DRKREQ ) 

            NOTLIT = ( NILLUM .LT. SRCREQ )
            

            UNKNWN =       UNKNWN 

     .               .AND. NOTECL 

     .               .AND. NOTLIT 

     .               .AND. (J .LT. NECAND(LSRCE))
C
C           We now examine each candidate eclipsing body until
C           we know our segment is eclipsed or all have been tested
C
            DO WHILE ( UNKNWN )
               J = J + 1
               K = ECANDS (J,LSRCE)               

                  

C
C              Find out if the segment passes behind the terminator
C              ellipse for this candidate body and source.
C

               CALL PLELSG( BEGCAN,         ENDCAN,
     .                      TNORML  (1,K,LSRCE),   

     .                      TMAJOR  (1,K,LSRCE),   

     .                      TMINOR  (1,K,LSRCE),
     .                      TCENTR  (1,K,LSRCE),   

     .                      VERTEX(1,K,LSRCE),
     .                      BEGSUB  (1,1),   ENDSUB(1,1),
     .                      INSIDE(1),     INBACK(1),
     .                      NSUBS              )

               IF ( NSUBS .GT. 1 ) THEN
C
C                 If multiple crossings were determined, the 

C                 current segment becomes the first sub-segment 

C                 and the rest are loaded onto the segment list
C
                  CALL VEQU( BEGSUB(1,1), BEGCAN )
                  CALL VEQU( ENDSUB(1,1), ENDCAN )
                  

                  DO SUB = 2,NSUBS
                     NUMSEG = NUMSEG + 1
                     I      = NUMSEG 

                     CALL VEQU( BEGSUB(1,SUB), BEGSEG(1,I) )
                     CALL VEQU( ENDSUB(1,SUB), ENDSEG(1,I) )
                  END DO
               END IF

               IF ( INSIDE(1) ) THEN
C
C                 if the segment lies in the ellipse of the
C                 terminator, find out if it is between the
C                 terminator plane and the light source.
C
                  IF ( .NOT.  SMSIDE( BEGCAN,     ENDCAN,
     .                                TNORML(1, K, LSRCE), 

     .                                TCENTR(1, K, LSRCE), 

     .                                LIGHTS (1,    LSRCE)  )
     .               ) THEN
C
C                    if it is increment our darkness counter
C                    and set darkness undecided to .FALSE.
C
                     NDARK  = NDARK + 1
                     UNKNWN = .FALSE.
                  END IF
               END IF

               UNKNWN = ((J .LT. NECAND(LSRCE))  

     .                              .AND. UNKNWN     )
               NOTECL       = ( NDARK .LT. DRKREQ )

            END DO !WHILE ( UNKNWN )

            IF (CURDRK .EQ. NDARK ) THEN
               NILLUM = NILLUM + 1
            END IF

            NOTLIT    = (NILLUM .LT. SRCREQ)

         END DO ! WHILE (      (LSRCE .LT. NLIGHT) 

C     .                  .AND. (     NOTECL      ) 

C     .                  .AND. (     NOTLIT      ) )


         IF ( NOTECL ) THEN
         

            IF ( NOVIEW ) THEN
               CALL FOVCLP ( BEGCAN, ENDCAN, COSFOV        )
               CALL ESDRAW ( BEGCAN, ENDCAN, BRIGHT, ERROR )
            ELSE   

               CALL ESDRAW ( BEGCAN, ENDCAN, BRIGHT, ERROR )
            END IF

         ELSE

            IF ( NOVIEW ) THEN
               CALL FOVCLP ( BEGCAN, ENDCAN, COSFOV        )
               CALL ESDRAW ( BEGCAN, ENDCAN, BRIGHT, ERROR )
            ELSE   

               CALL ESDRAW ( BEGCAN, ENDCAN, DARK, ERROR   )
            END IF
         END IF

      END DO ! WHILE (SEGNO .LT. NUMSEG)

C
C   clear the segment buffer of Escher
C

      CALL ESDUMP ( ERROR )

      RETURN

C
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC

      ENTRY EUTEMP ( XBEGIN,
     .               YBEGIN,
     .               XEND,
     .               YEND,
     .               NSEGS,
     .               COLOR     )

C
C   Make the Z-component of of each end point of each segment 1.
C   Then send everything to ESCHER for drawing.  

C
      DO I = 1,NSEGS

         BEGCAN(1) = -XBEGIN(I)
         BEGCAN(2) = -YBEGIN(I)
         BEGCAN(3) = 1.0D0

         ENDCAN(1) = -XEND(I)
         ENDCAN(2) = -YEND(I)
         ENDCAN(3) = 1.0D0

         CALL ESDRAW ( BEGCAN, ENDCAN, COLOR, ERROR   )

      END DO

      CALL ESDUMP ( ERROR )

      RETURN


C
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
      ENTRY EULAND ( BODY, 

     .               NSEGS,
     .               SEGBEG,
     .               SEGEND,
     .               BRIGHT,
     .               DARK )

C
C     

C
      RETURN




C
CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC
      ENTRY EUSTAR ( STRPOS, 

     .               NSTARS, 

     .               FONT, 

     .               FNTSIZ, 

     .               FNTSCL,
     .               COLOR )


      DO I = 1, NSTARS
C
C        First let's rotate the stellar position to the camera frame.
C
         CALL MTXV ( CAMERA, STRPOS(1,I),  STAR )
C
C        Create the collection of segments needed for drawing the star.
C
         CALL ESSTAR ( STAR,  

     .                 FONT,   FNTSIZ, FNTSCL,
     .                 BEGSEG, ENDSEG           )


         NUMSEG = FNTSIZ

C
C        Determine the "apparent radius" of the star 

C
         STARAD = 0

         DO J = 1, NUMSEG
         

            CALL VSUB  ( STAR, BEGSEG(1,J), TEMPV1 )
            CALL VSUB  ( STAR, ENDSEG(1,J), TEMPV2 )

            STARAD = MAX ( STARAD, VNORM(TEMPV1), VNORM(TEMPV2)  )
         END DO

C
C        See if the star lies within the FOV
C
         CALL OVRLAP ( STAR,   STARAD, 

     .                 FOVCEN, FOVRAD,  INTSEC )

         IF ( INTSEC .EQ. 0 ) THEN
C
C           None of the star lies within the Field of View, bag this.
C
            OCCLTD = .TRUE. 

         ELSE

            OCCLTD = .FALSE.
         END IF

C
C        Find the list of candidate occulting bodies
C

         J      = 0
         NOCAND = 0

         DO WHILE (     (J .LT.  NBODY)
     .             .AND.(  .NOT. OCCLTD) )

            J = J + 1
            

C     

C           We examine this body only if it can be seen.
C     

            IF ( CANSEE(J) ) THEN
            

C
C              See if the envelope disks of these bodies (centered about
C              their limb midpoints) overlap
C   

               CALL OVRLAP ( STAR,        STARAD,   

     .                       LCENTR(1,J), BIGA(J), INTSEC )
               

               CALL VSUB   ( STAR,        LCENTR(1,J),  SDTEST  )
               CALL VHAT   ( SDTEST,                    SDTEST  )
C     

C              First we take care that this point does not lie between
C              the OBSRVR and limb plane of the body.
C                    

               IF ( VDOT ( SDTEST, LNORML(1,J) ) .GT. 0 ) THEN
               

C     

C                 Do nothing, the object lies in front of the limb
C                 plane of this body, we will assume it is not
C                 inside the body.
C     

   

               ELSE IF ( INTSEC .GT. 1 ) THEN
   

                  NOCAND         = NOCAND + 1
                  OCANDS(NOCAND) = J
   

               ELSE IF ( INTSEC .EQ. 1 ) THEN
C   

C                 In this case the envelope disk of the star to be
C                 drawn fell completely within the envelope disk of
C                 the candidate body. It might be completely OCCLTD.
C                 See if the star lies within the limb of this candidate
C                 occulting body.
C   

   

                  NOCAND         = NOCAND + 1
                  OCANDS(NOCAND) = J
   

   

                  CALL PLNRAY ( LCENTR(1,J), LNORML(1,J), 

     .                          STAR,        INTSEC,
     .                          TEMPV1                     )
   

   

                  CALL VSUB   ( TEMPV1,    LCENTR(1,J),  TEMPV1 )
   

                  A2 = VDOT ( LMAJOR(1,J), LMAJOR(1,J) )
                  B2 = VDOT ( LMINOR(1,J), LMINOR(1,J) )
   

                  X  = VDOT ( TEMPV1,      LMAJOR(1,J) )
                  Y  = VDOT ( TEMPV1,      LMINOR(1,J) )
   

                  X  = X/A2
                  Y  = Y/B2
   

                  OCCLTD = ( X*X + Y*Y .LE. 1 )
   

               END IF
            END IF
            

         END DO


C
C        If the star is OCCLTD there is nothing to draw. Just drop
C        thru to the bottom of the outer loop.
C
         IF ( .NOT. OCCLTD) THEN 


C
C           Determine which segments are OCCLTD by some other body.
C
            SEGNO    = 0

            DO K = 1,3
               VUPNT(K) = 0
            END DO

            DO WHILE (SEGNO .LT. NUMSEG)
               SEGNO = SEGNO + 1
C
C              load the endpoints into the temporary points BEGCAN
C              ENDCAN
C
               CALL VEQU ( BEGSEG(1,SEGNO), BEGCAN)
               CALL VEQU ( ENDSEG(1,SEGNO), ENDCAN)

C
C              We begin by assuming this segment should be saved.
C
               SAVSEG = .TRUE.

C
C              Check candidate bodies for occultation for each body 

C              until occultation detected or all bodies have been checked.
C
               K = 0

               DO WHILE ((K .LT. NOCAND) .AND. (SAVSEG))
                  K = K + 1
                  J = OCANDS(K)

                  CALL PLELSG ( BEGCAN,           ENDCAN,
     .                          LNORML(1,J),      LMAJOR(1,J),
     .                          LMINOR(1,J),      LCENTR(1,J),
     .                          VUPNT,
     .                          BEGSUB(1,1),      ENDSUB(1,1),
     .                          INSIDE(1),        INBACK(1),
     .                          NSUBS              )


C
C                 find the first sub_segment not lying inside the 

C                 ellipse and not behind the candidate limb plane
C
                  SUB = 1
                  

                  DO WHILE (       INBACK    (SUB)
     .                      .AND.  INSIDE (SUB) 

     .                      .AND. (SUB .LE. NSUBS) )
                     SUB    = SUB + 1
                  END DO

                  IF ( SUB .LE. NSUBS) THEN
C
C                    This becomes the new test case.
C
                     CALL VEQU( BEGSUB(1,SUB), BEGCAN )
                     CALL VEQU( ENDSUB(1,SUB), ENDCAN )

                     SUB   = SUB + 1

                  ELSE
C
C                 ...otherwise the current test segment has been
C                    OCCLTD. We drop the current test segment and
C                    the loop structure will pick out the next one.
C                     

                     SAVSEG = .FALSE.

                  END IF

                  DO WHILE ( SUB .LE. NSUBS )
C
C                    Load any left over pieces onto the segment stack 

C                    for checking later.
C
                     IF ( .NOT. (INBACK(SUB) .AND. INSIDE(SUB)) ) 

     .               THEN

                        NUMSEG = NUMSEG + 1
                        J      = NUMSEG 

                        CALL VEQU( BEGSUB(1,SUB), BEGSEG(1,J) )
                        CALL VEQU( ENDSUB(1,SUB), ENDSEG(1,J) )

                     END IF

                     SUB = SUB + 1

                  END DO !WHILE ( SUB .LE. NSUBS )

               END DO !WHILE ((K .LT. NOCAND) .AND. (SAVSEG))
C
C              If a segment has passed this far, it is NOT OCCLTD. 

C              Since this is a star it cannot be in the shadow of 

C              anything.  Send it to ESCHER for drawing.
C   

               IF ( SAVSEG ) THEN

                  CALL ESDRAW ( BEGCAN, ENDCAN, COLOR, ERROR )

               END IF

            END DO !WHILE (SEGNO .LT. NUMSEG)


         END IF 

C
C               ! ( .NOT. OCCLTD )
C        


      END DO

C
C   clear the segment buffer of Escher
C
      CALL ESDUMP ( ERROR )

      RETURN


      END


