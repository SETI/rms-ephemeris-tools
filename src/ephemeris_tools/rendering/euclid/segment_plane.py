"""Segment-plane and FOV helpers (EUSKIP, FOVCLP, SMSIDE, PLELSG)."""

from __future__ import annotations

import math

from ephemeris_tools.rendering.euclid.vec_math import (
    Vec3,
    _brcktd,
    _dnint,
    _opsgnd,
    _smsgnd,
    _vdot,
    _vequ,
    _vhat,
    _vlcom,
    _vnorm,
    _vscl,
    _vsub,
)


def _euskip(major: float, center: Vec3, fovrad: float) -> int:
    """Determine how many segments to skip when drawing a circle (port of EUSKIP).

    Used to reduce segments for small circles in the FOV. Returns 1, 2, 3, 4, or 6.

    Parameters:
        major: Semi-major axis length.
        center: Center of circle (3-vector).
        fovrad: Field-of-view radius.

    Returns:
        Skip count (1 = draw every segment).
    """
    x = _vnorm(center)
    if x > 0.0 and fovrad > 0.0:
        ratio = major / (x * fovrad)
    else:
        ratio = 1.0
    if ratio > 0.2:
        return 1
    if ratio > 0.1:
        return 2
    if ratio > 0.04:
        return 3
    if ratio > 0.01:
        return 4
    return 6


def _fovclp(p: Vec3, q: Vec3, cosfov: float) -> tuple[Vec3, Vec3]:
    """Clip segment p-q to cone about z-axis (port of FOVCLP).

    Parameters:
        p: Start of segment.
        q: End of segment.
        cosfov: Cosine of half-angle of cone.

    Returns:
        Tuple of (clipped_start, clipped_end); both inside or on cone.
    """
    x = _vhat(p)
    y = _vhat(q)

    if x[2] >= cosfov and y[2] >= cosfov:
        return (_vequ(p), _vequ(q))

    cossqr = cosfov * cosfov
    qsubp = _vsub(q, p)

    c = p[2] * p[2] - cossqr * _vdot(p, p)
    b = p[2] * qsubp[2] - cossqr * _vdot(p, qsubp)
    a = qsubp[2] * qsubp[2] - cossqr * _vdot(qsubp, qsubp)

    discrm = b * b - a * c
    dump = False
    t_vals: list[float] = []

    if discrm <= 0.0:
        dump = True
    elif a == 0.0:
        if b != 0.0:
            t_vals.append(-c / b)
        else:
            dump = True
    else:
        sq = math.sqrt(discrm)
        t_vals.append((-b + sq) / a)
        t_vals.append((-b - sq) / a)

    # Keep only t in (0, 1)
    t_valid: list[float] = [t for t in t_vals if 0.0 < t < 1.0]

    if len(t_valid) == 0:
        dump = True

    if dump:
        sq = math.sqrt(1.0 - cossqr)
        pv = [sq, 0.0, cosfov]
        return (pv, _vequ(pv))

    pout = _vequ(p)
    qout = _vequ(q)

    if x[2] >= cosfov and y[2] < cosfov:
        s = min(t_valid) if len(t_valid) > 1 else t_valid[0]
        qout = _vlcom(1.0 - s, p, s, q)
    elif x[2] < cosfov and y[2] >= cosfov:
        s = max(t_valid) if len(t_valid) > 1 else t_valid[0]
        pout = _vlcom(1.0 - s, p, s, q)
    elif p[2] > 0.0 and q[2] > 0.0 and len(t_valid) >= 2:
        pout = _vlcom(1.0 - t_valid[0], p, t_valid[0], q)
        qout = _vlcom(1.0 - t_valid[1], p, t_valid[1], q)
    else:
        sq = math.sqrt(1.0 - cossqr)
        pout = [sq, 0.0, cosfov]
        qout = _vequ(pout)

    return (pout, qout)


def _smside(
    p: Vec3,
    q: Vec3,
    normal: Vec3,
    center: Vec3,
    refpnt: Vec3,
) -> bool:
    """Return True if segment p-q and refpnt are on the same side of the plane (port of SMSIDE).

    Plane: <normal, x> = <normal, center>.

    Parameters:
        p, q: Segment endpoints.
        normal: Plane normal.
        center: Point on plane.
        refpnt: Reference point.

    Returns:
        True if segment and refpnt are on same side of plane.
    """
    c = _vdot(center, normal)
    rfside = _vdot(refpnt, normal) - c
    pside = _vdot(p, normal) - c
    qside = _vdot(q, normal) - c

    testp = rfside * pside
    testq = rfside * qside

    if testp >= 0.0 and testq >= 0.0:
        return True
    if testp <= 0.0 and testq <= 0.0:
        return False

    small = min(abs(testp), abs(testq))
    if small == abs(testp):
        return testq >= 0.0
    return testp >= 0.0


def _plelsg(
    p: Vec3,
    q: Vec3,
    normal: Vec3,
    major: Vec3,
    minor: Vec3,
    center: Vec3,
    refpnt: Vec3,
) -> tuple[list[Vec3], list[Vec3], list[bool], list[bool], int]:
    """Project segment onto plane and find intersections with ellipse (port of PLELSG).

    Parameters:
        p, q: Segment endpoints.
        normal: Plane normal (ellipse lies in plane).
        major: Semi-major axis of ellipse.
        minor: Semi-minor axis of ellipse.
        center: Center of ellipse.
        refpnt: Reference point for plane.

    Returns:
        Tuple of (begsub_list, endsub_list, inside_list, inback_list, nsub):
        subsegment endpoints and flags, and number of subsegments.
    """
    quanta = 134217728.0  # 2^27

    pref = _vsub(p, refpnt)
    qref = _vsub(q, refpnt)
    cref = _vsub(center, refpnt)

    num = _vdot(normal, cref)
    denomp = _vdot(normal, pref)
    denomq = _vdot(normal, qref)

    aquad = _vdot(major, major)
    aquad = aquad * aquad
    bquad = _vdot(minor, minor)
    bquad = bquad * bquad

    # Determine behind flag
    if num != denomp:
        behind = _opsgnd(num - denomp, num)
    elif num != denomq:
        behind = _opsgnd(num - denomq, num)
    else:
        behind = False

    # Check if endpoints are on opposite sides of plane
    if _opsgnd(denomp - num, denomq - num):
        intsct = (num - denomp) / (denomq - denomp)
        intsct = _brcktd(intsct, 0.0, 1.0)
    else:
        intsct = 2.0

    # Maximum subsegments = 4
    max_sub = 5
    t_arr = [0.0] * (max_sub + 2)
    inelip = [False] * (max_sub + 2)
    subpnt = 1

    if not _smsgnd(denomp, denomq):
        # Some point projects to infinity
        tsub = 0.0
        tempp = denomp
        tempq = denomq
        if not _smsgnd(denomp, num):
            if denomp == 0.0:
                tsub = 0.5
            else:
                tint = denomp / (denomq - denomp)
                tsub = (1.0 + tint) * 0.5
            pref = _vlcom(1.0 - tsub, pref, tsub, qref)
            tempp = _vdot(normal, pref)
            tempq = denomq
        elif not _smsgnd(denomq, num):
            if denomq == 0.0:
                tsub = 0.5
            else:
                tint = denomp / (denomq - denomp)
                tsub = tint * 0.5
            qref = _vlcom(1.0 - tsub, pref, tsub, qref)
            tempp = denomp
            tempq = _vdot(normal, qref)
        else:
            # Fallback
            return ([_vequ(p)], [_vequ(q)], [False], [False], 1)

        if tempp == 0.0 or tempq == 0.0:
            return ([_vequ(p)], [_vequ(q)], [False], [False], 1)

        prjp = _vscl(num / tempp, pref)
        prjq = _vscl(num / tempq, qref)
        pc = _vsub(prjp, cref)
        qc = _vsub(prjq, cref)

        majorp = _vdot(major, pc)
        majorq = _vdot(major, qc)
        minorp = _vdot(minor, pc)
        minorq = _vdot(minor, qc)

        if aquad == 0.0 or bquad == 0.0:
            return ([_vequ(p)], [_vequ(q)], [False], [False], 1)

        insidp = (majorp * majorp / aquad) + (minorp * minorp / bquad)
        insidq = (majorq * majorq / aquad) + (minorq * minorq / bquad)

        alpha = (majorp - majorq) ** 2 / aquad + (minorp - minorq) ** 2 / bquad
        beta_v = majorp * (majorq - majorp) / aquad + minorp * (minorq - minorp) / bquad
        gamma_v = insidp - 1.0
        discrm = beta_v * beta_v - alpha * gamma_v

        cands = 0
        s_arr = [0.0, 0.0]
        if discrm > 0.0 and alpha != 0.0:
            sq = math.sqrt(discrm)
            cands = 2
            s_arr[0] = (-beta_v - sq) / alpha
            s_arr[1] = (-beta_v + sq) / alpha

        if cands != 0:
            for i in range(cands):
                a_v = s_arr[i] * tempp
                b_v = (1.0 - s_arr[i]) * tempq
                denom = b_v + a_v
                if denom != 0.0:
                    s_arr[i] = a_v / denom
                else:
                    s_arr[i] = 0.5

            if denomp <= 0.0:
                for i in range(cands):
                    t_arr[i + 2] = tsub + (1.0 - tsub) * s_arr[i]
            elif denomq <= 0.0:
                for i in range(cands):
                    t_arr[i + 2] = tsub * s_arr[i]

            if t_arr[2] > t_arr[3]:
                t_arr[2], t_arr[3] = t_arr[3], t_arr[2]

            inelip[1] = False
            if t_arr[2] > 0.0 and t_arr[3] < 1.0:
                subpnt += 2
                inelip[1] = False
                inelip[2] = True
                inelip[3] = False
            elif t_arr[2] <= 0.0:
                if 0.0 < t_arr[3] < 1.0:
                    subpnt += 1
                    t_arr[2] = t_arr[3]
                    if denomp * num <= 0.0:
                        inelip[1] = False
                        inelip[2] = True
                    else:
                        inelip[1] = True
                        inelip[2] = False
            elif t_arr[3] >= 1.0:
                if 0.0 < t_arr[2] < 1.0:
                    subpnt += 1
                    if denomp * num <= 0.0:
                        inelip[1] = False
                        inelip[2] = True
                    else:
                        inelip[1] = True
                        inelip[2] = False
        else:
            inelip[1] = False

    elif (num / denomp > 0.0 if denomp != 0.0 else False) and (
        num / denomq > 0.0 if denomq != 0.0 else False
    ):
        # Entire segment projects normally
        prjp = _vscl(num / denomp, pref)
        prjq = _vscl(num / denomq, qref)
        pc = _vsub(prjp, cref)
        qc = _vsub(prjq, cref)

        majorp = _vdot(major, pc)
        majorq = _vdot(major, qc)
        minorp = _vdot(minor, pc)
        minorq = _vdot(minor, qc)

        if aquad == 0.0 or bquad == 0.0:
            return ([_vequ(p)], [_vequ(q)], [False], [False], 1)

        insidp = (majorp * majorp / aquad) + (minorp * minorp / bquad)
        insidq = (majorq * majorq / aquad) + (minorq * minorq / bquad)

        if insidq <= 1.0 and insidp <= 1.0:
            inelip[1] = True
        else:
            alpha = (majorp - majorq) ** 2 / aquad + (minorp - minorq) ** 2 / bquad
            beta_v = majorp * (majorq - majorp) / aquad + minorp * (minorq - minorp) / bquad
            gamma_v = insidp - 1.0
            discrm = beta_v * beta_v - alpha * gamma_v

            if insidq < 1.0 and insidp > 1.0 and discrm > 0.0 and alpha != 0.0:
                subpnt += 1
                t_arr[subpnt] = (-beta_v - math.sqrt(discrm)) / alpha
                inelip[1] = False
                inelip[2] = True
            elif insidp < 1.0 and insidq > 1.0 and discrm > 0.0 and alpha != 0.0:
                subpnt += 1
                t_arr[subpnt] = (-beta_v + math.sqrt(discrm)) / alpha
                t_arr[subpnt] = t_arr[subpnt] + (1.0 - t_arr[subpnt]) * 0.01
                inelip[1] = True
                inelip[2] = False
            elif (
                discrm > 0.0
                and gamma_v >= 0.0
                and beta_v < 0.0
                and -beta_v < alpha
                and alpha != 0.0
                and alpha + beta_v + beta_v + gamma_v >= 0.0
            ):
                if gamma_v == 0.0:
                    subpnt += 1
                    inelip[1] = True
                    inelip[2] = False
                    t_arr[subpnt] = -2.0 * beta_v / alpha
                elif alpha + beta_v + beta_v + gamma_v == 0.0:
                    subpnt += 1
                    inelip[1] = False
                    inelip[2] = True
                    t_arr[subpnt] = (-beta_v - math.sqrt(discrm)) / alpha
                else:
                    inelip[1] = False
                    inelip[2] = True
                    inelip[3] = False
                    sq = math.sqrt(discrm)
                    subpnt += 1
                    t_arr[subpnt] = (-beta_v - sq) / alpha
                    subpnt += 1
                    t_arr[subpnt] = (-beta_v + sq) / alpha
            else:
                inelip[1] = False

        # Map T values back to original segment
        for i in range(2, subpnt + 1):
            a_v = t_arr[i] * denomp
            b_v = (1.0 - t_arr[i]) * denomq
            denom = b_v + a_v
            if denom != 0.0:
                t_arr[i] = a_v / denom
            else:
                t_arr[i] = 0.5

    else:
        return ([_vequ(p)], [_vequ(q)], [False], [False], 1)

    # Set boundary T values
    subpnt += 1
    t_arr[1] = 0.0
    t_arr[subpnt] = 1.0

    # Insert plane intersection point
    if 0.0 < intsct < 1.0:
        i = 1
        while i <= subpnt and intsct > t_arr[i]:
            i += 1
        j = subpnt + 1
        while j > i:
            t_arr[j] = t_arr[j - 1]
            inelip[j] = inelip[j - 1]
            j -= 1
        t_arr[i] = intsct
        subpnt += 1

    # Build fat intervals
    tl = [0.0] * (subpnt + 2)
    tu = [0.0] * (subpnt + 2)
    tl[1] = 0.0
    tu[1] = 0.0
    tl[subpnt] = 1.0
    tu[subpnt] = 1.0

    if subpnt > 2:
        for i in range(2, subpnt):
            tl[i] = max(0.0, (_dnint(quanta * t_arr[i]) - 1.0) / quanta)
            tu[i] = min(1.0, (_dnint(quanta * t_arr[i]) + 1.0) / quanta)

        j = 2
        i = 2
        while i < subpnt:
            if tu[j] >= tl[i]:
                tu[j] = tu[i]
                inelip[j] = inelip[i]
            else:
                j += 1
                tl[j] = tl[i]
                tu[j] = tu[i]
                inelip[j] = inelip[i]
            i += 1

        j += 1
        tl[j] = 1.0
        tu[j] = 1.0
        subpnt = j

    nsub = subpnt - 1

    # Construct subsegments
    begsub_list: list[Vec3] = []
    endsub_list: list[Vec3] = []
    inside_list: list[bool] = []
    inback_list: list[bool] = []

    for i in range(1, nsub + 1):
        beg = _vlcom(1.0 - tu[i], p, tu[i], q)
        end = _vlcom(1.0 - tl[i + 1], p, tl[i + 1], q)
        begsub_list.append(beg)
        endsub_list.append(end)
        inside_list.append(inelip[i])
        if intsct > tu[i]:
            inback_list.append(behind)
        else:
            inback_list.append(not behind)

    return (begsub_list, endsub_list, inside_list, inback_list, nsub)
