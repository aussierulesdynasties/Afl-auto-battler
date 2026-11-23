"""Real bare-earth land round every ground, from measured elevation data.

One shared source of land heights for everything built outside a stadium: each ground's own
surrounds in its model, the MCG's Yarra Park ring and the backdrops (tools/grounds/backdrop).
The playing surface and the stands are not touched by this tool.

Frame (the same for every ground): metres, x east and y north of the centre circle, height in
metres above the ground's turf, so turf at the centre circle = 0. A ground model turned to its
true bearing rotates its own points into this frame before it asks for a height.

Source: Mapterhorn terrain tiles (https://mapterhorn.com, code BSD-3, data from each source's
own licence). In Australia its zoom 14 tiles are Geoscience Australia's "DEM of Australia derived
from LiDAR 5 Metre Grid" (CC BY 4.0, bare earth), Tasmania zoom 15 is the LIST 2 m DEM (CC BY 3.0),
New Zealand zoom 16 is LINZ 1 m LiDAR (CC BY 4.0). Where no such tile exists the ground's entry
in grounds.json names its own source (see README: Mars, Traeger, Jiangwan).

    python3 tools/grounds/terrain/terrain.py build <slug>|all     # writes grids/<slug>.npz
    python3 tools/grounds/terrain/terrain.py far <slug>           # ±30 km grid into the cache
    python3 tools/grounds/terrain/terrain.py at <slug> x y ...    # heights at points
    python3 tools/grounds/terrain/terrain.py godot <slug>         # assets/grounds/<slug>/terrain.bin

From Python (any build tool):

    sys.path.insert(0, 'tools/grounds/terrain'); import terrain
    T = terrain.load('norwood')          # the committed near grid, ±1.5 km
    T.height(x_east, y_north)            # numpy arrays or floats; NaN outside the grid
    T.footprint_base(poly)               # lowest land under a building's outline (its floor level)
"""
import json, math, os, sys, time
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
GRIDS = os.path.join(HERE, 'grids')
CACHE = os.environ.get('TERRAIN_CACHE', os.path.expanduser('~/.cache/afl_terrain'))
R_EARTH = 6378137.0
NEAR_HALF = 1500.0
FAR_HALF, FAR_STEP = 30000.0, 60.0


def grounds():
    return json.load(open(os.path.join(HERE, 'grounds.json')))


# ---- Mapterhorn tiles (terrarium encoding, 512 px, webp lossless) -------------------------------

def _tile(z, x, y):
    import requests
    from PIL import Image
    d = os.path.join(CACHE, 'mapterhorn'); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, f'{z}_{x}_{y}.webp')
    if not os.path.exists(p):
        for attempt in range(4):
            try:
                r = requests.get(f'https://tiles.mapterhorn.com/{z}/{x}/{y}.webp', timeout=60)
                break
            except Exception:
                time.sleep(2 ** attempt)
        else:
            raise RuntimeError(f'tile {z}/{x}/{y} unreachable')
        if r.status_code == 404:
            return None
        r.raise_for_status()
        open(p, 'wb').write(r.content)
    a = np.asarray(Image.open(p).convert('RGB')).astype(np.float64)
    return a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768


def sample_mapterhorn(lat, lon, z):
    """Bilinear heights (metres, source datum) at lat/lon arrays from zoom z; NaN where no tile."""
    lat = np.asarray(lat, float); lon = np.asarray(lon, float)
    n = 2 ** z * 512
    X = (lon + 180) / 360 * n - 0.5
    Y = (1 - np.arcsinh(np.tan(np.radians(lat))) / math.pi) / 2 * n - 0.5
    x0 = np.floor(X).astype(np.int64); y0 = np.floor(Y).astype(np.int64)
    fx = X - x0; fy = Y - y0
    tiles = {}

    def get(px, py):
        tx, ty = px // 512, py // 512
        v = np.full(px.shape, np.nan)
        for k in set(zip(tx.ravel().tolist(), ty.ravel().tolist())):
            if k not in tiles:
                tiles[k] = _tile(z, *k)
            t = tiles[k]
            if t is None:
                continue
            m = (tx == k[0]) & (ty == k[1])
            v[m] = t[py[m] % 512, px[m] % 512]
        return v
    a = get(x0, y0); b = get(x0 + 1, y0); c = get(x0, y0 + 1); d = get(x0 + 1, y0 + 1)
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy


def to_latlon(lat0, lon0, x, y):
    """Metres east/north of (lat0, lon0) -> lat/lon (local tangent plane; < 1 cm error at 1.5 km,
    about 0.1 % of distance at 30 km, below the far grid's own step)."""
    lat = lat0 + np.degrees(np.asarray(y, float) / R_EARTH)
    lon = lon0 + np.degrees(np.asarray(x, float) / (R_EARTH * math.cos(math.radians(lat0))))
    return lat, lon


def source_heights(g, x, y, far=False):
    """Heights in the source datum for points in the ground's frame."""
    lat, lon = to_latlon(g['lat'], g['lon'], x, y)
    src = g.get('source', 'mapterhorn')
    if src == 'mapterhorn':
        z = g['far_zoom'] if far else g['zoom']
        return sample_mapterhorn(lat, lon, z)
    if src == 'fabdem':
        return sample_fabdem(lat, lon)
    raise SystemExit(f"source {src!r} has no reader yet (README: grounds without 5 m LiDAR)")


# ---- FABDEM v1-2 (30 m, buildings and forest removed; CC BY-NC-SA 4.0; University of Bristol) ----

FABDEM = 'https://data.bris.ac.uk/datasets/s5hqmjcdj8yo2ibzi9b4ew3sn/'


def _fabdem_tile(la, lo):
    """The 1-degree tile holding (la, lo), read out of its 10-degree zip by HTTP ranges."""
    import io, zipfile, requests
    name = f"{'N' if la >= 0 else 'S'}{abs(math.floor(la)):02d}{'E' if lo >= 0 else 'W'}{abs(math.floor(lo)):03d}_FABDEM_V1-2.tif"
    d = os.path.join(CACHE, 'fabdem'); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, name)
    if os.path.exists(p):
        return p
    a = math.floor(la / 10) * 10; b = math.floor(lo / 10) * 10
    def tag(v, pos, neg, w): return f"{pos if v >= 0 else neg}{abs(v):0{w}d}"
    z = f"{tag(a, 'N', 'S', 2)}{tag(b, 'E', 'W', 3)}-{tag(a + 10, 'N', 'S', 2)}{tag(b + 10, 'E', 'W', 3)}_FABDEM_V1-2.zip"

    class R(io.RawIOBase):
        def __init__(s, u):
            s.u = u; s.p = 0; s.ses = requests.Session()
            s.n = int(s.ses.head(u, timeout=60).headers['Content-Length'])
        def seekable(s): return True
        def readable(s): return True
        def tell(s): return s.p
        def seek(s, o, w=0):
            s.p = o if w == 0 else (s.p + o if w == 1 else s.n + o); return s.p
        def readinto(s, buf):
            if s.p >= s.n: return 0
            e = min(s.n, s.p + len(buf)) - 1
            data = s.ses.get(s.u, headers={'Range': f'bytes={s.p}-{e}'}, timeout=120).content
            buf[:len(data)] = data; s.p += len(data); return len(data)
    zf = zipfile.ZipFile(io.BufferedReader(R(FABDEM + z), 1 << 20))
    member = [m for m in zf.namelist() if m.endswith(name)][0]
    open(p, 'wb').write(zf.read(member))
    return p


def sample_fabdem(lat, lon):
    import rasterio
    out = np.full(np.shape(lat), np.nan)
    keys = np.floor(lat).astype(int) * 1000 + np.floor(lon).astype(int)
    for k in np.unique(keys):
        m = keys == k
        with rasterio.open(_fabdem_tile(float(lat[m].flat[0]), float(lon[m].flat[0]))) as ds:
            A = ds.read(1).astype(np.float64); inv = ~ds.transform
            c, r = inv * (lon[m], lat[m])
            c = np.asarray(c) - 0.5; r = np.asarray(r) - 0.5
            i = np.clip(np.floor(c).astype(int), 0, A.shape[1] - 2); j = np.clip(np.floor(r).astype(int), 0, A.shape[0] - 2)
            fx = np.clip(c - i, 0, 1); fy = np.clip(r - j, 0, 1)
            out[m] = (A[j, i] * (1 - fx) * (1 - fy) + A[j, i + 1] * fx * (1 - fy)
                      + A[j + 1, i] * (1 - fx) * fy + A[j + 1, i + 1] * fx * fy)
    return out


# ---- grids --------------------------------------------------------------------------------------

class Grid:
    """A height grid in a ground's frame. Rows run south -> north, columns west -> east."""

    def __init__(self, h, half, step, meta):
        self.h = h; self.half = half; self.step = step; self.meta = meta

    def height(self, x, y):
        x = np.asarray(x, float); y = np.asarray(y, float)
        n = self.h.shape[0]
        px = (x + self.half) / self.step; py = (y + self.half) / self.step
        i = np.floor(px).astype(np.int64); j = np.floor(py).astype(np.int64)
        ok = (i >= 0) & (j >= 0) & (i < n - 1) & (j < n - 1)
        i = np.clip(i, 0, n - 2); j = np.clip(j, 0, n - 2)
        fx = px - i; fy = py - j; H = self.h
        v = (H[j, i] * (1 - fx) * (1 - fy) + H[j, i + 1] * fx * (1 - fy)
             + H[j + 1, i] * (1 - fx) * fy + H[j + 1, i + 1] * fx * fy)
        return np.where(ok, v, np.nan)

    def footprint_base(self, poly, every=1.0):
        """Lowest land inside a footprint polygon [(x, y), ...] and along its edge: the level a
        building's ground floor sits at, so no wall ever hangs in the air on the low side (the
        high side is dug into the slope, as the real buildings are)."""
        P = np.asarray(poly, float)
        pts = [P]
        for a, b in zip(P, np.roll(P, -1, 0)):
            k = max(1, int(np.hypot(*(b - a)) / every))
            t = np.linspace(0, 1, k, endpoint=False)[:, None]
            pts.append(a + (b - a) * t)
        x0, y0 = P.min(0); x1, y1 = P.max(0)
        gx, gy = np.meshgrid(np.arange(x0, x1 + every, every), np.arange(y0, y1 + every, every))
        inside = _in_poly(gx.ravel(), gy.ravel(), P)
        pts.append(np.c_[gx.ravel()[inside], gy.ravel()[inside]])
        Q = np.vstack(pts)
        return float(np.nanmin(self.height(Q[:, 0], Q[:, 1])))


def _in_poly(x, y, P):
    inside = np.zeros(x.shape, bool)
    for (ax, ay), (bx, by) in zip(P, np.roll(P, -1, 0)):
        c = ((ay > y) != (by > y)) & (x < (bx - ax) * (y - ay) / np.where(by - ay == 0, 1e-12, by - ay) + ax)
        inside ^= c
    return inside


def build(slug, far=False):
    g = grounds()[slug]
    half, step = (FAR_HALF, FAR_STEP) if far else (NEAR_HALF, g.get('step', 5.0))
    r = np.arange(-half, half + step / 2, step)
    X, Y = np.meshgrid(r, r)                       # rows south -> north
    datum = float(source_heights(g, np.array([0.0]), np.array([0.0]))[0])
    H = source_heights(g, X, Y, far=far) - datum
    meta = {'ground': slug, 'lat': g['lat'], 'lon': g['lon'], 'half_m': half, 'step_m': step,
            'rows': 'south to north', 'cols': 'west to east', 'datum': 'turf at the centre circle = 0',
            'datum_source_m': round(datum, 3), 'source': g.get('source', 'mapterhorn'),
            'zoom': g['far_zoom' if far else 'zoom'], 'licence': g.get('licence', ''),
            'missing_cells': int(np.isnan(H).sum()), 'built': time.strftime('%Y-%m-%d')}
    if far:
        os.makedirs(CACHE, exist_ok=True)
        out = os.path.join(CACHE, f'{slug}_far')
        np.save(out + '.npy', H.astype(np.float32))
        json.dump(meta, open(out + '.json', 'w'), indent=1)
        return out + '.npy'
    os.makedirs(GRIDS, exist_ok=True)
    out = os.path.join(GRIDS, f'{slug}.npz')
    # centimetres as int32 compress to half the size of float32 and keep every centimetre
    np.savez_compressed(out, h_cm=np.round(np.nan_to_num(H, nan=-99999) * 100).astype(np.int32),
                        meta=json.dumps(meta))
    return out


def load(slug, far=False):
    if far:
        p = os.path.join(CACHE, f'{slug}_far.npy')
        if not os.path.exists(p):
            build(slug, far=True)
        meta = json.load(open(p[:-4] + '.json'))
        return Grid(np.load(p).astype(np.float64), meta['half_m'], meta['step_m'], meta)
    z = np.load(os.path.join(GRIDS, f'{slug}.npz'))
    meta = json.loads(str(z['meta']))
    h = z['h_cm'].astype(np.float64) / 100.0
    h[z['h_cm'] == -9999900] = np.nan
    return Grid(h, meta['half_m'], meta['step_m'], meta)


def export_npy(slug, out_dir):
    """The near grid as float32 .npy + .json, the format the backdrop's prep.py reads."""
    T = load(slug)
    os.makedirs(out_dir, exist_ok=True)
    np.save(os.path.join(out_dir, f'{slug}_near.npy'), T.h.astype(np.float32))
    json.dump(T.meta, open(os.path.join(out_dir, f'{slug}_near.json'), 'w'), indent=1)


def export_godot(slug, root=None):
    """assets/grounds/<slug>/terrain.bin for the game (GroundTerrain.gd). Header: 8 float32 (fine half,
    step, cells a side; coarse half, step, cells a side; 0, 0), then each grid as int16 centimetres
    above the turf, rows south to north. Fine: the near grid's 5 m cells to ±1 km; coarse: 20 m to
    ±3 km, so a surrounds ring running out to the horizon stays on real land. Only grounds whose
    surrounds the game draws itself (GroundModels.SURROUNDS) need it."""
    T = load(slug)
    g = grounds()[slug]
    FH, FS = 1000.0, 5.0
    CH, CS = 3000.0, 20.0
    r = np.arange(-FH, FH + FS / 2, FS); X, Y = np.meshgrid(r, r)
    fine = T.height(X, Y)
    r = np.arange(-CH, CH + CS / 2, CS); X, Y = np.meshgrid(r, r)
    coarse = source_heights(g, X, Y) - T.meta['datum_source_m']
    root = root or os.path.join(HERE, '..', '..', '..', 'assets', 'grounds', slug)
    os.makedirs(root, exist_ok=True)
    out = os.path.join(root, 'terrain.bin')
    with open(out, 'wb') as f:
        f.write(np.array([FH, FS, fine.shape[0], CH, CS, coarse.shape[0], 0, 0], np.float32).tobytes())
        for G in (fine, coarse):
            G = np.nan_to_num(G, nan=0.0)
            if np.abs(G).max() > 327:
                raise SystemExit(f'{slug}: land beyond the int16 centimetre range')
            f.write(np.round(G * 100).astype('<i2').tobytes())
    return os.path.normpath(out)


if __name__ == '__main__':
    cmd, slug = sys.argv[1], sys.argv[2]
    if cmd == 'build':
        todo = [s for s, g in grounds().items() if g.get('source', 'mapterhorn') != 'pending'] if slug == 'all' else [slug]
        for s in todo:
            t = time.time(); p = build(s); T = load(s)
            print(f'{s}: {p} {T.h.shape} {np.nanmin(T.h):+.1f}..{np.nanmax(T.h):+.1f} m, '
                  f'missing {T.meta["missing_cells"]}, {time.time() - t:.0f} s')
    elif cmd == 'far':
        print(build(slug, far=True))
    elif cmd == 'godot':
        print(export_godot(slug))
    elif cmd == 'npy':
        export_npy(slug, sys.argv[3])
    elif cmd == 'at':
        T = load(slug); v = list(map(float, sys.argv[3:]))
        for x, y in zip(v[0::2], v[1::2]):
            print(f'{x:8.1f} {y:8.1f} {float(T.height(x, y)):+7.2f}')
