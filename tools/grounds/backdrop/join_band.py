"""The circle seen from above (issue #2347): where a ground's own surrounds map (surrounds.webp, GroundModels
SURROUNDS) meets its backdrop's near ground (bg_near_ground in <slug>_backdrop_part1.glb), two separately painted
maps met on a hard line at the surrounds' `outer` radius.

`apply` does two things, in order:
1. `water`: both maps are brought to Overture's open water (OpenStreetMap's) where they painted land on it: the
   surrounds map over its whole span, the backdrop's bake round the join. The MCG's map had no Yarra.
2. The band: the surrounds map's outer JOIN_BAND m blends, in linear light, into the backdrop's own bake at the same
   spot: untouched JOIN_BAND m inside the join, the backdrop's colour at the join itself (its `tint` taken out, so the
   drawn colours meet). Both meshes stay opaque and do not overlap (director review on #2347, 28 Nov: no alpha fade
   over a 2 km plane). The surface settings are matched in GroundModels (both matte, no tint).

    python3 join_band.py apply SLUG [SLUG...]   # rewrites surrounds.webp (and the part1 glb's ground image) once
    python3 join_band.py check SLUG [SLUG...]   # the step left at the join; exit 1 over JOIN_MAX_STEP

A surrounds map rebuilt by its ground's surrounds.py comes out without either: run `apply` after it. `apply`
records the map it wrote (surrounds_join.json beside it) and leaves a map it already wrote alone. `water` needs
numpy, scipy, shapely, rasterio and the Overture water (horizon.fetch_water, fetched on first use); `check` needs
numpy and Pillow only (it runs in the nightly ground-shots job).
"""
import hashlib
import io
import json
import math
import os
import re
import struct
import sys

import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
JOIN_BAND = 60.0       # m: the surrounds map's outer band painted toward the backdrop's bake
JOIN_EDGE = 1.5        # m: `check` samples each map this far its own side of the join
JOIN_WINDOW = 15.0     # m: half-length of arc each `check` sample averages
JOIN_MAX_STEP = 0.03   # `check`: the median summed linear step allowed at the join
GROUND_CELL = 6.0      # m: `ground_field` averages the bake over cells this size first
# Where each ground's surrounds map has its 0, 0 (the model's), as its own surrounds.py lays it: lat, lon, and the
# model's 0, 0 east and north of that point in metres (KX = 111320 cos lat, KY = 110574, as they use). Checked by
# `water`: the map's painted water and Overture's agree to 0.2 % (Marvel, Geelong) and 1.7 % (Adelaide) of texels
# 300-950 m out, at no shift.
MAP_ORIGIN = {
    "marvel": (-37.816495302702705, 144.9475565216216, 0.0, 0.0),   # tools/grounds/marvel/surrounds.py LAT0, LON0
    "mcg": (-37.81977, 144.98316, 25.3, -23.5),                      # mcg/surrounds.py LAT0, LON0, PITCH_E, PITCH_N
    "adelaide": (-34.915489777922076, 138.59627692467532, 0.0, 0.0),  # adelaide/surrounds.py LAT0, LON0
    "gmhba": (-38.1579976, 144.3546774, 0.0, 0.0),                    # gmhba/surrounds.py S.LAT0, S.LON0
}
WATER_MIN = 3          # opening (m): water Overture has and a map lacks counts only past a 3 m sliver at a shore
WATER_TOL = 18         # 8-bit: a texel within this of a map's water colour is painted water
WATER_BAKE_OUT = 100.0  # m: the backdrop's bake is brought to Overture's water this far past the join
GROUND_SMOOTH = 30.0   # m: then takes the median over this, so a road or a roof drops out


def lin(c):
    c = np.asarray(c, np.float64) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb8(x):
    x = np.clip(x, 0.0, 1.0)
    return np.round(255.0 * np.where(x <= 0.0031308, 12.92 * x, 1.055 * x ** (1 / 2.4) - 0.055)).astype(np.uint8)


def surrounds(slug):
    """span, outer and tint of the ground's SURROUNDS entry in GroundModels.gd."""
    gm = open(os.path.join(ROOT, "scripts", "ui", "match", "GroundModels.gd")).read()
    block = gm[gm.index("const SURROUNDS := {"):gm.index("const SURROUNDS_SHADER")]
    m = re.search(r'^\t"%s": \{(.*?)(?=^\t"[a-z_]+": \{|^\})' % re.escape(slug), block, re.S | re.M)
    if not m:
        raise RuntimeError("%s: no SURROUNDS entry" % slug)
    e = m.group(1)
    num = lambda k, d: float(re.search(r'"%s": ([\d.]+)' % k, e).group(1)) if ('"%s"' % k) in e else d  # noqa: E731
    t = re.search(r'"tint": Color\(([\d., ]+)\)', e)
    tint = np.array([float(v) for v in t.group(1).split(",")][:3]) if t else np.ones(3)
    if '"outer"' not in e:
        raise RuntimeError("%s: SURROUNDS has no `outer`, so no join with a backdrop" % slug)
    return num("span", 2048.0), num("outer", 2500.0), tint


def near_bake(slug, path=None):
    """The backdrop's near-ground bake (linear, times its base colour factor) with its mesh's positions and UVs (for
    plan_fit), from `path` or the ground's own <slug>_backdrop_part1.glb."""
    path = path or os.path.join(ROOT, "assets", "grounds", slug, slug + "_backdrop_part1.glb")
    raw = open(path, "rb").read()
    jl = struct.unpack("<I", raw[12:16])[0]
    J = json.loads(raw[20:20 + jl])
    bl = struct.unpack("<I", raw[20 + jl:24 + jl])[0]
    BIN = raw[28 + jl:28 + jl + bl]

    def acc(i):
        a = J["accessors"][i]
        v = J["bufferViews"][a["bufferView"]]
        dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a["componentType"]]
        nc = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
        if v.get("byteStride", np.dtype(dt).itemsize * nc) != np.dtype(dt).itemsize * nc:
            raise RuntimeError("%s: accessor %d is interleaved" % (path, i))
        arr = np.frombuffer(BIN, dt, a["count"] * nc, v.get("byteOffset", 0) + a.get("byteOffset", 0))
        return arr.reshape(a["count"], nc) if nc > 1 else arr

    nodes = [n for n in J["nodes"] if "mesh" in n and J["meshes"][n["mesh"]].get("name", "").startswith("bg_near_ground")]
    if len(nodes) != 1:
        raise RuntimeError("%s: %d bg_near_ground meshes (need one)" % (path, len(nodes)))
    if any(k in nodes[0] for k in ("matrix", "translation", "rotation", "scale")):
        raise RuntimeError("%s: bg_near_ground has a node transform" % path)
    pr = J["meshes"][nodes[0]["mesh"]]["primitives"]
    if len(pr) != 1:
        raise RuntimeError("%s: bg_near_ground in %d primitives (need one)" % (path, len(pr)))
    pr = pr[0]
    if "COLOR_0" in pr["attributes"]:
        raise RuntimeError("%s: bg_near_ground carries vertex colours; the bake alone is not its colour" % path)
    P = acc(pr["attributes"]["POSITION"]).astype(np.float64)
    UV = acc(pr["attributes"]["TEXCOORD_0"]).astype(np.float64)
    pbr = J["materials"][pr["material"]].get("pbrMetallicRoughness", {})
    tx = J["textures"][pbr["baseColorTexture"]["index"]]
    im = J["images"][tx["source"] if "source" in tx else next(iter(tx["extensions"].values()))["source"]]
    bv = J["bufferViews"][im["bufferView"]]
    img = Image.open(io.BytesIO(BIN[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]])).convert("RGB")
    B = lin(np.asarray(img)) * np.array(pbr.get("baseColorFactor", [1, 1, 1, 1])[:3])
    return P, UV, B


def plan_fit(P, UV, r0, r1):
    sel = (np.hypot(P[:, 0], P[:, 2]) > r0) & (np.hypot(P[:, 0], P[:, 2]) < r1)
    if sel.sum() < 50:
        raise RuntimeError("only %d near-ground vertices between %.0f and %.0f m" % (sel.sum(), r0, r1))
    X = np.c_[P[sel][:, 0], P[sel][:, 2], np.ones(sel.sum())]
    cu = np.linalg.lstsq(X, UV[sel][:, 0], rcond=None)[0]
    cv = np.linalg.lstsq(X, UV[sel][:, 1], rcond=None)[0]
    err = np.hypot(X @ cu - UV[sel][:, 0], X @ cv - UV[sel][:, 1])
    return cu, cv, float(np.median(err)), float(np.percentile(err, 99))


def sample(img, u, v):
    """Bilinear sample of an (h, w, 3) linear image at UVs (any shape), clamped at the edge."""
    h, w = img.shape[:2]
    x = np.clip(u * w - 0.5, 0, w - 1)
    y = np.clip(v * h - 0.5, 0, h - 1)
    x0, y0 = np.floor(x).astype(int), np.floor(y).astype(int)
    x1, y1 = np.minimum(x0 + 1, w - 1), np.minimum(y0 + 1, h - 1)
    fx, fy = (x - x0)[..., None], (y - y0)[..., None]
    return (img[y0, x0] * (1 - fx) * (1 - fy) + img[y0, x1] * fx * (1 - fy)
            + img[y1, x0] * (1 - fx) * fy + img[y1, x1] * fx * fy)


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def overture_water(slug, half):
    """Overture's open water (OpenStreetMap's: the bay, the rivers, the harbour; the horizon's own source,
    horizon.fetch_water) on a 1 m grid of model x, z from -half to half, rows north to south as the maps."""
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "horizon"))
    import horizon
    from rasterio import features
    from rasterio.transform import from_origin
    from shapely import wkt
    from shapely.geometry import Polygon
    if not os.path.exists(horizon.work(slug, "overture_water.json")):
        horizon.fetch_water(slug)
    lat0, lon0, pe, pn = MAP_ORIGIN[slug]
    kx, ky = 111320.0 * math.cos(math.radians(lat0)), 110574.0

    def xz(c):
        c = np.asarray(c)
        return np.c_[(c[:, 0] - lon0) * kx - pe, -((c[:, 1] - lat0) * ky - pn)]

    shapes = []
    for r in json.load(open(horizon.work(slug, "overture_water.json"))):
        g = wkt.loads(r["wkt"])
        for gg in getattr(g, "geoms", [g]):
            if gg.geom_type == "Polygon" and not gg.is_empty:
                shapes.append(Polygon(xz(gg.exterior.coords), [xz(i.coords) for i in gg.interiors]))
    n = int(round(2 * half))
    return features.rasterize([(sh, 1) for sh in shapes], out_shape=(n, n), transform=from_origin(-half, -half, 1.0, -1.0),
                              dtype="uint8").astype(bool)


def _near(img, col, tol=WATER_TOL):
    return np.abs(np.asarray(img, float) - np.asarray(col, float)).max(-1) < tol


class _Glb:
    """Just enough of a glb to swap bg_near_ground's image and move its vertices (reland.Glb refuses a file with any
    transformed mesh node, as the MCG's has)."""

    def __init__(self, path):
        self.path = path
        raw = open(path, "rb").read()
        jl = struct.unpack("<I", raw[12:16])[0]
        self.J = json.loads(raw[20:20 + jl])
        bl = struct.unpack("<I", raw[20 + jl:24 + jl])[0]
        self.bin = bytearray(raw[28 + jl:28 + jl + bl])
        node = [n for n in self.J["nodes"] if "mesh" in n
                and self.J["meshes"][n["mesh"]].get("name", "").startswith("bg_near_ground")][0]
        self.pr = self.J["meshes"][node["mesh"]]["primitives"][0]
        pbr = self.J["materials"][self.pr["material"]]["pbrMetallicRoughness"]
        tx = self.J["textures"][pbr["baseColorTexture"]["index"]]
        self.ii = tx["source"] if "source" in tx else next(iter(tx["extensions"].values()))["source"]

    def _view(self, k):
        v = self.J["bufferViews"][k]
        return v.get("byteOffset", 0), v["byteLength"]

    def image(self):
        off, n = self._view(self.J["images"][self.ii]["bufferView"])
        return np.asarray(Image.open(io.BytesIO(bytes(self.bin[off:off + n]))).convert("RGB")).astype(int)

    def set_image(self, img):
        import zlib
        mime = self.J["images"][self.ii].get("mimeType", "image/webp")
        b = io.BytesIO()
        Image.fromarray(np.asarray(img, np.uint8)).save(b, "WEBP" if "webp" in mime else "PNG",
                                                        **({"lossless": True, "method": 4} if "webp" in mime else {}))
        k = self.J["images"][self.ii]["bufferView"]
        self.J["bufferViews"][k] = {"buffer": 0, "byteOffset": len(self.bin) + (-len(self.bin) % 4),
                                    "byteLength": len(b.getvalue())}
        self.bin += b"\0" * (-len(self.bin) % 4) + b.getvalue()
        # a new name: Godot keeps an image it once wrote out beside the model and drew that stale copy (reland)
        base = re.sub(r"(_toned)+(_[0-9a-f]{8})?$", "", self.J["images"][self.ii].get("name", "ground"))
        self.J["images"][self.ii]["name"] = "%s_toned_%08x" % (base, zlib.crc32(b.getvalue()))

    def attr(self, name):
        a = self.J["accessors"][self.pr["attributes"][name]]
        off, n = self._view(a["bufferView"])
        nc = {"VEC2": 2, "VEC3": 3}[a["type"]]
        return np.frombuffer(bytes(self.bin), np.float32, a["count"] * nc, off + a.get("byteOffset", 0)).reshape(-1, nc).copy()

    def set_attr(self, name, arr):
        a = self.J["accessors"][self.pr["attributes"][name]]
        off, _ = self._view(a["bufferView"])
        o = off + a.get("byteOffset", 0)
        data = np.asarray(arr, np.float32).tobytes()
        self.bin[o:o + len(data)] = data
        if name == "POSITION":
            a["min"], a["max"] = np.asarray(arr).min(0).tolist(), np.asarray(arr).max(0).tolist()

    def save(self):
        J = self.J
        # only the accessors a mesh uses (reduce.py leaves some pointing past the last buffer view), as reland.compact
        if J.get("skins") or J.get("animations"):
            raise RuntimeError("%s: _Glb.save knows meshes only" % self.path)
        refs = set()
        for m in J["meshes"]:
            for pr in m["primitives"]:
                refs |= set(pr["attributes"].values()) | ({pr["indices"]} if "indices" in pr else set())
                for tg in pr.get("targets", []):
                    refs |= set(tg.values())
        keep = sorted(refs)
        amap = {k: i for i, k in enumerate(keep)}
        J["accessors"] = [J["accessors"][k] for k in keep]
        for m in J["meshes"]:
            for pr in m["primitives"]:
                pr["attributes"] = {k: amap[v] for k, v in pr["attributes"].items()}
                if "indices" in pr:
                    pr["indices"] = amap[pr["indices"]]
                if "targets" in pr:
                    pr["targets"] = [{k: amap[v] for k, v in tg.items()} for tg in pr["targets"]]
        used = sorted({a["bufferView"] for a in self.J["accessors"] if "bufferView" in a}
                      | {im["bufferView"] for im in self.J.get("images", []) if "bufferView" in im})
        new, remap, views = bytearray(), {}, []
        for k in used:                                  # the old image's bytes leave the file
            off, n = self._view(k)
            new += b"\0" * (-len(new) % 4)
            v = dict(self.J["bufferViews"][k])
            v["byteOffset"] = len(new)
            new += self.bin[off:off + n]
            remap[k] = len(views)
            views.append(v)
        self.J["bufferViews"] = views
        for a in self.J["accessors"]:
            if "bufferView" in a:
                a["bufferView"] = remap[a["bufferView"]]
        for im in self.J.get("images", []):
            if "bufferView" in im:
                im["bufferView"] = remap[im["bufferView"]]
        self.J["buffers"][0]["byteLength"] = len(new)
        js = json.dumps(self.J, separators=(",", ":")).encode()
        js += b" " * (-len(js) % 4)
        body = bytes(new) + b"\0" * (-len(new) % 4)
        open(self.path, "wb").write(struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(body))
                                    + struct.pack("<II", len(js), 0x4E4F534A) + js
                                    + struct.pack("<II", len(body), 0x004E4942) + body)


def water(slug):
    """Bring both maps to Overture's open water where they paint land on it (plan step 2c, #2347): the surrounds map
    over its whole span (MCG's had no Yarra: its river was painted as grass) and the backdrop's bake from the band's
    inner edge to WATER_BAKE_OUT past the join. The new water takes the colour the backdrop paints Overture's water
    past the join, so both sides meet in one colour; a map that already paints its water keeps its own. Only land
    painted on Overture's water, past a WATER_MIN m sliver, changes. The backdrop's ground under its new water is laid
    flat at the level of its other painted water."""
    from scipy.ndimage import binary_erosion, binary_opening
    span, outer, tint = surrounds(slug)
    path = os.path.join(ROOT, "assets", "grounds", slug, "surrounds.webp")
    rec = os.path.join(ROOT, "assets", "grounds", slug, "surrounds_join.json")
    if os.path.exists(rec) and json.load(open(rec)).get("written") == sha(path):
        raise RuntimeError("%s: the band is already painted into this map; rebuild it before `water`" % slug)
    reach = outer + WATER_BAKE_OUT
    W = overture_water(slug, reach)
    n = W.shape[0]
    Wcore = binary_erosion(W, iterations=5)              # open water clear of its shores
    P, UV, B = near_bake(slug)
    cu, cv, _, _ = plan_fit(P, UV, outer - 50, outer + 300)
    x = np.arange(n) + 0.5 - n / 2
    X, Z = np.meshgrid(x, x)
    R = np.hypot(X, Z)
    far = Wcore & (R > outer + 20)
    if far.sum() < 200:
        print("%s: under 200 m2 of Overture's open water %d-%.0f m out; maps left as they are" % (slug, outer + 20, reach))
        return
    Bf = srgb8(sample(B, cu[0] * X[far] + cu[1] * Z[far] + cu[2], cv[0] * X[far] + cv[1] * Z[far] + cv[2])).astype(int)
    bcol = np.median(Bf, 0)
    bshare = float(_near(Bf, bcol).mean())
    # 1. the surrounds map
    S8 = np.array(Image.open(path).convert("RGB"))
    ms = S8.shape[0]
    o = (n - ms) // 2
    Wm, Wmc = W[o:o + ms, o:o + ms], Wcore[o:o + ms, o:o + ms]
    xm = np.arange(ms) + 0.5 - ms / 2
    Rm = np.hypot(*np.meshgrid(xm, xm))
    inner = Wmc & (Rm < outer - JOIN_BAND)
    to_map = srgb8(lin(bcol) / tint)
    mcol = to_map
    if inner.sum() > 200:
        own_col = np.median(S8[inner], 0)
        if _near(S8[inner], own_col).mean() > 0.7 and np.abs(own_col - to_map.astype(float)).max() < 40:
            mcol = own_col.round().astype(np.uint8)    # it paints its water already, in near the backdrop's colour
    own = _near(S8, mcol) | _near(S8, to_map)
    gap = binary_opening(Wm & ~own, iterations=WATER_MIN)
    if gap.any():
        S8[gap] = mcol
        Image.fromarray(S8).save(path, lossless=True, method=4)
    print("%s: surrounds map: %d m2 of Overture's water painted as land now water %s (the backdrop paints it %s, "
          "%.0f%% of its open water within %d)" % (slug, int(gap.sum()), list(map(int, mcol)), list(map(int, bcol)),
                                                   100 * bshare, WATER_TOL))
    # 2. the backdrop's bake round the join
    glb = os.path.join(ROOT, "assets", "grounds", slug, slug + "_backdrop_part1.glb")
    g = _Glb(glb)
    img = g.image()
    h, w = img.shape[:2]
    Ai = np.linalg.inv(np.array([[cu[0], cu[1]], [cv[0], cv[1]]]))
    tu, tv = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    bx = Ai[0, 0] * (tu - cu[2]) + Ai[0, 1] * (tv - cv[2])
    bz = Ai[1, 0] * (tu - cu[2]) + Ai[1, 1] * (tv - cv[2])
    ring = (np.hypot(bx, bz) > outer - JOIN_BAND - 10) & (np.hypot(bx, bz) < reach)
    gi = np.clip(np.floor(bz + n / 2).astype(int), 0, n - 1)
    gj = np.clip(np.floor(bx + n / 2).astype(int), 0, n - 1)
    bown = _near(img, bcol)
    mpp = 1.0 / (math.hypot(cu[0], cu[1]) * w)
    bgap = binary_opening(W[gi, gj] & ring & ~bown, iterations=max(1, int(round(WATER_MIN / mpp))))
    print("%s: backdrop bake %.0f-%.0f m: %d m2 of Overture's water painted as land now water %s" % (
        slug, outer - JOIN_BAND - 10, reach, int(bgap.sum() * mpp * mpp), list(map(int, bcol))))
    if not bgap.any():
        return
    img[bgap] = bcol
    g.set_image(img)
    Pg = g.attr("POSITION")
    UVg = g.attr("TEXCOORD_0")
    c = np.clip((UVg[:, 0] * w).astype(int), 0, w - 1)
    r_ = np.clip((UVg[:, 1] * h).astype(int), 0, h - 1)
    was = bown[r_, c] & (np.hypot(Pg[:, 0], Pg[:, 2]) > outer)
    now = bgap[r_, c]
    if was.sum() > 20 and now.any():
        level = float(np.median(Pg[was, 1]))
        Pg[now, 1] = level
        g.set_attr("POSITION", Pg)
        if "NORMAL" in g.pr["attributes"]:
            N = g.attr("NORMAL")
            N[now] = (0.0, 1.0, 0.0)
            g.set_attr("NORMAL", N)
        print("%s: %d ground vertices under the new water laid flat at its water's level %.2f m" % (
            slug, int(now.sum()), level))
    g.save()


def ground_field(slug, size, span, gain=1.0, smooth_m=GROUND_SMOOTH):
    """The backdrop's open-ground colour under a surrounds map `span` m a side at `size` px (rows north to south, as
    the map): its near-ground bake (painted from the same map data, scene/prep.py), with roads and roofs taken out by
    a median over `smooth_m` m, and the map's `tint` and the `gain` its surrounds.py puts on
    the whole map afterwards taken out, so it draws as the backdrop draws it. 8-bit sRGB, for a surrounds.py to paint
    its unmapped land with instead of a made-up mottle."""
    from scipy.ndimage import median_filter
    _, outer, tint = surrounds(slug)
    P, UV, B = near_bake(slug)
    cu, cv, _, _ = plan_fit(P, UV, outer - 50, outer + 300)
    h, w = B.shape[:2]
    mpp = 1.0 / (math.hypot(cu[0], cu[1]) * w)                # the bake's metres a pixel
    k = max(1, int(round(GROUND_CELL / mpp)))
    small = B[:h // k * k, :w // k * k].reshape(h // k, k, w // k, k, 3).mean((1, 3))
    small = median_filter(small, size=(max(3, int(round(smooth_m / (k * mpp))) | 1), ) * 2 + (1,))
    small = np.repeat(np.repeat(small, k, 0), k, 1)             # back to the bake's grid for `sample`
    x = ((np.arange(size) + 0.5) / size - 0.5) * span
    X, Z = np.meshgrid(x, x)
    return srgb8(sample(small, cu[0] * X + cu[1] * Z + cu[2], cv[0] * X + cv[1] * Z + cv[2]) / (tint * gain))


def apply(slug):
    span, outer, tint = surrounds(slug)
    if outer > span / 2:
        raise RuntimeError("%s: the join (%.0f m) lies past the map's own half-span (%.0f m); a band painted into "
                           "the map cannot reach it" % (slug, outer, span / 2))
    path = os.path.join(ROOT, "assets", "grounds", slug, "surrounds.webp")
    rec = os.path.join(ROOT, "assets", "grounds", slug, "surrounds_join.json")
    if os.path.exists(rec) and json.load(open(rec)).get("written") == sha(path):
        print("%s: band already painted into this map (surrounds_join.json); left alone" % slug)
        return
    P, UV, B = near_bake(slug)
    cu, cv, err, err99 = plan_fit(P, UV, outer - 50, outer + 300)
    S8 = np.asarray(Image.open(path).convert("RGB"))
    S = lin(S8)
    h, w = S.shape[:2]
    # each texel's centre in model metres (u = x / span + 0.5, as GroundModels._ring_mesh lays the map)
    x = ((np.arange(w) + 0.5) / w - 0.5) * span
    z = ((np.arange(h) + 0.5) / h - 0.5) * span
    X, Z = np.meshgrid(x, z)
    r = np.hypot(X, Z)
    band = r > outer - JOIN_BAND
    t = np.clip((r[band] - (outer - JOIN_BAND)) / JOIN_BAND, 0.0, 1.0)
    wgt = (t * t * (3 - 2 * t))[:, None]
    u = cu[0] * X[band] + cu[1] * Z[band] + cu[2]
    v = cv[0] * X[band] + cv[1] * Z[band] + cv[2]
    target = sample(B, u, v) / tint            # the backdrop's drawn colour, before this map's tint
    out = S.copy()
    out[band] = S[band] * (1 - wgt) + target * wgt
    O8 = S8.copy()
    O8[band] = srgb8(out[band])
    src = sha(path)
    # lossless, so the map inside the band stays exactly as its surrounds.py wrote it (a second lossy pass moved
    # texels by up to 26 levels; Godot imports these maps lossless, so the file size is the private repo's only)
    Image.fromarray(O8).save(path, lossless=True, method=4)
    json.dump({"ground": slug, "band_m": JOIN_BAND, "outer_m": outer, "span_m": span, "tint": tint.tolist(),
               "bake_fit_median_uv": err, "bake_fit_p99_uv": err99, "source": src, "written": sha(path),
               "texels_painted": int(band.sum())}, open(rec, "w"), indent=1)
    print("%s: painted the outer %.0f m (%d texels) toward the backdrop's bake; bake mapping fit median %.2g, p99 %.2g "
          "(uv)" % (slug, JOIN_BAND, int(band.sum()), err, err99))


def check(slug, path=None):
    """The step a top view sees at the join: the surrounds map as drawn JOIN_EDGE m inside it against the
    backdrop's bake JOIN_EDGE m outside it, averaged along JOIN_WINDOW m of arc, 144 spots round it. Returns the
    median summed linear step. `path` checks another copy of the surrounds map (a before)."""
    span, outer, tint = surrounds(slug)
    P, UV, B = near_bake(slug)
    cu, cv, _, _ = plan_fit(P, UV, outer - 50, outer + 300)
    path = path or os.path.join(ROOT, "assets", "grounds", slug, "surrounds.webp")
    S = lin(np.asarray(Image.open(path).convert("RGB")))
    steps, ratios = [], []
    k = np.linspace(-JOIN_WINDOW, JOIN_WINDOW, 7)
    for a in np.arange(0.0, 360.0, 2.5):
        th = math.radians(a)
        dx, dz = math.sin(th), -math.cos(th)
        tx, tz = -dz * k, dx * k                       # along the arc
        ri, ro = outer - JOIN_EDGE, outer + JOIN_EDGE
        si = sample(S, (ri * dx + tx) / span + 0.5, (ri * dz + tz) / span + 0.5).mean(0) * tint
        X, Z = ro * dx + tx, ro * dz + tz
        bo = sample(B, cu[0] * X + cu[1] * Z + cu[2], cv[0] * X + cv[1] * Z + cv[2]).mean(0)
        steps.append(float(np.abs(si - bo).sum()))
        ratios.append(float(bo.mean() / max(si.mean(), 1e-4)))
    med = float(np.median(steps))
    print("%s: step at the join %.3f median (p90 %.3f), outer/inner brightness %.3f median (p10 %.3f, p90 %.3f)" % (
        slug, med, np.percentile(steps, 90), np.median(ratios), np.percentile(ratios, 10), np.percentile(ratios, 90)))
    return med


if __name__ == "__main__":
    cmd, slugs = sys.argv[1], sys.argv[2:]
    if cmd == "apply":
        for s in slugs:
            rec = os.path.join(ROOT, "assets", "grounds", s, "surrounds_join.json")
            if not (os.path.exists(rec) and json.load(open(rec)).get("written") == sha(
                    os.path.join(ROOT, "assets", "grounds", s, "surrounds.webp"))):
                water(s)
            apply(s)
    elif cmd == "check":
        before = os.environ.get("JOIN_BEFORE")   # a folder holding <slug>/surrounds.webp as it was
        if before:
            for s in slugs:
                print("before:", end=" ")
                check(s, os.path.join(before, s, "surrounds.webp"))
        bad = [s for s in slugs if check(s) > JOIN_MAX_STEP]
        if bad:
            print("step over %.2f at: %s" % (JOIN_MAX_STEP, ", ".join(bad)))
            sys.exit(1)
    else:
        raise SystemExit(__doc__)
