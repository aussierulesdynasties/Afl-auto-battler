"""Fit People First's roof outline to the reference satellite (shape-first rule, 2026-11-23).

The roof's plan has one round lobe per bay between sharp valleys at the ribs. This script measures that edge on the
satellite and replaces the raw per-angle traces with one smooth, regular construction:

  ribs   rib k sits at arc length S(k) along the outline, S a quadratic in k fitted to the measured valleys
  V(a)   valley radius at each rib, a smooth Fourier curve through the measured valley radii
  depth  each bay's lobe depth (crest above its valley line), a smooth Fourier curve through the measured crests
  lobe   r = V + depth * sin(pi*t)**P between two ribs (V straight between the two valleys), P fitted on the clean bays
  rin    the roof's inner (field-side) line, a smooth Fourier curve through the old trace

It writes src/ribfit.json (read by build.py when RIBFIT is set) and prints every fit error in metres.
Usage: python3 roof_edge_fit.py [sat.png]   (default: $PF_SAT, see ../README.md)
"""
import json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, '..', 'src')
SAT = sys.argv[1] if len(sys.argv) > 1 else os.environ.get(
    'PF_SAT', '/mnt/project-files/people-first-rebuild/review-imagery/reference/sat.png')
S = json.load(open(os.path.join(SRC, 'sat.json')))
D = json.load(open(os.path.join(SRC, 'geo_n.json')))
SH = D['roofshift']; A0, A1 = D['a0'], D['a1']; M = S['mpp']
THR = float(os.environ.get('PF_WHITE', 185))
IM = np.asarray(Image.open(SAT).convert('RGB')).astype(float)


def pix(x, y):
    return IM[int(round(S['py'] - y / M)), int(round(S['px'] + x / M))]


def white(c):  # the membrane: bright and grey-white (the paving and sheds round it are darker or tinted)
    return c.min() > THR and c.max() - c.min() < 32


def trace(a):
    """Outer edge on one ray from the roof centre: the end of the white run that starts on the roof at 96 m."""
    t = math.radians(a); r = 96.0; last = None; miss = 0
    while r < 140:
        if white(pix(SH[0] + r * math.cos(t), SH[1] + r * math.sin(t))):
            last = r; miss = 0
        else:
            miss += 1
            if miss * 0.1 > 1.2 and last is not None:
                break
        r += 0.1
    return last


def fourier(a_deg, y, order, w=None):
    t = np.radians(a_deg); cols = [np.ones_like(t)]
    for k in range(1, order + 1):
        cols += [np.cos(k * t), np.sin(k * t)]
    X = np.stack(cols, 1); w = np.ones_like(y) if w is None else w
    c = np.linalg.lstsq(X * w[:, None], y * w, rcond=None)[0]
    return c


def feval(c, a_deg):
    t = np.radians(np.asarray(a_deg, float)); out = np.full_like(t, c[0])
    for k in range(1, (len(c) - 1) // 2 + 1):
        out += c[2 * k - 1] * np.cos(k * t) + c[2 * k] * np.sin(k * t)
    return out


def robust_fourier(a, y, order, cut=2.0, it=6):
    """Fourier fit that drops points more than `cut` m off (sheds, the light tower and trees touching the edge)."""
    w = np.ones_like(y)
    for _ in range(it):
        c = fourier(a, y, order, w); r = y - feval(c, a); w = (abs(r) < max(cut, 2.5 * np.median(abs(r[w > 0])))).astype(float)
    return c, r, w > 0


def stats(r):
    r = np.abs(np.asarray(r)); return 'median %.2f m, 90%% within %.2f m, max %.2f m' % (np.median(r), np.percentile(r, 90), r.max())


# 1. measure the edge every 0.25 deg over the roof
A = np.arange(A0, A1 + 1e-6, 0.25)
R = np.array([trace(a) or np.nan for a in A]); ok = ~np.isnan(R); R = np.interp(A, A[ok], R[ok])

# 2. arc length along a heavily smoothed base of the edge
def runmed(x, w):
    h = w // 2; return np.array([np.median(x[max(0, i - h):i + h + 1]) for i in range(len(x))])
base = runmed(R, 49); base = np.convolve(np.pad(base, 24, mode='edge'), np.ones(49) / 49, 'valid')
tt = np.radians(A); Sarc = np.concatenate([[0], np.cumsum(np.hypot(np.diff(base * np.cos(tt)), np.diff(base * np.sin(tt))))])

# 3. valleys: best chain of dips 12-17 m apart (dynamic programming over a 0.1 m grid)
Su = np.arange(0, Sarc[-1], 0.1); Du = np.interp(Su, Sarc, R - base)
env = np.array([Du[max(0, i - 50):i + 51].max() for i in range(len(Du))]); sc = np.clip(env - Du, 0, 8)
n = len(Su); lo, hi = 120, 170; best = np.full(n, -1e9); prev = np.full(n, -1, int)
for i in range(n):
    if Su[i] < 9: best[i] = sc[i]
    for j in range(max(0, i - hi), i - lo + 1):
        if best[j] + sc[i] > best[i]: best[i] = best[j] + sc[i]; prev[i] = j
p = [max(range(n - hi, n), key=lambda i: best[i])]
while prev[p[-1]] >= 0: p.append(prev[p[-1]])
Sv = Su[p[::-1]]; k = np.arange(len(Sv))
q = np.polyfit(k, Sv, 2); rib_err = Sv - np.polyval(q, k)
ribs = np.interp(np.polyval(q, k), Sarc, A)
ribs[0] = A0  # the first valley is the roof's west end (measured 0.3 m from it)
print('ribs: %d measured valleys, regular spacing %.1f-%.1f m; valley positions off the fit: %s' % (
    len(Sv), np.polyval(np.polyder(q), 0), np.polyval(np.polyder(q), len(Sv) - 1), stats(rib_err)))

# 4. valley and crest radii, each a smooth curve
def rib_at(a):
    return np.interp(a, ribs, np.arange(len(ribs)))
Vm = np.array([np.sort(R[abs(A - r) <= 0.75])[:3].mean() for r in ribs])
cV, rV, kV = robust_fourier(ribs, Vm, 4)
Cm, Ca = [], []
for i in range(len(ribs) - 1):
    a0, a1 = ribs[i], ribs[i + 1]; sel = (A >= a0 + 0.25 * (a1 - a0)) & (A <= a0 + 0.75 * (a1 - a0))
    Cm.append(R[sel].max()); Ca.append((a0 + a1) / 2)
a_end = ribs[-1]; sel = A > a_end; Cm.append(R[sel].max()); Ca.append(min(A1, a_end + 0.5 * (ribs[-1] - ribs[-2])))
Cm, Ca = np.array(Cm), np.array(Ca)
# fit the lobe depth (crest above the valley line), which changes slowly round the ground, then C = V + depth
Vmid = np.array([(feval(cV, ribs[i]) + feval(cV, ribs[i + 1])) / 2 if i < len(ribs) - 1 else feval(cV, ribs[-1]) for i in range(len(Ca))])
dep = Cm - Vmid; kC = abs(dep - np.median(dep)) < 1.5  # sheds, marquees and the light tower touching a crest read deep or shallow
cdep = fourier(Ca[kC], dep[kC], 2); rC = dep - feval(cdep, Ca)
cC = None  # C(a) = V(a) + depth(a), see model()
print('valley radius curve: %s (%d of %d valleys used)' % (stats(rV[kV]), kV.sum(), len(kV)))
print('lobe depth curve:    %s (%d of %d crests used)' % (stats(rC[kC]), kC.sum(), len(kC)))
print('  lobe depth %.1f-%.1f m round the ground' % (feval(cdep, Ca).min(), feval(cdep, Ca).max()))

# 5. lobe shape: exponent P on the bays whose valleys and crest all fitted
def model(a, P):
    i = np.clip(np.searchsorted(ribs, a) - 1, 0, len(ribs) - 2)
    last = a > ribs[-1]
    w = np.where(last, ribs[-1] - ribs[-2], ribs[np.minimum(i + 1, len(ribs) - 1)] - ribs[i])
    r0 = np.where(last, ribs[-1], ribs[i]); t = np.clip((a - r0) / w, 0, 1)
    v = feval(cV, r0 + t * w) if False else feval(cV, r0) + (feval(cV, r0 + w) - feval(cV, r0)) * t
    return v + feval(cdep, r0 + w / 2) * np.sin(np.pi * t) ** P
clean = np.zeros_like(A, bool)
for i in range(len(ribs) - 1):
    if kV[i] and kV[i + 1] and kC[i]: clean |= (A >= ribs[i]) & (A <= ribs[i + 1])
Ps = np.arange(0.2, 3.01, 0.05); errs = [np.median(abs(R[clean] - model(A[clean], P))) for P in Ps]
P = float(Ps[int(np.argmin(errs))])
print('lobe exponent P=%.2f (median %.2f m on %d clean samples)' % (P, min(errs), clean.sum()))

# 6. inner line: smooth Fourier through the old trace
RIN = np.array(D['rin']); aa = np.arange(1440) / 4.0
cI, rI, kI = robust_fourier(aa, RIN, 12, cut=1.0)
print('inner line (old trace -> order-12 curve): %s' % stats(rI))

# 7. whole outline against the measurement, old build vs new
new = model(A, P)
old = np.array([D['rout'][int((a % 360) * 4) % 1440] for a in A])
print('outline vs satellite, new: %s; within 2 m %.0f%%' % (stats(R - new), 100 * np.mean(abs(R - new) < 2)))
json.dump({'ribs': [round(float(x), 4) for x in ribs], 'V': [round(float(x), 5) for x in cV], 'depth': [round(float(x), 5) for x in cdep],
           'P': round(P, 3), 'rin': [round(float(x), 5) for x in cI],
           'note': 'tools/grounds/people_first/measure/roof_edge_fit.py; Fourier coefficients in degrees (c0, cos1, sin1, ...)'},
          open(os.path.join(SRC, 'ribfit.json'), 'w'), indent=1)
np.save('/tmp/pf_edge_trace.npy', np.stack([A, R, new]))
if os.environ.get('PF_DEBUG'):
    for a, c, f, k_ in zip(Ca, Cm, Vmid + feval(cdep, Ca), kC): print('crest %6.1f measured %6.1f curve %6.1f %s' % (a % 360, c, f, '' if k_ else 'DROPPED'))
    for a, v, f, k_ in zip(ribs, Vm, feval(cV, ribs), kV): print('valley %6.1f measured %6.1f curve %6.1f %s' % (a % 360, v, f, '' if k_ else 'DROPPED'))
