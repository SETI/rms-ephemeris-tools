"""Draw ring ellipse (EURING)."""

from __future__ import annotations

import math

from ephemeris_tools.rendering.escher import (
    EscherState,
    EscherViewState,
    esdraw,
    esdump,
)
from ephemeris_tools.rendering.euclid.constants import LIMFOV, STDSEG
from ephemeris_tools.rendering.euclid.ellipse import _ovrlap
from ephemeris_tools.rendering.euclid.init_geom import euinit
from ephemeris_tools.rendering.euclid.segment_plane import (
    _euskip,
    _fovclp,
    _plelsg,
    _smside,
)
from ephemeris_tools.rendering.euclid.state import EuclidState
from ephemeris_tools.rendering.euclid.vec_math import (
    Vec3,
    _mtxv,
    _v3t,
    _vadd,
    _vequ,
    _vlcom,
    _vnorm,
    _vscl,
    _vsub,
)


def euring(
    ring_center: Vec3,
    major: Vec3,
    minor: Vec3,
    srcreq: int,
    bright: int,
    dark: int,
    euclid_state: EuclidState,
    view_state: EscherViewState,
    escher_state: EscherState,
) -> None:
    """Draw an elliptical ring (port of EURING).

    Ring is a curve only; it does not cast shadows. Lit and dark portions use
    the given color codes. MAJOR and MINOR are assumed orthogonal (semi-axes).

    Parameters:
        ring_center: Center of the ring (e.g. planet center).
        major: Semi-major axis vector (direction and length).
        minor: Semi-minor axis vector (direction and length).
        srcreq: Number of light sources required to consider a point lit.
        bright: Color code for lit portion.
        dark: Color code for unlit portion.
        euclid_state: Euclid state (from eugeom/euview).
        view_state: Escher view state.
        escher_state: Escher output state.
    """
    st = euclid_state
    if not st.initialized:
        euinit(st)

    # Transform ring to camera frame
    rcentr = _vsub(ring_center, st.obsrvr)
    rcentr = _mtxv(st.camera, rcentr)
    rmajor = _mtxv(st.camera, major)
    rminor = _mtxv(st.camera, minor)

    largst = _vnorm(rmajor)
    intsec = _ovrlap(rcentr, largst, st.fovcen, st.fovrad)
    if intsec == 0:
        return

    # Find candidate occulting bodies
    occltd = False
    ringd = _vnorm(rcentr)
    fringd = ringd + largst
    nringd = ringd - largst

    x = largst / _vnorm(rcentr) if _vnorm(rcentr) > 0 else 1.0
    x = 1.0 - x * x
    occrng = _vscl(x, rcentr)

    nocand = 0
    ocands_r: list[int] = []

    i = 0
    while i < st.nbody and not occltd:
        near = _vnorm(st.centrs[i]) - st.biga[i]
        if st.cansee[i] and near < fringd:
            if x <= 0.0:
                ocands_r.append(i)
                nocand += 1
            else:
                intsec = _ovrlap(occrng, largst, st.lcentr[i], st.biga[i])
                if intsec > 1:
                    ocands_r.append(i)
                    nocand += 1
                elif intsec == 1:
                    ocands_r.append(i)
                    nocand += 1
                    if _vnorm(st.centrs[i]) + st.smalla[i] < nringd:
                        intsec2 = _ovrlap(
                            occrng,
                            largst,
                            st.centrs[i],
                            st.smalla[i],
                        )
                        occltd = intsec2 == 1
        i += 1

    if occltd:
        return

    # NOVIEW check
    if x < 0.0:
        noview = True
    else:
        intsec = _ovrlap(rcentr, largst, st.kaxis, math.tan(LIMFOV))
        noview = intsec != 1

    # Eclipse candidates
    drkreq = 1 + st.nlight - srcreq
    npsecl = 0
    ndfecl = 0
    necand_r: list[int] = [0] * st.nlight
    ecands_r: list[list[int]] = [[] for _ in range(st.nlight)]
    eclpsd_r: list[bool] = [False] * st.nlight

    for j in range(st.nlight):
        srcrng = _vsub(rcentr, st.lights[j])
        ringd_j = _vnorm(srcrng)
        fringd_j = ringd_j + largst
        nringd_j = ringd_j - largst
        necand_r[j] = 0
        eclpsd_r[j] = False

        i = 0
        while i < st.nbody and not eclpsd_r[j]:
            canbod = _vsub(st.centrs[i], st.lights[j])
            if st.canecl[i][j] and _vnorm(canbod) - st.biga[i] < fringd_j:
                canbod2 = _vsub(st.tcentr[i][j], st.vertex[i][j])
                eclrng = _vsub(rcentr, st.vertex[i][j])
                xv = largst / _vnorm(eclrng) if _vnorm(eclrng) > 0 else 1.0
                xv = 1.0 - xv * xv
                if xv <= 0.0:
                    ecands_r[j].append(i)
                    necand_r[j] += 1
                else:
                    eclrng_s = _vscl(xv, eclrng)
                    intsec = _ovrlap(eclrng_s, largst, canbod2, st.biga[i])
                    if intsec > 1:
                        ecands_r[j].append(i)
                        necand_r[j] += 1
                    elif intsec == 1:
                        ecands_r[j].append(i)
                        necand_r[j] += 1
                        canbod3 = _vsub(st.centrs[i], st.lights[j])
                        if _vnorm(canbod3) + st.smalla[i] < nringd_j:
                            canbod4 = _vsub(st.centrs[i], st.vertex[i][j])
                            intsec2 = _ovrlap(eclrng_s, largst, canbod4, st.smalla[i])
                            eclpsd_r[j] = intsec2 == 1
            i += 1

        if necand_r[j] > 0:
            npsecl += 1
        if eclpsd_r[j]:
            ndfecl += 1

    # Generate ring segments
    skip = _euskip(largst, rcentr, st.fovrad)

    begseg_list: list[Vec3] = [_vadd(rcentr, rmajor)]
    endseg_list: list[Vec3] = []

    nxtstd = skip
    segno = 0
    while nxtstd < STDSEG:
        cosang_v = st.stdcos[nxtstd]
        sinang_v = st.stdsin[nxtstd]
        endpt = _vadd(rcentr, _vlcom(cosang_v, rmajor, sinang_v, rminor))
        endseg_list.append(endpt)
        segno += 1
        begseg_list.append(_vequ(endpt))
        nxtstd += skip

    # Close the ring
    endseg_list.append(_vadd(rcentr, rmajor))
    segno += 1
    numseg = segno

    # Remove extra begin entry
    begseg_list = begseg_list[:numseg]

    # Check occultation
    vupnt_occ: Vec3 = [0.0, 0.0, 0.0]
    kept_beg: list[Vec3] = []
    kept_end: list[Vec3] = []

    si = 0
    while si < len(begseg_list):
        bc = _vequ(begseg_list[si])
        ec = _vequ(endseg_list[si])
        savseg = True

        oi = 0
        while oi < nocand and savseg:
            j_occ = ocands_r[oi]
            bsub, esub, ins, inb, ns = _plelsg(
                bc,
                ec,
                st.lnorml[j_occ],
                st.lmajor[j_occ],
                st.lminor[j_occ],
                st.lcentr[j_occ],
                vupnt_occ,
            )

            sub = 0
            while sub < ns and inb[sub] and ins[sub]:
                sub += 1

            if sub < ns:
                bc = _vequ(bsub[sub])
                ec = _vequ(esub[sub])
                sub += 1
            else:
                savseg = False

            while sub < ns:
                if not (inb[sub] and ins[sub]):
                    begseg_list.append(_vequ(bsub[sub]))
                    endseg_list.append(_vequ(esub[sub]))
                sub += 1
            oi += 1

        if savseg:
            kept_beg.append(bc)
            kept_end.append(ec)
        si += 1

    begseg_list = kept_beg
    endseg_list = kept_end
    numseg = len(begseg_list)

    # Eclipse checks
    if ndfecl >= drkreq:
        for si in range(numseg):
            bc = begseg_list[si]
            ec = endseg_list[si]
            if noview:
                bc, ec = _fovclp(bc, ec, st.cosfov)
            esdraw(_v3t(bc), _v3t(ec), dark, view_state, escher_state)
        numseg = 0

    if npsecl == 0 and numseg > 0:
        for si in range(numseg):
            bc = begseg_list[si]
            ec = endseg_list[si]
            if noview:
                bc, ec = _fovclp(bc, ec, st.cosfov)
            esdraw(_v3t(bc), _v3t(ec), bright, view_state, escher_state)
        numseg = 0

    # Per-segment eclipse check
    si = 0
    while si < numseg:
        bc = _vequ(begseg_list[si])
        ec = _vequ(endseg_list[si])

        lsrce = 0
        nillum = 0
        ndark_v = 0
        notecl = True
        notlit = True

        while lsrce < st.nlight and notecl and notlit:
            curdrk = ndark_v
            unknwn2 = True

            j2 = 0
            notecl = ndark_v < drkreq
            notlit = nillum < srcreq
            unknwn2 = unknwn2 and notecl and notlit and (j2 < necand_r[lsrce])

            while unknwn2:
                k = ecands_r[lsrce][j2]
                bsub, esub, ins, inb, ns = _plelsg(
                    bc,
                    ec,
                    st.tnorml[k][lsrce],
                    st.tmajor[k][lsrce],
                    st.tminor[k][lsrce],
                    st.tcentr[k][lsrce],
                    st.vertex[k][lsrce],
                )
                if ns > 1:
                    bc = _vequ(bsub[0])
                    ec = _vequ(esub[0])
                    for sub in range(1, ns):
                        begseg_list.append(_vequ(bsub[sub]))
                        endseg_list.append(_vequ(esub[sub]))
                        numseg += 1

                if (
                    ns >= 1
                    and ins[0]
                    and not _smside(
                        bc, ec, st.tnorml[k][lsrce], st.tcentr[k][lsrce], st.lights[lsrce]
                    )
                ):
                    ndark_v += 1
                    unknwn2 = False

                j2 += 1
                unknwn2 = unknwn2 and (j2 < necand_r[lsrce])
                notecl = ndark_v < drkreq

            if curdrk == ndark_v:
                nillum += 1
            notlit = nillum < srcreq
            lsrce += 1

        if notecl:
            if noview:
                bc, ec = _fovclp(bc, ec, st.cosfov)
            esdraw(_v3t(bc), _v3t(ec), bright, view_state, escher_state)
        else:
            if noview:
                bc, ec = _fovclp(bc, ec, st.cosfov)
            esdraw(_v3t(bc), _v3t(ec), dark, view_state, escher_state)

        si += 1

    esdump(view_state, escher_state)
