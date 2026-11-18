"""Esri z19 mosaic <-> OSM metres. Overlay OSM ways on the mosaic."""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LAT0, LON0 = -34.915489777922076, 138.59627692467532
Z, TX0, TY0 = 19, 463986, 316464
N = 256 * 2 ** Z
def px2ll(px, py):
    X = TX0 * 256 + px; Y = TY0 * 256 + py
    lon = X / N * 360 - 180
    lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * Y / N))))
    return lat, lon
def ll2px(lat, lon):
    X = (lon + 180) / 360 * N
    s = math.sin(math.radians(lat)); Y = (0.5 - math.log((1 + s) / (1 - s)) / (4 * math.pi)) * N
    return X - TX0 * 256, Y - TY0 * 256
def m2ll(x, y):
    return LAT0 + y / 110574, LON0 + x / (math.cos(math.radians(LAT0)) * math.pi / 180 * 6378137)
def ll2m(lat, lon):
    return (lon - LON0) * math.cos(math.radians(LAT0)) * math.pi / 180 * 6378137, (lat - LAT0) * 110574
SH = [0.0, 0.0]  # mosaic shift in px applied to OSM (set by registration)
if os.path.exists(os.path.join(ROOT, 'esri/reg.json')): SH = json.load(open(os.path.join(ROOT, 'esri/reg.json')))
def m2px(x, y):
    a, b = ll2px(*m2ll(x, y)); return a + SH[0], b + SH[1]
def px2m(px, py):
    return ll2m(*px2ll(px - SH[0], py - SH[1]))
def ways():
    W = {}
    for f in ('osm/geo.json', 'osm/geo2.json'):
        g = json.load(open(os.path.join(ROOT, f), encoding='utf-8'))
        for k, v in g['ways'].items():
            pts = v if isinstance(v, list) else v['xy']
            W[k] = pts
    return W
if __name__ == '__main__':
    m = Image.open(os.path.join(ROOT, 'esri/mosaic.jpg')).convert('RGB'); d = ImageDraw.Draw(m)
    for k, pts in ways().items():
        try: P = [m2px(p[0], p[1]) for p in pts]
        except Exception: continue
        d.line(P, fill=(255, 0, 255), width=2)
    for t in json.load(open(os.path.join(ROOT, 'osm/geo.json'), encoding='utf-8'))['towers']:
        x, y = m2px(t[1], t[2]); d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=(0, 255, 255), width=2)
    out = sys.argv[1] if len(sys.argv) > 1 else 'esri/osm_ovl.jpg'
    m.save(os.path.join(ROOT, out)); print('saved', out)
