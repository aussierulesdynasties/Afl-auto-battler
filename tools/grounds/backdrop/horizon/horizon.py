"""A ground's horizon: the real land, water and city past its backdrop, out to where the haze takes everything
(row 202 2b, the aerial orbit). <slug>_horizon.glb, which GroundModels.backdrop() loads with
the backdrop's parts (in place of the scene's own far terrain) and which opens the camera and the haze to 60 km.

    python3 horizon.py fetch <slug>      # Overture buildings + the EU's building-height map into $HORIZON_WORK
    python3 s2grid.py <slug> 5120 10 near; python3 s2grid.py <slug> 20480 40 mid; python3 s2grid.py <slug> 70000 150 far
    python3 horizon.py build <slug>      # -> assets/grounds/<slug>/<slug>_horizon.glb (+ a report)

Why. The backdrops end at their ±1.5 km square; past it the scene's far terrain was one plain olive colour that the
camera clipped at 7 km, so from the air the world ended in a straight hard line (Marvel's orbit, defect A), and the
CBD and Fishermans Bend past 1.5 km were not there at all (C, D).

What it builds, all in the model's own frame (x east, z south, y up, the arena floor at FIT[2]):
- land: square rings from the backdrop's edge out to LAND_OUT, about one vertex every 3 % of the distance (47 m at
  1.5 km, 2 km at 64 km). Heights from terrain.bin where it reaches (the same land the game's ring and the re-landed
  backdrop stand on), past it Mapterhorn's tiles (Geoscience Australia 5 m LiDAR, Copernicus GLO-30 further out)
  at a zoom whose pixel matches the ring's spacing; the earth's curve is taken off (with the usual 13 % for
  refraction), so far land drops behind the horizon as it does. Water (Sentinel-2's water share over half) lies flat
  at the backdrop's own water level;
- colour: Sentinel-2 (Digital Earth Australia, CC BY 4.0), median of the clear autumn and winter looks, scaled per
  channel so that under the backdrop's own square it matches the backdrop's ground bake (the seam keeps one colour):
  a 10 m texture to 5 km, a 40 m texture to 20 km, vertex colours past it. Lit by the match's own sun;
- the city between the backdrop's square and CITY_OUT: every Overture building (OpenStreetMap and Microsoft
  footprints), its mapped height (height, or levels x 3.4 m + 1 m), towers as their mapped parts (podium, shaft,
  crown). Where nothing gives a height, it is read from the EU's GHS-BUILT-H 2018 map (100 m cells, CC BY 4.0)
  through a table of the mapped buildings of the same kind and size in the same cell height, built from this
  ground's own neighbours (its error is printed). Rows of low buildings of one height that touch are joined into one
  block, as they read from a kilometre up. Drawn by the game's tower shader (material "city_towers"), roofs in their
  Sentinel-2 colour.
"""
import collections
import json
import math
import os
import struct
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", "..", ".."))
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "..", "terrain"))
import reland   # noqa: E402  (Land: terrain.bin as GroundTerrain.gd reads it; Glb; fit)
import terrain  # noqa: E402  (Mapterhorn tiles)

WORK = os.environ.get("HORIZON_WORK", os.path.expanduser("~/.cache/afl_horizon"))
OVERTURE = "s3://overturemaps-us-west-2/release/2026-11-18.0/theme=buildings/type=%s/*"
GHSL = ("https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_H_GLOBE_R2023A/"
        "GHS_BUILT_H_ANBH_E2018_GLOBE_R2023A_54009_100/V1-0/tiles/GHS_BUILT_H_ANBH_E2018_GLOBE_R2023A_54009_100_V1_0_R%d_C%d.zip")
R_EARTH = 6378137.0
REFRACTION = 0.13
INNER = 1500.0        # the backdrop's own square (reduce.py's near box)
SKIRT = 1480.0        # the first ring tucks under the backdrop's edge, so no crack shows
LAND_OUT = 64000.0
SIDE = 64             # vertices along each side of a ring
TEX_A, TEX_B = 5120.0, 20480.0
CITY_OUT = 4096.0
LEVEL_M, LEVEL_BASE = 3.4, 1.0   # prep.py's storey height
JOIN_BELOW = 20.0     # low buildings of one height band that touch are joined
JOIN_BAND = 3.0
JOIN_GAP = 2.0        # m: across a lane or a gap between neighbours narrower than twice this, they are one block
LOW_SIMPLIFY = 2.0    # m: a low block's outline is kept to this
WEDGES = 8
FAR_ZONE = 2500.0     # past this (square distance) joins and outlines are twice as coarse: a 4 m step there is
                      # under a pixel from the orbit's 430 m circle


def ground(slug):
    g = json.load(open(os.path.join(ROOT, "tools", "grounds", "terrain", "grounds.json")))[slug]
    return g


def work(slug, *p):
    d = os.path.join(WORK, slug)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, *p)


# ---- fetch ----------------------------------------------------------------------------------------

def fetch(slug):
    import duckdb
    import urllib.request
    import zipfile
    from pyproj import Transformer
    g = ground(slug)
    lat, lon = g["lat"], g["lon"]
    d = CITY_OUT * 1.08
    dx, dy = d / (R_EARTH * math.radians(1) * math.cos(math.radians(lat))), d / (R_EARTH * math.radians(1))
    con = duckdb.connect()
    con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial; SET enable_progress_bar=false;")
    con.execute("CREATE OR REPLACE SECRET anon (TYPE s3, PROVIDER config, KEY_ID '', SECRET '', REGION 'us-west-2')")
    box = "bbox.xmin>%f and bbox.xmax<%f and bbox.ymin>%f and bbox.ymax<%f" % (lon - dx, lon + dx, lat - dy, lat + dy)
    for kind, extra in (("building", "class, subtype, has_parts, is_underground"), ("building_part", "building_id")):
        q = ("select id, height, num_floors, min_height, min_floor, roof_shape, sources[1].dataset as src, %s, "
             "ST_AsText(geometry) as wkt from read_parquet('%s', hive_partitioning=1) where %s") % (extra, OVERTURE % kind, box)
        cur = con.execute(q)
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        json.dump(rows, open(work(slug, "overture_%s.json" % kind), "w"), default=str)
        print(kind, len(rows))
    x, y = Transformer.from_crs(4326, "ESRI:54009", always_xy=True).transform(lon, lat)
    col, row = int((x + 18041000) // 1000000) + 1, int((9000000 - y) // 1000000) + 1
    z = work(slug, "ghsl.zip")
    urllib.request.urlretrieve(GHSL % (row, col), z)
    with zipfile.ZipFile(z) as f:
        name = next(n for n in f.namelist() if n.endswith(".tif"))
        open(work(slug, "ghsl.tif"), "wb").write(f.read(name))
    print("ghsl tile R%d C%d" % (row, col))


# ---- frames ---------------------------------------------------------------------------------------

class Frame:
    """lat/lon <-> metres east/north of the centre circle <-> the model's x, z."""

    def __init__(self, slug):
        g = ground(slug)
        self.lat0, self.lon0 = g["lat"], g["lon"]
        f = reland.fit(slug)
        self.cx, self.cz, self.floor = f[0], f[1], f[2]

    def en(self, lon, lat):
        e = np.radians(np.asarray(lon, float) - self.lon0) * R_EARTH * math.cos(math.radians(self.lat0))
        n = np.radians(np.asarray(lat, float) - self.lat0) * R_EARTH
        return e, n

    def xz(self, e, n):
        return self.cx + np.asarray(e, float), self.cz - np.asarray(n, float)

    def e_n_of(self, x, z):
        return np.asarray(x, float) - self.cx, -(np.asarray(z, float) - self.cz)


def drop(x, z):
    """The earth's curve under a flat model: how far a point this far out lies below the turf's level plane."""
    d2 = np.asarray(x, float) ** 2 + np.asarray(z, float) ** 2
    return d2 / (2 * R_EARTH) * (1 - REFRACTION)


class Heights:
    """Model-frame land height (no curve) anywhere: terrain.bin inside its coarse grid, Mapterhorn past it, blended
    over the coarse grid's last 400 m so the two never step."""

    def __init__(self, slug, frame):
        self.F = frame
        self.land = reland.Land(slug)
        g = ground(slug)
        self.datum = float(terrain.source_heights(g, np.array([0.0]), np.array([0.0]))[0]) + g.get("turf_above_data_m", 0.0)
        self.g = g
        self.reach = self.land.reach() - 2 * self.land.coarse[1]

    def mapterhorn(self, e, n, spacing):
        # a zoom whose pixel is about half the spacing (Mapterhorn's lower zooms are averaged, so a far ring is not
        # a point sample of one 5 m pixel)
        m_per_px_z0 = 2 * math.pi * R_EARTH * math.cos(math.radians(self.g["lat"])) / 512
        out = np.empty(e.shape)
        sp = np.broadcast_to(spacing, e.shape)
        zs = np.clip(np.round(np.log2(m_per_px_z0 / np.maximum(sp / 2, 5.0))), 6, 14).astype(int)
        for z in np.unique(zs):
            m = zs == z
            lat, lon = terrain.to_latlon(self.g["lat"], self.g["lon"], e[m], n[m])
            out[m] = terrain.sample_mapterhorn(lat, lon, int(z)) - self.datum
        return self.F.floor + out

    def at(self, e, n, spacing):
        e, n = np.asarray(e, float), np.asarray(n, float)
        r = np.maximum(np.abs(e), np.abs(n))
        x, z = self.F.xz(e, n)
        out = np.full(e.shape, np.nan)
        inn = r < self.reach
        if inn.any():
            out[inn] = self.land.height(x[inn], z[inn])
        far = r >= self.reach - 400
        if far.any():
            mh = self.mapterhorn(e[far], n[far], np.broadcast_to(spacing, e.shape)[far])
            w = np.clip((r[far] - (self.reach - 400)) / 400, 0, 1)
            near_v = np.where(np.isnan(out[far]), mh, out[far])
            out[far] = near_v * (1 - w) + mh * w
        return out


# ---- colour ---------------------------------------------------------------------------------------

class S2:
    def __init__(self, slug, name):
        self.M = np.load(work(slug, name + ".npy"))
        self.W = np.load(work(slug, name + "_water.npy"))
        meta = json.load(open(work(slug, name + ".json")))
        self.half, self.step = meta["half_m"], meta["m_per_px"]
        bad = np.isnan(self.M).any(-1)
        if bad.any():   # no look at all (the tile edge): the nearest pixel that has one
            from scipy.ndimage import distance_transform_edt
            _, (ri, ci) = distance_transform_edt(bad, return_indices=True)
            self.M = self.M[ri, ci]
        self.W = np.nan_to_num(self.W, nan=0.0)

    def rc(self, e, n):
        return (self.half - np.asarray(n)) / self.step - 0.5, (np.asarray(e) + self.half) / self.step - 0.5

    def sample(self, e, n, arr=None, blur_m=0.0):
        from scipy.ndimage import gaussian_filter, map_coordinates
        a = self.M if arr is None else arr
        r, c = self.rc(e, n)
        if blur_m > self.step:
            s = blur_m / self.step / 2
            a = gaussian_filter(a, (s, s, 0) if a.ndim == 3 else (s, s))
        if a.ndim == 3:
            return np.stack([map_coordinates(a[..., k], [r, c], order=1, mode="nearest") for k in range(a.shape[2])], -1)
        return map_coordinates(a, [r, c], order=1, mode="nearest")


def srgb(lin):
    lin = np.clip(lin, 0, 1)
    return np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055)


def lin_of(s):
    s = np.asarray(s, float)
    return np.where(s <= 0.04045, s / 12.92, np.power((s + 0.055) / 1.055, 2.4))


def seam_gain(glb, frame, near):
    """Per channel: reflectance -> the backdrop's own ground bake (linear), least squares over 60 m blocks of the
    backdrop's square, so the two meet in one colour."""
    from PIL import Image
    import io
    prim = next(p for p in glb.prims if p[0].startswith("bg_near_ground"))
    mi = next(i for i, m in enumerate(glb.J["meshes"]) if any(p["attributes"]["POSITION"] == prim[1] for p in m["primitives"]))
    pr = next(p for p in glb.J["meshes"][mi]["primitives"] if p["attributes"]["POSITION"] == prim[1])
    P = glb.read(pr["attributes"]["POSITION"]).astype(float)
    UV = glb.read(pr["attributes"]["TEXCOORD_0"]).astype(float)
    mat = glb.J["materials"][pr["material"]]
    ti = mat["pbrMetallicRoughness"]["baseColorTexture"]["index"]
    tx = glb.J["textures"][ti]
    im = glb.J["images"][tx["source"] if "source" in tx else next(iter(tx["extensions"].values()))["source"]]
    bv = glb.J["bufferViews"][im["bufferView"]]
    img = np.asarray(Image.open(io.BytesIO(bytes(glb.bin[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]]))).convert("RGB"), float) / 255
    A = np.c_[P[:, 0], P[:, 2], np.ones(len(P))]
    cu, cv = np.linalg.lstsq(A, UV[:, 0], rcond=None)[0], np.linalg.lstsq(A, UV[:, 1], rcond=None)[0]
    blk = 60.0
    xs = np.arange(-1440, 1441, blk)
    X, Z = np.meshgrid(xs, xs)
    X, Z = X.ravel(), Z.ravel()
    h, w = img.shape[:2]
    lin_img = lin_of(img)
    bake = []
    k = int(blk / (3000 / w) / 2)
    for x, z in zip(X, Z):
        u, v = cu @ [x, z, 1], cv @ [x, z, 1]
        c, r = int(u * w), int(v * h)
        bake.append(lin_img[max(0, r - k):r + k, max(0, c - k):c + k].reshape(-1, 3).mean(0))
    bake = np.array(bake)
    e, n = frame.e_n_of(X, Z)
    s2 = near.sample(e, n, blur_m=blk) / 10000.0
    wat = near.sample(e, n, near.W, blur_m=blk) > 0.5
    ok = ~wat & np.isfinite(bake).all(1)
    gain = np.array([(bake[ok, c] * s2[ok, c]).sum() / (s2[ok, c] ** 2).sum() for c in range(3)])
    resid = np.abs(s2[ok] * gain - bake[ok]).mean(0)
    print("seam colour gain", gain.round(3), "mean miss (linear)", resid.round(4), "blocks", int(ok.sum()))
    return gain


# ---- land mesh ------------------------------------------------------------------------------------

def ring_sizes():
    """Half-sizes of the square rings: SKIRT, INNER, then about 1 + 2/SIDE apart, landing on TEX_A, TEX_B and LAND_OUT."""
    s = [SKIRT, INNER]
    for a, b in ((INNER, TEX_A), (TEX_A, TEX_B), (TEX_B, LAND_OUT)):
        k = max(1, int(round(math.log(b / a) / math.log(1 + 2.0 / SIDE))))
        s += list(a * (b / a) ** (np.arange(1, k + 1) / k))
    return np.array(s)


def ring_points(s):
    t = np.arange(4 * SIDE) / SIDE      # 0..4 round the square, anticlockwise from the south-west corner (e, n)
    side, f = np.floor(t).astype(int), t - np.floor(t)
    e = np.select([side == 0, side == 1, side == 2, side == 3], [-s + 2 * s * f, np.full_like(f, s), s - 2 * s * f, np.full_like(f, -s)])
    n = np.select([side == 0, side == 1, side == 2, side == 3], [np.full_like(f, -s), -s + 2 * s * f, np.full_like(f, s), s - 2 * s * f])
    return e, n


def land_mesh(slug, frame, H, water_y, gain, near, mid, far):
    S = ring_sizes()
    E, N, SP = [], [], []
    for s in S:
        e, n = ring_points(s)
        E.append(e); N.append(n); SP.append(np.full(e.shape, 2 * s / SIDE))
    E, N, SP = np.array(E), np.array(N), np.array(SP)   # (rings, 4*SIDE)
    Y = H.at(E.ravel(), N.ravel(), SP.ravel()).reshape(E.shape)
    # water: Sentinel-2's share of clear looks that saw water, read from the finest grid that reaches
    W = np.zeros(E.shape)
    for src in (far, mid, near):
        m = np.maximum(np.abs(E), np.abs(N)) < src.half - src.step
        W[m] = src.sample(E[m], N[m], src.W, blur_m=SP[m].mean() if m.any() else 0)
    wet = W > 0.5
    Y = np.where(wet, water_y, Y)
    # the shore: land at or under the water's level by the water stays a hair over it, so it never drowns in stripes
    Y = np.where(~wet & (Y < water_y + 0.2), water_y + 0.2, Y)
    Y[0] -= 1.5       # the skirt under the backdrop's edge
    Y[1] -= 0.3
    x, z = frame.xz(E, N)
    Y = Y - drop(x, z)
    nr, nc = E.shape
    V = np.stack([x, Y, z], -1).reshape(-1, 3)
    # normals from the ring grid
    P = V.reshape(nr, nc, 3)
    dr = np.gradient(P, axis=0)
    dc = np.roll(P, -1, 1) - np.roll(P, 1, 1)
    Nn = np.cross(dc, dr)
    Nn *= np.where(Nn[..., 1:2] < 0, -1, 1)
    Nn /= np.linalg.norm(Nn, axis=-1, keepdims=True)
    Nn = Nn.reshape(-1, 3)
    # colours
    r = np.maximum(np.abs(E), np.abs(N)).ravel()
    e, n = E.ravel(), N.ravel()
    col = far.sample(e, n, blur_m=1.0) / 10000.0
    m = r < far.half - far.step
    col[m] = far.sample(e[m], n[m], blur_m=float(np.median(SP.ravel()[m]))) / 10000.0
    col = np.clip(col * gain, 0, 1)
    surfaces = []
    ka = int(np.searchsorted(S, TEX_A - 1e-6))
    kb = int(np.searchsorted(S, TEX_B - 1e-6))
    for name, r0, r1, tex in (("land_a", 0, ka, ("near", TEX_A)), ("land_b", ka, kb, ("mid", TEX_B)), ("land_c", kb, nr - 1, None)):
        idx = []
        for k in range(r0, r1):
            a = k * nc + np.arange(nc)
            b = (k + 1) * nc + np.arange(nc)
            a1, b1 = k * nc + (np.arange(nc) + 1) % nc, (k + 1) * nc + (np.arange(nc) + 1) % nc
            idx.append(np.stack([a, b1, b, a, a1, b1], 1).ravel())
        idx = np.concatenate(idx)
        used = np.unique(idx)
        remap = np.full(len(V), -1)
        remap[used] = np.arange(len(used))
        surf = {"name": name, "pos": V[used].astype(np.float32), "nrm": Nn[used].astype(np.float32),
                "idx": remap[idx].astype(np.uint32)}
        if tex:
            half = tex[1]
            ee, nn = e[used], n[used]
            surf["uv"] = np.stack([(ee + half) / (2 * half), (half - nn) / (2 * half)], 1).astype(np.float32)
            surf["tex"] = tex[0]
        else:
            surf["col"] = np.c_[col[used], np.ones(len(used))].astype(np.float32)
        surfaces.append(surf)
    return surfaces, {"rings": int(nr), "per_ring": int(nc), "water_vertices": int(wet.sum())}


def texture_png(src, gain, size=1024):
    """The Sentinel-2 grid as an sRGB png (the material's albedo), north up."""
    from PIL import Image
    M = src.M / 10000.0 * gain
    img = (srgb(M) * 255 + 0.5).astype(np.uint8)
    if img.shape[0] != size:
        img = np.asarray(Image.fromarray(img).resize((size, size), Image.LANCZOS))
    import io
    b = io.BytesIO()
    Image.fromarray(img).save(b, "PNG", optimize=True)
    return b.getvalue()


# ---- city -----------------------------------------------------------------------------------------

CATEGORY = {"house": "h", "detached": "h", "semidetached_house": "h", "terrace": "h", "residential": "r",
            "apartments": "r", "industrial": "i", "warehouse": "i", "commercial": "c", "retail": "c", "office": "c"}
# GroundModels._add_towers' palettes (Color8), so the far towers read like the ring's own
TOWER_GLASS = [(84, 100, 114), (76, 92, 106), (96, 110, 120), (70, 84, 98), (104, 116, 126), (80, 96, 100)]
TOWER_CONCRETE = [(146, 150, 152), (130, 134, 138), (150, 154, 156), (122, 128, 134), (140, 146, 152), (116, 120, 126)]
LOW_WALLS = [(219, 214, 204), (199, 194, 184), (184, 153, 128), (230, 224, 214), (168, 168, 168)]   # _add_towers WALLS


def mapped_height(r):
    if r.get("height") not in (None, "None"):
        return float(r["height"])
    if r.get("num_floors") not in (None, "None"):
        return float(r["num_floors"]) * LEVEL_M + LEVEL_BASE
    return None


def part_base(r):
    if r.get("min_height") not in (None, "None"):
        return float(r["min_height"])
    if r.get("min_floor") not in (None, "None"):
        return float(r["min_floor"]) * LEVEL_M
    return 0.0


class HeightTable:
    """Untagged buildings' height: the median of the mapped ones of the same kind, size (log2 m2) and GHS-BUILT-H
    cell height (3 m bands), falling back to size and cell height alone. Cross-checked five ways at build."""

    def __init__(self, rows, ghsl_at):
        self.ghsl_at = ghsl_at
        self.tab, self.tab2 = collections.defaultdict(list), collections.defaultdict(list)
        keyed = [(self.key(r), r["_h"]) for r in rows if r["_h"] is not None]
        rng = np.random.default_rng(0)
        fold = rng.integers(0, 5, len(keyed))
        err = []
        for f in range(5):
            t1, t2 = collections.defaultdict(list), collections.defaultdict(list)
            for (k, h), fo in zip(keyed, fold):
                if fo != f:
                    t1[k].append(h); t2[k[1:]].append(h)
            for (k, h), fo in zip(keyed, fold):
                if fo == f:
                    err.append((self._look(t1, t2, k) - h, h))
        E = np.array(err)
        self.report = {}
        for lo, hi in ((0, 6), (6, 10), (10, 20), (20, 400)):
            m = (E[:, 1] >= lo) & (E[:, 1] < hi)
            if m.any():
                self.report["%d-%d m" % (lo, hi)] = {"n": int(m.sum()), "mean_abs_err_m": round(float(np.abs(E[m, 0]).mean()), 1)}
        for k, h in keyed:
            self.tab[k].append(h); self.tab2[k[1:]].append(h)

    def key(self, r):
        return (CATEGORY.get(r.get("class"), "o"), min(int(math.log2(max(r["_area"], 16))), 12), min(int(r["_ghsl"] // 3), 12))

    @staticmethod
    def _look(t1, t2, k):
        if len(t1.get(k, [])) >= 5:
            return float(np.median(t1[k]))
        if len(t2.get(k[1:], [])) >= 3:
            return float(np.median(t2[k[1:]]))
        return max(3.5, k[2] * 3 + 1.5)

    def height(self, r):
        return self._look(self.tab, self.tab2, self.key(r))


def city(slug, frame, H, gain, near):
    import rasterio
    from pyproj import Transformer
    from shapely import wkt
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    import mapbox_earcut as earcut
    rows = json.load(open(work(slug, "overture_building.json")))
    parts = json.load(open(work(slug, "overture_building_part.json")))
    ds = rasterio.open(work(slug, "ghsl.tif"))
    gh = ds.read(1)
    to_moll = Transformer.from_crs(4326, "ESRI:54009", always_xy=True)

    def local(geom):
        out = []
        for g in getattr(geom, "geoms", [geom]):
            if g.geom_type != "Polygon" or g.is_empty:
                continue
            lon, lat = np.array(g.exterior.coords).T
            e, n = frame.en(lon, lat)
            out.append(Polygon(np.c_[e, n]).buffer(0))
        return out

    def ghsl_at(lon, lat):
        x, y = to_moll.transform(lon, lat)
        r, c = ds.index(x, y)
        return max(float(gh[r, c]), 0.0) if 0 <= r < gh.shape[0] and 0 <= c < gh.shape[1] else 0.0

    for r in rows:
        g = wkt.loads(r["wkt"])
        c = g.centroid
        r["_geom"] = g
        r["_area"] = g.area * (R_EARTH * math.radians(1)) ** 2 * math.cos(math.radians(frame.lat0))
        r["_ghsl"] = ghsl_at(c.x, c.y)
        r["_h"] = mapped_height(r)
    table = HeightTable([r for r in rows if r.get("is_underground") not in (True, "True")], ghsl_at)
    print("height table check (estimate minus mapped, held-out fifths):", table.report)
    by_parts = collections.defaultdict(list)
    for p in parts:
        by_parts[p["building_id"]].append(p)
    pieces = []   # (polygon in e/n, base above ground, top above ground, look id, tall?)
    src = collections.Counter()
    for r in rows:
        if r.get("is_underground") in (True, "True"):
            continue
        c = r["_geom"].centroid
        e, n = frame.en(c.x, c.y)
        x, z = frame.xz(e, n)
        if max(abs(x), abs(z)) < INNER or max(abs(e), abs(n)) > CITY_OUT:
            continue
        look = zlib.crc32(r["id"].encode()) & 0x7FFFFFFF
        ps = by_parts.get(r["id"])
        if ps:
            for p in ps:
                top = mapped_height(p) or r["_h"]
                if top is None:
                    continue
                for poly in local(wkt.loads(p["wkt"])):
                    pieces.append((poly, part_base(p), top, look, True))
            src["mapped parts"] += 1
            continue
        h = r["_h"]
        src["mapped" if h is not None else "estimated"] += 1
        if h is None:
            h = table.height(r)
        if h < 2.0:
            continue
        for poly in local(r["_geom"]):
            pieces.append((poly, 0.0, h, look, h >= JOIN_BELOW))
    print("city buildings:", dict(src))
    # join touching low buildings of one height band (terraces, sheds side by side)
    low = collections.defaultdict(list)
    out = []
    for pc in pieces:
        if pc[4] or pc[1] > 0:
            out.append(pc)
        else:
            c = pc[0].centroid
            low[(int(pc[2] // JOIN_BAND), max(abs(c.x), abs(c.y)) > FAR_ZONE)].append(pc)
    joined = 0
    for (band, far_zone), pcs in low.items():
        gap = JOIN_GAP * (2 if far_zone else 1)
        u = unary_union([p[0].buffer(gap, join_style=2) for p in pcs])
        hs = np.array([p[2] for p in pcs]); ar = np.array([p[0].area for p in pcs])
        hmean = float((hs * ar).sum() / ar.sum())
        geoms = getattr(u, "geoms", [u])
        # each joined block keeps the area-weighted height of the buildings in it
        from shapely.strtree import STRtree
        tree = STRtree([p[0] for p in pcs])
        for gg in geoms:
            gg = gg.buffer(-gap, join_style=2)
            for g1 in getattr(gg, "geoms", [gg]):
                if g1.is_empty or g1.area < 40:
                    continue
                hit = tree.query(g1)
                if len(hit):
                    hm = float((hs[hit] * ar[hit]).sum() / ar[hit].sum())
                else:
                    hm = hmean
                out.append((g1, 0.0, hm, pcs[hit[0]][3] if len(hit) else 0, False))
        joined += len(pcs)
    print("low buildings", joined, "joined into", sum(1 for p in out if not p[4] and p[1] == 0))
    # mesh
    pos, nrm, col, uv, idx = [], [], [], [], []
    base_cache = {}
    nv = 0
    for poly, z0, top, look, tall in out:
        cpt = poly.centroid
        k_far = 2.0 if max(abs(cpt.x), abs(cpt.y)) > FAR_ZONE else 1.0
        poly = poly.simplify((0.5 if tall else LOW_SIMPLIFY) * k_far, preserve_topology=True)
        if poly.is_empty or poly.geom_type != "Polygon" or poly.area < 12:
            continue
        P = np.array(poly.exterior.coords)[:-1]
        if len(P) < 3:
            continue
        if np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1]) < 0:
            P = P[::-1]                        # anticlockwise in e/n
        # the ground floor at the lowest land under the outline (GroundModels' land.base), curve taken off
        q = np.vstack([P, P.mean(0)])
        key = (look, round(float(P[0, 0]), 1))
        y0 = base_cache.get(key)
        if y0 is None:
            y0 = float(np.nanmin(H.at(q[:, 0], q[:, 1], 5.0))) - 0.1
            base_cache[key] = y0
        x, zz = frame.xz(P[:, 0], P[:, 1])
        cxm, czm = float(x.mean()), float(zz.mean())
        y0c = y0 - float(drop(cxm, czm))
        ya, yb = y0c + z0, y0c + top
        if tall:
            pick = look % 100003
            glassy = (pick % 100) < (85 if top > 30 else 40)
            w = (TOWER_GLASS if glassy else TOWER_CONCRETE)[pick % 6]
            wall = (np.array(w) / 255.0, 1.0 if glassy else 0.5)
            roof = np.array((128, 128, 124)) / 255.0 if glassy else np.array(w) / 255.0 * 0.75
        else:
            wall = (np.array(LOW_WALLS[look % 5]) / 255.0, 0.0)
            ee, nn = P[:, 0], P[:, 1]
            rl = near.sample(np.r_[ee, P[:, 0].mean()], np.r_[nn, P[:, 1].mean()]) / 10000.0 * gain
            roof = srgb(np.median(rl, 0))
        run = 0.0
        k = len(P)
        for i in range(k):
            a, b = P[i], P[(i + 1) % k]
            side = float(np.hypot(*(b - a)))
            if side < 1e-3:
                continue
            ax, az = frame.xz(a[0], a[1]); bx, bz = frame.xz(b[0], b[1])
            o = np.array([b[1] - a[1], 0.0, b[0] - a[0]])   # outward in model x/z for anticlockwise e/n: (dn, 0, de)
            o /= np.linalg.norm(o)
            shade = wall[0] * (0.92 + 0.08 * abs(o[0]))
            quad = [(ax, ya, az, run, z0), (bx, ya, bz, run + side, z0), (bx, yb, bz, run + side, top), (ax, yb, az, run, top)]
            for vx, vy, vz, u, v in quad:
                pos.append((vx, vy, vz)); nrm.append(o); col.append((*shade, wall[1])); uv.append((u, v))
            idx += [nv, nv + 2, nv + 1, nv, nv + 3, nv + 2]
            nv += 4
            run += side
        tri = earcut.triangulate_float64(P.astype(np.float64), np.array([len(P)], np.uint32))
        for i in range(k):
            pos.append((float(x[i]), yb, float(zz[i]))); nrm.append((0.0, 1.0, 0.0)); col.append((*roof, 0.0)); uv.append((0.0, -1.0))
        t = np.asarray(tri).reshape(-1, 3)
        idx += (nv + t[:, [0, 2, 1]]).ravel().tolist()
        nv += k
    surf = {"name": "city_far", "pos": np.array(pos, np.float32), "nrm": np.array(nrm, np.float32),
            "col": np.array(col, np.float32), "uv": np.array(uv, np.float32), "idx": np.array(idx, np.uint32),
            "material": "city_towers"}
    return surf, {"buildings": dict(src), "pieces_drawn": len(out), "height_check": table.report}


# ---- glb ------------------------------------------------------------------------------------------

def write_glb(path, surfaces, images):
    J = {"asset": {"version": "2.0", "generator": "tools/grounds/backdrop/horizon/horizon.py"},
         "scene": 0, "scenes": [{"nodes": []}], "nodes": [], "meshes": [], "materials": [], "accessors": [],
         "bufferViews": [], "buffers": [], "images": [], "textures": [], "samplers": [{"magFilter": 9729, "minFilter": 9987}]}
    blob = bytearray()

    def view(data, target=None):
        while len(blob) % 4:
            blob.append(0)
        off = len(blob)
        blob.extend(data)
        bv = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target:
            bv["target"] = target
        J["bufferViews"].append(bv)
        return len(J["bufferViews"]) - 1

    def acc(arr, kind, comp=5126, target=34962, minmax=False):
        a = {"bufferView": view(arr.tobytes(), target), "componentType": comp, "count": int(arr.shape[0]), "type": kind}
        if minmax:
            a["min"] = arr.min(0).tolist(); a["max"] = arr.max(0).tolist()
        J["accessors"].append(a)
        return len(J["accessors"]) - 1

    tex_of = {}
    for name, png in images.items():
        J["images"].append({"bufferView": view(png), "mimeType": "image/png", "name": "horizon_" + name})
        J["textures"].append({"source": len(J["images"]) - 1, "sampler": 0})
        tex_of[name] = len(J["textures"]) - 1
    for s in surfaces:
        # every triangle faces the way its normals do (glTF: anticlockwise seen from the front)
        t = s["idx"].reshape(-1, 3).copy()
        p = s["pos"].astype(np.float64)
        fn = np.cross(p[t[:, 1]] - p[t[:, 0]], p[t[:, 2]] - p[t[:, 0]])
        back = (fn * s["nrm"][t[:, 0]]).sum(1) < 0
        t[back] = t[back][:, [0, 2, 1]]
        s["idx"] = t.ravel().astype(np.uint32)
        mat = {"name": s.get("material", "horizon_" + s["name"]),
               "pbrMetallicRoughness": {"metallicFactor": 0.0, "roughnessFactor": 1.0}}
        if "tex" in s:
            mat["pbrMetallicRoughness"]["baseColorTexture"] = {"index": tex_of[s["tex"]]}
        J["materials"].append(mat)
        mat_i = len(J["materials"]) - 1
        # cut into WEDGES round the ground, so the camera draws only the ones it faces (reduce.py does the same)
        c = p[t].mean(1)
        w = ((np.arctan2(c[:, 2], c[:, 0]) + math.pi) / (2 * math.pi) * WEDGES).astype(int) % WEDGES
        for k in range(WEDGES):
            tk = t[w == k]
            if not len(tk):
                continue
            used = np.unique(tk)
            remap = np.full(len(p), -1)
            remap[used] = np.arange(len(used))
            attrs = {"POSITION": acc(s["pos"][used], "VEC3", minmax=True), "NORMAL": acc(s["nrm"][used], "VEC3")}
            if "uv" in s:
                attrs["TEXCOORD_0"] = acc(s["uv"][used], "VEC2")
            if "col" in s:
                attrs["COLOR_0"] = acc(s["col"][used], "VEC4")
            ind = acc(remap[tk].ravel().astype(np.uint32), "SCALAR", comp=5125, target=34963)
            name = ("terrain_" if s["name"].startswith("land") else "") + s["name"] + "_%d" % k
            J["meshes"].append({"name": name, "primitives": [{"attributes": attrs, "indices": ind, "material": mat_i}]})
            J["nodes"].append({"name": name, "mesh": len(J["meshes"]) - 1})
            J["scenes"][0]["nodes"].append(len(J["nodes"]) - 1)
    while len(blob) % 4:
        blob.append(0)
    J["buffers"].append({"byteLength": len(blob)})
    js = json.dumps(J, separators=(",", ":")).encode()
    while len(js) % 4:
        js += b" "
    out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(blob))
    out += struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(blob), 0x004E4942) + bytes(blob)
    open(path, "wb").write(out)
    return len(out)


def build(slug, backdrop=None):
    frame = Frame(slug)
    H = Heights(slug, frame)
    part1 = backdrop or os.path.join(ROOT, "assets", "grounds", slug, slug + "_backdrop_part1.glb")
    G = reland.Glb(part1)
    wp = next(p for p in G.prims if p[0].startswith(reland.WATER))
    water_y = float(np.median(G.read(wp[1])[:, 1]))
    near, mid, far = S2(slug, "near"), S2(slug, "mid"), S2(slug, "far")
    gain = seam_gain(G, frame, near)
    land, land_rep = land_mesh(slug, frame, H, water_y, gain, near, mid, far)
    city_s, city_rep = city(slug, frame, H, gain, near)
    surfaces = land + [city_s]
    images = {"near": texture_png(near, gain), "mid": texture_png(mid, gain)}
    out = os.path.join(ROOT, "assets", "grounds", slug, slug + "_horizon.glb")
    size = write_glb(out, surfaces, images)
    tris = {s["name"]: int(len(s["idx"]) // 3) for s in surfaces}
    rep = {"ground": slug, "file": os.path.relpath(out, ROOT), "bytes": size, "triangles": tris,
           "triangles_total": int(sum(tris.values())), "vertices_total": int(sum(len(s["pos"]) for s in surfaces)),
           "draw_calls": len(surfaces) * WEDGES, "draw_calls_note": "each surface cut into WEDGES; a camera faces about a third", "textures": {k: "1024 x 1024" for k in images}, "water_y": round(water_y, 2),
           "seam_gain": gain.round(4).tolist(), "land": land_rep, "city": city_rep}
    json.dump(rep, open(work(slug, "horizon_report.json"), "w"), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    cmd, slug = sys.argv[1], sys.argv[2]
    {"fetch": fetch, "build": lambda s: build(s, sys.argv[3] if len(sys.argv) > 3 else None)}[cmd](slug)
