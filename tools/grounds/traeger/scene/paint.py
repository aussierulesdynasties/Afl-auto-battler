"""The near scene's ground map, painted from OpenStreetMap over Sentinel-2's ground colour.

The base is the land's own colour at 10 m from Sentinel-2 (graded as the far scene's), with every cell
under a roof or a canopy filled in from the open ground round it, so roofs and trees do not stain the yards.
Over it, sharp at the map's resolution: the sports grounds (turf, the baseball diamond's infield, the
hockey turf, the tennis and netball courts), car parks, roads with their lane lines, paths, pools, and each
building's slab. The trees' shade is painted under their canopies (they take no sun shadow in the game).
Colours are Google Earth's (sampled off its straight-down views of Alice Springs, qa/).
"""
import math

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage

import geo
import grade

ASPHALT = (92, 92, 94)
ASPHALT_OLD = (110, 106, 102)
PARKING = (104, 101, 98)
GRAVEL = (152, 128, 108)
CONCRETE = (172, 168, 160)
PATH = (176, 170, 158)
TRACK = (170, 120, 86)        # a red dirt track
PITCH = (78, 112, 52)         # Google Earth: the irrigated ovals, a deep green
LAWN = (108, 122, 66)
INFIELD = (184, 112, 76)      # the baseball diamond's red clay
HOCKEY = (70, 128, 104)       # Google Earth: the hockey turf, sea green
HOCKEY_RUN = (52, 96, 168)    # its blue run-offs
TENNIS_GREEN = (64, 104, 70)
TENNIS_BLUE = (62, 100, 170)
POOL = (86, 160, 196)
SLAB = (182, 176, 166)
LINE = (232, 232, 226)
LINE_Y = (214, 186, 70)

WIDTH = {"motorway": 16, "trunk": 13, "trunk_link": 7, "primary": 12, "primary_link": 7, "secondary": 11,
         "secondary_link": 7, "tertiary": 9, "residential": 8, "unclassified": 7, "service": 5,
         "living_street": 6, "pedestrian": 4, "footway": 2.0, "path": 1.8, "cycleway": 2.5, "steps": 2.5,
         "track": 3.5}


class Canvas:
    """A north-up map, `size` pixels a side over east/north -r..r."""

    def __init__(self, r, size, cx=0.0, cy=0.0):
        self.r, self.size, self.cx, self.cy = r, size, cx, cy
        self.k = size / (2 * r)

    def px(self, e, n):
        return ((e - self.cx + self.r) * self.k, (self.r - (n - self.cy)) * self.k)

    def pts(self, p):
        return [self.px(*q) for q in p]

    def grid(self):
        c = (np.arange(self.size) + 0.5) / self.k - self.r
        E, N = np.meshgrid(c + self.cx, -c + self.cy)
        return E, N


def base_colour(cv, buildings, ndvi_r=None):
    """Sentinel-2's ground colour at 10 m, roofs and canopies filled from the open ground round them."""
    R = 1500
    s2 = geo.s2_local("TCI", R, 300)               # 10 m cells over the near area
    red = geo.s2_local("B04", R, 300)[..., 0]
    nir = geo.s2_local("B08", R, 300)[..., 0]
    nd = (nir - red) / (nir + red + 1e-6)
    s2 = grade.grade(s2).astype(np.float32)
    cs = Canvas(R, 300)
    roof = Image.new("L", (300, 300), 0)
    d = ImageDraw.Draw(roof)
    for t, p in buildings:
        d.polygon(cs.pts(p), fill=255)
    roofm = np.asarray(roof.filter(ImageFilter.MaxFilter(3))) > 0
    canopy = (nd > 0.33) & ~roofm
    bad = roofm | canopy
    # Fill the bad cells from the nearest good ones (then soften), a ground colour under every roof and tree.
    idx = ndimage.distance_transform_edt(bad, return_distances=False, return_indices=True)
    filled = s2[idx[0], idx[1]]
    filled = ndimage.gaussian_filter(filled, (1.2, 1.2, 0))
    out = np.where(bad[..., None], filled, s2)
    # Under a canopy the leaf litter is a little darker and browner.
    out = np.where(canopy[..., None], out * np.array([0.92, 0.88, 0.85]), out)
    # To the canvas: bicubic, then grain at two scales (the earth's own unevenness).
    E, N = cv.grid()
    from scipy.ndimage import map_coordinates
    pxx = (E + R) / (2 * R) * 300 - 0.5
    pyy = (R - N) / (2 * R) * 300 - 0.5
    img = np.stack([map_coordinates(out[..., c], [pyy, pxx], order=3, mode="nearest") for c in range(3)], -1)
    rng = np.random.default_rng(3)
    s = cv.size
    g1 = np.asarray(Image.fromarray((rng.random((s // 8, s // 8)) * 255).astype(np.uint8)).resize((s, s), Image.BICUBIC), np.float32) / 255 - 0.5
    g2 = rng.random((s, s)).astype(np.float32) - 0.5
    img = img * (1 + 0.07 * g1[..., None]) + 9 * g2[..., None]
    return img, nd


def draw_world(cv, img, ways, extra=None):
    """Draw OpenStreetMap's areas, roads, courts and slabs onto img (float RGB, rows north to south)."""
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    lw = lambda m: max(1, int(round(m * cv.k)))

    def area(t):
        if t.get("leisure") == "swimming_pool" or t.get("amenity") == "fountain":
            return POOL
        if t.get("amenity") == "parking" and t.get("parking") not in ("underground", "multi-storey"):
            return ASPHALT_OLD if t.get("surface") in (None, "asphalt", "paved") else GRAVEL
        if t.get("leisure") == "pitch":
            sp = t.get("sport", "")
            if "tennis" in sp or "netball" in sp or "basketball" in sp:
                return TENNIS_BLUE if t.get("surface") in ("acrylic", "hard") else TENNIS_GREEN
            if "hockey" in sp:
                return HOCKEY
            if t.get("surface") in ("sand", "dirt"):
                return TRACK
            return PITCH
        if t.get("landuse") == "grass" or t.get("leisure") in ("garden",):
            return LAWN
        if t.get("natural") == "sand" or t.get("natural") == "bare_rock":
            return None
        return None

    areas = [(t, p) for _, t, p in ways if len(p) > 3 and p[0] == p[-1] and area(t)]
    areas.sort(key=lambda a: -abs(_area(a[1])))
    for t, p in areas:
        d.polygon(cv.pts(p), fill=area(t))
    if extra:
        extra(cv, d, im)
    order = sorted([(WIDTH[t["highway"]], t, p) for _, t, p in ways
                    if t.get("highway") in WIDTH and len(p) > 1 and t.get("tunnel") != "yes"
                    and t.get("area") != "yes"], key=lambda a: a[0])
    for w, t, p in order:
        hw = t["highway"]
        if hw in ("footway", "path", "cycleway", "steps", "pedestrian"):
            fill = PATH if t.get("surface") not in ("dirt", "ground", "unpaved", "gravel") else TRACK
        elif hw == "track" or t.get("surface") in ("dirt", "ground", "unpaved", "gravel", "compacted"):
            fill = TRACK
        elif t.get("service") == "parking_aisle":
            fill = PARKING
        else:
            fill = ASPHALT
        d.line(cv.pts(p), fill=fill, width=lw(w), joint="curve")
    # Lane lines on the bigger roads: a dashed white centre line (3 m paint, 9 m gap).
    for w, t, p in order:
        if t["highway"] in ("trunk", "primary", "secondary", "tertiary") and cv.k > 0.5:
            _dashes(d, cv, p, 3.0, 9.0, LINE, lw(0.12))
    return np.asarray(im, np.float32)


def lane_lines(cv, img, ways):
    """The dashed white centre line on the bigger roads (3 m of paint, 9 m gap), from OpenStreetMap."""
    if cv.k < 0.5:
        return img
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    for _, t, p in ways:
        if t.get("highway") in ("trunk", "primary", "secondary", "tertiary") and len(p) > 1 \
                and t.get("tunnel") != "yes" and t.get("oneway") != "yes":
            _dashes(d, cv, p, 3.0, 9.0, LINE, max(1, int(round(0.12 * cv.k))))
    return np.asarray(im, np.float32)


def _dashes(d, cv, p, on, off, col, w):
    acc = 0.0
    for a, b in zip(p[:-1], p[1:]):
        L = math.dist(a, b)
        t = 0.0
        while t < L:
            k = (acc + t) % (on + off)
            if k < on:
                t1 = min(L, t + on - k)
                q0 = (a[0] + (b[0] - a[0]) * t / L, a[1] + (b[1] - a[1]) * t / L)
                q1 = (a[0] + (b[0] - a[0]) * t1 / L, a[1] + (b[1] - a[1]) * t1 / L)
                d.line([cv.px(*q0), cv.px(*q1)], fill=col, width=w)
                t = t1
            else:
                t += on + off - k
        acc += L


def shade(cv, img, trees):
    """Soft shade under each canopy: darker and warmer (the game's sun casts none past 160 m)."""
    m = Image.new("L", (cv.size, cv.size), 0)
    d = ImageDraw.Draw(m)
    for e, n, h, rad in trees:
        x, y = cv.px(e, n)
        r = rad * cv.k * 0.9
        d.ellipse((x - r, y - r, x + r, y + r), fill=170)
    m = np.asarray(m.filter(ImageFilter.GaussianBlur(max(1.0, 1.2 * cv.k))), np.float32) / 255
    return img * (1 - 0.45 * m)[..., None] + np.array([10.0, 2.0, -6.0]) * m[..., None]


def _area(p):
    a = np.array(p)
    return 0.5 * np.sum(a[:-1, 0] * a[1:, 1] - a[1:, 0] * a[:-1, 1])
