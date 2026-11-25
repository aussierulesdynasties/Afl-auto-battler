"""Each ground's long axis against true north, for the sun over it in the 3D view.

    python3 tools/grounds/ground_axes.py [CACHE_DIR]

Reads every ground in data/ground_places.json, fetches the map round it from OpenStreetMap's own
API (api.openstreetmap.org, a 1.3 km box; cached in CACHE_DIR, default /tmp/ground_axes), takes
the biggest Australian-football pitch near the ground's point and measures its long axis (the
principal axis of its outline). Prints that bearing beside the one data/ground_places.json holds
and, for a ground with a model, the model's own (90 + GroundModels.FIT's angle: the models are
laid x east, z south). A model more than 10 degrees off the map is turned off true north, and
its "axis" takes the map's bearing, on the side nearest the model's. Looks only.
Map data (c) OpenStreetMap contributors, ODbL.
"""
import json
import math
import os
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
BOX = 0.006       # degrees each way round the ground's point
NEAR = 400.0      # metres: a pitch further than this from the point is another ground's


def en(lat, lon, lat0, lon0):
    return ((lon - lon0) * math.cos(math.radians(lat0)) * 111320.0, (lat - lat0) * 110574.0)


def pitch_axis(xml_bytes, lat, lon):
    """[bearing of the long axis 0-180, area m2, distance m] of the best pitch, or None."""
    root = ET.fromstring(xml_bytes)
    nodes = {n.get("id"): (float(n.get("lat")), float(n.get("lon"))) for n in root.findall("node")}
    best = None
    for w in root.findall("way"):
        tags = {t.get("k"): t.get("v") for t in w.findall("tag")}
        if tags.get("leisure") != "pitch":
            continue
        pts = [nodes[nd.get("ref")] for nd in w.findall("nd") if nd.get("ref") in nodes]
        if len(pts) < 6:
            continue
        lat0 = sum(p[0] for p in pts) / len(pts)
        lon0 = sum(p[1] for p in pts) / len(pts)
        xy = [en(p[0], p[1], lat0, lon0) for p in pts]
        area = 0.5 * abs(sum(xy[i][0] * xy[i - 1][1] - xy[i - 1][0] * xy[i][1] for i in range(len(xy))))
        dist = math.hypot(*en(lat0, lon0, lat, lon))
        if dist > NEAR or area < 10000.0:
            continue
        score = area * (3.0 if "australian" in tags.get("sport", "") else 1.0)
        if best is not None and score <= best[0]:
            continue
        sxx = sum(x * x for x, y in xy)
        syy = sum(y * y for x, y in xy)
        sxy = sum(x * y for x, y in xy)
        th = 0.5 * math.atan2(2.0 * sxy, sxx - syy)   # from east towards north
        best = (score, (90.0 - math.degrees(th)) % 180.0, area, dist)
    return None if best is None else best[1:]


def main():
    cache = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ground_axes"
    os.makedirs(cache, exist_ok=True)
    places = json.load(open(os.path.join(ROOT, "data", "ground_places.json")))["grounds"]
    src = open(os.path.join(ROOT, "scripts", "ui", "match", "GroundModels.gd")).read()
    fit = {m.group(1): float(m.group(2)) for m in
           re.finditer(r'"(\w+)": \[[-\d.]+, [-\d.]+, [-\d.]+, ([-\d.]+),', src)}
    slugs = dict(re.findall(r'"([^"]+)": "(\w+)"', src[src.index("const GROUNDS"):src.index("const FIT")]))
    print("%-36s %8s %8s %8s  %s" % ("ground", "held", "model", "map", "off"))
    for name, p in places.items():
        fn = os.path.join(cache, re.sub(r"\W", "_", name) + ".xml")
        if not os.path.exists(fn):
            url = "https://api.openstreetmap.org/api/0.6/map?bbox=%f,%f,%f,%f" % (
                p["lon"] - BOX, p["lat"] - BOX, p["lon"] + BOX, p["lat"] + BOX)
            req = urllib.request.Request(url, headers={"User-Agent": "ground-axes-check"})
            open(fn, "wb").write(urllib.request.urlopen(req, timeout=60).read())
            time.sleep(1.0)
        got = pitch_axis(open(fn, "rb").read(), p["lat"], p["lon"])
        slug = slugs.get(name, "")
        model = (90.0 + fit[slug]) % 360.0 if slug in fit else None
        off = ""
        if got is not None and model is not None:
            d = (got[0] - model + 90.0) % 180.0 - 90.0
            off = "%+.1f" % d
        print("%-36s %8s %8s %8s  %s" % (name, p.get("axis", "-"),
              "-" if model is None else "%.1f" % model, "-" if got is None else "%.1f" % got[0], off))


if __name__ == "__main__":
    main()
