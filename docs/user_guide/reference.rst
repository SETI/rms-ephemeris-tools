.. _reference:

Argument reference
===================

This page documents the accepted values for CLI arguments.

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

``--viewpoint`` selects the *type* of observer: ``observatory`` (default) or
``latlon``. It does not take a spacecraft name. To observe from a spacecraft,
use ``--viewpoint observatory`` and set ``--observatory`` to the spacecraft or
observatory name (e.g. ``--observatory Cassini``, not ``--viewpoint cas``).

- ``observatory`` (default): Observe from a named observatory or spacecraft.
  The name is given by ``--observatory`` (default: ``"Earth's center"``).
- ``latlon``: Observe from a geographic position on Earth, specified with
  ``--latitude``, ``--longitude``, ``--lon-dir`` (east/west), and ``--altitude``.

When ``--viewpoint`` is ``observatory``, ``--observatory`` accepts the
following spacecraft names or abbreviations (case-insensitive):

.. list-table:: Accepted observatory/spacecraft names
   :header-rows: 1
   :widths: 25 15 15

   * - Full Name
     - Abbreviation
     - NAIF Code
   * - Earth's center
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
     - Name(s)
     - Description
   * - 71
     - alpha, beta, eta, gamma, delta, epsilon
     - All Uranus rings (Six, Five, Four, Alpha, Beta, Eta, Gamma, Delta,
       Lambda, Epsilon, Nu, Mu). Any ring name maps to the same code.

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

FOV unit (``--fov-unit``)
--------------------------

The ``--fov-unit`` argument accepts angle units, distance units, planet-relative
units, and instrument FOV names:

.. list-table:: FOV unit values
   :header-rows: 1
   :widths: 25 50

   * - Value
     - Meaning
   * - ``deg``
     - Degrees (default)
   * - ``arcmin``
     - Arc minutes
   * - ``arcsec``
     - Arc seconds
   * - ``mrad``
     - Milliradians
   * - ``urad``
     - Microradians
   * - ``km``
     - Kilometres (converted using observer range)
   * - ``<Planet> radii``
     - Planet equatorial radii (e.g. ``Saturn radii``, ``Neptune radii``)
   * - ``Cassini ISS narrow``
     - Cassini ISS Narrow Angle Camera FOV
   * - ``Cassini ISS wide``
     - Cassini ISS Wide Angle Camera FOV
   * - ``Voyager ISS narrow``
     - Voyager ISS Narrow Angle Camera FOV
   * - ``Voyager ISS wide``
     - Voyager ISS Wide Angle Camera FOV
   * - ``Galileo SSI``
     - Galileo SSI FOV
   * - ``LORRI``
     - New Horizons LORRI FOV

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
     - mjd
     - Modified Julian Date
   * - 2
     - ymdhm
     - Date/time (year-month-day hour:min)
   * - 3
     - ymdhms
     - Date/time (year-month-day hour:min:sec)
   * - 4
     - ydhm
     - Year and day-of-year + hour:min
   * - 5
     - ydhms
     - Year and day-of-year + hour:min:sec
   * - 6
     - obsdist
     - Observer–planet distance (km)
   * - 7
     - sundist
     - Sun–planet distance (km)
   * - 8
     - phase
     - Phase angle (deg)
   * - 9
     - obsopen
     - Ring opening angle to observer (deg)
   * - 10
     - sunopen
     - Ring opening angle to Sun (deg)
   * - 11
     - obslon
     - Sub-observer longitude (deg)
   * - 12
     - sunlon
     - Sub-solar longitude (deg)
   * - 13
     - subobs
     - Sub-observer latitude (deg)
   * - 14
     - subsol
     - Sub-solar latitude (deg)
   * - 15
     - radec
     - RA and Dec (deg)
   * - 16
     - earthrd
     - Earth range and declination (deg)
   * - 17
     - sunrd
     - Sun range and declination (deg)
   * - 18
     - radius
     - Apparent radius (arcsec)
   * - 19
     - raddeg
     - Apparent radius (deg)
   * - 20
     - lphase
     - Lunar phase angle (deg)
   * - 21
     - sunsep
     - Sun separation (deg)
   * - 22
     - lsep
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
     - obsdist
     - Observer–moon distance (km)
   * - 2
     - phase
     - Phase angle (deg)
   * - 3
     - subobs
     - Sub-observer lat (deg)
   * - 4
     - subsol
     - Sub-solar lat (deg)
   * - 5
     - radec
     - RA and Dec (deg)
   * - 6
     - offset
     - Offset from planet (arcsec)
   * - 7
     - offdeg
     - Offset (deg)
   * - 8
     - orblon
     - Orbital longitude (deg)
   * - 9
     - orbopen
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
