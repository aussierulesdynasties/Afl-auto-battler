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
TIER_M = 3.0         # m: a measured structure's parts with tops this close are one tier
CANOPY_CELL = 6.0    # m: the far canopy's cell (canopy())
CANOPY_TRIS = 70000  # its triangles after thinning (the old shards' count)
JOIN_GAP = 2.0        # m: across a lane or a gap between neighbours narrower than twice this, they are one block
LOW_SIMPLIFY = 3.0    # m: a low block's outline is kept to this
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
    fetch_water(slug, con)
    x, y = Transformer.from_crs(4326, "ESRI:54009", always_xy=True).transform(lon, lat)
    col, row = int((x + 18041000) // 1000000) + 1, int((9000000 - y) // 1000000) + 1
    z = work(slug, "ghsl.zip")
    urllib.request.urlretrieve(GHSL % (row, col), z)
    with zipfile.ZipFile(z) as f:
        name = next(n for n in f.namelist() if n.endswith(".tif"))
        open(work(slug, "ghsl.tif"), "wb").write(f.read(name))
    print("ghsl tile R%d C%d" % (row, col))


WATER_SUBTYPES = ("ocean", "water", "river", "lake", "reservoir", "canal", "pond", "human_made")
WATER_SKIP_CLASSES = ("swimming_pool", "fountain")


def fetch_water(slug, con=None):
    """Open water to LAND_OUT from Overture's base water (OpenStreetMap's, with the coast's ocean): the sea, the bay,
    the rivers, lakes and ponds, clipped to the horizon's square. Sentinel-2's own water flag (fmask) is not used: in
    the city it calls tower shadows water and missed half of Victoria Harbour (2026-11-27)."""
    if con is None:
        import duckdb
        con = duckdb.connect()
        con.execute("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial; SET enable_progress_bar=false;")
        con.execute("CREATE OR REPLACE SECRET anon (TYPE s3, PROVIDER config, KEY_ID '', SECRET '', REGION 'us-west-2')")
    g = ground(slug)
    lat, lon = g["lat"], g["lon"]
    d = LAND_OUT * 1.05
    dx, dy = d / (R_EARTH * math.radians(1) * math.cos(math.radians(lat))), d / (R_EARTH * math.radians(1))
    env = "ST_MakeEnvelope(%f, %f, %f, %f)" % (lon - dx, lat - dy, lon + dx, lat + dy)
    q = ("select subtype, class, ST_AsText(ST_Intersection(geometry, %s)) as wkt from read_parquet('%s', hive_partitioning=1) "
         "where bbox.xmin < %f and bbox.xmax > %f and bbox.ymin < %f and bbox.ymax > %f "
         "and ST_GeometryType(geometry) in ('POLYGON', 'MULTIPOLYGON') and subtype in (%s) and class not in (%s)") % (
        env, OVERTURE.replace("theme=buildings", "theme=base") % "water", lon + dx, lon - dx, lat + dy, lat - dy,
        ", ".join("'%s'" % k for k in WATER_SUBTYPES), ", ".join("'%s'" % k for k in WATER_SKIP_CLASSES))
    rows = [{"subtype": r[0], "class": r[1], "wkt": r[2]} for r in con.execute(q).fetchall() if r[2] and "EMPTY" not in r[2]]
    json.dump(rows, open(work(slug, "overture_water.json"), "w"))
    print("water polygons", len(rows))


def water_grid(slug, frame, half, step):
    """The share of each cell of a north-up grid (half size, cell, metres) that is open water (fetch_water), or None."""
    path = work(slug, "overture_water.json")
    if not os.path.exists(path):
        return None
    cache = work(slug, "water_%d_%d.npy" % (half, step))
    if os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(path):
        return np.load(cache)
    from rasterio import features
    from rasterio.transform import from_origin
    from shapely import wkt
    from shapely.geometry import Polygon, MultiPolygon
    shapes = []
    for r in json.load(open(path)):
        geom = wkt.loads(r["wkt"])
        for gg in getattr(geom, "geoms", [geom]):
            if gg.geom_type != "Polygon" or gg.is_empty:
                continue
            ex = np.array(gg.exterior.coords)
            e, n = frame.en(ex[:, 0], ex[:, 1])
            holes = []
            for ring in gg.interiors:
                hr = np.array(ring.coords)
                he, hn = frame.en(hr[:, 0], hr[:, 1])
                holes.append(np.c_[he, hn])
            shapes.append(Polygon(np.c_[e, n], holes))
    k = 4   # supersampling: a cell's share of water
    n = int(round(2 * half / step)) * k
    grid = features.rasterize([(sh, 1) for sh in shapes], out_shape=(n, n),
                              transform=from_origin(-half, half, step / k, step / k), dtype="uint8", all_touched=False)
    W = grid.reshape(n // k, k, n // k, k).mean((1, 3)).astype(np.float32)
    np.save(cache, W)
    return W


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
    def __init__(self, slug, name, frame=None):
        self.M = np.load(work(slug, name + ".npy"))
        self.W = np.load(work(slug, name + "_water.npy"))
        meta = json.load(open(work(slug, name + ".json")))
        self.half, self.step = meta["half_m"], meta["m_per_px"]
        mapped = water_grid(slug, frame, self.half, self.step) if frame is not None else None
        if mapped is not None:
            self.W = mapped   # the mapped water (fetch_water), not Sentinel-2's fmask
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
    I = glb.read(pr["indices"]).reshape(-1, 3).astype(np.int64)
    blk = 60.0
    xs = np.arange(-1440, 1441, blk)
    X, Z = np.meshgrid(xs, xs)
    X, Z = X.ravel(), Z.ravel()
    h, w = img.shape[:2]
    lin_img = lin_of(img)
    bake = []
    k = int(blk / (3000 / w) / 2)
    # each block's texture coordinates from the ground triangle under it (the ground's UVs are its own, not one plan
    # projection); a block with no ground under it (inside the backdrop's cut) has no bake
    from shapely import points
    from shapely.geometry import Polygon
    from shapely.strtree import STRtree
    T = P[I][:, :, [0, 2]]
    tree = STRtree([Polygon(t) for t in T])
    pi, ti = tree.query(points(X, Z), predicate="intersects")
    uv_at = {}
    for p_, t_ in zip(pi, ti):
        if p_ in uv_at:
            continue
        a_, b_, c_ = T[t_]
        den = (b_[1] - c_[1]) * (a_[0] - c_[0]) + (c_[0] - b_[0]) * (a_[1] - c_[1])
        if abs(den) < 1e-9:
            continue
        l1 = ((b_[1] - c_[1]) * (X[p_] - c_[0]) + (c_[0] - b_[0]) * (Z[p_] - c_[1])) / den
        l2 = ((c_[1] - a_[1]) * (X[p_] - c_[0]) + (a_[0] - c_[0]) * (Z[p_] - c_[1])) / den
        uv_at[p_] = np.array([l1, l2, 1 - l1 - l2]) @ UV[I[t_]]
    for i in range(len(X)):
        if i not in uv_at:
            bake.append(np.full(3, np.nan))
            continue
        u, v = uv_at[i]
        c, r = int(u * w), int(v * h)
        if not (0 <= c < w and 0 <= r < h):
            bake.append(np.full(3, np.nan))
            continue
        bake.append(lin_img[max(0, r - k):r + k, max(0, c - k):c + k].reshape(-1, 3).mean(0))
    bake = np.array(bake)
    e, n = frame.e_n_of(X, Z)
    s2 = near.sample(e, n, blur_m=blk) / 10000.0
    wat = near.sample(e, n, near.W, blur_m=blk) > 0.5
    ok = ~wat & np.isfinite(bake).all(1)
    gain = np.array([(bake[ok, c] * s2[ok, c]).sum() / (s2[ok, c] ** 2).sum() for c in range(3)])
    resid = np.abs(s2[ok] * gain - bake[ok]).mean(0)
    print("seam colour gain", gain.round(3), "mean miss (linear)", resid.round(4), "blocks", int(ok.sum()))
    # open water takes the backdrop's own water (its ground paints the harbour and the river), not the land's gain:
    # Sentinel-2's water times the land's gain read a pale grey-green against Google Earth's navy (2026-11-27)
    wb = wat & np.isfinite(bake).all(1) & (np.hypot(X, Z) > 1060)   # where the backdrop's ground is (cut inside 1,024 m)
    water = np.median(bake[wb], 0) if wb.sum() >= 4 else None
    print("backdrop water (linear)", None if water is None else water.round(4), "blocks", int(wb.sum()))
    return gain, water


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


def land_mesh(slug, frame, H, water_y, gain, near, mid, far, water=None):
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
    if water is not None:
        wf = np.clip(W.ravel(), 0, 1)[:, None]
        col = col * (1 - wf) + water * wf
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


def texture_png(src, gain, water=None, size=1024):
    """The Sentinel-2 grid as an sRGB png (the material's albedo), north up; open water the backdrop's own."""
    from PIL import Image
    M = src.M / 10000.0 * gain
    if water is not None:
        w = np.clip(src.W, 0, 1)[..., None]
        M = M * (1 - w) + water * w
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


def com_parts(slug, frame, local):
    """The City of Melbourne's 2023 building footprints (CC BY), each a stacked part of a structure, heights AHD
    (measured from its aerial survey): every part of a structure that stands in the ring. [] where it has none."""
    path = work(slug, "com", "2023-building-footprints.geojson")
    if not os.path.exists(path):
        return []
    from shapely.geometry import shape
    out = []
    for f in json.load(open(path))["features"]:
        p = f["properties"]
        if not f["geometry"] or p.get("footprint_type") != "Structure" or p.get("footprint_max_elevation") is None:
            continue
        for poly in local(shape(f["geometry"])):
            c = poly.centroid
            x, z = frame.xz(c.x, c.y)
            if max(abs(float(x)), abs(float(z))) < INNER or max(abs(c.x), abs(c.y)) > CITY_OUT or poly.area < 4:
                continue
            out.append({"poly": poly, "sid": p["structure_id"], "fmin": float(p["footprint_min_elevation"]),
                        "fmax": float(p["footprint_max_elevation"]), "smin": float(p["structure_min_elevation"])})
    return out


def photomesh_colours(slug, com):
    """Each measured part's wall and roof colour (sRGB 0-1) from the council's photomesh (photomesh.py): the walls
    from the photographed wall faces round the part and between its floor and top, sunlit (north-facing) ones first,
    the roof from its upward faces near its top; a part with too few faces takes its structure's."""
    path = work(slug, "photomesh.npz")
    if not os.path.exists(path):
        return [None] * len(com), {"photomesh": "not fetched"}
    from shapely import points
    from shapely.strtree import STRtree
    D = np.load(path)
    mid, nrm, col, area = D["mid"], D["nrm"], D["col"].astype(np.float64), D["area"]
    tree = STRtree([c["poly"].buffer(1.5) for c in com])
    pi, gi = tree.query(points(mid[:, 0], mid[:, 1]), predicate="within")
    zc = mid[pi, 2]
    fmin = np.array([c["fmin"] for c in com])[gi]
    fmax = np.array([c["fmax"] for c in com])[gi]
    inz = (zc > fmin - 1.0) & (zc < fmax + 1.0)
    pi, gi, zc, fmax = pi[inz], gi[inz], zc[inz], fmax[inz]
    nz = nrm[pi, 2]
    wall_m = np.abs(nz) < 0.35
    roof_m = (nz > 0.75) & (zc > fmax - 2.5)
    lit = nrm[pi, 1] > 0.2

    def med(sel):
        if sel.sum() < 4:
            return None
        return np.median(col[pi[sel]], 0) / 255.0

    by_g = collections.defaultdict(list)
    for k, g in enumerate(gi):
        by_g[g].append(k)
    walls, roofs = [None] * len(com), [None] * len(com)
    for g, ks in by_g.items():
        ks = np.array(ks)
        w = np.zeros(len(pi), bool); w[ks] = True
        walls[g] = med(w & wall_m & lit)
        if walls[g] is None:
            walls[g] = med(w & wall_m)
        roofs[g] = med(w & roof_m)
    # a part with too few faces of its own: its structure's
    sw, sr = collections.defaultdict(list), collections.defaultdict(list)
    for c, wv, rv in zip(com, walls, roofs):
        if wv is not None:
            sw[c["sid"]].append(wv)
        if rv is not None:
            sr[c["sid"]].append(rv)
    out, rep = [], collections.Counter()
    for c, wv, rv in zip(com, walls, roofs):
        wv = wv if wv is not None else (np.median(sw[c["sid"]], 0) if sw[c["sid"]] else None)
        rv = rv if rv is not None else (np.median(sr[c["sid"]], 0) if sr[c["sid"]] else wv)
        wv = wv if wv is not None else rv
        out.append(None if wv is None else (wv, rv))
        rep["from its own photographed faces" if wv is not None else "from its photographed neighbours"] += 1
    # a part too small for the photomesh's 5 m faces (a shed, a narrow terrace): the median of the 8 nearest
    # photographed parts, the street's own colours
    from scipy.spatial import cKDTree
    have = [i for i, o in enumerate(out) if o is not None]
    if have:
        cen = np.array([[c["poly"].centroid.x, c["poly"].centroid.y] for c in com])
        kt = cKDTree(cen[have])
        for i, o in enumerate(out):
            if o is None:
                _, nb = kt.query(cen[i], k=min(8, len(have)))
                nb = np.atleast_1d(nb)
                out[i] = (np.median([out[have[j]][0] for j in nb], 0), np.median([out[have[j]][1] for j in nb], 0))
    return out, dict(rep)


def com_tiers(com, colours):
    """A measured structure's parts drawn as few tiers: parts whose tops are within TIER_M of each other (twice that
    past FAR_ZONE) are one outline from the lowest floor among them, at their area-weighted top and colours. The
    council maps every plant room and parapet as a part; 2 km out they are a pixel, and a tier keeps the skyline."""
    from shapely.ops import unary_union
    by = collections.defaultdict(list)
    for c, cl in zip(com, colours):
        by[c["sid"]].append((c, cl))
    out = []
    for sid, ps in by.items():
        ps.sort(key=lambda t: -t[0]["fmax"])
        c0 = ps[0][0]["poly"].centroid
        tier = TIER_M * (2 if max(abs(c0.x), abs(c0.y)) > FAR_ZONE else 1)
        groups = []
        for t in ps:
            if groups and groups[-1][0][0]["fmax"] - t[0]["fmax"] <= tier:
                groups[-1].append(t)
            else:
                groups.append([t])
        for g in groups:
            ar = np.array([t[0]["poly"].area for t in g])
            u = unary_union([t[0]["poly"].buffer(0.5, join_style=2) for t in g]).buffer(-0.5, join_style=2)
            top = float((np.array([t[0]["fmax"] for t in g]) * ar).sum() / ar.sum()) - g[0][0]["smin"]
            z0 = min(t[0]["fmin"] for t in g) - g[0][0]["smin"]
            rc = [(t[1], a) for t, a in zip(g, ar) if t[1] is not None]
            cl = None
            if rc:
                wa = sum(a for _, a in rc)
                cl = (sum(c[0] * a for c, a in rc) / wa, sum(c[1] * a for c, a in rc) / wa)
            for pl in getattr(u, "geoms", [u]):
                if pl.geom_type == "Polygon" and not pl.is_empty:
                    out.append((pl, z0, top, sid, cl, len(groups) == 1))
    return out


def canopy(slug, frame, H, com):
    """The trees' real canopy from the photomesh's green faces (photomesh.py), where they stand at least 2 m over the
    land and clear of every measured building, in the ring between the backdrop's square and CITY_OUT."""
    path = work(slug, "photomesh.npz")
    if not os.path.exists(path):
        return None
    D = np.load(path)
    T = D["veg_tri"].astype(np.float64)
    C = D["veg_col"]
    if not len(T):
        return None
    c = T.mean(1)
    x, z = frame.xz(c[:, 0], c[:, 1])
    keep = (np.maximum(np.abs(x), np.abs(z)) > INNER) & (np.maximum(np.abs(c[:, 0]), np.abs(c[:, 1])) < CITY_OUT)
    if com:
        from shapely import points
        from shapely.strtree import STRtree
        tree = STRtree([p["poly"].buffer(2.0) for p in com])
        hit = np.zeros(len(T), bool)
        pi, _ = tree.query(points(c[:, 0], c[:, 1]), predicate="within")
        hit[pi] = True
        keep &= ~hit
    land = H.at(c[:, 0], c[:, 1], 5.0)
    ahd = lambda zz: frame.floor + zz - H.datum                                   # noqa: E731
    keep &= ahd(c[:, 2]) > land + 2.0
    T, C = T[keep], C[keep]
    # The crowns as solid masses, not the photomesh's own faces: thinned, those were loose shards with sky between
    # them (Westgate Park from the West Gate Bridge, 2026-11-27, where the real park is solid bush). Each CANOPY_CELL
    # cell the faces fall in takes their highest top over the land and their mean colour; cells one apart are closed
    # into one mass; each cell is drawn as a low pyramid (its corners shared with its neighbours, its middle at the
    # top), so a lone tree is a peak and a park a canopy with its edge sloping to the ground.
    from scipy import ndimage
    c = T.mean(1)
    top = ahd(c[:, 2]) - land[keep]
    e0, n0 = c[:, 0].min() - CANOPY_CELL, c[:, 1].min() - CANOPY_CELL
    ci = ((c[:, 0] - e0) // CANOPY_CELL).astype(int)
    cj = ((c[:, 1] - n0) // CANOPY_CELL).astype(int)
    ni, nj = ci.max() + 2, cj.max() + 2
    hgt = np.zeros((ni, nj))
    np.maximum.at(hgt, (ci, cj), top)
    lc = lin_of(C.astype(np.float64) / 255.0)
    csum = np.zeros((ni, nj, 3))
    cnt = np.zeros((ni, nj))
    np.add.at(csum, (ci, cj), lc)
    np.add.at(cnt, (ci, cj), 1)
    seen = cnt > 0
    mask = ndimage.binary_closing(seen, np.ones((3, 3), bool)) | seen
    # a closed-in cell takes its nearest photographed cell's height and colour
    _, (ii, jj) = ndimage.distance_transform_edt(~seen, return_indices=True)
    hgt = np.where(seen, hgt, hgt[ii, jj])
    col = np.where(seen[..., None], csum / np.maximum(cnt, 1)[..., None], (csum / np.maximum(cnt, 1)[..., None])[ii, jj])
    hgt = np.minimum(hgt, 40.0)
    I, J = np.nonzero(mask)
    m = len(I)
    # corners: (ni + 1) x (nj + 1), each at the land plus the mean top of the masked cells round it (the others count 0)
    mk = np.pad(mask.astype(float), 1)
    hp = np.pad(hgt * mask, 1)
    cp = np.pad(col * mask[..., None], ((1, 1), (1, 1), (0, 0)))
    cn = mk[:-1, :-1] + mk[1:, :-1] + mk[:-1, 1:] + mk[1:, 1:]
    corner_h = (hp[:-1, :-1] + hp[1:, :-1] + hp[:-1, 1:] + hp[1:, 1:]) / 4
    corner_c = (cp[:-1, :-1] + cp[1:, :-1] + cp[:-1, 1:] + cp[1:, 1:]) / np.maximum(cn, 1)[..., None]
    used = np.zeros(corner_h.shape, bool)
    for di in (0, 1):
        for dj in (0, 1):
            used[I + di, J + dj] = True
    ui, uj = np.nonzero(used)
    vid = -np.ones(corner_h.shape, np.int64)
    vid[ui, uj] = np.arange(len(ui))
    ce, cnn = e0 + ui * CANOPY_CELL, n0 + uj * CANOPY_CELL
    me, mn = e0 + (I + 0.5) * CANOPY_CELL, n0 + (J + 0.5) * CANOPY_CELL
    E = np.r_[ce, me]
    N = np.r_[cnn, mn]
    L = H.at(E, N, CANOPY_CELL)
    UP = np.r_[corner_h[ui, uj], hgt[I, J]]
    X, Z = frame.xz(E, N)
    V = np.stack([X, L + UP - drop(X, Z), Z], 1)
    VC = np.r_[corner_c[ui, uj], col[I, J]]
    mid = len(ui) + np.arange(m)
    a0, a1, a2, a3 = vid[I, J], vid[I + 1, J], vid[I + 1, J + 1], vid[I, J + 1]
    F = np.concatenate([np.c_[a0, a1, mid], np.c_[a1, a2, mid], np.c_[a2, a3, mid], np.c_[a3, a0, mid]])
    # faces wound up (+y): e and n map to x and -z
    import pyfqmr
    from scipy.spatial import cKDTree
    s = pyfqmr.Simplify()
    s.setMesh(V, F.astype(np.int32))
    s.simplify_mesh(target_count=CANOPY_TRIS, aggressiveness=7, preserve_border=False, verbose=False)
    V2, F2, _ = s.getMesh()
    V2 = np.asarray(V2, np.float64); F2 = np.asarray(F2, np.int64)
    _, nb = cKDTree(V).query(V2, k=1)
    colv = VC[nb]
    fn = np.cross(V2[F2[:, 1]] - V2[F2[:, 0]], V2[F2[:, 2]] - V2[F2[:, 0]])
    flip = fn[:, 1] < 0
    F2[flip] = F2[flip][:, ::-1]
    fn[flip] *= -1
    vn = np.zeros_like(V2)
    for k in range(3):
        np.add.at(vn, F2[:, k], fn)
    vn /= np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-9)
    print("canopy faces", len(T), "in", int(seen.sum()), "cells,", m, "closed; drawn in", len(F2), "triangles")
    return {"name": "trees_far", "pos": V2.astype(np.float32), "nrm": vn.astype(np.float32),
            "col": np.c_[colv, np.ones(len(colv))].astype(np.float32),
            "idx": F2.ravel().astype(np.uint32), "material": "horizon_trees"}


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
    pieces = []   # (polygon in e/n, base above ground, top above ground, look id, tall?, (wall, roof) or None)
    src = collections.Counter()
    com = com_parts(slug, frame, local)
    from shapely.strtree import STRtree
    com_tree = STRtree([c["poly"] for c in com]) if com else None
    if com:
        colours, crep = photomesh_colours(slug, com)
        for poly, z0, top, sid, cl, alone in com_tiers(com, colours):
            alone_low = alone and z0 < 0.5 and top < JOIN_BELOW
            pieces.append((poly, 0.0 if alone_low else z0, top, ("com", sid), not alone_low, cl))
        src["City of Melbourne measured parts"] = len(com)
        print("photomesh colours:", crep)
    for r in rows:
        if r.get("is_underground") in (True, "True"):
            continue
        c = r["_geom"].centroid
        e, n = frame.en(c.x, c.y)
        x, z = frame.xz(e, n)
        if max(abs(x), abs(z)) < INNER or max(abs(e), abs(n)) > CITY_OUT:
            continue
        look = zlib.crc32(r["id"].encode()) & 0x7FFFFFFF
        if com_tree is not None and any(len(com_tree.query(pl, predicate="intersects")) for pl in local(r["_geom"])):
            src["left to the City of Melbourne's"] += 1
            continue
        ps = by_parts.get(r["id"])
        if ps:
            for p in ps:
                top = mapped_height(p) or r["_h"]
                if top is None:
                    continue
                for poly in local(wkt.loads(p["wkt"])):
                    pieces.append((poly, part_base(p), top, look, True, None))
            src["mapped parts"] += 1
            continue
        h = r["_h"]
        src["mapped" if h is not None else "estimated"] += 1
        if h is None:
            h = table.height(r)
        if h < 2.0:
            continue
        for poly in local(r["_geom"]):
            pieces.append((poly, 0.0, h, look, h >= JOIN_BELOW, None))
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
                # a block of photographed buildings keeps their area-weighted walls and roof
                rc = [(pcs[i][5], ar[i]) for i in hit if pcs[i][5] is not None]
                real = None
                if rc and sum(a for _, a in rc) > 0.5 * ar[hit].sum():
                    wa = sum(a for _, a in rc)
                    real = (sum(c[0] * a for c, a in rc) / wa, sum(c[1] * a for c, a in rc) / wa)
                lk = pcs[hit[0]][3] if len(hit) else 0
                out.append((g1, 0.0, hm, lk if isinstance(lk, int) else zlib.crc32(str(lk).encode()) & 0x7FFFFFFF,
                            False, real))
        joined += len(pcs)
    print("low buildings", joined, "joined into", sum(1 for p in out if not p[4] and p[1] == 0))
    # mesh
    pos, nrm, col, uv, idx = [], [], [], [], []
    base_cache = {}
    kind_tris = collections.Counter()
    nv = 0
    outline = collections.defaultdict(list)     # a measured structure's parts, for one ground floor under them all
    for pc in out:
        if isinstance(pc[3], tuple):
            outline[pc[3]].append(np.array(pc[0].exterior.coords))
    for poly, z0, top, look, tall, real in out:
        cpt = poly.centroid
        k_far = 2.0 if max(abs(cpt.x), abs(cpt.y)) > FAR_ZONE else 1.0
        poly = poly.simplify((1.0 if tall else LOW_SIMPLIFY) * k_far, preserve_topology=True)
        if poly.is_empty or poly.geom_type != "Polygon" or poly.area < 12:
            continue
        P = np.array(poly.exterior.coords)[:-1]
        if len(P) < 3:
            continue
        if np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1]) < 0:
            P = P[::-1]                        # anticlockwise in e/n
        # the ground floor at the lowest land under the outline (GroundModels' land.base), curve taken off
        q = np.vstack(outline[look]) if isinstance(look, tuple) else np.vstack([P, P.mean(0)])
        key = look if isinstance(look, tuple) else (look, round(float(P[0, 0]), 1))
        y0 = base_cache.get(key)
        if y0 is None:
            y0 = float(np.nanmin(H.at(q[:, 0], q[:, 1], 5.0))) - 0.1
            base_cache[key] = y0
        x, zz = frame.xz(P[:, 0], P[:, 1])
        cxm, czm = float(x.mean()), float(zz.mean())
        y0c = y0 - float(drop(cxm, czm))
        ya, yb = y0c + z0, y0c + top
        if real is not None:
            # its own photographed walls and roof (photomesh_colours), plain: the photo already holds the glass's sheen
            wall = (real[0], 0.0)
            roof = real[1]
        elif tall:
            pick = (look if isinstance(look, int) else zlib.crc32(str(look).encode())) % 100003
            glassy = (pick % 100) < (85 if top > 30 else 40)
            w = (TOWER_GLASS if glassy else TOWER_CONCRETE)[pick % 6]
            wall = (np.array(w) / 255.0, 1.0 if glassy else 0.5)
            roof = np.array((128, 128, 124)) / 255.0 if glassy else np.array(w) / 255.0 * 0.75
        else:
            wall = (np.array(LOW_WALLS[(look if isinstance(look, int) else 0) % 5]) / 255.0, 0.0)
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
        kind_tris[("measured part" if isinstance(look, tuple) else "tall" if tall else "low block")] += 3 * k - 2
        for i in range(k):
            pos.append((float(x[i]), yb, float(zz[i]))); nrm.append((0.0, 1.0, 0.0)); col.append((*roof, 0.0)); uv.append((0.0, -1.0))
        t = np.asarray(tri).reshape(-1, 3)
        idx += (nv + t[:, [0, 2, 1]]).ravel().tolist()
        nv += k
    surf = {"name": "city_far", "pos": np.array(pos, np.float32), "nrm": np.array(nrm, np.float32),
            "col": np.array(col, np.float32), "uv": np.array(uv, np.float32), "idx": np.array(idx, np.uint32),
            "material": "city_towers"}
    return surf, {"buildings": dict(src), "pieces_drawn": len(out), "triangles_by_kind": dict(kind_tris), "height_check": table.report}


def _local_poly(frame, g):
    from shapely.geometry import Polygon
    lon, lat = np.array(g.exterior.coords).T
    e, n = frame.en(lon, lat)
    return Polygon(np.c_[e, n]).buffer(0)


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
    if not os.path.exists(work(slug, "overture_water.json")):
        fetch_water(slug)
    near, mid, far = S2(slug, "near", frame), S2(slug, "mid", frame), S2(slug, "far", frame)
    gain, water = seam_gain(G, frame, near)
    land, land_rep = land_mesh(slug, frame, H, water_y, gain, near, mid, far, water)
    city_s, city_rep = city(slug, frame, H, gain, near)
    trees = canopy(slug, frame, H, com_parts(slug, frame, lambda g: [_local_poly(frame, gg) for gg in getattr(g, "geoms", [g])]))
    surfaces = land + [city_s] + ([trees] if trees is not None else [])
    images = {"near": texture_png(near, gain, water), "mid": texture_png(mid, gain, water)}
    out = os.path.join(ROOT, "assets", "grounds", slug, slug + "_horizon.glb")
    size = write_glb(out, surfaces, images)
    tris = {s["name"]: int(len(s["idx"]) // 3) for s in surfaces}
    rep = {"ground": slug, "file": os.path.relpath(out, ROOT), "bytes": size, "triangles": tris,
           "triangles_total": int(sum(tris.values())), "vertices_total": int(sum(len(s["pos"]) for s in surfaces)),
           "draw_calls": len(surfaces) * WEDGES, "draw_calls_note": "each surface cut into WEDGES; a camera faces about a third", "textures": {k: "1024 x 1024" for k in images}, "water_y": round(water_y, 2),
           "seam_gain": gain.round(4).tolist(),
           "water_colour_linear": None if water is None else water.round(4).tolist(), "land": land_rep, "city": city_rep}
    json.dump(rep, open(work(slug, "horizon_report.json"), "w"), indent=1)
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    cmd, slug = sys.argv[1], sys.argv[2]
    {"fetch": fetch, "build": lambda s: build(s, sys.argv[3] if len(sys.argv) > 3 else None)}[cmd](slug)
