# St Kilda on the flat pattern (run after bake_unwrap.py: python club_fixes/stk_neck_uw.py ATLAS CELL): the white
#   collar is one band of even width along the guernsey's neck edge, over the shoulder from the front's white tabs
#   into the back's collar (same rule as stk_neck.py): every pattern pixel whose spot on the body lies within the
#   band's width of the cut's neck edge is white (front 1.9 cm = the photo's 45 px tab, back 1.2 cm = the collar's
#   middle 28 px; 2310 px a metre). The back's tab stripes keep the photo's colours; only the top of the guernsey.
import json, struct, sys, numpy as np
from PIL import Image
from scipy.spatial import cKDTree
Image.MAX_IMAGE_PIXELS = None
ATLAS, CELL = sys.argv[1], int(sys.argv[2]); GX = 4
raw = open('wrap5_STK.glb', 'rb').read(); jl = struct.unpack('<I', raw[12:16])[0]
J = json.loads(raw[20:20 + jl]); B = raw[20 + jl + 8:]
COMP = {5126: np.float32, 5123: np.uint16, 5125: np.uint32, 5121: np.uint8}; KN = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
def acc(i):
    a = J['accessors'][i]; v = J['bufferViews'][a['bufferView']]; o = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    return np.frombuffer(B, COMP[a['componentType']], a['count'] * KN[a['type']], o).reshape(a['count'], -1)
W = (0xE6, 0xE8, 0xEE)
for m in J['meshes']:
    for p in m['primitives']:
        if J['materials'][p['material']]['name'] == 'ARD_guernsey':
            P = acc(p['attributes']['POSITION']).astype(float); T = acc(p['indices']).reshape(-1, 3)
key = np.unique(np.round(P * 1e5).astype(np.int64), axis=0, return_inverse=True)[1].ravel()
E = {}
for t in T:
    for u, v in ((t[0], t[1]), (t[1], t[2]), (t[2], t[0])):
        E.setdefault((min(key[u], key[v]), max(key[u], key[v])), []).append((u, v))
neck = [l[0] for l in E.values() if len(l) == 1 and P[l[0][0], 1] > 1.48 and abs(P[l[0][0], 0]) < 0.14]
NP = np.concatenate([P[u] + (P[v] - P[u]) * np.linspace(0, 1, 20)[:, None] for u, v in neck])
tree = cKDTree(NP)
tx = np.load('texels_STK.npz'); ys, xs, p3, isf, u0 = tx['ys'], tx['xs'], tx['p'], tx['front'], tx['u0']
d, ni = tree.query(p3)
# (director 2026-11-20, "Taper over shoulder"): over the shoulder top the band narrows smoothly from the front's
# width to the back's, by the depth of the nearest neck-edge spot: the neck edge crosses the shoulder from 8 cm in
# front of the body's middle (full front width) to 8 cm behind it (back width); halfway, 1.55 cm
t = np.clip((NP[ni, 2] + 0.08) / 0.16, 0, 1)
width = (28 + (45 - 28) * t) / 2310
dx = np.where(isf, u0[:, 0], 1 - u0[:, 0]) * 2000; dy = u0[:, 1] * 2000
tab = ~isf & (((dx >= 983) & (dx < 997)) | ((dx >= 1007) & (dx < 1021)))
# (director 2026-11-20, "Run down the V"): on the front the band follows the neck edge all the way down to the
# white middle panel (no flat end on the red or the black), so the front is not held to the photo's tab rows
rows = (dy < 340) | isf
hit = (d < width) & rows & (p3[:, 1] >= 1.40) & ~tab
at = np.array(Image.open(ATLAS).convert('RGB')); C = at.shape[1] // (GX * 2); row, col = divmod(CELL, GX)
cell = at[row*C:(row+1)*C, col*2*C:(col*2+2)*C]
# (director 2026-11-20, "Yes, fixed-width band"): the band replaces the photo's collar, so the photo's jagged
# white just past the band takes the colour of the cloth below it: each spot within 3 cm past the band copies the
# nearest spot 3-5 cm past it (a white panel there stays white).
top = rows & (p3[:, 1] >= 1.40) & ~tab
zone = top & (d >= width) & (d < width + 0.03)
ring = top & (d >= width + 0.03) & (d < width + 0.05)
for s in (True, False):
    z = zone & (isf == s); r = ring & (isf == s)
    if z.any() and r.any():
        # straight down the cloth, as the shoulder rule (sideways distance counts 8x): the panels' edges carry on
        # straight up to the band instead of breaking into the nearest-spot pattern's steps
        sc = np.array([8.0, 1.0, 1.0])
        _, j = cKDTree(p3[r] * sc).query(p3[z] * sc); cell[ys[z], xs[z]] = cell[ys[r][j], xs[r][j]]
cell[ys[hit], xs[hit]] = W
# the empty space round the pattern's pieces takes the nearest piece's colour again (bake_unwrap.py filled it
# before the band was painted, so the photo's old collar showed in specks along the neck edge)
from scipy import ndimage
has = np.zeros(cell.shape[:2], bool); has[ys, xs] = True
_, (iy, ix) = ndimage.distance_transform_edt(~has, return_indices=True)
cell[:] = cell[iy, ix]
Image.fromarray(at).save(ATLAS)
print('collar pattern pixels painted white', int(hit.sum()), '(front', int((hit & isf).sum()), ')')
