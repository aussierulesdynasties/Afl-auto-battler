"""OpenStreetMap round a ground, for the fault scan's real-world checks (roads under the stadium, missing
bridges and buildings, shelters built as solid blocks, blank lots).

    python3 tools/fault_scan/osm.py <slug> <out.json> [radius_m]

Reads the ground's centre from tools/grounds/terrain/grounds.json. Tries Overpass first, then the OSM
main API in small tiles. Writes every way (and multipolygon outer ring) with its tags, its points in
metres east and north of the centre circle. Data (c) OpenStreetMap contributors, ODbL.
"""
import json, math, os, sys, time, urllib.parse, urllib.request
import xml.etree.ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
UA = {"User-Agent": "afl-ground-fault-scan/1.0 (non-commercial)"}
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter",
            "https://maps.mail.ru/osm/tools/overpass/api/interpreter"]
KEYS = ["highway", "railway", "building", "building:part", "bridge", "man_made", "leisure", "landuse",
        "amenity", "natural", "water", "waterway", "shelter", "public_transport", "barrier", "tunnel"]


def centre(slug):
    g = json.load(open(os.path.join(ROOT, "tools/grounds/terrain/grounds.json")))[slug]
    return float(g["lat"]), float(g["lon"])


def enu(lat0, lon0, lat, lon):
    r = 6378137.0
    e = math.radians(lon - lon0) * r * math.cos(math.radians(lat0))
    n = math.radians(lat - lat0) * r
    return e, n


def bbox(lat0, lon0, rad):
    dlat = math.degrees(rad / 6378137.0)
    dlon = math.degrees(rad / (6378137.0 * math.cos(math.radians(lat0))))
    return lat0 - dlat, lon0 - dlon, lat0 + dlat, lon0 + dlon


def overpass(bb):
    s, w, n, e = bb
    box = "%.6f,%.6f,%.6f,%.6f" % (s, w, n, e)
    parts = "".join('way["%s"](%s);relation["%s"](%s);' % (k, box, k, box) for k in KEYS)
    q = "[out:json][timeout:180];(%s);out tags geom;" % parts
    data = urllib.parse.urlencode({"data": q}).encode()
    for url in OVERPASS:
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, data=data, headers=UA)
                return json.loads(urllib.request.urlopen(req, timeout=240).read())
            except Exception as ex:  # noqa: BLE001 - try the next mirror
                print("overpass %s failed: %s" % (url, ex))
                time.sleep(5)
    return None


def from_overpass(js, lat0, lon0):
    out = []
    for el in js.get("elements", []):
        tags = el.get("tags", {})
        if el["type"] == "way" and "geometry" in el:
            pts = [enu(lat0, lon0, p["lat"], p["lon"]) for p in el["geometry"]]
            out.append({"id": "w%d" % el["id"], "tags": tags, "pts": pts})
        elif el["type"] == "relation":
            for m in el.get("members", []):
                if m.get("type") == "way" and m.get("role") in ("outer", "") and "geometry" in m:
                    pts = [enu(lat0, lon0, p["lat"], p["lon"]) for p in m["geometry"]]
                    out.append({"id": "r%d/w%d" % (el["id"], m["ref"]), "tags": tags, "pts": pts})
    return out


def from_api(bb, lat0, lon0):
    s, w, n, e = bb
    nodes, ways, rels = {}, {}, []
    step = 0.004
    lat = s
    while lat < n:
        lon = w
        while lon < e:
            url = "https://api.openstreetmap.org/api/0.6/map?bbox=%.5f,%.5f,%.5f,%.5f" % (
                lon, lat, min(lon + step, e), min(lat + step, n))
            for attempt in range(4):
                try:
                    xml = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180).read()
                    break
                except Exception as ex:  # noqa: BLE001
                    print("osm api failed (%s), retrying" % ex)
                    time.sleep(10 * (attempt + 1))
            else:
                raise SystemExit("OSM API unreachable")
            root = ET.fromstring(xml)
            for nd in root.iter("node"):
                nodes[nd.get("id")] = (float(nd.get("lat")), float(nd.get("lon")))
            for wy in root.iter("way"):
                ways[wy.get("id")] = ([x.get("ref") for x in wy.iter("nd")],
                                      {t.get("k"): t.get("v") for t in wy.iter("tag")})
            for rl in root.iter("relation"):
                rels.append(({t.get("k"): t.get("v") for t in rl.iter("tag")},
                             [(m.get("ref"), m.get("role")) for m in rl.iter("member") if m.get("type") == "way"]))
            time.sleep(1.0)
            lon += step
        lat += step
    out = []
    keyset = set(KEYS)

    def pts(refs):
        return [enu(lat0, lon0, *nodes[r]) for r in refs if r in nodes]

    for wid, (refs, tags) in ways.items():
        if keyset & set(tags):
            out.append({"id": "w" + wid, "tags": tags, "pts": pts(refs)})
    for tags, members in rels:
        if keyset & set(tags):
            for ref, role in members:
                if role in ("outer", "") and ref in ways:
                    out.append({"id": "r/w" + ref, "tags": tags, "pts": pts(ways[ref][0])})
    return out


def main():
    slug, path = sys.argv[1], sys.argv[2]
    rad = float(sys.argv[3]) if len(sys.argv) > 3 else 800.0
    lat0, lon0 = centre(slug)
    bb = bbox(lat0, lon0, rad)
    js = overpass(bb)
    feats = from_overpass(js, lat0, lon0) if js is not None else from_api(bb, lat0, lon0)
    src = "overpass" if js is not None else "osm-api"
    json.dump({"slug": slug, "lat": lat0, "lon": lon0, "radius": rad, "source": src,
               "licence": "(c) OpenStreetMap contributors, ODbL", "features": feats}, open(path, "w"))
    print("osm: %d features for %s from %s" % (len(feats), slug, src))


if __name__ == "__main__":
    main()
