# Copies the two photos onto the flat pattern (unwrap.py), once (director, 2026-11-19: "Yes, all clubs").
#   python bake_unwrap.py CODE CELL PLANAR_ATLAS OUT_ATLAS
# PLANAR_ATLAS: an atlas where fillcell.py has put CODE's two photos in CELL (the old front/back pictures).
# Each pixel of the pattern is a spot on the guernsey. In front of the body's depth-middle it reads the front photo
# at that spot, behind it the back photo (the line the shader always used). Where the photo does not show the spot
# (past its cut edge), or shows it side-on (the cloth turned more than 70 degrees from the camera: there one photo
# pixel spreads over more than 3x the cloth, the streaks), the spot takes the colour of the nearest spot, measured
# over the body in 3D, that a photo shows face-on.
# Writes the pattern into OUT_ATLAS's CELL (left square front, right square back) and texels_CODE.npz (each pattern
# pixel's place on the body, for club fixes that paint by place).
import json, sys, numpy as np, cv2
from PIL import Image
from scipy.spatial import cKDTree
from scipy import ndimage
Image.MAX_IMAGE_PIXELS = None
CODE, CELL, PLAN, OUT = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
GX = 4
FACE = np.cos(np.radians(70))
d = json.load(open(f'unwrap_{CODE}.json')); G = np.array(d['g']); T = np.array(d['t']).reshape(-1, 3)
P, uv0, UW = G[:, :3], G[:, 3:5], G[:, 5:7]
lo = P[:, 1].min(); n = int(np.ceil((P[:, 1].max() - lo) / 0.01)) + 1
zmin = np.full(n, np.inf); zmax = np.full(n, -np.inf); r = np.round((P[:, 1] - lo) / 0.01).astype(int)
for k in range(-2, 3):
    rr = np.clip(r + k, 0, n - 1); ok = (r + k >= 0) & (r + k < n)
    np.minimum.at(zmin, rr[ok], P[ok, 2]); np.maximum.at(zmax, rr[ok], P[ok, 2])
mid = np.where(zmax >= zmin, (zmin + zmax) / 2, 0.0)
def fore(p):
    f = np.clip((p[:, 1] - lo) / 0.01, 0, n - 1); k = np.minimum(f.astype(int), n - 2)
    return p[:, 2] - (mid[k] + (mid[k + 1] - mid[k]) * (f - k))
nrm = np.cross(P[T[:, 1]] - P[T[:, 0]], P[T[:, 2]] - P[T[:, 0]]); nrm /= np.linalg.norm(nrm, axis=1)[:, None] + 1e-12
# outward: on the chest (in front, mid height) the normals face forward
cf = (fore(P[T].mean(1)) > 0.05)
if np.median(nrm[cf, 2]) < 0: nrm = -nrm

pa = np.array(Image.open(PLAN).convert('RGB'))
c = pa.shape[1] // (GX * 2); row, col = divmod(CELL, GX)
pic = [pa[row*c:(row+1)*c, (col*2+j)*c:(col*2+j+1)*c].astype(np.float32) for j in (0, 1)]
seen = []
for side in ('front', 'back'):
    a = (np.array(Image.open(f'design_{CODE}_{side}.png').convert('RGBA'))[..., 3] > 250).astype(np.uint8)
    a = cv2.erode(a, np.ones((11, 11), np.uint8)).astype(np.float32)
    seen.append(cv2.resize(a, (c, c), interpolation=cv2.INTER_AREA) > 0.99)

ys, xs, pos, nz = [], [], [], []
for ti, t in enumerate(T):
    q = UW[t] * c
    x0, y0 = np.maximum(np.floor(q.min(0)).astype(int) - 1, 0); x1 = min(int(np.ceil(q[:, 0].max())) + 1, 2 * c - 1); y1 = min(int(np.ceil(q[:, 1].max())) + 1, c - 1)
    M = np.c_[q[1] - q[0], q[2] - q[0]]
    if abs(np.linalg.det(M)) < 1e-12: continue
    gy, gx = np.mgrid[y0:y1 + 1, x0:x1 + 1]; g = np.c_[gx.ravel() + 0.5, gy.ravel() + 0.5]
    l = np.linalg.solve(M, (g - q[0]).T).T
    w = np.c_[1 - l.sum(1), l]; ins = (w >= -1e-4).all(1)
    if not ins.any(): continue
    w = np.clip(w[ins], 0, 1); w /= w.sum(1)[:, None]
    ys.append(g[ins, 1].astype(int)); xs.append(g[ins, 0].astype(int))
    pos.append(np.c_[w @ P[t], w @ uv0[t]]); nz.append(np.full(ins.sum(), nrm[ti, 2]))
ys = np.concatenate(ys); xs = np.concatenate(xs); pos = np.concatenate(pos); nz = np.concatenate(nz)
p3, u0 = pos[:, :3], pos[:, 3:5]
isf = fore(p3) > 0
px = np.where(isf, u0[:, 0], 1 - u0[:, 0]) * c - 0.5; py = u0[:, 1] * c - 0.5
col_ = np.zeros((len(ys), 3), np.float32); ok = np.zeros(len(ys), bool)
for j in (0, 1):
    m = isf if j == 0 else ~isf
    col_[m] = np.stack([ndimage.map_coordinates(pic[j][..., ch], [py[m], px[m]], order=1, mode='nearest') for ch in range(3)], 1)
    sx = np.clip(np.round(px[m]).astype(int), 0, c - 1); sy = np.clip(np.round(py[m]).astype(int), 0, c - 1)
    ok[m] = seen[j][sy, sx] & ((nz[m] > FACE) if j == 0 else (nz[m] < -FACE))
_, ix = cKDTree(p3[ok]).query(p3[~ok])
col_[~ok] = col_[ok][ix]
# shoulder tops (director 2026-11-20, "stripes run over"): each front stripe or panel carries straight on over the
# shoulder along the cloth until the seam line (the depth-middle), and the back's likewise: a spot there takes its
# own side's photographed colour from the cloth straight below it (sideways distance counts 8x).
SH = 1.45  # director 2026-11-20 "Yes, start at 1.45 m" (1.35 was armpit height: wedge under the arm)
for side in (True, False):
    src = ok & (isf == side); dst = ~ok & (isf == side) & (p3[:, 1] > SH)
    if src.any() and dst.any():
        sc = np.array([8.0, 1.0, 1.0])
        _, j2 = cKDTree(p3[src] * sc).query(p3[dst] * sc)
        col_[dst] = col_[src][j2]
print(CODE, 'pattern pixels', len(ys), 'read from a photo face-on', int(ok.sum()), 'from the nearest face-on cloth', int((~ok).sum()))
cell = np.zeros((c, 2 * c, 3), np.float32); has = np.zeros((c, 2 * c), bool)
cell[ys, xs] = col_; has[ys, xs] = True
# the empty space between the pattern's pieces takes the nearest piece's colour (so blurred, far-off views
# of the atlas don't mix in black at the pieces' edges)
_, (iy, ix2) = ndimage.distance_transform_edt(~has, return_indices=True)
cell = cell[iy, ix2]
at = np.array(Image.open(OUT).convert('RGB'))
at[row*c:(row+1)*c, col*2*c:(col*2+2)*c] = np.clip(cell, 0, 255).astype(np.uint8)
Image.fromarray(at).save(OUT)
np.savez_compressed(f"texels_{CODE}.npz", ys=ys, xs=xs, p=p3, front=isf, u0=u0)
