"""Mesh building blocks for the Barossa Park model, and a small glTF (.glb) writer.

Every part is real geometry in metres: x east, y up, z south (glTF's -z is north), the boundary fence's centre at
0, 0 and the arena floor at y 0. UVs are in metres on each face's own plane, divided by the material's tile size, so
a texture painted at a known metres-per-image tiles at its true scale on every wall.
"""
import json
import math
import struct
import zlib

import numpy as np


def _n(v):
    v = np.asarray(v, float)
    d = np.linalg.norm(v)
    return v / d if d > 1e-12 else v


class Mesh:
    """Triangles grouped by material name. Each triangle is wound counter-clockwise seen from its front."""

    def __init__(self):
        self.parts = {}

    def _p(self, mat):
        return self.parts.setdefault(mat, {"v": [], "n": [], "uv": [], "c": []})

    def tri(self, mat, a, b, c, n=None, uv=None, col=None):
        p = self._p(mat)
        a, b, c = (np.asarray(x, float) for x in (a, b, c))
        if n is None:
            n = _n(np.cross(b - a, c - a))
        n = np.asarray(n, float)
        for k, q in enumerate((a, b, c)):
            p["v"].append(q)
            p["n"].append(n)
            p["uv"].append(uv[k] if uv is not None else self._auto_uv(q, n))
            p["c"].append(col if col is not None else (1.0, 1.0, 1.0))

    @staticmethod
    def _auto_uv(q, n):
        # planar in metres: walls by (along, up), floors and roofs by (x, z)
        if abs(n[1]) > 0.7:
            return (q[0], q[2])
        t = _n(np.cross((0, 1, 0), n))
        return (float(np.dot(q, t)), -q[1])

    def quad(self, mat, a, b, c, d, uv=None, col=None, both=False):
        """a b c d counter-clockwise from the front"""
        n = _n(np.cross(np.asarray(b, float) - a, np.asarray(d, float) - a))
        if np.linalg.norm(n) < 1e-9:
            n = _n(np.cross(np.asarray(c, float) - b, np.asarray(a, float) - b))
        if uv is None:
            # one frame for the whole quad: u along a->b, v up the face (or along a->d for flat faces)
            u_ax = _n(np.asarray(b, float) - a)
            v_ax = _n(np.cross(n, u_ax))
            o = np.asarray(a, float)
            if abs(n[1]) > 0.7:
                uv = [(q[0], q[2]) for q in (a, b, c, d)]
            else:
                uv = [(float(np.dot(np.asarray(q, float), u_ax)), -float(np.dot(np.asarray(q, float) - o, v_ax)) - o[1])
                      for q in (a, b, c, d)]
        self.tri(mat, a, b, c, n, (uv[0], uv[1], uv[2]), col)
        self.tri(mat, a, c, d, n, (uv[0], uv[2], uv[3]), col)
        if both:
            self.quad(mat, d, c, b, a, uv=[uv[3], uv[2], uv[1], uv[0]], col=col)

    def box(self, mat, c, size, yaw=0.0, mats=None, skip=()):
        """an axis box centred c (x, y, z) of size (sx, sy, sz), turned yaw radians about y (from +x toward -z).
        mats: optional per face {'top','bottom','px','nx','pz','nz'}"""
        sx, sy, sz = (s / 2 for s in size)
        ca, sa = math.cos(yaw), math.sin(yaw)
        ex = np.array((ca, 0, -sa))
        ez = np.array((sa, 0, ca))
        ey = np.array((0, 1, 0))
        c = np.asarray(c, float)
        P = lambda i, j, k: c + ex * sx * i + ey * sy * j + ez * sz * k
        m = lambda f: (mats or {}).get(f, mat)
        if "top" not in skip:
            self.quad(m("top"), P(-1, 1, 1), P(1, 1, 1), P(1, 1, -1), P(-1, 1, -1))
        if "bottom" not in skip:
            self.quad(m("bottom"), P(-1, -1, -1), P(1, -1, -1), P(1, -1, 1), P(-1, -1, 1))
        if "px" not in skip:
            self.quad(m("px"), P(1, -1, 1), P(1, -1, -1), P(1, 1, -1), P(1, 1, 1))
        if "nx" not in skip:
            self.quad(m("nx"), P(-1, -1, -1), P(-1, -1, 1), P(-1, 1, 1), P(-1, 1, -1))
        if "pz" not in skip:
            self.quad(m("pz"), P(-1, -1, 1), P(1, -1, 1), P(1, 1, 1), P(-1, 1, 1))
        if "nz" not in skip:
            self.quad(m("nz"), P(1, -1, -1), P(-1, -1, -1), P(-1, 1, -1), P(1, 1, -1))

    def beam(self, mat, a, b, w, h=None, up=(0, 1, 0), skip_ends=False):
        """a square or rectangular member from point a to b, w wide and h deep"""
        h = w if h is None else h
        a, b = np.asarray(a, float), np.asarray(b, float)
        d = _n(b - a)
        upv = np.asarray(up, float)
        if abs(np.dot(d, upv)) > 0.95:
            upv = np.array((1.0, 0, 0)) if abs(d[0]) < 0.9 else np.array((0, 0, 1.0))
        s = _n(np.cross(d, upv)) * w / 2
        u = _n(np.cross(s, d)) * h / 2
        ring = [(-s - u), (s - u), (s + u), (-s + u)]
        for k in range(4):
            p0, p1 = ring[k], ring[(k + 1) % 4]
            self.quad(mat, a + p1, a + p0, b + p0, b + p1)
        if not skip_ends:
            self.quad(mat, b + ring[3], b + ring[2], b + ring[1], b + ring[0])
            self.quad(mat, a + ring[0], a + ring[1], a + ring[2], a + ring[3])

    def tube(self, mat, a, b, r0, r1=None, seg=8, caps=True):
        r1 = r0 if r1 is None else r1
        a, b = np.asarray(a, float), np.asarray(b, float)
        d = _n(b - a)
        t = _n(np.cross(d, (1, 0, 0) if abs(d[0]) < 0.9 else (0, 0, 1)))
        s = np.cross(d, t)
        ring = [(math.cos(2 * math.pi * k / seg) * t + math.sin(2 * math.pi * k / seg) * s) for k in range(seg)]
        L = float(np.linalg.norm(b - a))
        for k in range(seg):
            q0, q1 = ring[k], ring[(k + 1) % seg]
            u0, u1 = k / seg * 2 * math.pi * r0, (k + 1) / seg * 2 * math.pi * r0
            self.quad(mat, a + q0 * r0, a + q1 * r0, b + q1 * r1, b + q0 * r1, uv=[(u0, 0), (u1, 0), (u1, -L), (u0, -L)])
        if caps:
            for k in range(1, seg - 1):
                self.tri(mat, b + ring[0] * r1, b + ring[k] * r1, b + ring[k + 1] * r1)
                self.tri(mat, a + ring[0] * r0, a + ring[k + 1] * r0, a + ring[k] * r0)

    def prism(self, mat, poly, y0, y1, top=None, bottom=False, side=None):
        """a vertical extrusion of a plan polygon [(x, z)...] from y0 to y1 (any winding)"""
        poly = [tuple(map(float, p)) for p in poly]
        if _area(poly) > 0:   # want clockwise in (x, z) == counter-clockwise seen from +y
            poly = poly[::-1]
        n = len(poly)
        for k in range(n):
            (x0, z0), (x1, z1) = poly[k], poly[(k + 1) % n]
            self.quad(side or mat, (x1, y0, z1), (x0, y0, z0), (x0, y1, z0), (x1, y1, z1))
        if top is not False:
            self.cap(top or mat, poly, y1, up=True)
        if bottom:
            self.cap(mat, poly, y0, up=False)

    def cap(self, mat, poly, y, up=True):
        for i, j, k in triangulate(poly):
            a, b, c = poly[i], poly[j], poly[k]
            A, B, C = (a[0], y, a[1]), (b[0], y, b[1]), (c[0], y, c[1])
            n = np.cross(np.subtract(B, A), np.subtract(C, A))
            if (n[1] > 0) != up:
                B, C = C, B
            self.tri(mat, A, B, C)

    def merge(self, other):
        for m, p in other.parts.items():
            q = self._p(m)
            for k in p:
                q[k] += p[k]

    def tris(self):
        return sum(len(p["v"]) for p in self.parts.values()) // 3


def _area(poly):
    a = 0.0
    for k in range(len(poly)):
        x0, z0 = poly[k]
        x1, z1 = poly[(k + 1) % len(poly)]
        a += x0 * z1 - x1 * z0
    return a / 2


def triangulate(poly):
    """ear clipping of a simple polygon; returns index triples"""
    idx = list(range(len(poly)))
    if _area(poly) < 0:
        idx = idx[::-1]
    out = []
    guard = 0
    while len(idx) > 3 and guard < 10000:
        guard += 1
        n = len(idx)
        for k in range(n):
            i, j, l = idx[(k - 1) % n], idx[k], idx[(k + 1) % n]
            a, b, c = poly[i], poly[j], poly[l]
            cr = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
            if cr <= 1e-12:
                continue
            ok = True
            for m in idx:
                if m in (i, j, l):
                    continue
                if _inside(poly[m], a, b, c):
                    ok = False
                    break
            if ok:
                out.append((i, j, l))
                idx.pop(k)
                break
        else:
            break
    if len(idx) == 3:
        out.append(tuple(idx))
    return out


def _inside(p, a, b, c):
    def s(p1, p2, p3):
        return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
    d1, d2, d3 = s(p, a, b), s(p, b, c), s(p, c, a)
    return not ((d1 < 0 or d2 < 0 or d3 < 0) and (d1 > 0 or d2 > 0 or d3 > 0))


# ---------------------------------------------------------------- glTF writer

def _png(img):
    """img: HxWx3 or HxWx4 uint8 -> PNG bytes"""
    img = np.ascontiguousarray(img, np.uint8)
    h, w = img.shape[:2]
    ch = img.shape[2]
    raw = b"".join(b"\x00" + img[y].tobytes() for y in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6 if ch == 4 else 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def write_glb(path, nodes, materials, jpeg=False):
    """nodes: [(name, Mesh)]. materials: {name: {'tex': (img, metres_per_tile_u, metres_per_tile_v) or None,
    'col': (r,g,b) linear, 'rough':, 'metal':, 'alpha': 'MASK'|None, 'cull': bool, 'vcol': bool}}"""
    bin_ = bytearray()
    views, accs, meshes, gnodes, images, textures, gmats = [], [], [], [], [], [], []
    mat_index = {}

    def add_view(data, target=None):
        while len(bin_) % 4:
            bin_.append(0)
        off = len(bin_)
        bin_.extend(data)
        v = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target:
            v["target"] = target
        views.append(v)
        return len(views) - 1

    def add_acc(arr, typ, comp=5126, minmax=False, target=34962):
        arr = np.ascontiguousarray(arr, np.float32 if comp == 5126 else np.uint32)
        a = {"bufferView": add_view(arr.tobytes(), target), "componentType": comp, "count": int(arr.shape[0]), "type": typ}
        if minmax:
            a["min"] = [float(x) for x in arr.min(0)]
            a["max"] = [float(x) for x in arr.max(0)]
        accs.append(a)
        return len(accs) - 1

    tex_cache = {}

    def material(name):
        if name in mat_index:
            return mat_index[name]
        m = materials.get(name, {"col": (0.5, 0.5, 0.5)})
        pbr = {"baseColorFactor": list(m.get("col", (1, 1, 1))) + [1.0], "metallicFactor": m.get("metal", 0.0),
               "roughnessFactor": m.get("rough", 0.85)}
        if m.get("tex") is not None:
            key = id(m["tex"][0])
            if key not in tex_cache:
                if jpeg and m["tex"][0].shape[0] >= 1024:
                    import io
                    from PIL import Image
                    bio = io.BytesIO()
                    Image.fromarray(np.ascontiguousarray(m["tex"][0][..., :3], np.uint8)).save(bio, "JPEG", quality=90)
                    images.append({"bufferView": add_view(bio.getvalue()), "mimeType": "image/jpeg"})
                else:
                    images.append({"bufferView": add_view(_png(m["tex"][0])), "mimeType": "image/png"})
                textures.append({"source": len(images) - 1, "sampler": 0})
                tex_cache[key] = len(textures) - 1
            pbr["baseColorTexture"] = {"index": tex_cache[key]}
        g = {"name": name, "pbrMetallicRoughness": pbr, "doubleSided": not m.get("cull", True)}
        if m.get("alpha") == "MASK":
            g["alphaMode"] = "MASK"
            g["alphaCutoff"] = 0.5
        if m.get("emit"):
            g["emissiveFactor"] = list(m["emit"])
        gmats.append(g)
        mat_index[name] = len(gmats) - 1
        return mat_index[name]

    for name, mesh in nodes:
        prims = []
        for mname, p in mesh.parts.items():
            if not p["v"]:
                continue
            m = materials.get(mname, {})
            v = np.array(p["v"], np.float32)
            n = np.array(p["n"], np.float32)
            uv = np.array(p["uv"], np.float32)
            if m.get("tex") is not None:
                tu, tv = m["tex"][1], m["tex"][2]
                uv = uv / np.array((tu, tv), np.float32)
            attrs = {"POSITION": add_acc(v, "VEC3", minmax=True), "NORMAL": add_acc(n, "VEC3"),
                     "TEXCOORD_0": add_acc(uv, "VEC2")}
            if m.get("vcol"):
                attrs["COLOR_0"] = add_acc(np.array(p["c"], np.float32), "VEC3")
            prims.append({"attributes": attrs, "material": material(mname)})
        if not prims:
            continue
        meshes.append({"name": name, "primitives": prims})
        gnodes.append({"name": name, "mesh": len(meshes) - 1})
    doc = {"asset": {"version": "2.0", "generator": "tools/grounds/barossa"},
           "scene": 0, "scenes": [{"nodes": list(range(len(gnodes)))}], "nodes": gnodes, "meshes": meshes,
           "materials": gmats, "accessors": accs, "bufferViews": views, "buffers": [{"byteLength": len(bin_)}]}
    if images:
        doc["images"] = images
        doc["textures"] = textures
        doc["samplers"] = [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}]
    js = json.dumps(doc, separators=(",", ":")).encode()
    while len(js) % 4:
        js += b" "
    while len(bin_) % 4:
        bin_.append(0)
    out = struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_))
    out += struct.pack("<II", len(js), 0x4E4F534A) + js + struct.pack("<II", len(bin_), 0x004E4942) + bytes(bin_)
    open(path, "wb").write(out)
