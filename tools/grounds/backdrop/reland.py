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
  land and anything the scene stood below its water keep their depth under it.
Run it on the published glbs, then `tools/ground_assets.sh publish`. Running it twice is harmless: the second
run finds the land already right (shift 0).
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


def fit(slug):
    """GroundModels.FIT[slug]: [centre x, centre z, arena floor y, ...] read from the game's own source."""
    src = open(os.path.join(ROOT, "scripts", "ui", "match", "GroundModels.gd")).read()
    i = src.index('"%s": [' % slug, src.index("const FIT :="))
    return [float(v) for v in src[src.index("[", i) + 1:src.index("]", i)].split(",")]


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
            assert "mesh" not in n or not any(k in n for k in ("matrix", "translation", "rotation", "scale")), \
                "%s: a mesh node with a transform" % path
        self.name_of = {n["mesh"]: n.get("name", "") for n in self.J["nodes"] if "mesh" in n}
        seen = {}
        self.prims = []   # (mesh name, position accessor, indices accessor)
        for mi, m in enumerate(self.J["meshes"]):
            for p in m["primitives"]:
                a = p["attributes"]["POSITION"]
                assert a not in seen, "%s: position accessor shared by two meshes" % path
                seen[a] = mi
                self.prims.append((self.name_of.get(mi, m.get("name", "")), a, p.get("indices")))

    def read(self, ai):
        a = self.J["accessors"][ai]
        v = self.J["bufferViews"][a["bufferView"]]
        dt = np.dtype(CT[a["componentType"]])
        n = NC[a["type"]]
        assert v.get("byteStride", dt.itemsize * n) == dt.itemsize * n, "interleaved"
        off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        return np.frombuffer(bytes(self.bin), dt, a["count"] * n, off).reshape(a["count"], n).copy()

    def write_pos(self, ai, P):
        a = self.J["accessors"][ai]
        assert a["componentType"] == 5126 and a["type"] == "VEC3"
        v = self.J["bufferViews"][a["bufferView"]]
        off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
        b = np.ascontiguousarray(P, "<f4").tobytes()
        self.bin[off:off + len(b)] = b
        a["min"] = [float(x) for x in P.min(0)]
        a["max"] = [float(x) for x in P.max(0)]

    def save(self):
        js = json.dumps(self.J, separators=(",", ":")).encode()
        js += b" " * (-len(js) % 4)
        body = bytes(self.bin) + b"\0" * (-len(self.bin) % 4)
        blob = (struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(body)) + struct.pack("<II", len(js), 0x4E4F534A)
                + js + struct.pack("<II", len(body), 0x004E4942) + body)
        open(self.path, "wb").write(blob)


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
    slug = sys.argv[1]
    paths = sys.argv[2:] or sorted(
        os.path.join(ROOT, "assets", "grounds", slug, f) for f in os.listdir(os.path.join(ROOT, "assets", "grounds", slug))
        if f.startswith(slug + "_backdrop_part") and f.endswith(".glb"))
    land = Land(slug)
    glbs = [Glb(p) for p in paths]
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
    ring = far[(np.maximum(np.abs(far[:, 0]), np.abs(far[:, 2])) > reach - 500) &
               (np.maximum(np.abs(far[:, 0]), np.abs(far[:, 2])) < reach - 20)]
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
    for g in glbs:
        g.save()
    for kind, ds in stats.items():
        d = np.concatenate(ds)
        print("%-9s vertices %8d  shift median %+6.2f m  p5 %+6.2f  p95 %+6.2f" % (
            kind, len(d), np.median(d), np.percentile(d, 5), np.percentile(d, 95)))
    print("past %.0f m the far terrain moved %+.2f m; %d buildings" % (reach, far_shift, len(owners)))


if __name__ == "__main__":
    main()
