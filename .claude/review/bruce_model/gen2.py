# every part read off the gridded photos (ref46 pixels + measured height) -> parts.json in world metres
import numpy as np, json, math
from PIL import Image
from tri import mk
from fit import R as Rot
ray46, pr46 = mk('cam2.json', 1936, 1290); ray50, pr50 = mk('cam50.json', 1933, 1290)
E = dict(c=[20.972, 39.995], t=-2.135, A=101.832, B=66.66, z=0.45)
CX, CY = E['c']


def bp(u, v, z, ray=ray46):
    c, d = ray(u, v); t = (z - c[2]) / d[2]; return c + t * d


def ell(a, grow=0.0):
    t = E['t']; x = (E['A'] + grow) * math.cos(a); y = (E['B'] + grow) * math.sin(a)
    return np.array([CX + x * math.cos(t) - y * math.sin(t), CY + x * math.sin(t) + y * math.cos(t)])


def polar(p): return math.atan2(p[1] - CY, p[0] - CX)


ELL = [(polar(ell(i / 2880 * 2 * math.pi)), i / 2880 * 2 * math.pi) for i in range(2880)]


def ell_dir(th, grow=0.0):
    b = min(ELL, key=lambda e: abs(((e[0] - th + math.pi) % (2 * math.pi)) - math.pi)); return ell(b[1], grow)


# ---- the bowl outer top edge O (wall top), clockwise in ref46 from the west stand's north end to its south end
O = [(880, 945, 8), (830, 912, 6), (760, 900, 5), (700, 885, 5), (640, 860, 5), (600, 838, 5), (568, 800, 5), (552, 760, 5),
     (542, 700, 5), (543, 640, 5), (548, 600, 5), (563, 550, 5), (588, 505, 6), (615, 470, 7), (645, 445, 8), (686, 405, 9),
     (761, 361, 10), (830, 333, 10), (917, 314, 10), (1009, 313, 11), (1123, 309, 11), (1216, 316, 8), (1300, 331, 6),
     (1350, 357, 5), (1400, 388, 5), (1450, 422, 5), (1485, 458, 5), (1508, 520, 5), (1515, 580, 5), (1520, 640, 5),
     (1515, 690, 5), (1500, 725, 6), (1480, 745, 8)]
OW = [bp(u, v, z) for u, v, z in O]
# fence (advertising boards) offset from the grass edge, from the boards' pixels at 1.0 m
BOARDS = [(1200, 404), (690, 525), (900, 418), (1100, 408)]
offs = []
for u, v in BOARDS:
    p = bp(u, v, 1.0); th = polar(p); e = ell_dir(th); offs.append(np.linalg.norm(p[:2] - [CX, CY]) - np.linalg.norm(e - [CX, CY]))
G = float(np.median(offs)); print('fence offset m', np.round(offs, 2), '->', round(G, 2))

# angular span of the open bowl (clockwise in the photo = decreasing or increasing polar angle?)
thO = [polar(p) for p in OW]
th0, th1 = thO[0], thO[-1]
# unwrap along the trace
un = [thO[0]]
for t in thO[1:]:
    d = (t - un[-1] + math.pi) % (2 * math.pi) - math.pi; un.append(un[-1] + d)
N = 300
TH = np.linspace(un[0], un[-1], N)


def interp_trace(un, pts, th):
    pts = np.array(pts); s = 1 if un[-1] > un[0] else -1
    x = np.array(un) * s; return np.array([np.interp(th * s, x, pts[:, k]) for k in range(pts.shape[1])])


def ringO(th): return interp_trace(un, [list(p) for p in OW], th)


PLAZA = -2.5
rings = {k: [] for k in ('grass', 'fence', 'fence_top', 'seat_front', 'walk_a', 'walk_b', 'top_in', 'top_out', 'foot')}
# east walkway: inner edge traced in ref46 at 5.5 m
WALK = [(680, 432), (750, 412), (850, 393), (950, 382), (1050, 377), (1140, 377)]
WW = [bp(u, v, 5.5) for u, v in WALK]; wun = [polar(p) for p in WW]
for i in range(1, len(wun)):
    wun[i] = wun[i - 1] + ((wun[i] - wun[i - 1] + math.pi) % (2 * math.pi) - math.pi)
# put walk angles on the same unwrap branch as TH
while wun[0] - TH.mean() > math.pi: wun = [w - 2 * math.pi for w in wun]
while TH.mean() - wun[0] > math.pi: wun = [w + 2 * math.pi for w in wun]
wlo, whi = min(wun), max(wun)
# the navy outer face is a slope, not a wall: its foot read off ref46 at four places (top edge at rim height, foot at 0 m)
NAVY = [((548, 640), (533, 640), 5.0), ((700, 368), (690, 356), 9.0), ((900, 327), (900, 316), 10.0), ((1000, 322), (1000, 311), 11.0)]
nth = []; nrat = []
for tp, ft, zz in NAVY:
    A_ = bp(*tp, zz); B_ = bp(*ft, 0.0); t_ = polar(A_)
    t_ += 2 * math.pi * round((TH.mean() - t_) / (2 * math.pi))
    nth.append(t_); nrat.append(float(np.linalg.norm(A_[:2] - B_[:2])) / zz)
oi = np.argsort(nth); nth = np.array(nth)[oi]; nrat = np.array(nrat)[oi]
print('navy slope run/rise', np.round(nrat, 2))
for th in TH:
    o = ringO(th); z = o[2]
    g = ell_dir(th); f = ell_dir(th, G)
    d = (o[:2] - [CX, CY]); d /= np.linalg.norm(d)
    rings['grass'].append([*g, E['z']]); rings['fence'].append([*f, E['z']]); rings['fence_top'].append([*f, 1.6])
    sf = f + d * 1.0; rings['seat_front'].append([*sf, 1.6])
    ti = o[:2] - d * 3.0; rings['top_in'].append([*ti, z]); rings['top_out'].append([*o[:2], z])
    rings['foot'].append([*(o[:2] + d * float(np.interp(th, nth, nrat)) * z), 0.0])
    # walkway: traced on the east stand, elsewhere the rake runs straight through
    if wlo <= th <= whi:
        w = interp_trace(wun, [list(p) for p in WW], th); wb = w[:2] + d * 2.0
        rings['walk_a'].append([*w[:2], 5.5]); rings['walk_b'].append([*wb, 5.5])
    else:
        A = np.array([*sf, 1.6]); B = np.array([*ti, z])
        rings['walk_a'].append(list(A + (B - A) * 0.48)); rings['walk_b'].append(list(A + (B - A) * 0.52))
# concourse outer edge (red gravel -> brown grass), traced in ref46 at field level
CONC = [(458, 700), (460, 650), (465, 600), (470, 560), (490, 505), (520, 450), (560, 400), (620, 350), (700, 322), (800, 302), (900, 290),
        (1000, 285), (1100, 283), (1200, 288), (1300, 300), (1400, 325), (1460, 365), (1495, 420), (1495, 470), (1505, 550), (1515, 620), (1520, 700)]
CW = [bp(u, v, 0.0) for u, v in CONC]; cun = [polar(p) for p in CW]
for i in range(1, len(cun)):
    cun[i] = cun[i - 1] + ((cun[i] - cun[i - 1] + math.pi) % (2 * math.pi) - math.pi)
while cun[0] - TH.mean() > math.pi: cun = [c - 2 * math.pi for c in cun]
while TH.mean() - cun[0] > math.pi: cun = [c + 2 * math.pi for c in cun]
for k in ('path_out', 'conc_out', 'skirt'): rings[k] = []
# gravel width = trace distance beyond the path, smoothed along the ring (hand-picked points zigzag), at least 2 m
DS, PO, GW = [], [], []
for i, th in enumerate(TH):
    o = ringO(th); d = (o[:2] - [CX, CY]); d /= np.linalg.norm(d)
    ft = np.array(rings['foot'][i][:2]); po = ft + d * 3.0
    c = interp_trace(cun, [list(p) for p in CW], th)[:2]
    DS.append(d); PO.append(po); GW.append(float(np.dot(c - po, d)))
GW = np.convolve(np.pad(np.array(GW), 6, mode='edge'), np.ones(13) / 13, mode='valid')
for i in range(len(TH)):
    d, po = DS[i], PO[i]; c = po + d * max(2.0, GW[i])
    rings['path_out'].append([*po, 0.0]); rings['conc_out'].append([*c, 0.0]); rings['skirt'].append([*(c + d * 5.0), PLAZA])
strips = [['fence', 'fence_top', 'fence'],  # no grass inside the fence: the game draws it (director: 'Leave field out')
          ['fence_top', 'seat_front', 'seats'],
          ['seat_front', 'walk_a', 'seats'], ['walk_a', 'walk_b', 'concrete'], ['walk_b', 'top_in', 'seats'],
          ['top_in', 'top_out', 'concrete'], ['top_out', 'foot', 'navy'],
          ['foot', 'path_out', 'path'], ['path_out', 'conc_out', 'gravel'], ['conc_out', 'skirt', 'bank']]

# ---- west stand (pixels in ref46; heights: roof front from its shadow, rear eave 18 m from the rear masts' tops)
FRONT = [(920, 872, 17.5), (1003, 844, 17.5), (1074, 822, 17.25), (1146, 797, 15.5), (1217, 772, 15.0), (1289, 751, 16.25), (1360, 729, 17.5), (1390, 718, 17.5)]
REAR = [(930, 912), (1003, 897), (1100, 872), (1200, 842), (1300, 810), (1380, 787), (1440, 768)]
FW = [bp(u, v, z) for u, v, z in FRONT]; RW = [bp(u, v, 18.0) for u, v in REAR]


def resample(P, n):
    P = np.array(P); L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    s = np.linspace(0, L[-1], n); return np.array([[np.interp(x, L, P[:, k]) for k in range(P.shape[1])] for x in s])


NR = 49
Fr = resample(FW, NR); Rr = resample(RW, NR)
lofts = []
# roof: three folded strips across the depth (fold lines seen in both photos), 0.8 m deck
fold = [0.0, 0.5, 0.0, 0.5]   # ridge/valley offsets at the strip lines (front, 1/3, 2/3, rear)
lines = []
for k in range(4):
    L = Fr + (Rr - Fr) * (k / 3.0); L = L.copy(); L[:, 2] += fold[k]; lines.append(L)
for k in range(3):
    lofts.append(dict(name='roof_%d' % k, a=lines[k].tolist(), b=lines[k + 1].tolist(), close='roof', step=2.5))
under = [L.copy() for L in (lines[0], lines[3])]
for L in under: L[:, 2] -= 0.8
lofts.append(dict(name='roof_under', a=under[0].tolist(), b=under[1].tolist(), close='roof_under', step=3))
lofts.append(dict(name='roof_fascia', a=lines[0].tolist(), b=under[0].tolist(), close='white', step=2))
lofts.append(dict(name='roof_rear_fascia', a=lines[3].tolist(), b=under[1].tolist(), close='white', step=2))
# seating under the roof: fence top -> seat back (2 m in front of the rear wall, 9 m)
fence_full = []
for P_ in Fr:
    th = polar(P_); f = ell_dir(th, G); fence_full.append([*f, 1.6])
fence_full = np.array(fence_full)
seat_back = Rr.copy(); dirv = (fence_full[:, :2] - Rr[:, :2]); dirv /= np.linalg.norm(dirv, axis=1)[:, None]
seat_back[:, :2] += dirv * 2.0; seat_back[:, 2] = 9.0
lofts.append(dict(name='w_seats', a=fence_full.tolist(), b=seat_back.tolist(), close='seats_m', step=2))
fence_foot = fence_full.copy(); fence_foot[:, 2] = E['z']
grass_w = np.array([[*ell_dir(polar(p)), E['z']] for p in Fr])
# apron and fence under the stand: the same ellipse offsets as the bowl, over the gap between the bowl's two ends
t0 = TH[-1]; d_ = (TH[0] - TH[-1] + math.pi) % (2 * math.pi) - math.pi  # short way round, under the stand
G_TH = np.linspace(t0, t0 + d_, 60)
gg = [[*ell_dir(t), E['z']] for t in G_TH]; gf = [[*ell_dir(t, G), E['z']] for t in G_TH]; gt = [[*ell_dir(t, G), 1.6] for t in G_TH]
pass  # w_apron dropped: the game's turf covers the oval to the fence
lofts.append(dict(name='w_fence', a=gf, b=gt, close='fence', step=2))
top_walk = Rr.copy(); top_walk[:, 2] = 9.0
lofts.append(dict(name='w_topwalk', a=seat_back.tolist(), b=top_walk.tolist(), close='concrete', step=2))
PLAZA = -2.5
# rear: solid only up to the 9 m walkway; above it open, white columns every 8.4 m (ref50 column feet, median spacing)
# up to a 1.5 m concrete eave beam under the roof's rear edge
rw_lo = Rr.copy(); rw_lo[:, 2] = PLAZA; rw_hi = Rr.copy(); rw_hi[:, 2] = 9.0
lofts.append(dict(name='w_rear_wall', a=rw_lo.tolist(), b=rw_hi.tolist(), close='wall', step=2))
beam_lo = lines[3].copy(); beam_lo[:, 2] -= 1.5
lofts.append(dict(name='w_eave_beam', a=lines[3].tolist(), b=beam_lo.tolist(), close='concrete', step=2))
from tri import ray50 as _r50
_c, _d = _r50(817, 918); _col0 = _c + _d * (13.0 - _c[2]) / _d[2]
_L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(Rr[:, :2], axis=0), axis=1))]
_s0 = float(np.interp(0, [0], [0]))
_cols = []
_k = int(np.argmin(np.linalg.norm(Rr[:, :2] - _col0[:2], axis=1))); _s0 = _L[_k] % 8.4
for sv in np.arange(_s0, _L[-1], 8.4):
    x = float(np.interp(sv, _L, Rr[:, 0])); y = float(np.interp(sv, _L, Rr[:, 1])); zt = float(np.interp(sv, _L, beam_lo[:, 2]))
    _cols.append(dict(name='rear_col', p=[x, y, 9.0], q=[x, y, zt], r0=0.35, r1=0.35, seg=8, close='white'))
# stand ends: close the gap between the bowl ends and the stand (walls from plaza to roof under side)
boxes = []; tubes = list(_cols)
# end trusses (blue steel): roof front and rear corners to a ground point beyond the stand end
for i0, i1, sgn in ((0, 1, -1), (NR - 1, NR - 2, 1)):
    f0 = lines[0][i0]; r0 = lines[3][i0]; along = (Rr[i0] - Rr[i1]); along[2] = 0; along /= np.linalg.norm(along)
    g = Rr[i0].copy(); g[:2] += along[:2] * 4.0; g[2] = PLAZA
    for p in (f0, r0, (f0 + r0) / 2):
        tubes.append(dict(name='truss', p=list(g), q=list(p), r0=0.35, r1=0.3, seg=8, close='steel'))
    tubes.append(dict(name='truss', p=list(f0), q=list(r0), r0=0.3, r1=0.3, seg=8, close='steel'))
# rear masts (bases in ref46 at plaza level; tops at the rear eave, from the triangulated mast)
# masts triangulated from ref46 + ref50 (foot and top of each pole); one stay per mast from the top over the roof to the
# roof front, along the dark line read in ref46 (top pixel -> a second point on the line), met with the roof front line
from tri import tri as _tri
FP = np.array([(u, v) for u, v, z in FRONT], float); FZ = np.array([z for u, v, z in FRONT], float)
MASTS = [((1103, 962), (643, 847), (1103, 893), (645, 775), (1045, 845)), ((1222, 935), (708, 907), (1222, 857), (710, 833), (1167, 802)),
         ((1330, 875), (797, 970), (1330, 815), (798, 890), (1280, 760)), ((1417, 820), (905, 1000), (1418, 766), (906, 946), (1392, 720))]
for b46, b50, t46, t50, s46 in MASTS:
    B = _tri(b46, b50)[0]; T = _tri(t46, t50)[0]; B[2] = PLAZA
    tubes.append(dict(name='mast', p=list(B), q=list(T), r0=0.35, r1=0.25, seg=10, close='mast'))
    p0 = np.array(t46, float); dv = np.array(s46, float) - p0
    best = None
    for k in range(len(FP) - 1):
        e = FP[k + 1] - FP[k]; Mx = np.array([dv, -e]).T
        try: t_, w_ = np.linalg.solve(Mx, FP[k] - p0)
        except np.linalg.LinAlgError: continue
        if 0 <= w_ <= 1 and t_ > 0: best = (FP[k] + e * w_, FZ[k] + (FZ[k + 1] - FZ[k]) * w_)
    if best is not None:
        (fu, fv), fz = best; Fp = bp(fu, fv, fz)
        tubes.append(dict(name='stay', p=list(T), q=list(Fp), r0=0.12, r1=0.12, seg=6, close='mast'))
        print('stay', np.round(T, 1), '->', np.round(Fp, 1))


def block(name, a, b, depth_to_rear, z0, z1, close='white'):
    """box whose front edge runs a->b (world xy) and extends back to the rear wall"""
    a = np.array(a[:2]); b = np.array(b[:2]); c = (a + b) / 2; L = np.linalg.norm(b - a); yaw = math.atan2(*(b - a)[::-1])
    nrm = np.array([-math.sin(yaw), math.cos(yaw)])
    # rear wall direction: nearest rear point
    rp = Rr[np.argmin(np.linalg.norm(Rr[:, :2] - c, axis=1))][:2]
    if np.dot(rp - c, nrm) < 0: nrm = -nrm
    D = abs(np.dot(rp - c, nrm)) if depth_to_rear is None else depth_to_rear
    cc = c + nrm * D / 2
    boxes.append(dict(name=name, c=list(cc), hx=L / 2, hy=D / 2, z0=z0, z1=z1, yaw=yaw, close=close, top='roof_flat'))


# facade blocks: middle (two-view: band 2.1-5.4 m), south (ref46 band edge at 2.5 m), north (flat white block)
block('blk_mid', [-38.2, 113.0], [-54.0, 93.1], None, PLAZA, 6.0, 'facade')
block('blk_south', bp(1250, 890, 2.5), bp(1360, 845, 2.5), None, PLAZA, 6.0, 'facade')
block('blk_north', bp(925, 960, 2.5), bp(1015, 935, 2.5), None, PLAZA, 6.0)
# white box at the stand's south end (roof corners at 9 m) and the four stepped ramps beside it
bx = [bp(u, v, 9.0) for u, v in ((1378, 772), (1420, 752), (1440, 790), (1398, 808))]
ctr = np.mean(bx, 0); e1 = bx[1] - bx[0]; e2 = bx[3] - bx[0]
boxes.append(dict(name='white_box', c=list(ctr[:2]), hx=float(np.linalg.norm(e1[:2]) / 2), hy=float(np.linalg.norm(e2[:2]) / 2), z0=PLAZA, z1=9.0,
                  yaw=math.atan2(e1[1], e1[0]), close='white'))
for k, (u0, v0, u1, v1, z) in enumerate(((1400, 862, 1478, 787, 6.0), (1410, 868, 1486, 795, 4.5), (1420, 874, 1494, 803, 3.0), (1430, 880, 1502, 811, 1.5))):
    pa = bp(u0, v0, z); pb = bp(u1, v1, z); c = (pa + pb) / 2; d = pb - pa
    boxes.append(dict(name='ramp%d' % k, c=list(c[:2]), hx=float(np.linalg.norm(d[:2]) / 2), hy=1.0, z0=z - 0.4, z1=z, yaw=math.atan2(d[1], d[0]), close='concrete'))
# light towers: shafts thick at the base, thin at the top; lamp heads read off ref46 at the head height
TOW = json.load(open('osm/geo.json'))['towers']; TH_ = json.load(open('cam2.json'))['p'][7]
for (x, y) in TOW:
    tubes.append(dict(name='tower', p=[x, y, 0], q=[x, y, TH_ - 3], r0=1.1, r1=0.45, seg=16, close='tower'))
    yaw = math.atan2(CY - y, CX - x)
    boxes.append(dict(name='lamp_head', c=[x + math.cos(yaw) * 0.5, y + math.sin(yaw) * 0.5], hx=1.0, hy=5.5, z0=TH_ - 3.5, z1=TH_ + 3.0, yaw=yaw, close='lamp'))
# scoreboard behind the north end, on legs
sa = np.array([100.1, 127.4]); sb = np.array([82.4, 140.2]); d = sb - sa
boxes.append(dict(name='scoreboard', c=list((sa + sb) / 2), hx=float(np.linalg.norm(d) / 2), hy=0.6, z0=4.0, z1=11.0, yaw=math.atan2(d[1], d[0]), close='board'))
for t in (0.2, 0.8):
    p = sa + d * t; tubes.append(dict(name='sb_leg', p=[p[0], p[1], 0], q=[p[0], p[1], 4.0], r0=0.3, r1=0.3, seg=8, close='steel'))

# ---- hand-made textures (paint.py), no photo pixels on the model
cl = json.load(open('tex/index.json'))
cl['apron'] = cl['grass']
# bowl aisles: one every 15 m at mid-tier, phase from the aisle read at ref46 (913, 335) at 8 m
pa = bp(913, 335, 8.0); R_mid = float(np.linalg.norm(pa[:2] - [CX, CY]))
BAY_ANG = 15.0 / R_mid; BAY_PHASE = polar(pa)
BAY_PHASE += 2 * math.pi * round((TH.mean() - BAY_PHASE) / (2 * math.pi))
M46 = Rot(*json.load(open('cam2.json'))['p'][3:6]); M50 = Rot(*json.load(open('cam50.json'))['p'][3:6])
p46 = json.load(open('cam2.json'))['p']; p50 = json.load(open('cam50.json'))['p']
cams = [dict(name='46', C=p46[:3], M=M46.tolist(), f=p46[6], W=1936, H=1290, img='ref46.jpg'),
        dict(name='50', C=p50[:3], M=M50.tolist(), f=p50[6], W=1933, H=1290, img='ref50.jpg')]
# the open ends: the bowl's last cross-section runs down to the plaza as a wall; the stand's ends close the same way
for i in (0, N - 1):
    prof = [rings[k][i] for k in ('fence_top', 'seat_front', 'walk_a', 'walk_b', 'top_in', 'top_out')]
    low = [[p[0], p[1], PLAZA] for p in prof]
    lofts.append(dict(name='bowl_end', a=prof, b=low, close='concrete', step=2))
for i in (0, NR - 1):
    prof = [list(fence_full[i]), list(seat_back[i]), list(top_walk[i]), [Rr[i][0], Rr[i][1], 17.2]]
    low = [[p[0], p[1], PLAZA] for p in prof]
    lofts.append(dict(name='stand_end', a=prof, b=low, close='white', step=2))
field_ring =[[*ell(i / 240 * 2 * math.pi), E['z']] for i in range(240)]
# stair flights from the plaza up to the 9 m walkway, between the facade blocks (ref46 centrelines, 5 m wide)
for k, ((tu, tv), (bu, bv)) in enumerate((((1040, 918), (1048, 978)), ((1235, 888), (1242, 936)), ((1360, 820), (1378, 868)))):
    T = bp(tu, tv, 9.0); Bt = bp(bu, bv, PLAZA); dv = Bt[:2] - T[:2]; nv = np.array([-dv[1], dv[0]]) / np.linalg.norm(dv) * 2.5
    # real steps: one solid block per tread, 0.17 m risers, treads spread evenly along the measured flight
    N = int(round((9.0 - PLAZA) / 0.17)); run = float(np.linalg.norm(dv)) / N; du = -dv / np.linalg.norm(dv); yaw = math.atan2(du[1], du[0])
    for n in range(N):
        cc = Bt[:2] + du * run * (n + 0.5)
        boxes.append(dict(name='stair%d_%02d' % (k, n), c=list(cc), hx=run / 2, hy=2.5, z0=PLAZA, z1=PLAZA + (9.0 - PLAZA) * (n + 1) / N, yaw=yaw, close='riser', top='tread', fuv=True))
        zt = PLAZA + (9.0 - PLAZA) * (n + 1) / N
        boxes.append(dict(name='nose%d_%02d' % (k, n), c=list(cc - du * (run / 2 - 0.03)), hx=0.05, hy=2.45, z0=zt, z1=zt + 0.01, yaw=yaw, close='nosing'))
    nv1 = nv / np.linalg.norm(nv)
    for sd in (-1, 1):
        off = nv1 * sd * 2.4
        p0 = Bt[:2] + off; p1 = T[:2] + off
        tubes.append(dict(name='rail%d_%d' % (k, sd + 1), p=[*p0, PLAZA + 0.9], q=[*p1, 9.0 + 0.9], r0=0.025, r1=0.025, seg=8, close='rail'))
        npost = int(np.linalg.norm(dv) / 2.0) + 1
        for m in range(npost + 1):
            f = m / npost; pp = p0 + (p1 - p0) * f; zb = PLAZA + (9.0 - PLAZA) * f
            tubes.append(dict(name='post%d_%d_%d' % (k, sd + 1, m), p=[*pp, zb], q=[*pp, zb + 0.9], r0=0.02, r1=0.02, seg=6, close='rail'))
    if k in (1, 2):  # ref46 shows the orange gate at the head of these flights
        gc = T[:2] - du * 0.3
        boxes.append(dict(name='gate%d' % k, c=list(gc), hx=0.05, hy=2.5, z0=9.0, z1=11.4, yaw=yaw, close='gate', fuv=True))
        # 1980s waist-high tripod turnstiles at the foot of the gated flight: three steel cabinets across the
        # 5 m flight (passages about 1 m), each with a hub on its side and three 0.5 m arms at 120 degrees
        for m, off in enumerate((-1.75, -0.25, 1.25)):
            cc2 = Bt[:2] - du * 1.6 + nv1 * off
            boxes.append(dict(name='turn%d_%d' % (k, m), c=list(cc2), hx=0.55, hy=0.14, z0=PLAZA, z1=PLAZA + 1.0, yaw=yaw, close='turnstile', top='nosing', fuv=True))
            # hub on an arm-mount 0.38 m out from the cabinet centre; axis tilted 45 deg (toward the entrant and up)
            # so one arm sits level across the passage at waist height and the other two point down
            hub = np.array([*(cc2 + nv1 * 0.38), PLAZA + 0.92])
            tubes.append(dict(name='tmnt%d_%d' % (k, m), p=[*(cc2 + nv1 * 0.12), PLAZA + 0.92], q=list(hub), r0=0.04, r1=0.04, seg=8, close='rail'))
            ax = np.array([*(-du * 0.7071), 0.7071]); e1 = np.array([*nv1, 0.0]); e2 = np.cross(ax, e1)
            tubes.append(dict(name='thub%d_%d' % (k, m), p=list(hub - ax * 0.06), q=list(hub + ax * 0.08), r0=0.08, r1=0.08, seg=12, close='rail'))
            for j in range(3):
                th = j * 2 * math.pi / 3
                d = e1 * math.cos(th) + e2 * math.sin(th)
                h0 = hub + ax * 0.04
                tubes.append(dict(name='tarm%d_%d_%d' % (k, m, j), p=list(h0), q=list(h0 + d * 0.45), r0=0.022, r1=0.022, seg=8, close='rail'))
# ground behind the main stand, traced on ref46 (pixels back-projected to the plaza height): pale pavers and road,
# the car park with its bays, lawn under the rest. The upper edge runs under the stand (hidden).
PAVE = [(780, 925), (885, 915), (930, 945), (1060, 965), (1200, 915), (1350, 870), (1445, 815), (1480, 780), (1515, 725), (1540, 700),
        (1600, 700), (1580, 760), (1560, 790), (1540, 850), (1500, 895), (1470, 915), (1405, 960), (1370, 1000), (1330, 1030), (1355, 1050),
        (1380, 1080), (1450, 1078), (1446, 1100), (1455, 1150), (1470, 1265), (1430, 1265), (1405, 1200), (1355, 1160), (1255, 1160),
        (1190, 1140), (1150, 1130), (1130, 1110), (1090, 1095), (1060, 1080), (990, 1080), (940, 1080), (860, 1100), (780, 1115)]
CARP = [(1450, 1078), (1700, 1055), (1700, 1265), (1470, 1265), (1455, 1150), (1446, 1100)]
LAWN = [(700, 900), (1700, 700), (1700, 1285), (700, 1285)]
_c = bp(1545, 1115, PLAZA); rd = bp(1595, 1250, PLAZA)[:2] - _c[:2]; rd = rd / np.linalg.norm(rd); _n = np.array([-rd[1], rd[0]])  # rows' direction and across
flats = [dict(name='g_lawn', poly=[list(bp(u, v, PLAZA - 0.06)) for u, v in LAWN], close='lawn', rot=0.0),
         dict(name='g_pave', poly=[list(bp(u, v, PLAZA - 0.03)) for u, v in PAVE], close='pavers', rot=0.0),
         dict(name='g_carpark', poly=[list(bp(u, v, PLAZA - 0.02)) for u, v in CARP], close='carpark', rot=float(math.atan2(_n[1], _n[0])), uoff=float(np.dot(_c[:2], _n)))]
out = dict(cams=cams, centre=[CX, CY], field_ring=field_ring, rings=rings, ring_order=list(rings), bowl_strips=strips, closed=False,
           lofts=lofts, boxes=boxes, tubes=tubes, flats=[], no_field=True, closeups=cl, step=2.0, min_cos=0.30, no_photo=True,
           ring_th=TH.tolist(), bay_ang=BAY_ANG, bay_phase=BAY_PHASE, field_axis=E['t'])
json.dump(out, open('parts.json', 'w'), default=lambda o: o.tolist() if hasattr(o, 'tolist') else float(o))
print('rings', len(TH), 'lofts', len(lofts), 'boxes', len(boxes), 'tubes', len(tubes))
