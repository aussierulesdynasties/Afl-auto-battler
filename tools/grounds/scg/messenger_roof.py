"""The SCG's Messenger, Noble and Bradman roof brought down to its real height (SCG rebuild, 2026-11-22).

The model (#1909) built the north stands' roof as a wedge that climbs from about 30 m at its front edge
to 47-51 m at its back. Google Earth shows a near-flat shell: seen end-on from the west, its whole
section sits at about 33-35 m, its back no higher than its front (docs/MCG_STANDARD.md, the gate). The
model's source (.claude/review/scg/build/geo.py on branch claude/inspiring-heisenberg-a3f33c) guessed
the back heights; nothing measured them.

This edits the shipped glb pieces in place, without the model's source: in the roof's sector it fits
the roof's top surface per half degree (height against distance from the pitch centre), keeps the front
edge where it is and lays the back FALL metres lower than the front. Everything in the sector above
H0 (the roof, its fascias and glazed strip, the back walls and struts under it) is squeezed onto the new
line, so walls still meet the roof and nothing pokes through. The light towers, lamps and scoreboard are
left alone. Roof normals are recomputed. Run it once on the model as #1909 shipped it:

    python3 tools/grounds/scg/messenger_roof.py assets/grounds/scg/scg_part1.glb assets/grounds/scg/scg_part2.glb

Model axes: x east, y up, z south; the pitch centre is PC.
"""
import json
import struct
import sys

import numpy as np

PC = np.array([0.94, 11.82])      # x, z of the pitch centre (geo.py's PC)
SECTOR = (39.0, 114.0)            # degrees anticlockwise from east (90 = north): the Messenger roof
FALL = 1.5                        # metres the back edge sits under the front edge
H0 = 22.0                         # nothing below this moves (the top seats are at 23 m, under the front edge)
ROOF = ("roof", "roofu", "fascia", "glassroof")
KEEP = ("tower", "lamp", "headback", "sbface", "sbad", "sbback", "screen")


def read(path):
    d = open(path, "rb").read()
    jl = struct.unpack("<I", d[12:16])[0]
    j = json.loads(d[20:20 + jl])
    b0 = 20 + jl + 8
    bl = struct.unpack("<I", d[20 + jl:24 + jl])[0]
    return j, bytearray(d[b0:b0 + bl])


def write(path, j, bin_):
    js = json.dumps(j, separators=(",", ":")).encode()
    js += b" " * ((4 - len(js) % 4) % 4)
    bin_ = bytes(bin_) + b"\0" * ((4 - len(bin_) % 4) % 4)
    total = 12 + 8 + len(js) + 8 + len(bin_)
    with open(path, "wb") as f:
        f.write(struct.pack("<III", 0x46546C67, 2, total))
        f.write(struct.pack("<II", len(js), 0x4E4F534A) + js)
        f.write(struct.pack("<II", len(bin_), 0x004E4942) + bin_)


def view(j, bin_, acc_i):
    """(array view of the accessor as float32 rows, byte offsets) for an interleaved float VEC3."""
    a = j["accessors"][acc_i]
    bv = j["bufferViews"][a["bufferView"]]
    stride = bv.get("byteStride", 12)
    off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    idx = off + np.arange(a["count"]) * stride
    return idx


def get3_fast(bin_, idx):
    raw = np.frombuffer(bytes(bin_), np.uint8)
    rows = np.stack([raw[idx + b] for b in range(12)], 1).copy()
    return rows.view("<f4").reshape(-1, 3)


def put3(bin_, idx, v):
    by = np.ascontiguousarray(v.astype("<f4")).view(np.uint8).reshape(-1, 12)
    raw = np.frombuffer(bin_, np.uint8)      # writable: bin_ is a bytearray
    for b in range(12):
        raw[idx + b] = by[:, b]


def indices(j, bin_, acc_i):
    a = j["accessors"][acc_i]
    bv = j["bufferViews"][a["bufferView"]]
    off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
    dt = {5123: "<u2", 5125: "<u4", 5121: "u1"}[a["componentType"]]
    return np.frombuffer(bytes(bin_), dt, count=a["count"], offset=off).astype(np.int64)


def polar(v):
    x = v[:, 0] - PC[0]
    z = v[:, 2] - PC[1]
    return np.degrees(np.arctan2(-z, x)), np.hypot(x, z)


def main(paths):
    parts = [(p,) + read(p) for p in paths]
    # 1. The roof's top surface as it stands: per half degree, front radius/height and the slope.
    pts = []
    for _p, j, bin_ in parts:
        for pr in j["meshes"][0]["primitives"]:
            if j["materials"][pr["material"]]["name"] != "roof":
                continue
            v = get3_fast(bin_, view(j, bin_, pr["attributes"]["POSITION"]))
            ang, r = polar(v)
            m = (ang > SECTOR[0]) & (ang < SECTOR[1]) & (r > 80)
            pts.append(np.c_[ang[m], r[m], v[m, 1]])
    pts = np.concatenate(pts)
    bins = np.arange(SECTOR[0], SECTOR[1] + 0.5, 0.5)
    prof = []
    for b in bins:
        m = np.abs(pts[:, 0] - b) < 1.0
        if m.sum() < 6:
            prof.append((b, np.nan, np.nan, np.nan, np.nan))
            continue
        q = pts[m]
        # the top surface: the upper envelope by radius
        rs = np.linspace(q[:, 1].min(), q[:, 1].max(), 12)
        top = []
        for k in range(len(rs) - 1):
            mm = (q[:, 1] >= rs[k]) & (q[:, 1] <= rs[k + 1])
            if mm.any():
                top.append((q[mm, 1].mean(), q[mm, 2].max()))
        top = np.array(top)
        slope, icpt = np.polyfit(top[:, 0], top[:, 1], 1) if len(top) > 1 else (0.0, top[0, 1])
        rf, ro = q[:, 1].min(), q[:, 1].max()
        prof.append((b, rf, ro, slope, icpt))
    prof = np.array(prof)
    good = ~np.isnan(prof[:, 1])
    for c in range(1, 5):
        prof[:, c] = np.interp(prof[:, 0], prof[good, 0], prof[good, c])
    print("roof sector %.1f-%.1f deg; back minus front before: %.1f to %.1f m" % (
        SECTOR[0], SECTOR[1], np.min(prof[:, 3] * (prof[:, 2] - prof[:, 1])), np.max(prof[:, 3] * (prof[:, 2] - prof[:, 1]))))

    def heights(ang, r):
        rf = np.interp(ang, prof[:, 0], prof[:, 1])
        ro = np.interp(ang, prof[:, 0], prof[:, 2])
        sl = np.interp(ang, prof[:, 0], prof[:, 3])
        ic = np.interp(ang, prof[:, 0], prof[:, 4])
        rc = np.clip(r, rf, ro)
        zold = ic + sl * rc
        zfront = ic + sl * rf
        t = (rc - rf) / np.maximum(1.0, ro - rf)
        znew = zfront - FALL * t
        return zold, znew, ro

    moved = 0
    for path, j, bin_ in parts:
        for pr in j["meshes"][0]["primitives"]:
            name = j["materials"][pr["material"]]["name"]
            if name in KEEP:
                continue
            acc = pr["attributes"]["POSITION"]
            idx = view(j, bin_, acc)
            v = get3_fast(bin_, idx)
            ang, r = polar(v)
            zold, znew, ro = heights(ang, r)
            m = (ang > SECTOR[0]) & (ang < SECTOR[1]) & (r > 70) & (r < ro + 4.0) & (v[:, 1] > H0) & (zold > znew + 0.05)
            if not m.any():
                continue
            ratio = (znew[m] - H0) / np.maximum(0.5, zold[m] - H0)
            v2 = v.copy()
            v2[m, 1] = H0 + (v[m, 1] - H0) * ratio
            put3(bin_, idx, v2)
            moved += int(m.sum())
            a = j["accessors"][acc]
            a["min"] = [float(x) for x in v2.min(0)]
            a["max"] = [float(x) for x in v2.max(0)]
            if name in ROOF and "indices" in pr and "NORMAL" in pr["attributes"]:
                tri = indices(j, bin_, pr["indices"]).reshape(-1, 3)
                fn = np.cross(v2[tri[:, 1]] - v2[tri[:, 0]], v2[tri[:, 2]] - v2[tri[:, 0]])
                nidx = view(j, bin_, pr["attributes"]["NORMAL"])
                n_old = get3_fast(bin_, nidx)
                acc_n = np.zeros_like(v2)
                for k in range(3):
                    np.add.at(acc_n, tri[:, k], fn)
                ln = np.linalg.norm(acc_n, axis=1)
                n_new = n_old.copy()
                ok = m & (ln > 1e-9)
                n_new[ok] = acc_n[ok] / ln[ok, None]
                # keep each normal on the side it faced (top faces up, undersides down)
                flip = (n_new * n_old).sum(1) < 0
                n_new[flip] *= -1
                put3(bin_, nidx, n_new)
        write(path, j, bin_)
    print("moved", moved, "vertices")


if __name__ == "__main__":
    main(sys.argv[1:])
