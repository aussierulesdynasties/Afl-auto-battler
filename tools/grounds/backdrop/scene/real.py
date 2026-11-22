"""Real-place data for a ground's scene (2026-11-22, after the director rejected generic suburbs):
- heights from Overture Maps buildings (OSM footprints with measured/estimated heights) where OSM has none;
- the ground's colours from the aerial, as a colour field (12 m cells, trees, roofs and shadow left out),
  laid only on soft cover (grass, yards, open land): no photo pixels, no painted detail;
- the tree canopy traced from the aerial (where crowns are), so trees stand where the real ones do."""
import json, os, math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

def overture_heights(g, xy):
    p = os.path.join(os.environ.get('WORK', '/home/user/work'), 'overture', g + '.json')
    if not os.path.exists(p): return None
    from shapely import wkt as W
    from shapely.strtree import STRtree
    from shapely.ops import transform
    polys, hs = [], []
    for r in json.load(open(p)):
        h = r['height']
        if h is None and r['num_floors']: h = r['num_floors'] * 3.4 + 1.0
        if h is None: continue
        try: g_ = W.loads(r['wkt'])
        except Exception: continue
        polys.append(transform(lambda x, y, z=None: xy(y, x), g_)); hs.append(float(h))
    tree = STRtree(polys)
    from shapely.geometry import Point, Polygon
    def look(cx, cy, pts=None):
        """the tallest Overture building at the outline's middle, or (with the outline) the tallest one
        lying mostly inside it: one OSM outline often holds a whole block of flats"""
        pt = Point(cx, cy); best = None
        for i in tree.query(pt):
            if polys[i].contains(pt): best = hs[i] if best is None else max(best, hs[i])
        if pts is not None and len(pts) >= 3:
            try: q = Polygon(pts).buffer(0)
            except Exception: q = None
            if q is not None and q.area > 0:
                for i in tree.query(q):
                    a_ = polys[i].area
                    if a_ > 8 and polys[i].intersection(q).area > 0.5 * a_: best = hs[i] if best is None else max(best, hs[i])
        return best
    print('overture heights', len(polys))
    return look

def sat(D):
    sp = os.path.join(D, 'sat.png')
    if not os.path.exists(sp): return None
    sj = json.load(open(os.path.join(D, 'sat.json')))
    return np.asarray(Image.open(sp).convert('RGB')).astype(np.float32), sj['half_m'], sj['m_per_px']

def canopy(SA):
    """crowns: dark, green and textured (lawns are lighter and smooth); open water (dark and smooth) left out"""
    R, G, B = SA[..., 0], SA[..., 1], SA[..., 2]
    V = SA.max(-1); exg = 2 * G - R - B
    from scipy.ndimage import uniform_filter, binary_opening, binary_closing
    mu = uniform_filter(V, 7); sd = np.sqrt(np.maximum(0, uniform_filter(V * V, 7) - mu * mu))
    water = (uniform_filter(V, 15) < 55) & (uniform_filter(sd, 15) < 10)
    t = (exg > 8) & (V < 110) & (V > 14) & (sd > 8) & ~water   # checked on Queens Gardens' belts and shrubberies
    return binary_closing(binary_opening(t, iterations=2), iterations=1)

def shade(SA):
    R, G, B = SA[..., 0], SA[..., 1], SA[..., 2]; V = SA.max(-1)
    exg = 2 * G.astype(np.int32) - R - B
    # deep or bluish shadow; a dark lawn (Perth's irrigated grass sits near V 85) is green, not shade
    return (V < 55) | ((V < 95) & (exg < 12)) | ((B >= G - 2) & (V < 130) & (B > R))

def colour_field(SA, half, mpp, bld_polys, tree_mask, cell=12.0):
    """median-ish colour per cell of the aerial's open ground (no trees, roofs, deep shadow), filled and smoothed"""
    H, W_ = SA.shape[:2]
    mk = Image.new('L', (W_, H), 0); d = ImageDraw.Draw(mk)
    for p in bld_polys: d.polygon([((x + half) / mpp, (half - y) / mpp) for x, y in p], fill=255)
    bad = (np.asarray(mk.filter(ImageFilter.MaxFilter(5))) > 0) | tree_mask | shade(SA)
    c = max(1, int(round(cell / mpp))); h2, w2 = H // c, W_ // c
    A = SA[:h2 * c, :w2 * c].reshape(h2, c, w2, c, 3); ok = (~bad[:h2 * c, :w2 * c]).reshape(h2, c, w2, c, 1)
    n = ok.sum((1, 3)); s = (A * ok).sum((1, 3))
    from scipy.ndimage import gaussian_filter
    # normalised convolution fills cells without open ground from their neighbours
    w = gaussian_filter((n[..., 0] > c * c * 0.2).astype(np.float32), 1.2) + 1e-6
    col = np.stack([gaussian_filter(np.where(n[..., 0] > c * c * 0.2, s[..., k] / np.maximum(n[..., 0], 1), 0), 1.2) for k in range(3)], -1) / w[..., None]
    col = col * np.minimum(1.0, 175.0 / np.maximum(col.max(-1, keepdims=True), 1))   # bright pavement capped like the roofs
    return col   # (h2, w2, 3), north up, cell metres = c * mpp, covering [-half, half)
