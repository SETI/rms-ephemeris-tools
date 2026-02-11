"""Euclid init, view, and geometry (EUINIT, EUVIEW, EUGEOM)."""

from __future__ import annotations

import math

from ephemeris_tools.rendering.escher import (
    EscherState,
    EscherViewState,
    esview,
)
from ephemeris_tools.rendering.euclid.constants import _PI, LIMFOV, STDSEG
from ephemeris_tools.rendering.euclid.ellipse import _eclpmd, _ellips
from ephemeris_tools.rendering.euclid.state import EuclidState
from ephemeris_tools.rendering.euclid.vec_math import (
    Vec3,
    _mtxv,
    _vdot,
    _vequ,
    _vhat,
    _vnorm,
    _vsub,
)


def euinit(state: EuclidState) -> None:
    """Initialize Euclid: compute trig tables and constants (port of EUINIT).

    Call once before any other Euclid entry points. Repeated calls have no
    effect after the first.

    Parameters:
        state: EuclidState to initialize (modified in place).
    """
    angle = 2.0 * _PI / float(STDSEG)
    q4 = STDSEG // 4  # 24
    state.stdcos[q4] = 0.0
    state.stdsin[q4] = 1.0

    q8 = STDSEG // 8  # 12
    for i in range(1, q8 + 1):
        state.stdcos[i] = math.cos(float(i) * angle)
        state.stdsin[i] = math.sin(float(i) * angle)

    for i in range(q8 + 1, q4):
        state.stdsin[i] = state.stdcos[q4 - i]
        state.stdcos[i] = state.stdsin[q4 - i]

    j = 1
    for i in range(q4 + 1, STDSEG + 1):
        state.stdcos[i] = -state.stdsin[j]
        state.stdsin[i] = state.stdcos[j]
        j += 1

    state.kaxis = [0.0, 0.0, 1.0]
    state.cosfov = math.cos(LIMFOV)
    state.initialized = True


def euview(
    device: int,
    h1: float,
    h2: float,
    v1: float,
    v2: float,
    x1: float,
    x2: float,
    y1: float,
    y2: float,
    euclid_state: EuclidState,
    view_state: EscherViewState,
    escher_state: EscherState,
) -> None:
    """Set display region and field of view (port of EUVIEW).

    Describes where the image goes (device, h1-h2, v1-v2) and what portion
    of the image plane is displayed (x1-x2, y1-y2). Image plane is at
    distance 1 from pinhole; e.g. x1=-tan(A/2), x2=tan(A/2) for FOV A radians.

    Parameters:
        device: Display device number recognized by Escher.
        h1, h2: Horizontal limits of display region.
        v1, v2: Vertical limits of display region.
        x1, x2: x-coordinate bounds in image plane.
        y1, y2: y-coordinate bounds in image plane.
        euclid_state: Euclid state (initialized if needed).
        view_state: Escher view state (updated).
        escher_state: Escher output state (updated).
    """
    if not euclid_state.initialized:
        euinit(euclid_state)

    # Compute corner directions
    corners = [
        _vhat([-x1, -y1, 1.0]),
        _vhat([-x1, -y2, 1.0]),
        _vhat([-x2, -y1, 1.0]),
        _vhat([-x2, -y2, 1.0]),
    ]

    fovcen = _vhat([-0.5 * (x1 + x2), -0.5 * (y1 + y2), 1.0])
    mincos = 2.0
    cosang = 0.0
    for c in corners:
        cosang = _vdot(c, fovcen)
        if cosang < mincos:
            mincos = cosang

    if cosang <= 0.001:
        mincos = 2.0
        for c in corners:
            if c[2] < mincos:
                mincos = c[2]
        fovcen = [0.0, 0.0, 1.0]

    euclid_state.fovrad = math.sqrt(1.0 - mincos * mincos) / mincos
    euclid_state.fovcen = fovcen
    euclid_state.dspdev = device
    euclid_state.device = device
    euclid_state.view = (h1, h2, v1, v2)
    euclid_state.fov = (x1, x2, y1, y2)

    view = (h1, h2, v1, v2)
    fov = (x1, x2, y1, y2)
    esview(device, view, fov, view_state, escher_state)


def eugeom(
    nlites: int,
    source: list[Vec3],
    srcrad: list[float],
    obsrve: Vec3,
    camfrm: list[Vec3],
    nbods: int,
    bodies: list[Vec3],
    axes: list[list[Vec3]],
    euclid_state: EuclidState,
) -> None:
    """Set scene geometry: lights, camera, bodies; compute limbs/terminators (port of EUGEOM).

    Defines illumination sources (positions and radii), camera position and
    orientation (obsrve, camfrm), and ellipsoid bodies (positions and principal
    axes). Computes limb ellipses and terminator/eclipse geometry per body/light.

    Parameters:
        nlites: Number of light sources.
        source: Light positions (list of 3-vectors).
        srcrad: Light radii.
        obsrve: Camera (pinhole) position.
        camfrm: 3x3 camera frame (columns = x, y, z in image plane and toward scene).
        nbods: Number of bodies.
        bodies: Body center positions.
        axes: Body principal axes; axes[i][j] is j-th axis of body i (length = semi-axis).
        euclid_state: Euclid state (modified in place).
    """
    if not euclid_state.initialized:
        euinit(euclid_state)

    st = euclid_state
    st.nlight = nlites
    st.nbody = nbods
    st.radii = srcrad[:nlites]
    st.obsrvr = _vequ(obsrve)
    st.camera = [_vequ(camfrm[i]) for i in range(3)]

    # Translate to camera-centered frame, rotate to camera frame
    st.centrs = []
    st.prnpls = []
    for i in range(nbods):
        cv = _vsub(bodies[i], obsrve)
        st.centrs.append(_mtxv(camfrm, cv))
        body_axes: list[Vec3] = []
        for j in range(3):
            body_axes.append(_mtxv(camfrm, axes[i][j]))
        st.prnpls.append(body_axes)

    st.lights = []
    for i in range(nlites):
        lv = _vsub(source[i], obsrve)
        st.lights.append(_mtxv(camfrm, lv))

    # Axis lengths
    st.a = []
    st.biga = []
    st.smalla = []
    for i in range(nbods):
        a1 = _vnorm(st.prnpls[i][0])
        a2 = _vnorm(st.prnpls[i][1])
        a3 = _vnorm(st.prnpls[i][2])
        st.a.append([a1, a2, a3])
        st.biga.append(max(a1, a2, a3))
        st.smalla.append(min(a1, a2, a3))

    # Limb ellipses
    vupnt: Vec3 = [0.0, 0.0, 0.0]
    st.lnorml = []
    st.lmajor = []
    st.lminor = []
    st.lcentr = []
    st.cansee = []
    for i in range(nbods):
        normal, major, minor, midpnt, cs = _ellips(
            st.prnpls[i][0],
            st.prnpls[i][1],
            st.prnpls[i][2],
            st.centrs[i],
            vupnt,
        )
        st.lnorml.append(normal)
        st.lmajor.append(major)
        st.lminor.append(minor)
        st.lcentr.append(midpnt)
        st.cansee.append(cs)

    # Terminator planes and eclipse cones
    st.tnorml = [[[0.0, 0.0, 0.0] for _ in range(nlites)] for _ in range(nbods)]
    st.tmajor = [[[0.0, 0.0, 0.0] for _ in range(nlites)] for _ in range(nbods)]
    st.tminor = [[[0.0, 0.0, 0.0] for _ in range(nlites)] for _ in range(nbods)]
    st.tcentr = [[[0.0, 0.0, 0.0] for _ in range(nlites)] for _ in range(nbods)]
    st.vertex = [[[0.0, 0.0, 0.0] for _ in range(nlites)] for _ in range(nbods)]
    st.ecaxis = [[[0.0, 0.0, 0.0] for _ in range(nlites)] for _ in range(nbods)]
    st.canecl = [[False for _ in range(nlites)] for _ in range(nbods)]

    for j in range(nlites):
        for i in range(nbods):
            tn, tm, tmi, tc, vx, ca, ce = _eclpmd(
                st.prnpls[i][0],
                st.prnpls[i][1],
                st.prnpls[i][2],
                st.centrs[i],
                st.lights[j],
                srcrad[j],
            )
            st.tnorml[i][j] = tn
            st.tmajor[i][j] = tm
            st.tminor[i][j] = tmi
            st.tcentr[i][j] = tc
            st.vertex[i][j] = vx
            st.ecaxis[i][j] = ca
            st.canecl[i][j] = ce
