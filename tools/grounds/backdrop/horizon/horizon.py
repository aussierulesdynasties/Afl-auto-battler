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
import glob
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
SQUARE_FADE = 150.0  # m: the land past the backdrop's square fades from its ground's colour to Sentinel-2 (square_fade)
CITY_OUT = 4096.0
LEVEL_M, LEVEL_BASE = 3.4, 1.0   # prep.py's storey height
JOIN_BELOW = 20.0     # low buildings of one height band that touch are joined
JOIN_BAND = 3.0
TIER_M = 6.0         # m: a measured structure's parts with tops this close are one tier (3 m drew 168k
                     # triangles of plant rooms and parapets 1.5 km out; 6 m keeps the skyline at a third of that)
CANOPY_CELL = 8.0    # m: the far canopy's cell (canopy()); 6 m cells thinned to CANOPY_TRIS left big facets and spikes
CANOPY_TRIS = 70000  # its top's triangles after thinning (its border is kept whole, so Marvel's stops at about 92k)
CANOPY_MIN_UP = 2.5  # m: a photomesh face this far over the land (and no building) can be a crown
CANOPY_SHARE = 0.25  # a cell is a tree where at least this share of its faces are crowns (canopy())
CANOPY_MIN_CELLS = 3  # a mass of fewer cells is a pole or a sign, not a tree
CANOPY_WALL_SHADE = 0.8  # a crown's side under the canopy's top: its own shade
CANOPY_OUTLINE_PASSES = 4  # smoothing passes over the canopy's outline (8 m cells' stairs into curves)
CANOPY_RIM_DROP = 0.8   # the outline's top, as a share of the mass's height there
CANOPY_WALL_TOL = 1.5    # m: a crown's side is drawn straight where the top's edge strays less than this from a line
# The canopy's colour (sRGB), its median brought to this, each cell keeping its own shade round it: the photomesh's
# own faces (2020, sunlit, with the sky's haze in them) drew the far bush pale grey-green, near white, where the
# real bush is dark (review, 2026-11-28). Marvel's is measured from the West Gate Bridge photo (March 2026, Westgate
# Park's canopy, its median over 145,000 pixels).
CANOPY_TARGET = {"marvel": (41, 60, 44)}
JOIN_GAP = 2.0        # m: across a lane or a gap between neighbours narrower than twice this, they are one block
LOW_SIMPLIFY = 6.0    # m: a low block's outline is kept to this (a pixel at 1.5 km in a phone's picture is ~2 m)
TALL_SIMPLIFY = 2.0   # m: a tall building's or a measured tier's outline is kept to this
MIN_AREA = 40.0       # m2: a smaller outline is not drawn (twice this past FAR_ZONE)
FAR_HOUSES_BELOW = 8.0  # m: past FAR_ZONE a low block under this (houses, one-storey sheds) is left to the land's
                        # own photo: a pixel high from the orbit, and 40% of the far city's triangles
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
# The near water sheet starts where the surrounds' painted water ends (GroundModels: SURROUNDS outer plus its skirt,
# reland.surrounds_outer), on FIT's centre, and its inner edge dives under the ring by NEAR_WATER_DIVE: the ring's
# water lies under the backdrop's (Marvel: 0.55 m) and its skirt drops away, so the orbit saw the sky through the
# step as a thin white line along the join (review, 2026-11-28).
NEAR_WATER_DIVE = (6.0, 1.0)   # m: inward from the sheet's edge, and down under the backdrop's water
NEAR_WATER_STEP = 1.0      # m: the near water sheet's tracing grid (near_water())
NEAR_WATER_LIFT = 0.3      # m: the sheet over the painted water, clear of it at the orbit's distance


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


def seam_gain(glb, frame, near, slug):
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
    m_per_texel = (P[:, 0].max() - P[:, 0].min()) / max(UV[:, 0].max() - UV[:, 0].min(), 1e-9) / w
    k = int(blk / m_per_texel / 2)
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
    cx, cz = reland.fit(slug)[:2]
    outer = reland.surrounds_outer(slug)[0]
    # where the backdrop's ground is (it is cut inside the ring's outer edge), a block clear of the cut
    wb = wat & np.isfinite(bake).all(1) & (np.hypot(X - cx, Z - cz) > outer + blk / 2 + 6)
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


def square_fade(src, frame, part1, gain, band=SQUARE_FADE):
    """A copy of the near Sentinel-2 grid whose land just outside the backdrop's square takes the colour of the
    backdrop's own ground at the square's edge (its bake, near_bake.py), fading to Sentinel-2 over band metres: from
    above, the square edge was a hard line between two maps (PC check, 28 Nov)."""
    import copy
    sys.path.insert(0, os.path.join(HERE, ".."))
    from near_bake import _near_ground, _lin
    from scipy.ndimage import uniform_filter
    img, cu, cv = _near_ground(part1)
    m_px = 1.0 / max(abs(cu[0]), 1e-12) / img.shape[1]
    blur = uniform_filter(_lin(img), (int(40 / m_px), int(40 / m_px), 1), mode="nearest")   # 40 m: no streaks outward
    out = copy.copy(src)
    nr, nc = src.M.shape[:2]
    rr, cc = np.mgrid[0:nr, 0:nc]
    n = src.half - (rr + 0.5) * src.step
    e = (cc + 0.5) * src.step - src.half
    x, z = frame.xz(e, n)
    d = np.maximum(np.abs(x), np.abs(z))
    w = np.clip(1.0 - (d - INNER) / band, 0.0, 1.0)
    sel = w > 0
    xc = np.clip(x[sel], -(INNER - 30), INNER - 30)
    zc = np.clip(z[sel], -(INNER - 30), INNER - 30)
    u = cu[0] * xc + cu[1] * zc + cu[2]
    v = cv[0] * xc + cv[1] * zc + cv[2]
    h, wd = img.shape[:2]
    edge = blur[np.clip((v * h).astype(int), 0, h - 1), np.clip((u * wd).astype(int), 0, wd - 1)]
    M = src.M.copy()
    M[sel] = M[sel] * (1 - w[sel, None]) + (edge / np.maximum(gain, 1e-6) * 10000.0) * w[sel, None]
    out.M = M
    return out


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
    """The trees' real canopy from the council's photomesh (photomesh.py) in the ring between the backdrop's square and
    CITY_OUT: where its faces stand at least CANOPY_MIN_UP over the land, clear of every building, as solid masses.

    Which cells are trees: a cell holds a tree where the photomesh's green faces stand over the land (veg_tri), or
    where a good share of all its faces stand CANOPY_MIN_UP up, face upward, have a crown's colour (greener than blue,
    or deep shade) and lie off every building footprint (City of Melbourne and Overture). The green faces alone took
    only the sunlit crowns: the PC check of 2026-11-28 drew Westgate Park as half-bare mounds against the photo's
    near-continuous bush.

    How they are drawn: each cell's top is its crowns' height over the land (median then softly blurred); the top's
    corners take the mean of the tree cells round them only, so a mass keeps its height to its edge; its edge drops
    to the land as a wall (a crown's side). The old corners counted bare cells as 0 and sloped each mass to the
    ground, so from the West Gate Bridge (2 to 4 km, a degree above it) a park read as low tents with bare ground
    between them, where real crowns hide what lies behind them."""
    path = work(slug, "photomesh.npz")
    if not os.path.exists(path):
        return None
    from scipy import ndimage
    from shapely import points
    from shapely.strtree import STRtree
    D = np.load(path)
    ahd = lambda zz: frame.floor + zz - H.datum                                   # noqa: E731

    def ring(e, n):
        x, z = frame.xz(e, n)
        return (np.maximum(np.abs(x), np.abs(z)) > INNER) & (np.maximum(np.abs(e), np.abs(n)) < CITY_OUT)

    blds = [p["poly"].buffer(2.0) for p in com] + [g.buffer(2.0) for g in _overture_footprints(slug, frame)]
    tree = STRtree(blds) if blds else None

    def off_buildings(e, n):
        ok = np.ones(len(e), bool)
        if tree is not None:
            pi, _ = tree.query(points(e, n), predicate="within")
            ok[pi] = False
        return ok
    # the green faces (the sunlit crowns), as before
    T = D["veg_tri"].astype(np.float64)
    vc = T.mean(1)
    keep = ring(vc[:, 0], vc[:, 1])
    vc, VC = vc[keep], D["veg_col"][keep]
    keep = off_buildings(vc[:, 0], vc[:, 1])
    vc, VC = vc[keep], VC[keep]
    vland = H.at(vc[:, 0], vc[:, 1], 5.0)
    vtop = ahd(vc[:, 2]) - vland
    keep = vtop > 2.0
    vc, VC, vtop = vc[keep], VC[keep], vtop[keep]
    # every face: a crown in shade is no green face, but it stands up off the land and is no roof
    M = D["mid"].astype(np.float64)
    keep = ring(M[:, 0], M[:, 1])
    M, MN, MC = M[keep], D["nrm"][keep], D["col"][keep].astype(np.int32)
    mland = H.at(M[:, 0], M[:, 1], 5.0)
    mtop = ahd(M[:, 2]) - mland
    r, g, b = MC[:, 0], MC[:, 1], MC[:, 2]
    mx = MC.max(1)
    crown = (((g >= r - 1) & (g >= b + 2) & (mx < 170)) | ((mx < 50) & (g >= b) & (g >= r - 2)))
    tall = (mtop > CANOPY_MIN_UP) & (MN[:, 2] > 0.3)
    e0 = min(vc[:, 0].min(), M[:, 0].min()) - CANOPY_CELL
    n0 = min(vc[:, 1].min(), M[:, 1].min()) - CANOPY_CELL
    ni = int((max(vc[:, 0].max(), M[:, 0].max()) - e0) // CANOPY_CELL) + 2
    nj = int((max(vc[:, 1].max(), M[:, 1].max()) - n0) // CANOPY_CELL) + 2
    cell = lambda e, n: (((e - e0) // CANOPY_CELL).astype(int), ((n - n0) // CANOPY_CELL).astype(int))  # noqa: E731
    vi, vj = cell(vc[:, 0], vc[:, 1])
    mi, mj = cell(M[:, 0], M[:, 1])
    allf = np.zeros((ni, nj))
    np.add.at(allf, (mi, mj), 1)
    cand = tall & crown
    cf = np.zeros((ni, nj))
    np.add.at(cf, (mi[cand], mj[cand]), 1)
    cnt_v = np.zeros((ni, nj))
    np.add.at(cnt_v, (vi, vj), 1)
    seen_m = (cf / np.maximum(allf, 1) >= CANOPY_SHARE) & (cf > 0)
    # the shaded crowns: off the buildings too (the green faces were filtered above)
    ci_, cj_ = np.nonzero(seen_m)
    ce, cn = e0 + (ci_ + 0.5) * CANOPY_CELL, n0 + (cj_ + 0.5) * CANOPY_CELL
    seen_m[ci_[~off_buildings(ce, cn)], cj_[~off_buildings(ce, cn)]] = False
    seen = (cnt_v > 0) | seen_m
    # each cell: its crowns' top over the land (the highest green face, else the highest shaded crown face) and colour
    hgt = np.zeros((ni, nj))
    np.maximum.at(hgt, (vi, vj), vtop)
    hm = np.zeros((ni, nj))
    np.maximum.at(hm, (mi[cand], mj[cand]), mtop[cand])
    hgt = np.where(hgt > 0, hgt, hm)
    csum = np.zeros((ni, nj, 3))
    cnt = np.zeros((ni, nj))
    np.add.at(csum, (vi, vj), lin_of(VC.astype(np.float64) / 255.0))
    np.add.at(cnt, (vi, vj), 1)
    np.add.at(csum, (mi[cand], mj[cand]), lin_of(MC[cand].astype(np.float64) / 255.0))
    np.add.at(cnt, (mi[cand], mj[cand]), 1)
    mask = ndimage.binary_closing(seen, np.ones((3, 3), bool)) | seen
    _, (ii, jj) = ndimage.distance_transform_edt(~seen, return_indices=True)
    hgt = np.where(seen, hgt, hgt[ii, jj])
    colc = csum / np.maximum(cnt, 1)[..., None]
    col = np.where((cnt > 0)[..., None], colc, colc[ii, jj])
    hgt = np.clip(hgt, CANOPY_MIN_UP + 1.0, 35.0)
    # no cell on open water (Overture's), and none in a lone speck (a pole, a sign: the leftover shards)
    W = water_grid(slug, frame, CITY_OUT, CANOPY_CELL)
    if W is not None:
        ce_, cn_ = e0 + (np.arange(ni) + 0.5) * CANOPY_CELL, n0 + (np.arange(nj) + 0.5) * CANOPY_CELL
        wr = np.clip(((CITY_OUT - cn_) / CANOPY_CELL).astype(int), 0, W.shape[0] - 1)
        wc = np.clip(((ce_ + CITY_OUT) / CANOPY_CELL).astype(int), 0, W.shape[1] - 1)
        mask &= ~(W[wr[None, :], wc[:, None]] > 0.3)
    lab, nl = ndimage.label(mask)
    if nl:
        size = ndimage.sum(mask, lab, np.arange(1, nl + 1))
        mask &= np.r_[False, size >= CANOPY_MIN_CELLS][lab]
    # a crown's top smoothed over its neighbours (a lone tall face read as a spike): the median, then a soft blur
    hgt = np.where(mask, ndimage.median_filter(np.where(mask, hgt, 0.0), size=3), 0.0)
    wsum = ndimage.gaussian_filter(mask.astype(float), 1.0)
    hgt = np.where(mask, ndimage.gaussian_filter(hgt, 1.0) / np.maximum(wsum, 1e-6), 0.0)
    hgt = np.where(mask, np.maximum(hgt, CANOPY_MIN_UP + 1.0), 0.0)
    if slug in CANOPY_TARGET:
        med = np.median(col[mask], 0)
        col = col * (lin_of(np.array(CANOPY_TARGET[slug]) / 255.0) / np.maximum(med, 1e-6))
    I, J = np.nonzero(mask)
    m = len(I)
    # the top's corners: (ni + 1) x (nj + 1), each at the land plus the mean top of the tree cells round it (bare cells
    # left out, so a mass keeps its height to its edge)
    mk = np.pad(mask.astype(float), 1)
    hp = np.pad(hgt * mask, 1)
    cp = np.pad(col * mask[..., None], ((1, 1), (1, 1), (0, 0)))
    cn4 = mk[:-1, :-1] + mk[1:, :-1] + mk[:-1, 1:] + mk[1:, 1:]
    corner_h = (hp[:-1, :-1] + hp[1:, :-1] + hp[:-1, 1:] + hp[1:, 1:]) / np.maximum(cn4, 1)
    corner_c = (cp[:-1, :-1] + cp[1:, :-1] + cp[:-1, 1:] + cp[1:, 1:]) / np.maximum(cn4, 1)[..., None]
    used = np.zeros(corner_h.shape, bool)
    for di in (0, 1):
        for dj in (0, 1):
            used[I + di, J + dj] = True
    ui, uj = np.nonzero(used)
    vid = -np.ones(corner_h.shape, np.int64)
    vid[ui, uj] = np.arange(len(ui))
    E, N = e0 + ui * CANOPY_CELL, n0 + uj * CANOPY_CELL
    UP = corner_h[ui, uj]
    a0, a1, a2, a3 = vid[I, J], vid[I + 1, J], vid[I + 1, J + 1], vid[I, J + 1]
    F = np.concatenate([np.c_[a0, a1, a2], np.c_[a0, a2, a3]])
    # the masses' outline: the cells' stairs smoothed into the crowns' own curves (each corner on the outline drawn
    # towards its two neighbours on it), and the outline's top a little under the mass's, so a crown's edge rounds off
    E, N, rim = _smooth_outline(F, E, N, CANOPY_OUTLINE_PASSES)
    UP = np.where(rim, UP * CANOPY_RIM_DROP, UP)
    L = H.at(E, N, CANOPY_CELL)
    X, Z = frame.xz(E, N)
    V = np.stack([X, L + UP - drop(X, Z), Z], 1)
    VL = np.stack([X, L - 0.5 - drop(X, Z), Z], 1)     # the same corner on the land, for the walls
    VC = corner_c[ui, uj]
    # thinned with its border kept (thinning the border left slivers standing off the masses: the shards)
    import pyfqmr
    from scipy.spatial import cKDTree
    s = pyfqmr.Simplify()
    s.setMesh(V, F.astype(np.int32))
    s.simplify_mesh(target_count=CANOPY_TRIS, aggressiveness=7, preserve_border=True, verbose=False)
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
    # lit mostly from above: the masses' own facets lit one by one read as folded paper
    vn = 0.3 * vn + 0.7 * np.array([0.0, 1.0, 0.0])
    vn /= np.linalg.norm(vn, axis=1, keepdims=True)
    # the walls: every top edge used by one triangle only, dropped to the land
    ed = np.sort(np.concatenate([F2[:, [0, 1]], F2[:, [1, 2]], F2[:, [2, 0]]]), 1)
    ed_t = np.tile(np.arange(len(F2)), 3)
    ue, inv, ec = np.unique(ed, axis=0, return_inverse=True, return_counts=True)
    inv = inv.ravel()
    once = ec[inv] == 1
    border, border_t, top_y, sub = _wall_runs(ed[once], ed_t[once], V2, CANOPY_WALL_TOL)
    low = VL[nb[border.ravel()]].reshape(-1, 2, 3)
    low[..., 1] -= 1.5                                  # under the land between a run's ends too
    nw = len(border)
    base = len(V2)
    t0, t1 = V2[border[:, 0]].copy(), V2[border[:, 1]].copy()
    t0[:, 1] = top_y; t1[:, 1] = top_y                  # the run's highest top: a lip, never a gap under the top
    WV = np.concatenate([t0, t1, low[:, 1], low[:, 0]])
    WC = np.concatenate([colv[border[:, 0]], colv[border[:, 1]], colv[border[:, 1]], colv[border[:, 0]]]) * CANOPY_WALL_SHADE
    k = np.arange(nw)
    q0, q1, q2, q3 = base + k, base + nw + k, base + 2 * nw + k, base + 3 * nw + k
    WF = np.concatenate([np.c_[q0, q1, q2], np.c_[q0, q2, q3]])
    # each wall faces out of its mass: away from the mass's middle there (the top triangle on its edge)
    P3 = np.concatenate([V2, WV])
    wn = np.cross(P3[WF[:, 1]] - P3[WF[:, 0]], P3[WF[:, 2]] - P3[WF[:, 0]])
    tc = V2[F2[border_t]].mean(1)
    em = (V2[sub[:, 0]] + V2[sub[:, 1]]) / 2           # the run's first top edge, outward from its own triangle
    out = np.tile(em - tc, (2, 1))
    inward = (wn[:, [0, 2]] * out[:, [0, 2]]).sum(1) < 0
    WF[inward] = WF[inward][:, ::-1]
    wn[inward] *= -1
    wn[:, 1] = 0.0
    wn /= np.maximum(np.linalg.norm(wn, axis=1, keepdims=True), 1e-9)
    WN = np.zeros_like(WV)
    for kk in range(3):
        np.add.at(WN, WF[:, kk] - base, wn)
    WN = 0.6 * WN / np.maximum(np.linalg.norm(WN, axis=1, keepdims=True), 1e-9) + 0.4 * np.array([0.0, 1.0, 0.0])
    WN /= np.linalg.norm(WN, axis=1, keepdims=True)
    pos = np.concatenate([V2, WV])
    nrm = np.concatenate([vn, WN])
    colall = np.concatenate([colv, WC])
    idx = np.concatenate([F2, WF])
    print("canopy: %d green faces, %d shaded crown faces; %d cells (%d closed); drawn in %d top and %d wall triangles"
          % (len(vc), int(cand.sum()), int(seen.sum()), m, len(F2), len(WF)))
    return {"name": "trees_far", "pos": pos.astype(np.float32), "nrm": nrm.astype(np.float32),
            "col": np.c_[colall, np.ones(len(colall))].astype(np.float32),
            "idx": idx.ravel().astype(np.uint32), "material": "horizon_trees"}


def _smooth_outline(F, E, N, passes):
    """The border of a triangle mesh (F into E, N) smoothed in plan: each border corner where exactly two border edges
    meet moved half way to its two neighbours' middle, passes times. Returns the moved E, N and which corners are
    on the border."""
    ed = np.sort(np.concatenate([F[:, [0, 1]], F[:, [1, 2]], F[:, [2, 0]]]), 1)
    ue, ec = np.unique(ed, axis=0, return_counts=True)
    b = ue[ec == 1]
    rim = np.zeros(len(E), bool)
    rim[b.ravel()] = True
    deg = np.bincount(b.ravel(), minlength=len(E))
    nsum_e, nsum_n = np.zeros(len(E)), np.zeros(len(E))
    E, N = E.astype(np.float64).copy(), N.astype(np.float64).copy()
    move = deg == 2
    for _ in range(passes):
        nsum_e[:] = 0; nsum_n[:] = 0
        np.add.at(nsum_e, b[:, 0], E[b[:, 1]]); np.add.at(nsum_e, b[:, 1], E[b[:, 0]])
        np.add.at(nsum_n, b[:, 0], N[b[:, 1]]); np.add.at(nsum_n, b[:, 1], N[b[:, 0]])
        E = np.where(move, 0.5 * E + 0.25 * nsum_e, E)
        N = np.where(move, 0.5 * N + 0.25 * nsum_n, N)
    return E, N, rim


def _wall_runs(edges, owner, V, tol):
    """The canopy top's border edges (index pairs into V, each with the top triangle it belongs to) joined into
    straight runs: each chain of the border (broken where more than two edges meet) thinned by Douglas-Peucker in
    plan to within tol. Returns the runs' end pairs, a top triangle on each, each run's highest top and its first edge."""
    from collections import defaultdict
    adj = defaultdict(list)
    for k, (a, b) in enumerate(edges):
        adj[a].append(k)
        adj[b].append(k)
    used = np.zeros(len(edges), bool)
    out_e, out_t, out_y, out_s = [], [], [], []

    def dp(pts, i0, i1, keep):
        if i1 <= i0 + 1:
            return
        p, q = pts[i0], pts[i1]
        d = q - p
        L = math.hypot(d[0], d[1])
        r = pts[i0 + 1:i1] - p
        dist = np.abs(r[:, 0] * d[1] - r[:, 1] * d[0]) / L if L > 1e-9 else np.hypot(r[:, 0], r[:, 1])
        m = int(np.argmax(dist))
        if dist[m] > tol:
            keep.append(i0 + 1 + m)
            dp(pts, i0, i0 + 1 + m, keep)
            dp(pts, i0 + 1 + m, i1, keep)

    for k0 in range(len(edges)):
        if used[k0]:
            continue
        # walk back to a chain end (a vertex not of degree two), or round a loop
        k, v = k0, edges[k0][0]
        for _ in range(len(edges)):
            if len(adj[v]) != 2:
                break
            nk = adj[v][0] if adj[v][1] == k else adj[v][1]
            if nk == k0:
                break
            k = nk
            v = edges[k][1] if edges[k][0] == v else edges[k][0]
        start, verts, ks = k, [v], []
        while True:
            used[k] = True
            ks.append(k)
            v = edges[k][1] if edges[k][0] == v else edges[k][0]
            verts.append(v)
            if len(adj[v]) != 2:
                break
            nk = adj[v][0] if adj[v][1] == k else adj[v][1]
            if used[nk] or nk == start:
                break
            k = nk
        pts = V[verts][:, [0, 2]]
        keep = [0, len(verts) - 1]
        if verts[0] == verts[-1] and len(verts) > 3:      # a loop: split it at its far point first
            far = int(np.argmax(np.hypot(*(pts - pts[0]).T)))
            keep.append(far)
            dp(pts, 0, far, keep)
            dp(pts, far, len(verts) - 1, keep)
        else:
            dp(pts, 0, len(verts) - 1, keep)
        keep = sorted(set(keep))
        ys = V[verts][:, 1]
        for i0, i1 in zip(keep[:-1], keep[1:]):
            out_e.append((verts[i0], verts[i1]))
            out_t.append(owner[ks[i0]])
            out_s.append(edges[ks[i0]])
            out_y.append(float(ys[i0:i1 + 1].max()))
    return (np.array(out_e, np.int64).reshape(-1, 2), np.array(out_t, np.int64), np.array(out_y),
            np.array(out_s, np.int64).reshape(-1, 2))


def _overture_footprints(slug, frame):
    """Overture's building footprints (overture_building.json, fetch) as polygons in metres east and north."""
    path = work(slug, "overture_building.json")
    if not os.path.exists(path):
        return []
    from shapely import wkt
    out = []
    for r in json.load(open(path)):
        out += _local_poly_all(frame, wkt.loads(r["wkt"]))
    return out


def _local_poly_all(frame, geom):
    from shapely.geometry import Polygon
    out = []
    for g in getattr(geom, "geoms", [geom]):
        if g.geom_type != "Polygon" or g.is_empty:
            continue
        lon, lat = np.array(g.exterior.coords).T
        e, n = frame.en(lon, lat)
        out.append(Polygon(np.c_[e, n]).buffer(0))
    return out


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
    acc = {k: ([], [], [], [], [], [0]) for k in ("city_far", "city_far_low")}   # pos, nrm, col, uv, idx, nv
    base_cache = {}
    kind_tris = collections.Counter()
    outline = collections.defaultdict(list)     # a measured structure's parts, for one ground floor under them all
    for pc in out:
        if isinstance(pc[3], tuple):
            outline[pc[3]].append(np.array(pc[0].exterior.coords))
    for poly, z0, top, look, tall, real in out:
        cpt = poly.centroid
        far_zone = max(abs(cpt.x), abs(cpt.y)) > FAR_ZONE
        k_far = 2.0 if far_zone else 1.0
        low_block = not tall and not isinstance(look, tuple)
        if low_block and far_zone and top < FAR_HOUSES_BELOW:
            kind_tris["far house left to the land"] += 1
            continue
        pos, nrm, col, uv, idx, nvb = acc["city_far_low" if low_block else "city_far"]
        nv = nvb[0]
        poly = poly.simplify((TALL_SIMPLIFY if tall else LOW_SIMPLIFY) * k_far, preserve_topology=True)
        if poly.is_empty or poly.geom_type != "Polygon" or poly.area < MIN_AREA * k_far:
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
        nvb[0] = nv
    # two surfaces: the towers and measured structures, and the low blocks (which a phone on Low leaves out,
    # Oval3DQuality.apply_model)
    surf = [{"name": name, "pos": np.array(a[0], np.float32), "nrm": np.array(a[1], np.float32),
             "col": np.array(a[2], np.float32), "uv": np.array(a[3], np.float32), "idx": np.array(a[4], np.uint32),
             "material": "city_towers"} for name, a in acc.items() if a[4]]
    return surf, {"buildings": dict(src), "pieces_drawn": len(out), "triangles_by_kind": dict(kind_tris), "height_check": table.report}


def _local_poly(frame, g):
    from shapely.geometry import Polygon
    lon, lat = np.array(g.exterior.coords).T
    e, n = frame.en(lon, lat)
    return Polygon(np.c_[e, n]).buffer(0)


# ---- glb ------------------------------------------------------------------------------------------

def near_water(G, water_y, slug):
    """The backdrop's painted harbour and river, past the surrounds' edge, as one flat sheet with a hard edge: traced
    at NEAR_WATER_STEP from the ground's own painted water, so it lies exactly where the painting has it. Seen from
    the orbit the painting alone smeared the quay by the paddock at the harbour's west end into a soft, ragged beige
    fringe (its 1.5 m texels stretched over 30 m triangles; the PC's renders, 2026-11-27). Drawn in the painted
    water's own mean colour, NEAR_WATER_LIFT over it, and lit as the ground is (GroundModels' matte backdrop)."""
    import mapbox_earcut as earcut
    from rasterio import features
    from rasterio.transform import from_origin
    from shapely.geometry import Point, box, shape
    from shapely.ops import unary_union
    for mi, m in enumerate(G.J["meshes"]):
        if not G.name_of.get(mi, m.get("name", "")).startswith("bg_near_ground"):
            continue
        pr = m["primitives"][0]
        got = reland._ground_texture(G, pr)
        if got is None or "TEXCOORD_0" not in pr["attributes"]:
            continue
        img = got[1]
        P = G.read(pr["attributes"]["POSITION"]).astype(np.float64)
        UV = G.read(pr["attributes"]["TEXCOORD_0"]).astype(np.float64)
        T = G.read(pr["indices"]).reshape(-1, 3)
        break
    else:
        return None
    wtex = reland._water_texels(img)
    if not wtex.any():
        return None
    outer, reach, _ = reland.surrounds_outer(slug)
    near_from = outer + reach
    cx, cz = reland.fit(slug)[:2]
    colour = lin_of(img[wtex].mean(0) / 255.0)
    st, half = NEAR_WATER_STEP, SKIRT
    xs = np.arange(-half + st / 2, half, st)
    n = len(xs)
    grid = np.zeros((n, n), np.uint8)
    h, w = wtex.shape
    # each ground triangle's own grid points, its UV taken across it (barycentric), the painted texel looked up
    for a, b, cc in T:
        A, B, C = P[a, [0, 2]], P[b, [0, 2]], P[cc, [0, 2]]
        lo, hi = np.minimum(np.minimum(A, B), C), np.maximum(np.maximum(A, B), C)
        i0, i1 = np.searchsorted(xs, [lo[0], hi[0]])
        j0, j1 = np.searchsorted(xs, [lo[1], hi[1]])
        if i1 <= i0 or j1 <= j0:
            continue
        gx, gz = np.meshgrid(xs[i0:i1], xs[j0:j1])
        d = (B[1] - C[1]) * (A[0] - C[0]) + (C[0] - B[0]) * (A[1] - C[1])
        if abs(d) < 1e-9:
            continue
        l1 = ((B[1] - C[1]) * (gx - C[0]) + (C[0] - B[0]) * (gz - C[1])) / d
        l2 = ((C[1] - A[1]) * (gx - C[0]) + (A[0] - C[0]) * (gz - C[1])) / d
        l3 = 1 - l1 - l2
        inside = (l1 >= -1e-6) & (l2 >= -1e-6) & (l3 >= -1e-6) & (np.hypot(gx - cx, gz - cz) >= near_from - 3 * st)
        if not inside.any():
            continue
        u = l1[inside] * UV[a, 0] + l2[inside] * UV[b, 0] + l3[inside] * UV[cc, 0]
        v = l1[inside] * UV[a, 1] + l2[inside] * UV[b, 1] + l3[inside] * UV[cc, 1]
        jj, ii = np.nonzero(inside)
        grid[j0 + jj, i0 + ii] = wtex[np.clip((v * h).astype(int), 0, h - 1), np.clip((u * w).astype(int), 0, w - 1)]
    tf = from_origin(-half, -half, st, -st)   # row j is z = -half + j * st, column i is x = -half + i * st
    polys = [shape(g) for g, v in features.shapes(grid, mask=grid > 0, transform=tf) if v == 1]
    if not polys:
        return None
    sheet = unary_union(polys).simplify(st * 0.7).intersection(
        box(-half, -half, half, half).difference(Point(cx, cz).buffer(near_from, 256)))
    Vs, F, n0, spans = [], [], 0, []
    for pg in getattr(sheet, "geoms", [sheet]):
        if pg.geom_type != "Polygon" or pg.area < 20.0:
            continue
        rings = [np.array(pg.exterior.coords)[:-1]] + [np.array(q.coords)[:-1] for q in pg.interiors]
        pts = np.concatenate(rings)
        t = earcut.triangulate_float64(pts, np.cumsum([len(q) for q in rings]).astype(np.uint32)).reshape(-1, 3)
        F.append(t + n0)
        Vs.append(pts)
        for c0, c1 in zip(np.r_[0, np.cumsum([len(q) for q in rings])[:-1]], np.cumsum([len(q) for q in rings])):
            spans.append((n0 + c0, n0 + c1))
        n0 += len(pts)
    if not Vs:
        return None
    Q = np.concatenate(Vs)
    F = np.concatenate(F)
    Y = water_y + NEAR_WATER_LIFT - drop(Q[:, 0], Q[:, 1])
    # the edge along the ring: a band from it, NEAR_WATER_DIVE in and down, under the ring's own water (the sheet is
    # traced from inside the circle and cut on it, so its whole inner edge lies on the circle and carries the band;
    # traced from the circle, its edge was a 1 m staircase just outside it, and the band only on the steps that touched)
    rq = np.hypot(Q[:, 0] - cx, Q[:, 1] - cz)
    on = rq < near_from + 0.3
    band, nb = [], 0
    for s0, s1 in spans:   # each ring, closed
        for i in range(s0, s1):
            j = i + 1 if i + 1 < s1 else s0
            if on[i] and on[j]:
                band.append((i, j))
    if band:
        e = np.array(band)
        k0 = len(Q)
        pin = Q[np.unique(e)]
        idx_of = {v: k0 + j for j, v in enumerate(np.unique(e))}
        rr = np.hypot(pin[:, 0] - cx, pin[:, 1] - cz)
        sc = (rr - NEAR_WATER_DIVE[0]) / rr
        low = np.c_[cx + (pin[:, 0] - cx) * sc, cz + (pin[:, 1] - cz) * sc]
        Q = np.r_[Q, low]
        Y = np.r_[Y, water_y - NEAR_WATER_DIVE[1] - drop(low[:, 0], low[:, 1])]
        quads = [(a, b, idx_of[b], idx_of[a]) for a, b in e]
        F = np.r_[F, [(a, b, c) for a, b, c, d in quads], [(a, c, d) for a, b, c, d in quads]]
        # wound up (+y) like the sheet: a triangle facing down flips
        P3 = np.c_[Q[:, 0], Y, Q[:, 1]]
        nrm_y = np.cross(P3[F[:, 1]] - P3[F[:, 0]], P3[F[:, 2]] - P3[F[:, 0]])[:, 1]
        F[nrm_y < 0] = F[nrm_y < 0][:, ::-1]
        nb = len(quads)
    pos = np.c_[Q[:, 0], Y, Q[:, 1]].astype(np.float32)
    print("near water: edge along the ring dives under it in", nb, "quads")
    print("near water sheet", round(sheet.area), "m2 in", len(F), "triangles, colour (linear)", colour.round(4))
    return {"name": "water_near", "pos": pos, "nrm": np.tile([0.0, 1.0, 0.0], (len(pos), 1)).astype(np.float32),
            "col": np.tile(np.r_[colour, 1.0], (len(pos), 1)).astype(np.float32),
            "idx": F.ravel().astype(np.uint32), "material": "water_near"}


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
        # the name carries the picture's own hash: Godot writes an embedded image out beside the model once
        # (<model>_<image>.png) and keeps drawing that copy after the model changes
        J["images"].append({"bufferView": view(png), "mimeType": "image/png",
                            "name": "horizon_%s_%08x" % (name, zlib.crc32(png))})
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


IMAGE_IMPORT = """[remap]

importer="texture"
type="CompressedTexture2D"

[params]

compress/mode=2
compress/high_quality=false
mipmaps/generate=true
mipmaps/limit=-1
detect_3d/compress_to=0
"""


def write_image_imports(glb, images):
    """The land's pictures as Godot would write them out of the model, each with its import settings: mipmaps (or the
    10 m and 40 m land shimmers as the orbit turns) and VRAM compression. A picture fetched or written before the
    model's import took a plain 2D picture's settings, no mipmaps (review, 2026-11-28); the horizon's shader material
    is not one Godot's 3D detection sees. Publish the pictures with the model (tools/ground_assets.sh publish ... PATH)
    and commit their settings. The old pictures' copies and settings go."""
    import glob
    stem = os.path.splitext(glb)[0]
    keep = set()
    for name, png in images.items():
        f = "%s_horizon_%s_%08x.png" % (stem, name, zlib.crc32(png))
        keep.add(f)
        # written here, not left for Godot to write out of the model: with its settings file present and the picture
        # missing, Godot's import of the model fails to find it (and a fresh checkout has the settings from git and
        # the picture from the lock, tools/ground_assets.lock)
        open(f, "wb").write(png)
        open(f + ".import", "w").write(IMAGE_IMPORT)
    for f in glob.glob(stem + "_horizon_*.png"):
        if f not in keep:
            for g in (f, f + ".import"):
                if os.path.exists(g):
                    os.remove(g)


# The inputs a ground's horizon needs beyond the open data every ground has (build() stops without them).
MEASURED_CITY = {"marvel": ("com/2023-building-footprints.geojson", "photomesh.npz")}


def build(slug, backdrop=None):
    frame = Frame(slug)
    H = Heights(slug, frame)
    part1 = backdrop or os.path.join(ROOT, "assets", "grounds", slug, slug + "_backdrop_part1.glb")
    G = reland.Glb(part1)
    # the seam colour, the water and the near water sheet read the near ground from part1, its one primitive
    near_prims = [n for n, _, _ in G.prims if n.startswith("bg_near_ground")]
    if len(near_prims) != 1:
        raise RuntimeError("%s: near ground in %d primitives; seam_gain/near_water read one" % (part1, len(near_prims)))
    for other in sorted(glob.glob(os.path.join(os.path.dirname(part1), slug + "_backdrop_part*.glb"))):
        if os.path.abspath(other) != os.path.abspath(part1):
            if any(n.startswith("bg_near_ground") for n, _, _ in reland.Glb(other).prims):
                raise RuntimeError("%s carries near ground too; seam_gain/near_water read part1's only" % other)
    # the measured city (City of Melbourne footprints and photomesh): a ground that has it must not build without
    for need in MEASURED_CITY.get(slug, ()):
        if not os.path.exists(work(slug, *need.split("/"))):
            raise SystemExit("%s: %s missing from %s (fetch it first: see com_parts() and photomesh.py); without it "
                             "the far city loses its measured heights and the trees" % (slug, need, work(slug)))
    wp = next(p for p in G.prims if p[0].startswith(reland.WATER))
    water_y = float(np.median(G.read(wp[1])[:, 1]))
    if not os.path.exists(work(slug, "overture_water.json")):
        fetch_water(slug)
    near, mid, far = S2(slug, "near", frame), S2(slug, "mid", frame), S2(slug, "far", frame)
    gain, water = seam_gain(G, frame, near, slug)
    land, land_rep = land_mesh(slug, frame, H, water_y, gain, near, mid, far, water)
    city_s, city_rep = city(slug, frame, H, gain, near)
    trees = canopy(slug, frame, H, com_parts(slug, frame, lambda g: [_local_poly(frame, gg) for gg in getattr(g, "geoms", [g])]))
    sheet = near_water(G, water_y, slug)
    surfaces = land + city_s + ([trees] if trees is not None else []) + ([sheet] if sheet is not None else [])
    images = {"near": texture_png(square_fade(near, frame, part1, gain), gain, water), "mid": texture_png(mid, gain, water)}
    out = os.path.join(ROOT, "assets", "grounds", slug, slug + "_horizon.glb")
    size = write_glb(out, surfaces, images)
    write_image_imports(out, images)
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
