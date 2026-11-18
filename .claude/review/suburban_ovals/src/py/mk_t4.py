"""Type 4 (country ground, ref: Euroa Memorial Oval photo). Every placement is read off grid/t4_country_grid.jpg
through the matched camera (py/cam.py, fitted pose spec/t4_pose.json)."""
import sys, math, json; sys.path.insert(0, 'py'); from cam import Cam
c = Cam(1291, horizon=600)
cx, cy, psi = json.load(open("spec/t4_pose.json"))["pose"]
FW = (math.cos(psi), math.sin(psi)); RT = (math.sin(psi), -math.cos(psi))
def W(X, Z): return [round(cx + Z * FW[0] + X * RT[0], 3), round(cy + Z * FW[1] + X * RT[1], 3)]
def front(L, R, **kw):
    """part whose field face runs from camera-frame point L to R (left to right in the photo)"""
    a, b = W(*L), W(*R); m = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]
    d = dict(x=round(m[0], 3), y=round(m[1], 3), rot=round(math.degrees(math.atan2(b[1] - a[1], b[0] - a[0])), 2))
    d.update(kw); return d, math.dist(a, b)
def on_line(u, L, R, H=None, v=None):
    """local x (from centre) where pixel column u meets the vertical plane through L-R; height of pixel v there"""
    dx, dy, dz = c.ray(u, v if v is not None else c.hz)
    (x1, z1), (x2, z2) = L, R
    # solve t*dx = x1 + s(x2-x1), t*dz = z1 + s(z2-z1)
    den = dx * (z2 - z1) - dz * (x2 - x1)
    t = (x1 * (z2 - z1) - z1 * (x2 - x1)) / den
    s = (t * dx - x1) / (x2 - x1) if abs(x2 - x1) > 1e-6 else (t * dz - z1) / (z2 - z1)
    lx = (s - 0.5) * math.dist(L, R)
    h = None
    if v is not None:
        h = c.eye + dy * t
    return round(lx, 2), (round(h, 2) if h is not None else None)

spec = {"name": "oval_t4_country", "seed": 4,
        "field": {"a": 80.0, "b": 65.0, "turf": "turf", "apron": 3.0},
        "surround": [{"d0": 3.0, "d1": 12.0, "tex": "concrete"}, {"d0": 12.0, "d1": 40.0, "tex": "gravel"}],
        "outer": {"d": 400, "tex": "turf_dry"},
        "fence": {"type": "chainlink", "d": 3.0, "h": 1.2},
        "posts": {"goal_h": 12.0, "behind_h": 7.0, "pad": "pad_blue"}}

# ---- grandstand: front post line (posts at u 717 and 1310, deck 3.6 m) ----
SL, SR = c.back(717, 520, 3.6), c.back(1310, 500, 3.6)
st, Ls = front(SL, SR)
dl = lambda u, v=None: on_line(u, SL, SR, v=v)
st.update(len=round(Ls, 2), rows=9, tread=0.8, riser=0.22, base=3.6, seat="bench_timber", riser_tex="concrete",
          front="block_grey", back="block_grey", back_h=0.0, ends="block_grey",
          roof="gable", eave=6.5, ridge=8.1, roof_over=1.2, roof_back=0.3, roof_end=0.8, roof_tex="iron_skyblue", bay=3.7,
          truss="white_paint", rail=True,
          doors=[[dl(938)[0], 0.9, 2.04, "door_black"], [dl(1258)[0], 0.95, 2.04, "door_white"]],
          stairs=[{"x": dl(722)[0] + 1.0, "top": 3.6, "dir": 1, "run": 4.2, "y": -1.1},
                  {"x": dl(1255)[0], "top": 3.6, "dir": -1, "run": 4.4, "y": -1.1}])
spec["stands"] = [st]
print("stand", st["x"], st["y"], st["rot"], "len", st["len"], "doors", st["doors"], "stairs", [s["x"] for s in st["stairs"]])

# ---- social club (left): glass front parallel to the photo, Z 40.5; wall top 2.86, parapet ----
Zc = c.back(400, 657)[1]
X = lambda u, Z: (u - c.cx) * Z / c.f
glass, Lg = front((X(175, Zc), Zc), (X(560, Zc), Zc), w=0, dpt=12.0, h=2.9, wall="block_grey", front="glass_curtain",
                  roof="flat", roof_tex="iron_zinc", parapet="white_paint")
glass["w"] = round(Lg, 2)
entry, Le = front((X(560, Zc), Zc), (X(720, Zc), Zc), w=0, dpt=12.0, h=3.2, wall="block_grey", front="block_grey",
                  roof="flat", roof_tex="iron_zinc", parapet="white_paint", doors=[[0.0, 1.6, 2.1, "door_black"]])
entry["w"] = round(Le, 2)
cant, Lc = front((X(60, Zc + 0.3), Zc + 0.3), (X(175, Zc + 0.3), Zc + 0.3), w=0, dpt=4.0, h=2.9, wall="block_grey")
spec["buildings"] = [glass, entry]
spec["boxes"] = [dict(cant, w=round(Lc, 2), dpt=4.0, z0=2.85, h=3.4, wall="white_paint", top="iron_zinc")]

# ---- right wing: front parallel to the photo at Z of door bases (doors B, C) ----
Zw = (c.back(1525, 690)[1] + c.back(1870, 692)[1]) / 2
wl, Lwl = front((X(1318, Zw), Zw), (X(1590, Zw), Zw), w=0, dpt=8.0, h=3.3, wall="block_grey", front="block_grey_window",
                roof="skillion", rise=1.0, roof_tex="iron_skyblue", overhang=0.4)
wl["w"] = round(Lwl, 2)
wr_end = 19.5
wr, Lwr = front((X(1590, Zw), Zw), (wr_end, Zw), w=0, dpt=10.0, h=3.4, wall="block_grey", front="block_grey_window",
                roof="skillion", rise=1.7, roof_tex="iron_skyblue", overhang=0.4)
wr["w"] = round(Lwr, 2)
wl["doors"] = [[round((X(1351, Zw) - X(1318, Zw)) - Lwl / 2, 2), 0.9, 2.0, "door_white", 1.4], [round((X(1527, Zw) - X(1318, Zw)) - Lwl / 2, 2), 0.95, 2.04, "door_white"]]
wl["stairs"] = [{"x": round((X(1351, Zw) - X(1318, Zw)) - Lwl / 2, 2) + 0.5, "top": 1.4, "dir": 1, "run": 2.4, "y": -1.1}]
wr["doors"] = [[round((X(1870, Zw) - X(1590, Zw)) - Lwr / 2, 2), 0.95, 2.04, "door_white"]]
wr["stairs"] = [{"x": round((X(1598, Zw) - X(1590, Zw)) - Lwr / 2, 2), "top": 1.8, "dir": -1, "run": 1.6, "y": -1.1, "landing": False}]
spec["buildings"] += [wl, wr]

# ---- interchange benches (grey iron, 1.3 m above their visible base) ----
def bench(u0, u1, v):
    Z = c.back((u0 + u1) / 2, v)[1]; b, L = front((X(u0, Z), Z), (X(u1, Z), Z)); b.update(w=round(L, 2)); return b
spec["benches"] = [dict(bench(808, 1062, 705), h=1.33, dd=1.8, wall="iron_zinc"),
                   dict(bench(1342, 1432, 718), h=1.30, dd=1.6, wall="iron_zinc"),
                   dict(bench(1852, 2060, 740), h=1.30, dd=1.8, wall="iron_zinc")]

# ---- flag pole at u 1278, on the stand's front ----
fp = c.back(1278, 640, 0.0)
spec["poles"] = [{"x": W(*c.back(1278, 668))[0], "y": W(*c.back(1278, 668))[1], "h": 8.6, "r": 0.05}]

# ---- signs on the left fence (generic hand-made sponsor boards): photo u 200-360 and 515-640 ----
spec["signs"] = []
def tval(u, v=677):
    x, y = W(*c.back(u, v)); return math.atan2(y / 65.0, x / 80.0)
for (u0, u1, tx) in ((0, 70, "sign_sponsor3"), (210, 360, "sign_sponsor2"), (515, 640, "sign_sponsor4")):
    a, b = sorted((tval(u0), tval(u1)))
    spec["signs"].append({"t0": round(a, 5), "t1": round(b + (b - a) * 0.087, 5), "n": 1, "d": 2.92, "z": [0.35, 1.1], "tex": [tx]})
# trees in the photo: gums behind the club and the stand (camera frame), plus the country windbreak opposite
spec["trees"] = [{"p0": W(-38, 58), "p1": W(-6, 52), "n": 7, "h": 21, "kind": "gum_mix", "djit": 3},
                 {"p0": W(11, 48), "p1": W(30, 46), "n": 4, "h": 13, "kind": "gum_mix", "djit": 2},
                 {"t0": math.radians(200), "t1": math.radians(340), "d": 26, "n": 26, "h": 18, "kind": "pine", "djit": 1.5}]
spec["lights"] = [{"t": math.radians(a), "d": 9, "h": 24, "rows": 2, "cols": 3} for a in (35, 145, 215, 325)]
# stadium only (lead ruling 2026-11-18): trees kept under bg_ for the later background pass; build.py ignores bg_ keys
spec["bg_trees"] = spec.pop("trees")
spec["off_signs"] = spec.pop("signs")   # director 2026-11-18: no sponsor boards (bare fence)
json.dump(spec, open("spec/t4_country.json", "w"), indent=1)

# matched camera render job
cam = W(0, 0); look = W(0, 100)
pitch = c.pitch
job = {"out": "../out/t4/r", "res": [2000, 1291], "samples": 48, "sun": {"az": 250, "el": 22, "power": 4.0},
       "views": [{"name": "match", "cam": [cam[0], cam[1], c.eye], "look": [look[0], look[1], c.eye + 100 * math.tan(pitch)], "fov_h": c.fov_h}]}
json.dump(job, open("spec/t4_job_match.json", "w"), indent=1)
print("cam", cam, "look", look)
