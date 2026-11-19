"""Re-cut the guernsey's armholes in player_mh.glb along one smooth line each.

The guernsey (ARD_guernsey) and the skin (ARD_skin) are the body's own triangles, split by region
along whole triangles, so each armhole's edge zigzags. For each armhole: the plane of its edge
loop (Newell normal, through the loop's middle). Every skin or guernsey triangle within BAND of
the old edge is split along that plane; the torso side goes to the guernsey, the arm side to the
skin. Plane and body meet in a smooth curve, so the new edge is one clean line. Every vertex
attribute (skin coords, guernsey coords, weights) and the body morphs are interpolated along the
split edges, so nothing else changes.

python recut.py IN.glb OUT.glb
"""
import json, struct, sys
import numpy as np

BAND = 0.035  # metres from the old edge where triangles may change side

src, OUTP = sys.argv[1], sys.argv[2]
raw = open(src, 'rb').read()
jl = struct.unpack('<I', raw[12:16])[0]
J = json.loads(raw[20:20 + jl])
B = raw[20 + jl + 8:]
COMP = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}
KN = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def view_bytes(vi):
    v = J['bufferViews'][vi]
    o = v.get('byteOffset', 0)
    return B[o:o + v['byteLength']], v.get('byteStride', 0)


def read(ai):
    a = J['accessors'][ai]
    comp, k = COMP[a['componentType']], KN[a['type']]
    isz = np.dtype(comp).itemsize
    n = a['count']
    if 'bufferView' in a:
        vb, st = view_bytes(a['bufferView'])
        o = a.get('byteOffset', 0)
        st = st or k * isz
        idx = o + np.arange(n)[:, None] * st + np.arange(k * isz)[None, :]
        out = np.frombuffer(np.frombuffer(vb, np.uint8)[idx].tobytes(), comp).reshape(n, k).copy()
    else:
        out = np.zeros((n, k), comp)
    if 'sparse' in a:
        s = a['sparse']
        ib, _ = view_bytes(s['indices']['bufferView'])
        ii = np.frombuffer(ib, COMP[s['indices']['componentType']], s['count'], s['indices'].get('byteOffset', 0))
        vb2, _ = view_bytes(s['values']['bufferView'])
        vv = np.frombuffer(vb2, comp, s['count'] * k, s['values'].get('byteOffset', 0)).reshape(-1, k)
        out[ii.astype(np.int64)] = vv
    return out


prims = J['meshes'][0]['primitives']
mats = [J['materials'][p['material']]['name'] for p in prims]
SK, GU = mats.index('ARD_skin'), mats.index('ARD_guernsey')


def load_prim(p):
    attrs = {k: read(v) for k, v in p['attributes'].items()}
    tg = [{k: read(v).astype(np.float64) for k, v in t.items()} for t in p['targets']]
    ind = read(p['indices']).ravel().astype(np.int64).reshape(-1, 3)
    return attrs, tg, ind


S = load_prim(prims[SK])
G = load_prim(prims[GU])
SH = load_prim(prims[mats.index('ARD_shorts')])

# The guernsey's open edges, welded; the two side loops high up are the armholes.
gp = G[0]['POSITION'].astype(np.float64)
gn = G[0]['NORMAL'].astype(np.float64)
key = np.round(gp * 1e5).astype(np.int64)
_, wid = np.unique(key, axis=0, return_inverse=True)
wid = wid.ravel()
T = wid[G[2]]
E = np.sort(np.r_[T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]], 1)
u, cnt = np.unique(E, axis=0, return_counts=True)
bd = u[cnt == 1]
pts = np.zeros((wid.max() + 1, 3))
pts[wid] = gp
nbr = {}
for a, b in bd:
    nbr.setdefault(a, []).append(b)
    nbr.setdefault(b, []).append(a)
loops, seen = [], set()
for v0 in nbr:
    if v0 in seen:
        continue
    ids, cur = [v0], v0
    seen.add(v0)
    while True:
        nx = [w for w in nbr[cur] if w not in seen]
        if not nx:
            break
        cur = nx[0]
        seen.add(cur)
        ids.append(cur)
    if len(ids) >= 8:
        loops.append(pts[ids])
loops.sort(key=lambda l: l[:, 1].mean())
rest = loops[1:]
rest.sort(key=lambda l: abs(l[:, 0].mean()))
arms = rest[1:3]
assert len(arms) == 2, len(loops)

# ---- the photo's outline and pattern, wrapped round the body ----
from unroll import unroll
from scipy import ndimage as nd
from PIL import Image
CODE = sys.argv[3]
PA = np.r_[S[0]['POSITION'], G[0]['POSITION']].astype(np.float64)
TA = np.r_[S[2], G[2] + len(S[0]['POSITION'])]
Q, WID, SF, SB, HH, ZC, DS = unroll(PA, TA)
nS = len(S[0]['POSITION'])
ARMPIT_PX, ARMPIT_H = 765.0, 0.2979
masks, hw, cx, TOP = {}, {}, {}, {}
for side in ('front', 'back'):
    al = np.array(Image.open(f'design_{CODE}_{side}.png'))[..., 3] > 127
    sd = nd.distance_transform_edt(al) - nd.distance_transform_edt(~al)
    masks[side] = sd
    rows = np.arange(al.shape[0])
    lo = np.array([np.nonzero(r)[0].min() if r.any() else 0 for r in al])
    hi = np.array([np.nonzero(r)[0].max() if r.any() else 0 for r in al])
    hw[side] = (hi - lo) / 2.0
    cx[side] = (hi + lo) / 2.0
    cols = np.where(al.any(0))[0]
    top = np.array([np.nonzero(al[:, c])[0].min() for c in cols], float)
    hull = []
    for p in zip(cols, top):
        while len(hull) >= 2 and (hull[-1][0] - hull[-2][0]) * (p[1] - hull[-2][1]) - (hull[-1][1] - hull[-2][1]) * (p[0] - hull[-2][0]) < 0:
            hull.pop()
        hull.append(p)
    hull = np.array(hull)
    TOP[side] = (hull[:, 0], hull[:, 1])
CHEST = 860
KY = hw['front'][CHEST] / 0.2429   # px per metre (the chest's quarter round = the flat front's half width)
print('px per metre', KY)
S_PX = 2310.0
KY = S_PX
Y_ARMPIT = 1.37
# the body's torso half-width per height below the armpit (front view, arms excluded)
BODY_Y, BODY_HW = [], []
_gp = G[0]['POSITION'].astype(np.float64)
for yy in np.arange(1.08, Y_ARMPIT + 0.001, 0.01):
    rr = np.abs(_gp[np.abs(_gp[:, 1] - yy) < 0.006, 0])
    BODY_Y.append(yy); BODY_HW.append(rr.max())
BODY_Y = np.array(BODY_Y); BODY_HW = np.array(BODY_HW)
BODY_HW[BODY_Y < 1.10] = BODY_HW[np.argmin(np.abs(BODY_Y - 1.10))]   # the hem rows are sparse
# front/back split: the body's mid-depth per height (the camera sees the front half from the front)
ZM_Y = np.arange(1.08, 1.61, 0.01)
ZM = np.array([(lambda z: (z.max() + z.min()) / 2)(_gp[np.abs(_gp[:, 1] - yy) < 0.006, 2]) for yy in ZM_Y])
ZM[ZM_Y < 1.15] = ZM[np.argmin(np.abs(ZM_Y - 1.15))]  # the hem's last rows are too sparse to find the middle
BODY_HW_ARM = 452.5 / S_PX
print('body half-widths', np.round(BODY_HW, 3))

def photo(i_w, x):
    """Welded vertex ids + x sign -> (side 0 front 1 back, px, py)."""
    return photo_from(SF[i_w], SB[i_w], DS[i_w], np.sign(x), Q[i_w])

def top_at(side, px):
    return np.interp(px, *TOP[side])

def photo_from(sf, sb, ds, sg, P=None):
    """Front projection matched to the body: the photo is a ghost-mannequin shot, so a point's
    photo pixel is where the camera sees it. Top of the shoulder line beside the neck (photo row
    189) = body y 1.62; one scale, 2310 px per metre; below the armpit each row's width is fitted to
    the body's own width so the side seams meet the body's sides."""
    x, y = P[:, 0], P[:, 1]
    back = P[:, 2] < np.interp(y, ZM_Y, ZM)
    py = 189.0 + (1.62 - y) * S_PX
    row = np.clip(py, 0, 1999).astype(int)
    k = np.where(y < Y_ARMPIT, np.interp(y, BODY_Y, BODY_HW), BODY_HW_ARM)
    pxf = cx['front'][CHEST] + x * np.where(y < Y_ARMPIT, hw['front'][np.maximum(row, 765)] / k, S_PX)
    pxb = cx['back'][CHEST] - x * np.where(y < Y_ARMPIT, hw['back'][np.maximum(row, 765)] / k, S_PX)
    return back, np.where(back, pxb, pxf), py

def sample(sd, px, py):
    return nd.map_coordinates(sd, [py, px], order=1, mode='nearest')

def side_dist_w(ids_w, X):
    back, px, py = photo(ids_w, X[:, 0])
    d = np.where(back, sample(masks['back'], px, py), sample(masks['front'], px, py))
    return d / KY

# which welded id each prim vertex is
WS = WID[:nS]; WG = WID[nS:]
KEYMAP = {}
def wid_of(src_id, i):
    return (WS if src_id == SK else WG)[i]

# only near the guernsey's neck and armholes (old loops) may a triangle change side: the hem stays
gp = G[0]['POSITION'].astype(np.float64)
key = np.round(gp * 1e5).astype(np.int64)
_, wid = np.unique(key, axis=0, return_inverse=True)
wid = wid.ravel()
T = wid[G[2]]
E = np.sort(np.r_[T[:, [0, 1]], T[:, [1, 2]], T[:, [2, 0]]], 1)
u_, cnt = np.unique(E, axis=0, return_counts=True)
bd = u_[cnt == 1]
pts = np.zeros((wid.max() + 1, 3)); pts[wid] = gp
edge_pts = pts[np.unique(bd)]
edge_pts = edge_pts[edge_pts[:, 1] > 1.2]
from scipy.spatial import cKDTree
EDGE_TREE = cKDTree(edge_pts)
BAND = 0.09

def near_edge(P):
    d, _ = EDGE_TREE.query(P)
    return d, np.zeros(len(P), np.int64)

class Prim:
    def __init__(self, data):
        self.attrs = {k: [v] for k, v in data[0].items()}
        self.tg = [{k: [v] for k, v in t.items()} for t in data[1]]
        self.n = len(data[0]['POSITION'])
        self.tris = []

    def add(self, row):
        """row: dict attr -> 1D value, targets list of dicts."""
        for k, v in row['a'].items():
            self.attrs[k].append(v[None, :])
        for t, tv in zip(self.tg, row['t']):
            for k, v in tv.items():
                t[k].append(v[None, :])
        self.n += 1
        return self.n - 1

    def done(self):
        a = {k: np.concatenate(v) for k, v in self.attrs.items()}
        t = [{k: np.concatenate(v) for k, v in tt.items()} for tt in self.tg]
        return a, t, np.array(self.tris, np.int64).reshape(-1, 3)


def vrow(data, i):
    return {'a': {k: v[i] for k, v in data[0].items()}, 't': [{k: v[i] for k, v in t.items()} for t in data[1]]}


def mix(data, i, j, f):
    """The vertex f of the way from i to j."""
    r = {'a': {}, 't': []}
    for k, v in data[0].items():
        x, y = v[i].astype(np.float64), v[j].astype(np.float64)
        if k == '_UNR':
            r['a'][k] = x + (y - x) * f
            r['a'][k][3] = x[3] if x[3] != 0 else y[3]
            continue
        if k in ('JOINTS_0', 'WEIGHTS_0'):
            continue
        z = x + (y - x) * f
        if k == 'NORMAL':
            z /= max(np.linalg.norm(z), 1e-9)
        if k == 'TANGENT':
            z[:3] /= max(np.linalg.norm(z[:3]), 1e-9)
            z[3] = x[3]
        if k == 'COLOR_0':
            z = np.round(z)
        r['a'][k] = z.astype(v.dtype)
    # Skin weights: both ends' bones, shared by the split, the four biggest kept.
    w = {}
    for idx, s in ((i, 1 - f), (j, f)):
        for b, ww in zip(data[0]['JOINTS_0'][idx], data[0]['WEIGHTS_0'][idx].astype(np.float64)):
            if ww > 0:
                w[int(b)] = w.get(int(b), 0.0) + ww * s
    top = sorted(w.items(), key=lambda kv: -kv[1])[:4]
    tot = sum(x for _, x in top)
    jt = np.zeros(4, data[0]['JOINTS_0'].dtype)
    wt = np.zeros(4, np.float64)
    for q, (b, x) in enumerate(top):
        jt[q], wt[q] = b, x / tot
    wdt = data[0]['WEIGHTS_0'].dtype
    if wdt == np.float32:
        r['a']['WEIGHTS_0'] = wt.astype(np.float32)
    else:
        mx = np.iinfo(wdt).max
        wi = np.round(wt * mx)
        wi[0] += mx - wi.sum()
        r['a']['WEIGHTS_0'] = wi.astype(wdt)
    r['a']['JOINTS_0'] = jt
    for t in data[1]:
        r['t'].append({k: v[i] + (v[j] - v[i]) * f for k, v in t.items()})
    return r


for d0, ww in ((S, WID[:nS]), (G, WID[nS:])):
    d0[0]['_UNR'] = np.c_[SF[ww], SB[ww], DS[ww], np.sign(d0[0]['POSITION'][:, 0])].astype(np.float64)
out = {SK: Prim(S), GU: Prim(G)}
moved = {SK: 0, GU: 0}
splits = 0
for src_id, data in ((SK, S), (GU, G)):
    P = data[0]['POSITION'].astype(np.float64)
    tri = data[2]
    cen = P[tri].mean(1)
    dist, which = near_edge(cen)
    # Each vertex of the source carried over to the other surface, once.
    carried = {SK: {}, GU: {}}
    cut = {}

    def put(dst, i):
        if dst == src_id:
            return i
        c = carried[dst]
        if i not in c:
            c[i] = out[dst].add(vrow(data, i))
        return c[i]

    def edge_point(i, j):
        k = (min(i, j), max(i, j))
        if k not in cut:
            a, b = k
            sa, sb = side_dist_w(np.array([wid_of(src_id, a), wid_of(src_id, b)]), P[[a, b]])
            f = sa / (sa - sb)
            row = mix(data, a, b, f)
            cut[k] = {SK: None, GU: None, 'row': row}
        e = cut[k]
        return e

    def ep_index(e, dst):
        if e[dst] is None:
            e[dst] = out[dst].add(e['row'])
        return e[dst]

    for t in range(len(tri)):
        ids = tri[t]
        if dist[t] > BAND:
            out[src_id].tris.append(ids.tolist())
            continue
        cur_plane = which[t]
        s = side_dist_w(np.array([wid_of(src_id, i) for i in ids]), P[ids])
        side = [GU if x >= 0 else SK for x in s]
        if side[0] == side[1] == side[2]:
            dst = side[0]
            if dst != src_id:
                moved[src_id] += 1
            out[dst].tris.append([put(dst, i) for i in ids])
            continue
        splits += 1
        # Rotate so vertex 0 is the one alone on its side.
        for r in range(3):
            if side[r] != side[(r + 1) % 3] and side[r] != side[(r + 2) % 3]:
                break
        a, b, cc = ids[r], ids[(r + 1) % 3], ids[(r + 2) % 3]
        lone, pair = side[r], side[(r + 1) % 3]
        eab, eac = edge_point(a, b), edge_point(a, cc)
        out[lone].tris.append([put(lone, a), ep_index(eab, lone), ep_index(eac, lone)])
        out[pair].tris.append([ep_index(eab, pair), put(pair, b), put(pair, cc)])
        out[pair].tris.append([ep_index(eab, pair), put(pair, cc), ep_index(eac, pair)])

print(f"triangles split {splits}, moved skin->guernsey {moved[SK]}, guernsey->skin {moved[GU]}")

# ---- write: compact buffer with only referenced views, new accessors for the two primitives ----
newB = bytearray()
views = []


def add_view(data, target=None):
    while len(newB) % 16:
        newB.append(0)
    v = {'buffer': 0, 'byteOffset': len(newB), 'byteLength': len(data)}
    if target:
        v['target'] = target
    newB.extend(data)
    views.append(v)
    return len(views) - 1


remap = {}


def keep_view(vi):
    if vi not in remap:
        vb, st = view_bytes(vi)
        old = J['bufferViews'][vi]
        nv = add_view(vb, old.get('target'))
        if st:
            views[nv]['byteStride'] = st
        remap[vi] = nv
    return remap[vi]


accs = J['accessors']
# The two re-cut surfaces' old data is replaced below: left out of the file (a tiny stub keeps the
# accessor numbering).
gone = set()

def fill_small_holes(a, tri, maxlen=40):
    """Close every open loop of up to maxlen corners (holes the cut left), fanned from one corner,
    winding the same way as the triangles round it."""
    P = a['POSITION'].astype(np.float64)
    key = np.round(P * 1e4).astype(np.int64)
    _, w = np.unique(key, axis=0, return_inverse=True)
    w = w.ravel()
    rep = {}
    for i in range(len(P)):
        rep.setdefault(w[i], i)
    cnt = {}
    for t3 in tri:
        for q in range(3):
            u, v = w[t3[q]], w[t3[(q + 1) % 3]]
            k2 = (min(u, v), max(u, v))
            cnt[k2] = cnt.get(k2, 0) + 1
    nxt = {}
    for t3 in tri:
        for q in range(3):
            u, v = w[t3[q]], w[t3[(q + 1) % 3]]
            if cnt[(min(u, v), max(u, v))] == 1:
                nxt[v] = u  # the hole runs the other way round
    seen, add = set(), []
    for s0 in list(nxt):
        if s0 in seen:
            continue
        loop, x = [], s0
        while x not in seen and x in nxt:
            seen.add(x); loop.append(x); x = nxt[x]
        if x == s0 and 3 <= len(loop) <= maxlen:
            for k in range(1, len(loop) - 1):
                add.append([rep[loop[0]], rep[loop[k]], rep[loop[k + 1]]])
            print('filled hole', len(loop), P[rep[loop[0]]].round(3))
    if add:
        tri = np.r_[tri, np.array(add, np.int64)]
    return tri


for pid in (SK, GU):
    p = prims[pid]
    gone.update(p['attributes'].values())
    gone.add(p['indices'])
    for t in p['targets']:
        gone.update(t.values())
used_elsewhere = set()
for mi, m in enumerate(J['meshes']):
    for pi, p in enumerate(m['primitives']):
        if mi == 0 and pi in (SK, GU):
            continue
        used_elsewhere.update(p['attributes'].values())
        used_elsewhere.update([p['indices']] if 'indices' in p else [])
        for t in p.get('targets', []):
            used_elsewhere.update(t.values())
gone -= used_elsewhere
# Their types (a colour is stored as normalised shorts, a joint as bytes) before the stubs.
orig_acc = {i: dict(accs[i]) for i in gone}
for i in gone:
    accs[i] = {'componentType': 5126, 'count': 1, 'type': 'SCALAR'}
for a in accs:
    if 'bufferView' in a:
        a['bufferView'] = keep_view(a['bufferView'])
    if 'sparse' in a:
        a['sparse']['indices']['bufferView'] = keep_view(a['sparse']['indices']['bufferView'])
        a['sparse']['values']['bufferView'] = keep_view(a['sparse']['values']['bufferView'])
for im in J.get('images', []):
    if 'bufferView' in im:
        im['bufferView'] = keep_view(im['bufferView'])

TYPE = {1: 'SCALAR', 2: 'VEC2', 3: 'VEC3', 4: 'VEC4'}
CT = {np.dtype(np.float32): 5126, np.dtype(np.uint16): 5123, np.dtype(np.uint32): 5125, np.dtype(np.uint8): 5121}


def new_acc(arr, old=None, target=34962, minmax=False, sparse_ok=False):
    arr = np.ascontiguousarray(arr)
    a = {'componentType': CT[arr.dtype], 'count': int(arr.shape[0]), 'type': TYPE[arr.shape[1] if arr.ndim > 1 else 1]}
    if old is not None and old.get('normalized'):
        a['normalized'] = True
    nz = np.nonzero(np.any(arr != 0, axis=1))[0] if arr.ndim > 1 else None
    if sparse_ok and nz is not None and len(nz) * 4 < arr.shape[0] * 3:
        a['sparse'] = {'count': int(len(nz)),
                       'indices': {'bufferView': add_view(nz.astype(np.uint32).tobytes()), 'componentType': 5125},
                       'values': {'bufferView': add_view(arr[nz].tobytes())}}
        if len(nz) == 0:
            del a['sparse']
    else:
        a['bufferView'] = add_view(arr.tobytes(), target)
    if minmax:
        a['min'] = arr.min(0).astype(float).tolist()
        a['max'] = arr.max(0).astype(float).tolist()
    accs.append(a)
    return len(accs) - 1


Y_BOT = 1.62 - (1764 - 189) / S_PX      # the photo's hem
RINGS = 8
# the photo's half-width and middle per row (both sides averaged), smoothed over 2 cm
_k = np.ones(45) / 45
for _sd in ('front', 'back'):
    _ok = np.nonzero(hw[_sd] > 0)[0]
    _near = _ok[np.clip(np.searchsorted(_ok, np.arange(2000)), 0, len(_ok) - 1)]
    cx[_sd] = cx[_sd][_near]; hw[_sd] = hw[_sd][_near]
cx_row = {sd: np.convolve(np.pad(cx[sd], 22, mode='edge'), _k, 'valid') for sd in ('front', 'back')}
HW_ROW = np.convolve(np.pad((hw['front'] + hw['back']) / 2, 22, mode='edge'), _k, 'valid') / S_PX
SHP = SH[0]['POSITION'].astype(np.float64)
SHN = SH[0]['NORMAL'].astype(np.float64)
SMOOTH_TOP = 1.26
CLEAR = 0.01
SKIN_T = None


def target_hw(y):
    return HW_ROW[np.clip(189.0 + (1.62 - y) * S_PX, 0, 1999).astype(int)]


def shape_to_photo(a, t, tri):
    """Below the armpit, the sides out to the photo's width (x only); then a panel from the hem
    down to the photo's hem, 1 cm clear of the shorts, moving with the hem (the hips)."""
    P = a['POSITION'].astype(np.float64)
    y = P[:, 1]
    k = np.interp(y, BODY_Y, BODY_HW)
    f = np.where(y < Y_ARMPIT, np.maximum(1.0, target_hw(y) / k), 1.0)
    P[:, 0] *= f
    a['POSITION'] = P.astype(np.float32)
    # the hem: open edges low on the body (welded), each with its own triangle's corners
    key = np.round(P / f[:, None] * 1e5).astype(np.int64)
    _, w = np.unique(key, axis=0, return_inverse=True)
    w = w.ravel()
    E = {}
    for ti, (i0, i1, i2) in enumerate(tri):
        for u, v in ((i0, i1), (i1, i2), (i2, i0)):
            kk = (min(w[u], w[v]), max(w[u], w[v]))
            E.setdefault(kk, []).append((u, v))
    hem = [e[0] for kk, e in E.items() if len(e) == 1 and P[e[0][0], 1] < 1.2 and P[e[0][1], 1] < 1.2]
    print('hem edges', len(hem))
    n = len(P)
    newv = {}
    rows_a = {kk: [] for kk in a}
    rows_t = [{kk: [] for kk in tt} for tt in t]
    newP = []

    def ring_pt(i, r):
        if (i, r) in newv:
            return newv[(i, r)]
        h = P[i]
        yy = h[1] + (Y_BOT - h[1]) * r / RINGS
        x = h[0] * target_hw(np.array([yy]))[0] / max(target_hw(np.array([h[1]]))[0], 1e-6)
        # 1 cm clear of the shorts at that height, along the line from the body's middle
        band = SHP[np.abs(SHP[:, 1] - yy) < 0.01]
        zc = (band[:, 2].max() + band[:, 2].min()) / 2 if len(band) else h[2]
        d = np.array([x, h[2] - zc])
        ln = np.linalg.norm(d)
        if len(band) and ln > 1e-6:
            dirn = d / ln
            rel = band[:, [0, 2]] - [0, zc]
            along = rel @ dirn
            perp = np.abs(rel @ np.array([-dirn[1], dirn[0]]))
            near = along[perp < 0.015]
            if len(near):
                ln = max(ln, near.max() + 0.01)
        q = np.array([0.0, yy, zc]) + np.array([dirn[0] * ln, 0, dirn[1] * ln]) if ln > 1e-6 else np.array([x, yy, h[2]])
        idx = n + len(newP)
        newP.append(q)
        for kk in a:
            rows_a[kk].append(a[kk][i])
        for ti, tt in enumerate(t):
            for kk in tt:
                rows_t[ti][kk].append(tt[kk][i])
        newv[(i, r)] = idx
        return idx

    new_tris = []
    for (u, v) in hem:
        # the hem triangle runs u -> v; the panel below runs v -> u so it faces the same way
        for r in range(RINGS):
            u0 = u if r == 0 else ring_pt(u, r)
            v0 = v if r == 0 else ring_pt(v, r)
            u1, v1 = ring_pt(u, r + 1), ring_pt(v, r + 1)
            new_tris += [[v0, u0, u1], [v0, u1, v1]]
    for kk in a:
        a[kk] = np.concatenate([a[kk], np.array(rows_a[kk], a[kk].dtype)])
    a['POSITION'][n:] = np.array(newP, np.float32)
    for ti, tt in enumerate(t):
        for kk in tt:
            tt[kk] = np.concatenate([tt[kk], np.array(rows_t[ti][kk], tt[kk].dtype)])
    tri = np.r_[tri, np.array(new_tris, np.int64)]
    # Smooth the whole lower guernsey together (the panel and the body-moulded rows above it, fading
    # out by 1.26 m), Taubin steps so it doesn't shrink; then kept clear of the shorts and the torso
    # skin by a signed test along their own normals.
    PP = a['POSITION'].astype(np.float64)
    keyw = np.round(PP * 1e5).astype(np.int64)
    _, ww = np.unique(keyw, axis=0, return_inverse=True)
    ww = ww.ravel()
    T_all = np.asarray(tri)
    nW = ww.max() + 1
    pos = np.zeros((nW, 3)); pos[ww] = PP
    eu = np.r_[ww[T_all[:, 0]], ww[T_all[:, 1]], ww[T_all[:, 2]]]
    ev = np.r_[ww[T_all[:, 1]], ww[T_all[:, 2]], ww[T_all[:, 0]]]
    import scipy.sparse as sps
    Adj = sps.coo_matrix((np.ones(len(eu)), (eu, ev)), shape=(nW, nW)).tocsr()
    Adj = ((Adj + Adj.T) > 0).astype(np.float64)
    deg = np.asarray(Adj.sum(1)).ravel()
    ramp = np.clip((SMOOTH_TOP - pos[:, 1]) / 0.10, 0, 1)
    bottom = np.abs(pos[:, 1] - Y_BOT) < 1e-6
    from scipy.spatial import cKDTree
    CP = np.r_[SHP, SKIN_T[0]]
    CN = np.r_[SHN, SKIN_T[1]]
    CN /= np.maximum(np.linalg.norm(CN, axis=1, keepdims=True), 1e-12)
    ctree = cKDTree(CP)

    def clear(pos):
        d, j = ctree.query(pos, k=6)
        for kk in range(6):
            s_ = ((pos - CP[j[:, kk]]) * CN[j[:, kk]]).sum(1)
            fix = (s_ < CLEAR) & (d[:, kk] < 0.04) & (ramp > 0)
            pos[fix] += CN[j[fix, kk]] * (CLEAR - s_[fix])[:, None]
        return pos

    for it in range(60):
        for lam in (0.5, -0.53):
            m = (Adj @ pos) / np.maximum(deg, 1)[:, None]
            step = lam * ramp[:, None] * (m - pos)
            step[bottom, 1] = 0
            pos = pos + step
        pos = clear(pos)
    PP = pos[ww]
    a['POSITION'] = PP.astype(np.float32)
    # The panel moves with the hips as the shorts under it do: each panel corner takes the skin
    # weights of the nearest shorts corner (the hem ring keeps its own).
    _sj, _sw = SH[0]['JOINTS_0'], SH[0]['WEIGHTS_0']
    _d, _j = cKDTree(SHP).query(PP[n:])
    a['JOINTS_0'][n:] = _sj[_j].astype(a['JOINTS_0'].dtype)
    a['WEIGHTS_0'][n:] = _sw[_j].astype(a['WEIGHTS_0'].dtype)
    # Normals from the faces, on the panel and the old hem's last rows (welded, area-weighted).
    T3 = np.asarray(tri)
    fn = np.cross(PP[T3[:, 1]] - PP[T3[:, 0]], PP[T3[:, 2]] - PP[T3[:, 0]])
    acc_n = np.zeros((ww.max() + 1, 3))
    for q in range(3):
        np.add.at(acc_n, ww[T3[:, q]], fn)
    NN = acc_n[ww]
    NN /= np.maximum(np.linalg.norm(NN, axis=1, keepdims=True), 1e-12)
    low = PP[:, 1] < SMOOTH_TOP
    a['NORMAL'][low] = NN[low].astype(a['NORMAL'].dtype)
    tg = a['TANGENT'][low, :3].astype(np.float64)
    tg -= NN[low] * (tg * NN[low]).sum(1, keepdims=True)
    tg /= np.maximum(np.linalg.norm(tg, axis=1, keepdims=True), 1e-12)
    a['TANGENT'][low, :3] = tg.astype(a['TANGENT'].dtype)
    print('panel verts', len(newP), 'tris', len(new_tris), 'widest x', np.abs(a['POSITION'][:, 0]).max())
    return a, t, tri


for pid in (SK, GU):
    p = prims[pid]
    a, t, tri = out[pid].done()
    # Vertices new to this surface (carried over from the other one, or on the cut) take this
    # surface's own coordinates: the guernsey's pattern coordinates are a fixed function of the
    # position (UV0) or copied from the nearest original guernsey corner (UV1, the colour regions),
    # and the skin's colour regions from its nearest original corner. Without this a skin triangle
    # moved onto the guernsey kept the skin's coordinates and showed no stripes.
    n0 = len((S if pid == SK else G)[0]['POSITION'])
    if len(a['POSITION']) > n0:
        P0 = a['POSITION'][:n0].astype(np.float64)
        Pn = a['POSITION'][n0:].astype(np.float64)
        near = np.array([np.argmin(((P0 - q) ** 2).sum(1)) for q in Pn])
        keys = ['COLOR_0'] + (['TEXCOORD_1'] if pid == GU else [])
        for k in keys:
            if k in a:
                a[k][n0:] = a[k][near]

    if pid == GU:
        a, t, tri = shape_to_photo(a, t, tri)
        tri = fill_small_holes(a, tri)
        # Front and back split on the guernsey's own depth-middle, as the game measures it
        # (Oval3D._depth_middle: every 1 cm, corners within 2 cm of that height).
        _P = a['POSITION'].astype(np.float64)
        _lo = _P[:, 1].min(); _n = int(np.ceil((_P[:, 1].max() - _lo) / 0.01)) + 1
        _r = np.round((_P[:, 1] - _lo) / 0.01).astype(int)
        _zmin = np.full(_n, np.inf); _zmax = np.full(_n, -np.inf)
        for _d in range(-2, 3):
            _k = np.clip(_r + _d, 0, _n - 1); _ok = (_r + _d >= 0) & (_r + _d < _n)
            np.minimum.at(_zmin, _k[_ok], _P[_ok, 2]); np.maximum.at(_zmax, _k[_ok], _P[_ok, 2])
        ZM_Y = _lo + np.arange(_n) * 0.01
        ZM = np.where(_zmax >= _zmin, (_zmin + _zmax) / 2, 0.0)
        U4 = a['_UNR']
        sf, sb, h, sg = U4[:, 0], U4[:, 1], U4[:, 2], U4[:, 3]
        sg = np.where(sg == 0, np.sign(a['POSITION'][:, 0]), sg)
        back, px_, py = photo_from(sf, sb, h, sg, a['POSITION'].astype(np.float64))
        # The guernsey now has the photo's own outline: one scale everywhere.
        Pw = a['POSITION'].astype(np.float64)
        rw = np.clip(py, 0, 1999).astype(int)
        pxf = cx_row['front'][rw] + Pw[:, 0] * S_PX
        pxb = cx_row['back'][rw] - Pw[:, 0] * S_PX
        a['TEXCOORD_0'][:, 0] = np.where(back, 1.0 - pxb / 2000.0, pxf / 2000.0)
        a['TEXCOORD_0'][:, 1] = py / 2000.0
        a['TEXCOORD_1'][:, 1] = back.astype(np.float32)
        print('guernsey uv range', a['TEXCOORD_0'].min(0), a['TEXCOORD_0'].max(0), 'back verts', back.sum())
    if pid == SK:
        _sp = a['POSITION'].astype(np.float64); _sel = (np.abs(_sp[:, 0]) < 0.16) & (_sp[:, 1] > 0.9) & (_sp[:, 1] < 1.3)
        SKIN_T = (_sp[_sel], a['NORMAL'][_sel].astype(np.float64))
        # The skin's guernsey and shorts regions (COLOR_0 r, g) above the hem are cleared: the
        # guernsey is its own surface now, and skin the old staircase marked as guernsey was
        # painted in the shorts' colour.
        up = a['POSITION'][:, 1] > 1.15
        a['COLOR_0'][up, 0] = 0
        a['COLOR_0'][up, 1] = 0
    for k in list(p['attributes']):
        old = orig_acc[p['attributes'][k]]
        v = a[k] if old['componentType'] == 5126 else np.rint(a[k])
        p['attributes'][k] = new_acc(v.astype(COMP[old['componentType']]), old, minmax=(k == 'POSITION'))
    for ti, tt in enumerate(t):
        for k in list(p['targets'][ti]):
            p['targets'][ti][k] = new_acc(tt[k].astype(np.float32), None, None, minmax=(k == 'POSITION'), sparse_ok=True)
    p['indices'] = new_acc(tri.astype(np.uint32).reshape(-1, 1), None, 34963)
    print(mats[pid], 'verts', a['POSITION'].shape[0], 'tris', len(tri))

J['bufferViews'] = views
while len(newB) % 4:
    newB.append(0)
J['buffers'] = [{'byteLength': len(newB)}]
js = json.dumps(J, separators=(',', ':')).encode()
while len(js) % 4:
    js += b' '
total = 12 + 8 + len(js) + 8 + len(newB)
with open(OUTP, "wb") as f:
    f.write(struct.pack('<III', 0x46546C67, 2, total))
    f.write(struct.pack('<II', len(js), 0x4E4F534A))
    f.write(js)
    f.write(struct.pack('<II', len(newB), 0x004E4942))
    f.write(newB)
print("wrote", OUTP, total)
