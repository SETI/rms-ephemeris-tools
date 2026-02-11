"""Draw one body (EUBODY)."""

from __future__ import annotations

import math

from ephemeris_tools.rendering.escher import (
    EscherState,
    EscherViewState,
    esdraw,
    esdump,
)
from ephemeris_tools.rendering.euclid.constants import _PI, LIMFOV, STDSEG
from ephemeris_tools.rendering.euclid.ellipse import _arderd, _asort, _ovrlap, _plpnts
from ephemeris_tools.rendering.euclid.segment_plane import (
    _euskip,
    _fovclp,
    _plelsg,
    _smside,
)
from ephemeris_tools.rendering.euclid.state import EuclidState
from ephemeris_tools.rendering.euclid.vec_math import (
    Vec3,
    _opsgnd,
    _v3t,
    _vadd,
    _vdot,
    _vequ,
    _vhat,
    _vlcom,
    _vnorm,
    _vscl,
    _vsub,
)


def eubody(
    body: int,
    merids: int,
    latcir: int,
    srcreq: int,
    bright: int,
    dark: int,
    term: int,
    euclid_state: EuclidState,
    view_state: EscherViewState,
    escher_state: EscherState,
) -> None:
    """Draw one body (port of EUBODY)."""
    st = euclid_state
    bi = body - 1  # 0-based index

    if bi < 0 or bi >= st.nbody:
        return
    if not st.cansee[bi]:
        return

    # Check FOV overlap
    intsec = _ovrlap(st.lcentr[bi], st.biga[bi], st.fovcen, st.fovrad)
    if intsec == 0:
        return

    # Find candidate occulting bodies
    occltd = False
    bodyd = _vnorm(st.centrs[bi])
    fbodyd = bodyd + st.biga[bi]
    nbodyd = bodyd - st.biga[bi]
    nocand = 0
    ocands: list[int] = []

    i = 0
    while i < st.nbody and not occltd:
        if i != bi and st.cansee[i]:
            near = _vnorm(st.centrs[i]) - st.biga[i]
            if near < fbodyd:
                intsec = _ovrlap(
                    st.lcentr[bi],
                    st.biga[bi],
                    st.lcentr[i],
                    st.biga[i],
                )
                if intsec > 1:
                    ocands.append(i)
                    nocand += 1
                elif intsec == 1:
                    ocands.append(i)
                    nocand += 1
                    if _vnorm(st.centrs[i]) < nbodyd:
                        intsec2 = _ovrlap(
                            st.lcentr[bi],
                            st.biga[bi],
                            st.centrs[i],
                            st.smalla[i],
                        )
                        occltd = intsec2 == 1
        i += 1

    if occltd:
        return

    # NOVIEW check
    intsec = _ovrlap(
        st.lcentr[bi],
        st.biga[bi],
        st.kaxis,
        math.tan(LIMFOV),
    )
    noview = intsec != 1

    # Unit vectors along body axes
    tempv1 = _vhat(st.prnpls[bi][0])
    tempv2 = _vhat(st.prnpls[bi][1])
    tempv3 = _vhat(st.prnpls[bi][2])

    # Set up planes array
    planes = 0
    fplans = 0
    pnorml: list[Vec3] = []
    pmajor: list[Vec3] = []
    pminor: list[Vec3] = []
    pcentr: list[Vec3] = []
    tsrce: list[int] = []

    # First: limb plane
    pnorml.append(_vequ(st.lnorml[bi]))
    pmajor.append(_vequ(st.lmajor[bi]))
    pminor.append(_vequ(st.lminor[bi]))
    pcentr.append(_vequ(st.lcentr[bi]))
    tsrce.append(0)
    planes = 1
    fplans = 1

    # Terminator planes
    for lsrce in range(st.nlight):
        if st.canecl[bi][lsrce]:
            pnorml.append(_vequ(st.tnorml[bi][lsrce]))
            pmajor.append(_vequ(st.tmajor[bi][lsrce]))
            pminor.append(_vequ(st.tminor[bi][lsrce]))
            pcentr.append(_vequ(st.tcentr[bi][lsrce]))
            tsrce.append(lsrce + 1)  # 1-based light source index
            planes += 1
            fplans += 1

    # Meridian planes
    if merids > 0:
        basesn = math.sin(_PI / float(merids))
        basecs = math.cos(_PI / float(merids))
        cosang = 1.0
        sinang = 0.0
        a2 = st.a[bi][0] ** 2
        b2 = st.a[bi][1] ** 2
        num_v = a2 * b2
        denom_v = a2 * sinang * sinang + b2 * cosang * cosang

        for _ in range(merids):
            n = _vlcom(-sinang, tempv1, cosang, tempv2)
            mj = _vlcom(cosang, tempv1, sinang, tempv2)
            if denom_v > 0.0:
                t = math.sqrt(num_v / denom_v)
            else:
                t = 1.0
            mj = _vscl(t, mj)
            mi = _vequ(st.prnpls[bi][2])
            ct = _vequ(st.centrs[bi])
            pnorml.append(n)
            pmajor.append(mj)
            pminor.append(mi)
            pcentr.append(ct)
            tsrce.append(0)
            planes += 1

            x = cosang
            y = sinang
            sinang = y * basecs + x * basesn
            cosang = x * basecs - y * basesn
            denom_v = a2 * sinang * sinang + b2 * cosang * cosang

    # Latitude planes
    if latcir > 0:
        basesn = math.sin(_PI / float(latcir + 1))
        basecs = math.cos(_PI / float(latcir + 1))
        cosang = basesn
        sinang = -basecs
        a2 = st.a[bi][0] ** 2
        c2 = st.a[bi][2] ** 2
        ab = st.a[bi][0] * st.a[bi][1]

        for _ in range(latcir):
            if cosang == 0.0:
                cosang = 1e-30
            tanang = sinang / cosang
            num_v = c2 * tanang
            factor_sq = a2 + num_v * tanang
            if factor_sq > 0.0:
                factor = 1.0 / math.sqrt(factor_sq)
            else:
                factor = 1.0
            z = num_v * factor
            xv = a2 * factor
            yv = ab * factor

            mj = _vscl(xv, tempv1)
            mi = _vscl(yv, tempv2)
            ct_off = _vscl(z, tempv3)
            ct = _vadd(st.centrs[bi], ct_off)
            pnorml.append(_vequ(tempv3))
            pmajor.append(mj)
            pminor.append(mi)
            pcentr.append(ct)
            tsrce.append(0)
            planes += 1

            x = cosang
            y = sinang
            sinang = y * basecs + x * basesn
            cosang = x * basecs - y * basesn

    # Compute plane constants
    pconst: list[float] = []
    for i in range(planes):
        pconst.append(_vdot(pcentr[i], pnorml[i]))

    # Find eclipse candidates
    npsecl = 0
    ndfecl = 0
    drkreq = 1 + st.nlight - srcreq

    necand: list[int] = [0] * st.nlight
    ecands: list[list[int]] = [[] for _ in range(st.nlight)]
    eclpsd: list[bool] = [False] * st.nlight

    for j in range(st.nlight):
        srcbod = _vsub(st.centrs[bi], st.lights[j])
        bodyd_j = _vnorm(srcbod)
        fbodyd_j = bodyd_j + st.biga[bi]
        nbodyd_j = bodyd_j - st.biga[bi]
        necand[j] = 0
        eclpsd[j] = False

        i = 0
        while i < st.nbody and not eclpsd[j]:
            if i != bi and st.canecl[i][j]:
                canbod = _vsub(st.centrs[i], st.lights[j])
                if _vnorm(canbod) - st.biga[i] < fbodyd_j:
                    canbod2 = _vsub(st.tcentr[i][j], st.vertex[i][j])
                    eclbod = _vsub(st.centrs[bi], st.vertex[i][j])
                    x = st.biga[bi] / _vnorm(eclbod) if _vnorm(eclbod) > 0 else 1.0
                    x = 1.0 - x * x
                    if x <= 0.0:
                        ecands[j].append(i)
                        necand[j] += 1
                    else:
                        eclbod_s = _vscl(x, eclbod)
                        intsec = _ovrlap(eclbod_s, st.biga[bi], canbod2, st.biga[i])
                        if intsec > 1:
                            ecands[j].append(i)
                            necand[j] += 1
                        elif intsec == 1:
                            ecands[j].append(i)
                            necand[j] += 1
                            canbod3 = _vsub(st.centrs[i], st.lights[j])
                            if _vnorm(canbod3) + st.smalla[i] < nbodyd_j:
                                canbod4 = _vsub(st.centrs[i], st.vertex[i][j])
                                intsec2 = _ovrlap(
                                    eclbod_s,
                                    st.biga[bi],
                                    canbod4,
                                    st.smalla[i],
                                )
                                eclpsd[j] = intsec2 == 1
            i += 1

        if necand[j] > 0:
            npsecl += 1
        if eclpsd[j]:
            ndfecl += 1

    # Compute skip count
    skip = _euskip(st.biga[bi], st.centrs[bi], st.fovrad)

    # Process each ellipse
    solve = [True] * planes

    for ellpse in range(planes):
        solve[ellpse] = False

        # Find intersections with other planes
        coeffx, coeffy, meetns = _plpnts(
            pmajor[ellpse],
            pminor[ellpse],
            pcentr[ellpse],
            pnorml,
            pconst,
            planes,
            solve,
        )

        # Update solve array
        if ellpse < fplans - 1:
            solve[ellpse] = True
        elif ellpse == fplans - 1:
            solve[ellpse] = True
            for idx in range(ellpse + 1, planes):
                solve[idx] = False

        # Sort intersection points
        if meetns > 0:
            _asort(coeffx, coeffy, meetns)

        # Generate segments from this ellipse
        segno = 0
        nxtstd = skip
        nxtaux = 0

        begcan = _vadd(pmajor[ellpse], pcentr[ellpse])

        # Determine visibility relative to limb
        if ellpse > 0:
            vuside = -pconst[0]
            x = -pconst[0] + _vdot(begcan, pnorml[0])
            begvis = not _opsgnd(x, vuside)
        else:
            begvis = True
            endvis = True

        begseg_list: list[Vec3] = []
        endseg_list: list[Vec3] = []

        # Merge standard and auxiliary endpoints
        while nxtstd <= STDSEG - 1 and nxtaux < meetns:
            if _arderd(st.stdcos[nxtstd], st.stdsin[nxtstd], coeffx[nxtaux], coeffy[nxtaux]):
                cosang_v = st.stdcos[nxtstd]
                sinang_v = st.stdsin[nxtstd]
                nxtstd += skip
            else:
                cosang_v = coeffx[nxtaux]
                sinang_v = coeffy[nxtaux]
                nxtaux += 1

            endcan = _vadd(
                _vlcom(cosang_v, pmajor[ellpse], sinang_v, pminor[ellpse]),
                pcentr[ellpse],
            )

            if ellpse > 0:
                x = _vdot(endcan, st.lnorml[bi]) - pconst[0]
                endvis = not _opsgnd(x, vuside)
            else:
                endvis = True

            if endvis and begvis:
                segno += 1
                begseg_list.append(_vequ(begcan))
                endseg_list.append(_vequ(endcan))

            if ellpse == 0:
                pass  # limb point tracking omitted (not needed for PS output)

            begcan = _vequ(endcan)
            begvis = endvis

        # Remaining endpoints
        moresg = True
        while moresg:
            if nxtstd <= STDSEG - 1:
                cosang_v = st.stdcos[nxtstd]
                sinang_v = st.stdsin[nxtstd]
                nxtstd += skip
            elif nxtaux < meetns:
                cosang_v = coeffx[nxtaux]
                sinang_v = coeffy[nxtaux]
                nxtaux += 1
            else:
                cosang_v = 1.0
                sinang_v = 0.0
                moresg = False

            endcan = _vadd(
                _vlcom(cosang_v, pmajor[ellpse], sinang_v, pminor[ellpse]),
                pcentr[ellpse],
            )

            if ellpse > 0:
                x = _vdot(endcan, st.lnorml[bi]) - pconst[0]
                endvis = not _opsgnd(x, vuside)

            if endvis and begvis:
                segno += 1
                begseg_list.append(_vequ(begcan))
                endseg_list.append(_vequ(endcan))

            begcan = _vequ(endcan)
            begvis = endvis

        numseg = segno

        # Check occultation by other bodies
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
                j_occ = ocands[oi]
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

        # Determine shadow/illumination
        bright_segs: list[Vec3] = []
        bright_ends: list[Vec3] = []

        for si in range(numseg):
            bc = _vequ(begseg_list[si])
            ec = _vequ(endseg_list[si])

            ndark_v = 0
            nillum = 0

            ls = 0
            unknwn = ls < st.nlight
            while unknwn:
                if tsrce[ellpse] != ls + 1:
                    if _smside(bc, ec, st.tnorml[bi][ls], st.tcentr[bi][ls], st.lights[ls]):
                        nillum += 1
                    else:
                        ndark_v += 1
                else:
                    ndark_v += 1
                ls += 1

                if ellpse == 0 or ellpse >= fplans:
                    unknwn = nillum < srcreq and ndark_v < drkreq
                else:
                    unknwn = nillum < srcreq and ls < st.nlight

            if ellpse == 0 or ellpse >= fplans:
                if ndark_v == drkreq:
                    if noview:
                        bc, ec = _fovclp(bc, ec, st.cosfov)
                    esdraw(_v3t(bc), _v3t(ec), dark, view_state, escher_state)
                else:
                    bright_segs.append(bc)
                    bright_ends.append(ec)
            else:
                if ndark_v == drkreq and nillum == srcreq - 1:
                    if noview:
                        bc, ec = _fovclp(bc, ec, st.cosfov)
                    esdraw(_v3t(bc), _v3t(ec), term, view_state, escher_state)

        # Eclipse checks on remaining bright segments
        numseg_b = len(bright_segs)

        if ndfecl >= drkreq:
            for si in range(numseg_b):
                bc = bright_segs[si]
                ec = bright_ends[si]
                if noview:
                    bc, ec = _fovclp(bc, ec, st.cosfov)
                esdraw(_v3t(bc), _v3t(ec), dark, view_state, escher_state)
            numseg_b = 0

        if npsecl == 0 and numseg_b > 0:
            for si in range(numseg_b):
                bc = bright_segs[si]
                ec = bright_ends[si]
                if noview:
                    bc, ec = _fovclp(bc, ec, st.cosfov)
                esdraw(_v3t(bc), _v3t(ec), bright, view_state, escher_state)
            numseg_b = 0

        # Per-segment eclipse check
        si = 0
        while si < numseg_b:
            bc = _vequ(bright_segs[si])
            ec = _vequ(bright_ends[si])

            lsrce = 0
            nillum = 0
            ndark_v = 0
            notecl = ndark_v < drkreq
            notlit = nillum < srcreq

            while lsrce < st.nlight and notecl and notlit:
                curdrk = ndark_v
                unknwn2 = True

                if st.canecl[bi][lsrce] and not _smside(
                    bc, ec, st.tnorml[bi][lsrce], st.tcentr[bi][lsrce], st.lights[lsrce]
                ):
                    ndark_v += 1
                    unknwn2 = False

                j2 = 0
                notecl = ndark_v < drkreq
                notlit = nillum < srcreq
                unknwn2 = unknwn2 and notecl and notlit and (j2 < necand[lsrce])

                while unknwn2:
                    k = ecands[lsrce][j2]
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
                            bright_segs.append(_vequ(bsub[sub]))
                            bright_ends.append(_vequ(esub[sub]))
                            numseg_b += 1

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
                    unknwn2 = unknwn2 and (j2 < necand[lsrce])
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

    # Flush segment buffer
    esdump(view_state, escher_state)
