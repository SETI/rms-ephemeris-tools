.. _reference:

Argument reference
===================

This page documents the accepted values for key CLI arguments.

You can pass **IDs** (integers) or **names** (case-insensitive strings) for
``--columns``, ``--mooncols``, ``--moons``, and ``--planet``, and mix them
in one list (e.g. ``--columns 1 2 ymdhms radec``, ``--moons 1 io europa``,
``--planet saturn``).

Planet (``--planet``)
---------------------

The ``--planet`` argument accepts either a number (4-9) or a case-insensitive
name:

.. list-table:: Planet number and name
   :header-rows: 1
   :widths: 10 20

   * - Number
     - Name
   * - 4
     - mars
   * - 5
     - jupiter
   * - 6
     - saturn
   * - 7
     - uranus
   * - 8
     - neptune
   * - 9
     - pluto

Viewpoint and observatory (``--viewpoint``, ``--observatory``)
---------------------------------------------------------------

The ``--viewpoint`` argument selects the *type* of observer position:

- ``observatory`` (default): Observe from a named observatory or spacecraft.
  The specific name is given by ``--observatory`` (default: ``"Earth's Center"``).
- ``latlon``: Observe from a geographic position on Earth, specified with
  ``--latitude``, ``--longitude``, ``--lon-dir`` (east/west), and ``--altitude``.

When ``--viewpoint`` is ``observatory``, the ``--observatory`` argument accepts
the following spacecraft names or abbreviations (case-insensitive):

.. list-table:: Accepted observatory/spacecraft names
   :header-rows: 1
   :widths: 25 15 15

   * - Full Name
     - Abbreviation
     - NAIF Code
   * - Earth's Center
     - (default)
     -
   * - Voyager 1
     - VG1
     - -31
   * - Voyager 2
     - VG2
     - -32
   * - Galileo
     - GLL
     - -77
   * - Cassini
     - CAS
     - -82
   * - New Horizons
     - NH
     - -98
   * - Juno
     - JNO
     - -61
   * - Europa Clipper
     - EC
     - -159
   * - JUICE
     - JCE
     - -28
   * - JWST
     - JWST
     - -170
   * - HST
     - HST
     - -48

For spacecraft observers, use ``--sc-trajectory`` to select the trajectory
file variant (0 = default).

Ring options (``--rings``)
---------------------------

The ``--rings`` argument accepts integer option codes or case-insensitive
ring names. The available options depend on the planet. Integers and names
can be mixed (e.g. ``--rings main 62`` for Saturn).

**Jupiter** (``--planet jupiter``)

.. list-table:: Jupiter ring options
   :header-rows: 1
   :widths: 10 20 40

   * - Code
     - Name
     - Description
   * - 51
     - main
     - Main ring (Halo + Main)
   * - 52
     - gossamer
     - Gossamer rings (Amalthea + Thebe)

**Saturn** (``--planet saturn``)

.. list-table:: Saturn ring options
   :header-rows: 1
   :widths: 10 20 40

   * - Code
     - Name
     - Description
   * - 61
     - main
     - Main rings (A, B, C, F)
   * - 62
     - ge
     - G and E rings
   * - 63
     - outer
     - Outer rings (beyond G)

**Uranus** (``--planet uranus``)

.. list-table:: Uranus ring options
   :header-rows: 1
   :widths: 10 20 40

   * - Code
     - Name
     - Description
   * - 71
     - epsilon
     - Epsilon ring

**Neptune** (``--planet neptune``)

.. list-table:: Neptune ring options
   :header-rows: 1
   :widths: 10 20 40

   * - Code
     - Name
     - Description
   * - 81
     - rings
     - Neptune rings (Galle, Le Verrier, Adams)

Mars and Pluto have no ring options.

Ephemeris column index (``--columns``)
----------------------------------------

The ephemeris table can include the following columns. Use ``--columns`` with
column IDs or names (e.g. ``--columns 1 2 3 15 8`` or ``--columns ymdhms radec phase``).
Accepted names (case-insensitive): mjd, ymdhm, ymdhms, ydhm, ydhms, obsdist, sundist,
phase, obsopen, sunopen, obslon, sunlon, subobs, subsol, radec, earthrd, sunrd, radius,
raddeg, lphase, sunsep, lsep.

.. list-table:: Planet/moon geometry columns
   :header-rows: 1
   :widths: 8 20 40

   * - ID
     - Name
     - Description
   * - 1
     - ``COL_MJD``
     - Modified Julian Date
   * - 2
     - ``COL_YMDHM``
     - Date/time (year-month-day hour:min)
   * - 3
     - ``COL_YMDHMS``
     - Date/time (year-month-day hour:min:sec)
   * - 4
     - ``COL_YDHM``
     - Year and day-of-year + hour:min
   * - 5
     - ``COL_YDHMS``
     - Year and day-of-year + hour:min:sec
   * - 6
     - ``COL_OBSDIST``
     - Observer–planet distance (km)
   * - 7
     - ``COL_SUNDIST``
     - Sun–planet distance (km)
   * - 8
     - ``COL_PHASE``
     - Phase angle (deg)
   * - 9
     - ``COL_OBSOPEN``
     - Ring opening angle to observer (deg)
   * - 10
     - ``COL_SUNOPEN``
     - Ring opening angle to Sun (deg)
   * - 11
     - ``COL_OBSLON``
     - Sub-observer longitude (deg)
   * - 12
     - ``COL_SUNLON``
     - Sub-solar longitude (deg)
   * - 13
     - ``COL_SUBOBS``
     - Sub-observer latitude (deg)
   * - 14
     - ``COL_SUBSOL``
     - Sub-solar latitude (deg)
   * - 15
     - ``COL_RADEC``
     - RA and Dec (deg)
   * - 16
     - ``COL_EARTHRD``
     - Earth range and declination (deg)
   * - 17
     - ``COL_SUNRD``
     - Sun range and declination (deg)
   * - 18
     - ``COL_RADIUS``
     - Apparent radius (arcsec)
   * - 19
     - ``COL_RADDEG``
     - Apparent radius (deg)
   * - 20
     - ``COL_LPHASE``
     - Lunar phase angle (deg)
   * - 21
     - ``COL_SUNSEP``
     - Sun separation (deg)
   * - 22
     - ``COL_LSEP``
     - Lunar separation (deg)

Moon column index (``--mooncols``)
----------------------------------

Moon blocks in the ephemeris table use these column IDs with ``--mooncols``.
You can use IDs or names (e.g. ``--mooncols 5 6 8 9`` or ``--mooncols radec offset orblon``).
Accepted names (case-insensitive): obsdist, phase, subobs, subsol, radec, offset, offdeg,
orblon, orbopen.

.. list-table:: Moon columns
   :header-rows: 1
   :widths: 8 20 40

   * - ID
     - Name
     - Description
   * - 1
     - ``MCOL_OBSDIST``
     - Observer–moon distance (km)
   * - 2
     - ``MCOL_PHASE``
     - Phase angle (deg)
   * - 3
     - ``MCOL_SUBOBS``
     - Sub-observer lat (deg)
   * - 4
     - ``MCOL_SUBSOL``
     - Sub-solar lat (deg)
   * - 5
     - ``MCOL_RADEC``
     - RA and Dec (deg)
   * - 6
     - ``MCOL_OFFSET``
     - Offset from planet (arcsec)
   * - 7
     - ``MCOL_OFFDEG``
     - Offset (deg)
   * - 8
     - ``MCOL_ORBLON``
     - Orbital longitude (deg)
   * - 9
     - ``MCOL_ORBOPEN``
     - Orbital opening angle (deg)

Moon index (``--moons``)
-------------------------

The ``--moons`` argument takes 1-based indices into the planet’s moon list
(e.g. ``--moons 1 2 3`` or ``--moons io europa ganymede``); you can mix indices and names.
Moon order is fixed per planet. Below: index to moon name for each planet. Names are case-insensitive (e.g. ``io``, ``Io``).

**Jupiter** (``--planet 5`` or ``--planet jupiter``)

.. list-table:: Jupiter moon index
   :header-rows: 1
   :widths: 10 20

   * - Index
     - Moon name
   * - 1
     - Io
   * - 2
     - Europa
   * - 3
     - Ganymede
   * - 4
     - Callisto
   * - 5
     - Amalthea
   * - 6
     - Thebe
   * - 7
     - Adrastea
   * - 8
     - Metis
   * - 9
     - Himalia
   * - 10
     - Elara

**Saturn** (``--planet 6`` or ``--planet saturn``)

.. list-table:: Saturn moon index
   :header-rows: 1
   :widths: 10 20

   * - Index
     - Moon name
   * - 1
     - Mimas
   * - 2
     - Enceladus
   * - 3
     - Tethys
   * - 4
     - Dione
   * - 5
     - Rhea
   * - 6
     - Titan
   * - 7
     - Hyperion
   * - 8
     - Iapetus
   * - 9
     - Phoebe
   * - 10
     - Janus
   * - 11
     - Epimetheus
   * - 12
     - Helene
   * - 13
     - Telesto
   * - 14
     - Calypso
   * - 15
     - Atlas
   * - 16
     - Prometheus
   * - 17
     - Pandora
   * - 18
     - Pan
   * - 19
     - Methone
   * - 20
     - Pallene
   * - 21
     - Polydeuces
   * - 22
     - Daphnis
   * - 23
     - Anthe
   * - 24
     - Aegaeon

**Uranus** (``--planet 7`` or ``--planet uranus``)

.. list-table:: Uranus moon index
   :header-rows: 1
   :widths: 10 20

   * - Index
     - Moon name
   * - 1
     - Ariel
   * - 2
     - Umbriel
   * - 3
     - Titania
   * - 4
     - Oberon
   * - 5
     - Miranda
   * - 6
     - Cordelia
   * - 7
     - Ophelia
   * - 8
     - Bianca
   * - 9
     - Cressida
   * - 10
     - Desdemona
   * - 11
     - Juliet
   * - 12
     - Portia
   * - 13
     - Rosalind
   * - 14
     - Belinda
   * - 15
     - Puck
   * - 16
     - Perdita
   * - 17
     - Mab
   * - 18
     - Cupid

**Neptune** (``--planet 8`` or ``--planet neptune``)

.. list-table:: Neptune moon index
   :header-rows: 1
   :widths: 10 20

   * - Index
     - Moon name
   * - 1
     - Triton
   * - 2
     - Nereid
   * - 3
     - Naiad
   * - 4
     - Thalassa
   * - 5
     - Despina
   * - 6
     - Galatea
   * - 7
     - Larissa
   * - 8
     - Proteus
   * - 9
     - Hippocamp

**Mars** (``--planet 4`` or ``--planet mars``)

.. list-table:: Mars moon index
   :header-rows: 1
   :widths: 10 20

   * - Index
     - Moon name
   * - 1
     - Phobos
   * - 2
     - Deimos

**Pluto** (``--planet 9`` or ``--planet pluto``)

.. list-table:: Pluto moon index
   :header-rows: 1
   :widths: 10 20

   * - Index
     - Moon name
   * - 1
     - Charon
   * - 2
     - Nix
   * - 3
     - Hydra
   * - 4
     - Kerberos
   * - 5
     - Styx
