"""Mars Stadium's surroundings as a second GLB (assets/grounds/mars/mars_part2.glb), run with pip bpy:

    python tools/grounds/mars/surrounds/build_bpy.py OUT_DIR DEM_TILES_DIR

- every building of buildings.json (data.py, OSM footprints) on its real footprint: houses with hipped roofs at
  22 degrees, sheds and works buildings with low gables, shops and schools flat behind a parapet. A footprint
  that is not a rectangle is roofed as the union of its largest inner rectangles, so an L-shaped house gets
  the valley an L-shaped hip roof has. Roof colour: data.py's pick from real roofing colours.
- the Ballarat North workshops' brick chimney (located from Google Earth 3D, Dec 2025)
- the land past the painted map (1.9 km out to 26 km) from open terrain tiles (AWS Terrain Tiles, terrarium),
  heights above the ground's own level with the earth's curve, so Mt Warrenheip, Mt Buninyong and the
  ranges stand on the horizon where they are
Model frame: x east, y north, origin the OSM pitch centroid; Blender +Y becomes glTF -Z.
"""
import bpy, bmesh, json, math, os, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'work'))
from geo import xy2ll, LAT0, LON0

OUT = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else sys.argv[1]
DEM = sys.argv[sys.argv.index('--') + 2] if '--' in sys.argv else sys.argv[2]
B = json.load(open(os.path.join(HERE, 'buildings.json')))

# ---- palette: one texture, every face takes one flat cell ----
ROOFS = [(150, 74, 54), (118, 62, 50), (170, 172, 170), (138, 140, 136), (96, 100, 100), (60, 62, 64),
         (214, 212, 200), (112, 80, 64), (86, 98, 80), (66, 80, 98)]
WALLS = [(232, 230, 222), (222, 212, 186), (150, 76, 56), (208, 190, 150), (186, 186, 182), (196, 210, 214)]
MISC = {'brick': (138, 66, 48), 'brick_dark': (112, 54, 42), 'galv': (176, 178, 178), 'concrete': (170, 168, 162)}
CELLS = ROOFS + WALLS + list(MISC.values())
GRID = 8


def palette():
    a = np.zeros((GRID * 8, GRID * 8, 3), np.uint8)
    for i, c in enumerate(CELLS):
        r, q = divmod(i, GRID); a[r * 8:(r + 1) * 8, q * 8:(q + 1) * 8] = c
    p = os.path.join(HERE, 'palette.png'); Image.fromarray(a).save(p); return p


def cell_uv(i):
    r, q = divmod(i, GRID); return ((q + 0.5) / GRID, 1 - (r + 0.5) / GRID)


ROOF_I = lambda k: k
WALL_I = lambda k: len(ROOFS) + k
MISC_I = {k: len(ROOFS) + len(WALLS) + i for i, k in enumerate(MISC)}


UP = (0, 0, 1.0)


class Acc:
    def __init__(s): s.V = []; s.F = []; s.U = []

    def face(s, pts, cell, want=None):
        if want is not None:   # wind the face so its normal points along 'want'
            P = np.array(pts, float); nrm = np.cross(P[1] - P[0], P[2] - P[0])
            if len(P) > 3: nrm = nrm + np.cross(P[2] - P[0], P[3] - P[0])
            if np.dot(nrm, want) < 0: pts = pts[::-1]
        n = len(s.V); s.V += [tuple(p) for p in pts]; s.F.append(tuple(range(n, n + len(pts)))); s.U.append(cell_uv(cell))

    def build(s, name, mat):
        me = bpy.data.meshes.new(name); me.from_pydata(s.V, [], s.F); me.update()
        uv = me.uv_layers.new(name='UVMap')
        for poly, c in zip(me.polygons, s.U):
            for li in poly.loop_indices: uv.data[li].uv = c
        me.materials.append(mat)
        ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob


def ccw(p):
    s = sum(p[i][0] * p[(i + 1) % len(p)][1] - p[(i + 1) % len(p)][0] * p[i][1] for i in range(len(p)))
    return p if s > 0 else p[::-1]


def obb(p):
    """the footprint's minimum-area rectangle: angle, and points turned into its frame"""
    P = np.array(p); best = None
    for i in range(len(P)):
        e = P[(i + 1) % len(P)] - P[i]; a = math.atan2(e[1], e[0])
        R = np.array([[math.cos(a), math.sin(a)], [-math.sin(a), math.cos(a)]]); Q = P @ R.T
        A = np.ptp(Q[:, 0]) * np.ptp(Q[:, 1])
        if best is None or A < best[0]: best = (A, a, R, Q)
    return best


def inside(P, x, y):
    c = False
    for (x0, y0), (x1, y1) in zip(P, np.roll(P, -1, 0)):
        if (y0 > y) != (y1 > y) and x < x0 + (y - y0) * (x1 - x0) / (y1 - y0): c = not c
    return c


def rects(p):
    """largest rectangles inside the footprint, in its OBB frame: (angle, R, [(x0, y0, x1, y1)...])"""
    A, a, R, Q = obb(p)
    area = abs(sum(Q[i][0] * Q[(i + 1) % len(Q)][1] - Q[(i + 1) % len(Q)][0] * Q[i][1] for i in range(len(Q)))) / 2
    x0, x1, y0, y1 = Q[:, 0].min(), Q[:, 0].max(), Q[:, 1].min(), Q[:, 1].max()
    if area > 0.86 * A or len(p) > 14:
        return a, R, [(x0, y0, x1, y1)]
    snap = lambda v: sorted(set(round(x * 2) / 2 for x in v))
    xs, ys = snap(Q[:, 0]), snap(Q[:, 1])
    if len(xs) > 9 or len(ys) > 9:
        return a, R, [(x0, y0, x1, y1)]
    ins = np.array([[inside(Q, 0.5 * (xs[i] + xs[i + 1]), 0.5 * (ys[j] + ys[j + 1])) for j in range(len(ys) - 1)]
                    for i in range(len(xs) - 1)])
    cand = []
    for i0 in range(len(xs) - 1):
        for i1 in range(i0 + 1, len(xs)):
            for j0 in range(len(ys) - 1):
                for j1 in range(j0 + 1, len(ys)):
                    if ins[i0:i1, j0:j1].all(): cand.append((i0, j0, i1, j1))
    mx = [c for c in cand if not any(d != c and d[0] <= c[0] and d[1] <= c[1] and d[2] >= c[2] and d[3] >= c[3] for d in cand)]
    mx.sort(key=lambda c: -(xs[c[2]] - xs[c[0]]) * (ys[c[3]] - ys[c[1]]))
    out = [(xs[c[0]], ys[c[1]], xs[c[2]], ys[c[3]]) for c in mx[:4] if (xs[c[2]] - xs[c[0]]) > 1.5 and (ys[c[3]] - ys[c[1]]) > 1.5]
    return a, R, out or [(x0, y0, x1, y1)]


def hip(acc, R, r, z0, pitch, o, cell, gable=False):
    """hipped (or gabled) roof over rectangle r = (x0, y0, x1, y1) in the OBB frame, eave z0, overhang o"""
    x0, y0, x1, y1 = r[0] - o, r[1] - o, r[2] + o, r[3] + o
    L, W = x1 - x0, y1 - y0; Rt = R.T
    W2 = lambda x, y, z: (*(Rt @ np.array([x, y])), z)
    if L >= W:
        h = W / 2 * math.tan(math.radians(pitch)); ym = (y0 + y1) / 2; i0, i1 = (x0, x1) if gable else (x0 + W / 2, x1 - W / 2)
        a, b, c, d = W2(x0, y0, z0), W2(x1, y0, z0), W2(x1, y1, z0), W2(x0, y1, z0); r0, r1 = W2(i0, ym, z0 + h), W2(i1, ym, z0 + h)
        acc.face([a, b, r1, r0], cell, UP); acc.face([c, d, r0, r1], cell, UP)
        acc.face([b, c, r1], cell, (*(Rt @ np.array([1.0, 0])), 0.3)); acc.face([d, a, r0], cell, (*(Rt @ np.array([-1.0, 0])), 0.3))
    else:
        h = L / 2 * math.tan(math.radians(pitch)); xm = (x0 + x1) / 2; i0, i1 = (y0, y1) if gable else (y0 + L / 2, y1 - L / 2)
        a, b, c, d = W2(x0, y0, z0), W2(x1, y0, z0), W2(x1, y1, z0), W2(x0, y1, z0); r0, r1 = W2(xm, i0, z0 + h), W2(xm, i1, z0 + h)
        acc.face([b, c, r1, r0], cell, UP); acc.face([d, a, r0, r1], cell, UP)
        acc.face([a, b, r0], cell, (*(Rt @ np.array([0, -1.0])), 0.3)); acc.face([c, d, r1], cell, (*(Rt @ np.array([0, 1.0])), 0.3))
    acc.face([W2(x0, y0, z0), W2(x0, y1, z0), W2(x1, y1, z0), W2(x1, y0, z0)], MISC_I['concrete'], (0, 0, -1.0))   # eave soffit


def walls(acc, p, z0, z1, cell):
    p = ccw([tuple(q) for q in p])
    for i in range(len(p)):
        a, b = p[i], p[(i + 1) % len(p)]
        acc.face([(a[0], a[1], z0), (b[0], b[1], z0), (b[0], b[1], z1), (a[0], a[1], z1)], cell)


def flat(acc, p, z, cell, parapet=0.6):
    p = ccw([tuple(q) for q in p])
    bm = bmesh.new(); vs = [bm.verts.new((x, y, z)) for x, y in p]; f = bm.faces.new(vs)
    bmesh.ops.triangulate(bm, faces=[f])
    for t in bm.faces: acc.face([tuple(v.co) for v in t.verts], cell, UP)
    bm.free()
    walls(acc, p, z, z + parapet, cell if cell >= len(ROOFS) else MISC_I['concrete'])


def buildings(acc):
    for b in B['buildings']:
        p = b['p']; k = b['kind']; e = b['eave']; rc = ROOF_I(b['roof']); wc = WALL_I(b['wall'])
        if k == 'shed': wc = MISC_I['galv']
        walls(acc, p, -0.06, e, wc)
        if k == 'commercial':
            flat(acc, p, e, rc); continue
        a, R, rs = rects(p)
        pitch, o, gable = {'house': (22, 0.45, False), 'shed': (10, 0.15, True), 'industrial': (8, 0.3, True),
                           'church': (35, 0.3, True)}[k]
        for r in rs:
            W = min(r[2] - r[0], r[3] - r[1])
            if k == 'industrial' and W > 24:   # wide sheds: parallel gable bays about 15 m wide (GE: the workshops' roofs)
                nb = max(2, round(W / 15.0)); along_x = (r[2] - r[0]) >= (r[3] - r[1])
                for j in range(nb):
                    if along_x: q = (r[0], r[1] + (r[3] - r[1]) * j / nb, r[2], r[1] + (r[3] - r[1]) * (j + 1) / nb)
                    else: q = (r[0] + (r[2] - r[0]) * j / nb, r[1], r[0] + (r[2] - r[0]) * (j + 1) / nb, r[3])
                    hip(acc, R, q, e, 14, 0.0 if 0 < j < nb - 1 else o, rc, True)
            else:
                hip(acc, R, r, e, pitch, o, rc, gable)


def chimney(acc, x, y, h=30.0, w0=3.0, w1=1.9):
    """square brick chimney, tapering, corbelled cap (GE 3D: beside the red-brick building south-east of the
    workshops sheds; height from the GE oblique, about 30 m)"""
    def ring(z, w): return [(x - w / 2, y - w / 2, z), (x + w / 2, y - w / 2, z), (x + w / 2, y + w / 2, z), (x - w / 2, y + w / 2, z)]
    lev = [(0, w0, 'brick'), (h - 1.6, w1, 'brick'), (h - 1.6, w1 + 0.5, 'brick_dark'), (h - 0.9, w1 + 0.5, 'brick_dark'), (h - 0.9, w1, 'brick'), (h, w1, 'brick')]
    for (za, wa, _), (zb, wb, m) in zip(lev[:-1], lev[1:]):
        A, Bq = ring(za, wa), ring(zb, wb)
        for i in range(4): acc.face([A[i], A[(i + 1) % 4], Bq[(i + 1) % 4], Bq[i]], MISC_I[m])
    T = ring(h, w1); I = ring(h - 0.5, w1 - 0.6)
    for i in range(4): acc.face([T[i], T[(i + 1) % 4], I[(i + 1) % 4], I[i]], MISC_I['brick_dark'], UP)


# ---- far land ----
def elev_fn(d):
    cache = {}
    def tile(z, x, y):
        k = (z, x, y)
        if k not in cache:
            a = np.asarray(Image.open(os.path.join(d, f'{z}_{x}_{y}.png')).convert('RGB'), float)
            cache[k] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
        return cache[k]
    def e(lat, lon, z=12):
        n = 2 ** z; fx = (lon + 180) / 360 * n; fy = (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
        tx, ty = int(fx), int(fy); u, v = (fx - tx) * 256 - 0.5, (fy - ty) * 256 - 0.5
        i, j = int(math.floor(v)), int(math.floor(u)); fv, fu = v - i, u - j
        a = tile(z, tx, ty); i0, j0 = min(max(i, 0), 255), min(max(j, 0), 255); i1, j1 = min(i0 + 1, 255), min(j0 + 1, 255)
        return (a[i0, j0] * (1 - fu) * (1 - fv) + a[i0, j1] * fu * (1 - fv) + a[i1, j0] * (1 - fu) * fv + a[i1, j1] * fu * fv)
    return e


def far_land(mat_far, r0=1900.0, r1=26000.0, na=360, nr=56):
    """polar mesh from the map's edge out; height above the ground's level, less the earth's curve; u = height band
    for the far-land gradient (pasture and town low, bush and pine plantations on the mounts)"""
    e = elev_fn(DEM); g0 = e(LAT0, LON0)
    rs = [r0 * (r1 / r0) ** (k / (nr - 1)) for k in range(nr)]
    V, F, U = [], [], []
    for i in range(na):
        a = 2 * math.pi * i / na
        for k, r in enumerate(rs):
            x, y = r * math.sin(a), r * math.cos(a); lat, lon = xy2ll(x, y)
            h = e(lat, lon) - g0; blend = min(1.0, (r - r0) / 1200.0)
            z = -0.06 + blend * h - r * r / (2 * 6371000.0)
            V.append((x, y, z)); U.append((min(0.999, max(0.001, (h + 20) / 340.0)), 0.5 + 0.4 * math.sin(i * 1.7 + k * 0.9) * min(1.0, r / 6000)))
    for i in range(na):
        for k in range(nr - 1):
            a0, a1 = i * nr + k, ((i + 1) % na) * nr + k
            F.append((a0, a1, a1 + 1, a0 + 1))
    me = bpy.data.meshes.new('far_land'); me.from_pydata(V, [], F); me.update()
    uv = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices: uv.data[li].uv = U[me.loops[li].vertex_index]
    me.materials.append(mat_far)
    ob = bpy.data.objects.new('far_land', me); bpy.context.scene.collection.objects.link(ob)
    # where are the two mounts, for the QA log
    for name, (la, lo) in {'Mt Warrenheip': (-37.576, 143.960), 'Mt Buninyong': (-37.654, 143.927)}.items():
        print(name, 'height above the ground %.0f m' % (e(la, lo) - g0))


def far_texture():
    """256 x 64 gradient: u = height band (dry pasture gold-green low, darker green bush higher, pine-dark on the
    mounts), v = a slow field-to-field variation"""
    u = np.linspace(0, 1, 256)[None, :, None]; v = np.linspace(0, 1, 64)[:, None, None]
    low = np.array([150, 146, 98.0]); mid = np.array([108, 118, 74.0]); high = np.array([56, 72, 50.0])
    c = np.where(u < 0.35, low + (mid - low) * (u / 0.35), mid + (high - mid) * np.clip((u - 0.35) / 0.45, 0, 1))
    c = c * (0.9 + 0.2 * v)
    p = os.path.join(HERE, 'far_land.png'); Image.fromarray(np.clip(c, 0, 255).astype(np.uint8)).save(p); return p


def material(name, img, nearest=True):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    t = nt.nodes.new('ShaderNodeTexImage'); t.image = bpy.data.images.load(img); t.interpolation = 'Closest' if nearest else 'Linear'
    nt.links.new(t.outputs['Color'], b.inputs['Base Color']); b.inputs['Roughness'].default_value = 0.9
    return m


def main():
    for ob in list(bpy.data.objects): bpy.data.objects.remove(ob)
    pal = material('surround_palette', palette()); far = material('far_land', far_texture(), nearest=False)
    acc = Acc(); buildings(acc); chimney(acc, 300.0, -318.0)
    acc.build('surround_buildings', pal)
    far_land(far)
    os.makedirs(OUT, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'mars_part2.glb'), export_format='GLB', export_cameras=False, export_lights=False)
    print('buildings', len(B['buildings']), 'faces', len(acc.F))


main()
