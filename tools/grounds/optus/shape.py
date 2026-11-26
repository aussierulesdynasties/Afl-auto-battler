"""Optus Stadium's plan shape, measured from Google Earth (tools/grounds/optus/survey/README.md).

Every ring of the model is derived from ONE smooth curve: the roof's outer edge, traced from six calibrated
Google Earth nadir shots and fitted as a polar Fourier series about the bowl centre OC (fit error 0.09 m RMS,
0.72 m worst, survey/outer2_c10.json). Other rings are exact offsets of it along its own normal, so they are
smooth and parallel by construction: no polygon corners, no separately traced wobbles.

Model frame: x east, y north, z up (metres), turf at z 0.
"""
import json, math, os
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SV = os.path.join(HERE, 'survey')
OC = np.array([-30.382794076748684, -8.777071878585646])
_C = np.array(json.load(open(os.path.join(SV, 'outer2_c10.json'))))
_ZC = np.array(json.load(open(os.path.join(SV, 'roofz_c4.json'))))


def fourier(c, th):
    th = np.asarray(th, float)
    out = np.full(th.shape, c[0])
    for n in range(1, (len(c) - 1) // 2 + 1):
        out = out + c[2 * n - 1] * np.cos(n * th) + c[2 * n] * np.sin(n * th)
    return out


def fourier_d(c, th):
    th = np.asarray(th, float)
    out = np.zeros(th.shape)
    for n in range(1, (len(c) - 1) // 2 + 1):
        out = out - n * c[2 * n - 1] * np.sin(n * th) + n * c[2 * n] * np.cos(n * th)
    return out


def edge_r(th):
    """Radius of the roof's outer edge about OC at angle th (rad, counter-clockwise from east)."""
    return fourier(_C, th)


def edge_z(th):
    """Height of the roof's outer edge (Google Earth hover readouts, 1 m steps, smoothed)."""
    return fourier(_ZC, th)


def edge_xy(th):
    th = np.asarray(th, float); r = edge_r(th)
    return np.stack([OC[0] + r * np.cos(th), OC[1] + r * np.sin(th)], -1)


def edge_normal(th):
    """Outward unit normal of the edge curve at th."""
    th = np.asarray(th, float); r = edge_r(th); dr = fourier_d(_C, th)
    tx = dr * np.cos(th) - r * np.sin(th); ty = dr * np.sin(th) + r * np.cos(th)
    L = np.hypot(tx, ty)
    return np.stack([ty / L, -tx / L], -1)


# arc length table along the edge, for even spacing and for the trusses
_TT = np.linspace(0.0, 2 * math.pi, 200001)
_XY = edge_xy(_TT)
_S = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(_XY, axis=0).T))])
PERIMETER = float(_S[-1])


def th_at_s(s):
    """Edge angle at arc length s (m, from east, counter-clockwise; wraps)."""
    return np.interp(np.mod(s, PERIMETER), _S, _TT)


def s_at_th(th):
    return np.interp(np.mod(th, 2 * math.pi), _TT, _S)


def offset(th, d):
    """Point d m outward (negative: inward) of the edge along its normal, at edge angle th."""
    return edge_xy(th) + np.asarray(d, float)[..., None] * edge_normal(th)


NBAY = 50   # LSAA: "fifty (50), approximately 35m triangular truss cantilevers (~44m in total length)"
_TM = json.load(open(os.path.join(SV, 'truss_model.json')))


def truss_s(k):
    """Arc position (m) on the edge of truss k (0..49): even spacing plus a 2-harmonic drift fitted to the 50
    trusses found on Google Earth (survey/truss_model.json, 0.6 m RMS)."""
    k = np.asarray(k, float); c = _TM['coef']; P = _TM['P']
    s = c[0] + P * k / NBAY
    for h in range(1, _TM['H'] + 1):
        s = s + c[2 * h - 1] * np.cos(2 * math.pi * h * k / NBAY) + c[2 * h] * np.sin(2 * math.pi * h * k / NBAY)
    return s * PERIMETER / P
