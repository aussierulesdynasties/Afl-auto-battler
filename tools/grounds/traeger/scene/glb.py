"""A small glTF 2.0 binary writer for the scene builders: meshes of positions, normals, optional UVs
and vertex colours (RGBA bytes), triangles, and a material each (a plain colour or one embedded JPEG/PNG).

    w = Glb(); m = w.material("far_land", image=jpeg_bytes) ; w.mesh("land", P, N, F, uv=UV, col=C, mat=m)
    w.save(path)

Positions are glTF metres (x east, y up, z south). Nothing here reads back into play.
"""
import io
import json
import math
import struct

import numpy as np


class Glb:
    def __init__(self, frame=None):
        """frame: (rotation about y in radians, x, z), the node transform every mesh takes (geo.model_frame():
        the scene is built north-up and laid into the stadium model's own frame)."""
        self.frame = frame
        self.bin = bytearray()
        self.j = {"asset": {"version": "2.0", "generator": "afl traeger scene"}, "scene": 0,
                  "scenes": [{"nodes": []}], "nodes": [], "meshes": [], "materials": [], "accessors": [],
                  "bufferViews": [], "buffers": [], "images": [], "textures": [], "samplers": []}

    def _view(self, data, target=None):
        while len(self.bin) % 4:
            self.bin.append(0)
        off = len(self.bin)
        self.bin += data
        v = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target:
            v["target"] = target
        self.j["bufferViews"].append(v)
        return len(self.j["bufferViews"]) - 1

    def _acc(self, arr, comp, typ, target, normalized=False, minmax=False):
        arr = np.ascontiguousarray(arr)
        v = self._view(arr.tobytes(), target)
        a = {"bufferView": v, "componentType": comp, "count": int(arr.shape[0]), "type": typ}
        if normalized:
            a["normalized"] = True
        if minmax:
            a["min"] = [float(x) for x in arr.min(0)]
            a["max"] = [float(x) for x in arr.max(0)]
        self.j["accessors"].append(a)
        return len(self.j["accessors"]) - 1

    def material(self, name, colour=(1, 1, 1, 1), image=None, mime="image/jpeg", rough=1.0, double=False,
                 alpha_cut=None):
        m = {"name": name, "pbrMetallicRoughness": {"baseColorFactor": list(colour), "metallicFactor": 0.0,
                                                      "roughnessFactor": rough}}
        if double:
            m["doubleSided"] = True
        if alpha_cut is not None:
            m["alphaMode"] = "MASK"
            m["alphaCutoff"] = alpha_cut
        if image is not None:
            if not self.j["samplers"]:
                self.j["samplers"].append({"magFilter": 9729, "minFilter": 9987, "wrapS": 33071, "wrapT": 33071})
            v = self._view(image)
            self.j["images"].append({"bufferView": v, "mimeType": mime, "name": name})
            self.j["textures"].append({"source": len(self.j["images"]) - 1, "sampler": 0})
            m["pbrMetallicRoughness"]["baseColorTexture"] = {"index": len(self.j["textures"]) - 1}
        self.j["materials"].append(m)
        return len(self.j["materials"]) - 1

    def mesh(self, name, P, N, F, mat, uv=None, col=None):
        P = np.asarray(P, "<f4")
        N = np.asarray(N, "<f4")
        F = np.asarray(F)
        idx_t = 5125 if P.shape[0] > 65535 else 5123
        attrs = {"POSITION": self._acc(P, 5126, "VEC3", 34962, minmax=True),
                 "NORMAL": self._acc(N, 5126, "VEC3", 34962)}
        if uv is not None:
            attrs["TEXCOORD_0"] = self._acc(np.asarray(uv, "<f4"), 5126, "VEC2", 34962)
        if col is not None:
            # glTF vertex colours are linear; ours are picked as sRGB (as a photo shows them)
            c = np.asarray(col, np.float32) / 255.0
            c[:, :3] = np.where(c[:, :3] <= 0.04045, c[:, :3] / 12.92, ((c[:, :3] + 0.055) / 1.055) ** 2.4)
            attrs["COLOR_0"] = self._acc(np.round(c * 65535).astype("<u2"), 5123, "VEC4", 34962, normalized=True)
        ind = self._acc(F.reshape(-1).astype("<u4" if idx_t == 5125 else "<u2"), idx_t, "SCALAR", 34963)
        self.j["meshes"].append({"name": name, "primitives": [{"attributes": attrs, "indices": ind,
                                                               "material": mat}]})
        node = {"name": name, "mesh": len(self.j["meshes"]) - 1}
        if self.frame is not None:
            phi, tx, tz = self.frame
            node["rotation"] = [0.0, math.sin(phi / 2), 0.0, math.cos(phi / 2)]
            node["translation"] = [tx, 0.0, tz]
        self.j["nodes"].append(node)
        self.j["scenes"][0]["nodes"].append(len(self.j["nodes"]) - 1)

    def save(self, path):
        for k in ("images", "textures", "samplers"):
            if not self.j[k]:
                del self.j[k]
        while len(self.bin) % 4:
            self.bin.append(0)
        self.j["buffers"] = [{"byteLength": len(self.bin)}]
        js = json.dumps(self.j, separators=(",", ":")).encode()
        while len(js) % 4:
            js += b" "
        out = io.BytesIO()
        out.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(self.bin)))
        out.write(struct.pack("<II", len(js), 0x4E4F534A))
        out.write(js)
        out.write(struct.pack("<II", len(self.bin), 0x004E4942))
        out.write(self.bin)
        with open(path, "wb") as f:
            f.write(out.getvalue())


def grid_normals(P, F):
    """Smooth vertex normals from the triangles (area weighted)."""
    a, b, c = P[F[:, 0]], P[F[:, 1]], P[F[:, 2]]
    fn = np.cross(b - a, c - a)
    N = np.zeros_like(P)
    for k in range(3):
        np.add.at(N, F[:, k], fn)
    L = np.linalg.norm(N, axis=1, keepdims=True)
    return N / np.maximum(L, 1e-9)


def jpeg(img, q=88):
    b = io.BytesIO()
    img.save(b, "JPEG", quality=q, optimize=True)
    return b.getvalue()
