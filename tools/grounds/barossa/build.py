"""Barossa Park (Lyndoch, SA) to the MCG standard: the precinct as it stood for Gather Round 2026.

    python3 tools/grounds/barossa/build.py

Writes assets/grounds/barossa/barossa.glb, the seat files and seat_tmpl.bin. Everything is modelled in metres from
the references listed in README.md (the 2026 satellite for the plan; the clubrooms' and terraces' photos for heights
and detail). Nothing is painted on: piers, recesses, columns, braces, rails, slats, steps, mullions and the folded
roof are geometry. Textures carry only stone coursing, sheet ribs and surface grain. No lettering (the tower's
"BAROSSA PARK" sign is left off, as the Gabba's numbers were), no goalposts, nets or turf (the game draws those).
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import paint  # noqa: E402
from geom import Mesh, write_glb, _n  # noqa: E402
from plan import (FENCE, TOWERS, TEMP_STANDS, club, fence_r, polar, to3, bearing, interp, RING, dem_height, offsets)  # noqa: E402
from dem import Dem  # noqa: E402

import precinct as site  # noqa: E402
import oval2  # noqa: E402

OUT = os.path.join(HERE, "..", "..", "..", "assets", "grounds", "barossa")

M = {}       # material name -> glTF material
SEATS = []   # (transform 3x4 rows, colour)


def lin(c):
    """sRGB 0-255 -> linear 0-1"""
    c = np.asarray(c, float) / 255.0
    return tuple(np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4))


def materials():
    M.update({
        "sandstone": {"tex": paint.sandstone(), "rough": 0.9},
        "clad_dark": {"tex": paint.cladding((62, 64, 67)), "rough": 0.6},
        "clad_black": {"tex": paint.cladding((34, 35, 37), rib=0.4), "rough": 0.55},
        "steel_dark": {"col": lin((52, 54, 57)), "rough": 0.5, "metal": 0.3},
        "steel_maroon": {"col": lin((128, 28, 36)), "rough": 0.45, "metal": 0.2},
        "steel_galv": {"col": lin((176, 178, 176)), "rough": 0.45, "metal": 0.6},
        "steel_white": {"col": lin((232, 232, 228)), "rough": 0.5, "cull": False},
        "roof_white": {"tex": paint.roof_sheet(), "rough": 0.55},
        "roof_soffit": {"col": lin((196, 200, 196)), "rough": 0.8},
        "roof_dark": {"tex": paint.roof_sheet((70, 72, 74)), "rough": 0.6},
        "glass": {"col": lin((40, 52, 58)), "rough": 0.08, "metal": 0.5},
        "glass_light": {"col": lin((92, 110, 118)), "rough": 0.1, "metal": 0.45},
        "frame_dark": {"col": lin((40, 42, 44)), "rough": 0.5, "metal": 0.3},
        "concrete": {"tex": paint.concrete(), "rough": 0.9},
        "concrete_step": {"tex": paint.concrete((206, 202, 194), joints=0), "rough": 0.9},
        "roller": {"tex": paint.roller_door(), "rough": 0.5, "metal": 0.3},
        "door_white": {"col": lin((226, 226, 222)), "rough": 0.6},
        "soffit": {"col": lin((214, 214, 208)), "rough": 0.9},
        "picket": {"col": lin((240, 240, 236)), "rough": 0.6},
        "site": {"tex": None, "rough": 0.95},
        "led": {"col": lin((230, 232, 226)), "rough": 0.3, "emit": (0.0, 0.0, 0.0)},
        "scaffold": {"col": lin((168, 170, 170)), "rough": 0.4, "metal": 0.6},
        "seat_deck": {"tex": paint.seat_deck(), "rough": 0.5, "metal": 0.4},
        "riser_dark": {"col": lin((60, 64, 72)), "rough": 0.6},
        "stand_panel": {"col": lin((214, 216, 218)), "rough": 0.6},
        "tank": {"tex": paint.cladding((186, 188, 186), rib=0.076, metres=1.2), "rough": 0.45, "metal": 0.5},
        "mesh_fence": {"col": lin((30, 32, 32)), "rough": 0.6, "metal": 0.3},
        "rail_steel": {"col": lin((96, 84, 72)), "rough": 0.6, "metal": 0.5},
        "sleeper": {"col": lin((92, 76, 60)), "rough": 0.95},
        "kerb": {"col": lin((200, 198, 190)), "rough": 0.9},
        "brick_shed": {"tex": paint.cladding((74, 76, 78), rib=0.25), "rough": 0.6},
        "white_render": {"tex": paint.concrete((226, 224, 218), joints=0, seed=9), "rough": 0.9},
        "post_white": {"col": lin((238, 238, 234)), "rough": 0.5},
        "post_pad": {"col": lin((226, 226, 222)), "rough": 0.8},
        "net": {"tex": oval2.net_texture(), "alpha": "MASK", "cull": False, "rough": 0.9},
        "pitch_synthetic": {"tex": paint.flat((70, 112, 72), metres=2.0), "rough": 0.9},
        "shelter_roof": {"col": lin((200, 204, 206)), "rough": 0.4, "metal": 0.4, "cull": False},
    })


# ------------------------------------------------------------------ helpers in plan space

def P3(e, n, h):
    return np.array(to3(e, n, h), float)


def C3(u, v, h):
    """clubroom frame -> 3D"""
    e, n = club(u, v)
    return P3(e, n, h)


def quad_uv(m, mat, a, b, c, d):
    m.quad(mat, a, b, c, d)


def box_pts(m, mat, base4, h0, h1, mats=None, skip=()):
    """a box from four plan corners (counter-clockwise from above) between heights h0 and h1"""
    mats = mats or {}
    lo = [P3(e, n, h0) for e, n in base4]
    hi = [P3(e, n, h1) for e, n in base4]
    if "top" not in skip:
        m.quad(mats.get("top", mat), hi[0], hi[1], hi[2], hi[3]) if _ccw_up(hi) else m.quad(mats.get("top", mat), hi[3], hi[2], hi[1], hi[0])
    if "bottom" not in skip:
        m.quad(mats.get("bottom", mat), lo[3], lo[2], lo[1], lo[0]) if _ccw_up(lo) else m.quad(mats.get("bottom", mat), lo[0], lo[1], lo[2], lo[3])
    order = range(4) if _ccw_up(hi) else range(3, -1, -1)
    idx = list(order)
    for k in range(4):
        i, j = idx[k], idx[(k + 1) % 4]
        if ("side", k) in skip:
            continue
        m.quad(mats.get(("side", k), mats.get("side", mat)), lo[i], lo[j], hi[j], hi[i])


def _ccw_up(pts):
    a, b, c = pts[0], pts[1], pts[2]
    return np.cross(b - a, c - a)[1] > 0


def ubox(m, mat, u0, u1, v0, v1, h0, h1, **kw):
    box_pts(m, mat, [club(u0, v0), club(u1, v0), club(u1, v1), club(u0, v1)], h0, h1, **kw)


# ------------------------------------------------------------------ site

def build_site(dem):
    cls, E, N, b, off = site.classify()
    tex = site.paint_map(cls)
    M["site"]["tex"] = (tex, 2 * site.HALF, 2 * site.HALF)
    m = Mesh()
    step = 2.0
    g = np.arange(-site.HALF, site.HALF + 0.01, step)
    GE, GN = np.meshgrid(g, g)
    gb, goff = offsets(GE, GN)
    dh = dem.at_en(GE, GN)
    H, w = site.design(GE, GN, gb, goff, dh)
    # the arena itself sits a hand under the game's turf
    H = np.where(goff < -1.0, -0.05, H)
    n = len(g)
    V = np.stack([GE, H, -GN], -1)
    for i in range(n - 1):
        for j in range(n - 1):
            a, bq, c, d = V[i, j], V[i, j + 1], V[i + 1, j + 1], V[i + 1, j]
            uv = [((p[0] + site.HALF), (p[2] + site.HALF)) for p in (a, bq, c, d)]
            # rows go south in N (i grows north->? g ascends, so i is south->north); wind upward
            m.quad("site", a, bq, c, d, uv=uv)
    site_h = (g, H)
    return m, site_h


def height_at(site_h, e, n):
    g, H = site_h
    fx = (e - g[0]) / (g[1] - g[0])
    fy = (n - g[0]) / (g[1] - g[0])
    i0, j0 = int(np.clip(math.floor(fy), 0, len(g) - 2)), int(np.clip(math.floor(fx), 0, len(g) - 2))
    ax, ay = fx - j0, fy - i0
    return float(H[i0, j0] * (1 - ax) * (1 - ay) + H[i0, j0 + 1] * ax * (1 - ay) + H[i0 + 1, j0] * (1 - ax) * ay
                 + H[i0 + 1, j0 + 1] * ax * ay)


# ------------------------------------------------------------------ picket fence

def build_fence(m):
    """the white picket fence round the boundary: 1.1 m, 70 mm pickets with 50 mm gaps, 90 mm posts every 2.4 m,
    two rails on the outside face, on a concrete plinth (the 2025 photo from the north-east)."""
    pts = []
    # walk the ellipse at even spacing
    bb = np.linspace(0, 360, 20000, endpoint=False)
    xy = np.array([polar(x, 0.0) for x in bb])
    seg = np.linalg.norm(np.diff(np.vstack([xy, xy[:1]]), axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    L = s[-1]

    def at(d):
        d = d % L
        k = np.searchsorted(s, d) - 1
        f = (d - s[k]) / seg[k]
        p = xy[k] * (1 - f) + xy[(k + 1) % len(xy)] * f
        q = xy[(k + 1) % len(xy)] - xy[k]
        t = q / np.linalg.norm(q)
        return p, t

    ph = 1.1
    for k in range(int(L / 0.12)):
        p, t = at(k * 0.12)
        nrm = np.array((t[1], -t[0]))   # outward (clockwise walk -> right is outward)
        c = p + nrm * 0.0
        # picket: 70 x 19 mm with a rounded-off top (a low point)
        a0 = c - t * 0.035
        a1 = c + t * 0.035
        o = nrm * 0.0095
        corners = [a0 - o, a1 - o, a1 + o, a0 + o]
        box_pts(m, "picket", corners, 0.12, ph - 0.03, skip=("bottom",))
        top = P3(*c, ph)
        lo = [P3(*q, ph - 0.03) for q in corners]
        m.tri("picket", lo[0], lo[1], top)
        m.tri("picket", lo[1], lo[2], top)
        m.tri("picket", lo[2], lo[3], top)
        m.tri("picket", lo[3], lo[0], top)
    for k in range(int(L / 2.4)):
        p, t = at(k * 2.4 + 0.06)
        nrm = np.array((t[1], -t[0]))
        c = p + nrm * 0.06
        h = 0.045
        box_pts(m, "picket", [c - t * h - nrm * h, c + t * h - nrm * h, c + t * h + nrm * h, c - t * h + nrm * h], 0.0, ph + 0.05)
    # rails behind the pickets, 0.3 and 0.85 m, and the plinth
    for k in range(int(L / 2.4)):
        p0, t0 = at(k * 2.4)
        p1, t1 = at((k + 1) * 2.4)
        n0 = np.array((t0[1], -t0[0]))
        n1 = np.array((t1[1], -t1[0]))
        for hr in (0.3, 0.85):
            a = P3(*(p0 + n0 * 0.03), hr)
            b = P3(*(p1 + n1 * 0.03), hr)
            m.beam("picket", a, b, 0.04, 0.09)
        q = [p0 - n0 * 0.05, p1 - n1 * 0.05, p1 + n1 * 0.12, p0 + n0 * 0.12]
        box_pts(m, "concrete", q, -0.1, 0.12, skip=("bottom",))


# ------------------------------------------------------------------ light towers

def build_towers(m, site_h):
    for e, n in TOWERS:
        base = height_at(site_h, e, n)
        b = bearing(e, n)
        # the head faces the field's middle
        to_mid = _n(np.array((-e, -n)))
        side = np.array((to_mid[1], -to_mid[0]))
        top = 40.0
        m.tube("steel_galv", P3(e, n, base - 0.3), P3(e, n, base + top), 0.42, 0.2, seg=12)
        # base plate and footing collar
        m.tube("concrete", P3(e, n, base - 0.3), P3(e, n, base + 0.35), 0.8, 0.8, seg=12)
        # a small speaker / camera box at 6 m on the field side
        c = np.array((e, n)) + to_mid * 0.5
        box_pts(m, "steel_dark", [c - side * 0.2 - to_mid * 0.15, c + side * 0.2 - to_mid * 0.15,
                                  c + side * 0.2 + to_mid * 0.25, c - side * 0.2 + to_mid * 0.25], base + 5.6, base + 6.3)
        # access door at the foot
        c2 = np.array((e, n)) + to_mid * 0.43
        box_pts(m, "steel_galv", [c2 - side * 0.18 - to_mid * 0.02, c2 + side * 0.18 - to_mid * 0.02,
                                  c2 + side * 0.18 + to_mid * 0.03, c2 - side * 0.18 + to_mid * 0.03], base + 0.6, base + 1.6)
        # headframe: a 6 x 3.2 m frame of square steel, tilted 15 degrees to the field, 18 LED floods in three rows
        hc = np.array((e, n)) + to_mid * 0.6
        tilt = math.radians(15)
        up = np.array((0, 1, 0))
        fwd3 = np.array((to_mid[0], 0, -to_mid[1]))
        side3 = np.array((side[0], 0, -side[1]))
        ax_up = up * math.cos(tilt) + fwd3 * math.sin(tilt)
        o = P3(*hc, base + top)
        W, Hh = 6.0, 3.2
        corners = [o - side3 * W / 2, o + side3 * W / 2, o + side3 * W / 2 + ax_up * Hh, o - side3 * W / 2 + ax_up * Hh]
        for i in range(4):
            m.beam("steel_galv", corners[i], corners[(i + 1) % 4], 0.12)
        for r in range(1, 3):
            a = corners[0] + ax_up * Hh * r / 3
            m.beam("steel_galv", a, a + side3 * W, 0.08)
        # arm from the pole top to the frame
        m.beam("steel_galv", P3(e, n, base + top - 0.4), o + ax_up * 0.4, 0.2)
        m.beam("steel_galv", P3(e, n, base + top - 1.4), o + ax_up * 1.6, 0.14)
        for r in range(3):
            for k in range(6):
                cpt = corners[0] + side3 * (W * (k + 0.5) / 6) + ax_up * (Hh * (r + 0.5) / 3) + fwd3 * 0.18
                # each flood: a dark finned body with a pale lens to the field
                fx = _n(fwd3 * math.cos(tilt) - up * math.sin(tilt))
                body = [cpt - side3 * 0.3 - ax_up * 0.22, cpt + side3 * 0.3 - ax_up * 0.22,
                        cpt + side3 * 0.3 + ax_up * 0.22, cpt - side3 * 0.3 + ax_up * 0.22]
                back = [q - fx * 0.16 for q in body]
                m.quad("led", body[0], body[1], body[2], body[3]) if np.dot(np.cross(body[1] - body[0], body[3] - body[0]), fx) > 0 \
                    else m.quad("led", body[3], body[2], body[1], body[0])
                for i in range(4):
                    a, b2 = body[i], body[(i + 1) % 4]
                    m.quad("steel_dark", back[i], back[(i + 1) % 4], b2, a) if np.dot(np.cross(back[(i + 1) % 4] - back[i], a - back[i]), (a + b2) / 2 - cpt) > 0 \
                        else m.quad("steel_dark", a, b2, back[(i + 1) % 4], back[i])
                m.quad("steel_dark", back[3], back[2], back[1], back[0]) if np.dot(np.cross(back[2] - back[3], back[0] - back[3]), -fx) > 0 \
                    else m.quad("steel_dark", back[0], back[1], back[2], back[3])


# ------------------------------------------------------------------ clubrooms

L = 52.0          # length along the building
BAY = 6.5        # structural bay: the stone piers below and the maroon columns above
GF = 0.25         # ground floor level
DECK = 4.4        # first floor / deck level
FACE = 24.4       # ground floor face to the field (v)
DECK_EDGE = 25.1
UPPER = 20.5      # first floor glazing (v), set back behind the deck
WEST = 2.0        # first floor's west wall
VER_H = 7.3       # verandah roof
EAVE, RIDGE = 8.6, 12.2


def build_club(m):
    bays = int(L / BAY)
    # ---- ground floor: west and side walls in stone, the field face as stone piers with recessed bays
    # west wall (dark cladding over a stone plinth), with recessed windows
    ubox(m, "clad_dark", 0, L, -0.3, 0.0, -1.0, DECK, mats={"bottom": "clad_dark"})
    # end walls (stone)
    ubox(m, "sandstone", -0.4, 0.0, -0.3, FACE + 0.5, -1.0, 3.9)
    ubox(m, "sandstone", L, L + 0.4, -0.3, FACE + 0.5, -1.0, 3.9)
    types = ["door", "roller", "glass", "roller", "door", "roller", "glass", "door"]
    for k in range(bays):
        u0, u1 = k * BAY, (k + 1) * BAY
        # pier 1.1 m wide centred on each bay line (and the last)
        pw = 0.55
        ubox(m, "sandstone", u0 - pw if k else 0.0, u0 + pw, FACE, FACE + 0.5, -1.0, 3.9)
        # recess: back wall 1.4 m in, reveals and soffit in stone
        a, b = u0 + pw, u1 - pw
        back = FACE - 1.0
        t = types[k % len(types)]
        # side reveals
        for uu in (a, b):
            pass
        # soffit over the opening (stone lintel, full depth)
        ubox(m, "sandstone", a, b, back, FACE + 0.5, 3.2, 3.9)
        m.quad("soffit", C3(a, back, 3.2), C3(b, back, 3.2), C3(b, FACE + 0.5, 3.2), C3(a, FACE + 0.5, 3.2)) if False else None
        # back wall of the recess with its opening
        if t == "roller":
            ubox(m, "roller", a, b, back - 0.25, back, GF, 3.2, skip=("top",))
            # door head and guides (steel)
            ubox(m, "steel_dark", a, b, back, back + 0.25, 2.95, 3.2)
            ubox(m, "steel_dark", a, a + 0.12, back, back + 0.1, GF, 2.95)
            ubox(m, "steel_dark", b - 0.12, b, back, back + 0.1, GF, 2.95)
        elif t == "glass":
            ubox(m, "glass", a, b, back - 0.1, back, GF + 0.6, 3.0)
            ubox(m, "clad_dark", a, b, back - 0.25, back, GF, GF + 0.6)
            ubox(m, "clad_dark", a, b, back - 0.25, back, 3.0, 3.2)
            n = max(2, int(round((b - a) / 1.3)))
            for i in range(n + 1):
                uu = a + (b - a) * i / n
                ubox(m, "frame_dark", uu - 0.04, uu + 0.04, back, back + 0.12, GF + 0.6, 3.0)
            ubox(m, "frame_dark", a, b, back, back + 0.12, 2.2, 2.27)
        else:
            # pale render wall with two white doors set into it
            ubox(m, "white_render", a, b, back - 0.25, back, GF, 3.2)
            for dc in ((a + b) / 2 - 1.1, (a + b) / 2 + 1.1):
                ubox(m, "door_white", dc - 0.45, dc + 0.45, back, back + 0.05, GF, GF + 2.1)
                ubox(m, "frame_dark", dc - 0.5, dc + 0.5, back, back + 0.03, GF + 2.1, GF + 2.16)
        # floor of the recess
        ubox(m, "concrete", a, b, back, FACE + 0.5, GF - 0.3, GF, skip=("bottom",))
    # last pier
    ubox(m, "sandstone", L - 0.55, L, FACE, FACE + 0.5, -1.0, 3.9)
    # ---- deck: slab, dark fascia, slatted balustrade
    ubox(m, "concrete", 0, L, UPPER, DECK_EDGE, 3.9, DECK, mats={"bottom": "soffit"})
    ubox(m, "clad_dark", -0.05, L + 0.05, DECK_EDGE, DECK_EDGE + 0.08, 3.75, DECK + 0.05)
    _balustrade(m, [(0.1, DECK_EDGE - 0.15), (L - 0.1, DECK_EDGE - 0.15)], DECK, 1.1)
    _balustrade(m, [(0.1, DECK_EDGE - 0.15), (0.1, UPPER + 0.1)], DECK, 1.1)
    # ---- first floor: glazing to the deck, west wall, floor
    ubox(m, "concrete", 0, L, WEST, UPPER, 3.9, DECK, skip=("top",))
    ubox(m, "clad_dark", 0, L, WEST - 0.3, WEST, DECK, EAVE)
    ubox(m, "clad_dark", -0.3, 0.0, WEST, UPPER, DECK, EAVE)
    ubox(m, "clad_dark", L, L + 0.3, WEST, UPPER, DECK, EAVE)
    _glass_wall(m, 0.0, L, UPPER, DECK, EAVE)
    # west wall windows: ribbon of recessed glass on the first floor
    for k in range(bays):
        a, b = k * BAY + 1.0, (k + 1) * BAY - 1.0
        ubox(m, "glass", a, b, WEST - 0.42, WEST - 0.3, DECK + 0.9, DECK + 2.8)
        ubox(m, "frame_dark", a - 0.08, b + 0.08, WEST - 0.5, WEST - 0.3, DECK + 0.82, DECK + 0.9)
        ubox(m, "frame_dark", a - 0.08, b + 0.08, WEST - 0.5, WEST - 0.3, DECK + 2.8, DECK + 2.88)
    # ---- west annex (change rooms' lower wing): single storey, flat dark roof
    ubox(m, "clad_dark", 2.0, L - 6.0, -5.0, -0.3, -1.0, 4.2, mats={"top": "roof_dark"})
    for k in range(6):
        u = 4.0 + k * 6.5
        ubox(m, "glass", u, u + 2.4, -5.12, -5.0, 2.2, 3.2)
        ubox(m, "frame_dark", u - 0.08, u + 2.48, -5.2, -5.0, 3.2, 3.28)
    ubox(m, "frame_dark", 2.0, L - 6.0, -5.25, -4.9, 4.2, 4.5)
    # ---- maroon columns, knee braces and the verandah roof
    for k in range(bays + 1):
        u = min(max(k * BAY, 0.15), L - 0.15)
        ubox(m, "steel_maroon", u - 0.1, u + 0.1, DECK_EDGE - 0.45, DECK_EDGE - 0.25, DECK, VER_H)
        for s in (-1, 1):
            if (u + s * 1.4) < 0 or (u + s * 1.4) > L:
                continue
            m.beam("steel_maroon", C3(u, DECK_EDGE - 0.35, VER_H - 1.3), C3(u + s * 1.4, DECK_EDGE - 0.35, VER_H - 0.1), 0.12, 0.1)
        m.beam("steel_maroon", C3(u, DECK_EDGE - 0.35, VER_H - 0.1), C3(u, UPPER, VER_H - 0.1), 0.14, 0.18)
    ubox(m, "steel_maroon", 0, L, DECK_EDGE - 0.47, DECK_EDGE - 0.23, VER_H - 0.25, VER_H)
    ubox(m, "roof_dark", -0.2, L + 0.2, UPPER - 0.2, DECK_EDGE + 0.5, VER_H, VER_H + 0.18, mats={"bottom": "soffit"})
    ubox(m, "clad_dark", -0.2, L + 0.2, DECK_EDGE + 0.5, DECK_EDGE + 0.56, VER_H - 0.1, VER_H + 0.28)
    # ---- the folded roof: four gables, ridges across the building, white sheet with a white fascia. The folds are
    # where the satellite's sunlit and shaded slopes meet (0.2 m mosaic): valleys at u 5.4, 15.4, 24.8 and 36.9, the
    # ridges midway, the north gable the widest, so the highest (one pitch for all, as the photos show); south of
    # the first gable a flat roof.
    folds = [5.4, 15.4, 24.8, 36.9, L]
    pitch = math.tan(math.radians(29.0))
    v0, v1 = WEST - 1.2, DECK_EDGE + 0.4
    ubox(m, "roof_white", -0.6, folds[0], v0, v1, EAVE - 0.6, EAVE - 0.38, mats={"bottom": "roof_soffit"})
    for k in range(len(folds) - 1):
        u0, u1 = folds[k], folds[k + 1]
        um, ridge = (u0 + u1) / 2, EAVE + (u1 - u0) / 2 * pitch
        last = k == len(folds) - 2
        for (ua, ha), (ub, hb) in (((u0, EAVE), (um, ridge)),
                                   ((um, ridge), (u1 + (0.6 if last else 0), EAVE - (0.17 if last else 0)))):
            t = 0.22
            top = [C3(ua, v0, ha + t), C3(ub, v0, hb + t), C3(ub, v1, hb + t), C3(ua, v1, ha + t)]
            bot = [C3(ua, v0, ha), C3(ub, v0, hb), C3(ub, v1, hb), C3(ua, v1, ha)]
            _q(m, "roof_white", top, up=True)
            _q(m, "roof_soffit", bot, up=False)
            # fascia on both cut edges
            m.quad("steel_white", bot[1], bot[0], top[0], top[1])
            m.quad("steel_white", bot[3], bot[2], top[2], top[3])
        # gable infill: glazing to the field, dark cladding to the west, with mullions
        for vv, mat in ((UPPER, "glass"), (WEST, "clad_dark")):
            a, b, c = C3(u0, vv, EAVE), C3(u1, vv, EAVE), C3(um, vv, ridge)
            m.tri(mat, a, b, c)
            m.tri(mat, a, c, b)
            if mat == "glass":
                n = max(4, int(round((u1 - u0) / 1.6)))
                for i in range(1, n):
                    uu = u0 + (u1 - u0) * i / n
                    hh = EAVE + (ridge - EAVE) * (1 - abs(uu - um) / ((u1 - u0) / 2))
                    ubox(m, "frame_dark", uu - 0.04, uu + 0.04, UPPER, UPPER + 0.12, EAVE, hh)
    # the box gutters at each fold
    for u in folds:
        ubox(m, "steel_white", u - 0.25, u + 0.25, v0, v1, EAVE - 0.05, EAVE + 0.1)
    # ---- the tower at the north-east corner, on the field side (dark on the mosaic at u 52.6-58, v 20.5-26; the
    # photo from the north-east shows it standing over the stair's foot): dark grey box, a thin light trim at the top
    # (sign left off)
    t0, t1, tv0, tv1, th = L + 0.6, L + 6.0, 20.5, 26.0, 14.5
    ubox(m, "clad_black", t0, t1, tv0, tv1, -1.0, th)
    ubox(m, "steel_galv", t0 - 0.05, t1 + 0.05, tv0 - 0.05, tv1 + 0.05, th, th + 0.12)
    ubox(m, "frame_dark", t0 + 2.0, t0 + 2.6, tv1, tv1 + 0.1, 1.5, th - 1.0)
    # ---- the north stair: on the field side of the tower, rising south from the ground to the deck's north-east
    # corner; 23 risers, 0.3 m goings, a landing at deck level onto the deck; dark slat balustrades, a stone stringer
    nr = 23
    rise = (DECK - GF) / (nr + 1)
    sv0, sv1 = 26.1, 28.6
    top_u = L + 1.4
    foot = top_u + nr * 0.3
    for i in range(nr):
        ub = foot - i * 0.3
        ubox(m, "concrete_step", ub - 0.3, ub, sv0, sv1, GF - 0.2, GF + rise * (i + 1))
    ubox(m, "concrete_step", L - 1.2, top_u, DECK_EDGE - 0.2, sv1, 3.9, DECK, mats={"bottom": "soffit"})
    ubox(m, "sandstone", top_u, foot, sv0 - 0.4, sv0, -0.5, GF + 0.3)
    for vv in (sv0 + 0.05, sv1 - 0.05):
        _balustrade(m, [(foot + 0.2, vv), (top_u, vv)], None, 1.0, slope=(GF, DECK, foot, top_u))
    _balustrade(m, [(top_u, sv1 - 0.05), (L - 1.2, sv1 - 0.05)], DECK, 1.1)
    # ---- the south end: the first floor's glass box over a stone base
    _glass_wall_end(m, 0.0, WEST, UPPER, DECK, EAVE)


def _q(m, mat, pts, up=True):
    n = np.cross(pts[1] - pts[0], pts[3] - pts[0])
    if (n[1] > 0) == up:
        m.quad(mat, *pts)
    else:
        m.quad(mat, pts[3], pts[2], pts[1], pts[0])


def _faces(a, b, c, sgn):
    return True


def _glass_wall(m, u0, u1, v, h0, h1):
    m.quad("glass", C3(u0, v, h0), C3(u1, v, h0), C3(u1, v, h1), C3(u0, v, h1)) \
        if np.cross(C3(u1, v, h0) - C3(u0, v, h0), C3(u0, v, h1) - C3(u0, v, h0)).dot(_vdir()) > 0 \
        else m.quad("glass", C3(u0, v, h1), C3(u1, v, h1), C3(u1, v, h0), C3(u0, v, h0))
    n = int((u1 - u0) / 1.5625)
    for i in range(n + 1):
        u = u0 + (u1 - u0) * i / n
        ubox(m, "frame_dark", u - 0.04, u + 0.04, v, v + 0.14, h0, h1)
    for hh in (h0 + 0.05, h0 + 2.7, h1 - 0.05):
        ubox(m, "frame_dark", u0, u1, v, v + 0.14, hh - 0.04, hh + 0.04)


def _glass_wall_end(m, u, v0, v1, h0, h1):
    ubox(m, "glass", u - 0.35, u - 0.3, v0, v1, h0, h1)
    n = int((v1 - v0) / 1.5)
    for i in range(n + 1):
        v = v0 + (v1 - v0) * i / n
        ubox(m, "frame_dark", u - 0.45, u - 0.3, v - 0.04, v + 0.04, h0, h1)


def _vdir():
    e, n = club(0, 1)
    e0, n0 = club(0, 0)
    return np.array((e - e0, 0, -(n - n0)))


def _balustrade(m, line, h0, hgt, slope=None, along_v=False):
    """dark steel balustrade on line (u, v) -> (u, v): top rail, bottom rail, posts every 1.5 m, slats every 0.11 m.
    slope = (h_start, h_end, u_start, u_end) for a stair (heights follow u)"""
    (ua, va), (ub, vb) = line
    def hat(u, v=None):
        if slope is None:
            return h0
        h_s, h_e, u_s, u_e = slope
        x = v if along_v else u
        f = np.clip((x - u_s) / (u_e - u_s), 0, 1)
        return h_s + (h_e - h_s) * f
    Lh = math.hypot(ub - ua, vb - va)
    n = max(1, int(Lh / 0.11))
    for i in range(n + 1):
        f = i / n
        u, v = ua + (ub - ua) * f, va + (vb - va) * f
        h = hat(u, v)
        m.beam("frame_dark", C3(u, v, h + 0.1), C3(u, v, h + hgt - 0.05), 0.022, 0.05)
    for hh in (0.08, hgt - 0.02):
        m.beam("frame_dark", C3(ua, va, hat(ua, va) + hh), C3(ub, vb, hat(ub, vb) + hh), 0.05, 0.06)
    np_ = max(1, int(Lh / 1.5))
    for i in range(np_ + 1):
        f = i / np_
        u, v = ua + (ub - ua) * f, va + (vb - va) * f
        h = hat(u, v)
        m.beam("frame_dark", C3(u, v, h), C3(u, v, h + hgt), 0.06, 0.06)


# ------------------------------------------------------------------ terraces south of the clubrooms

def build_terraces(m):
    """concrete terraces stepping up from the concourse to the upper level: 7 steps, 1 m treads, 0.43 m risers, from
    11 m to 18 m outside the fence between bearings 262 and 283 (photos: the aerials and the clubrooms from the south),
    with a stair and handrails every 7 m and concrete end walls."""
    b0, b1 = 262.0, 283.0
    o0, n = 11.0, 7
    tread, rise = 1.0, 0.43
    bs = np.linspace(b0, b1, 40)
    for i in range(n):
        r0, r1 = o0 + i * tread, o0 + (i + 1) * tread
        h = 0.15 + rise * (i + 1)
        for k in range(len(bs) - 1):
            ba, bb = bs[k], bs[k + 1]
            pa0, pb0 = polar(ba, r0), polar(bb, r0)
            pa1, pb1 = polar(ba, r1), polar(bb, r1)
            box_pts(m, "concrete_step", [pa0, pb0, pb1, pa1], h - rise - 0.4, h, skip=("bottom", ("side", 1), ("side", 3)))
    # end walls
    for bb_, sgn in ((b0, -1), (b1, 1)):
        for i in range(n):
            pass
        q0 = polar(bb_, o0 - 0.3)
        q1 = polar(bb_, o0 + n * tread + 0.3)
        d = _n(np.array(polar(bb_ + sgn * 1, o0)) - np.array(q0)) * 0.3
        box_pts(m, "concrete", [q0, q1, tuple(np.array(q1) + d), tuple(np.array(q0) + d)], -0.2, 0.15 + rise * n + 0.9)
    # handrails down the terraces (stainless, posts at each tread)
    for bb_ in np.arange(b0 + 3.5, b1 - 1, 5.2):
        pts = []
        for i in range(n + 1):
            r = o0 + i * tread - 0.5 if i else o0 - 0.4
            h = 0.15 + rise * i
            pts.append(P3(*polar(bb_, r), h + 0.95))
            m.tube("steel_galv", P3(*polar(bb_, r), h), P3(*polar(bb_, r), h + 0.95), 0.025, seg=6, caps=False)
        for a, b in zip(pts[:-1], pts[1:]):
            m.tube("steel_galv", a, b, 0.024, seg=6, caps=False)


# ------------------------------------------------------------------ viewing pavilion (south-west)

def build_pavilion(m):
    """the viewing pavilion on the concourse south of the terraces: a stone-ended base of glass, a glazed viewing box
    above, both under a thin white flat roof that overhangs to the field (2025 aerial and the clubrooms photo)."""
    b = 251.0
    c = np.array(polar(b, 13.5))
    out = _n(c)                          # away from the field
    tan = np.array((out[1], -out[0]))
    def Q(a, d):
        p = c + tan * a + out * d
        return (p[0], p[1])
    # base: 16 x 8, 3.4 m, stone ends, glass to the field
    box_pts(m, "sandstone", [Q(-8, -4), Q(-7.5, -4), Q(-7.5, 4), Q(-8, 4)], -0.5, 3.4)
    box_pts(m, "sandstone", [Q(7.5, -4), Q(8, -4), Q(8, 4), Q(7.5, 4)], -0.5, 3.4)
    box_pts(m, "clad_dark", [Q(-7.5, 3.6), Q(7.5, 3.6), Q(7.5, 4), Q(-7.5, 4)], -0.5, 3.4)
    box_pts(m, "glass", [Q(-7.5, -3.5), Q(7.5, -3.5), Q(7.5, -3.4), Q(-7.5, -3.4)], 0.15, 3.0)
    for k in range(11):
        a = -7.5 + 15 * k / 10
        box_pts(m, "frame_dark", [Q(a - 0.04, -3.6), Q(a + 0.04, -3.6), Q(a + 0.04, -3.4), Q(a - 0.04, -3.4)], 0.15, 3.0)
    box_pts(m, "clad_dark", [Q(-7.5, -3.6), Q(7.5, -3.6), Q(7.5, 3.6), Q(-7.5, 3.6)], 3.0, 3.6)
    # upper viewing box: 10 x 5.5, glass all round with a dark frame, 3 m
    box_pts(m, "concrete", [Q(-8.2, -4.4), Q(8.2, -4.4), Q(8.2, 4.2), Q(-8.2, 4.2)], 3.4, 3.65)
    box_pts(m, "glass", [Q(-5, -2.6), Q(5, -2.6), Q(5, 2.9), Q(-5, 2.9)], 3.65, 6.4, skip=("top",))
    for k in range(9):
        a = -5 + 10 * k / 8
        box_pts(m, "frame_dark", [Q(a - 0.05, -2.72), Q(a + 0.05, -2.72), Q(a + 0.05, -2.6), Q(a - 0.05, -2.6)], 3.65, 6.4)
    _rail(m, [Q(-8.0, -4.2), Q(8.0, -4.2)], 3.65)
    # white flat roof on four slim white columns, overhanging the field side by 2.5 m
    for a, d in ((-6.5, -3.9), (6.5, -3.9), (-6.5, 3.6), (6.5, 3.6)):
        box_pts(m, "steel_white", [Q(a - 0.08, d - 0.08), Q(a + 0.08, d - 0.08), Q(a + 0.08, d + 0.08), Q(a - 0.08, d + 0.08)], 3.65, 6.6)
    box_pts(m, "steel_white", [Q(-8.6, -6.4), Q(8.6, -6.4), Q(8.6, 4.4), Q(-8.6, 4.4)], 6.6, 6.95, mats={"top": "roof_white", "bottom": "soffit"})


def _rail(m, line, h):
    a, b = (np.array(p) for p in line)
    L_ = np.linalg.norm(b - a)
    n = int(L_ / 0.12)
    for i in range(n + 1):
        p = a + (b - a) * i / n
        m.beam("frame_dark", P3(*p, h + 0.05), P3(*p, h + 1.05), 0.02, 0.04)
    m.beam("frame_dark", P3(*a, h + 1.05), P3(*b, h + 1.05), 0.05, 0.05)


# ------------------------------------------------------------------ temporary grandstands (Gather Round 2026)

SEAT_COL = "seat_barossa_blue"


def build_temp_stands(m, site_h):
    """Hired tiered grandstands: an aluminium deck of 0.8 m rows rising 0.38 m, blue moulded seats every 0.5 m, a
    1.1 m white fascia panel and rail at the front, rails up the sides and across the back, aisle stairs at each end
    and in the middle, and the scaffold frame underneath (standards every 2 m, ledgers, diagonal braces)."""
    for S in TEMP_STANDS:
        a, b = np.array(S["a"], float), np.array(S["b"], float)
        t = _n(b - a)
        o = np.array((t[1], -t[0]))
        if np.dot(o, (a + b) / 2) < 0:
            o = -o
        W = float(np.linalg.norm(b - a))
        rows, row = S["rows"], S["depth"] / S["rows"]
        rise = 0.38
        g0 = min(height_at(site_h, *a), height_at(site_h, *b))
        base = g0 + 0.9                  # first tread
        def Q(s, d):
            p = a + t * s + o * d
            return (p[0], p[1])
        aisles = [(0.0, 1.1), (W / 2 - 0.55, W / 2 + 0.55), (W - 1.1, W)]
        for r in range(rows):
            d0, d1 = r * row, (r + 1) * row
            h = base + r * rise
            # tread and riser
            box_pts(m, "seat_deck", [Q(0, d0), Q(W, d0), Q(W, d1), Q(0, d1)], h - 0.06, h, skip=("bottom",))
            box_pts(m, "riser_dark", [Q(0, d1 - 0.03), Q(W, d1 - 0.03), Q(W, d1), Q(0, d1)], h, h + rise)
            # aisle half-steps
            for s0, s1 in aisles:
                box_pts(m, "seat_deck", [Q(s0, d0 + row / 2), Q(s1, d0 + row / 2), Q(s1, d1), Q(s0, d1)], h, h + rise / 2)
            # seats between the aisles
            for s0, s1 in ((aisles[0][1], aisles[1][0]), (aisles[1][1], aisles[2][0])):
                n = int((s1 - s0 - 0.1) / 0.5)
                for i in range(n):
                    s = s0 + 0.3 + i * 0.5
                    p = np.array(Q(s, d0 + 0.42))
                    SEATS.append((p, h, t, o, SEAT_COL))
        top = base + rows * rise
        D = S["depth"]
        # front fascia panel and rail
        box_pts(m, "stand_panel", [Q(-0.05, -0.08), Q(W + 0.05, -0.08), Q(W + 0.05, 0.0), Q(-0.05, 0.0)], g0, base + 1.0)
        _rail_line(m, Q(0, -0.04), Q(W, -0.04), base + 1.0, 0.0)
        # back rail and back panel
        box_pts(m, "stand_panel", [Q(-0.05, D), Q(W + 0.05, D), Q(W + 0.05, D + 0.06), Q(-0.05, D + 0.06)], g0, top + 1.1)
        # side panels (triangular-ish: full height at the back) and side rails
        for s in (0.0, W):
            pts = [Q(s, 0), Q(s, D)]
            for k in range(rows):
                h = base + k * rise
                box_pts(m, "stand_panel", [Q(s - 0.03, k * row), Q(s + 0.03, k * row), Q(s + 0.03, (k + 1) * row), Q(s - 0.03, (k + 1) * row)], g0, h + 0.02)
            _rail_line(m, Q(s, 0.2), Q(s, D), base + 1.1, rise / row)
        # scaffold underneath: standards on a 2 m x 1.6 m grid up to each tread, ledgers at 0.9 m lifts, braces
        ns = int(W / 2.0) + 1
        nd = int(D / 1.6) + 1
        for i in range(ns):
            s = min(i * 2.0, W - 0.1) + 0.05
            for j in range(nd):
                d = min(j * 1.6, D - 0.1) + 0.05
                h = base + int(d / row) * rise - 0.06
                m.tube("scaffold", P3(*Q(s, d), g0 - 0.1), P3(*Q(s, d), h), 0.024, seg=6, caps=False)
            for lift in np.arange(g0 + 0.3, top, 0.9):
                for j in range(nd - 1):
                    d_a, d_b = min(j * 1.6, D - 0.1) + 0.05, min((j + 1) * 1.6, D - 0.1) + 0.05
                    if base + int(d_a / row) * rise > lift:
                        m.tube("scaffold", P3(*Q(s, d_a), lift), P3(*Q(s, d_b), lift), 0.024, seg=6, caps=False)
        for j in range(nd):
            d = min(j * 1.6, D - 0.1) + 0.05
            hmax = base + int(d / row) * rise - 0.06
            for lift in np.arange(g0 + 0.3, hmax, 0.9):
                m.tube("scaffold", P3(*Q(0.05, d), lift), P3(*Q(W - 0.05, d), lift), 0.024, seg=6, caps=False)
            # diagonal braces in alternate bays along the back
            if j == nd - 1:
                for i in range(0, ns - 1, 2):
                    s_a, s_b = i * 2.0 + 0.05, min((i + 1) * 2.0, W - 0.1) + 0.05
                    m.tube("scaffold", P3(*Q(s_a, d), g0 + 0.2), P3(*Q(s_b, d), hmax - 0.2), 0.024, seg=6, caps=False)


def _rail_line(m, p0, p1, h0, slope):
    a, b = np.array(p0), np.array(p1)
    L_ = np.linalg.norm(b - a)
    h1 = h0 + slope * L_
    m.tube("steel_galv", P3(*a, h0), P3(*b, h1), 0.024, seg=6)
    for f in np.linspace(0, 1, max(2, int(L_ / 2.0) + 1)):
        p = a + (b - a) * f
        h = h0 + (h1 - h0) * f
        m.tube("steel_galv", P3(*p, h - 1.0), P3(*p, h), 0.02, seg=6, caps=False)
    m.tube("steel_galv", P3(*a, h0 - 0.5), P3(*b, h1 - 0.5), 0.016, seg=6, caps=False)


def seat_template():
    """a moulded stadium seat, closed solid (pan and back with thickness), on a steel bracket. Local frame: x along the
    row, y up, -z to the field; origin on the tread under the seat's middle."""
    m = Mesh()
    hw = 0.2
    th = 0.012
    prof = [(-0.25, 0.42), (-0.05, 0.44), (0.08, 0.46), (0.13, 0.56), (0.16, 0.74), (0.17, 0.84)]
    def V(i, j, s):
        z, y = prof[i]
        w = hw * (1 - 0.25 * max(0.0, (y - 0.56) / 0.28))
        dish = 0.025 * (1 - abs(j)) * (1 if y < 0.55 else -1)
        return np.array((j * w, y - (dish if y < 0.55 else 0) + s * th, z + (dish if y >= 0.55 else 0) + s * th))
    for i in range(len(prof) - 1):
        for j in (-1, 0):
            a, b, c, d = V(i, j, 1), V(i, j + 1, 1), V(i + 1, j + 1, 1), V(i + 1, j, 1)
            m.quad("seat", a, b, c, d)
            a, b, c, d = V(i, j, -1), V(i, j + 1, -1), V(i + 1, j + 1, -1), V(i + 1, j, -1)
            m.quad("seat", d, c, b, a)
        for j in (-1, 1):
            a, b, c, d = V(i, j, -1), V(i + 1, j, -1), V(i + 1, j, 1), V(i, j, 1)
            if j > 0:
                m.quad("seat", a, b, c, d)
            else:
                m.quad("seat", d, c, b, a)
    for j in (-1, 0):
        a, b, c, d = V(0, j, -1), V(0, j + 1, -1), V(0, j + 1, 1), V(0, j, 1)
        m.quad("seat", d, c, b, a)
        n = len(prof) - 1
        a, b, c, d = V(n, j, -1), V(n, j + 1, -1), V(n, j + 1, 1), V(n, j, 1)
        m.quad("seat", a, b, c, d)
    m.box("seat", (0, 0.2, 0.05), (0.06, 0.4, 0.06))
    p = m.parts["seat"]
    return np.array(p["v"], np.float32)


def write_seats():
    os.makedirs(OUT, exist_ok=True)
    tmpl = seat_template()
    open(os.path.join(OUT, "seat_tmpl.bin"), "wb").write(tmpl.astype(np.float32).tobytes())
    by = {}
    for p, h, t, o, col in SEATS:
        # basis columns: x = along the row (t), y = up, z = away from the field (o); -z faces the field
        X = np.array((t[0], 0, -t[1]))
        Y = np.array((0, 1.0, 0))
        Z = np.array((o[0], 0, -o[1]))
        pos = P3(p[0], p[1], h)
        rowm = [X[0], Y[0], Z[0], pos[0], X[1], Y[1], Z[1], pos[1], X[2], Y[2], Z[2], pos[2]]
        by.setdefault(col, []).extend(rowm)
    for col, buf in by.items():
        open(os.path.join(OUT, "seats_%s.bin" % col), "wb").write(np.array(buf, np.float32).tobytes())
    return {k: len(v) // 12 for k, v in by.items()}


# ------------------------------------------------------------------ other buildings

def build_others(m, site_h):
    # the dark grey shed west of the clubrooms (gable roof east-west, roller doors to the car park)
    sh = [(-122.5, 10.5), (-104.0, 10.5), (-104.0, 28.0), (-122.5, 28.0)]
    g = height_at(site_h, -113, 19)
    box_pts(m, "brick_shed", sh, g - 1.0, g + 4.2, skip=("top",))
    _gable(m, sh, g + 4.2, g + 6.0, "roof_dark", "brick_shed", axis=0)
    for k in range(3):
        x = -120.5 + k * 5.5
        box_pts(m, "roller", [(x, 10.38), (x + 3.6, 10.38), (x + 3.6, 10.5), (x, 10.5)], g, g + 3.4)
    # four galvanised water tanks by the west car park, 3.6 m across, 4 m high, with conical lids
    for e, n in ((-150.5, 9.5), (-145.0, 5.5), (-139.5, 1.8), (-134.2, -2.0)):
        gg = height_at(site_h, e, n)
        m.tube("concrete", P3(e, n, gg - 0.3), P3(e, n, gg + 0.15), 2.0, seg=20)
        m.tube("tank", P3(e, n, gg + 0.15), P3(e, n, gg + 4.0), 1.8, seg=24, caps=False)
        m.tube("tank", P3(e, n, gg + 4.0), P3(e, n, gg + 4.6), 1.82, 0.15, seg=24, caps=False)
    # court pavilion by the netball courts: white wall, dark skillion roof
    pv = [(-130.0, 126.0), (-116.0, 126.0), (-116.0, 160.0), (-130.0, 160.0)]
    g = height_at(site_h, -123, 143)
    box_pts(m, "white_render", pv, g - 1.0, g + 3.6, mats={"top": "roof_dark"})
    box_pts(m, "roof_dark", [(-131.0, 125.0), (-115.0, 125.0), (-115.0, 161.0), (-131.0, 161.0)], g + 3.6, g + 3.9, mats={"bottom": "soffit"})
    box_pts(m, "clad_dark", [(-116.0, 128.0), (-115.6, 128.0), (-115.6, 158.0), (-116.0, 158.0)], g, g + 3.6)
    # the kiosk in the east park
    g = height_at(site_h, 88, -52)
    box_pts(m, "white_render", [(85.5, -54.5), (90.5, -54.5), (90.5, -49.5), (85.5, -49.5)], g - 0.5, g + 2.9)
    box_pts(m, "roof_white", [(85.0, -55.0), (91.0, -55.0), (91.0, -49.0), (85.0, -49.0)], g + 2.9, g + 3.1)
    # court fences: 3.6 m black chain mesh on posts every 3 m (mesh as a dark see-through-reading lattice of wires)
    for poly in ([(-177, 24), (-106, 24), (-106, 77), (-177, 77)], [(-114, 84), (-61, 84), (-61, 161), (-114, 161)]):
        for k in range(4):
            a, b = np.array(poly[k], float), np.array(poly[(k + 1) % 4], float)
            Lf = np.linalg.norm(b - a)
            n = int(Lf / 3.0)
            ga = height_at(site_h, *((a + b) / 2))
            for i in range(n + 1):
                p = a + (b - a) * i / n
                m.tube("mesh_fence", P3(*p, ga - 0.2), P3(*p, ga + 3.6), 0.03, seg=6)
            for hh in (0.05, 1.8, 3.6):
                m.tube("mesh_fence", P3(*a, ga + hh), P3(*b, ga + hh), 0.02, seg=6, caps=False)
            # the mesh itself: diagonal wires every 0.6 m (finer mesh reads the same from the stands)
            dirv = (b - a) / Lf
            for s in np.arange(0, Lf, 0.6):
                p = a + dirv * s
                q = a + dirv * min(s + 3.6, Lf)
                m.beam("mesh_fence", P3(*p, ga + 0.05), P3(*q, ga + 0.05 + (min(s + 3.6, Lf) - s)), 0.006, 0.006)
                q2 = a + dirv * max(s - 3.6, 0)
                m.beam("mesh_fence", P3(*p, ga + 0.05), P3(*q2, ga + 0.05 + (s - max(s - 3.6, 0))), 0.006, 0.006)


def _gable(m, poly, h0, h1, mat, wall, axis=0):
    (x0, y0), (x1, _), (_, y1), _ = poly
    ov = 0.4
    if axis == 0:
        ym = (y0 + y1) / 2
        A = [P3(x0 - ov, y0 - ov, h0), P3(x1 + ov, y0 - ov, h0), P3(x1 + ov, ym, h1), P3(x0 - ov, ym, h1)]
        B = [P3(x0 - ov, ym, h1), P3(x1 + ov, ym, h1), P3(x1 + ov, y1 + ov, h0), P3(x0 - ov, y1 + ov, h0)]
        _q(m, mat, A, up=True)
        _q(m, mat, B, up=True)
        _q(m, "soffit", A, up=False)
        _q(m, "soffit", B, up=False)
        for x in (x0, x1):
            a, b, c = P3(x, y0, h0), P3(x, y1, h0), P3(x, ym, h1)
            m.tri(wall, a, b, c)
            m.tri(wall, a, c, b)


# ------------------------------------------------------------------ the disused Gawler-Angaston line

def build_rail(m, site_h):
    """two rails on sleepers in a ballast bed along the old line west and south of the ground (the satellite shows the
    track still in place)"""
    line = [(-180.0, 18.0), (-120.0, -18.5), (-60.0, -95.0), (-30.0, -132.0), (0.0, -168.0)]
    pts = []
    for a, b in zip(line[:-1], line[1:]):
        a, b = np.array(a), np.array(b)
        n = int(np.linalg.norm(b - a) / 0.68)
        for i in range(n):
            pts.append(a + (b - a) * i / n)
    pts.append(np.array(line[-1]))
    for i in range(len(pts) - 1):
        p, q = pts[i], pts[i + 1]
        t = _n(q - p)
        nrm = np.array((t[1], -t[0]))
        g = height_at(site_h, *p)
        box_pts(m, "sleeper", [p - nrm * 1.25 - t * 0.12, p + nrm * 1.25 - t * 0.12, p + nrm * 1.25 + t * 0.12, p - nrm * 1.25 + t * 0.12],
                g + 0.05, g + 0.2, skip=("bottom",))
    for side in (-0.8, 0.8):
        for i in range(0, len(pts) - 1, 6):
            p, q = pts[i], pts[min(i + 6, len(pts) - 1)]
            t = _n(q - p)
            nrm = np.array((t[1], -t[0]))
            gp, gq = height_at(site_h, *p), height_at(site_h, *q)
            m.beam("rail_steel", P3(*(p + nrm * side), gp + 0.28), P3(*(q + nrm * side), gq + 0.28), 0.07, 0.15)


# ------------------------------------------------------------------ kerbs and the south-west retaining wall

def build_kerbs(m, site_h):
    """a 150 mm kerb along both edges of the ring road, and the retaining wall (with a black safety fence on top)
    between the south-west grass verge and the raised road"""
    for col, sel in ((1, None), (2, None)):
        bs = np.arange(0, 236, 0.5)
        for b0, b1 in zip(bs[:-1], bs[1:]):
            r0 = interp(RING, b0)[col]
            r1 = interp(RING, b1)[col]
            if r0 <= 0.5 and col == 1:
                continue
            for off, h in ((-0.15, 0.15), (0.0, 0.15)):
                pass
            pa, pb = np.array(polar(b0, r0)), np.array(polar(b1, r1))
            pa2, pb2 = np.array(polar(b0, r0 - 0.15)), np.array(polar(b1, r1 - 0.15))
            ga, gb = height_at(site_h, *pa), height_at(site_h, *pb)
            g = min(ga, gb)
            box_pts(m, "kerb", [tuple(pa2), tuple(pb2), tuple(pb), tuple(pa)], g - 0.2, max(ga, gb) + 0.12, skip=("bottom",))
    # the wall: from bearing 178 to 238, at the road's inner edge, top at the road level
    bs = np.arange(178, 238.5, 1.0)
    for b0, b1 in zip(bs[:-1], bs[1:]):
        r0 = interp(RING, b0)[1] - 0.3
        r1 = interp(RING, b1)[1] - 0.3
        pa, pb = np.array(polar(b0, r0)), np.array(polar(b1, r1))
        qa, qb = np.array(polar(b0, r0 + 0.3)), np.array(polar(b1, r1 + 0.3))
        top = max(site.upper_level(b0), site.upper_level(b1)) + 0.25
        box_pts(m, "concrete", [tuple(pa), tuple(pb), tuple(qb), tuple(qa)], -0.5, top)
        # safety fence: black posts and rails
        m.tube("frame_dark", P3(*qa, top), P3(*qa, top + 1.2), 0.03, seg=6)
        m.beam("frame_dark", P3(*qa, top + 1.15), P3(*qb, top + 1.15), 0.05, 0.05)
        for f in np.linspace(0, 1, 9)[:-1]:
            p = qa + (qb - qa) * f
            m.beam("frame_dark", P3(*p, top + 0.1), P3(*p, top + 1.15), 0.015, 0.015)


# ------------------------------------------------------------------ the second oval (oval2.py)

def build_oval2(m, site_h, dem):
    def h(e, n):
        if abs(e) < site.HALF - 2 and abs(n) < site.HALF - 2:
            return height_at(site_h, e, n)
        return dem_height(dem, e, n)
    oval2.goal_posts(m, h, "post_white", "post_pad")
    oval2.light_poles(m, h, "steel_galv", "led")
    oval2.shelters(m, h, "steel_dark", "shelter_roof", "door_white")
    oval2.nets(m, h, "steel_galv", "net", "pitch_synthetic")


def main():
    materials()
    dem = Dem(15, 600)
    nodes = []
    s, site_h = build_site(dem)
    nodes.append(("site", s))
    for name, fn in (("fence", lambda mm: build_fence(mm)), ("towers", lambda mm: build_towers(mm, site_h)),
                     ("clubrooms", build_club), ("terraces", build_terraces), ("pavilion", build_pavilion),
                     ("temp_stands", lambda mm: build_temp_stands(mm, site_h)), ("others", lambda mm: build_others(mm, site_h)),
                     ("rail", lambda mm: build_rail(mm, site_h)), ("kerbs", lambda mm: build_kerbs(mm, site_h)),
                     ("oval2", lambda mm: build_oval2(mm, site_h, dem))):
        mm = Mesh()
        fn(mm)
        nodes.append((name, mm))
        print(name, mm.tris(), "triangles")
    os.makedirs(OUT, exist_ok=True)
    write_glb(os.path.join(OUT, "barossa.glb"), nodes, M, jpeg=True)
    print("seats", write_seats())


if __name__ == "__main__":
    main()
