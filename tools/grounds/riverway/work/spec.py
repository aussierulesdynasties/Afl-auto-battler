# Writes model/riverway.json: the stand's roof table [b, r_front, r_back] from the satellite trace (sat/esri_025.png,
# 8 px/m crop gs.png), sampled every 0.5 deg by intersecting each bearing with the front and back polylines.
import json, math, numpy as np
FRONT = [(-73.5, 28), (-76, 15), (-77, 0), (-77, -15), (-77, -30), (-77.5, -45), (-79, -55), (-84, -63)]
BACK = [(-95, 28), (-95, 15), (-95, 0), (-95.5, -14), (-101, -16), (-101, -34), (-96, -48), (-90, -63)]
def ray(poly, b):
    d = np.array((math.sin(math.radians(b)), math.cos(math.radians(b)))); best = None
    for a, c in zip(poly[:-1], poly[1:]):
        a, c = np.array(a, float), np.array(c, float); e = c - a; M = np.array([[d[0], -e[0]], [d[1], -e[1]]])
        if abs(np.linalg.det(M)) < 1e-9: continue
        t, s = np.linalg.solve(M, a)
        if t > 0 and -1e-6 <= s <= 1 + 1e-6: best = t
    return best
bear = lambda p: math.degrees(math.atan2(p[0], p[1])) % 360
b0 = max(bear(FRONT[-1]), bear(BACK[-1])); b1 = min(bear(FRONT[0]), bear(BACK[0]))
b0 = math.ceil(b0 * 2) / 2; b1 = math.floor(b1 * 2) / 2
roof = []
for b in np.arange(b0, b1 + 1e-6, 0.5):
    f, k = ray(FRONT, b), ray(BACK, b)
    if f and k: roof.append([float(b), round(f, 2), round(k, 2)])
S = {"name": "symonds", "b0": roof[0][0], "b1": roof[-1][0], "kind": "single", "roof": roof,
     "seat_front": 3.0, "seat_depth": 8.0, "z_seat": [3.0, 6.6], "z_roof": [11.2, 13.4], "back_in": 1.0,
     "mats": {"seat": "conc_tread", "roof": "roof_grey", "back": "facade_back", "front": "podium", "bowl": "glass_corp"},
     "rib": 0, "solar": [[roof[0][0] + 3, roof[-1][0] - 3, 0.25, 0.8]],   # panels along the whole roof (Esri tile; tcb.jpg is older)
     "back_zones": [[roof[0][0] - 1, 263.0, "clad_dark"]]}   # charcoal panels south of y -11.5 (GE l090: render wall ends at crop x640), grey render north of it
# shelters, race canopy: cream boxes on the Esri tile (render/satW.png); HOME left of AWAY seen from the field
# light poles: west bases picked on GE l090 (work/pick.py, Z0=5), east bases from the head-and-shadow on the Esri tile; heads at 30 m from the l090 pixel rows
TW = [{"xy": xy, "top": 30.0, "head_h": 2.0, "head_w": 3.2, "r_base": 0.35, "r_top": 0.2, "tilt": 12} for xy in
      [(-53.2, 56.9), (-50.2, -64.6), (56.5, -58.5), (57.5, 56.5)]]
def tang(x, y, a=72.76, b=86.04):
    u = np.array([-y / b ** 2, x / a ** 2]); return u / np.linalg.norm(u)
sc = np.array((54.52, 67.79)); su = np.array((0.64, -0.77)); su /= np.linalg.norm(su)   # screen: steel strip on the Esri tile, 16 m, checked on GE l045/c090
EX = {"boxes": [
        {"c": (-96.0, -29.5), "L": 11.0, "W": 10.0, "h": 16.0, "a": 90, "mat": "tower_panel", "z0": 0.0, "top": "roof_grey"},   # stair tower, ground to 2.6 m over the roof (tcb.jpg)
        {"c": (-73.85, -1.5), "L": 8.4, "W": 4.7, "h": 0.35, "a": 90, "mat": "podium", "z0": 2.25, "top": "roof_grey"}] +      # race canopy and its two front posts
      [{"c": (-71.75, y), "L": 0.2, "W": 0.2, "h": 2.25, "a": 90, "mat": "steel_galv"} for y in (-5.5, 2.5)],
      "sails": [{"c": (-75.0, 37.5), "L": 13.0, "W": 11.0, "a": 90, "z": [3.2, 4.2], "mat": "sail_blue"},
                {"c": (-68.0, -63.0), "L": 13.0, "W": 9.5, "a": 50, "z": [3.2, 4.2], "mat": "sail_blue"},
                {"c": (-67.0, -57.0), "L": 10.0, "W": 8.0, "a": 50, "z": [3.8, 4.8], "mat": "sail_blue"}],   # second, higher sail at the south end (Esri tile)
      "shelters": [{"c": (-70.3, 17.0), "L": 6.5, "W": 3.2, "h": 2.4, "a": 90}, {"c": (-70.3, -19.5), "L": 7.0, "W": 3.2, "h": 2.4, "a": 90}],
      "screen": {"left": list(sc - su * 8.0), "right": list(sc + su * 8.0), "z": [3.4, 11.8], "depth": 0.6}}
EX["boxes"] += [{"c": (-98.5 + 2.2 * i, -33.0 + 2.3 * j), "L": 1.0, "W": 0.8, "h": 0.9, "a": 90, "mat": "paint_white", "z0": 16.0, "top": "paint_white"}
                for i in range(3) for j in range(4)]   # air-con units on the tower top: 3 x 4 (tcb.jpg)
EX["boxes"].append({"c": (33.75, 80.5), "L": 8.0, "W": 6.0, "h": 3.0, "a": -41, "mat": "paint_white", "top": "paint_white"})   # white hut by the NE boundary (Esri tile, GE c090/l270)
SG = [{"c": (-76.19, -1.5), "u": (0.0, 1.0), "w": 8.0, "h": 2.25, "z0": 0.0, "mat": "race_gates"},
      {"c": (-71.5, -1.5), "u": (0.0, 1.0), "w": 8.0, "h": 0.65, "z0": 2.62, "mat": "sign_symonds"},
      {"c": (-71.5, -3.5), "u": (0.0, 1.0), "w": 3.8, "h": 0.32, "z0": 2.27, "mat": "sign_home"},
      {"c": (-71.5, 0.5), "u": (0.0, 1.0), "w": 3.8, "h": 0.32, "z0": 2.27, "mat": "sign_away"}]
# back-wall windows and door, picked on GE l090 (work/pick.py at x=-95, heights fitted on the l090 overlay), set on the
# back wall (back poly pulled in by back_in = 1 m): three windows north, a pair south of the race line, a service door
def onback(y):
    b = math.degrees(math.atan2(-95.0, y)) % 360; r = ray(BACK, b); d = np.array((math.sin(math.radians(b)), math.cos(math.radians(b))))
    return tuple(round(float(v), 2) for v in d * (r - S['back_in']))
SG += [{"c": onback(y), "u": (0.0, 1.0), "w": 0.7, "h": 2.6, "z0": z0, "mat": "window_back", "out": True}
       for y, z0 in ((23.4, 3.5), (21.1, 3.5), (18.8, 3.5), (-5.9, 2.2), (-8.4, 2.2))]
SG += [{"c": (-101.0, -26.6), "u": (0.0, 1.0), "w": 1.9, "h": 8.2, "z0": 4.3, "mat": "sign_tower", "out": True}]   # vertical name sign on the tower
def onback2(y):   # point and tangent on the back wall where the bearing through (-95, y) meets it (works on the slanted south legs)
    b = math.degrees(math.atan2(-95.0, y)) % 360; r = ray(BACK, b); d = np.array((math.sin(math.radians(b)), math.cos(math.radians(b))))
    p = d * (r - S['back_in']); q = d * r
    for A, C in zip(BACK[:-1], BACK[1:]):
        A, C = np.array(A, float), np.array(C, float); e = C - A; t = np.dot(q - A, e) / np.dot(e, e)
        if -1e-3 <= t <= 1 + 1e-3 and np.linalg.norm(A + t * e - q) < 0.05: u = e / np.linalg.norm(e); break
    return tuple(round(float(v), 2) for v in p), tuple(round(float(v), 3) for v in u)
# south back (GE l090 crop x1000-1350, about 0.08 m/px along the wall): two dark doorways at ground level, one high window by the south end
for y, w, h, z0, mat in ((-41.0, 1.6, 2.4, 0.0, "door_back"), (-45.0, 1.6, 2.4, 0.0, "door_back"), (-58.0, 1.4, 2.6, 6.0, "window_back")):
    c, u = onback2(y); SG.append({"c": c, "u": u, "w": w, "h": h, "z0": z0, "mat": mat, "out": True})
SG += [{"c": onback(-4.4), "u": (0.0, 1.0), "w": 1.6, "h": 2.2, "z0": 0.0, "mat": "door_back", "out": True}]
D = {"_note": "Riverway Stadium (Townsville), Andrew 'Roy' Symonds Grandstand, 2024. Plan from the Esri z19 tile (sat/esri_025.png); heights fitted to Google Earth 2024 views (ge/). Stadium only: stops at the outer path ring; no turf, posts, nets, ads, marquees or crowd.",
     "fence_h": 1.1, "fence_gaps": [[265.6, 272.0]], "step": 0.5, "stands": [S], "outer_r": 101.0, "towers": TW, "extras": EX, "signs": SG, "mats_ground": {"concourse": "grass_bank"}}
json.dump(D, open('model/riverway.json', 'w', newline=''), indent=1); print(S['b0'], S['b1'], len(roof), roof[0], roof[len(roof)//2], roof[-1])
