"""The real colours of the far city's walls and roofs, read off the City of Melbourne's photographed 3D city
(Photomesh 2020, 2 cm aerial capture, CC BY: "City of Melbourne 3D textured mesh (photomesh) 2020", served as I3S
integrated-mesh scene layers). horizon.py gives each measured building (City of Melbourne 2023 footprints) the colour
its own photographed walls and roof have.

    python3 photomesh.py <slug>      -> $HORIZON_WORK/<slug>/photomesh.npz

Reads, from every region the council publishes, the mesh-pyramid nodes about NODE_M across (each a few thousand
triangles and a 512 px texture) that reach into the ring between INNER and CITY_OUT, and keeps, per triangle, its
middle (metres east and north of the centre circle, height AHD), its facing and its texture colour at the middle
(sRGB 0-255); and the green triangles whole (veg_tri, veg_col): the trees' real canopy, which horizon.py keeps where it
stands clear of the ground and of every building.
"""
import gzip
import io
import json
import math
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import horizon  # noqa: E402

BASE = "https://tiles.arcgis.com/tiles/KGdHCCUjGBpOPPac/arcgis/rest/services/%s_WGS84/SceneServer/layers/0"
REGIONS = ["CBD", "Southbank", "Hoddle", "Bolte", "Westgate", "Royal_Park", "Flemington", "Melb_Uni"]
NODE_M = 260.0   # the shallowest nodes whose box is under this (half size, m): about 5 m triangles


def get(u, tries=6):
    for k in range(tries):
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers={"Accept-Encoding": "gzip"}), timeout=90).read()
            try:
                return gzip.decompress(r)
            except OSError:
                return r
        except Exception as e:   # the service resets busy connections: back off and try again
            if k == tries - 1:
                raise
            time.sleep(2 * (k + 1))
    return None


def page(region, k):
    """One node page; past the last one the service answers an error (or nothing): an empty page."""
    try:
        return json.loads(get("%s/nodepages/%d?f=json" % (BASE % region, k), tries=4)).get("nodes", [])
    except Exception:
        return []


def nodes(region):
    cache = horizon.work("_photomesh", region + "_nodes.json")
    if os.path.exists(cache):
        return json.load(open(cache))
    out, p, done = [], 0, False
    with ThreadPoolExecutor(16) as ex:
        while not done:
            pages = list(ex.map(lambda k: page(region, k), range(p, p + 64)))
            for pg in pages:
                out += pg
                if len(pg) < 64:
                    done = True
                    break
            p += 64
    json.dump(out, open(cache, "w"))
    return out


def pick(ns, frame, r0, r1):
    by = {n["index"]: n for n in ns}
    keep = []
    stack = [ns[0]["index"]]
    while stack:
        n = by[stack.pop()]
        c = n["obb"]["center"]
        e, nn = frame.en(c[0], c[1])
        h = max(n["obb"]["halfSize"])
        d = max(abs(float(e)), abs(float(nn)))
        if d + h < r0 or d - h > r1:
            continue                               # wholly inside the backdrop's square, or past the city's reach
        if h < NODE_M and "mesh" in n:
            keep.append(n)
            continue
        stack += n.get("children", [])
    return keep


def read(region, n, frame):
    from PIL import Image
    u = BASE % region
    g = n["mesh"]["geometry"]
    b = get("%s/nodes/%d/geometries/0" % (u, g["resource"]))
    nv = int(np.frombuffer(b[:4], "<u4")[0])
    o = 8
    P = np.frombuffer(b, "<f4", nv * 3, o).reshape(-1, 3).astype(np.float64); o += 12 * nv
    N = np.frombuffer(b, "<f4", nv * 3, o).reshape(-1, 3); o += 12 * nv
    UV = np.frombuffer(b, "<f4", nv * 2, o).reshape(-1, 2); o += 8 * nv
    tex = np.asarray(Image.open(io.BytesIO(get("%s/nodes/%d/textures/0" % (u, n["mesh"]["material"]["resource"])))).convert("RGB"))
    c = n["obb"]["center"]
    lon, lat, z = c[0] + P[:, 0], c[1] + P[:, 1], c[2] + P[:, 2]
    e, nn = frame.en(lon, lat)
    T = np.stack([e, nn, z], 1).reshape(-1, 3, 3)
    mid = T.mean(1)
    fn = np.cross(T[:, 1] - T[:, 0], T[:, 2] - T[:, 0])
    area = np.linalg.norm(fn, axis=1) / 2
    fn = fn / np.maximum(area[:, None] * 2, 1e-9)
    nv_ = N.reshape(-1, 3, 3).mean(1)
    fn = np.where((fn * nv_).sum(1, keepdims=True) < 0, -fn, fn)    # the face's own normal, turned to the stored one's side
    uv = UV.reshape(-1, 3, 2).mean(1) % 1.0
    h, w = tex.shape[:2]
    col = tex[np.clip((uv[:, 1] * h).astype(int), 0, h - 1), np.clip((uv[:, 0] * w).astype(int), 0, w - 1)]
    ok = area > 0.5
    c16 = col.astype(np.int16)
    green = ok & (c16[:, 1] > c16[:, 0] + 4) & (c16[:, 1] >= c16[:, 2]) & (c16.max(1) - c16.min(1) > 10)
    return (mid[ok].astype(np.float32), fn[ok].astype(np.float32), col[ok], area[ok].astype(np.float32),
            T[green].astype(np.float32), col[green])


def main(slug):
    frame = horizon.Frame(slug)
    M, F, C, A, VT, VC = [], [], [], [], [], []
    for region in REGIONS:
        try:
            ns = nodes(region)
        except Exception as e:
            print(region, "unreadable:", e)
            continue
        keep = pick(ns, frame, horizon.INNER - 100, horizon.CITY_OUT + 100)
        print(region, len(ns), "nodes,", len(keep), "in the ring", flush=True)
        with ThreadPoolExecutor(8) as ex:
            for got in ex.map(lambda n: read(region, n, frame), keep):
                M.append(got[0]); F.append(got[1]); C.append(got[2]); A.append(got[3])
                VT.append(got[4]); VC.append(got[5])
    np.savez_compressed(horizon.work(slug, "photomesh.npz"), mid=np.concatenate(M), nrm=np.concatenate(F),
                        col=np.concatenate(C), area=np.concatenate(A),
                        veg_tri=np.concatenate(VT), veg_col=np.concatenate(VC))
    print("triangles", sum(len(m) for m in M))


if __name__ == "__main__":
    main(sys.argv[1])
