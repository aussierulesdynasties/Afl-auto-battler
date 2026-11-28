"""Stand a finished backdrop on the same measured land as the game's own ring round the ground (row 202 2b).

    python3 reland.py <slug> [part1.glb part2.glb ...]     (default: assets/grounds/<slug>/<slug>_backdrop_part*.glb)

Why. The backdrops built before the terrain tool (#2072) stand on the scene's own land (AWS Terrarium, flattened
round the ground, the turf at y 0), while a ground whose ring follows the land (GroundModels.SURROUNDS
"follow_land") draws the land from terrain.bin (Geoscience Australia 5 m LiDAR, tools/grounds/terrain) at the
model's arena floor. At Marvel the two disagreed by 10 to 15 m round most of the 1,024 m seam and stood 18 m
the other way to the north-west: from the aerial orbit the ring's edge read as a raised grey plateau with
stair-stepped sides, and the backdrop's streets and towers sat in a trench past it (2026-11-27).

What it does, in place, to every backdrop part (positions only; nothing is added, dropped or re-coloured):
- the old land is the backdrop's own ground (bg_near_ground, then bg_far_terrain past it); the new land is
  terrain.bin read the way GroundTerrain.gd reads it (floor_y + the grid), so the seam meets the ring exactly;
  past terrain.bin's coarse grid (3 km) the far terrain moves by the median shift of its last 500 m;
- ground-hugging meshes (ground, roads, kerbs, lines, rails, car parks, platforms) take the new land under
  every vertex, keeping their height above the old land;
- every building moves as one piece, so its roof stays level: its walls' foot goes to the lowest new land
  along its foot, sunk as deep below it as it was below the old but never over SINK_MAX (a wall never hangs on
  the low side, and the building keeps its measured height); a part
  standing on another (a tower on its podium) rides with it; roofs, parapets and roof plant move with the
  building whose outline holds them;
- everything else (trees, cars, masts, bridges) moves as one piece per connected part, by the shift under it;
- open water (bg_water) moves as one flat sheet to the ring's water level (the LiDAR's water surface), and the
  land and anything the scene stood below its water keep their depth under it; a sheet that is only scattered
  pieces (more than SCATTERED) leaves the scene, as the ground's texture already paints that water.
- the flat overlays (roads, lines, kerbs, paving, rails) are then laid on the near ground's own triangles
  (lay_overlays), and any overlay lying on the painted water, not on a deck, is left out.
Run it once on the scene's own export, then `tools/ground_assets.sh publish`. It is not to be run twice: the old
land it reads the second time is the new land read across its corners, not the measured land under them, and things
move by up to a few metres (measured 2026-11-28). On a backdrop already relanded, `reland.py <slug> --overlays-only
[glbs]` lays its overlays again and nothing else; the water's tone is never applied twice (tone_painted_water), and
the image it replaces leaves the file (Glb.compact).
"""
import json
import math
import os
import struct
import sys

import numpy as np
from scipy.interpolate import LinearNDInterpolator, NearestNDInterpolator
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}
GROUND_KEYS = ("near_ground", "roads", "road_lines", "kerbs", "rails", "rail_bed", "platforms", "carparks",
               "paved", "oval_lines", "paths", "ground")
FAR, WATER = "bg_far_terrain", "bg_water"
# A building's foot stays at most this far under the lowest land along it (the old scene sank some 3 to 5 m into
# its bumps, which took that much off their measured height).
SINK_MAX = 0.3
# A water sheet in more separate pieces than this is only scattered fragments over the painted water: left out.
SCATTERED = 100
# A ground's painted water brought to this colour (sRGB, on average), so the harbour draws in one colour with the
# surrounds map's water across the backdrop's cut. Marvel's is fitted to renders (2026-11-27): its painted water
# (51, 74, 84) drew (50, 88, 105) beside the surrounds' (45, 79, 98) and (28, 56, 67) drew (21, 68, 88), and the
# straight line through the two (linear light) meets the surrounds at (47, 66, 77). The two layers are lit apart.
WATER_TARGET = {"marvel": (47, 66, 77)}
# The flat overlays (roads, their lines, kerbs, paving, rails) are laid on the near ground's own triangles, this far
# over them. Laid on the measured land under each of their vertices instead, they ran up to half a metre over and
# under the ground's 30 m triangles between its corners and broke into dashes from the orbit (review, 2026-11-28).
OVERLAY_LIFT = (("road_lines", 0.30), ("oval_lines", 0.30), ("rails", 0.30), ("kerbs", 0.22), ("rail_bed", 0.18),
                ("roads", 0.18), ("carparks", 0.15), ("paved", 0.15), ("paths", 0.15))
OVERLAY_RAISED = 2.5   # m: a vertex this far over the ground is on a deck (a bridge, a ramp) and stays where it is


def fit(slug):
    """GroundModels.FIT[slug]: [centre x, centre z, arena floor y, ...] read from the game's own source."""
    src = open(os.path.join(ROOT, "scripts", "ui", "match", "GroundModels.gd")).read()
    i = src.index('"%s": [' % slug, src.index("const FIT :="))
    return [float(v) for v in src[src.index("[", i) + 1:src.index("]", i)].split(",")]


def surrounds_outer(slug):
    """GroundModels.SURROUNDS[slug]["outer"] (where the background scene takes over from the ring) plus the ring's
    skirt past it (RING_SKIRT: [reach, drop]), read from the game's own source: (outer, skirt reach, skirt drop)."""
    src = open(os.path.join(ROOT, "scripts", "ui", "match", "GroundModels.gd")).read()
    i = src.index('"%s": {' % slug, src.index("const SURROUNDS :="))
    depth, j = 0, src.index("{", i)
    for j in range(j, len(src)):
        depth += {"{": 1, "}": -1}.get(src[j], 0)
        if depth == 0:
            break
    block = src[i:j]
    k = block.index('"outer":')
    outer = float(block[k + 8:].split(",")[0].split("}")[0])
    sk = src[src.index("const RING_SKIRT := [") + 21:]
    reach, drop = (float(v) for v in sk[:sk.index("]")].split(","))
    return outer, reach, drop


class Land:
    """GroundTerrain.gd in Python: terrain.bin's fine and coarse grids, y in the model's frame."""

    def __init__(self, slug):
        b = open(os.path.join(ROOT, "assets", "grounds", slug, "terrain.bin"), "rb").read()
        head = np.frombuffer(b[:32], "<f4")
        nf, nc = int(head[2]), int(head[5])
        self.fine = (float(head[0]), float(head[1]), nf, np.frombuffer(b, "<i2", nf * nf, 32).reshape(nf, nf))
        self.coarse = (float(head[3]), float(head[4]), nc, np.frombuffer(b, "<i2", nc * nc, 32 + 2 * nf * nf).reshape(nc, nc))
        f = fit(slug)
        self.cx, self.cz, self.floor = f[0], f[1], f[2]

    @staticmethod
    def _sample(g, e, n):
        half, step, cells, h = g
        px = np.clip((e + half) / step, 0.0, cells - 1.001)
        py = np.clip((n + half) / step, 0.0, cells - 1.001)
        i, j = px.astype(int), py.astype(int)
        fx, fy = px - i, py - j
        return (h[j, i] * (1 - fx) * (1 - fy) + h[j, i + 1] * fx * (1 - fy) + h[j + 1, i] * (1 - fx) * fy
                + h[j + 1, i + 1] * fx * fy)

    def height(self, x, z):
        e, n = np.asarray(x, float) - self.cx, -(np.asarray(z, float) - self.cz)
        fine = np.maximum(np.abs(e), np.abs(n)) < self.fine[0] - self.fine[1]
        return self.floor + 0.01 * np.where(fine, self._sample(self.fine, e, n), self._sample(self.coarse, e, n))

    def reach(self):
        return self.coarse[0]


class Glb:
    def __init__(self, path):
        self.path = path
        raw = open(path, "rb").read()
        jl = struct.unpack("<I", raw[12:16])[0]
        self.J = json.loads(raw[20:20 + jl])
        bl = struct.unpack("<I", raw[20 + jl:24 + jl])[0]
        self.head, self.bin = raw[:20 + jl + 8], bytearray(raw[28 + jl:28 + jl + bl])
        self.tail = raw[28 + jl + bl:]
        for n in self.J["nodes"]:
            if "mesh" in n and any(k in n for k in ("matrix", "translation", "rotation", "scale")):
                raise RuntimeError("%s: a mesh node with a transform" % path)
        self.name_of = {n["mesh"]: n.get("name", "") for n in self.J["nodes"] if "mesh" in n}
        seen = {}
        self.prims = []   # (mesh name, position accessor, indices accessor)
        for mi, m in enumerate(self.J["meshes"]):
            for p in m["primitives"]:
                a = p["attributes"]["POSITION"]
                if a in seen:
                    raise RuntimeError("%s: position accessor shared by two meshes" % path)
                seen[a] = mi
                self.prims.append((self.name_of.get(mi, m.get("name", "")), a, p.get("indices")))

    def read(self, ai):
        a = self.J["accessors"][ai]
        v = self.J["bufferViews"][a["bufferView"]]
        dt = np.dtype(CT[a["componentType"]])
        n = NC[a["type"]]
        if v.get("byteStride", dt.itemsize * n) != dt.itemsize * n:
            raise RuntimeError("accessor %d: interleaved buffer view" % ai)
        off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        return np.frombuffer(bytes(self.bin), dt, a["count"] * n, off).reshape(a["count"], n).copy()

    def write_pos(self, ai, P):
        a = self.J["accessors"][ai]
        if a["componentType"] != 5126 or a["type"] != "VEC3":
            raise RuntimeError("accessor %d: not float VEC3" % ai)
        v = self.J["bufferViews"][a["bufferView"]]
        off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        b = np.ascontiguousarray(P, "<f4").tobytes()
        self.bin[off:off + len(b)] = b
        a["min"] = [float(x) for x in P.min(0)]
        a["max"] = [float(x) for x in P.max(0)]

    def write_vec3(self, ai, V):
        a = self.J["accessors"][ai]
        if a["componentType"] != 5126 or a["type"] != "VEC3":
            raise RuntimeError("accessor %d: not float VEC3" % ai)
        v = self.J["bufferViews"][a["bufferView"]]
        off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        b = np.ascontiguousarray(V, "<f4").tobytes()
        self.bin[off:off + len(b)] = b

    def write_idx(self, ai, F):
        a = self.J["accessors"][ai]
        v = self.J["bufferViews"][a["bufferView"]]
        off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        b = np.ascontiguousarray(F, CT[a["componentType"]]).tobytes()
        if len(b) != a["count"] * np.dtype(CT[a["componentType"]]).itemsize:
            raise RuntimeError("accessor %d: %d indices written over %d" % (ai, len(b) // np.dtype(CT[a["componentType"]]).itemsize, a["count"]))
        self.bin[off:off + len(b)] = b

    def compact(self):
        """Drop buffer views nothing refers to (an image replaced by tone_painted_water) and close the gaps."""
        J = self.J
        # accessors no mesh uses (reduce.py leaves some, pointing past the last buffer view) leave too
        refs = set()
        for m in J["meshes"]:
            for pr in m["primitives"]:
                refs |= set(pr["attributes"].values())
                refs |= {pr["indices"]} if "indices" in pr else set()
                for tg in pr.get("targets", []):
                    refs |= set(tg.values())
        if J.get("skins") or J.get("animations"):
            raise RuntimeError("compact() knows meshes only")
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
        self.prims = [(n, amap[a], None if i is None else amap[i]) for n, a, i in self.prims]
        used = sorted({a["bufferView"] for a in J["accessors"] if "bufferView" in a}
                      | {im["bufferView"] for im in J.get("images", []) if "bufferView" in im})
        new, remap = bytearray(), {}
        views = []
        for k in used:
            v = dict(J["bufferViews"][k])
            new += b"\0" * (-len(new) % 4)
            off = v.get("byteOffset", 0)
            chunk = self.bin[off:off + v["byteLength"]]
            v["byteOffset"] = len(new)
            new += chunk
            remap[k] = len(views)
            views.append(v)
        for a in J["accessors"]:
            if "bufferView" in a:
                a["bufferView"] = remap[a["bufferView"]]
        for im in J.get("images", []):
            if "bufferView" in im:
                im["bufferView"] = remap[im["bufferView"]]
        dropped = len(self.bin) - len(new)
        J["bufferViews"] = views
        self.bin = new
        J["buffers"][0]["byteLength"] = len(new)
        return dropped

    def save(self):
        self.compact()
        js = json.dumps(self.J, separators=(",", ":")).encode()
        js += b" " * (-len(js) % 4)
        body = bytes(self.bin) + b"\0" * (-len(self.bin) % 4)
        blob = (struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(body)) + struct.pack("<II", len(js), 0x4E4F534A)
                + js + struct.pack("<II", len(body), 0x004E4942) + body)
        open(self.path, "wb").write(blob)


def _ground_texture(g, pr):
    """The ground primitive's base colour image: (image index, RGB array 0-255), or None."""
    import io
    from PIL import Image
    J = g.J
    bt = J["materials"][pr["material"]].get("pbrMetallicRoughness", {}).get("baseColorTexture")
    if bt is None:
        return None
    tx = J["textures"][bt["index"]]
    ii = tx["source"] if "source" in tx else next(iter(tx["extensions"].values()))["source"]
    bv = J["bufferViews"][J["images"][ii]["bufferView"]]
    off = bv.get("byteOffset", 0)
    return ii, np.asarray(Image.open(io.BytesIO(bytes(g.bin[off:off + bv["byteLength"]]))).convert("RGB"), float)


def _water_texels(img):
    """The scene's harbour and river blue in its ground texture."""
    return (img[..., 2] - img[..., 0] > 22) & (img[..., 1] - img[..., 0] > 12) & (img.max(-1) < 120)


def _lin(c):
    c = np.asarray(c, float) / 255
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def tone_painted_water(g, target):
    """Bring the ground texture's painted water to `target` (sRGB) on average, scaling it in linear light so its
    small grain stays: it then meets the surrounds' water in one colour at the seam. The new image goes on the end of
    the buffer and the old one's bytes leave it when the file is saved (Glb.compact). A second run finds the water
    already toned and leaves it."""
    import io
    from PIL import Image
    done = set()
    for mi, m in enumerate(g.J["meshes"]):
        if not g.name_of.get(mi, m.get("name", "")).startswith("bg_near_ground"):
            continue
        for pr in m["primitives"]:
            got = _ground_texture(g, pr)
            if got is None or got[0] in done:
                continue
            ii, img = got
            done.add(ii)
            w = _water_texels(img)
            if not w.any() or np.abs(img[w].mean(0) - target).max() < 1.5:
                continue   # none, or already toned (a second run)
            lin = _lin(img)
            gain = _lin(target) / lin[w].mean(0)
            lin[w] = np.clip(lin[w] * gain, 0, 1)
            out = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * np.power(lin, 1 / 2.4) - 0.055) * 255
            b = io.BytesIO()
            mime = g.J["images"][ii].get("mimeType", "image/webp")
            Image.fromarray(np.clip(out + 0.5, 0, 255).astype(np.uint8)).save(
                b, "WEBP" if "webp" in mime else "PNG", **({"quality": 92, "method": 6} if "webp" in mime else {}))
            g.bin += b"\0" * (-len(g.bin) % 4)
            g.J["bufferViews"].append({"buffer": 0, "byteOffset": len(g.bin), "byteLength": len(b.getvalue())})
            g.bin += b.getvalue()
            g.J["buffers"][0]["byteLength"] = len(g.bin)
            g.J["images"][ii]["bufferView"] = len(g.J["bufferViews"]) - 1
            # a new name: Godot keeps an image it once wrote out beside the model (<model>_<image>.webp) and drew
            # that stale copy, not the toned one, after the model changed
            import re
            import zlib
            base = re.sub(r"(_toned)+(_[0-9a-f]{8})?$", "", g.J["images"][ii].get("name", "ground"))
            g.J["images"][ii]["name"] = "%s_toned_%08x" % (base, zlib.crc32(b.getvalue()))
            print("%s: painted water %s brought to %s (%d texels)" % (
                os.path.basename(g.path), img[w].mean(0).round().astype(int).tolist(), list(target), int(w.sum())))


def flatten_painted_water(g, level):
    """Lay the ground flat at the water's level wherever its own texture paints open water (the scene's harbour and
    river blue): the scene's ground there wandered half a metre round the old sheet and fell into 15 m pits by the
    bridges, which read as dark holes and a step at the seams once the scattered sheet is gone. The count."""
    import io
    from PIL import Image
    n = 0
    J = g.J
    for mi, m in enumerate(J["meshes"]):
        if not g.name_of.get(mi, m.get("name", "")).startswith("bg_near_ground"):
            continue
        for pr in m["primitives"]:
            mat = J["materials"][pr["material"]]
            bt = mat.get("pbrMetallicRoughness", {}).get("baseColorTexture")
            if bt is None or "TEXCOORD_0" not in pr["attributes"]:
                continue
            tx = J["textures"][bt["index"]]
            im = J["images"][tx["source"] if "source" in tx else next(iter(tx["extensions"].values()))["source"]]
            bv = J["bufferViews"][im["bufferView"]]
            off = bv.get("byteOffset", 0)
            img = np.asarray(Image.open(io.BytesIO(bytes(g.bin[off:off + bv["byteLength"]]))).convert("RGB"), float)
            h, w = img.shape[:2]
            UV = g.read(pr["attributes"]["TEXCOORD_0"])
            P = g.read(pr["attributes"]["POSITION"]).astype(np.float64)
            c = np.clip((UV[:, 0] * w).astype(int), 1, w - 2)
            r = np.clip((UV[:, 1] * h).astype(int), 1, h - 2)
            tex = sum(img[r + dr, c + dc] for dr in (-1, 0, 1) for dc in (-1, 0, 1)) / 9
            water = (tex[:, 2] - tex[:, 0] > 22) & (tex[:, 1] - tex[:, 0] > 12) & (tex.max(1) < 120)
            P[water, 1] = level
            n += int(water.sum())
            g.write_pos(pr["attributes"]["POSITION"], P.astype(np.float32))
            if "NORMAL" in pr["attributes"]:   # level water faces straight up: its old normals lit it in blotches
                N = g.read(pr["attributes"]["NORMAL"])
                N[water] = (0.0, 1.0, 0.0)
                g.write_vec3(pr["attributes"]["NORMAL"], N.astype(np.float32))
    return n


def drop_scattered_water(g):
    """Leave out a water sheet that is only scattered pieces. Marvel's bg_water was 2,181 triangles in 900 separate
    pieces (62,000 m2 of the river and harbour's bed): the ground's own texture paints the water there, and the
    pieces over it read from the orbit as a speckle of triangles. The mesh stays in the file (horizon.py reads its
    level); only its node leaves the scene."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    for ni, n in enumerate(g.J["nodes"]):
        if "mesh" not in n or g.name_of.get(n["mesh"]) != WATER:
            continue
        pieces = 0
        for name, a, ia in g.prims:
            if name == WATER:
                P = g.read(a)
                I = g.read(ia).reshape(-1, 3).astype(np.int64) if ia is not None else np.arange(len(P)).reshape(-1, 3)
                u = unary_union([Polygon(P[t][:, [0, 2]]).buffer(0.01) for t in I])
                pieces += len(getattr(u, "geoms", [u]))
        if pieces > SCATTERED:
            for sc in g.J["scenes"]:
                sc["nodes"] = [k for k in sc["nodes"] if k != ni]
            for m in g.J["nodes"]:
                if "children" in m:
                    m["children"] = [k for k in m["children"] if k != ni]
            print("%s: open water in %d separate pieces, left out (the ground's texture paints it)" % (
                os.path.basename(g.path), pieces))


def mesh_surface(P, I, step=1.0):
    """A sampler of a triangle mesh's own surface (its triangles, not a re-triangulation of its corners):
    at(x, z) -> (y, triangle index), nan and -1 off the mesh."""
    x0, z0 = P[:, 0].min() - step, P[:, 2].min() - step
    nx, nz = int((P[:, 0].max() - x0) / step) + 2, int((P[:, 2].max() - z0) / step) + 2
    tid = -np.ones((nx, nz), np.int64)
    A, B, C = P[I[:, 0]], P[I[:, 1]], P[I[:, 2]]
    for t in range(len(I)):
        q = np.array([A[t], B[t], C[t]])[:, [0, 2]]
        i0, j0 = np.floor((q.min(0) - (x0, z0)) / step).astype(int)
        i1, j1 = np.ceil((q.max(0) - (x0, z0)) / step).astype(int)
        gx, gz = np.meshgrid(x0 + (np.arange(i0, i1 + 1) + 0.5) * step, z0 + (np.arange(j0, j1 + 1) + 0.5) * step,
                             indexing="ij")
        a, b, c = q
        den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(den) < 1e-9:
            continue
        l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gz - c[1])) / den
        l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gz - c[1])) / den
        sub = tid[i0:i1 + 1, j0:j1 + 1]
        sub[(l1 >= -0.02) & (l2 >= -0.02) & (1 - l1 - l2 >= -0.02)] = t

    def at(x, z):
        """A cell holds one triangle, the last drawn over its middle: a point near the cell's edge may lie in a
        neighbour's, so the cell's own triangle and then its 8 neighbours' are tried, and the first that holds the
        point (to 1 cm) gives its height."""
        x, z = np.atleast_1d(np.asarray(x, float)), np.atleast_1d(np.asarray(z, float))
        ci = ((x - x0) / step).astype(int)
        cj = ((z - z0) / step).astype(int)
        y = np.full(len(x), np.nan)
        tri = -np.ones(len(x), np.int64)
        todo = np.ones(len(x), bool)
        for di, dj in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]:
            k = np.nonzero(todo)[0]
            if not len(k):
                break
            t = tid[np.clip(ci[k] + di, 0, nx - 1), np.clip(cj[k] + dj, 0, nz - 1)]
            tt = np.maximum(t, 0)
            a, b, c = A[tt], B[tt], C[tt]
            den = (b[:, 2] - c[:, 2]) * (a[:, 0] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (a[:, 2] - c[:, 2])
            den = np.where(np.abs(den) < 1e-9, 1e-9, den)
            l1 = ((b[:, 2] - c[:, 2]) * (x[k] - c[:, 0]) + (c[:, 0] - b[:, 0]) * (z[k] - c[:, 2])) / den
            l2 = ((c[:, 2] - a[:, 2]) * (x[k] - c[:, 0]) + (a[:, 0] - c[:, 0]) * (z[k] - c[:, 2])) / den
            l3 = 1 - l1 - l2
            # inside to 1 cm along the triangle's own size
            tol = 0.01 / np.maximum(np.sqrt(np.abs(den)), 1e-6)
            ok = (t >= 0) & (l1 >= -tol) & (l2 >= -tol) & (l3 >= -tol)
            y[k[ok]] = (l1 * a[:, 1] + l2 * b[:, 1] + l3 * c[:, 1])[ok]
            tri[k[ok]] = t[ok]
            todo[k[ok]] = False
        return y, tri
    return at


def lay_overlays(glbs, level):
    """Lay the flat overlays on the near ground's own surface (OVERLAY_LIFT over it), and leave out any overlay
    triangle lying wholly on the painted water (not on a deck): a guard; at Marvel none does (2026-11-28; the white
    line the review saw on its harbour was the sky through the step at the ring's edge, horizon.near_water). A count
    per layer."""
    P, I, n = [], [], 0
    for g in glbs:
        for name, a, ia in g.prims:
            if name.startswith("bg_near_ground") and ia is not None:
                P.append(g.read(a).astype(np.float64))
                I.append(g.read(ia).reshape(-1, 3).astype(np.int64) + n)
                n += len(P[-1])
    if not P:
        return {}
    P, I = np.vstack(P), np.vstack(I)
    at = mesh_surface(P, I)
    wet_tri = (np.abs(P[I][:, :, 1] - level) < 0.01).all(1) if level is not None else np.zeros(len(I), bool)
    out = {}
    for g in glbs:
        for name, a, ia in g.prims:
            lift = next((v for k, v in OVERLAY_LIFT if k in name), None)
            if lift is None or name.startswith("bg_near_ground") or name == FAR:
                continue
            V = g.read(a).astype(np.float64)
            y, t = at(V[:, 0], V[:, 2])
            lay = ~np.isnan(y) & (V[:, 1] - np.nan_to_num(y) < OVERLAY_RAISED)
            V[lay, 1] = y[lay] + lift
            g.write_pos(a, V.astype(np.float32))
            gone = 0
            if ia is not None:
                F = g.read(ia).reshape(-1, 3)
                on_water = (lay[F] & wet_tri[np.maximum(t[F], 0)] & (t[F] >= 0)).all(1)
                if on_water.any():
                    F = F.copy()
                    F[on_water] = F[on_water][:, :1]   # degenerate: drawn as nothing
                    g.write_idx(ia, F.ravel())
                    gone = int(on_water.sum())
            r = out.setdefault(name, [0, 0, 0])
            r[0] += int(lay.sum()); r[1] += int((~lay).sum()); r[2] += gone
    return out


def components(P, I):
    """Connected parts of a triangle mesh (vertices welded at 5 cm): a label per triangle."""
    key = np.round(P * 20).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.ravel()
    T = inv[I]
    n = int(inv.max()) + 1
    r = np.r_[T[:, 0], T[:, 1]]
    c = np.r_[T[:, 1], T[:, 2]]
    k, lab = connected_components(coo_matrix((np.ones(len(r)), (r, c)), shape=(n, n)), directed=False)
    return k, lab[T[:, 0]]


def is_ground(name):
    return name != FAR and any(k in name for k in GROUND_KEYS)


def main():
    args = sys.argv[1:]
    overlays_only = "--overlays-only" in args
    args = [a for a in args if a != "--overlays-only"]
    slug = args[0]
    paths = args[1:] or sorted(
        os.path.join(ROOT, "assets", "grounds", slug, f) for f in os.listdir(os.path.join(ROOT, "assets", "grounds", slug))
        if f.startswith(slug + "_backdrop_part") and f.endswith(".glb"))
    land = Land(slug)
    glbs = [Glb(p) for p in paths]
    if overlays_only:
        # a backdrop already relanded: only lay its overlays again (lay_overlays) at its water's level
        wat = [g.read(a) for g in glbs for name, a, _ in g.prims if name == WATER]
        laid = lay_overlays(glbs, float(np.median(np.vstack(wat)[:, 1])) if wat else None)
        for name, (n_laid, n_deck, n_gone) in sorted(laid.items()):
            print("%-16s %7d vertices laid on the ground, %6d on decks left, %5d triangles on open water left out" % (
                name, n_laid, n_deck, n_gone))
        for g in glbs:
            g.save()
        return
    # The old land: the backdrop's own near ground, then its far terrain where the near ground has none.
    pts = []
    for g in glbs:
        for name, a, _ in g.prims:
            if name.startswith("bg_near_ground"):
                pts.append(g.read(a))
    near = np.vstack(pts)
    far = np.vstack([g.read(a) for g in glbs for name, a, _ in g.prims if name == FAR])
    _, u = np.unique(np.round(near[:, [0, 2]] * 2), axis=0, return_index=True)
    near = near[u]
    old_near = LinearNDInterpolator(near[:, [0, 2]], near[:, 1])
    old_far = LinearNDInterpolator(far[:, [0, 2]], far[:, 1])
    old_any = NearestNDInterpolator(np.r_[near[:, [0, 2]], far[:, [0, 2]]], np.r_[near[:, 1], far[:, 1]])

    def old(x, z):
        y = old_near(x, z)
        y = np.where(np.isnan(y), old_far(x, z), y)
        return np.where(np.isnan(y), old_any(x, z), y)

    reach = land.reach()
    sq = np.maximum(np.abs(far[:, 0] - land.cx), np.abs(far[:, 2] - land.cz))   # terrain.bin's square is on FIT's centre
    ring = far[(sq > reach - 500) & (sq < reach - 20)]
    far_shift = float(np.median(land.height(ring[:, 0], ring[:, 2]) - ring[:, 1])) if len(ring) else 0.0

    def shift(x, z):
        """New land minus old under (x, z); past terrain.bin's coarse grid, the far ring's median."""
        x, z = np.asarray(x, float), np.asarray(z, float)
        inside = np.maximum(np.abs(x - land.cx), np.abs(z - land.cz)) < reach - 20
        return np.where(inside, land.height(x, z) - old(x, z), far_shift)

    # Buildings: one shift each, from the walls' foot. Their outlines (convex hulls of the foot) own the roofs.
    # Buildings: one shift each, from the walls' foot. A building standing on the land goes to the lowest new land
    # along its foot, sunk as deep under it as it was under the old, to SINK_MAX (the old land read rooftops and noise as hills,
    # so keeping its old height above the old land would leave it floating). A part standing on another (a tower on
    # its podium: its foot over 2 m above the land, inside a bigger building's outline) moves with that building.
    # Their outlines (convex hulls) then own the roofs, parapets and plant.
    from matplotlib.path import Path
    from scipy.spatial import ConvexHull
    parts = []   # [hull path, area, y0, foot xz, free shift, raised]
    for g in glbs:
        for name, a, ia in g.prims:
            if not name.startswith("bg_bld_") or ia is None:
                continue
            P = g.read(a).astype(np.float64)
            I = g.read(ia).reshape(-1, 3).astype(np.int64)
            k, lab = components(P, I)
            for c in range(k):
                V = P[np.unique(I[lab == c])]
                y0 = V[:, 1].min()
                foot = V[V[:, 1] < y0 + 0.3][:, [0, 2]]
                if len(foot) < 3:
                    foot = V[:, [0, 2]]
                o, nw = old(foot[:, 0], foot[:, 1]), land.height(foot[:, 0], foot[:, 1])
                inside = np.maximum(np.abs(foot[:, 0] - land.cx), np.abs(foot[:, 1] - land.cz)).max() < reach - 20
                sink = min(SINK_MAX, max(0.0, float(o.min()) - y0))
                free = (float(nw.min()) - sink - y0) if inside else far_shift
                try:
                    h = ConvexHull(V[:, [0, 2]])
                    path, area = Path(V[:, [0, 2]][h.vertices]), h.volume
                except Exception:
                    path, area = Path(V[:, [0, 2]][[0, 1, 2]]), 0.0
                parts.append([path, area, y0, foot, free, y0 > float(o.min()) + 2.0])
    parts.sort(key=lambda t: -t[1])   # large first
    owners = []
    for i, (path, area, y0, foot, free, raised) in enumerate(parts):
        s = free
        if raised:   # on top of a bigger building already placed: ride with it
            for j in range(i - 1, -1, -1):
                if parts[j][1] > area and parts[j][0].contains_points(foot, radius=0.6).mean() > 0.6:
                    s = owners[j][1]
                    break
        owners.append((path, s, area))
    lo = np.array([o[0].vertices.min(0) for o in owners]) if owners else np.zeros((0, 2))
    hi = np.array([o[0].vertices.max(0) for o in owners]) if owners else np.zeros((0, 2))

    def owner_shift(xz):
        """The shift of the smallest building outline holding most of these points, or None."""
        mn, mx = xz.min(0), xz.max(0)
        cand = np.nonzero((lo[:, 0] <= mx[0]) & (hi[:, 0] >= mn[0]) & (lo[:, 1] <= mx[1]) & (hi[:, 1] >= mn[1]))[0]
        best = None
        for i in cand:
            if owners[i][0].contains_points(xz, radius=0.6).mean() > 0.6:
                best = owners[i][1]   # sorted large to small: the last match is the smallest
        return best

    # Open water: one flat sheet, at the ring's water (the LiDAR's water surface under it). Land the scene sank below
    # its water (the harbour's bed, the river's) keeps its depth under the new sheet, or it would rise through it.
    wat = [(g.read(a), g.read(ia).reshape(-1, 3)) for g in glbs for name, a, ia in g.prims if name == WATER]
    CELL = 4.0
    wet = np.zeros((1, 1), bool)
    wx0 = wz0 = 0.0
    if wat:
        W = np.vstack([w for w, _ in wat])
        wat_old = float(np.median(W[:, 1]))
        wat_shift = float(np.median(land.height(W[:, 0], W[:, 2]))) - wat_old
        # where the sheet lies, rasterised at CELL m (only land under the sheet is the water's bed)
        wx0, wz0 = W[:, 0].min(), W[:, 2].min()
        wet = np.zeros((int((W[:, 0].max() - wx0) / CELL) + 2, int((W[:, 2].max() - wz0) / CELL) + 2), bool)
        for Wp, Wi in wat:
            for t in Wi:
                q = Wp[t][:, [0, 2]]
                i0, j0 = np.floor((q.min(0) - (wx0, wz0)) / CELL).astype(int)
                i1, j1 = np.ceil((q.max(0) - (wx0, wz0)) / CELL).astype(int)
                gx, gz = np.meshgrid(wx0 + (np.arange(i0, i1 + 1) + 0.5) * CELL, wz0 + (np.arange(j0, j1 + 1) + 0.5) * CELL,
                                     indexing="ij")
                a, b, c = q
                den = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
                if abs(den) < 1e-9:
                    continue
                l1 = ((b[1] - c[1]) * (gx - c[0]) + (c[0] - b[0]) * (gz - c[1])) / den
                l2 = ((c[1] - a[1]) * (gx - c[0]) + (a[0] - c[0]) * (gz - c[1])) / den
                inside = (l1 >= -0.05) & (l2 >= -0.05) & (1 - l1 - l2 >= -0.05)
                wet[i0:i1 + 1, j0:j1 + 1] |= inside
    else:
        wat_old, wat_shift = -1e9, 0.0

    def under_water(x, z, y_old):
        """Below the old sheet and under it in plan: the water's bed."""
        i = np.clip(((np.asarray(x) - wx0) / CELL).astype(int), 0, wet.shape[0] - 1)
        j = np.clip(((np.asarray(z) - wz0) / CELL).astype(int), 0, wet.shape[1] - 1)
        inb = (np.asarray(x) >= wx0) & (np.asarray(z) >= wz0)
        return wet[i, j] & inb & (np.asarray(y_old) < wat_old - 0.3)

    stats = {}
    for g in glbs:
        for name, a, ia in g.prims:
            P = g.read(a).astype(np.float64)
            if name == FAR or is_ground(name):
                d = np.where(under_water(P[:, 0], P[:, 2], old(P[:, 0], P[:, 2])), wat_shift, shift(P[:, 0], P[:, 2]))
                kind = "land"
            elif name == WATER:
                d = np.full(len(P), wat_shift)
                kind = "water"
            else:
                I = g.read(ia).reshape(-1, 3).astype(np.int64) if ia is not None else np.arange(len(P)).reshape(-1, 3)
                k, lab = components(P, I)
                d = np.zeros(len(P))
                kind = "buildings" if name.startswith(("bg_bld_", "bg_roof", "bg_parapets", "bg_station_roof")) else "objects"
                vlab = np.full(len(P), -1)
                vlab[I.ravel()] = np.repeat(lab, 3)
                for c in range(k):
                    vi = np.nonzero(vlab == c)[0]
                    V = P[vi]
                    s = owner_shift(V[:, [0, 2]]) if kind == "buildings" else None
                    if s is None:
                        low = V[V[:, 1] < V[:, 1].min() + 0.5][:, [0, 2]].mean(0)
                        under = bool(under_water(low[0:1], low[1:2], old(low[0:1], low[1:2]))[0])   # on the water (a boat, a pier's piles)
                        s = wat_shift if under else float(shift(low[0:1], low[1:2])[0])
                    d[vi] = s
            P[:, 1] += d
            g.write_pos(a, P.astype(np.float32))
            st = stats.setdefault(kind, [])
            st.append(d)
    if wat:
        flat = sum(flatten_painted_water(g, wat_old + wat_shift) for g in glbs)
        print("ground vertices on painted water laid flat at its level: %d" % flat)
    laid = lay_overlays(glbs, (wat_old + wat_shift) if wat else None)
    for name, (n_laid, n_deck, n_gone) in sorted(laid.items()):
        print("%-16s %7d vertices laid on the ground, %6d on decks left, %5d triangles on open water left out" % (
            name, n_laid, n_deck, n_gone))
    if slug in WATER_TARGET:   # after the flattening, which finds the water by its old colour
        for g in glbs:
            tone_painted_water(g, WATER_TARGET[slug])
    for g in glbs:
        drop_scattered_water(g)
        g.save()
    for kind, ds in stats.items():
        d = np.concatenate(ds)
        print("%-9s vertices %8d  shift median %+6.2f m  p5 %+6.2f  p95 %+6.2f" % (
            kind, len(d), np.median(d), np.percentile(d, 5), np.percentile(d, 95)))
    print("past %.0f m the far terrain moved %+.2f m; %d buildings" % (reach, far_shift, len(owners)))


if __name__ == "__main__":
    main()
