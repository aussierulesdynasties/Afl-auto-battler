"""The land round Barossa Park out to 1 km: Lyndoch's streets and houses, the vineyards, Lyndoch Creek, the paddocks,
and every tree the satellite shows.

    python3 tools/grounds/barossa/land.py

Sources (all measured, nothing generic):
- OpenStreetMap (c) OpenStreetMap contributors, ODbL: land use (vineyards, paddocks, the town), roads, water, the
  creek and every building footprint. Fetched from the OSM API into work/osm.osm.
- Terrarium heights (open data): the land's shape.
- The Google satellite mosaic (work/z18.png, 0.5 m a pixel), used only to MEASURE: where each tree stands and how
  wide its crown is, which way each vineyard's rows run and how far apart, how full the vines are, and each roof's
  colour. No satellite pixel is drawn: the ground is painted in code by class.

Writes assets/grounds/barossa/barossa_land.glb (terrain, vines, houses; no shadows) and
assets/grounds/barossa/trees.bin (x, y, z, height, crown radius, shade per tree, float32, model metres), which
GroundModels.SURROUNDS["barossa"] draws.
"""
import math
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import oval2  # noqa: E402
import paint  # noqa: E402
from dem import Dem  # noqa: E402
from geom import Mesh, write_glb, _n  # noqa: E402
from plan import LAT0, LON0, FIELD_ASL, fence_r  # noqa: E402

OUT = os.path.join(HERE, "..", "..", "..", "assets", "grounds", "barossa")
WORK = os.path.join(HERE, "work")
R = 1024.0                 # the land's half width
HOLE = 179.0               # the precinct (build.py) covers +-180 m
TEX = 4096                 # 0.5 m a pixel
MPP = 2 * R / TEX
STEP = 8.0                 # terrain grid
SAT_RES, SAT_HALF = 0.5, 1600.0
BBOX = (138.8655, -34.6080, 138.9065, -34.5890)


def en(lat, lon):
    return ((lon - LON0) * math.cos(math.radians(LAT0)) * 111320.0, (lat - LAT0) * 110900.0)


# ------------------------------------------------------------------ OSM

def load_osm():
    path = os.path.join(WORK, "osm.osm")
    if not os.path.exists(path):
        os.makedirs(WORK, exist_ok=True)
        u = "https://api.openstreetmap.org/api/0.6/map?bbox=%.4f,%.4f,%.4f,%.4f" % BBOX
        urllib.request.urlretrieve(u, path)
    r = ET.parse(path).getroot()
    nodes = {n.get("id"): en(float(n.get("lat")), float(n.get("lon"))) for n in r.iter("node")}
    ways = {}
    for w in r.iter("way"):
        t = {x.get("k"): x.get("v") for x in w.iter("tag")}
        pts = [nodes[nd.get("ref")] for nd in w.iter("nd") if nd.get("ref") in nodes]
        ways[w.get("id")] = (t, pts)
    rels = []
    for rel in r.iter("relation"):
        t = {x.get("k"): x.get("v") for x in rel.iter("tag")}
        outer = [ways[m.get("ref")][1] for m in rel.iter("member") if m.get("type") == "way" and m.get("role") == "outer"
                 and m.get("ref") in ways]
        rels.append((t, outer))
    return list(ways.values()), rels


# ------------------------------------------------------------------ satellite measures

class Sat:
    def __init__(self):
        import cv2
        self.cv2 = cv2
        self.a = cv2.imread(os.path.join(WORK, "z18.png"))
        if self.a is None:
            raise SystemExit("work/z18.png missing: python3 tools/grounds/barossa/satmosaic.py 18 1600 0.5 work/z18.png")
        self.hsv = cv2.cvtColor(self.a, cv2.COLOR_BGR2HSV).astype(np.float32)

    def px(self, e, n):
        return (e + SAT_HALF) / SAT_RES, (SAT_HALF - n) / SAT_RES

    def canopy(self):
        """tree crown mask: dark, olive-green, textured"""
        cv2 = self.cv2
        H, S, V = self.hsv[..., 0], self.hsv[..., 1], self.hsv[..., 2]
        gray = cv2.cvtColor(self.a, cv2.COLOR_BGR2GRAY).astype(np.float32)
        mu = cv2.blur(gray, (5, 5))
        sd = np.sqrt(np.maximum(cv2.blur(gray * gray, (5, 5)) - mu * mu, 0))
        m = ((V < 108) & (H >= 14) & (H <= 72) & (S > 42) & (sd > 9.0)).astype(np.uint8)
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        m = cv2.morphologyEx(m, cv2.MORPH_OPEN, k)
        m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, k)
        n, lab, st, _ = cv2.connectedComponentsWithStats(m)
        small = st[:, cv2.CC_STAT_AREA] < 14
        m[small[lab]] = 0
        return m

    def mean_colour(self, poly):
        cv2 = self.cv2
        pts = np.array([self.px(e, n) for e, n in poly], np.int32)
        mask = np.zeros(self.a.shape[:2], np.uint8)
        cv2.fillPoly(mask, [pts], 1)
        mask = cv2.erode(mask, np.ones((3, 3), np.uint8))
        if mask.sum() < 4:
            return None
        return np.median(self.a[mask > 0], 0)[::-1]

    def rows(self, poly):
        """dominant row direction (unit plan vector along the rows), row spacing and canopy cover in a vineyard"""
        cv2 = self.cv2
        pts = np.array([self.px(e, n) for e, n in poly], np.int32)
        x0, y0 = np.maximum(pts.min(0), 0)
        x1, y1 = np.minimum(pts.max(0), (self.a.shape[1] - 1, self.a.shape[0] - 1))
        if x1 - x0 < 8 or y1 - y0 < 8:
            return None
        sub = cv2.cvtColor(self.a[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY).astype(np.float32)
        mask = np.zeros(sub.shape, np.uint8)
        cv2.fillPoly(mask, [pts - (x0, y0)], 1)
        mask = cv2.erode(mask, np.ones((7, 7), np.uint8))
        if mask.sum() < 200:
            return None
        gx = cv2.Sobel(sub, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(sub, cv2.CV_32F, 0, 1, ksize=3)
        w = mask > 0
        jxx, jyy, jxy = (gx * gx)[w].sum(), (gy * gy)[w].sum(), (gx * gy)[w].sum()
        ang = 0.5 * math.atan2(2 * jxy, jxx - jyy)          # gradient direction in image axes
        coh = math.sqrt((jxx - jyy) ** 2 + 4 * jxy ** 2) / (jxx + jyy + 1e-6)
        g = np.array((math.cos(ang), -math.sin(ang)))       # to plan (y up)
        along = np.array((-g[1], g[0]))
        # spacing: profile across the rows
        ys, xs = np.nonzero(w)
        proj = (xs * math.cos(ang) + ys * math.sin(ang)) * SAT_RES
        vals = sub[ys, xs]
        if len(proj) < 100:
            return None
        bins = np.arange(proj.min(), proj.max(), 0.25)
        if len(bins) < 64:
            return None
        prof, _ = np.histogram(proj, bins, weights=vals)
        cnt, _ = np.histogram(proj, bins)
        prof = np.where(cnt > 0, prof / np.maximum(cnt, 1), np.nan)
        prof = np.nan_to_num(prof - np.nanmean(prof))
        f = np.abs(np.fft.rfft(prof * np.hanning(len(prof))))
        fr = np.fft.rfftfreq(len(prof), 0.25)
        sel = (fr > 1 / 3.8) & (fr < 1 / 2.0)
        spacing = 1 / fr[sel][np.argmax(f[sel])] if sel.any() else 2.75
        # canopy cover: share of darker-than-soil pixels
        V = self.hsv[y0:y1, x0:x1, 2]
        soil = np.percentile(V[w], 80)
        cover = float(((V < soil - 25) & w).sum() / w.sum())
        return along, float(spacing), cover, coh


# ------------------------------------------------------------------ painting the land

# Dry ground matched to Google Earth on the PC render (2026-11-23, straight-down view, median of open paddock and
# town patches): GE's paddocks are about (152, 127, 103) and its town (107, 97, 80) with roofs and trees; the first
# palette rendered 20-30% brighter and yellower.
C = {
    "paddock": (155, 133, 110), "stubble": (152, 126, 101), "meadow": (138, 126, 100), "vine_soil": (140, 118, 94),
    "vine_grass": (128, 122, 86), "town": (130, 120, 98), "lawn": (112, 128, 70), "road": (88, 88, 90),
    "track": (160, 140, 112), "water": (70, 84, 78), "creek": (112, 98, 78), "wood": (108, 96, 74),
    "orchard": (124, 120, 84), "quarry": (196, 182, 158), "rail": (118, 104, 90), "yard": (128, 118, 98),
}
ROAD_W = {"primary": 10.0, "secondary": 9.0, "tertiary": 8.0, "residential": 7.0, "unclassified": 6.5,
          "service": 4.0, "track": 3.5, "living_street": 5.0, "cycleway": 2.5, "footway": 2.0, "path": 1.8}


def paint_ground(ways, rels, sat_cls, half=R, px=TEX):
    """the land's colours (no grain) on a px x px grid covering +-half m round the fence centre; the precinct
    (precinct.py) paints its open ground from the same function so the two meet without a seam"""
    W = px
    mpp = 2 * half / px
    base = np.ones((W, W, 3), np.float32) * np.array(C["paddock"], np.float32)
    im = Image.fromarray(base.astype(np.uint8))
    d = ImageDraw.Draw(im)
    P = lambda p: ((p[0] + half) / mpp, (half - p[1]) / mpp)
    # unmapped land by its coarse class (wooded / irrigated / dry), measured on the satellite
    w, g = sat_cls
    arr = np.array(im).astype(np.float32)
    arr = arr * (1 - w - g)[..., None] + np.array(C["wood"], np.float32) * w[..., None] \
        + np.array(C["lawn"], np.float32) * g[..., None]
    im = Image.fromarray(arr.astype(np.uint8))
    d = ImageDraw.Draw(im)
    order = ["farmland", "meadow", "grass", "orchard", "residential", "recreation_ground", "vineyard", "quarry",
             "cemetery", "industrial"]
    # mapped grass, parks and the cemetery are watered only in places: they take a dry colour here, and the lawns the
    # satellite measures show through below (as in town)
    col = {"farmland": C["stubble"], "meadow": C["meadow"], "grass": C["meadow"], "orchard": C["orchard"],
           "residential": C["town"], "recreation_ground": C["meadow"], "vineyard": C["vine_soil"], "quarry": C["quarry"],
           "cemetery": C["yard"], "industrial": C["yard"]}
    see_through = ("residential", "grass", "recreation_ground", "cemetery")
    polys = []
    for t, pts in ways:
        lu = t.get("landuse") or t.get("leisure")
        if lu in col and len(pts) > 2 and not (lu == "vineyard" and oval2.stale_vineyard(pts)):
            polys.append((order.index(lu) if lu in order else 0, col[lu], pts, lu))
    for t, outer in rels:
        lu = t.get("landuse") or t.get("leisure")
        if lu in col:
            for pts in outer:
                polys.append((order.index(lu) if lu in order else 0, col[lu], pts, lu))
    for _, c, pts, _lu in sorted(polys, key=lambda x: x[0]):
        d.polygon([P(p) for p in pts], fill=tuple(int(x) for x in c))
    # in town, the lawns and garden trees measured on the satellite show through the residential colour (the
    # town was a flat dry colour between the houses where Google Earth shows lawns, gardens and trees)
    town = Image.new("L", (W, W), 0)
    dt = ImageDraw.Draw(town)
    for _, c, pts, lu in polys:
        if lu in see_through:
            dt.polygon([P(p) for p in pts], fill=255)
    tm = np.array(town).astype(np.float32)[..., None] / 255.0
    arr = np.array(im).astype(np.float32)
    garden = arr * (1 - w - g)[..., None] + np.array(C["wood"], np.float32) * w[..., None] \
        + np.array(C["lawn"], np.float32) * g[..., None]
    arr = arr * (1 - tm) + garden * tm
    im = Image.fromarray(arr.astype(np.uint8))
    d = ImageDraw.Draw(im)
    for t, pts in ways:
        if t.get("natural") == "water" and len(pts) > 2:
            d.polygon([P(p) for p in pts], fill=C["water"])
    for t, pts in ways:
        if t.get("waterway") in ("stream", "river", "drain", "ditch") and len(pts) > 1:
            w = 5.0 if t.get("waterway") == "river" else 3.0
            d.line([P(p) for p in pts], fill=C["creek"], width=max(1, int(w / mpp)), joint="curve")
    for t, pts in ways:
        hw = t.get("highway")
        if hw in ROAD_W and len(pts) > 1:
            c = C["track"] if hw in ("track", "path") or t.get("surface") in ("unpaved", "gravel", "dirt") else C["road"]
            d.line([P(p) for p in pts], fill=c, width=max(1, int(ROAD_W[hw] / mpp)), joint="curve")
        if (t.get("railway") or t.get("disused:railway")) and len(pts) > 1:
            d.line([P(p) for p in pts], fill=C["rail"], width=int(4.0 / mpp), joint="curve")
    # house yards: a ring of garden round each house in town
    for t, pts in ways:
        if "building" in t and len(pts) > 2:
            d.polygon([P(p) for p in pts], fill=C["yard"])
    a = np.array(im).astype(np.float32)
    # the second oval (oval2.py): its west part lies out here past the precinct
    g = (np.arange(W) + 0.5) * mpp - half
    E, N = np.meshgrid(g, -g)
    oval2.paint(a, E, N, C["lawn"])
    return a


def paint_land(ways, rels, sat_cls):
    W = TEX
    a = paint_ground(ways, rels, sat_cls)
    n1 = paint.fbm(W, W, 301, (16, 48, 128, 512), (0.35, 0.3, 0.2, 0.15))
    n2 = paint.fbm(W, W, 302, (1024, 2048, 2048, 4096), (0.3, 0.3, 0.2, 0.2))
    a *= (0.86 + 0.2 * n1 + 0.1 * (n2 - 0.5))[..., None]
    out = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))
    return np.array(out)


def coarse_classes(sat, canopy, half=R, px=TEX):
    """the share of wooded and of green (watered) ground round each texture pixel, measured on the satellite and
    softened over about 4 m so class edges are smooth curves, not cells -> (wood, green), each TEX x TEX, 0..1"""
    cv2 = sat.cv2
    H, S, V = sat.hsv[..., 0], sat.hsv[..., 1], sat.hsv[..., 2]
    green = ((H > 30) & (H < 75) & (S > 70) & (V > 70)).astype(np.float32)
    wood = (canopy > 0.5).astype(np.float32)
    sig = 4.0 / SAT_RES
    green = cv2.GaussianBlur(green, (0, 0), sig)
    wood = cv2.GaussianBlur(wood, (0, 0), sig)
    mpp = 2 * half / px
    e = (np.arange(px) + 0.5) * mpp - half        # columns run east
    nn = half - (np.arange(px) + 0.5) * mpp       # rows run south from the north edge
    x = ((e + SAT_HALF) / SAT_RES - 0.5).astype(np.float32)
    y = ((SAT_HALF - nn) / SAT_RES - 0.5).astype(np.float32)
    X, Y = np.meshgrid(x, y)
    wood = cv2.remap(wood, X, Y, cv2.INTER_LINEAR)
    green = cv2.remap(green, X, Y, cv2.INTER_LINEAR)
    # a smooth step: mostly one class or the other, with a soft rim
    st = lambda f, lo, hi: np.clip((f - lo) / (hi - lo), 0, 1) ** 2 * (3 - 2 * np.clip((f - lo) / (hi - lo), 0, 1))
    w = st(wood, 0.25, 0.45)
    g = st(green, 0.4, 0.6) * (1 - w)
    return w, g


def ground_window(half, px):
    """paint_ground for a window round the fence centre, loading the map and the satellite itself"""
    ways, rels = load_osm()
    sat = Sat()
    return paint_ground(ways, rels, coarse_classes(sat, sat.canopy(), half, px), half, px)


# ------------------------------------------------------------------ terrain

def terrain(dem, tex):
    m = Mesh()
    g = np.arange(-R, R + 0.01, STEP)
    GE, GN = np.meshgrid(g, g)
    H = dem.at_en(GE, GN) - FIELD_ASL
    n = len(g)
    inside = (np.abs(GE) < HOLE) & (np.abs(GN) < HOLE)
    for i in range(n - 1):
        for j in range(n - 1):
            if inside[i, j] and inside[i, j + 1] and inside[i + 1, j] and inside[i + 1, j + 1]:
                continue
            # cells that straddle the precinct's edge are kept but sink under it
            a = (GE[i, j], H[i, j], -GN[i, j])
            b = (GE[i, j + 1], H[i, j + 1], -GN[i, j + 1])
            c = (GE[i + 1, j + 1], H[i + 1, j + 1], -GN[i + 1, j + 1])
            d = (GE[i + 1, j], H[i + 1, j], -GN[i + 1, j])
            pts = [a, b, c, d]
            pts = [(p[0], p[1] - (0.6 if abs(p[0]) < HOLE + 1 and abs(-p[2]) < HOLE + 1 else 0.0), p[2]) for p in pts]
            uv = [((p[0] + R), (p[2] + R)) for p in pts]
            m.quad("land", pts[0], pts[1], pts[2], pts[3], uv=uv)
    return m, (g, H)


def h_at(th, e, n):
    g, H = th
    fx = (e - g[0]) / (g[1] - g[0])
    fy = (n - g[0]) / (g[1] - g[0])
    j = np.clip(np.floor(fx).astype(int), 0, len(g) - 2)
    i = np.clip(np.floor(fy).astype(int), 0, len(g) - 2)
    ax, ay = fx - j, fy - i
    return H[i, j] * (1 - ax) * (1 - ay) + H[i, j + 1] * ax * (1 - ay) + H[i + 1, j] * (1 - ax) * ay + H[i + 1, j + 1] * ax * ay


# ------------------------------------------------------------------ trees

def trees(sat, canopy, th, keep_out, in_vines):
    """fill every crown the satellite shows with gums: a crown radius from the crown's own size (1.5 to 6 m), packed
    without overlap; height from the crown (river red gums and blue gums: about 2.4 x the crown radius + 4 m)"""
    cv2 = sat.cv2
    x0, y0 = sat.px(-R, R)
    x1, y1 = sat.px(R, -R)
    x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
    m = canopy[y0:y1, x0:x1].copy()
    dist = cv2.distanceTransform(m, cv2.DIST_L2, 5) * SAT_RES
    rng = np.random.default_rng(5)
    ys, xs = np.nonzero(m)
    order = np.argsort(-(dist[ys, xs] + rng.random(len(ys)) * 0.6))
    taken = np.zeros(m.shape, np.uint8)
    out = []
    for k in order:
        y, x = ys[k], xs[k]
        if taken[y, x] or dist[y, x] < 1.0:
            continue
        r = float(np.clip(dist[y, x] + 1.2, 2.4, 7.0))
        e = -R + (x + 0.5) * SAT_RES
        n = R - (y + 0.5) * SAT_RES
        if keep_out(e, n):
            cv2.circle(taken, (int(x), int(y)), int(r / SAT_RES * 0.8), 1, -1)
            continue
        if in_vines(e, n) and dist[y, x] < 2.2:
            continue
        cv2.circle(taken, (int(x), int(y)), max(1, int(r / SAT_RES * 1.05)), 1, -1)
        h = 1.9 * r + 3.0 + rng.normal(0, 1.0)
        y_ = float(h_at(th, e, n))
        out.append((e, y_, -n, h, r, rng.random()))
    return out


# ------------------------------------------------------------------ vineyards

def vines(sat, ways, th, keep_out, mesh, reach=760.0):
    """each vineyard's rows as trellised canopy hedges, at the rows' measured bearing and spacing, following the
    ground; young or thin vineyards (low cover) get a lower, narrower, gappy canopy"""
    from shapely.geometry import Polygon, LineString
    count = 0
    rng = np.random.default_rng(9)
    for t, pts in ways:
        if t.get("landuse") != "vineyard" or len(pts) < 4 or oval2.stale_vineyard(pts):
            continue
        poly = Polygon(pts)
        if not poly.is_valid:
            poly = poly.buffer(0)
        c = poly.centroid
        if abs(c.x) > reach + 200 or abs(c.y) > reach + 200:
            continue
        meas = sat.rows(pts)
        if meas is None:
            along, spacing, cover, coh = np.array((1.0, 0.0)), 2.75, 0.4, 0.0
        else:
            along, spacing, cover, coh = meas
        if coh < 0.08:
            # no clear rows (a newly planted or pulled block): plant at the block's long axis
            mrr = poly.minimum_rotated_rectangle
            q = np.array(mrr.exterior.coords)
            e1, e2 = q[1] - q[0], q[2] - q[1]
            along = _n(e1 if np.linalg.norm(e1) > np.linalg.norm(e2) else e2)
        across = np.array((-along[1], along[0]))
        hgt = 1.0 + 0.8 * np.clip(cover / 0.5, 0.2, 1.0)
        wid = 0.35 + 0.5 * np.clip(cover / 0.5, 0.2, 1.0)
        gappy = cover < 0.18
        inner = poly.buffer(-1.5)
        if inner.is_empty:
            continue
        b = np.array(inner.bounds)
        cx, cy = c.x, c.y
        span = math.hypot(b[2] - b[0], b[3] - b[1])
        k0 = -int(span / spacing)
        for k in range(k0, -k0 + 1):
            o = np.array((cx, cy)) + across * k * spacing
            line = LineString([tuple(o - along * span), tuple(o + along * span)])
            seg = inner.intersection(line)
            for s in getattr(seg, "geoms", [seg]):
                if s.is_empty or s.geom_type != "LineString":
                    continue
                p0, p1 = np.array(s.coords[0]), np.array(s.coords[-1])
                Ls = np.linalg.norm(p1 - p0)
                nseg = max(1, int(Ls / 12.0))
                for i in range(nseg):
                    a = p0 + (p1 - p0) * i / nseg
                    bq = p0 + (p1 - p0) * (i + 1) / nseg
                    if keep_out(*((a + bq) / 2)):
                        continue
                    if gappy:
                        # break the hedge into vines 1.8 m apart with their gaps
                        sub = int(np.linalg.norm(bq - a) / 1.8)
                        for jj in range(sub):
                            q0 = a + (bq - a) * (jj + 0.2) / sub
                            q1 = a + (bq - a) * (jj + 0.75) / sub
                            _hedge(mesh, q0, q1, across, th, hgt * 0.8, wid)
                            count += 1
                    else:
                        _hedge(mesh, a, bq, across, th, hgt, wid)
                        count += 1
    return count


def _hedge(m, a, b, across, th, hgt, wid):
    ha, hb = float(h_at(th, *a)), float(h_at(th, *b))
    lo = 0.55
    w = across * wid / 2
    wt = across * wid * 0.35
    A0, A1 = a - w, a + w
    B0, B1 = b - w, b + w
    T0, T1 = a - wt, a + wt
    U0, U1 = b - wt, b + wt
    P = lambda p, h: (p[0], h, -p[1])
    # two sides (slightly battered), a narrower top, and the open underside left out (the trunks' gap)
    _qq(m, "vine", P(A0, ha + lo), P(B0, hb + lo), P(U0, hb + hgt), P(T0, ha + hgt), -across)
    _qq(m, "vine", P(B1, hb + lo), P(A1, ha + lo), P(T1, ha + hgt), P(U1, hb + hgt), across)
    _qq(m, "vine_top", P(T0, ha + hgt), P(U0, hb + hgt), P(U1, hb + hgt), P(T1, ha + hgt), "up")
    _qq(m, "vine_under", P(A1, ha + lo), P(B1, hb + lo), P(B0, hb + lo), P(A0, ha + lo), "down")


def _qq(m, mat, a, b, c, d, out):
    a, b, c, d = (np.array(x, float) for x in (a, b, c, d))
    nrm = np.cross(b - a, d - a)
    if isinstance(out, str):
        want = np.array((0, 1.0 if out == "up" else -1.0, 0))
    else:
        want = np.array((out[0], 0, -out[1])) if out is not None else None
    if want is not None and np.dot(nrm, want) < 0:
        a, b, c, d = d, c, b, a
    m.quad(mat, a, b, c, d)


# ------------------------------------------------------------------ houses

WALLS = [(222, 214, 196), (206, 192, 168), (184, 150, 120), (232, 228, 218), (168, 120, 96), (210, 204, 190),
         (196, 178, 150)]


def houses(sat, ways, th, keep_out, m):
    from shapely.geometry import Polygon, box
    from shapely import affinity
    rng = np.random.default_rng(3)
    n = 0
    for t, pts in ways:
        if "building" not in t or len(pts) < 4:
            continue
        poly = Polygon(pts)
        if not poly.is_valid:
            poly = poly.buffer(0)
            if poly.geom_type != "Polygon":
                continue
        c = poly.centroid
        if abs(c.x) > R - 10 or abs(c.y) > R - 10 or keep_out(c.x, c.y):
            continue
        area = poly.area
        kind = t.get("building")
        rc = sat.mean_colour(list(poly.exterior.coords))
        roof = _roof_colour(rc)
        wall = WALLS[int(rng.integers(len(WALLS)))]
        ground = float(min(h_at(th, x, y) for x, y in poly.exterior.coords))
        top = float(max(h_at(th, x, y) for x, y in poly.exterior.coords))
        shed = kind in ("shed", "industrial", "warehouse", "farm_auxiliary", "barn") or (area > 350 and kind not in ("house", "residential", "detached"))
        eave = top + (4.5 if shed else 2.9) + (0.6 if kind in ("retail", "commercial", "church") else 0.0)
        if kind == "church":
            eave = top + 5.5
        mrr = poly.minimum_rotated_rectangle
        q = np.array(mrr.exterior.coords)[:4]
        fill = area / max(mrr.area, 1e-6)
        # walls follow the true footprint
        ext = list(poly.exterior.coords)[:-1]
        _walls(m, ext, ground - 0.3, eave, wall)
        # roofs: a hip (houses) or a low gable (sheds) on the footprint's rectangle, or on its two rectangles
        # when the house is an L
        rects = [q]
        if fill < 0.85 and not shed:
            rects = _split_l(poly, q) or [q]
        for rq in rects:
            if shed:
                _gable_roof(m, rq, eave, roof, pitch=10.0)
            else:
                _hip_roof(m, rq, eave, roof, pitch=24.0 if kind != "church" else 45.0)
        n += 1
    return n


# The newest houses in the south-west estate, in neither OpenStreetMap nor Microsoft's footprints: traced on the
# 2026 mosaic (work/z18.png) as (e0, n0, e1, n1), with the aerial's lean for a 4.5 m roof taken off (lean_view.LEAN).
TRACED_HOUSES = [
    (-979.3, -895.9, -960.3, -871.9), (-946.3, -902.9, -925.3, -879.9), (-973.3, -922.9, -951.3, -895.4),
    (-960.3, -941.9, -937.3, -913.9), (-937.3, -934.9, -907.3, -903.9), (-888.3, -906.9, -865.3, -892.9),
    (-885.3, -923.9, -860.3, -906.9), (-883.3, -966.9, -853.3, -937.9), (-855.3, -953.9, -835.3, -929.9),
    (-792.8, -898.9, -775.3, -882.9), (-828.8, -917.9, -821.3, -909.9), (-925.3, -962.9, -902.8, -946.4),
    (-919.3, -981.4, -900.3, -962.9), (-923.3, -995.9, -887.3, -979.9), (-945.3, -1008.9, -925.3, -982.9),
    (-1000.3, -968.9, -965.3, -953.9), (-999.3, -992.9, -976.3, -968.9), (-1022.3, -1015.9, -1000.3, -991.9),
    (-867.3, -1004.9, -841.3, -978.9), (-850.3, -1003.9, -832.3, -976.4), (-835.3, -1002.9, -816.3, -976.4),
    (-974.3, -1026.9, -951.3, -1005.9),
]


def ms_buildings(ways):
    """Microsoft's Global ML Building Footprints (ODbL; 2026-02 release, quadkey 311220301, cut to the land by
    work/msbuildings.geojsonl, see README) for the houses OpenStreetMap lacks: the newer streets west of the ground
    above all. A footprint is added when under a fifth of it overlaps a mapped building. Checked on the 2026 mosaic:
    they sit on the roofs."""
    import json
    from shapely.geometry import Polygon
    from shapely.strtree import STRtree
    path = os.path.join(WORK, "msbuildings.geojsonl")
    if not os.path.exists(path):
        raise SystemExit("work/msbuildings.geojsonl missing (README: Microsoft building footprints)")
    osm = [Polygon(p).buffer(0) for t, p in ways if "building" in t and len(p) >= 4]
    tree = STRtree(osm)
    out = []
    for line in open(path):
        f = json.loads(line)
        pts = [en(la, lo) for lo, la in f["geometry"]["coordinates"][0]]
        poly = Polygon(pts).buffer(0)
        if poly.geom_type != "Polygon" or poly.area < 12:
            continue
        if any(poly.intersection(osm[i]).area > 0.2 * poly.area for i in tree.query(poly)):
            continue
        out.append(({"building": "yes", "source": "microsoft"}, list(poly.exterior.coords)))
    print("Microsoft footprints added", len(out))
    for e0, n0, e1, n1 in TRACED_HOUSES:
        out.append(({"building": "house", "source": "traced"}, [(e0, n0), (e1, n0), (e1, n1), (e0, n1), (e0, n0)]))
    return out


def _roof_colour(rc):
    if rc is None:
        return (150, 150, 146)
    rc = np.array(rc, float)
    g = rc.mean()
    # pull the satellite's haze out: a little more contrast and saturation
    rc = g + (rc - g) * 1.25
    return tuple(np.clip(rc * 1.02, 30, 240))


def _walls(m, ext, h0, h1, col):
    from geom import _area
    pts = ext if _area(ext) < 0 else ext[::-1]
    for k in range(len(pts)):
        (x0, y0), (x1, y1) = pts[k], pts[(k + 1) % len(pts)]
        m.quad("house_wall", (x1, h0, -y1), (x0, h0, -y0), (x0, h1, -y0), (x1, h1, -y1), col=_lin(col))


def _lin(c):
    c = np.asarray(c, float) / 255.0
    return tuple(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4))


def _hip_roof(m, q, eave, col, pitch=24.0, ov=0.45):
    q = np.array(q, float)
    e1, e2 = q[1] - q[0], q[3] - q[0]
    L1, L2 = np.linalg.norm(e1), np.linalg.norm(e2)
    u1, u2 = e1 / L1, e2 / L2
    o = q[0] - u1 * ov - u2 * ov
    L1, L2 = L1 + 2 * ov, L2 + 2 * ov
    if L1 < L2:
        o, u1, u2, L1, L2 = o, u2, u1, L2, L1
    hw = L2 / 2
    rise = hw * math.tan(math.radians(pitch))
    h0 = eave - ov * math.tan(math.radians(pitch))
    A = o
    B = o + u1 * L1
    Cc = o + u1 * L1 + u2 * L2
    D = o + u2 * L2
    r0 = o + u2 * hw + u1 * min(hw, L1 / 2)
    r1 = o + u2 * hw + u1 * max(L1 - hw, L1 / 2)
    P = lambda p, h: (p[0], h, -p[1])
    lc = _lin(col)
    top = h0 + rise
    for tri in ((A, B, r1, r0), (Cc, D, r0, r1)):
        a, b, c, d = tri
        _face(m, P(a, h0), P(b, h0), P(c, top), P(d, top), lc)
    _face3(m, P(B, h0), P(Cc, h0), P(r1, top), lc)
    _face3(m, P(D, h0), P(A, h0), P(r0, top), lc)
    # eaves' underside
    _qq(m, "house_soffit", P(D, h0), P(Cc, h0), P(B, h0), P(A, h0), "down")


def _gable_roof(m, q, eave, col, pitch=10.0, ov=0.3):
    q = np.array(q, float)
    e1, e2 = q[1] - q[0], q[3] - q[0]
    L1, L2 = np.linalg.norm(e1), np.linalg.norm(e2)
    u1, u2 = e1 / L1, e2 / L2
    if L1 < L2:
        u1, u2, L1, L2 = u2, u1, L2, L1
    o = q[0] - u1 * ov - u2 * ov
    L1, L2 = L1 + 2 * ov, L2 + 2 * ov
    hw = L2 / 2
    rise = hw * math.tan(math.radians(pitch))
    P = lambda p, h: (p[0], h, -p[1])
    lc = _lin(col)
    A, B, Cc, D = o, o + u1 * L1, o + u1 * L1 + u2 * L2, o + u2 * L2
    M0, M1 = o + u2 * hw, o + u1 * L1 + u2 * hw
    _face(m, P(A, eave), P(B, eave), P(M1, eave + rise), P(M0, eave + rise), lc)
    _face(m, P(Cc, eave), P(D, eave), P(M0, eave + rise), P(M1, eave + rise), lc)
    # gable ends
    for a, b, c in ((A, M0, D), (B, M1, Cc)):
        m.tri("house_wall", P(a + u1 * ov * (1 if a is A else -1), eave), P(c + u1 * ov * (1 if a is A else -1), eave),
              P(b + u1 * ov * (1 if a is A else -1), eave + rise), col=(0.6, 0.6, 0.6))
        m.tri("house_wall", P(a + u1 * ov * (1 if a is A else -1), eave), P(b + u1 * ov * (1 if a is A else -1), eave + rise),
              P(c + u1 * ov * (1 if a is A else -1), eave), col=(0.6, 0.6, 0.6))
    _qq(m, "house_soffit", P(D, eave), P(Cc, eave), P(B, eave), P(A, eave), "down")


def _face(m, a, b, c, d, col):
    a, b, c, d = (np.array(x, float) for x in (a, b, c, d))
    if np.cross(b - a, d - a)[1] < 0:
        a, b, c, d = d, c, b, a
    m.quad("house_roof", a, b, c, d, col=col)


def _face3(m, a, b, c, col):
    a, b, c = (np.array(x, float) for x in (a, b, c))
    if np.cross(b - a, c - a)[1] < 0:
        b, c = c, b
    m.tri("house_roof", a, b, c, col=col)


def _split_l(poly, q):
    """an L-shaped footprint as two rectangles: the largest rectangle inside it on the footprint's own axes, and the
    rectangle round what is left"""
    from shapely.geometry import Polygon
    q = np.array(q, float)
    u1 = _n(q[1] - q[0])
    u2 = _n(q[3] - q[0])
    pts = np.array(poly.exterior.coords)
    a = (pts - q[0]) @ u1
    b = (pts - q[0]) @ u2
    A, B = np.unique(np.round(a, 2)), np.unique(np.round(b, 2))
    best, area = None, 0
    loc = Polygon(np.stack([a, b], 1))
    for i in range(len(A)):
        for j in range(i + 1, len(A)):
            for k in range(len(B)):
                for l in range(k + 1, len(B)):
                    r = Polygon([(A[i], B[k]), (A[j], B[k]), (A[j], B[l]), (A[i], B[l])])
                    ar = r.area
                    if ar > area and loc.buffer(0.05).contains(r):
                        best, area = (A[i], A[j], B[k], B[l]), ar
    if best is None or area < 0.4 * loc.area:
        return None
    a0, a1, b0, b1 = best
    rest = loc.difference(Polygon([(a0, b0), (a1, b0), (a1, b1), (a0, b1)]))
    if rest.is_empty or rest.area < 6:
        return None
    rr = rest.minimum_rotated_rectangle
    rq = np.array(rr.exterior.coords)[:4]
    to = lambda x, y: q[0] + u1 * x + u2 * y
    r1 = np.array([to(a0, b0), to(a1, b0), to(a1, b1), to(a0, b1)])
    r2 = np.array([to(x, y) for x, y in rq])
    return [r1, r2]


# ------------------------------------------------------------------ main

def main():
    os.makedirs(OUT, exist_ok=True)
    ways, rels = load_osm()
    dem = Dem(15, R + 200)
    sat = Sat()
    canopy = sat.canopy()
    from shapely.geometry import Point
    # keep trees and vines off the oval, the precinct's hard surfaces and the buildings build.py models
    def keep_out(e, n):
        if oval2.on_oval(e, n):
            return True
        if abs(e) < HOLE and abs(n) < HOLE:
            b = math.degrees(math.atan2(e, n)) % 360
            r = math.hypot(e, n)
            if r < fence_r(b) + 22:
                return True
            if -180 < e < -55 and -25 < n < 165:      # courts, clubrooms, pavilion
                return True
            if -175 < e < -90 and -22 < n < 30:      # west car park, shed, tanks
                return True
        return False
    sat_cls = coarse_classes(sat, canopy)
    tex = paint_land(ways, rels, sat_cls)
    land, th = terrain(dem, tex)
    from shapely.geometry import Polygon
    from shapely.prepared import prep
    from shapely.ops import unary_union
    vy = unary_union([Polygon(p).buffer(0) for t, p in ways if t.get("landuse") == "vineyard" and len(p) > 3
                     and not oval2.stale_vineyard(p)])
    pv = prep(vy)
    tr = trees(sat, canopy, th, keep_out, lambda e, n: pv.contains(Point(e, n)))
    vm = Mesh()
    nv = vines(sat, ways, th, keep_out, vm)
    hm = Mesh()
    # inside the precinct square, only the buildings build.py models are left out (the temporary stands too): the
    # town's houses and sheds in the square's corners stay
    from plan import TEMP_STANDS
    def seg_d(e, n, a, b):
        a, b, p = np.array(a), np.array(b), np.array((e, n))
        t = np.clip(np.dot(p - a, b - a) / np.dot(b - a, b - a), 0, 1)
        return float(np.hypot(*(p - a - t * (b - a))))
    def house_out(e, n):
        return keep_out(e, n) or any(seg_d(e, n, st["a"], st["b"]) < 16 for st in TEMP_STANDS) \
            or math.hypot(e - 88, n + 52) < 8
    nh = houses(sat, ways + ms_buildings(ways), th, house_out, hm)
    print("trees", len(tr), "vine segments", nv, "houses", nh, "land tris", land.tris(), "vine tris", vm.tris(),
          "house tris", hm.tris())
    from PIL import Image as _I
    import io
    mats = {
        "land": {"tex": (tex, 2 * R, 2 * R), "rough": 1.0},
        "vine": {"col": _lin((74, 92, 52)), "rough": 0.95},
        "vine_top": {"col": _lin((96, 112, 62)), "rough": 0.95},
        "vine_under": {"col": _lin((40, 46, 30)), "rough": 1.0},
        "house_wall": {"col": (1, 1, 1), "vcol": True, "rough": 0.9},
        "house_roof": {"col": (1, 1, 1), "vcol": True, "rough": 0.6},
        "house_soffit": {"col": _lin((180, 176, 168)), "rough": 0.9},
    }
    write_glb(os.path.join(OUT, "barossa_land.glb"), [("land", land), ("vines", vm), ("houses", hm)], mats, jpeg=True)
    buf = np.array(tr, np.float32).reshape(-1)
    open(os.path.join(OUT, "trees.bin"), "wb").write(buf.tobytes())


if __name__ == "__main__":
    main()
