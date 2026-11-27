"""Which OpenStreetMap buildings are not solid blocks, and how to stand them up (shared by the grounds' surrounds.py).

Every ground's surroundings builder extrudes OSM building outlines to a height. A feature tagged `building=*` is not
always a building with walls: a tram or bus shelter, a carport, a canopy or an open pavilion is a roof on posts, and a
public artwork or a trackside equipment cabinet a metre or two across is not a building at all. Extruded to the
builders' 8 m default they stood as solid windowed blocks: Marvel's MPavilion 2015 (a petal canopy on thin stalks in
Docklands Park) read as an 8 m gear-shaped office block, its tram shelters as 8 m kiosks, its rail cabinets as 8 m
pillars (inspection of 2026-11-27).

    kind(tags, area_m2) -> "solid" | "open" | "omit"
    open_roof(tags)     -> (roof top, roof thickness) in metres above the ground, from the tags or a sourced size
    posts(ring, ...)    -> the posts under an open roof, as small square outlines

"omit" is only for features with no measured or published size that are too small to read from outside the ground
(under OMIT_AREA_M2): drawing them at a guessed height would be a placeholder, leaving them out is faithful at the
distance the surroundings are seen from.
"""
import math

# Open structures: a roof on posts, no walls.
OPEN_BUILDING = {"roof", "carport", "canopy", "shelter", "pavilion", "gazebo", "pergola", "bridge"}
OPEN_AMENITY = {"shelter"}
OPEN_MAN_MADE = {"canopy", "pergola"}
# Not buildings at all at a ground's surroundings' scale when small and unmeasured.
OMIT_AREA_M2 = 6.0

# Published sizes, by the feature's OSM name: (roof top m, roof thickness m, stalks, stalk width m). A tag (height,
# building:levels, min_height) always wins.
# MPavilion 2015 (AL_A, moved to Docklands Park): 13 large and 30 small petals, 3 and 5 m across and 2-3 mm thick,
# "hovering at three and four metres high" on 95 carbon-fibre stalks (Dezeen 2015-10-05; Architecture Australia
# Mar/Apr 2016, Kane; Arup). The petals are drawn as one thin canopy at 4 m over its OSM outline (the petals' edge
# as traced), 0.15 m deep so its edge reads, on 95 stalks spread evenly under it.
SIZES_BY_NAME = {"MPavillion 2015": (4.0, 0.15, 95, 0.06), "MPavilion 2015": (4.0, 0.15, 95, 0.06)}
# Tram and bus shelters: no published height was found (Yarra Trams' platform standard CE-019-ST-0039 gives none),
# so a shelter without a height tag is left out rather than stood up at a guess (kind() returns "omit").
SHELTER_TOP = None
ROOF_THICK = 0.3            # a shelter's or carport's roof sheet and its beam, seen from outside
POST_W = 0.15               # a steel post
POST_STEP = 6.0             # posts along the roof's outline, about one every 6 m (one at least at each end)


def _num(v):
    try:
        return float(str(v).replace("m", "").strip())
    except (TypeError, ValueError):
        return None


def kind(tags, area_m2):
    b = tags.get("building")
    open_ = (b in OPEN_BUILDING or tags.get("amenity") in OPEN_AMENITY or tags.get("man_made") in OPEN_MAN_MADE
             or tags.get("building:walls") == "no" or tags.get("covered") == "yes")
    tagged = any(k in tags for k in ("height", "building:levels", "roof:height", "min_height"))
    if not open_ and not tagged and area_m2 < OMIT_AREA_M2 and (b in ("service", "yes") or "tourism" in tags):
        return "omit"
    if open_:
        top, _ = open_roof(tags)
        return "open" if top else "omit"
    return "solid"


def open_roof(tags):
    """(top, thickness) above the ground under it, or (None, None) when no tag or published size gives one."""
    top = _num(tags.get("height"))
    if top is None and _num(tags.get("building:levels")) is not None:
        top = _num(tags.get("building:levels")) * 3.0
    if top is None:
        top = SIZES_BY_NAME.get(tags.get("name"), (None,))[0]
    if top is None and (tags.get("amenity") == "shelter" and tags.get("shelter_type") == "public_transport"):
        top = SHELTER_TOP
    if top is None:
        return None, None
    lo = _num(tags.get("min_height"))
    thick = SIZES_BY_NAME.get(tags.get("name"), (None, ROOF_THICK))[1] if lo is None else top - lo
    return top, max(0.1, thick)


def supports(tags, ring):
    """The posts or stalks under an open roof: an even spread of the published number when one is listed
    (SIZES_BY_NAME), else posts along the outline (posts())."""
    size = SIZES_BY_NAME.get(tags.get("name"))
    if not size:
        return posts(ring)
    return stalks(ring, size[2], size[3])


def _inside(pt, poly):
    x, y = pt
    c = False
    j = len(poly) - 1
    for i in range(len(poly)):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            c = not c
        j = i
    return c


def stalks(ring, count, w):
    """`count` square stalk outlines spread evenly (a square grid, then trimmed) inside the ring."""
    xs = [p[0] for p in ring]
    ys = [p[1] for p in ring]
    area = abs(sum(ring[k][0] * ring[(k + 1) % len(ring)][1] - ring[(k + 1) % len(ring)][0] * ring[k][1]
                   for k in range(len(ring)))) / 2
    step = math.sqrt(area / count)
    for _ in range(40):
        pts = [(x, y) for i in range(int((max(xs) - min(xs)) / step) + 2) for j in range(int((max(ys) - min(ys)) / step) + 2)
               for x, y in [(min(xs) + (i + 0.5) * step, min(ys) + (j + 0.5) * step)] if _inside((x, y), ring)]
        if len(pts) >= count:
            break
        step *= 0.97
    pts = pts[:: max(1, len(pts) // count)][:count]
    h = w / 2
    return [[(x - h, y - h), (x + h, y - h), (x + h, y + h), (x - h, y + h)] for x, y in pts]


def posts(ring, step=POST_STEP, w=POST_W, inset=0.4):
    """Square post outlines (lists of (x, y)) along the ring, `inset` m inside its corners: a post at each end of
    every side longer than `step` and one every `step` m between, so a shelter of 2 x 5 m stands on four."""
    n = len(ring)
    cx = sum(p[0] for p in ring) / n
    cy = sum(p[1] for p in ring) / n
    pts = []
    for k in range(n):
        a, c = ring[k], ring[(k + 1) % n]
        L = math.hypot(c[0] - a[0], c[1] - a[1])
        if L < 1.0:
            continue
        m = max(1, int(L // step))
        for s in range(m):
            t = s / m
            pts.append((a[0] + (c[0] - a[0]) * t, a[1] + (c[1] - a[1]) * t))
    out, seen = [], []
    for x, y in pts:
        d = math.hypot(cx - x, cy - y)
        if d > 1e-6:
            x += (cx - x) / d * min(inset, d * 0.5)
            y += (cy - y) / d * min(inset, d * 0.5)
        if any(math.hypot(x - sx, y - sy) < step * 0.5 for sx, sy in seen):
            continue
        seen.append((x, y))
        h = w / 2
        out.append([(x - h, y - h), (x + h, y - h), (x + h, y + h), (x - h, y + h)])
    return out
