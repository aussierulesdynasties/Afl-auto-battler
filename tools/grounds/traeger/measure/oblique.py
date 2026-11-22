"""Measure the stadium model against Google Earth's 3D views, in metres, through each view's solved camera.

1. Camera. Each Google Earth shot (ge_compare.py's 1280 x 720 crop, F = 1585.8 px, vertical FOV 25.58 degrees,
   principal point in the middle) has its camera solved (position, yaw, pitch, roll) from the turf's edge: the
   traced curve of outline_model.json, lying at Google Earth's own turf level (573 m), matched by ICP along the
   projected curve's normals to the strongest grass-to-not-grass step in the picture.
2. Model. Each part's edges (open edges and creases over 35 degrees: roof eaves, ridges, gables, fence tops,
   the scoreboard's frame) are projected through that camera, and the part is slid across the picture up to 5 m
   each way to where its edges sit on the picture's strongest edges (each point's gradient taken across its own
   edge). That shift is the part's error in metres where the camera sees it: 0 means it sits where Google
   Earth's mesh has it.
3. Report: per part, the shift in metres and how clear the best fit is (its score over the search's median; near
   1 means the picture shows no matching edge there, a shaded or same-coloured part, so the shift means nothing).

    python3 oblique.py <ge dir> <out dir> NAME [NAME ...]      # writes <out>/NAME_meas.png and oblique.json
Google Earth pictures are measuring references only and stay out of the repository.
"""
import json
import math
import os
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as nd
from scipy.optimize import least_squares

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scene"))
import geo  # noqa: E402

F, CX, CY, W, H = 1585.8, 640.0, 360.0, 1280, 720
GLB = os.environ.get("GLB", os.path.join(HERE, "..", "..", "..", "..", "assets", "grounds", "traeger", "traeger.glb"))
VIEWS = os.environ.get("VIEWS", os.path.join(HERE, "..", "qa", "views.json"))
SKIP = {"ground_dirt"}     # the ground itself: measured as the turf edge
# light towers: thin lattices the picture blurs into the ground; measured by eye in the fly-through
SKIP |= {"FL_2_br", "FL_2_head_lamps", "FL_pole_sign", "NL_pole_sign"}


def turf_edge():
    d = json.load(open(os.path.join(HERE, "outline_model.json")))
    xz = np.array(d["turf_edge"], float)
    e, n = geo.from_model(xz[:, 0], -xz[:, 1])
    return np.c_[e, n, np.zeros(len(e))]


def R_of(yaw, pitch, roll):
    f = np.array([math.sin(yaw) * math.cos(pitch), math.cos(yaw) * math.cos(pitch), math.sin(pitch)])
    r = np.cross(f, [0, 0, 1.0])
    r /= np.linalg.norm(r)
    up = np.cross(r, f)
    cr, sr = math.cos(roll), math.sin(roll)
    return f, cr * r + sr * up, -sr * r + cr * up


def proj(p, P):
    f, r, u = R_of(*p[3:6])
    Q = P - p[:3]
    z = Q @ f
    return np.stack([CX + F * (Q @ r) / z, CY - F * (Q @ u) / z], 1), z


def init(v):
    e, n, u = v.get("at", [0, 0, 0])
    h, t, d = math.radians(v["h"]), math.radians(v["t"]), v["d"]
    dirv = np.array([math.sin(t) * math.sin(h), math.sin(t) * math.cos(h), -math.cos(t)])
    C = np.array([e, n, u]) - d * dirv
    if v["t"] < 1:        # straight down: yaw from the heading, pitch just off vertical
        return np.r_[C, h, -math.radians(89.9), 0.0]
    return np.r_[C, math.atan2(dirv[0], dirv[1]), math.asin(dirv[2]), 0.0]


def grass(a):
    """Grassiness: green over red and blue (the dry buff verge and red earth read as not grass)."""
    return nd.gaussian_filter(a[..., 1] - 0.5 * (a[..., 0] + a[..., 2]), 1.2)


def normals(uv):
    tg = np.gradient(uv, axis=0)
    n = np.stack([-tg[:, 1], tg[:, 0]], 1)
    return n / (np.linalg.norm(n, axis=1, keepdims=True) + 1e-9)


def edge_matches(p, P, sig, R_m, step=2):
    """For the turf curve: along each projected normal, up to R_m metres either side, the strongest rise in
    grassiness toward the inside (measured over 1.2 m of ground, whatever the picture's scale)."""
    uv, z = proj(p, P)
    n = normals(uv)
    cen = proj(p, np.array([[P[:, 0].mean(), P[:, 1].mean(), 0.0]]))[0][0]
    flip = np.sign(np.sum((cen - uv) * n, 1))
    n = n * flip[:, None]                         # n points into the field
    out = []
    for i in range(0, len(P), step):
        if z[i] <= 0:
            continue
        mpp = z[i] / F
        R = R_m / mpp
        if not (R + 3 < uv[i, 0] < W - R - 3 and R + 3 < uv[i, 1] < H - R - 3):
            continue
        k = np.arange(-R, R + 0.01, 0.5)
        q = uv[i] + np.outer(k, n[i])
        v = nd.map_coordinates(sig, [q[:, 1], q[:, 0]], order=1)
        w = max(1, int(round(0.6 / mpp / 0.5)))
        if len(k) < 2 * w + 3:
            continue
        dv = np.zeros_like(v)
        dv[w:-w] = (v[2 * w:] - v[:-2 * w]) / 2
        j = int(dv.argmax())
        if dv[j] > 4.0 and w < j < len(k) - 1 - w:
            out.append((P[i], q[j], n[i]))
    return out


def solve(img, v):
    """The camera from the turf edge, held near the camera Google Earth's link sets (3 m, half a degree). A close
    view sees one arc of the edge, which cannot fix a camera (it slides along the arc), so a view marked
    "solve": "none" keeps its link's camera: the straight-down 'top' view's solve moves that by under a metre."""
    a = np.asarray(img, float)
    sig = grass(a)
    P = turf_edge()
    p0 = init(v)
    if v.get("solve") == "none":
        return p0, dict(n=0, inliers=1.0, rms_px=0.0, moved_m=[0.0] * 3, turned_deg=[0.0] * 3)
    # straight down, the oval's near-round outline barely fixes a turn of the picture (a few degrees moves the
    # edge a pixel or two), so a straight-down view keeps its link's heading and level and solves where it stands
    nadir = v["t"] < 1
    free = np.array([0, 1, 2]) if nadir else np.array([0, 1, 2, 3, 4, 5])
    if v.get("solve") == "xy":     # a close straight-down view of the oval's curved end: where the camera stands
        free = np.array([0, 1])
    p = p0.copy()
    # held near Google Earth's camera: its link fixes the position to a few metres, but a capture can sit a few
    # degrees off (the page's bars move the crop), so the aim is left loose and first found by a coarse search
    prior = np.array([3.0, 3.0, 3.0, math.radians(8), math.radians(8), math.radians(2)])
    gy_, gx_ = np.gradient(sig)
    best = (-1e9, 0, 0)
    for dyaw in (np.radians(np.arange(-6, 6.01, 0.25)) if not nadir else [0.0]):
        for dpit in (np.radians(np.arange(-8, 8.01, 0.25)) if not nadir else [0.0]):
            q = p0 + [0, 0, 0, dyaw, dpit, 0]
            uv, z = proj(q, P)
            nn = normals(uv)
            cen = proj(q, np.array([[P[:, 0].mean(), P[:, 1].mean(), 0.0]]))[0][0]
            nn = nn * np.sign(np.sum((cen - uv) * nn, 1))[:, None]
            ok = (z > 0) & (uv[:, 0] > 2) & (uv[:, 0] < W - 3) & (uv[:, 1] > 2) & (uv[:, 1] < H - 3)
            if ok.sum() < len(P) * 0.3:
                continue
            g = (nd.map_coordinates(gx_, [uv[ok, 1], uv[ok, 0]], order=1) * nn[ok, 0]
                 + nd.map_coordinates(gy_, [uv[ok, 1], uv[ok, 0]], order=1) * nn[ok, 1])
            sc = g.sum() / len(P)
            if sc > best[0]:
                best = (sc, dyaw, dpit)
    p[3] += best[1]
    p[4] += best[2]
    xs = np.array([1, 1, 1, .01, .01, .01])[free]
    for R in v.get("search_m", (12, 8, 5, 3, 1.5)):
        M = edge_matches(p, P, sig, R)
        X = np.array([m[0] for m in M])
        Y = np.array([m[1] for m in M])
        N = np.array([m[2] for m in M])

        def fres(q, X=X, Y=Y, N=N):
            pp = p.copy()
            pp[free] = q
            return np.sum((proj(pp, X)[0] - Y) * N, 1)

        def fall(q):     # held near Google Earth's own camera: its link sets it to within a few metres
            return np.r_[fres(q), (q - p0[free]) / prior[free] * math.sqrt(len(X)) / 2]
        p[free] = least_squares(fall, p[free], loss="huber", f_scale=1.5, x_scale=xs).x
        r = fres(p[free])
    inl = np.abs(r) < 3
    return p, dict(n=len(r), inliers=float(inl.mean()), rms_px=float(np.sqrt((r[inl] ** 2).mean())),
                   moved_m=[float(x) for x in p[:3] - p0[:3]], turned_deg=[float(x) for x in np.degrees(p[3:] - p0[3:])])


# ---- the model's edges
def load_glb(path):
    b = open(path, "rb").read()
    n = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + n])
    binoff = 20 + n + 8
    out = {}

    def acc(i):
        A = j["accessors"][i]
        bv = j["bufferViews"][A["bufferView"]]
        dt = {5126: "<f4", 5125: "<u4", 5123: "<u2", 5121: "u1"}[A["componentType"]]
        nc = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[A["type"]]
        off = binoff + bv.get("byteOffset", 0) + A.get("byteOffset", 0)
        stride = bv.get("byteStride", 0)
        isz = np.dtype(dt).itemsize * nc
        if stride and stride != isz:
            raw = np.frombuffer(b, np.uint8, A["count"] * stride, off).reshape(-1, stride)[:, :isz]
            return np.frombuffer(raw.tobytes(), dt).reshape(A["count"], nc)
        return np.frombuffer(b, dt, A["count"] * nc, off).reshape(A["count"], nc)

    for nd_ in j["nodes"]:
        if "mesh" not in nd_:
            continue
        Ps, Fs, base = [], [], 0
        for pr in j["meshes"][nd_["mesh"]]["primitives"]:
            Pp = acc(pr["attributes"]["POSITION"]).astype(float)
            Ff = acc(pr["indices"]).reshape(-1, 3).astype(int)
            Ps.append(Pp)
            Fs.append(Ff + base)
            base += len(Pp)
        out[nd_["name"]] = (np.concatenate(Ps), np.concatenate(Fs))
    return out


def feature_edges(P, Fc, crease=35.0, spacing=0.5):
    """Open edges and creases, as world (east, north, up) points every `spacing` metres with their 3D tangents."""
    # weld by position first (a glTF splits vertices at every seam)
    key = np.round(P * 200).astype(np.int64)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    Fw = inv[Fc]
    Pw = np.zeros((inv.max() + 1, 3))
    Pw[inv] = P
    fn = np.cross(Pw[Fw[:, 1]] - Pw[Fw[:, 0]], Pw[Fw[:, 2]] - Pw[Fw[:, 0]])
    fn /= np.linalg.norm(fn, axis=1, keepdims=True) + 1e-12
    E = np.concatenate([Fw[:, [0, 1]], Fw[:, [1, 2]], Fw[:, [2, 0]]])
    fi = np.tile(np.arange(len(Fw)), 3)
    Es = np.sort(E, 1)
    order = np.lexsort((Es[:, 1], Es[:, 0]))
    Es, fi = Es[order], fi[order]
    same = np.all(Es[1:] == Es[:-1], 1)
    keep = []
    i = 0
    cosc = math.cos(math.radians(crease))
    while i < len(Es):
        if i + 1 < len(Es) and same[i]:
            j = i + 1
            while j + 1 < len(Es) and same[j]:
                j += 1
            if abs(fn[fi[i]] @ fn[fi[j]]) < cosc:
                keep.append(Es[i])
            i = j + 1
        else:
            keep.append(Es[i])
            i += 1
    pts, tans = [], []
    for a, b in keep:
        A, B = Pw[a], Pw[b]
        L = np.linalg.norm(B - A)
        if L < 0.3:
            continue
        m = max(1, int(L / spacing))
        t = (np.arange(m) + 0.5) / m
        pts.append(A + np.outer(t, B - A))
        tans.append(np.repeat(((B - A) / L)[None], m, 0))
    if not pts:
        return np.zeros((0, 3)), np.zeros((0, 3))
    G, T = np.concatenate(pts), np.concatenate(tans)
    # glTF model (x, y up, z) -> world east, north, up
    e, n = geo.from_model(G[:, 0], -G[:, 2])
    te, tn = geo.from_model(G[:, 0] + T[:, 0], -(G[:, 2] + T[:, 2]))
    W3 = np.c_[e, n, G[:, 1]]
    T3 = np.c_[te - e, tn - n, T[:, 1]]
    return W3, T3


def edge_map(img):
    a = np.asarray(img.convert("L"), float)
    g = nd.gaussian_filter(a, 1.0)
    gy, gx = np.gradient(g)
    return gx, gy


def render_ids(p, model, names):
    """A z-buffered picture of the model through the camera: each pixel the index (into names) of the nearest part,
    -1 where nothing is."""
    ids = np.full((H, W), -1, np.int32)
    dep = np.full((H, W), np.inf)
    for k, nm in enumerate(names):
        P, Fc = model[nm]
        e, n = geo.from_model(P[:, 0], -P[:, 2])
        uv, z = proj(p, np.c_[e, n, P[:, 1]])
        for f in Fc:
            if (z[f] <= 1).any():
                continue
            t = uv[f]
            x0, y0 = np.floor(t.min(0)).astype(int)
            x1, y1 = np.ceil(t.max(0)).astype(int)
            x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, W - 1), min(y1, H - 1)
            if x1 < x0 or y1 < y0:
                continue
            yy, xx = np.mgrid[y0:y1 + 1, x0:x1 + 1] + 0.5
            (ax, ay), (bx, by), (cx, cy) = t
            den = (by - cy) * (ax - cx) + (cx - bx) * (ay - cy)
            if abs(den) < 1e-9:
                continue
            w0 = ((by - cy) * (xx - cx) + (cx - bx) * (yy - cy)) / den
            w1 = ((cy - ay) * (xx - cx) + (ax - cx) * (yy - cy)) / den
            w2 = 1 - w0 - w1
            ins = (w0 >= 0) & (w1 >= 0) & (w2 >= 0)
            if not ins.any():
                continue
            zz = w0 * z[f[0]] + w1 * z[f[1]] + w2 * z[f[2]]
            sub_d = dep[y0:y1 + 1, x0:x1 + 1]
            sub_i = ids[y0:y1 + 1, x0:x1 + 1]
            m = ins & (zz < sub_d)
            sub_d[m] = zz[m]
            sub_i[m] = k
    return ids, dep


def outlines(ids, dep, names):
    """Each building's outline where it stands in front of what is behind it (the ground or something farther):
    the connected patches of model pixels, their edge pixels and outward normals."""
    solid = ids >= 0
    lab, nlab = nd.label(solid)
    out = []
    sm = nd.gaussian_filter(solid.astype(float), 1.0)
    gy, gx = np.gradient(sm)
    for L in range(1, nlab + 1):
        m = lab == L
        if m.sum() < 150:
            continue
        edge = m & ~nd.binary_erosion(m)
        edge[:12] = edge[-12:] = False
        edge[:, :12] = edge[:, -12:] = False
        ys, xs = np.nonzero(edge)
        if len(xs) < 40:
            continue
        n = -np.stack([gx[ys, xs], gy[ys, xs]], 1)
        n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
        parts = np.bincount(ids[m], minlength=len(names))
        top = [names[i] for i in np.argsort(-parts)[:4] if parts[i] > 0]
        out.append(dict(uv=np.c_[xs, ys].astype(float), n=n, z=dep[ys, xs], parts=top, px=int(m.sum())))
    return out


def offset(gx, gy, o, R_m=3.0):
    """Where an outline sits best on the picture's edges: its 2D shift (searched over +-R_m metres) that gives the
    strongest gradient across it. Returns the shift in metres, the peak over the search's median, metres a pixel."""
    uv, n = o["uv"], o["n"]
    mpp = float(np.median(o["z"])) / F
    Rp = int(math.ceil(R_m / mpp))
    sh = np.arange(-Rp, Rp + 1)
    S = np.zeros((len(sh), len(sh)))
    for i, dy in enumerate(sh):
        for j, dx in enumerate(sh):
            q = uv + [dx, dy]
            S[i, j] = np.mean(np.abs(nd.map_coordinates(gx, [q[:, 1], q[:, 0]], order=1) * n[:, 0]
                                     + nd.map_coordinates(gy, [q[:, 1], q[:, 0]], order=1) * n[:, 1]))
    i, j = np.unravel_index(S.argmax(), S.shape)
    edge = i in (0, len(sh) - 1) or j in (0, len(sh) - 1)
    return (sh[j] * mpp, sh[i] * mpp), float(S[i, j] / np.median(S)), mpp, edge


def main():
    ge, out, names = sys.argv[1], sys.argv[2], sys.argv[3:]
    os.makedirs(out, exist_ok=True)
    V = {v["name"]: v for v in json.load(open(VIEWS))}
    model = load_glb(GLB)
    names_ = [nm for nm in sorted(model) if nm not in SKIP]
    report = json.load(open(os.path.join(out, "oblique.json"))) if os.path.exists(os.path.join(out, "oblique.json")) else {}
    for name in names:
        img = Image.open(os.path.join(ge, name + ".png")).convert("RGB")
        p, st = solve(img, V[name])
        o = img.copy()
        dr = ImageDraw.Draw(o)
        uvc, zc = proj(p, turf_edge())
        dr.line([tuple(x) for x, zz in zip(uvc, zc) if zz > 0], fill=(0, 255, 255), width=1)
        rep = {"camera": [float(x) for x in p], "turf_fit": {k: v for k, v in st.items() if k not in ("curve_uv", "hit")}}
        print(f"{name}: camera from the turf edge, {st['n']} points, {st['inliers']:.0%} within 3 px, rms {st['rms_px']:.2f} px, moved {np.round(st['moved_m'], 1)} m, turned {np.round(st['turned_deg'], 2)} deg")
        gx, gy = edge_map(img)
        ids, dep = render_ids(p, model, names_)
        for o_ in outlines(ids, dep, names_):
            (dx, dy), conf, mpp, at_edge = offset(gx, gy, o_)
            for q in o_["uv"]:
                dr.point(tuple(q), fill=(255, 0, 0))
            key = "+".join(o_["parts"][:2])
            rep.setdefault("outlines", []).append({"parts": o_["parts"], "pixels": o_["px"], "shift_m": [round(dx, 2), round(dy, 2)],
                                                  "shift_abs_m": round(math.hypot(dx, dy), 2), "peak_over_median": round(conf, 2),
                                                  "m_per_px": round(mpp, 3), "beyond_search": at_edge})
            print(f"  {key:32s} {o_['px']:6d} px  off by {math.hypot(dx, dy):4.1f} m  (x {dx:+.1f}, y {dy:+.1f})"
                  f"  peak {conf:.2f}{'  BEYOND 3 m' if at_edge else ''}")
        o.save(os.path.join(out, name + "_meas.png"))
        report[name] = rep
    json.dump(report, open(os.path.join(out, "oblique.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
