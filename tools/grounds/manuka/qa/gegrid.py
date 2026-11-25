"""Measuring grid on a Google Earth shot (MCG standard gate): projects points given in the stadium's polar frame
(compass bearing from the field centre, metres past the fence, height above the field) into a ge_compare view, so
heights and depths can be read off Google Earth. Model frame: x east, y north from the OSM pitch centroid.

    python3 gegrid.py <views.json> <name> <ge.png> <out.png>  [b0 b1 db]
"""
import json, math, os, sys
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__))
C = np.array([4.7, -5.0])                       # field centre (model metres)
G = json.load(open(os.path.join(HERE, '..', 'osm', 'geo.json')))
_p = np.array(G['pitch']) - C
_b = np.degrees(np.arctan2(_p[:, 0], _p[:, 1])) % 360; _r = np.hypot(_p[:, 0], _p[:, 1]); _o = np.argsort(_b)


def fence_r(b):
    return float(np.interp(b % 360, _b[_o], _r[_o], period=360))


def polar(b, d, z):
    a = math.radians(b); r = fence_r(b) + d
    return np.array([C[0] + r * math.sin(a), C[1] + r * math.cos(a), z])


def camera(v, W=1280, H=720, fov=23.5):
    e, n, u = v['at']; u = u + v.get('dz', 0.0); h, t, d = math.radians(v['h']), math.radians(v['t']), v['d']
    dirv = np.array([math.sin(t) * math.sin(h), math.sin(t) * math.cos(h), -math.cos(t)])
    tgt = np.array([e, n, u]); cam = tgt - d * dirv
    f = dirv / np.linalg.norm(dirv); r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r); up = np.cross(r, f)
    F = H / 2 / math.tan(math.radians(fov / 2))
    def proj(P):
        q = np.atleast_2d(P) - cam; x = q @ r; y = q @ up; z = q @ f
        return np.stack([W / 2 + F * x / z, H / 2 - F * y / z], 1), z
    return proj


if __name__ == '__main__':
    vf, name, src, out = sys.argv[1:5]
    b0, b1, db = (float(a) for a in sys.argv[5:8]) if len(sys.argv) > 7 else (None, None, 5.0)
    v = [x for x in json.load(open(vf)) if x['name'] == name][0]
    v['dz'] = float(os.environ.get('DZ', 0))
    proj = camera(v)
    im = Image.open(src).convert('RGB'); d = ImageDraw.Draw(im)
    if b0 is None:
        b0, b1 = v['h'] - 40, v['h'] + 40
    for b in np.arange(b0, b1 + 0.01, db):
        for dd, col in ((0, (255, 255, 0)), (10, (0, 255, 255)), (20, (255, 0, 255)), (30, (255, 128, 0))):
            P, z = proj([polar(b, dd, zz) for zz in range(0, 26, 1)])
            if (z > 0).all():
                d.line([tuple(p) for p in P], fill=col, width=1)
                for k in range(0, 26, 5):
                    d.ellipse([P[k][0] - 2, P[k][1] - 2, P[k][0] + 2, P[k][1] + 2], fill=col)
        P, z = proj([polar(b, 0, 0)])
        if z[0] > 0: d.text((P[0][0] + 3, P[0][1] + 3), '%d' % b, fill=(255, 255, 255))
    im.save(out)
