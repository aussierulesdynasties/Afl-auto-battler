"""Hand-made sign lettering as flat geometry (no photo pixels). Glyph outlines come from DejaVu Sans Bold (Bitstream Vera
licence: free to use, embed and sell; bundled with matplotlib). Each word is stretched to the box it fills in the
reference photo, then triangulated (constrained Delaunay, holes kept) so the letters are real faces in the model."""
import numpy as np
import shapely
from shapely.geometry import Polygon
from matplotlib.textpath import TextPath
from matplotlib.font_manager import FontProperties

FONT = FontProperties(family='DejaVu Sans', weight='bold')
FONTS = {'bold': FONT, 'normal': FontProperties(family='DejaVu Sans', weight='normal')}


def glyph_polys(text, weight='bold'):
    """the word's outline as shapely polygons (holes cut), in font units"""
    tp = TextPath((0, 0), text, size=10, prop=FONTS[weight])
    rings = [np.array(r) for r in tp.to_polygons() if len(r) >= 3]
    polys = sorted([Polygon(r).buffer(0) for r in rings], key=lambda q: -q.area)
    # even-odd: a ring inside an odd number of other rings is a hole
    out = None
    for i, p in enumerate(polys):
        depth = sum(1 for j, q in enumerate(polys) if j != i and q.area > p.area and q.contains(p.representative_point()))
        out = (p if out is None else (out.difference(p) if depth % 2 else out.union(p)))
    return out


def word_tris(text, box, weight='bold'):
    """triangles of the word filling box (u0, v0, u1, v1) in sign units: returns (V Nx2, T Mx3)"""
    g = glyph_polys(text, weight) if isinstance(text, str) else text   # a word, or a ready shapely shape
    x0, y0, x1, y1 = g.bounds
    u0, v0, u1, v1 = box
    sx, sy = (u1 - u0) / (x1 - x0), (v1 - v0) / (y1 - y0)
    V, T = [], []
    geoms = g.geoms if hasattr(g, 'geoms') else [g]
    for p in geoms:
        tri = shapely.constrained_delaunay_triangles(p)
        for t in tri.geoms:
            c = np.array(t.exterior.coords)[:3]
            o = len(V)
            V += [(u0 + (x - x0) * sx, v0 + (y - y0) * sy) for x, y in c]
            T.append((o, o + 1, o + 2))
    return np.array(V, float), np.array(T, int)


def place(text, o, a, b, box, weight='bold'):
    """3D triangles of text filling box (u0, v0, u1, v1) in a sign frame: point o, reading direction a, letter-up direction b
    (unit 3-vectors, metres); returns (V Nx3, T Mx3), both faces"""
    V2, T = word_tris(text, box, weight)
    o, a, b = (np.asarray(x, float) for x in (o, a, b))
    V = o + V2[:, :1] * a + V2[:, 1:] * b
    return V, np.r_[T, T[:, ::-1]]


def ring(cx, cy, ro, ri, gap0=None, gap1=None):
    """a ring (annulus) as a shapely shape, optionally open between angles gap0..gap1 (degrees)"""
    from shapely.geometry import Point
    g = Point(cx, cy).buffer(ro, 64).difference(Point(cx, cy).buffer(ri, 64))
    if gap0 is not None:
        A = np.radians(np.linspace(gap0, gap1, 16)); R = ro * 2
        g = g.difference(Polygon([(cx, cy)] + [(cx + R * np.cos(x), cy + R * np.sin(x)) for x in A]))
    return g
