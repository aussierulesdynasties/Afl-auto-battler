"""Where Traeger Park is, and the open data its scene is built from.

- The model's origin: the centre of OpenStreetMap's AFL pitch (way 242194673, the mean of its nodes),
  lat -23.7097309, lon 133.8759053. Model metres: x east, z south (glTF), y up.
- Heights: the open Terrarium elevation tiles (Mapzen / AWS open data, zoom 13, about 17 m a sample here).
- Colour: Sentinel-2 L2A true colour (10 m), scene S2B_53KLP_20251029 (late October 2025, cloud free),
  read from the open sentinel-cogs bucket. Contains modified Copernicus Sentinel data 2025.
"""
import math
import os
import urllib.request

import numpy as np
from PIL import Image

LAT0, LON0 = -23.7097309, 133.8759053
KX = 111320.0 * math.cos(math.radians(LAT0))
KY = 110574.0
CACHE = os.environ.get("TRAEGER_CACHE", "/tmp/traeger_cache")
DEM_Z = 13
S2 = ("https://sentinel-cogs.s3.us-west-2.amazonaws.com/sentinel-s2-l2a-cogs/53/K/LP/2025/10/"
      "S2B_53KLP_20251029_0_L2A/")


def latlon(e, n):
    return LAT0 + np.asarray(n) / KY, LON0 + np.asarray(e) / KX


def en(lat, lon):
    return (np.asarray(lon) - LON0) * KX, (np.asarray(lat) - LAT0) * KY


def _txy(lat, lon, z=DEM_Z):
    n = 2 ** z
    lat = np.asarray(lat, float)
    return ((np.asarray(lon) + 180) / 360 * n,
            (1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / math.pi) / 2 * n)


class Dem:
    """Heights above the sea (m) at any east/north metres, bilinear between the tile samples."""

    def __init__(self, r):
        d = os.path.join(CACHE, "dem")
        os.makedirs(d, exist_ok=True)
        la1, lo1 = latlon(-r, r)
        la2, lo2 = latlon(r, -r)
        x0, y0 = _txy(la1, lo1)
        x1, y1 = _txy(la2, lo2)
        self.tx0, self.ty0 = int(x0), int(y0)
        nx, ny = int(x1) - self.tx0 + 1, int(y1) - self.ty0 + 1
        self.h = np.zeros((ny * 256, nx * 256), np.float32)
        for i in range(nx):
            for j in range(ny):
                p = os.path.join(d, "%d_%d_%d.png" % (DEM_Z, self.tx0 + i, self.ty0 + j))
                if not os.path.exists(p):
                    urllib.request.urlretrieve("https://s3.amazonaws.com/elevation-tiles-prod/terrarium/%d/%d/%d.png"
                                               % (DEM_Z, self.tx0 + i, self.ty0 + j), p)
                a = np.asarray(Image.open(p).convert("RGB"), np.float32)
                self.h[j * 256:(j + 1) * 256, i * 256:(i + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768

    def at(self, e, n):
        x, y = _txy(*latlon(e, n))
        fx, fy = (x - self.tx0) * 256 - 0.5, (y - self.ty0) * 256 - 0.5
        x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
        ax, ay = fx - x0, fy - y0
        H = self.h
        x0 = np.clip(x0, 0, H.shape[1] - 2)
        y0 = np.clip(y0, 0, H.shape[0] - 2)
        return (H[y0, x0] * (1 - ax) * (1 - ay) + H[y0, x0 + 1] * ax * (1 - ay)
                + H[y0 + 1, x0] * (1 - ax) * ay + H[y0 + 1, x0 + 1] * ax * ay)


def s2_band(name, r):
    """A Sentinel-2 band (or 'TCI', 3 x rows x cols) round the origin, r m each way, in its own UTM grid,
    with the UTM easting/northing of its top-left corner."""
    import rasterio
    from rasterio.windows import from_bounds
    from rasterio.warp import transform
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, "s2_%s_%d.npz" % (name, r))
    if os.path.exists(p):
        z = np.load(p)
        return z["a"], float(z["x0"]), float(z["y0"])
    with rasterio.open("/vsicurl/" + S2 + name + ".tif") as ds:
        xs, ys = transform("EPSG:4326", ds.crs, [LON0], [LAT0])
        b = (max(ds.bounds.left, xs[0] - r), max(ds.bounds.bottom, ys[0] - r),
             min(ds.bounds.right, xs[0] + r), min(ds.bounds.top, ys[0] + r))
        w = from_bounds(*b, ds.transform).round_offsets().round_lengths()
        a = ds.read(window=w)
        t = ds.window_transform(w)
    np.savez(p, a=a, x0=t.c, y0=t.f)
    return a, t.c, t.f


def _utm_of(e, n):
    """UTM 53S easting/northing of local east/north metres (exact on a coarse grid, linear between)."""
    from rasterio.warp import transform
    la, lo = latlon(e, n)
    x, y = transform("EPSG:4326", "EPSG:32753", list(np.ravel(lo)), list(np.ravel(la)))
    return np.reshape(x, np.shape(e)), np.reshape(y, np.shape(e))


def s2_local(name, r, size):
    """The band resampled onto a north-up local grid size x size covering east/north -r..r (bilinear).
    Returns float array (rows north to south, cols west to east, channels last)."""
    a, x0, y0 = s2_band(name, r + 400)
    if a.ndim == 2:
        a = a[None]
    a = np.moveaxis(a, 0, -1).astype(np.float32)
    k = 65
    g = np.linspace(-r, r, k)
    GE, GN = np.meshgrid(g, g[::-1])
    UX, UY = _utm_of(GE, GN)
    # bilinear interpolation of the coarse mapping to the full grid
    from scipy.ndimage import map_coordinates
    t = (np.arange(size) + 0.5) / size * (k - 1)
    TI, TJ = np.meshgrid(t, t)          # TJ rows, TI cols
    ux = map_coordinates(UX, [TJ, TI], order=1)
    uy = map_coordinates(UY, [TJ, TI], order=1)
    px = (ux - x0) / 10.0 - 0.5
    py = (y0 - uy) / 10.0 - 0.5
    out = np.stack([map_coordinates(a[..., c], [py, px], order=1, mode="nearest") for c in range(a.shape[2])], -1)
    return out


def osm(r=1400.0):
    """OpenStreetMap round the ground (main API, in 0.008 degree tiles cached in CACHE/osm): returns
    (nodes {id: (e, n, tags)}, ways [(id, tags, [(e, n)...])], relations' outer ways as extra ways).
    Map data (c) OpenStreetMap contributors, ODbL."""
    import xml.etree.ElementTree as ET
    d = os.path.join(CACHE, "osm")
    os.makedirs(d, exist_ok=True)
    step = 0.008
    k = int(math.ceil(r / (step * KY) + 0.5))
    nodes, ways, rels = {}, {}, []
    for i in range(-k, k + 1):
        for j in range(-k, k + 1):
            p = os.path.join(d, "t_%d_%d.osm" % (i, j))
            if not os.path.exists(p):
                a, b = LON0 + i * step - step / 2, LAT0 + j * step - step / 2
                url = "https://api.openstreetmap.org/api/0.6/map?bbox=%.6f,%.6f,%.6f,%.6f" % (a, b, a + step, b + step)
                req = urllib.request.Request(url, headers={"User-Agent": "afl-ground-builder/1.0"})
                with urllib.request.urlopen(req, timeout=120) as resp, open(p, "wb") as f:
                    f.write(resp.read())
            root = ET.parse(p).getroot()
            for n in root.iter("node"):
                e_, n_ = en(float(n.get("lat")), float(n.get("lon")))
                nodes[n.get("id")] = (float(e_), float(n_), {t.get("k"): t.get("v") for t in n.iter("tag")})
            for w in root.iter("way"):
                ways[w.get("id")] = ([x.get("ref") for x in w.iter("nd")], {t.get("k"): t.get("v") for t in w.iter("tag")})
            for rel in root.iter("relation"):
                t = {x.get("k"): x.get("v") for x in rel.iter("tag")}
                if t.get("type") == "multipolygon":
                    rels.append((rel.get("id"), t, [m.get("ref") for m in rel.iter("member")
                                                    if m.get("type") == "way" and m.get("role") == "outer"]))
    out = []
    for wid, (nds, t) in ways.items():
        pts = [nodes[x][:2] for x in nds if x in nodes]
        if len(pts) > 1:
            out.append((wid, t, pts))
    seen = set()
    for rid, t, members in rels:
        if rid in seen:
            continue
        seen.add(rid)
        for m in members:
            if m in ways:
                pts = [nodes[x][:2] for x in ways[m][0] if x in nodes]
                if len(pts) > 2:
                    out.append(("r" + rid + "_" + m, t, pts))
    return nodes, out


# Meta and WRI's 1 m canopy height map (2024, CC BY 4.0), one zoom-9 quadkey tile over Alice Springs.
CHM = "https://dataforgood-fb-data.s3.amazonaws.com/forests/v1/alsgedi_global_v6_float/chm/310311130.tif"


class Chm:
    """Tree canopy height (m above ground) at east/north, read from the Web Mercator tile (1.19 m cells)."""

    def __init__(self, r=1450.0):
        path = os.path.join(CACHE, "chm_%d.npz" % r)
        R = 6378137.0
        x0 = math.radians(LON0) * R
        y0 = R * math.log(math.tan(math.pi / 4 + math.radians(LAT0) / 2))
        k = 1 / math.cos(math.radians(LAT0))
        if not os.path.exists(path):
            import rasterio
            from rasterio.windows import from_bounds
            with rasterio.open("/vsicurl/" + CHM) as d:
                w = from_bounds(x0 - r * k, y0 - r * k, x0 + r * k, y0 + r * k, d.transform)
                a = d.read(1, window=w)
                tr = d.window_transform(w)
            os.makedirs(CACHE, exist_ok=True)
            np.savez_compressed(path, a=a, tr=np.array(tr)[:6])
        z = np.load(path)
        self.a, tr = z["a"].astype(np.float32), z["tr"]
        self.res, self.left, self.top = tr[0], tr[2], tr[5]
        self.x0, self.y0, self.k = x0, y0, k

    def at(self, e, n, rad=0.0):
        """The tallest canopy within rad metres of (e, n)."""
        c = (self.x0 + e * self.k - self.left) / self.res
        rr = (self.top - (self.y0 + n * self.k)) / self.res
        w = int(math.ceil(rad * self.k / self.res))
        i0, j0 = int(rr), int(c)
        blk = self.a[max(0, i0 - w):i0 + w + 1, max(0, j0 - w):j0 + w + 1]
        return float(blk.max()) if blk.size else 0.0
