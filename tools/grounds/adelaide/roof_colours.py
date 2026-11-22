"""Each building's roof colour round Adelaide Oval, read off Google Earth (director 2026-11-23: build the surroundings
from Google Earth, no placeholder colours; OSM leaves most roofs untagged, and the palette painted the cricket sheds
by the west face terracotta where Google Earth shows white and grey iron).

  python3 tools/grounds/adelaide/roof_colours.py plan <workdir>      # straight-down Google Earth views over the area
  node    tools/grounds/ge_shoot.js <workdir>                         # the shots (they stay in <workdir>, never the repo)
  python3 tools/grounds/adelaide/roof_colours.py read  # needs shapely (the bpy env has it) <workdir> [osm files as surrounds.py takes them]

`read` writes roof_colours.json beside this file: OSM way id -> the median colour of the roof inside its footprint
(shrunk 1 m, green tree pixels left out), one number per building, no imagery; and pitch_colours.json, each sports
pitch's surface the same way (Memorial Drive's grass courts are tagged as hard ones). surrounds.py uses it before its palette.
The camera is ge_compare.py's, measured 2026-11-22: 35 degrees vertical over the 1000 px window, the 720-row crop
centred on it; a roof h metres up sits F / (range - h) pixels a metre from the shot's centre."""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import surrounds as S   # noqa: E402

GE_ALT = 26.0           # Google Earth's turf height at the oval (ge_compare.py GROUNDS)
RANGE = 1500.0          # metres above the turf: about 1 px a metre, 1.2 x 0.68 km a shot
F = 500.0 / math.tan(math.radians(17.5))
STEP_E, STEP_N = 1100.0, 620.0
REACH = S.BUILD_R + 100.0


def centres():
    es = np.arange(-REACH + STEP_E / 2, REACH, STEP_E)
    ns = np.arange(-REACH + STEP_N / 2, REACH, STEP_N)
    return [(float(e), float(n)) for n in ns for e in es]


def latlon(e, n):
    return S.LAT0 + n / 110574.0, S.LON0 + e / (111320.0 * math.cos(math.radians(S.LAT0)))


def plan(work):
    os.makedirs(os.path.join(work, "ge"), exist_ok=True)
    urls = []
    for i, (e, n) in enumerate(centres()):
        lat, lon = latlon(e, n)
        urls.append([os.path.join(work, "ge", "t%02d.png" % i),
                     "https://earth.google.com/web/@%.7f,%.7f,%.1fa,%.1fd,35y,0h,0t,0r" % (lat, lon, GE_ALT, RANGE)])
    json.dump(urls, open(os.path.join(work, "urls.json"), "w"), indent=1)
    json.dump(centres(), open(os.path.join(work, "centres.json"), "w"))
    print(len(urls), "shots planned")


def read(work, osm):
    from PIL import Image, ImageDraw
    from shapely.geometry import Polygon
    C = json.load(open(os.path.join(work, "centres.json")))
    shots = {}
    path = osm[0] if osm else "/tmp/adelaide_surrounds.osm"
    extra = osm[1:] if len(osm) > 1 else [p for p in (["/tmp/adelaide_cbd_%d.osm" % i for i in range(len(S.CBD_TILES))]
                                                        + ["/tmp/adelaide_rel_%d.osm" % r for r in S.RELATIONS]) if os.path.exists(p)]
    _, ways = S.load(path, extra)
    out = {}; pitches = {}
    for t, p in ways:
        pitch = t.get("leisure") == "pitch"   # a pitch's own surface colour too (grass tennis courts tagged as hard ones)
        if not ("building" in t or pitch) or "_id" not in t or len(p) < 4 or p[0] != p[-1]:
            continue
        a = np.array(p[:-1], float)
        if np.hypot(*a.mean(0)) > REACH:
            continue
        g = Polygon(a).buffer(-1.0)
        if g.is_empty or g.area < 12:
            continue
        h = 0.0 if pitch else S.building_height(t)
        k = F / (RANGE - h)
        best = None
        for i, (ce, cn) in enumerate(C):   # the shot whose centre is nearest, if the roof is wholly in its crop
            x = 640 + (a[:, 0] - ce) * k; y = 360 - (a[:, 1] - cn) * k
            if x.min() < 2 or x.max() > 1278 or y.min() < 60 or y.max() > 718:
                continue
            dd = math.hypot(a[:, 0].mean() - ce, a[:, 1].mean() - cn)
            if best is None or dd < best[0]:
                best = (dd, i, ce, cn)
        if best is None:
            continue
        _, i, ce, cn = best
        if i not in shots:
            f = os.path.join(work, "ge", "t%02d.png" % i)
            if not os.path.exists(f):
                continue
            shots[i] = np.asarray(Image.open(f).convert("RGB")).astype(int)
        im = shots[i]
        ring = np.array(g.exterior.coords) if g.geom_type == "Polygon" else np.array(max(g.geoms, key=lambda q: q.area).exterior.coords)
        px = np.c_[640 + (ring[:, 0] - ce) * k, 360 - (ring[:, 1] - cn) * k]
        mk = Image.new("L", (im.shape[1], im.shape[0])); ImageDraw.Draw(mk).polygon([tuple(q) for q in px], fill=1)
        c = im[np.asarray(mk, bool)]
        if len(c) < 6:
            continue
        if pitch:
            pitches[t["_id"]] = [int(v) for v in np.median(c, axis=0)]
            continue
        leaf = (c[:, 1] > c[:, 0] + 12) & (c[:, 1] > c[:, 2] + 12)   # tree crowns over the roof
        if (~leaf).sum() < 6:
            continue
        out[t["_id"]] = [int(v) for v in np.median(c[~leaf], axis=0)]
    json.dump(out, open(os.path.join(HERE, "roof_colours.json"), "w"), separators=(",", ":"), sort_keys=True)
    json.dump(pitches, open(os.path.join(HERE, "pitch_colours.json"), "w"), separators=(",", ":"), sort_keys=True)
    print(len(out), "roof colours and", len(pitches), "pitch colours from", len(shots), "shots")


if __name__ == "__main__":
    if sys.argv[1] == "plan":
        plan(sys.argv[2])
    else:
        read(sys.argv[2], sys.argv[3:])
