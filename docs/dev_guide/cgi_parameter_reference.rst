CGI Parameter Reference
=======================

This document catalogs every CGI environment variable that the web forms
can send to the three tools (Viewer, Tracker, Ephemeris Generator), with
every possible value listed explicitly.  It is derived from the SHTML
form definitions in ``web/old/tools/``.

The Perl ``newcgi.pm`` module parses the query string and exports each
``key=value`` pair as an environment variable.  The FORTRAN binary (or,
now, the Python ``--cgi`` mode) reads these environment variables
directly.

.. contents:: Table of Contents
   :local:
   :depth: 2

Viewer Parameters
-----------------

All viewer forms submit to ``viewer3_xxx.pl`` (now ``viewer3_xxx.sh``).

Metadata (consumed by the CGI wrapper, not the backend)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``abbrev`` (hidden)
   Identifies the planet and optional mission prefix.

   Possible values:

   - ``"sat"``
   - ``"jup"``
   - ``"ura"``
   - ``"nep"``
   - ``"plu"``
   - ``"mar"``
   - ``"satc"``
   - ``"jupc"``
   - ``"jupj"``
   - ``"jupjc"``
   - ``"jupnh"``
   - ``"jupec"``
   - ``"plunh"``

``version`` (hidden)
   Form version string.

   Possible values:

   - ``"3.1"``

``output`` (radio)
   Output format.

   Possible values:

   - ``"HTML"``
   - ``"PDF"``
   - ``"JPEG"``
   - ``"PS"``

``submit`` (submit button)
   Always ``"Render diagram"``.  Ignored by the backend.

Ephemeris Selection
~~~~~~~~~~~~~~~~~~~

``ephem`` (hidden)
   SPICE kernel selection string.  The leading three-digit number is the
   version code (``000`` = latest); the rest describes the kernel files.

   Possible values:

   - ``"000 MAR097 + DE440"`` (Mars)
   - ``"000 JUP365 + DE440"`` (Jupiter, non-New-Horizons)
   - ``"000 JUP344 + JUP365 + DE440"`` (Jupiter, New Horizons)
   - ``"000 SAT415 + SAT441 + DE440"`` (Saturn)
   - ``"000 URA111 + URA115 + DE440"`` (Uranus)
   - ``"000 NEP095 + NEP097 + NEP101 + DE440"`` (Neptune)
   - ``"000 PLU058 + DE440"`` (Pluto)

Observation Time
~~~~~~~~~~~~~~~~

``time`` (text)
   Free-text datetime string.  Format: ``yyyy-mm-dd hh:mm:ss``.
   Required field.

Field of View
~~~~~~~~~~~~~

``fov`` (text)
   Numeric value for the field of view.  Free text.  Examples: ``".005"``,
   ``"10"``, ``"0.5"``.  Required field.

``fov_unit`` (select)
   Unit for the ``fov`` value.  Note: all form values have a leading
   space due to HTML formatting.

   Possible values (all planets):

   - ``" seconds of arc"``
   - ``" degrees"``
   - ``" milliradians"``
   - ``" microradians"``
   - ``" kilometers"``

   Planet-specific values (selected by default for each planet):

   - ``" Mars radii"`` (Mars)
   - ``" Jupiter radii"`` (Jupiter)
   - ``" Saturn radii"`` (Saturn)
   - ``" Uranus radii"`` (Uranus)
   - ``" Neptune radii"`` (Neptune)
   - ``" Pluto radii (1153 km)"`` (Pluto)
   - ``" Pluto-Charon separations (19,571 km)"`` (Pluto, default)

   Instrument-specific values (only when PREFIX is empty or matches
   mission):

   - ``" Voyager ISS wide angle FOVs"`` (Jupiter, Saturn, Uranus, Neptune)
   - ``" Voyager ISS narrow angle FOVs"`` (Jupiter, Saturn, Uranus, Neptune)
   - ``" Galileo SSI FOVs"`` (Jupiter only)
   - ``" Cassini ISS wide angle FOVs"`` (Jupiter, Saturn)
   - ``" Cassini ISS narrow angle FOVs"`` (Jupiter, Saturn)
   - ``" Cassini VIMS 64x64 FOVs"`` (Jupiter, Saturn)
   - ``" Cassini UVIS slit widths"`` (Jupiter, Saturn)
   - ``" LORRI FOVs"`` (Pluto only)

Diagram Center
~~~~~~~~~~~~~~

``center`` (radio)
   Center mode.

   Possible values:

   - ``"body"``
   - ``"ansa"``
   - ``"J2000"``
   - ``"star"``

``center_body`` (select, when center="body")
   Body to center on.  Leading space from HTML formatting.

   Mars:

   - ``" Mars"``
   - ``" Phobos (M1)"``
   - ``" Deimos (M2)"``

   Jupiter:

   - ``" Jupiter"``
   - ``" Io (J1)"``
   - ``" Europa (J2)"``
   - ``" Ganymede (J3)"``
   - ``" Callisto (J4)"``
   - ``" Amalthea (J5)"``
   - ``" Thebe (J14)"``
   - ``" Adrastea (J15)"``
   - ``" Metis (J16)"``

   Saturn:

   - ``" Saturn"``
   - ``" Mimas (S1)"``
   - ``" Enceladus (S2)"``
   - ``" Tethys (S3)"``
   - ``" Dione (S4)"``
   - ``" Rhea (S5)"``
   - ``" Titan (S6)"``
   - ``" Hyperion (S7)"``
   - ``" Iapetus (S8)"``
   - ``" Phoebe (S9)"``
   - ``" Janus (S10)"``
   - ``" Epimetheus (S11)"``
   - ``" Helene (S12)"``
   - ``" Telesto (S13)"``
   - ``" Calypso (S14)"``
   - ``" Atlas (S15)"``
   - ``" Prometheus (S16)"``
   - ``" Pandora (S17)"``
   - ``" Pan (S18)"``
   - ``" Methone (S32)"``
   - ``" Pallene (S33)"``
   - ``" Polydeuces (S34)"``
   - ``" Daphnis (S35)"``
   - ``" Anthe (S49)"``
   - ``" Aegaeon (S53)"``

   Uranus:

   - ``" Uranus"``
   - ``" Miranda (U5)"``
   - ``" Ariel (U1)"``
   - ``" Umbriel (U2)"``
   - ``" Titania (U3)"``
   - ``" Oberon (U4)"``
   - ``" Cordelia (U6)"``
   - ``" Ophelia (U7)"``
   - ``" Bianca (U8)"``
   - ``" Cressida (U9)"``
   - ``" Desdemona (U10)"``
   - ``" Juliet (U11)"``
   - ``" Portia (U12)"``
   - ``" Rosalind (U13)"``
   - ``" Belinda (U14)"``
   - ``" Puck (U15)"``
   - ``" Perdita (U25)"``
   - ``" Mab (U26)"``
   - ``" Cupid (U27)"``

   Neptune:

   - ``" Neptune"``
   - ``" Triton (N1)"``
   - ``" Nereid (N2)"``
   - ``" Naiad (N3)"``
   - ``" Thalassa (N4)"``
   - ``" Despina (N5)"``
   - ``" Galatea (N6)"``
   - ``" Larissa (N7)"``
   - ``" Proteus (N8)"``
   - ``" Hippocamp (N14)"``

   Pluto:

   - ``" Barycenter"``
   - ``" Pluto"``
   - ``" Charon (P1)"``
   - ``" Nix (P2)"``
   - ``" Hydra (P3)"``
   - ``" Kerberos (P4)"``
   - ``" Styx (P5)"``

``center_ansa`` (select, when center="ansa")
   Ring to center on.  Leading space from HTML formatting.

   Mars:

   - ``" Phobos Ring"``
   - ``" Deimos Ring"``

   Jupiter:

   - ``" Halo"``
   - ``" Main Ring"``
   - ``" Amalthea Ring"``
   - ``" Thebe Ring"``

   Saturn:

   - ``" C Ring"``
   - ``" B Ring"``
   - ``" A Ring"``
   - ``" F Ring"``
   - ``" G Ring"``
   - ``" E Ring core"``

   Uranus:

   - ``" 6 Ring"``
   - ``" 5 Ring"``
   - ``" 4 Ring"``
   - ``" Alpha Ring"``
   - ``" Beta Ring"``
   - ``" Eta Ring"``
   - ``" Gamma Ring"``
   - ``" Delta Ring"``
   - ``" Lambda Ring"``
   - ``" Epsilon Ring"``
   - ``" Nu Ring"``
   - ``" Mu Ring"``

   Neptune:

   - ``" Galle Ring"``
   - ``" LeVerrier Ring"``
   - ``" Arago Ring"``
   - ``" Adams Ring"``

   Pluto:

   - ``" Styx"``
   - ``" Nix"``
   - ``" Kerberos"``
   - ``" Hydra"``

``center_ew`` (select, when center="ansa")
   Ansa direction.

   Possible values:

   - ``" east"``
   - ``" west"``

``center_ra`` (text, when center="J2000")
   Right ascension for diagram center.  Free-text numeric.

``center_ra_type`` (select, when center="J2000")
   RA unit.

   Possible values:

   - ``" hours"``
   - ``" degrees"``

``center_dec`` (text, when center="J2000")
   Declination in degrees for diagram center.  Free-text numeric.

``center_star`` (text, when center="star")
   Star name for diagram center.  Free text.

Viewpoint
~~~~~~~~~

``viewpoint`` (radio or hidden)
   Observer type.

   Possible values:

   - ``"observatory"``
   - ``"latlon"``

   When PREFIX is set (mission-specific forms), this is a hidden field
   with value ``"observatory"``.

``observatory`` (select or hidden)
   Observatory or spacecraft name.

   When PREFIX is set, this is a hidden field with one of:

   - ``"Cassini"``
   - ``"New Horizons"``
   - ``"Juno"``
   - ``"JUICE"``
   - ``"Europa Clipper"``

   When PREFIX is empty (Earth-based forms), this is a select with:

   - ``" Earth's center"``
   - ``" HST"``
   - ``" JWST"``
   - ``" Apache Point Observatory (32.780361, -105.820417, 2674.)"``
   - ``" Kitt Peak National Observatory (31.958833, -111.594694, 2058.4)"``
   - ``" Lowell Observatory (35.097, -111.537, 2200.)"``
   - ``" Mauna Kea Observatory (19.827, -155.472, 4215.)"``
   - ``" McDonald Observatory (30.671500, -104.022611, 2076.)"``
   - ``" Mt. Evans Observatory (39.587, -105.640, 4305.)"``
   - ``" NMSU Observatory (32.27631, -106.746556, 0.)"``
   - ``" Paranal Observatory/VLT (-24.625417, -70.402806, 2635.)"``
   - ``" Yerkes Observatory (41.098, 88.557, 334.)"``

   Plus spacecraft options when the viewer TOOL is ``viewer3`` and PREFIX
   is empty:

   - ``" Voyager 1"`` (Jupiter, Saturn)
   - ``" Voyager 2"`` (Jupiter, Saturn, Uranus, Neptune)
   - ``" Galileo"`` (Jupiter)
   - ``" Cassini"`` (Jupiter, Saturn)
   - ``" New Horizons"`` (Jupiter, Pluto)
   - ``" Juno"`` (Jupiter)
   - ``" JUICE"`` (Jupiter)
   - ``" Europa Clipper"`` (Jupiter)

``latitude`` (text, when viewpoint="latlon")
   Observer latitude in degrees.  Free-text numeric.

``longitude`` (text, when viewpoint="latlon")
   Observer longitude in degrees.  Free-text numeric.

``lon_dir`` (select, when viewpoint="latlon")
   Longitude direction.

   Possible values:

   - ``" east"``
   - ``" west"``

``altitude`` (text, when viewpoint="latlon")
   Observer altitude in meters.  Free-text numeric.

Moon Selection
~~~~~~~~~~~~~~

``moons`` (radio, single value)
   Predefined moon group.  The leading number is a group code used by
   the FORTRAN to select moons where ``moon_id <= group_code``.

   Mars (hidden field, not radio):

   - ``"402 Phobos, Deimos"``

   Jupiter:

   - ``"504 Galilean satellites (J1-J4)"``
   - ``"505 Galileans satellites, Amalthea (J1-J5)"``
   - ``"516 All inner moons (J1-J5,J14-J16)"``

   Saturn:

   - ``"609 Classical satellites (S1-S9)"``
   - ``"618 Classicals, Voyager discoveries (S1-S18)"``
   - ``"653 All inner moons (S1-S18,S32-S35,S49,S53)"``

   Uranus:

   - ``"705 Classical satellites (U1-U5)"``
   - ``"715 Classicals, Voyager discoveries (U1-U15)"``
   - ``"727 All inner moons (U1-U15,U25-U27)"``

   Neptune:

   - ``"802 Triton & Nereid"``
   - ``"814 All inner moons (N1-N8,N14)"``

   Pluto:

   - ``"901 Charon (P1)"``
   - ``"903 Charon, Nix, Hydra (P1-P3)"``
   - ``"905 All moons (P1-P5)"``

   NAIF IDs included per group code:

   - 402: 401 (Phobos), 402 (Deimos)
   - 504: 501 (Io), 502 (Europa), 503 (Ganymede), 504 (Callisto)
   - 505: 501-505 (adds Amalthea)
   - 516: 501-505, 514 (Thebe), 515 (Adrastea), 516 (Metis)
   - 609: 601 (Mimas) through 609 (Phoebe)
   - 618: 601-618 (Mimas through Pan)
   - 653: 601-618, 632 (Methone), 633 (Pallene), 634 (Polydeuces),
     635 (Daphnis), 649 (Anthe), 653 (Aegaeon)
   - 705: 701 (Ariel) through 705 (Miranda)
   - 715: 701-715 (Ariel through Puck)
   - 727: 701-715, 725 (Perdita), 726 (Mab), 727 (Cupid)
   - 802: 801 (Triton), 802 (Nereid)
   - 814: 801-808, 814 (Hippocamp)
   - 901: 901 (Charon)
   - 903: 901 (Charon), 902 (Nix), 903 (Hydra)
   - 905: 901-905 (Charon, Nix, Hydra, Kerberos, Styx)

Ring Selection
~~~~~~~~~~~~~~

``rings`` (radio, single value)
   Comma-separated ring names or group descriptions.

   Mars:

   - ``"None"``
   - ``"Phobos, Deimos"``

   Jupiter:

   - ``"None"``
   - ``"Main"``
   - ``"Main & Gossamer"``

   Saturn:

   - ``"A,B,C"``
   - ``"A,B,C,F"``
   - ``"A,B,C,F,E"``
   - ``"A,B,C,F,G,E"``

   Uranus:

   - ``"Alpha, Beta, Eta, Gamma, Delta, Epsilon"``
   - ``"Nine major rings"``
   - ``"All inner rings"``
   - ``"All rings"``

   Neptune:

   - ``"LeVerrier, Adams"``
   - ``"LeVerrier, Arago, Adams"``
   - ``"Galle, LeVerrier, Arago, Adams"``

   Pluto:

   - ``"None"``
   - ``"Charon"``
   - ``"Charon, Nix, Hydra"``
   - ``"Charon, Styx, Nix, Kerberos, Hydra"``
   - ``"Nix, Hydra"``
   - ``"Styx, Nix, Kerberos, Hydra"``

Arc Model (Neptune only)
~~~~~~~~~~~~~~~~~~~~~~~~

``arcmodel`` (radio)
   Neptune arc motion model.

   Possible values:

   - ``"#1 (820.1194 deg/day)"``
   - ``"#2 (820.1118 deg/day)"``
   - ``"#3 (820.1121 deg/day)"``

Background Objects
~~~~~~~~~~~~~~~~~~

``standard`` (checkbox)
   Standard stars overlay.

   Possible values:

   - ``"Yes"`` (when checked)
   - absent (when unchecked)

``additional`` (checkbox)
   Additional user-specified star.

   Possible values:

   - ``"Yes"`` (when checked)
   - absent (when unchecked)

``extra_ra`` (text)
   Additional star right ascension.  Free-text numeric.

``extra_ra_type`` (select)
   RA unit for additional star.

   Possible values:

   - ``" hours"``
   - ``" degrees"``

``extra_dec`` (text)
   Additional star declination in degrees.  Free-text numeric.

``extra_name`` (text)
   Additional star label.  Free text.

``other`` (checkbox, multi-valued)
   Other bodies to mark on the diagram.  Multiple values are joined
   with ``#`` by ``newcgi.pm``.

   All planets:

   - ``"Sun"``
   - ``"Anti-Sun"``
   - ``"Earth"``

   Jupiter (PREFIX empty):

   - ``"Voyager 1"``
   - ``"Voyager 2"``
   - ``"Galileo"``
   - ``"Cassini"``
   - ``"New Horizons"``
   - ``"Juno"``
   - ``"JUICE"``
   - ``"Europa Clipper"``

   Jupiter (PREFIX="JUICE/"):

   - ``"Europa Clipper"``

   Jupiter (PREFIX="Europa Clipper/"):

   - ``"JUICE"``

   Saturn (PREFIX empty):

   - ``"Voyager 1"``
   - ``"Voyager 2"``
   - ``"Cassini"``

   Uranus (PREFIX empty):

   - ``"Voyager 2"``

   Neptune (PREFIX empty):

   - ``"Voyager 2"``

   Pluto:

   - ``"Barycenter"``
   - ``"New Horizons"`` (PREFIX empty only)

Diagram Options
~~~~~~~~~~~~~~~

``title`` (text)
   Plot title.  Free text, max 60 characters.

``labels`` (select)
   Moon and star label size.

   Possible values:

   - ``"None"``
   - ``"Small (6 points)"``
   - ``"Medium (9 points)"``
   - ``"Large (12 points)"``

``moonpts`` (text)
   Moon enlargement in points.  Free-text numeric.  Default ``"0"``.

``blank`` (radio, PREFIX empty only)
   Blank disks mode.

   Possible values:

   - ``"Yes"``
   - ``"No"``

``opacity`` (select, Saturn only)
   Ring plot type.

   Possible values:

   - ``"Transparent"``
   - ``"Semi-transparent (2x file size)"``
   - ``"Opaque"``

``peris`` (select, Saturn and Uranus only)
   Pericenter marker selection.

   Saturn:

   - ``"None"``
   - ``"F Ring"``

   Uranus:

   - ``"None"``
   - ``"Epsilon Ring only"``
   - ``"All rings"``

``peripts`` (text, Saturn and Uranus only)
   Pericenter marker size in points.  Free-text numeric.  Default ``"4"``.

``meridians`` (radio)
   Highlight prime meridians.

   Possible values:

   - ``"Yes"``
   - ``"No"``

``arcpts`` (text, Neptune only)
   Arc weight in points.  Free-text numeric.  Default ``"4"``.

Jupiter-Specific
~~~~~~~~~~~~~~~~

``torus`` (checkbox, Jupiter only)
   Io torus overlay.

   Possible values:

   - ``"Yes"`` (when checked)
   - absent (when unchecked)

``torus_inc`` (text, Jupiter only)
   Io torus inclination in degrees.  Default ``"6.8"``.

``torus_rad`` (text, Jupiter only)
   Io torus radius in km.  Default ``"422000"``.


Tracker Parameters
------------------

All tracker forms submit to ``tracker3_xxx.pl`` (now ``tracker3_xxx.sh``).

Metadata
~~~~~~~~

``abbrev`` (hidden)
   Identifies the planet and optional mission prefix.

   Possible values:

   - ``"sat"``
   - ``"jup"``
   - ``"ura"``
   - ``"nep"``
   - ``"satc"``
   - ``"jupc"``
   - ``"jupj"``
   - ``"jupjc"``
   - ``"jupnh"``
   - ``"jupec"``

``version`` (hidden)
   Form version string.

   Possible values:

   - ``"3.0"``

``output`` (radio)
   Output format.

   Possible values:

   - ``"HTML"``
   - ``"PDF"``
   - ``"JPEG"``
   - ``"PS"``
   - ``"TAB"``

``submit`` (submit button)
   Always ``"Submit"``.  Ignored by the backend.

Ephemeris Selection
~~~~~~~~~~~~~~~~~~~

``ephem`` (hidden)
   SPICE kernel selection string.

   Possible values:

   - ``"000 JUP365 + DE440"`` (Jupiter, non-New-Horizons)
   - ``"000 JUP344 + JUP365 + DE440"`` (Jupiter, New Horizons)
   - ``"000 SAT415 + SAT441 + DE440"`` (Saturn)
   - ``"000 URA111 + URA115 + DE440"`` (Uranus)
   - ``"000 NEP095 + NEP097 + NEP101 + DE440"`` (Neptune)

   Note: Mars and Pluto do not have tracker forms.

Time Range
~~~~~~~~~~

``start`` (text)
   Start time.  Free-text datetime.

``stop`` (text)
   Stop time.  Free-text datetime.

``interval`` (text)
   Time step size.  Free-text numeric.

``time_unit`` (select)
   Time step unit.

   Possible values:

   - ``"seconds"``
   - ``"minutes"``
   - ``"hours"``
   - ``"days"``

Viewpoint
~~~~~~~~~

``viewpoint`` (radio or hidden)
   Observer type.

   Possible values:

   - ``"observatory"``
   - ``"latlon"``

   When PREFIX is set (mission-specific forms), this is a hidden field
   with value ``"observatory"``.

``observatory`` (select or hidden)
   Observatory or spacecraft name.

   When PREFIX is set, this is a hidden field with one of:

   - ``"Cassini"``
   - ``"New Horizons"``
   - ``"Juno"``
   - ``"JUICE"``
   - ``"Europa Clipper"``

   When PREFIX is empty (Earth-based forms), this is a select with:

   - ``" Earth's center"``
   - ``" HST"``
   - ``" JWST"``
   - ``" Apache Point Observatory (32.780361, -105.820417, 2674.)"``
   - ``" Kitt Peak National Observatory (31.958833, -111.594694, 2058.4)"``
   - ``" Lowell Observatory (35.097, -111.537, 2200.)"``
   - ``" Mauna Kea Observatory (19.827, -155.472, 4215.)"``
   - ``" McDonald Observatory (30.671500, -104.022611, 2076.)"``
   - ``" Mt. Evans Observatory (39.587, -105.640, 4305.)"``
   - ``" NMSU Observatory (32.27631, -106.746556, 0.)"``
   - ``" Paranal Observatory/VLT (-24.625417, -70.402806, 2635.)"``
   - ``" Yerkes Observatory (41.098, 88.557, 334.)"``

   Note: spacecraft observatory options (Voyager, etc.) only appear
   for the viewer tool, not the tracker.

``latitude`` (text, when viewpoint="latlon")
   Observer latitude in degrees.  Free-text numeric.

``longitude`` (text, when viewpoint="latlon")
   Observer longitude in degrees.  Free-text numeric.

``lon_dir`` (select, when viewpoint="latlon")
   Longitude direction.

   Possible values:

   - ``" east"``
   - ``" west"``

``altitude`` (text, when viewpoint="latlon")
   Observer altitude in meters.  Free-text numeric.

Moon Selection
~~~~~~~~~~~~~~

``moons`` (checkbox, multi-valued)
   Individual moon checkboxes.  The leading three-digit number is the
   moon's 1-based index within the planet system.  Multiple values are
   joined with ``#`` by ``newcgi.pm``.

   Mars:

   - ``"001 Phobos (M1)"``
   - ``"002 Deimos (M2)"``

   Jupiter:

   - ``"001 Io (J1)"``
   - ``"002 Europa (J2)"``
   - ``"003 Ganymede (J3)"``
   - ``"004 Callisto (J4)"``
   - ``"005 Amalthea (J5)"``
   - ``"014 Thebe (J14)"``
   - ``"015 Adrastea (J15)"``
   - ``"016 Metis (J16)"``
   - ``"006 Himalia (J6)"`` (New Horizons only)
   - ``"007 Elara (J7)"`` (New Horizons only)

   Saturn:

   - ``"001 Mimas (S1)"``
   - ``"002 Enceladus (S2)"``
   - ``"003 Tethys (S3)"``
   - ``"004 Dione (S4)"``
   - ``"005 Rhea (S5)"``
   - ``"006 Titan (S6)"``
   - ``"007 Hyperion (S7)"``
   - ``"008 Iapetus (S8)"``
   - ``"009 Phoebe (S9)"``
   - ``"010 Janus (S10)"``
   - ``"011 Epimetheus (S11)"``
   - ``"012 Helene (S12)"``
   - ``"013 Telesto (S13)"``
   - ``"014 Calypso (S14)"``
   - ``"015 Atlas (S15)"``
   - ``"016 Prometheus (S16)"``
   - ``"017 Pandora (S17)"``
   - ``"018 Pan (S18)"``
   - ``"032 Methone (S32)"``
   - ``"033 Pallene (S33)"``
   - ``"034 Polydeuces (S34)"``
   - ``"035 Daphnis (S35)"``
   - ``"049 Anthe (S49)"``
   - ``"053 Aegaeon (S53)"``

   Uranus:

   - ``"001 Ariel (U1)"``
   - ``"002 Umbriel (U2)"``
   - ``"003 Titania (U3)"``
   - ``"004 Oberon (U4)"``
   - ``"005 Miranda (U5)"``
   - ``"006 Cordelia (U6)"``
   - ``"007 Ophelia (U7)"``
   - ``"008 Bianca (U8)"``
   - ``"009 Cressida (U9)"``
   - ``"010 Desdemona (U10)"``
   - ``"011 Juliet (U11)"``
   - ``"012 Portia (U12)"``
   - ``"013 Rosalind (U13)"``
   - ``"014 Belinda (U14)"``
   - ``"015 Puck (U15)"``
   - ``"025 Perdita (U25)"``
   - ``"026 Mab (U26)"``
   - ``"027 Cupid (U27)"``

   Neptune:

   - ``"001 Triton (N1)"``
   - ``"002 Nereid (N2)"``
   - ``"003 Naiad (N3)"``
   - ``"004 Thalassa (N4)"``
   - ``"005 Despina (N5)"``
   - ``"006 Galatea (N6)"``
   - ``"007 Larissa (N7)"``
   - ``"008 Proteus (N8)"``
   - ``"014 Hippocamp (N14)"``

   Pluto:

   - ``"001 Charon (P1)"``
   - ``"005 Styx (P5)"``
   - ``"002 Nix (P2)"``
   - ``"004 Kerberos (P4)"``
   - ``"003 Hydra (P3)"``

Ring Selection
~~~~~~~~~~~~~~

``rings`` (checkbox, multi-valued)
   Ring option checkboxes.  The leading three-digit number is an
   internal code (not a NAIF ID).  Multiple values are joined with
   ``#`` by ``newcgi.pm``.

   Jupiter:

   - ``"051 Main Ring"``
   - ``"052 Gossamer Rings"``

   Saturn:

   - ``"061 Main Rings"``
   - ``"062 G Ring"``
   - ``"063 E Ring"``

   Uranus:

   - ``"071 Epsilon Ring"``

   Neptune:

   - ``"081 Adams Ring"``

   Note: Mars and Pluto tracker forms do not have ring selection.

Plot Options
~~~~~~~~~~~~

``xrange`` (text)
   Scale half-width.  Free-text numeric.

``xunit`` (select)
   Scale unit.

   Possible values (when PREFIX is empty):

   - ``"arcsec"``
   - ``"Jupiter radii"`` (Jupiter)
   - ``"Saturn radii"`` (Saturn)
   - ``"Uranus radii"`` (Uranus)
   - ``"Neptune radii"`` (Neptune)

   Possible values (when PREFIX is set):

   - ``"degrees"``
   - ``"Jupiter radii"`` (Jupiter)
   - ``"Saturn radii"`` (Saturn)
   - ``"Uranus radii"`` (Uranus)
   - ``"Neptune radii"`` (Neptune)

``title`` (text)
   Plot title.  Free text, max 60 characters.


Ephemeris Generator Parameters
------------------------------

All ephemeris forms submit to ``ephem3_xxx.pl`` (now ``ephem3_xxx.sh``).

Metadata
~~~~~~~~

``abbrev`` (hidden)
   Identifies the planet and optional mission prefix.

   Possible values:

   - ``"mar"``
   - ``"jup"``
   - ``"sat"``
   - ``"ura"``
   - ``"nep"``
   - ``"plu"``
   - ``"jupc"``
   - ``"jupj"``
   - ``"jupjc"``
   - ``"jupnh"``
   - ``"jupec"``
   - ``"satc"``
   - ``"plunh"``

``version`` (hidden)
   Form version string.

   Possible values:

   - ``"3.0"``

``output`` (radio)
   Output format.

   Possible values:

   - ``"HTML"``
   - ``"TAB"``

``submit`` (submit button)
   Always ``"Generate table"``.  Ignored by the backend.

Ephemeris Selection
~~~~~~~~~~~~~~~~~~~

``ephem`` (hidden)
   SPICE kernel selection string.

   Possible values:

   - ``"000 MAR097 + DE440"`` (Mars)
   - ``"000 JUP365 + DE440"`` (Jupiter, non-New-Horizons)
   - ``"000 JUP344 + JUP365 + DE440"`` (Jupiter, New Horizons)
   - ``"000 SAT415 + SAT441 + DE440"`` (Saturn)
   - ``"000 URA111 + URA115 + DE440"`` (Uranus)
   - ``"000 NEP095 + NEP097 + NEP101 + DE440"`` (Neptune)
   - ``"000 PLU058 + DE440"`` (Pluto)

Time Range
~~~~~~~~~~

``start`` (text)
   Start time.  Free-text datetime.

``stop`` (text)
   Stop time.  Free-text datetime.

``interval`` (text)
   Time step size.  Free-text numeric.

``time_unit`` (select)
   Time step unit.

   Possible values:

   - ``"seconds"``
   - ``"minutes"``
   - ``"hours"``
   - ``"days"``

Viewpoint
~~~~~~~~~

``viewpoint`` (radio or hidden)
   Observer type.

   Possible values:

   - ``"observatory"``
   - ``"latlon"``

   When PREFIX is set (mission-specific forms), this is a hidden field
   with value ``"observatory"``.

``observatory`` (select or hidden)
   Observatory or spacecraft name.

   When PREFIX is set, this is a hidden field with one of:

   - ``"Cassini"``
   - ``"New Horizons"``
   - ``"Juno"``
   - ``"JUICE"``
   - ``"Europa Clipper"``

   When PREFIX is empty (Earth-based forms), this is a select with:

   - ``" Earth's center"``
   - ``" HST"``
   - ``" JWST"``
   - ``" Apache Point Observatory (32.780361, -105.820417, 2674.)"``
   - ``" Kitt Peak National Observatory (31.958833, -111.594694, 2058.4)"``
   - ``" Lowell Observatory (35.097, -111.537, 2200.)"``
   - ``" Mauna Kea Observatory (19.827, -155.472, 4215.)"``
   - ``" McDonald Observatory (30.671500, -104.022611, 2076.)"``
   - ``" Mt. Evans Observatory (39.587, -105.640, 4305.)"``
   - ``" NMSU Observatory (32.27631, -106.746556, 0.)"``
   - ``" Paranal Observatory/VLT (-24.625417, -70.402806, 2635.)"``
   - ``" Yerkes Observatory (41.098, 88.557, 334.)"``

   Note: spacecraft observatory options (Voyager, etc.) do not appear
   for the ephemeris tool.

``latitude`` (text, when viewpoint="latlon")
   Observer latitude in degrees.  Free-text numeric.

``longitude`` (text, when viewpoint="latlon")
   Observer longitude in degrees.  Free-text numeric.

``lon_dir`` (select, when viewpoint="latlon")
   Longitude direction.

   Possible values:

   - ``" east"``
   - ``" west"``

``altitude`` (text, when viewpoint="latlon")
   Observer altitude in meters.  Free-text numeric.

General Columns
~~~~~~~~~~~~~~~

``columns`` (checkbox, multi-valued)
   Column selection checkboxes.  The leading three-digit number is the
   column ID.  Multiple values are joined with ``#`` by ``newcgi.pm``.

   All planets (PREFIX empty, Earth-based):

   - ``"001 Modified Julian Date"``
   - ``"002 Year, Month, Day, Hour, Minute"``
   - ``"003 Year, Month, Day, Hour, Minute, Second"``
   - ``"004 Year, DOY, Hour, Minute"``
   - ``"005 Year, DOY, Hour, Minute, Second"``
   - ``"006 Observer-[Planet] distance"``
   - ``"007 Sun-[Planet] distance"``
   - ``"008 [Planet] phase angle"``
   - ``"009 Ring plane opening angle to observer"``
   - ``"010 Ring plane opening angle to Sun"``
   - ``"011 Sub-observer inertial longitude"``
   - ``"012 Sub-solar inertial longitude"``
   - ``"013 Sub-observer latitude & rotating longitude"``
   - ``"014 Sub-solar latitude & rotating longitude"``
   - ``"015 [Planet] RA & Dec"``
   - ``"018 [Planet] projected equatorial radius"`` (arcsec)
   - ``"020 Lunar phase angle"``
   - ``"021 Sun-[Planet] sky separation angle"``
   - ``"022 Lunar-[Planet] sky separation angle"``

   All planets (PREFIX set, spacecraft-based):

   - ``"001 Modified Julian Date"``
   - ``"002 Year, Month, Day, Hour, Minute"``
   - ``"003 Year, Month, Day, Hour, Minute, Second"``
   - ``"004 Year, DOY, Hour, Minute"``
   - ``"005 Year, DOY, Hour, Minute, Second"``
   - ``"006 Observer-[Planet] distance"``
   - ``"007 Sun-[Planet] distance"``
   - ``"008 [Planet] phase angle"``
   - ``"009 Ring plane opening angle to observer"``
   - ``"010 Ring plane opening angle to Sun"``
   - ``"011 Sub-observer inertial longitude"``
   - ``"012 Sub-solar inertial longitude"``
   - ``"013 Sub-observer latitude & rotating longitude"``
   - ``"014 Sub-solar latitude & rotating longitude"``
   - ``"015 [Planet] RA & Dec"``
   - ``"016 Earth RA & Dec"``
   - ``"017 Sun RA & Dec"``
   - ``"019 [Planet] projected equatorial radius"`` (deg)

   Note: ``[Planet]`` is replaced by the actual planet name (Mars,
   Jupiter, Saturn, Uranus, Neptune, Pluto) in each form.

Moon Columns
~~~~~~~~~~~~

``mooncols`` (checkbox, multi-valued)
   Moon column selection checkboxes.  The leading three-digit number is
   the column ID.  Multiple values are joined with ``#`` by ``newcgi.pm``.

   Earth-based (PREFIX empty):

   - ``"003 Sub-observer latitude & rotating longitude"``
   - ``"004 Sub-solar latitude & rotating longitude"``
   - ``"005 RA & Dec"``
   - ``"006 Offset RA & Dec from the moon"`` (arcsec)
   - ``"008 Orbital longitude relative to observer"``
   - ``"009 Orbit plane opening angle to observer"``

   Spacecraft-based (PREFIX set):

   - ``"001 Observer-moon distance"``
   - ``"002 Moon phase angle"``
   - ``"003 Sub-observer latitude & rotating longitude"``
   - ``"004 Sub-solar latitude & rotating longitude"``
   - ``"005 RA & Dec"``
   - ``"007 Offset RA & Dec from the moon"`` (deg)
   - ``"008 Orbital longitude relative to observer"``
   - ``"009 Orbit plane opening angle to observer"``

Moon Selection
~~~~~~~~~~~~~~

``moons`` (checkbox, multi-valued)
   Individual moon checkboxes.  Identical to the Tracker moon selection
   (see Tracker Parameters > Moon Selection above for the complete list
   per planet).
