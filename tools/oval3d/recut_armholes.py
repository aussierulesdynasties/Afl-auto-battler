"""Re-cut the guernsey's armholes in player_mh.glb along one smooth line each.

The guernsey (ARD_guernsey) and the skin (ARD_skin) are the body's own triangles, split by region
along whole triangles, so each armhole's edge zigzags. For each armhole: the plane of its edge
loop (Newell normal, through the loop's middle). Every skin or guernsey triangle within BAND of
the old edge is split along that plane; the torso side goes to the guernsey, the arm side to the
skin. Plane and body meet in a smooth curve, so the new edge is one clean line. Every vertex
attribute (skin coords, guernsey coords, weights) and the body morphs are interpolated along the
split edges, so nothing else changes.

python tools/oval3d/recut_armholes.py IN.glb OUT.glb  (run once on player_mh.glb, director 2026-11-18:
"Start from scratch": the armhole cut in the model, not painted over in the shader)
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

planes = []
for L in arms:
    c = L.mean(0)
    n = np.zeros(3)
    for i in range(len(L)):
        a, b = L[i] - c, L[(i + 1) % len(L)] - c
        n += np.cross(a, b)
    n /= np.linalg.norm(n)
    if np.dot(-c * np.array([1, 0, 0]), n) < 0:  # normal points to the body's middle (torso side +)
        n = -n
    s = (L - c) @ n
    print(f"armhole at x={c[0]:+.3f}: {len(L)} edge points, off the plane {s.min()*100:+.2f}..{s.max()*100:+.2f} cm, normal {np.round(n, 3)}")
    planes.append((c, n, L))


# The cut line: each armhole's old edge loop smoothed (Taubin, which keeps its size) and sampled
# finely. A point's side is how far it lies into the cloth from the nearest point of that line,
# measured along the surface (square to the line, towards the cloth). A flat plane grazed the chest
# at the front of the armpit, where the surface runs almost parallel to it, and left islands there.
SMOOTH_ITERS = 20
lines = []
for (c, n, L) in planes:
    m = len(L)
    sm = L.copy()
    for _ in range(SMOOTH_ITERS):
        for f in (0.5, -0.53):
            sm = sm + f * (0.5 * (np.roll(sm, 1, 0) + np.roll(sm, -1, 0)) - sm)
    k = 10
    fine = np.concatenate([sm[i] + (sm[(i + 1) % m] - sm[i]) * (np.arange(k)[:, None] / k) for i in range(m)])
    along = np.roll(fine, -1, 0) - np.roll(fine, 1, 0)
    along /= np.linalg.norm(along, axis=1, keepdims=True)
    into = np.zeros_like(fine)
    nrm = np.zeros_like(fine)
    for i, q in enumerate(fine):
        d2 = ((gp - q) ** 2).sum(1)
        nn = gn[d2 < 0.02 ** 2].sum(0)
        nrm[i] = nn / np.linalg.norm(nn)
        v = gp[d2 < 0.04 ** 2].mean(0) - q
        v -= along[i] * (v @ along[i]) + nrm[i] * (v @ nrm[i])
        into[i] = v / np.linalg.norm(v)
    lines.append((fine, into, nrm))


def side_dist(k, X):
    """Metres into the cloth from armhole k's smoothed edge line (negative: the arm's side)."""
    from scipy.spatial import cKDTree
    fine, into, nrm = lines[k]
    _, i = cKDTree(fine).query(X)
    d = X - fine[i]
    # Less the distance off the cloth's surface there: under the armpit the arm's underside lies
    # below the line's lowest point (so 'into the cloth' by that measure alone) but stands off the
    # side of the chest, and stays the arm's.
    return (d * into[i]).sum(-1) - np.abs((d * nrm[i]).sum(-1))


def near_edge(P):
    """Distance from each point to the nearer armhole's old edge points."""
    from scipy.spatial import cKDTree
    d = np.full(len(P), np.inf)
    which = np.zeros(len(P), np.int64)
    for k, (c, n, L) in enumerate(planes):
        dk, _ = cKDTree(L).query(P)
        better = dk < d
        d[better] = dk[better]
        which[better] = k
    return d, which


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
            sa, sb = side_dist(cur_plane, P[[a, b]])
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
        s = side_dist(cur_plane, P[ids])
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
            a['TEXCOORD_0'][n0:, 0] = 0.5 + 2.0 * Pn[:, 0]
            a['TEXCOORD_0'][n0:, 1] = 3.049 - 1.8998 * Pn[:, 1]
    if pid == SK:
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
