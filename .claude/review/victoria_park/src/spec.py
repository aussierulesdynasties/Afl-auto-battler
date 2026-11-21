import os
# Victoria Park exterior: every part read off photo.jpg (photo px) and back-projected with cam5 into
# oval-frame metres (origin = centre circle, x along the long axis, +x = east end, z up).
import sys
exec(open('cam.py').read())
p = loadcam('cam5.json')
J = json.load(open('cam5.json')); A, B = J['ab']
MESH = []

def W(pts, z):
    zs = z if hasattr(z, '__len__') else [z] * len(pts)
    return np.array([at_z(p, u, v, zz) for (u, v), zz in zip(pts, zs)])

def resample(P, n):
    P = np.asarray(P, float); d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))]
    t = np.linspace(0, d[-1], n); return np.array([[np.interp(tt, d, P[:, k]) for k in range(P.shape[1])] for tt in t])

def add(name, mat, V, F, UV=None):
    m = {'name': name, 'mat': mat, 'v': np.asarray(V).round(3).tolist(), 'f': [list(map(int, f)) for f in F]}
    if UV is not None: m['uv'] = np.asarray(UV).round(4).tolist()
    MESH.append(m)

def ribbon(name, mat, Pa, Pb, n=None, uvscale=None, closed=False):
    n = n or max(len(Pa), len(Pb)) * 4
    # already-paired point lists of length n keep their pairing (no arc resampling)
    a = np.asarray(Pa, float) if len(Pa) == n == len(Pb) else resample(Pa, n)
    b = np.asarray(Pb, float) if len(Pb) == n == len(Pa) else resample(Pb, n)
    V = np.r_[a, b]; F = []
    m = n if closed else n - 1
    for i in range(m):
        j = (i + 1) % n; F.append([i, j, n + j, n + i])
    uvscale = uvscale or (1.0, -1.0)   # default: u = metres along, v = metres across
    UV = None
    if uvscale:
        s = np.r_[0, np.cumsum(np.linalg.norm(np.diff(a, axis=0), axis=1))] / uvscale[0]
        vb = np.ones(n) * uvscale[1] if uvscale[1] > 0 else np.linalg.norm(b - a, axis=1) / -uvscale[1]
        UV = np.r_[np.c_[s, np.zeros(n)], np.c_[s, vb]]
    add(name, mat, V, F, UV)
    return a, b

def addq(name, mat, V, F, su=1.0, sv=1.0):
    # every quad gets its own 4 vertices; u runs along its longer edge (su m per crop), v across (sv m per crop)
    V = np.asarray(V, float); VV = []; FF = []; UU = []
    for f in F:
        q = V[f]; e1 = np.linalg.norm(q[1] - q[0]); e2 = np.linalg.norm(q[3] - q[0])
        uv = [[0, 0], [e1 / su, 0], [e1 / su, e2 / sv], [0, e2 / sv]] if e1 >= e2 else              [[0, 0], [0, e1 / sv], [e2 / su, e1 / sv], [e2 / su, 0]]
        FF.append([len(VV) + k for k in range(4)]); VV += list(q); UU += uv
    add(name, mat, VV, FF, UU)

def wall(name, mat, P, z0=0.0, uvscale=None):
    P = np.asarray(P, float); Q = P.copy(); Q[:, 2] = z0
    return ribbon(name, mat, P, Q, n=len(P), uvscale=uvscale)

def slab(name, mat, Pa, Pb, th=0.6, fascia=None, n=None):
    a, b = ribbon(name + '_top', mat, Pa, Pb, n=n)
    a2 = a.copy(); a2[:, 2] -= th; b2 = b.copy(); b2[:, 2] -= th
    # underside: corrugated sheet (close-up 2026_44, straightened): 15.3 ribs of 76 mm across the 706 px crop
    # = 1.16 m along the stand; same px/m down the slope (265 px = 0.44 m)
    ribbon(name + '_under', 'under', b2, a2, n=len(a))
    ribbon(name + '_front', fascia or mat, a, a2, n=len(a))
    ribbon(name + '_back', mat, b2, b, n=len(a))
    return a, b

# projection UVs onto the director's full-size copy of the reference (2000x1355; small->full = 2.6653x + (10.75, 15.50))
AFF = np.load('aff_small_to_full.npy'); FW, FH = 2000, 1355
def uvp(V):
    q = proj(p, np.asarray(V, float)); q = np.c_[q, np.ones(len(q))] @ AFF.T
    return np.c_[q[:, 0] / FW, 1 - q[:, 1] / FH]

def ellipse(a, b, n=180, z=0.0):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False); return np.c_[a * np.cos(t), b * np.sin(t), np.full(n, z)]

# ---------- grass (the game's own surface; drawn here so the board can be checked) ----------
E = ellipse(A, B, 180, 0.02)
V = np.r_[[[0, 0, 0.02]], E]; F = [[0, 1 + i, 1 + (i + 1) % 180] for i in range(180)]
UV = np.c_[(V[:, 0] + A) / (2 * A), (V[:, 1] + B) / (2 * B)]
# field floor removed (lead/director: the game draws the turf)


# ---------- terraces: grass fence line up to the outer rim / under the stands ----------
# outer boundary, photo px with the terrace top height (m) at each point, anticlockwise from the Rush's east end
OUT = [
    # Rush rear (roof rear edge, plan at roof height 12 m); terrace top under the roof 9 m
    ((206, 68.8), 12, 9), ((250, 64.8), 12, 9), ((300, 61), 12, 9), ((350, 58.8), 12, 9), ((400, 61), 12, 9),
    ((450, 64.8), 12, 9), ((510, 82), 12, 9),
]
# (the SW corner, Sherrin, Social Club, Ryder, NE building and east rim are added below in world terms)

def to_world(lst):
    return np.array([np.r_[at_z(p, u, v, zp)[:2], zt] for (u, v), zp, zt in lst])

# Rush roof (a) and front edges
rush_front_px = [(206, 80), (250, 76), (300, 72.5), (350, 70), (400, 72), (450, 78), (510, 96), (570, 118),
                 (597.6, 142.4), (618.2, 168.8), (630, 198.2), (631.5, 211.5)]
rush_rear_px = [(206, 68.8), (250, 64.8), (300, 61), (350, 58.8), (400, 61), (450, 64.8), (510, 82), (545, 94)]
RZ = 12.0
rf = W(rush_front_px, RZ)
rr = W(rush_rear_px, RZ)
# roof (a) round the SW corner: rear edge is not separable from the concourse in the photo, so it keeps the
# Rush roof's own depth (front-to-rear distance at x 545 px) as it turns the corner
dep = np.linalg.norm(rr[-1, :2] - W([(560, 112)], RZ)[0, :2])
cent = np.zeros(2)
ext = []
for P in W([(570, 118), (597.6, 142.4), (618.2, 168.8), (630, 198.2), (631.5, 211.5)], RZ):
    d = P[:2] - cent; d = d / np.linalg.norm(d); ext.append(np.r_[P[:2] + d * dep, RZ])
rr = np.r_[rr, np.array(ext)]
slab('rush_roof', 'roof', rf, rr, th=0.5, fascia='fascia', n=120)
# rear wall (exposed metal decking) under the roof rear edge, down to the concourse
rw = resample(rr, 120)
wall('rush_rear', 'deck', rw, 0.0)

# ---------- Sherrin roof (18 m, measured from its shadow on the grass) ----------
SZ = 18.0
sh_front_px = [(613.8, 212.9), (610.9, 239.4), (600.6, 254.1), (590, 265), (580, 274.7), (566, 283),
               (553.5, 289.4), (530, 304.1), (513.8, 315.9), (499.1, 317.4)]
sh_rear_px = [(683, 213), (685.9, 227.6), (680, 251.2), (672, 270), (662.4, 286.5), (650, 303), (635.9, 318.8),
              (617, 331), (597.6, 342.4), (575, 351), (553.5, 357.1)]
sf = W(sh_front_px, SZ)
# sh_rear_px traces the dark FOOT line of the west elevation (ground level), not the roof edge: the roof's rear
# edge (top of the thin white band) sits ~7 photo px further in (image up-left), the overhang leaning out over
# the brick base (CMP 2003: "cantilevers over the brick rear", "overhangs the Lulie Street boundary wall").
_sp = np.asarray(sh_rear_px, float); _tg = np.gradient(_sp, axis=0); _tg /= np.linalg.norm(_tg, axis=1)[:, None]
_nin = np.c_[_tg[:, 1], -_tg[:, 0]]          # image normal pointing into the stand (up-left)
if np.mean(_nin[:, 1]) > 0: _nin = -_nin
REAR_IN = 7.0
sr = W([tuple(q) for q in _sp + _nin * REAR_IN], SZ)
sh_foot = W([tuple(q) for q in _sp], 0.0)
a, b = slab('sherrin_roof', 'roof', sf, sr, th=0.8, fascia='fascia', n=80)
# rear (west) elevation: white fascia band 2 m, then the cranked underside back to the brick undercroft
b2 = b.copy(); b2[:, 2] -= 2.2
ribbon('sherrin_westband', 'white', b, b2, n=80)
# CMP 2003: the west elevation cantilevers over the brick rear (face brick at concourse level) with an arc of
# alternating black and white painted panels. Below the white band the panels slope back under the stand to the
# brick wall, set 6 m in from the roof's rear edge, 4 m up; the photo shows ground right beside the band.
# each band point meets the foot line at its nearest point (the foot runs ~25 m further south than the roof)
fd = resample(sh_foot, 2000)
_e0 = fd[0] - (fd[5] - fd[0]) / np.linalg.norm(fd[5] - fd[0]) * 15; _e1 = fd[-1] + (fd[-1] - fd[-6]) / np.linalg.norm(fd[-1] - fd[-6]) * 15
fdx = resample(np.r_[[_e0], fd, [_e1]], 2400)   # foot line run on straight past both ends: pairs drop square, no fan at the ends
# each stripe runs square to the band (perpendicular in plan) until it meets the foot line: straight stripes, no skew
def _square_hit(q, nrm):
    best = None
    for k in range(len(fdx) - 1):
        A_, B_ = fdx[k, :2], fdx[k + 1, :2]; e = B_ - A_
        M_ = np.array([[nrm[0], -e[0]], [nrm[1], -e[1]]])
        if abs(np.linalg.det(M_)) < 1e-9: continue
        sv, tv = np.linalg.solve(M_, A_ - q[:2])
        if sv > 0 and -1e-6 <= tv <= 1 + 1e-6 and (best is None or sv < best[0]): best = (sv, A_ + e * tv)
    return best
_tg2 = np.gradient(b2[:, :2], axis=0); _tg2 /= np.linalg.norm(_tg2, axis=1)[:, None]
_nn = np.c_[-_tg2[:, 1], _tg2[:, 0]]
_near = np.array([fdx[np.argmin(np.linalg.norm(fdx[:, :2] - q[:2], axis=1))] for q in b2])
if np.mean(np.sum(_nn * (_near[:, :2] - b2[:, :2]), axis=1)) < 0: _nn = -_nn
ftx = []
for q, nrm, nr in zip(b2, _nn, _near):
    h = _square_hit(q, nrm); ftx.append(np.r_[h[1], 0] if h is not None else nr)
ftx = np.array(ftx)
ft = np.array([fd[np.argmin(np.linalg.norm(fd[:, :2] - q[:2], axis=1))] for q in b2])
WALLZ = 4.0
# director 2026-11-18 picked "B: straight": the panel runs a constant 6 m back from the band (CMP 2003), square to it;
# the rear wall, columns, end walls and terraces all follow that line (the measured foot line is no longer used)
brkx = np.c_[b2[:, :2] + 6.0 * _nn, np.full(len(b2), WALLZ)]
brk = brkx.copy(); ft = np.c_[brkx[:, :2], np.zeros(len(b2))]
# CMP 2003: metal cladding painted in black and white stripes over the overhang; hand-painted texture, u in metres
ribbon('sherrin_rearpanels', 'cladding', b2, brkx, n=len(b2))
# Lulie Street rear wall: exposed-aggregate panels between regular piers (CMP 2003), under the panel foot
wtop = brk.copy(); base = wtop.copy(); base[:, 2] = 0.0
ribbon('sherrin_rearwall', 'aggr', wtop, base, n=len(wtop))
# piers line up with the stand's columns: shift u so a bay edge (pier) falls at the first column's foot
_wa = resample(wtop, 100); _arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(_wa, axis=0), axis=1))]
_s0 = _arc[np.argmin(np.linalg.norm(_wa[:, :2] - brk[0, :2], axis=1))]
_fa = resample(brk, 400); _fa_arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(_fa, axis=0), axis=1))]
_cols = [np.argmin(np.linalg.norm(_fa[:, :2] - c[:2], axis=1)) for c in (resample(brk, 13)[0], resample(brk, 13)[-1])]
BAY = (_fa_arc[_cols[1]] - _fa_arc[_cols[0]]) / 12.0     # one wall bay per structural bay, measured on the foot
MESH[-1]['uv'] = [[(u - _s0) / BAY, v] for u, v in MESH[-1]['uv']]
print('sherrin wall bay', round(BAY, 2))
base = brk.copy(); base[:, 2] = 0.0   # the stand's own footprint (columns, terraces)
# south end (step down to roof (a)) and north end walls
# ends: open between roof and rake (photo); the elevated glazed box closes the rear (close-up 2026_5): face from
# the roof's rear edge down the soffit to the brick top, straightened photo of that same end mapped corner to corner
for nm, i in (('sherrin_south', 0), ('sherrin_north', -1)):
    q = np.array([np.r_[b[i][:2], SZ - 0.8], np.r_[ft[i][:2], SZ - 0.8], brk[i], b2[i]])
    add(nm, 'sher_end', q, [[0, 1, 2, 3]], [[0, 1], [1, 1], [1, 0], [0, 0]])

# terraces under the Sherrin: up to 14 m at the rear wall line
sher_out = [np.r_[P[:2], 14.0] for P in base[::-1]]

# purlins under the Sherrin sheeting (close-up 2026_44: 13 counted front to back), 0.4 m deep black steel
for k in range(1, 14):
    t = k / 14.0; P = a * (1 - t) + b * t; P[:, 2] = SZ - 0.8
    Q = P.copy(); Q[:, 2] -= 0.4
    ribbon('sher_purlin%02d' % k, 'steel', P, Q, n=80)

# Sherrin structure (CMP 2003: 12 structural bays, unencased I-beam columns, tapered cantilever beams):
# 13 frames spaced evenly along the stand; each column stands just inside the rear wall, each beam tapers from
# 1.6 m deep at the column to 0.3 m at the front fascia, under the roof.
def box(name, mat, c, ax, w, d, z0, z1):
    ax = np.asarray(ax, float)[:2]; ax = ax / np.linalg.norm(ax); nx = np.array([-ax[1], ax[0]])
    pts = [c + ax * sx * d / 2 + nx * sy * w / 2 for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    V = [np.r_[q, z0] for q in pts] + [np.r_[q, z1] for q in pts]
    addq(name, mat, V, [[0, 1, 2, 3], [4, 7, 6, 5], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]])
fa = resample(a, 13); fb = resample(base, 13)   # columns rise from just inside the brick base line
for k in range(13):
    rear = fb[k][:2]; front = fa[k][:2]; ax = front - rear
    col = rear + ax / np.linalg.norm(ax) * 1.0
    box('sher_col%02d' % k, 'steel', col, ax, 0.35, 0.45, 0.0, SZ - 0.8)
    top_ = SZ - 0.8
    u = ax / np.linalg.norm(ax); n_ = np.array([-u[1], u[0]]) * 0.15
    P0, P1 = col, front - u * 0.3
    V = [np.r_[P0 - n_, top_], np.r_[P1 - n_, top_], np.r_[P1 - n_, top_ - 0.3], np.r_[P0 - n_, top_ - 1.6],
         np.r_[P0 + n_, top_], np.r_[P1 + n_, top_], np.r_[P1 + n_, top_ - 0.3], np.r_[P0 + n_, top_ - 1.6]]
    addq('sher_beam%02d' % k, 'steel', V, [[0, 1, 2, 3], [4, 7, 6, 5], [0, 4, 5, 1], [2, 6, 7, 3], [1, 5, 6, 2], [0, 3, 7, 4]])

# (white building outside the east rim removed: director, stadium only, background pass later)

# ---------- Social Club (15 m, two verticals measured; partial fifth level 19.5 m) ----------
CZ = 15.0
SE, NE, NW = W([(420, 355.8), (450, 400), (540, 375.8)], CZ)
SW = SE + NW - NE
top = np.array([NE, NW, SW, SE])
bot = top.copy(); bot[:, 2] = 0
V = np.r_[top, bot]
add('sc_roof', 'roof', top, [[0, 3, 2, 1]])
# north face: chequer up to the white section; UV in metres for the panel texture
chq_end = W([(521.7, 380.8)], CZ)[0]
L = np.linalg.norm(NW[:2] - NE[:2]); Lc = np.linalg.norm(chq_end[:2] - NE[:2])
add('sc_north_chq', 'chequer', [NE, chq_end, np.r_[chq_end[:2], 0], np.r_[NE[:2], 0]], [[0, 1, 2, 3]],
    [[0, 1], [1, 1], [1, 0], [0, 0]])
add('sc_north_white', 'white', [chq_end, NW, np.r_[NW[:2], 0], np.r_[chq_end[:2], 0]], [[0, 1, 2, 3]])
add('sc_east', 'scdark', [SE, NE, np.r_[NE[:2], 0], np.r_[SE[:2], 0]], [[0, 1, 2, 3]])
add('sc_west', 'white', [NW, SW, np.r_[SW[:2], 0], np.r_[NW[:2], 0]], [[0, 1, 2, 3]])
add('sc_south', 'glass', [SW, SE, np.r_[SE[:2], 0], np.r_[SW[:2], 0]], [[0, 1, 2, 3]])
MZ = 19.5
m1, m2, m3 = W([(430, 375), (479.2, 368.7), (474.2, 349.7)], MZ)
m4 = m1 + m3 - m2
mt = np.array([m1, m2, m3, m4]); mb = mt.copy(); mb[:, 2] = CZ
add('sc_mezz_roof', 'roof', mt, [[0, 3, 2, 1]])
for i in range(4):
    j = (i + 1) % 4; add('sc_mezz_w%d' % i, 'render_cream', [mt[i], mt[j], mb[j], mb[i]], [[0, 1, 2, 3]])
# roof plant: salmon plant room and two dark plant boxes, read off the photo grid (small px)
ax = (NW - NE)[:2] / np.linalg.norm((NW - NE)[:2]); ay = (SE - NE)[:2] / np.linalg.norm((SE - NE)[:2])
def box(nm, mt_, c, a, b, z0, z1):
    c = np.asarray(c[:2]); q = [c, c + ax * a, c + ax * a + ay * b, c + ay * b]
    t = [np.r_[v, z1] for v in q]; bb = [np.r_[v, z0] for v in q]
    add(nm + '_top', mt_, t, [[0, 1, 2, 3]])
    for i in range(4):
        j = (i + 1) % 4; add('%s_w%d' % (nm, i), mt_, [t[i], t[j], bb[j], bb[i]], [[0, 1, 2, 3]])
box('sc_plantroom', 'plant_pink', W([(503, 361)], 18.0)[0], 7.0, 5.0, CZ, 18.0)
box('sc_plant1', 'steel', W([(466, 361)], 16.5)[0], 2.0, 2.0, 19.5, 21.0)
box('sc_plant2', 'steel', W([(491, 358)], 16.5)[0], 2.5, 2.0, CZ, 16.5)

# ---------- Ryder Stand (rear brick wall verticals: 10.5 m west of the step, 7 m east) ----------
ry_L_front = [(155.7, 337.1), (190, 341.4), (218.6, 345.7), (250, 351.4), (282, 356)]
ry_L_rear = [(150, 361.4), (198.6, 372.9), (250, 382.9), (289, 390)]
ry_R_front = [(282, 356), (332.9, 360.9), (378.6, 362.9)]
ry_R_rear = [(289, 390), (332.9, 394.3), (378.6, 396.3)]
for nm, fr, rr_, z in (('ryder_w', ry_L_front, ry_L_rear, 10.5), ('ryder_e', ry_R_front, ry_R_rear, 7.0)):
    f = W(fr, z); r = W(rr_, z)
    a_, b_ = slab(nm, 'roof_ry', f, r, th=0.4, fascia='fascia', n=40)
    wall(nm + '_rear', 'brick_ry', b_, 0.0)
ryL_rear_w = W(ry_L_rear, 10.5); ryR_rear_w = W(ry_R_rear, 7.0)
# Ryder east: lower brick annex on the street side (photo x 312-372; roof edge y 418, foot y 428 -> 4.2 m high)
AZ = 4.2
af = W([(312, 418), (372, 417)], AZ); ab = W([(312, 401.5), (372, 400.5)], AZ)
atop = [ab[0], ab[1], af[1], af[0]]; abot = [np.r_[q[:2], 0.0] for q in atop]
add('ryder_annex_roof', 'concrete', atop, [[0, 1, 2, 3]])
for i, j in ((1, 2), (2, 3), (3, 0)):
    add('ryder_annex_w%d' % i, 'brick', [atop[i], atop[j], abot[j], abot[i]], [[0, 1, 2, 3]])

# ---------- NE corner building (low, 5 m) ----------
ne = W([(100, 331), (122.5, 308.3), (150, 313.3), (150, 359.2)], 5.0)
nb = ne.copy(); nb[:, 2] = 0
add('ne_roof', 'roof', ne, [[0, 1, 2, 3]])
for i in range(4):
    j = (i + 1) % 4; add('ne_w%d' % i, 'brick', [ne[i], ne[j], nb[j], nb[i]], [[0, 1, 2, 3]])

# ---------- east rim (crowd's outer edge; top of the embankment 5 m) with its outer wall ----------
rim_px = [(204, 95), (200, 121.3), (166.7, 134.7), (133.3, 148), (100, 176.3), (66.7, 196.3), (46.7, 216.3),
          (38.3, 236.3), (36.7, 259.7), (38.3, 286.3), (46.7, 306.3), (66.7, 323), (100, 331)]
RIMZ = 5.0
rim = W(rim_px, RIMZ)
rimw = resample(rim, 60)
wall('east_wall', 'white', rimw, 0.0)
# walkway band along the rim top (light concrete strip seen in the photo)
inner = rimw.copy(); d = -rimw[:, :2] / np.linalg.norm(rimw[:, :2], axis=1)[:, None]; inner[:, :2] += d * 2.5
ribbon('east_walk', 'concrete', rimw, inner, n=60)

# ---------- terrace ring: stepped rows, one sector per stand ----------
# each outer point: (xyz, sector). Sectors get their own row count so every tread is ~0.8 m deep (real plats).
grp = []
grp += [(np.r_[P[:2], 9.0], 'rush') for P in rr]
grp += [(P, 'sherrin') for P in sher_out]
grp += [(np.r_[P[:2], 3.0], 'social') for P in (SW, SE)]
grp += [(np.r_[P[:2], 4.0], 'ryder_e') for P in ryR_rear_w[::-1]]
grp += [(np.r_[P[:2], 7.0], 'ryder_w') for P in ryL_rear_w[::-1]]
grp += [(np.r_[P[:2], 4.0], 'ne') for P in ne[[3, 2, 1]]]
grp += [(np.r_[P[:2], RIMZ], 'outer') for P in rim[::-1]]
pts = np.array([g[0] for g in grp]); lab = np.array([g[1] for g in grp])
ang = np.arctan2(pts[:, 1] / B, pts[:, 0] / A)
o = np.argsort(ang); pts = pts[o]; ang = ang[o]; lab = lab[o]
N = 720
tt = np.linspace(-np.pi, np.pi, N, endpoint=False)
outer = np.array([[np.interp(t, ang, pts[:, k], period=2 * np.pi) for k in range(3)] for t in tt])
# sector of each sample = label of the nearest outer point in angle
dang = np.abs((tt[:, None] - ang[None, :] + np.pi) % (2 * np.pi) - np.pi)
slab_ = lab[np.argmin(dang, axis=1)].copy()
# a run shorter than 12 samples (interleaved rear lines) takes its neighbour's sector
for _ in range(3):
    i = 0
    while i < N:
        j = i
        while j < N and slab_[j] == slab_[i]: j += 1
        if j - i < 12: slab_[i:j] = slab_[i - 1]
        i = j
FZ = 1.0
innr = np.c_[(A + 1.5) * np.cos(tt), (B + 1.5) * np.sin(tt), np.full(N, FZ)]
fz = innr.copy(); fz[:, 2] = 0
# fence boards (2.5 m): each board painted red or white by the photo colour where it projects (colour read only)
from PIL import Image as _I
_ph = np.asarray(_I.open('photo.jpg').convert('RGB')).astype(int)
_rg = resample(np.r_[innr, innr[:1]], 2000); _d = np.r_[0, np.cumsum(np.linalg.norm(np.diff(_rg, axis=0), axis=1))]
NB = int(round(_d[-1] / 2.5)); _t = np.linspace(0, _d[-1], NB + 1)
_bp = np.array([[np.interp(t, _d, _rg[:, k]) for k in range(3)] for t in _t])
_mid = (_bp[:-1] + _bp[1:]) / 2; _mid[:, 2] = 0.6
_uv = proj(p, _mid); FENCE_RED = []
for k, (u, v) in enumerate(_uv):
    ui, vi = int(round(u)), int(round(v))
    if 1 <= ui < _ph.shape[1] - 1 and 1 <= vi < _ph.shape[0] - 1:
        # the fence line sits up to 8 px above the projected spot; a board is red when 3+ clearly red pixels lie there
        win = _ph[max(vi - 8, 0):vi + 1, ui - 1:ui + 2].reshape(-1, 3)
        red = (win[:, 0] > 140) & (win[:, 0] - win[:, 1] > 40) & (win[:, 0] - win[:, 2] > 30)
        if red.sum() >= 3: FENCE_RED.append(k)
FENCE_RED = []   # director 2026-11-18: no boards, bare fence at every ground (no ads)
for mt_, sel in (('fence', [k for k in range(NB) if k not in FENCE_RED]), ('fence_red', FENCE_RED)):
    V, F, UV = [], [], []
    for k in sel:
        a0, a1 = _bp[k], _bp[k + 1]; n0 = len(V)
        V += [a0, a1, np.r_[a1[:2], 0], np.r_[a0[:2], 0]]; F.append([n0, n0 + 1, n0 + 2, n0 + 3])
        UV += [(0, FZ), (2.5, FZ), (2.5, 0), (0, 0)]
    if V: add(mt_, mt_, V, F, UV)
print('fence boards', NB, 'red', len(FENCE_RED), FENCE_RED)
np.save('out/fence_uv.npy', np.c_[_uv, np.isin(np.arange(NB), FENCE_RED)])
TREAD = {'rush': 'plat', 'sherrin': 'plat', 'social': 'terr', 'ryder_e': 'plat', 'ryder_w': 'plat', 'ne': 'terr',
         'outer': 'terr'}
SEATED = {'rush', 'sherrin', 'ryder_e', 'ryder_w'}   # CMP: fixed timber benches on concrete plats
# split the ring into runs of equal sector
runs = []; i0 = 0
for i in range(1, N + 1):
    if i == N or slab_[i] != slab_[i0]:
        runs.append((i0, i, slab_[i0])); i0 = i
if len(runs) > 1 and runs[0][2] == runs[-1][2]:   # wrap the first run onto the last
    a0 = runs.pop(0); runs[-1] = (runs[-1][0], a0[1] + N, a0[2])
for (i0, i1, sec) in runs:
    idx = [k % N for k in range(i0, i1 + 1)]
    I = innr[idx]; O = outer[idx]
    depth = np.linalg.norm(O[:, :2] - I[:, :2], axis=1)
    R_ = max(3, int(round(np.median(depth) / 0.8)))
    n = len(idx); Vt = []; Ft = []; UVt = []; Vr = []; Fr = []; UVr = []; Vb = []; Fb = []; UVb = []
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(I[:, :2], axis=0), axis=1))]
    for r in range(R_):
        s0, s1 = r / R_, (r + 1) / R_
        P0 = I * (1 - s0) + O * s0; P1 = I * (1 - s1) + O * s1
        z1 = P1[:, 2]
        # riser: from row r's front edge up to its tread height
        base = len(Vr)
        Vr += list(np.c_[P0[:, :2], P0[:, 2]]) + list(np.c_[P0[:, :2], z1])
        UVr += [[a, 0] for a in arc] + [[a, 1] for a in arc]
        for k in range(n - 1): Fr.append([base + k, base + k + 1, base + n + k + 1, base + n + k])
        base = len(Vt)
        Vt += list(np.c_[P0[:, :2], z1]) + list(np.c_[P1[:, :2], z1])
        UVt += [[a, 0] for a in arc] + [[a, 1] for a in arc]
        for k in range(n - 1): Ft.append([base + k, base + k + 1, base + n + k + 1, base + n + k])
        if sec in SEATED:
            # timber bench (close-up photo 2026_6): seat plank 0.42 m up, 0.3 m deep; backrest 0.5-0.68 m up
            u = (P1 - P0)[:, :2]; u = u / np.linalg.norm(u, axis=1)[:, None]
            rear = P1[:, :2]
            for (d0, d1, h0, h1) in ((0.50, 0.20, 0.42, 0.42), (0.12, 0.12, 0.50, 0.68)):
                A0 = np.c_[rear - u * d0, z1 + h0]; A1 = np.c_[rear - u * d1, z1 + h1]
                base = len(Vb)
                Vb += list(A0) + list(A1)
                UVb += [[a, 0] for a in arc] + [[a, 1] for a in arc]
                for k in range(n - 1): Fb.append([base + k, base + k + 1, base + n + k + 1, base + n + k])
    if sec not in SEATED:
        # standing terrace: steel crush barriers (1.1 m pipe rail on posts every 3 m) on every 5th tread, and aisles
        # (1.2 m wide, a half-step in every row, white nosing) every 25 m along the fence, barriers broken at each aisle
        L = arc[-1]; AIS = [c for c in np.arange(12.5, L - 3.0, 25.0)] if L > 8 else []
        def at(a_, s_):
            P_ = np.array([np.interp(a_, arc, I[:, k]) for k in range(3)]) * (1 - s_) +                  np.array([np.interp(a_, arc, O[:, k]) for k in range(3)]) * s_
            return P_
        _zo = np.median(O[:, 2])
        def flat(a_):       # this sector's own terrace (not the slope where it meets a taller stand)
            return abs(np.interp(a_, arc, O[:, 2]) - _zo) < 0.75
        AIS = [c for c in AIS if flat(c - 0.6) and flat(c + 0.6)]
        def zrow(a_, r_):   # tread height of row r_ at arc a_
            return at(a_, (r_ + 1) / R_)[2] if r_ >= 0 else at(a_, 0)[2]
        Va, Fa, UVa = [], [], []
        for c in AIS:
            for r in range(R_):
                s0, s1 = r / R_, (r + 1) / R_; sm = (s0 + s1) / 2
                zl, zh = zrow(c, r - 1), zrow(c, r); zm = (zl + zh) / 2
                for (sa, sb, z_) in ((s0, sm, zm), (sm, s1, zh)):
                    q = [at(c - 0.6, sa), at(c + 0.6, sa), at(c + 0.6, sb), at(c - 0.6, sb)]
                    q = [np.r_[w_[:2], z_ + 0.012] for w_ in q]; n0 = len(Va)
                    Va += q; Fa.append([n0, n0 + 1, n0 + 2, n0 + 3]); UVa += [(0, 0), (1.2, 0), (1.2, 1), (0, 1)]
                    # riser face up to this half-step
                    zb = zl if sa == s0 else zm
                    q = [np.r_[at(c - 0.6, sa)[:2], zb], np.r_[at(c + 0.6, sa)[:2], zb],
                         np.r_[at(c + 0.6, sa)[:2], z_ + 0.012], np.r_[at(c - 0.6, sa)[:2], z_ + 0.012]]
                    n0 = len(Va); Va += q; Fa.append([n0, n0 + 1, n0 + 2, n0 + 3]); UVa += [(0, 0.5), (1.2, 0.5), (1.2, 0.9), (0, 0.9)]
        if Va: add('aisles_%s_%d' % (sec, i0), 'aisle', Va, Fa, UVa)
        Vs, Fs = [], []
        def bar(Pa_, Pb_, h0, h1, wdt):
            # a square steel member from Pa_ to Pb_ (plan) between heights: 4 side quads
            dd = (Pb_ - Pa_)[:2]; ll = np.linalg.norm(dd)
            if ll < 1e-6: dd = np.array([1.0, 0.0])
            else: dd = dd / ll
            nn = np.array([-dd[1], dd[0]]) * wdt / 2
            cs = [Pa_[:2] - nn, Pb_[:2] - nn, Pb_[:2] + nn, Pa_[:2] + nn]
            if ll < 1e-6: cs = [Pa_[:2] - nn - dd * wdt / 2, Pa_[:2] - nn + dd * wdt / 2, Pa_[:2] + nn + dd * wdt / 2, Pa_[:2] + nn - dd * wdt / 2]
            for k in range(4):
                c0, c1 = cs[k], cs[(k + 1) % 4]; n0 = len(Vs)
                Vs.extend([np.r_[c0, h0[k] if hasattr(h0, '__len__') else h0], np.r_[c1, h0[(k+1)%4] if hasattr(h0, '__len__') else h0],
                           np.r_[c1, h1[(k+1)%4] if hasattr(h1, '__len__') else h1], np.r_[c0, h1[k] if hasattr(h1, '__len__') else h1]])
                Fs.append([n0, n0 + 1, n0 + 2, n0 + 3])
        gaps = [(c - 1.0, c + 1.0) for c in AIS]
        for r in range(4, R_ - 1, 5):
            sb_ = (r + 1) / R_ - 0.15 / max(np.median(depth), 1)       # 15 cm in from the tread's back edge
            st = 0.0
            for (g0, g1) in gaps + [(L - 0.3, L + 1)]:
                a0_, a1_ = st + 0.3, g0
                if a1_ - a0_ > 1.0:
                    aa = np.linspace(a0_, a1_, max(2, int((a1_ - a0_) / 1.5) + 1))
                    for k in range(len(aa) - 1):
                        if not (flat(aa[k]) and flat(aa[k + 1])): continue
                        P0_, P1_ = at(aa[k], sb_), at(aa[k + 1], sb_); z0_ = zrow(aa[k], r)
                        bar(P0_, P1_, z0_ + 1.04, z0_ + 1.10, 0.06)                    # top rail
                    for a_ in np.arange(a0_, a1_ + 1e-6, 3.0):
                        if not flat(a_): continue
                        P_ = at(a_, sb_); z0_ = zrow(a_, r); bar(P_, P_, z0_, z0_ + 1.04, 0.06)   # post
                st = g1
        if Vs: add('barriers_%s_%d' % (sec, i0), 'steel', Vs, Fs)
        print('  terrace', sec, 'aisles', len(AIS), 'barrier rows', len(range(4, R_ - 1, 5)))
    if Vb: add('benches_%s_%d' % (sec, i0), 'bench', Vb, Fb, UVb)
    add('rows_%s_%d' % (sec, i0), TREAD[sec], Vt, Ft, UVt)
    add('risers_%s_%d' % (sec, i0), 'riser', Vr, Fr, UVr)
    print('sector', sec, 'samples', n, 'rows', R_, 'depth', np.median(depth).round(1))

# ---------- concourse apron, SW corner (Lulie / Turner) ----------
con_px = [(560, 100), (600, 107), (650, 116), (700, 126), (708, 170), (692, 212), (683, 213)]
con = W(con_px, 0.03)
ra = np.array([np.r_[P[:2], 0.03] for P in rr[-6:][::-1]])
V = np.r_[con, ra]; add('concourse', 'asphalt', V, [list(range(len(V)))])

# ---------- ground the stadium sits on, out to its outer walls only (director: stadium only, no surroundings) ----------
from scipy.spatial import ConvexHull
_xy = np.array([v[:2] for m in MESH for v in m['v']]); _h = _xy[ConvexHull(_xy).vertices]
_c = _xy.mean(0); _h = _c + (_h - _c) * (1 + 2.0 / np.linalg.norm(_h - _c, axis=1))[:, None]   # 2 m past the outer face
# ring from the boundary fence out to the hull (inside the fence stays empty: the game draws the turf)
def _hull_r(th):
    d = np.array([np.cos(th), np.sin(th)]); best = 0
    for k in range(len(_h)):
        A_, B_ = _h[k], _h[(k + 1) % len(_h)]; e = B_ - A_
        M_ = np.array([[d[0], -e[0]], [d[1], -e[1]]])
        if abs(np.linalg.det(M_)) < 1e-9: continue
        sv, tv = np.linalg.solve(M_, A_)
        if sv > 0 and 0 <= tv <= 1: best = max(best, sv)
    return best
_th = np.linspace(-np.pi, np.pi, 360, endpoint=False)
_in = np.c_[(A + 1.5) * np.cos(_th), (B + 1.5) * np.sin(_th), np.full(360, -0.05)]
_ou = np.array([np.r_[np.array([np.cos(t), np.sin(t)]) * max(_hull_r(t), np.hypot(*q[:2]) + 1), -0.05] for t, q in zip(_th, _in)])
Vg = np.r_[_in, _ou]
add('ground_apron', 'asphalt', Vg, [[i, (i + 1) % 360, 360 + (i + 1) % 360, 360 + i] for i in range(360)], Vg[:, :2])

# ---------- light pole (23.6 m, tapering) with two lamp heads ----------
pb = np.array([-58.4, 83.6]); PH = 23.6
n = 10; V = []; F = []
for k, (z, r) in enumerate(((0, 0.35), (PH, 0.15))):
    for i in range(n):
        t = 2 * np.pi * i / n; V.append([pb[0] + r * np.cos(t), pb[1] + r * np.sin(t), z])
for i in range(n):
    j = (i + 1) % n; F.append([i, j, n + j, n + i])
add('pole', 'white', V, F)
for k, dx in enumerate((-0.9, 0.9)):
    c0 = np.r_[pb + [dx, 0], PH]
    V = [c0 + [sx * 0.5, sy * 0.4, sz * 0.6] for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
    F = [[0, 1, 3, 2], [4, 6, 7, 5], [0, 4, 5, 1], [2, 3, 7, 6], [0, 2, 6, 4], [1, 5, 7, 3]]
    add('lamp%d' % k, 'white', V, F)

json.dump(MESH, open('meshes.json', 'w'))
print(len(MESH), 'meshes; rush roof depth', round(dep, 1))
for nm, X in (('rush front', rf), ('rush rear', rr), ('sherrin front', sf), ('sherrin rear', sr)):
    print(nm, X[[0, -1], :2].round(1).tolist())
