"""Heights of York Park's neighbours read off Google Earth with the mouse (the calibrated tool's status bar).

  python3 probe.py plan <workdir>     # probe.json: a straight-down view per building, mouse spots on its roof
  node ge_probe.js <workdir>           # the readouts
  python3 probe.py read <workdir>     # heights above Google Earth's turf (2 m), per building: ridge and eave
"""
import json, math, os, sys
os.environ.setdefault("OMP_THREAD_LIMIT", "1")   # tesseract: one thread (with Chromium busy, its threads crawl: 30 s a strip)
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ge_compare as G
g = G.GROUNDS["york_park"]; D = 150.0
PX_M = 1000.0 / (2 * D * math.tan(math.radians(G.GE_FOV / 2)))   # pixels a metre at the turf, straight down


def spots(pts):
    """The footprint's centre and 8 spots inside it on its long and short axes, in metres."""
    import numpy as np
    P = np.array(pts); c = P.mean(0)
    u, s, vt = np.linalg.svd(P - c); a, b = vt[0], vt[1]
    ext = lambda d: (np.min((P - c) @ d), np.max((P - c) @ d))
    out = [c]
    for d in (a, b):
        lo, hi = ext(d)
        for f in (0.15, 0.35, 0.65, 0.85):
            out.append(c + d * (lo + (hi - lo) * f))
    return [list(map(float, q)) for q in out]


def plan(work):
    foot = json.load(open(os.path.join(HERE, "..", "neighbours_osm.json")))
    used = json.load(open(os.path.join(HERE, "..", "neighbours_used.json")))
    jobs = []
    for b in foot:
        if b["c"] not in used:
            continue
        c = b["c"]; lat, lon = G.latlon(g, *c)
        sp = spots(b["pts"])
        # straight down; Google Earth needs a hair of tilt off vertical to keep north up (none here: 0t, 0h)
        px = [[640 + (q[0] - c[0]) * PX_M, 500 - (q[1] - c[1]) * PX_M] for q in sp]
        name = "b_%d_%d" % (round(c[0]), round(c[1]))
        jobs.append({"name": name, "c": c, "spots": sp, "px": px,
                     "url": "https://earth.google.com/web/@%.7f,%.7f,%.1fa,%.0fd,%gy,0h,0t,0r" % (lat, lon, g["ge_alt"], D, G.GE_FOV)})
    json.dump(jobs, open(os.path.join(work, "probe.json"), "w"), indent=0)
    print(len(jobs), "buildings to probe")


def read(work):
    jobs = json.load(open(os.path.join(work, "probe.json")))
    res = {}
    for j in jobs:
        hs = []
        for k in range(len(j["px"])):
            r = G.readouts(os.path.join(work, "probe", "%s_%d.png" % (j["name"], k)))
            if r and r[0][1] is not None:
                hs.append(r[0][1] - g["ge_alt"])
        if hs:
            hs.sort()
            res[j["name"]] = {"c": j["c"], "n": len(hs), "max": hs[-1], "min": hs[0], "med": hs[len(hs) // 2], "all": hs}
            print("%-14s n%d  ridge %5.1f  median %5.1f  low %5.1f" % (j["name"], len(hs), hs[-1], hs[len(hs) // 2], hs[0]))
    json.dump(res, open(os.path.join(HERE, "..", "neighbours_heights.json"), "w"), indent=0)


if __name__ == "__main__" and sys.argv[1] in ("plan", "read"):
    {"plan": plan, "read": read}[sys.argv[1]](sys.argv[2])


def dms(txt):
    """lat, lon from a status-bar line like 41°25'27.59"S 147°08'02.43"E (tesseract's text)."""
    import re
    m = re.findall(r"(\d+)\D{1,2}(\d+)\D{1,2}([\d.]+)\D{0,2}([NSEW])", txt)
    out = {}
    for d, mi, s, h in m:
        v = float(d) + float(mi) / 60 + float(s) / 3600
        out["lat" if h in "NS" else "lon"] = -v if h in "SW" else v
    return out.get("lat"), out.get("lon")


def plan_stand(work, d=250.0, bearings=range(0, 360, 6), r0=72.0, r1=140.0, step=2.0, sector=18):
    """Straight-down views, one per 18 degrees of bearing, each centred on its sector at 106 m; the mouse walks out
    along each bearing from the boundary to past the stands. Each readout gives the true lat/lon and height of what
    is under it (a roof is nearer the camera, so it shows displaced outward; the readout's own lat/lon corrects
    that). Google Earth's toolbar covers the window's top 140 rows and its status bar the bottom 50, where the
    readout freezes on the centre, so every spot is kept inside rows 150-940."""
    pxm = 1000.0 / (2 * d * math.tan(math.radians(G.GE_FOV / 2)))
    jobs = []
    for s0 in range(0, 360, sector):
        bc = math.radians(s0 + sector / 2.0)
        ce, cn = 106.0 * math.sin(bc), 106.0 * math.cos(bc)
        px, sp = [], []
        for b in [x for x in bearings if s0 <= x < s0 + sector]:
            for r in [r0 + k * step for k in range(int((r1 - r0) / step) + 1)]:
                e, n = r * math.sin(math.radians(b)), r * math.cos(math.radians(b))
                x, y = 640 + (e - ce) * pxm, 500 - (n - cn) * pxm
                assert 150 <= y <= 940 and 0 <= x <= 1280, (b, r, x, y)
                px.append([x, y]); sp.append([b, r, e, n])
        lat, lon = G.latlon(g, ce, cn)
        jobs.append({"name": "st%03d" % s0, "spots": sp, "px": px,
                     "url": "https://earth.google.com/web/@%.7f,%.7f,%.1fa,%.0fd,%gy,0h,0t,0r" % (lat, lon, g["ge_alt"], d, G.GE_FOV)})
    json.dump(jobs, open(os.path.join(work, "probe.json"), "w"))
    print(len(jobs), "views,", sum(len(j["px"]) for j in jobs), "spots")


def read_stand(work):
    """(bearing, asked radius, east, north, height above turf) for every spot read: the stands' outline in metres.
    A readout more than 10 m from the asked spot is dropped (the most a 30 m roof can shift in these views is 8 m)."""
    import subprocess
    from PIL import Image
    out = []
    for job in json.load(open(os.path.join(work, "probe.json"))):
        for k, (b, r, ea, na) in enumerate(job["spots"]):
            p = os.path.join(work, "probe", "%s_%d.png" % (job["name"], k))
            if not os.path.exists(p):
                continue
            im = Image.open(p).convert("L"); big = p[:-4] + "_x4.png"
            im.resize((im.width * 4, im.height * 4), Image.LANCZOS).save(big)
            txt = subprocess.run(["tesseract", big, "-", "--psm", "6"], capture_output=True, text=True).stdout; os.remove(big)
            la, lo = dms(txt)
            hh = G.readouts_text(txt)
            if la is None or lo is None or not hh or hh[0][1] is None:
                continue
            n = (la - g["lat"]) * 110574.0; e = (lo - g["lon"]) * 111320.0 * math.cos(math.radians(g["lat"]))
            if math.hypot(e - ea, n - na) > 10.0:
                continue
            out.append([b, r, round(e, 2), round(n, 2), hh[0][1] - g["ge_alt"]])
    json.dump(out, open(os.path.join(HERE, "stand_probe.json"), "w"))
    print(len(out), "spots read")


if __name__ == "__main__" and sys.argv[1] in ("plan_stand", "read_stand"):
    {"plan_stand": plan_stand, "read_stand": read_stand}[sys.argv[1]](sys.argv[2])
