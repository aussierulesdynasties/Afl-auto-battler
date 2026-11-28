"""Refit a kit ground's boundary fence to its measured turf edge (Legacy old grounds, row 202).

python3 tools/grounds/legacy/fence_fourier.py <slug> <turf_enu.json> [K] [--write]

- The turf outline (metres east/north of the model origin, from the measuring pass) is pushed out 0.3 m along its
  normal to the fence rail line, the same offset Blacktown used (grass edge + 0.3 m to the rail).
- It is fitted with one smooth polar Fourier curve of order K (default 6) about the outline's centroid, the kit's
  `fence_fourier` {c, a0, ab}; the model's `fence` ellipse is replaced by the least-squares ellipse closest to that
  curve, which is what GroundModels.FIT and the kit's ellipse users read.
- It prints the fit, the old fence's gap to the turf, and the clearance of every straight stand front, tower and
  extra box/building/poly from the new curve (negative = inside the field). With --write it updates
  tools/grounds/<slug>/model/<slug>.json.
"""
import json, math, os, sys
import numpy as np

slug, src = sys.argv[1], sys.argv[2]
K = int(sys.argv[3]) if len(sys.argv) > 3 and not sys.argv[3].startswith('-') else 6
WRITE = '--write' in sys.argv
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLAN = os.path.join(ROOT, slug, 'model', slug + '.json')
D = json.load(open(PLAN))
O = np.array(json.load(open(src))['outline_enu_m'], float)

# outward normal offset of 0.3 m (outline is a closed loop)
c0 = O.mean(0)
t = np.roll(O, -1, 0) - np.roll(O, 1, 0); n = np.stack([t[:, 1], -t[:, 0]], 1); n /= np.linalg.norm(n, axis=1)[:, None]
n *= np.sign(np.sum((O - c0) * n, 1))[:, None]          # make every normal point away from the centre
F = O + 0.3 * n

def fit(c):
    q = F - c; th = np.arctan2(q[:, 1], q[:, 0]); r = np.hypot(q[:, 0], q[:, 1])
    A = np.column_stack([np.ones_like(th)] + [f(k * th) for k in range(1, K + 1) for f in (np.cos, np.sin)])
    x, *_ = np.linalg.lstsq(A, r, rcond=None); return x, r - A @ x
c = c0.copy()
for _ in range(5):   # centre on the curve's own middle (the Fourier k=1 terms are the centre shift)
    x, res = fit(c); c = c + np.array([x[1], x[2]])
x, res = fit(c)
ab = [[float(x[2 * k - 1]), float(x[2 * k])] for k in range(1, K + 1)]
def R(th): return x[0] + sum(a * math.cos(k * th) + b * math.sin(k * th) for k, (a, b) in enumerate(ab, 1))
print(f'{slug}: K={K} centre ({c[0]:.2f}, {c[1]:.2f}), rms {np.sqrt(np.mean(res ** 2)):.2f} m, max {np.abs(res).max():.2f} m')

# closest ellipse to the curve (sampled), for FIT and the kit's ellipse users
ths = np.linspace(0, 2 * math.pi, 720, endpoint=False); P = np.array([c + R(a) * np.array([math.cos(a), math.sin(a)]) for a in ths])
M = np.column_stack([P[:, 0] ** 2, P[:, 0] * P[:, 1], P[:, 1] ** 2, P[:, 0], P[:, 1]])
A_, B_, C_, D_, E_ = np.linalg.lstsq(M, np.ones(len(P)), rcond=None)[0]
cx, cy = np.linalg.solve([[2 * A_, B_], [B_, 2 * C_]], [-D_, -E_])
ang = 0.5 * math.atan2(B_, A_ - C_); co, si = math.cos(ang), math.sin(ang)
g = 1 + A_ * cx * cx + B_ * cx * cy + C_ * cy * cy
l1 = A_ * co * co + B_ * co * si + C_ * si * si; l2 = A_ * si * si - B_ * co * si + C_ * co * co
ax_u, ax_v = math.sqrt(g / l1), math.sqrt(g / l2)       # half-axes along ang and ang+90
if ax_u > ax_v: along, across, rot_ax = ax_u, ax_v, math.degrees(ang)
else: along, across, rot_ax = ax_v, ax_u, math.degrees(ang) + 90
rot_ax = (rot_ax + 90) % 180 - 90                        # long-axis angle from east, -90..90
# kit `fence` = [x0, y0, a1, a2, rot]: a1 is the half-axis along the math angle rot, a2 the one across it (kit/build.py
# fence_r); the kit plans put the short half-axis at rot, so rot = long axis - 90 (hands: 78.09 at -28.31, 92.51 at 61.69)
kit_rot = rot_ax - 90 if rot_ax > 0 else rot_ax + 90
kit_rot = (kit_rot + 90) % 180 - 90
def ell_r(a):
    u = math.cos(a - math.radians(rot_ax)); v = math.sin(a - math.radians(rot_ax)); return 1 / math.sqrt((u / along) ** 2 + (v / across) ** 2)
er = np.array([np.hypot(*(p - (cx, cy))) - ell_r(math.atan2(*(p - (cx, cy))[::-1])) for p in P])
print(f'  closest ellipse: centre ({cx:.2f}, {cy:.2f}), {2 * along:.1f} x {2 * across:.1f} m, long axis {rot_ax:.1f} deg from east, '
      f'off the curve rms {np.sqrt(np.mean(er ** 2)):.2f} m, max {np.abs(er).max():.2f} m')

# old fence against the turf
x0, y0, a1, a2, rot = D['fence']
def old_r(a):   # kit ellipse (kit/build.py fence_r): a1 along the math angle rot, a2 across it
    th = math.radians(rot); u = math.cos(a - th); v = math.sin(a - th); return 1 / math.sqrt((u / a1) ** 2 + (v / a2) ** 2)
gap = np.array([np.hypot(*(p - (x0, y0))) - old_r(math.atan2(*(p - (x0, y0))[::-1])) for p in O])
print(f'  old fence vs turf edge: from {gap.min():.1f} m (fence inside the turf) to {gap.max():.1f} m outside')

# clearances from the new curve
def clear(p):
    q = np.array(p, float) - c; return np.hypot(*q) - R(math.atan2(q[1], q[0]))
bad = []
def chk(name, pts):
    m = min(clear(p) for p in pts); print(f'  {name:30s} {m:7.1f}'); (m < 1.0) and bad.append(name)
for S in D.get('stands', []):
    if S['kind'] == 'straight':
        A, B = np.array(S['a']), np.array(S['b']); chk('stand ' + S['name'], [A + (B - A) * f for f in np.linspace(0, 1, 41)])
E = D.get('extras', {})
for P_ in E.get('polys', []): chk('poly ' + str(P_.get('name', P_.get('mat', ''))), P_['p'])
for k in ('boxes', 'buildings', 'shelters'):
    for B in E.get(k, []):
        a = math.radians(B['a']); u = np.array([math.cos(a), math.sin(a)]); v = np.array([-u[1], u[0]]); cc = np.array(B['c'])
        chk(k + ' ' + str(B.get('name', B.get('mat', ''))), [cc + u * i * B['L'] / 2 + v * j * B['W'] / 2 for i in (-1, 1) for j in (-1, 1)])
for i, T in enumerate(D.get('towers', [])): chk(f'tower {i}', [T['xy']])
print('  INSIDE OR WITHIN 1 m OF THE NEW FENCE:', bad if bad else 'none')

if WRITE:
    D['fence_fourier'] = {'c': [round(float(c[0]), 3), round(float(c[1]), 3)], 'a0': float(x[0]), 'ab': ab, 'K': K,
                          'how': f'K={K} polar Fourier about c (x east, y north, model metres) fitted to the measured turf edge '
                                 f'({os.path.relpath(src, ROOT)}) pushed out 0.3 m to the rail line; tools/grounds/legacy/fence_fourier.py'}
    D['fence'] = [round(float(cx), 2), round(float(cy), 2), round(across, 2), round(along, 2), round(kit_rot, 2)]
    json.dump(D, open(PLAN, 'w'), indent=1); print('  written', os.path.relpath(PLAN, ROOT), 'fence', D['fence'])
