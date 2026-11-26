"""Shared by Manuka's surroundings tools: the frame, the caches and the open data they read.

Frame: metres east (x) and north (y) of the model's origin, the node centroid of the OSM pitch way
4941717 (lat -35.3180995, lon 149.1345344), as tools/grounds/manuka/model/build.py. Heights are metres
above the field (574.4 m above sea level in the Terrarium tiles).

Sources (all open; credits in docs/CREDITS_3D.md):
- OpenStreetMap (ODbL): streets, land use, building footprints and levels, named places.
- ACT Government open data (CC BY 4.0, (c) Australian Capital Territory): ACTGOV_Mature_Trees_2020
  (LiDAR tree crowns and crown heights), ACTGOV_Tree_Assets (the public trees' species),
  ACTGOV_BUILDING_FOOTPRINTS (footprints OpenStreetMap lacks).
- Terrarium elevation tiles (Mapzen / AWS open data): the ground's shape and the hills.
Aerial imagery and Google Earth were looked at and measured from (roof colours, storeys); none of it is
copied into a file here.

The downloads are cached in $MANUKA_CACHE (default /tmp/manuka_cache).
"""
import json
import math
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

import numpy as np

LAT0, LON0 = -35.3180995, 149.1345344
KX = 111320.0 * math.cos(math.radians(LAT0))
KY = 110574.0
FIELD_ASL = 574.4
C = (4.7, -5.0)          # the field's centre
CACHE = os.environ.get("MANUKA_CACHE", "/tmp/manuka_cache")
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
ASSETS = os.path.join(REPO, "assets", "grounds", "manuka")
UA = {"User-Agent": "afl-ground-builder/1.0"}
SPAN, TILES = 2200.0, 3


def en(lat, lon):
    return ((lon - LON0) * KX, (lat - LAT0) * KY)


def latlon(e, n):
    return (LAT0 + n / KY, LON0 + e / KX)


def _get(url, path):
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
            data = r.read()
        with open(path, "wb") as f:
            f.write(data)
    return path


def osm_paths():
    """OpenStreetMap round the ground, 2.2 km a side in nine tiles."""
    dlat = SPAN / KY / TILES
    dlon = SPAN / KX / TILES
    lat0, lon0 = LAT0 - SPAN / 2 / KY, LON0 - SPAN / 2 / KX
    out = []
    for i in range(TILES):
        for j in range(TILES):
            a, b = lon0 + i * dlon, lat0 + j * dlat
            out.append(_get("https://api.openstreetmap.org/api/0.6/map?bbox=%f,%f,%f,%f" % (a, b, a + dlon, b + dlat),
                            os.path.join(CACHE, "osm_%d%d.osm" % (i, j))))
    return out


def load_osm():
    """(nodes {id: (e, n, tags)}, ways [(id, tags, [(e, n)...])]) with multipolygon outers as extra ways
    carrying the relation's tags, and inner rings marked role=inner."""
    nodes, raw, rels, seen = {}, {}, [], set()
    for p in osm_paths():
        root = ET.parse(p).getroot()
        for nd in root.iter("node"):
            nodes[nd.get("id")] = (*en(float(nd.get("lat")), float(nd.get("lon"))),
                                   {t.get("k"): t.get("v") for t in nd.iter("tag")})
        for w in root.iter("way"):
            raw.setdefault(w.get("id"), ({t.get("k"): t.get("v") for t in w.iter("tag")},
                                         [n.get("ref") for n in w.iter("nd")]))
        for r in root.iter("relation"):
            if r.get("id") in seen:
                continue
            seen.add(r.get("id"))
            rels.append(({t.get("k"): t.get("v") for t in r.iter("tag")},
                         [(m.get("type"), m.get("ref"), m.get("role")) for m in r.iter("member")]))
    ways = []
    for wid, (t, refs) in raw.items():
        ways.append((wid, t, [nodes[r][:2] for r in refs if r in nodes]))
    pts = {wid: [nodes[r][:2] for r in refs if r in nodes] for wid, (t, refs) in raw.items()}
    for t, mem in rels:
        if t.get("type") != "multipolygon":
            continue
        for typ, ref, role in mem:
            if typ == "way" and ref in pts and len(pts[ref]) > 2:
                tt = dict(t)
                if role == "inner":
                    tt = {"_inner": "yes", **{k: v for k, v in t.items() if k != "building"}}
                ways.append(("r" + ref, tt, pts[ref]))
    return nodes, ways


def act_layer(name, fields="*", r=1150.0):
    """An ACT Government open-data layer round the ground, as GeoJSON features."""
    path = os.path.join(CACHE, name + ".json")
    if not os.path.exists(path):
        url = "https://services1.arcgis.com/E5n4f1VY84i0xSjy/ArcGIS/rest/services/%s/FeatureServer/0/query" % name
        env = "%f,%f,%f,%f" % (LON0 - r / KX, LAT0 - r / KY, LON0 + r / KX, LAT0 + r / KY)
        out, off = [], 0
        while True:
            q = dict(where="1=1", geometry=env, geometryType="esriGeometryEnvelope", inSR=4326, outSR=4326,
                     spatialRel="esriSpatialRelIntersects", outFields=fields, f="geojson", resultOffset=off,
                     resultRecordCount=1000)
            with urllib.request.urlopen(url + "?" + urllib.parse.urlencode(q), timeout=180) as resp:
                fs = json.load(resp).get("features", [])
            out += fs
            off += len(fs)
            if len(fs) < 1000:
                break
        with open(path, "w") as f:
            json.dump({"type": "FeatureCollection", "features": out}, f)
    with open(path) as f:
        return json.load(f)["features"]


def rings(geom):
    """A GeoJSON polygon's outer rings in the frame."""
    polys = [geom["coordinates"]] if geom["type"] == "Polygon" else geom["coordinates"]
    return [[en(la, lo) for lo, la in poly[0]] for poly in polys]


def area(p):
    p = np.asarray(p, float)
    x, y = p[:, 0], p[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


class Dem:
    """Terrarium heights (m above the field) at zoom z, sampled bilinearly anywhere within r m."""

    def __init__(self, z, r):
        self.z, n = z, 2 ** z
        self.n = n
        x0, y0 = self.txy(LAT0 + r / KY, LON0 - r / KX)
        x1, y1 = self.txy(LAT0 - r / KY, LON0 + r / KX)
        self.X0, self.Y0 = int(x0), int(y0)
        nx, ny = int(x1) - self.X0 + 1, int(y1) - self.Y0 + 1
        from PIL import Image
        self.h = np.zeros((ny * 256, nx * 256), np.float32)
        for i in range(nx):
            for j in range(ny):
                p = _get("https://s3.amazonaws.com/elevation-tiles-prod/terrarium/%d/%d/%d.png" % (z, self.X0 + i, self.Y0 + j),
                         os.path.join(CACHE, "terrarium", "%d_%d_%d.png" % (z, self.X0 + i, self.Y0 + j)))
                a = np.asarray(Image.open(p).convert("RGB"), np.float32)
                self.h[j * 256:(j + 1) * 256, i * 256:(i + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
        self.h -= FIELD_ASL

    def txy(self, lat, lon):
        lat = np.asarray(lat, float)
        return ((np.asarray(lon, float) + 180) / 360 * self.n,
                (1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / math.pi) / 2 * self.n)

    def smooth(self, sigma_px):
        from scipy import ndimage
        self.h = ndimage.gaussian_filter(self.h, sigma_px)

    def at(self, e, n):
        lat, lon = latlon(np.asarray(e, float), np.asarray(n, float))
        x, y = self.txy(lat, lon)
        x = (x - self.X0) * 256 - 0.5
        y = (y - self.Y0) * 256 - 0.5
        x0 = np.clip(np.floor(x).astype(int), 0, self.h.shape[1] - 2)
        y0 = np.clip(np.floor(y).astype(int), 0, self.h.shape[0] - 2)
        fx, fy = np.clip(x - x0, 0, 1), np.clip(y - y0, 0, 1)
        h = self.h
        return (h[y0, x0] * (1 - fx) * (1 - fy) + h[y0, x0 + 1] * fx * (1 - fy)
                + h[y0 + 1, x0] * (1 - fx) * fy + h[y0 + 1, x0 + 1] * fx * fy)
