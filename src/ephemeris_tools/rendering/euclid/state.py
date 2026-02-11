"""Euclid geometry and view state (FORTRAN saved variables)."""

from __future__ import annotations

from ephemeris_tools.rendering.euclid.constants import STDSEG
from ephemeris_tools.rendering.euclid.vec_math import Vec3


class EuclidState:
    """Geometry and view state for Euclid (replaces FORTRAN saved variables)."""

    def __init__(self) -> None:
        self.device = 0
        self.view = (0.0, 0.0, 0.0, 0.0)
        self.fov = (0.0, 0.0, 0.0, 0.0)
        # Initialized by euinit
        self.stdcos: list[float] = [0.0] * (STDSEG + 1)
        self.stdsin: list[float] = [0.0] * (STDSEG + 1)
        self.cosfov = 0.0
        self.kaxis: Vec3 = [0.0, 0.0, 1.0]
        self.initialized = False
        # EUVIEW state
        self.fovcen: Vec3 = [0.0, 0.0, 1.0]
        self.fovrad = 0.0
        self.dspdev = 0
        # EUGEOM state
        self.nlight = 0
        self.nbody = 0
        self.radii: list[float] = []
        self.lights: list[Vec3] = []
        self.obsrvr: Vec3 = [0.0, 0.0, 0.0]
        self.camera: list[Vec3] = [[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]
        self.centrs: list[Vec3] = []
        self.prnpls: list[list[Vec3]] = []  # prnpls[body][axis] = Vec3
        self.a: list[Vec3] = []  # axis lengths a[body] = [a1, a2, a3]
        self.biga: list[float] = []
        self.smalla: list[float] = []
        self.lnorml: list[Vec3] = []
        self.lmajor: list[Vec3] = []
        self.lminor: list[Vec3] = []
        self.lcentr: list[Vec3] = []
        self.cansee: list[bool] = []
        self.tnorml: list[list[Vec3]] = []  # tnorml[body][lsrce]
        self.tmajor: list[list[Vec3]] = []
        self.tminor: list[list[Vec3]] = []
        self.tcentr: list[list[Vec3]] = []
        self.vertex: list[list[Vec3]] = []
        self.ecaxis: list[list[Vec3]] = []
        self.canecl: list[list[bool]] = []  # canecl[body][lsrce]
