# Flat pattern (director, 2026-11-19: "Yes, all clubs"). Run after recut5.py:   python unwrap.py CODE
# The guernsey is unfolded like a sewing pattern so every bit of cloth gets its own pixels (the photos laid on from
# the front and back stretch one pixel up to 3.5 cm where the cloth turns side-on: the shoulder tops, the sides).
# Front half (in front of the body's depth-middle, as the shader splits it) unfolds into the cell's left square,
# back half into the right one. xatlas (MIT licence, a build tool only) does the unfolding.
# Writes unwrap_CODE.json:
#   g: the guernsey's unfolded points: [x, y, z, u0, v0, U, V]  (place, TEXCOORD_0, place in the cell: U 0-2, V 0-1)
#   t: its triangles, three of those points each
#   s: skin points within 3 cm of the guernsey, [x, y, z, u0, v0, U, V] with the nearest guernsey point's U, V
#      (the skin in the cut's steps wears the guernsey, oval3d_player.gdshader on_skin)
import json, struct, sys, numpy as np, xatlas
from scipy.spatial import cKDTree
CODE = sys.argv[1]
raw = open(f'wrap5_{CODE}.glb', 'rb').read(); jl = struct.unpack('<I', raw[12:16])[0]
J = json.loads(raw[20:20 + jl]); B = raw[20 + jl + 8:]
COMP = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}; KN = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
def acc(i):
    a = J['accessors'][i]; v = J['bufferViews'][a['bufferView']]; o = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    return np.frombuffer(B, COMP[a['componentType']], a['count'] * KN[a['type']], o).reshape(a['count'], -1)
prim = {}
for m in J['meshes']:
    for p in m['primitives']:
        nm = J['materials'][p['material']]['name']
        if nm in ('ARD_guernsey', 'ARD_skin'):
            prim[nm] = (acc(p['attributes']['POSITION']).astype(np.float64), acc(p['attributes']['TEXCOORD_0']).astype(np.float64),
                        acc(p['indices']).reshape(-1, 3).astype(np.uint32))
P, uv, T = prim['ARD_guernsey']
# the body's depth-middle (Oval3D._depth_middle / _middle_at)
lo = P[:, 1].min(); n = int(np.ceil((P[:, 1].max() - lo) / 0.01)) + 1
zmin = np.full(n, np.inf); zmax = np.full(n, -np.inf); r = np.round((P[:, 1] - lo) / 0.01).astype(int)
for k in range(-2, 3):
    rr = np.clip(r + k, 0, n - 1); ok = (r + k >= 0) & (r + k < n)
    np.minimum.at(zmin, rr[ok], P[ok, 2]); np.maximum.at(zmax, rr[ok], P[ok, 2])
mid = np.where(zmax >= zmin, (zmin + zmax) / 2, 0.0)
f = np.clip((P[:, 1] - lo) / 0.01, 0, n - 1); k = np.minimum(f.astype(int), n - 2)
fore = P[:, 2] - (mid[k] + (mid[k + 1] - mid[k]) * (f - k))
front = fore[T].mean(1) > 0

G, TT = [], []
for half, sel in ((0, front), (1, ~front)):
    tri = T[sel]
    used = np.unique(tri); remap = -np.ones(len(P), int); remap[used] = np.arange(len(used))
    po = P[used].astype(np.float32); ti = remap[tri].astype(np.uint32)
    at = xatlas.Atlas(); at.add_mesh(po, ti)
    po_ = xatlas.PackOptions(); po_.resolution = 1024; po_.padding = 6; po_.bilinear = True; po_.rotate_charts = True
    at.generate(pack_options=po_)
    vm, ix, uw = at[0]
    base = len(G)
    for j, v in enumerate(vm):
        o = used[v]
        G.append([*P[o], *uv[o], half + float(uw[j, 0]), float(uw[j, 1])])
    TT += (ix + base).tolist()
    print(CODE, ('front', 'back')[half], 'triangles', len(tri), 'points', len(vm), 'atlas', at.width, at.height)
G = np.array(G)
SP, Suv, _ = prim['ARD_skin']
d, j = cKDTree(G[:, :3]).query(SP)
near = d < 0.03
S = np.c_[SP[near], Suv[near], G[j[near], 5:7]]
json.dump({'g': G.round(7).tolist(), 't': TT, 's': S.round(7).tolist()}, open(f'unwrap_{CODE}.json', 'w'))
print(CODE, 'unwrap points', len(G), 'skin points', len(S))
