"""The country round Lyndoch beyond the land model (land.py stops at 1 km), out to 16 km: the Barossa Range and the
hills of Mount Crawford to the east and south-east, the valley floor north to Tanunda, the plains west to Gawler,
the South Para and Warren reservoirs, the pine plantations. From the field these are the skyline: the photographs
of Barossa Park show the golden, tree-dotted ranges standing over the clubrooms and the town.

Heights are the Terrarium tiles (dem.py), with the earth's curve. The ground's colour is painted from a palette by
land cover, and the cover is MEASURED from the Google satellite mosaic (work/z15.png, 10 m a pixel): which of dry
paddock, woodland, pine, vineyard, green crop, town or water each 10 m holds. No satellite pixel is used as a colour:
the texture is the palette by class with painted unevenness, and distance haze baked in as seen from the ground.

    python3 tools/grounds/barossa/satmosaic.py 15 16000 10 work/z15.png
    python3 tools/grounds/barossa/far.py      # assets/grounds/barossa/barossa_far.glb
"""
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dem import Dem  # noqa: E402
from geom import Mesh, write_glb  # noqa: E402
from plan import FIELD_ASL  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(HERE, "work")
OUT = os.path.join(HERE, "..", "..", "..", "assets", "grounds", "barossa")
SAT_HALF, SAT_RES = 16000.0, 10.0
LAND = 1024.0      # land.py's square half side: inside it this mesh sinks under the land
EARTH = 6371000.0 / 0.87   # the curve, eased by the air's refraction

# (sRGB) the cover's colours as the ranges show them in late summer and autumn, from the reference photos
PALETTE = {
    "paddock": (168, 144, 104),   # cured grass on the hills, golden tan
    "woodland": (78, 86, 62),     # gums along gullies and on the range tops
    "pine": (42, 54, 42),         # Mount Crawford's plantations
    "vines": (118, 120, 78),      # vineyard rows, leaf over bare earth
    "green": (104, 132, 70),      # watered crops, ovals, gardens
    "town": (150, 144, 134),      # roofs, roads and gardens together
    "water": (70, 88, 98),        # the reservoirs
}
KEYS = list(PALETTE)
HAZE = np.array((168, 186, 206), float)  # the sky low over the hills


def cover():
    """the mosaic -> per-class share maps (each the mosaic's size, 0..1)"""
    import cv2
    a = cv2.imread(os.path.join(WORK, "z15.png"))
    if a is None:
        raise SystemExit("work/z15.png missing: python3 tools/grounds/barossa/satmosaic.py 15 16000 10 work/z15.png")
    hsv = cv2.cvtColor(a, cv2.COLOR_BGR2HSV).astype(np.float32)
    H, S, V = hsv[..., 0], hsv[..., 1], hsv[..., 2]
    b, g, r = (a[..., k].astype(np.float32) for k in range(3))
    gray = cv2.cvtColor(a, cv2.COLOR_BGR2GRAY).astype(np.float32)
    mu = cv2.blur(gray, (5, 5))
    sd = np.sqrt(np.maximum(cv2.blur(gray * gray, (5, 5)) - mu * mu, 0))
    water = (b > g + 4) & (b > r + 8) & (V < 120) & (sd < 12)
    water |= (H > 80) & (H < 100) & (S > 60)
    pine = ~water & (V < 50) & (sd < 14)
    wood = ~water & ~pine & (V < 95) & (S > 30)
    town = ~water & (b >= r - 6) & (S < 60) & (V > 80) & (sd > 14)
    green = ~water & ~wood & ~pine & ~town & (g > r + 6) & (V > 60)
    vines = ~water & ~wood & ~pine & ~town & ~green & (g > r - 8) & (sd > 10) & (V < 140)
    paddock = ~(water | pine | wood | town | green | vines)
    maps = {"paddock": paddock, "woodland": wood, "pine": pine, "vines": vines, "green": green, "town": town,
            "water": water}
    # water and pine come in big blocks; tidy specks
    k = np.ones((5, 5), np.uint8)
    for key in ("water", "pine"):
        maps[key] = cv2.morphologyEx(maps[key].astype(np.uint8), cv2.MORPH_OPEN, k).astype(bool)
    return {key: m.astype(np.float32) for key, m in maps.items()}


def paint_texture(maps):
    """the cover maps -> the ground's colour at 10 m a pixel (sRGB uint8), each class in its palette colour with a
    field-to-field and within-field unevenness, and the distance haze as seen from the ground"""
    import cv2
    import paint
    h, w = maps["paddock"].shape
    pri = ["paddock", "vines", "green", "town", "woodland", "pine", "water"]
    out = np.zeros((h, w, 3), np.float32)
    for k in pri:
        out[maps[k] > 0.5] = PALETTE[k]
    # soften class edges a little (a pixel is 10 m) and vary the colour
    out = cv2.GaussianBlur(out, (0, 0), 0.8)
    n1 = paint.fbm(h, w, 401, (40, 120, 320, 800), (0.3, 0.3, 0.25, 0.15))
    n2 = paint.fbm(h, w, 402, (8, 16, 32, 64), (0.3, 0.3, 0.2, 0.2))
    out *= (0.86 + 0.18 * n1 + 0.1 * (n2 - 0.5))[..., None]
    e = (np.arange(w) + 0.5) * SAT_RES - SAT_HALF
    E, N = np.meshgrid(e, -e)
    d = np.hypot(E, N)
    f = np.clip(1.0 - np.exp(-d / 26000.0), 0, 0.35)[..., None]
    out = out * (1 - f) + HAZE[None, None, :] * f
    return np.clip(out, 0, 255).astype(np.uint8)


def grid(m, dem, half, step, hole, sink):
    g = np.arange(-half, half + 0.01, step)
    GE, GN = np.meshgrid(g, g)
    E, N = GE.ravel(), GN.ravel()
    Hh = dem.at_en(E, N) - FIELD_ASL - np.hypot(E, N) ** 2 / (2 * EARTH)
    inner = (np.abs(E) < hole) & (np.abs(N) < hole)
    Hh = np.where(inner, Hh - sink, Hh)
    n = len(g)
    P = np.stack([E, Hh, -N], 1)
    p = m._p("far")
    cnt = 0
    for i in range(n - 1):
        for j in range(n - 1):
            ids = (i * n + j, i * n + j + 1, (i + 1) * n + j + 1, (i + 1) * n + j)
            if all(inner[k] for k in ids) and all(abs(E[k]) < hole - step and abs(N[k]) < hole - step for k in ids):
                continue
            a, b, c, d = ids
            # i runs north, j east: (a, b, c) and (a, c, d) wind counter-clockwise seen from above
            for tri in ((a, b, c), (a, c, d)):
                for k in tri:
                    p["v"].append(P[k])
                    p["n"].append((0.0, 1.0, 0.0))
                    p["uv"].append(((E[k] + SAT_HALF) / (2 * SAT_HALF), (SAT_HALF - N[k]) / (2 * SAT_HALF)))
                    p["c"].append((1.0, 1.0, 1.0))
            cnt += 1
    return cnt


def smooth_normals(m):
    """per-vertex normals from the faces round each grid point (shared positions)"""
    p = m.parts["far"]
    V = np.array(p["v"])
    key = np.round(V[:, [0, 2]], 1)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.ravel()
    fn = np.cross(V[1::3] - V[0::3], V[2::3] - V[0::3])
    acc = np.zeros((inv.max() + 1, 3))
    for k in range(3):
        np.add.at(acc, inv[k::3], fn)
    acc /= np.linalg.norm(acc, axis=1, keepdims=True) + 1e-9
    p["n"] = list(acc[inv])


def main():
    maps = cover()
    shares = {k: float(v.mean()) for k, v in maps.items()}
    print("cover", {k: round(v, 3) for k, v in shares.items()})
    m = Mesh()
    # mid ring to 4 km at 40 m, far ring to 16 km at 160 m; each sinks where the finer one lies over it
    dem_mid = Dem(13, 4200)
    c1 = grid(m, dem_mid, 4000.0, 40.0, LAND, 3.0)
    dem_far = Dem(11, 16500)
    c2 = grid(m, dem_far, 16000.0, 160.0, 4000.0, 25.0)
    smooth_normals(m)
    print("cells", c1, c2, "tris", m.tris())
    tex = paint_texture(maps)
    # uv already spans the texture once: one tile of 1 x 1
    mats = {"far": {"tex": (tex, 1.0, 1.0), "rough": 1.0}}
    write_glb(os.path.join(OUT, "barossa_far.glb"), [("far", m)], mats, jpeg=True)


if __name__ == "__main__":
    main()
