"""Cut a finished backdrop glb back to past `inner` m, the way reduce.py's `inner` does, without the
Blender scene it was reduced from (row 202 2b). For a ground whose backdrop was reduced with no `inner`
but which draws its own measured surroundings (GroundModels.SURROUNDS) out to that radius: the two
otherwise draw everything twice, the backdrop's generic boxes standing over the measured buildings.
    python3 cut_inner.py in.glb out.glb inner
Same rules as reduce.py: each mesh loses every triangle whose centre lies nearer than `inner` (in the
ground plane); the scene's ground (bg_near_ground) keeps each triangle that reaches past the circle, its
inner corners moved out onto the circle (their height kept), and the far terrain's inner corners sink
5 m. The file is rewritten with its buffers packed again; images, materials and names are copied as
they are. gltf is y-up, so the ground plane is x, z.
"""
import json, struct, sys
import numpy as np

SRC, OUT, INNER = sys.argv[1], sys.argv[2], float(sys.argv[3])
SEAM_GROUND, SEAM_FAR = "bg_near_ground", "bg_far_terrain"

raw = open(SRC, "rb").read()
jlen = struct.unpack("<I", raw[12:16])[0]
J = json.loads(raw[20:20 + jlen])
blen = struct.unpack("<I", raw[20 + jlen:24 + jlen])[0]
BIN = raw[28 + jlen:28 + jlen + blen]
CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4, "MAT4": 16}


def read(i):
    a = J["accessors"][i]
    v = J["bufferViews"][a["bufferView"]]
    assert "byteStride" not in v or v["byteStride"] == np.dtype(CT[a["componentType"]]).itemsize * NC[a["type"]], "interleaved"
    n = NC[a["type"]]
    off = v.get("byteOffset", 0) + a.get("byteOffset", 0)
    return np.frombuffer(BIN, dtype=CT[a["componentType"]], count=a["count"] * n, offset=off).reshape(a["count"], n)


# (primitives of one mesh may share their vertex accessors: each gets its own packed copy of the ones it uses)
assert all("mesh" not in n or ("matrix" not in n and "translation" not in n and "rotation" not in n
                               and "scale" not in n) for n in J["nodes"]), "mesh node with a transform"

out = bytearray()
views, new_acc = [], {}


def put(arr, target=None):
    while len(out) % 4:
        out.append(0)
    b = np.ascontiguousarray(arr).tobytes()
    v = {"buffer": 0, "byteOffset": len(out), "byteLength": len(b)}
    if target:
        v["target"] = target
    out.extend(b)
    views.append(v)
    return len(views) - 1


name_of = {n["mesh"]: n.get("name", "") for n in J["nodes"] if "mesh" in n}
kept_tris = dropped = 0
dead_meshes = set()
for mi, m in enumerate(J["meshes"]):
    name = name_of.get(mi, m.get("name", ""))
    prims = []
    for p in m["primitives"]:
        assert p.get("mode", 4) == 4 and "indices" in p and "targets" not in p
        P = read(p["attributes"]["POSITION"]).astype(np.float64)
        T = read(p["indices"]).reshape(-1, 3).astype(np.int64)
        r = np.hypot(P[:, 0], P[:, 2])
        if name == SEAM_GROUND:
            keep = r[T].max(1) >= INNER
        else:
            c = P[T].mean(1)
            keep = np.hypot(c[:, 0], c[:, 2]) >= INNER
        kept_tris += int(keep.sum()); dropped += int((~keep).sum())
        T = T[keep]
        if len(T) == 0:
            continue
        used = np.unique(T)
        remap = -np.ones(len(P), np.int64); remap[used] = np.arange(len(used))
        np_ = dict(p); np_["attributes"] = {}
        for k, ai in p["attributes"].items():
            a = dict(J["accessors"][ai]); A = read(ai)[used].copy()
            if k == "POSITION":
                if name in (SEAM_GROUND, SEAM_FAR):
                    rr = np.hypot(A[:, 0], A[:, 2]); inn = rr < INNER
                    if name == SEAM_GROUND:
                        s = INNER / np.maximum(rr[inn], 1e-3); A[inn, 0] *= s; A[inn, 2] *= s
                    else:
                        A[inn, 1] = np.minimum(A[inn, 1], -5.0)
                a["min"] = [float(x) for x in A.min(0)]; a["max"] = [float(x) for x in A.max(0)]
            a["count"] = len(A); a["bufferView"] = put(A, 34962); a.pop("byteOffset", None)
            J["accessors"].append(a); np_["attributes"][k] = len(J["accessors"]) - 1
        I = remap[T].reshape(-1)
        ct = 5123 if len(used) < 65536 else 5125
        a = {"componentType": ct, "count": len(I), "type": "SCALAR",
             "bufferView": put(I.astype(CT[ct]), 34963)}
        J["accessors"].append(a); np_["indices"] = len(J["accessors"]) - 1
        prims.append(np_)
    if prims:
        m["primitives"] = prims
    else:
        dead_meshes.add(mi)

# images (and anything else on a buffer view that no primitive owns) copied over as they are
img_views = {im["bufferView"] for im in J.get("images", []) if "bufferView" in im}
vmap = {}
for vi in sorted(img_views):
    v = J["bufferViews"][vi]
    vmap[vi] = put(np.frombuffer(BIN, np.uint8, v["byteLength"], v.get("byteOffset", 0)))
for im in J.get("images", []):
    if "bufferView" in im:
        im["bufferView"] = vmap[im["bufferView"]]

# keep only live accessors: the new ones (appended) are the only ones primitives reference now
live = sorted({k for m in J["meshes"] for p in m["primitives"] for k in list(p["attributes"].values()) + [p["indices"]]})
amap = {o: n for n, o in enumerate(live)}
J["accessors"] = [J["accessors"][o] for o in live]
for m in J["meshes"]:
    for p in m["primitives"]:
        p["attributes"] = {k: amap[v] for k, v in p["attributes"].items()}
        p["indices"] = amap[p["indices"]]
J["bufferViews"] = views
J["buffers"] = [{"byteLength": len(out)}]

# meshes left empty: their nodes lose the mesh (and the mesh goes)
if dead_meshes:
    mmap, ms = {}, []
    for i, m in enumerate(J["meshes"]):
        if i not in dead_meshes:
            mmap[i] = len(ms); ms.append(m)
    J["meshes"] = ms
    for n in J["nodes"]:
        if "mesh" in n:
            if n["mesh"] in dead_meshes:
                del n["mesh"]
            else:
                n["mesh"] = mmap[n["mesh"]]

while len(out) % 4:
    out.append(0)
js = json.dumps(J, separators=(",", ":")).encode()
js += b" " * (-len(js) % 4)
blob = (struct.pack("<III", 0x46546C67, 2, 28 + len(js) + len(out)) + struct.pack("<II", len(js), 0x4E4F534A) + js
        + struct.pack("<II", len(out), 0x004E4942) + bytes(out))
open(OUT, "wb").write(blob)
print("%s: kept %d triangles, dropped %d inside %.0f m; %d meshes emptied; %.1f MB -> %.1f MB"
      % (OUT, kept_tris, dropped, INNER, len(dead_meshes), len(raw) / 1e6, len(blob) / 1e6))
