"""The backdrop's own ground (its bg_near_ground bake, from <slug>_backdrop_part1.glb) under a ground's surrounds map,
in that map's colours: the ring where the surrounds map ends at 1,024 m and the backdrop takes over draws one ground,
not a pale circle (Marvel PC check, 28 Nov: "the 1,024 m ring edge shows as a circle on land").

The two maps render through different materials (the surrounds' tint, the backdrop's ground), so the bake is carried
into the surrounds' colours per channel (linear) by a gain measured on a PC render of the land either side of the join.

    from near_bake import matched_bake
    far = matched_bake(part1_glb, size, gain)   # (size, size, 3) float, 0-255
"""
import io
import json
import struct

import numpy as np


def _lin(c):
    c = np.asarray(c, float) / 255.0
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _srgb(c):
    c = np.clip(c, 0.0, 1.0)
    return 255.0 * np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def _near_ground(path):
    """The near ground's texture (sRGB, 0-255) and its plan mapping u = a.(x, z, 1), v = b.(x, z, 1) in the
    model's metres (x east, z south), fitted to its vertices: the bake is one plan projection, checked here."""
    from PIL import Image
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[12:16])[0]
    J = json.loads(b[20:20 + n])
    o = 20 + n
    o += (4 - o % 4) % 4
    binlen = struct.unpack("<I", b[o:o + 4])[0]
    BIN = b[o + 8:o + 8 + binlen]

    def read(ai):
        a = J["accessors"][ai]
        bv = J["bufferViews"][a["bufferView"]]
        k = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[a["type"]]
        dt = {5126: "<f4", 5125: "<u4", 5123: "<u2", 5121: "u1"}[a["componentType"]]
        off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        st = bv.get("byteStride", 0)
        isz = np.dtype(dt).itemsize
        if st and st != k * isz:
            raw = np.frombuffer(BIN, np.uint8, a["count"] * st, off).reshape(-1, st)[:, :k * isz]
            return np.frombuffer(raw.tobytes(), dt).reshape(a["count"], k)
        return np.frombuffer(BIN, dt, a["count"] * k, off).reshape(a["count"], k)

    pr = None
    for nd in J["nodes"]:
        if str(nd.get("name", "")).startswith("bg_near_ground") and "mesh" in nd:
            pr = J["meshes"][nd["mesh"]]["primitives"]
            break
    if pr is None:
        for m in J["meshes"]:
            if str(m.get("name", "")).startswith("bg_near_ground"):
                pr = m["primitives"]
                break
    if pr is None or len(pr) != 1:
        raise RuntimeError("%s: no single bg_near_ground primitive" % path)
    pr = pr[0]
    P = read(pr["attributes"]["POSITION"]).astype(float)
    UV = read(pr["attributes"]["TEXCOORD_0"]).astype(float)
    A = np.c_[P[:, 0], P[:, 2], np.ones(len(P))]
    cu, ru = np.linalg.lstsq(A, UV[:, 0], rcond=None)[:2]
    cv, rv = np.linalg.lstsq(A, UV[:, 1], rcond=None)[:2]
    # a few corners were moved after the bake was laid (the water's edge, the circle's own corners): the plan mapping
    # holds for the rest to about a texel, and is what the surrounds' fade reads
    err = np.percentile(np.maximum(np.abs(A @ cu - UV[:, 0]), np.abs(A @ cv - UV[:, 1])), 75)
    tx = J["textures"][J["materials"][pr["material"]]["pbrMetallicRoughness"]["baseColorTexture"]["index"]]
    im = J["images"][tx["source"] if "source" in tx else next(iter(tx["extensions"].values()))["source"]]
    bv = J["bufferViews"][im["bufferView"]]
    img = np.asarray(Image.open(io.BytesIO(BIN[bv.get("byteOffset", 0):bv.get("byteOffset", 0) + bv["byteLength"]]))
                     .convert("RGB"), float)
    if err * img.shape[1] > 3.0:
        raise RuntimeError("%s: the near ground's texture is not one plan projection (a quarter of its corners %.2f texels off or more)" % (path, err * img.shape[1]))
    return img, cu, cv


def matched_bake(part1_glb, size, gain):
    """The backdrop's ground bake at each pixel of a size x size surrounds map (1 m a pixel, centred on the model's
    0, 0, rows running south), carried into the surrounds' colours by gain: per channel (linear), how much brighter
    the backdrop's ground draws a colour than the surrounds map does, measured on a PC render of the land either side
    of the join (the water is no guide: the surrounds draw it through their own water shader)."""
    img, cu, cv = _near_ground(part1_glb)
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:size, 0:size]
    x = xx - size / 2 + 0.5
    z = yy - size / 2 + 0.5
    u = cu[0] * x + cu[1] * z + cu[2]
    v = cv[0] * x + cv[1] * z + cv[2]
    c = np.clip((u * w).astype(int), 0, w - 1)
    r = np.clip((v * h).astype(int), 0, h - 1)
    return _srgb(_lin(img[r, c]) * np.asarray(gain, float))
