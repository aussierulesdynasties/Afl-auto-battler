"""Blender builder for the generic suburban ovals.
    blender -b -P build.py -- SPEC.json OUTDIR
World: metres, x along the ground's long axis (goal to goal), y across, z up, origin = centre of the oval.
Every texture is from tex.py (hand-made). UVs are at true world scale (tex_m.json).
"""
import bpy, bmesh, json, math, os, sys, random
from mathutils import Vector, Matrix

argv = sys.argv[sys.argv.index("--") + 1:]
SPEC = json.load(open(argv[0]))
OUT = argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
TEXDIR = os.path.abspath(os.path.join(HERE, "..", "tex"))
TEX_M = json.load(open(os.path.join(TEXDIR, "tex_m.json")))
R = random.Random(SPEC.get("seed", 1))

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# ------------------------------------------------------------------ materials
MATS = {}
ALPHA = {"picket", "pipe_rail", "chainlink", "chainlink_black", "turf_worn", "gum_leaves", "gum_leaves_b", "pine_leaves", "palm_frond"}


def mat(name, rough=0.8, metal=0.0, emit=0.0):
    key = name
    if key in MATS:
        return MATS[key]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if name.startswith("rgb:"):
        r, g, b = [int(v) / 255 for v in name[4:].split(",")]
        bsdf.inputs["Base Color"].default_value = (r ** 2.2, g ** 2.2, b ** 2.2, 1)
    else:
        img = bpy.data.images.load(os.path.join(TEXDIR, name + ".png"), check_existing=True)
        tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = img
        tx.interpolation = "Linear"
        nt.links.new(tx.outputs["Color"], bsdf.inputs["Base Color"])
        if name in ALPHA:
            gt = nt.nodes.new("ShaderNodeMath"); gt.operation = "GREATER_THAN"; gt.inputs[1].default_value = 0.5
            nt.links.new(tx.outputs["Alpha"], gt.inputs[0])
            nt.links.new(gt.outputs[0], bsdf.inputs["Alpha"])
            m.use_backface_culling = False
            try:
                m.surface_render_method = "DITHERED"
            except Exception:
                pass
        if emit > 0:
            nt.links.new(tx.outputs["Color"], bsdf.inputs["Emission Color"])
            bsdf.inputs["Emission Strength"].default_value = emit
    MATS[key] = m
    return m


ROUGH = {"glass_curtain": (0.08, 0.2), "iron_zinc": (0.45, 0.5), "steel_grey": (0.5, 0.6), "dark_metal": (0.5, 0.4)}

# ------------------------------------------------------------------ mesh accumulator
class Acc:
    """Collect faces per material into one mesh object per group (few draw calls)."""
    def __init__(self):
        self.groups = {}

    def g(self, group):
        return self.groups.setdefault(group, {"v": [], "f": [], "uv": [], "m": [], "mats": []})

    def face(self, group, pts, uvs, texname):
        G = self.g(group)
        if texname not in G["mats"]:
            G["mats"].append(texname)
        base = len(G["v"])
        G["v"].extend([tuple(p) for p in pts])
        G["f"].append(list(range(base, base + len(pts))))
        G["uv"].append(uvs)
        G["m"].append(G["mats"].index(texname))

    def quad(self, group, p0, p1, p2, p3, tex, uvmode="world", uvrect=None):
        """p0 bottom-left, p1 bottom-right, p2 top-right, p3 top-left (counter-clockwise seen from the front)."""
        p0, p1, p2, p3 = map(Vector, (p0, p1, p2, p3))
        zl = getattr(self, "zl", 0.0)
        if zl:
            p0, p1, p2, p3 = [q + Vector((0, 0, zl)) for q in (p0, p1, p2, p3)]
        if uvrect is not None:
            u0, v0, u1, v1 = uvrect
            uvs = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
        else:
            tm = TEX_M.get(tex, 1.0)
            ex = (p1 - p0); L = ex.length or 1e-6; ex /= L
            nrm = (p1 - p0).cross(p3 - p0)
            ey = nrm.cross(ex).normalized() if nrm.length > 1e-9 else Vector((0, 0, 1))
            # keep v pointing up for walls, along depth for floors
            uvs = []
            for p in (p0, p1, p2, p3):
                d = p - p0
                uvs.append((d.dot(ex) / tm, d.dot(ey) / tm))
        self.face(group, [p0, p1, p2, p3], uvs, tex)

    def tri(self, group, a, b, c, tex):
        a, b, c = map(Vector, (a, b, c)); tm = TEX_M.get(tex, 1.0)
        ex = (b - a).normalized(); n = (b - a).cross(c - a); ey = n.cross(ex).normalized()
        self.face(group, [a, b, c], [((p - a).dot(ex) / tm, (p - a).dot(ey) / tm) for p in (a, b, c)], tex)

    def build(self, coll):
        objs = []
        for name, G in self.groups.items():
            if not G["f"]:
                continue
            me = bpy.data.meshes.new(name)
            me.from_pydata(G["v"], [], G["f"])
            me.update()
            uvl = me.uv_layers.new(name="UVMap")
            li = 0
            for poly, uvs in zip(me.polygons, G["uv"]):
                for k, loop in enumerate(poly.loop_indices):
                    uvl.data[loop].uv = uvs[k]
            for t in G["mats"]:
                r, mt = ROUGH.get(t, (0.85, 0.0))
                me.materials.append(mat(t, r, mt))
            for poly, mi in zip(me.polygons, G["m"]):
                poly.material_index = mi
            ob = bpy.data.objects.new(name, me)
            coll.objects.link(ob)
            objs.append(ob)
        return objs


A = Acc()


def rot(x, y, ang):
    c, s = math.cos(ang), math.sin(ang)
    return (x * c - y * s, x * s + y * c)


def frame(cx, cy, ang):
    """Local frame: returns f(lx, ly, z) -> world point. ly = depth (positive = away from field if facing in)."""
    def f(lx, ly, z):
        x, y = rot(lx, ly, ang)
        return (cx + x, cy + y, z)
    return f


def box(group, f, x0, x1, y0, y1, z0, z1, walls, top=None, bottom=None, sides=(1, 1, 1, 1)):
    """Axis box in local frame f. walls: tex or dict per side {'front','back','left','right'}; front = -y side."""
    if isinstance(walls, str):
        walls = {"front": walls, "back": walls, "left": walls, "right": walls}
    P = lambda x, y, z: f(x, y, z)
    if sides[0] and walls.get("front"):
        A.quad(group, P(x0, y0, z0), P(x1, y0, z0), P(x1, y0, z1), P(x0, y0, z1), walls["front"])
    if sides[1] and walls.get("back"):
        A.quad(group, P(x1, y1, z0), P(x0, y1, z0), P(x0, y1, z1), P(x1, y1, z1), walls["back"])
    if sides[2] and walls.get("left"):
        A.quad(group, P(x0, y1, z0), P(x0, y0, z0), P(x0, y0, z1), P(x0, y1, z1), walls["left"])
    if sides[3] and walls.get("right"):
        A.quad(group, P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1), walls["right"])
    if top:
        A.quad(group, P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1), top)
    if bottom:
        A.quad(group, P(x0, y1, z0), P(x1, y1, z0), P(x1, y0, z0), P(x0, y0, z0), bottom)


def post(group, x, y, z0, z1, r, tex, n=8):
    for i in range(n):
        a0 = 2 * math.pi * i / n; a1 = 2 * math.pi * (i + 1) / n
        p0 = (x + r * math.cos(a0), y + r * math.sin(a0)); p1 = (x + r * math.cos(a1), y + r * math.sin(a1))
        A.quad(group, (*p0, z0), (*p1, z0), (*p1, z1), (*p0, z1), tex)


def taper(group, x, y, z0, z1, r0, r1, tex, n=7, lean=(0, 0)):
    for i in range(n):
        a0 = 2 * math.pi * i / n; a1 = 2 * math.pi * (i + 1) / n
        q = lambda a, r, z, t: (x + lean[0] * t + r * math.cos(a), y + lean[1] * t + r * math.sin(a), z)
        A.quad(group, q(a0, r0, z0, 0), q(a1, r0, z0, 0), q(a1, r1, z1, 1), q(a0, r1, z1, 1), tex)


# ------------------------------------------------------------------ field
F = SPEC["field"]
AX, BY = F["a"], F["b"]          # half length, half width of the boundary line ellipse


def ell(t, da=0.0):
    """Point on the boundary ellipse grown outward by da metres (approx. normal offset)."""
    x, y = AX * math.cos(t), BY * math.sin(t)
    nx, ny = x / AX ** 2, y / BY ** 2; nl = math.hypot(nx, ny)
    return (x + da * nx / nl, y + da * ny / nl)


def ring(group, d0, d1, z0, z1, tex, t0=0, t1=2 * math.pi, n=160, flip=False):
    """Ring band between offsets d0 (inner) and d1 (outer) from the boundary, z rising from z0 to z1."""
    ts = [t0 + (t1 - t0) * i / n for i in range(n + 1)]
    tm = TEX_M.get(tex, 4.0)
    s = 0.0
    for i in range(n):
        a, b = ts[i], ts[i + 1]
        pa0, pb0 = ell(a, d0), ell(b, d0); pa1, pb1 = ell(a, d1), ell(b, d1)
        seg = math.dist(pa0, pb0)
        w = math.hypot(d1 - d0, z1 - z0)
        A.face(group, [(*pa0, z0), (*pb0, z0), (*pb1, z1), (*pa1, z1)],
               [(s / tm, 0), ((s + seg) / tm, 0), ((s + seg) / tm, w / tm), (s / tm, w / tm)], tex)
        s += seg


def disc_field():
    """Playing surface: ellipse fan out to 4 m beyond the boundary line, true-scale UVs."""
    n = 192; tex = F.get("turf", "turf"); tm = TEX_M[tex]
    ext = F.get("apron", 4.0)
    for i in range(n):
        a, b = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        pa, pb = ell(a, ext), ell(b, ext)
        A.face("field", [(0, 0, 0), (*pa, 0), (*pb, 0)], [(0, 0), (pa[0] / tm, pa[1] / tm), (pb[0] / tm, pb[1] / tm)], tex)


def line_strip(pts, w=0.1, z=0.02, closed=False):
    if closed:
        pts = pts + [pts[0]]
    for i in range(len(pts) - 1):
        a, b = Vector((*pts[i], z)), Vector((*pts[i + 1], z))
        d = (b - a); d.z = 0
        if d.length < 1e-6:
            continue
        nrm = Vector((-d.y, d.x, 0)).normalized() * (w / 2)
        A.quad("lines", a - nrm, b - nrm, b + nrm, a + nrm, "white_paint", uvrect=(0, 0, 1, 1))


def circle(cx, cy, r, n=48, a0=0.0, a1=2 * math.pi):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def markings():
    line_strip([ell(2 * math.pi * i / 240) for i in range(240)], 0.1, closed=True)      # boundary line
    line_strip([(-25, -25), (25, -25), (25, 25), (-25, 25)], 0.1, closed=True)           # centre square
    line_strip(circle(0, 0, 5.0), 0.1); line_strip(circle(0, 0, 1.5), 0.1)               # centre circles
    line_strip([(0, -1.5), (0, 1.5)], 0.1)
    for s in (-1, 1):
        gx = s * AX
        line_strip([(gx, -9.6), (gx, 9.6)], 0.1)                                        # goal line (to behind posts)
        line_strip([(gx, -3.2), (gx - s * 9, -3.2), (gx - s * 9, 3.2), (gx, 3.2)], 0.1)  # goal square 6.4 x 9


def arcs50():
    for s in (-1, 1):
        gx = s * AX
        pts = []
        for i in range(361):
            a = math.pi * i / 360 - math.pi / 2          # -90..90 deg, opening toward the centre
            x = gx - s * 50 * math.cos(a); y = 50 * math.sin(a)
            if (x / AX) ** 2 + (y / BY) ** 2 <= 1.0:
                pts.append((x, y))
        line_strip(pts, 0.1)


def goalposts():
    gp = SPEC.get("posts", {})
    gh, bh = gp.get("goal_h", 12.0), gp.get("behind_h", 7.0)
    pad = gp.get("pad", "pad_blue")
    for s in (-1, 1):
        gx = s * AX
        for y, h, r in ((-3.2, gh, 0.12), (3.2, gh, 0.12), (-9.6, bh, 0.08), (9.6, bh, 0.08)):
            post("posts", gx, y, 0, h, r, "white_paint")
            post("posts", gx, y, 0, 2.5, r + 0.13, pad)


# ------------------------------------------------------------------ surrounds
def surround():
    for band in SPEC.get("surround", []):
        ring("ground", band["d0"], band["d1"], band.get("z0", 0.0), band.get("z1", 0.0), band["tex"],
             band.get("t0", 0), band.get("t1", 2 * math.pi))
    # outer apron ring down to a skirt so nothing floats
    out = SPEC.get("outer", {"d": 60, "tex": "turf_dry"})
    last = max([b["d1"] for b in SPEC.get("surround", [])] + [F.get("apron", 4.0)])
    lastz = SPEC.get("surround", [{}])[-1].get("z1", 0.0) if SPEC.get("surround") else 0.0
    ring("ground", last, out["d"], lastz, lastz, out["tex"])


def fence():
    fc = SPEC.get("fence")
    if not fc:
        return
    typ = fc["type"]; tex = fc.get("tex", typ); d = fc.get("d", 3.0); h = {"picket": 1.2, "pipe_rail": 1.2, "chainlink": 1.0}[typ] * fc.get("hscale", 1.0)
    n = 400; s = 0.0; tm = TEX_M[tex]
    gaps = fc.get("gaps", [])
    for i in range(n):
        a, b = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        if any(g0 <= (a + b) / 2 <= g1 for g0, g1 in gaps):
            continue
        pa, pb = ell(a, d), ell(b, d); seg = math.dist(pa, pb)
        hh = h if typ != "chainlink" else fc.get("h", 1.8)
        vt = hh / tm
        A.face("fence", [(*pa, 0), (*pb, 0), (*pb, hh), (*pa, hh)],
               [(s / tm, 0), ((s + seg) / tm, 0), ((s + seg) / tm, vt), (s / tm, vt)], tex)
        s += seg
    if typ == "chainlink":   # posts and pipe rails
        pt = fc.get("post_tex", "steel_grey")
        for i in range(0, n, 4):
            p = ell(2 * math.pi * i / n, d); post("fence_posts", p[0], p[1], 0, fc.get("h", 1.8), 0.03, pt, 6)
        for zr in fc.get("rails", []):
            ring("fence_posts", d, d, zr - 0.025, zr + 0.025, pt)


def signs():
    for sg in SPEC.get("signs", []):
        d = sg.get("d", 3.4); h0, h1 = sg.get("z", (0.1, 1.0))
        t0, t1 = sg["t0"], sg["t1"]; n = sg.get("n", 6)
        texs = sg.get("tex", ["sign_sponsor1", "sign_sponsor2", "sign_sponsor3", "sign_sponsor4"])
        for i in range(n):
            a = t0 + (t1 - t0) * i / n; b = t0 + (t1 - t0) * (i + 0.92) / n
            pa, pb = ell(a, d), ell(b, d)
            tx = texs[i % len(texs)]
            # face the field: field side = inner; quad wound so normal points inward
            A.quad("signs", (*pb, h0), (*pa, h0), (*pa, h1), (*pb, h1), tx, uvrect=(0, 0, 1, 1)) if True else None
            qa, qb = ell(a, d + 0.04), ell(b, d + 0.04)   # back panel sits 4 cm behind the print (no z-fight)
            A.quad("signs", (*qa, h0), (*qb, h0), (*qb, h1), (*qa, h1), "dark_metal")


# ------------------------------------------------------------------ parts
def place(p):
    """Local frame for a part: position by boundary angle t + offset d, or by x,y; facing the field by default."""
    if "t" in p:
        x, y = ell(p["t"], p.get("d", 10.0))
    else:
        x, y = p["x"], p["y"]
    if "rot" in p:
        ang = math.radians(p["rot"])
    else:   # face the oval centre: local -y toward field
        ang = math.atan2(y, x) - math.pi / 2
        if "t" in p:  # face along the ellipse normal
            nx, ny = x / AX ** 2, y / BY ** 2
            ang = math.atan2(ny, nx) - math.pi / 2
    return frame(x, y, ang), x, y, ang


def roof(group, f, x0, x1, y0, y1, zf, zb, tex, under="iron_zinc", th=0.25, gable=False):
    """Skillion roof from front (y0, zf) to back (y1, zb), with fascia edges."""
    if not gable:
        A.quad(group, f(x0, y0, zf), f(x1, y0, zf), f(x1, y1, zb), f(x0, y1, zb), tex)
        A.quad(group, f(x1, y0, zf - th), f(x0, y0, zf - th), f(x0, y1, zb - th), f(x1, y1, zb - th), under)
        A.quad(group, f(x0, y0, zf - th), f(x1, y0, zf - th), f(x1, y0, zf), f(x0, y0, zf), "white_paint")
        A.quad(group, f(x1, y1, zb - th), f(x0, y1, zb - th), f(x0, y1, zb), f(x1, y1, zb), "white_paint")
        A.quad(group, f(x0, y1, zb - th), f(x0, y0, zf - th), f(x0, y0, zf), f(x0, y1, zb), "white_paint")
        A.quad(group, f(x1, y0, zf - th), f(x1, y1, zb - th), f(x1, y1, zb), f(x1, y0, zf), "white_paint")
    else:
        ym = (y0 + y1) / 2; zr = zf + (y1 - y0) * 0.3
        A.quad(group, f(x0, y0, zf), f(x1, y0, zf), f(x1, ym, zr), f(x0, ym, zr), tex)
        A.quad(group, f(x1, y1, zf), f(x0, y1, zf), f(x0, ym, zr), f(x1, ym, zr), tex)
        A.tri(group, f(x0, y1, zf), f(x0, y0, zf), f(x0, ym, zr), p_gable_tex(group))
        A.tri(group, f(x1, y0, zf), f(x1, y1, zf), f(x1, ym, zr), p_gable_tex(group))


_GABLE = {}


def p_gable_tex(group):
    return _GABLE.get(group, "weatherboard_white")


def building(p):
    """Clubrooms / kiosk / toilet block: walls, windows on the field face, roof (skillion/gable/flat), verandah."""
    f, *_ = place(p)
    w, dp, h = p["w"], p["dpt"], p["h"]
    x0, x1, y0, y1 = -w / 2, w / 2, 0, dp
    wall = p.get("wall", "brick_red"); front = p.get("front", wall)
    g = p.get("group", "buildings")
    _GABLE[g] = p.get("gable_tex", wall)
    box(g, f, x0, x1, y0, y1, 0, h, {"front": front, "back": wall, "left": wall, "right": wall})
    rt = p.get("roof", "skillion"); rtex = p.get("roof_tex", "iron_zinc"); ov = p.get("overhang", 0.5)
    if rt == "flat":
        A.quad(g, f(x0, y0, h), f(x1, y0, h), f(x1, y1, h), f(x0, y1, h), rtex)
        box(g, f, x0 - 0.05, x1 + 0.05, y0 - 0.05, y1 + 0.05, h, h + 0.6, p.get("parapet", "white_paint"), top=None)
    elif rt == "gable":
        roof(g, f, x0 - ov, x1 + ov, y0 - ov, y1 + ov, h, h, rtex, gable=True)
    else:
        rise = p.get("rise", 0.8)
        roof(g, f, x0 - ov, x1 + ov, y0 - ov, y1 + ov, h + rise if p.get("high_front") else h, h if p.get("high_front") else h + rise, rtex)
    v = p.get("verandah")
    if v:   # posted verandah on the field side
        vd = v.get("d", 3.0); vh = v.get("h", 2.8)
        roof(g, f, x0, x1, -vd, 0, vh, vh + 0.35, v.get("tex", rtex), th=0.12)
        n = max(2, int(w / v.get("bay", 4.0)) + 1)
        for i in range(n):
            px = x0 + 0.15 + (w - 0.3) * i / (n - 1)
            pp = f(px, -vd + 0.15, 0); post(g, pp[0], pp[1], 0, vh, 0.06, v.get("post", "white_paint"), 6)
        if v.get("deck"):
            box(g, f, x0, x1, -vd, 0, 0, 0.3, "concrete", top=v.get("deck"))
    if p.get("sign"):
        sw = min(w * 0.6, 12); sh = sw / 6
        z = h - sh - 0.2 if not v else v.get("h", 2.8) + 0.45
        A.quad(g, f(-sw / 2, -0.04 - (v.get("d", 3.0) if v else 0), z), f(sw / 2, -0.04 - (v.get("d", 3.0) if v else 0), z),
               f(sw / 2, -0.04 - (v.get("d", 3.0) if v else 0), z + sh), f(-sw / 2, -0.04 - (v.get("d", 3.0) if v else 0), z + sh),
               p["sign"], uvrect=(0, 0, 1, 1))
    for d in p.get("doors", []):   # roller doors / doors on the field face: [x, w, h(, tex, z0)]
        dx, dw, dh = d[:3]; dt = d[3] if len(d) > 3 else "roller_door"; dz = d[4] if len(d) > 4 else 0.0
        A.quad(g, f(dx - dw / 2, -0.03, dz), f(dx + dw / 2, -0.03, dz), f(dx + dw / 2, -0.03, dz + dh), f(dx - dw / 2, -0.03, dz + dh),
               dt, uvrect=(0, 0, 1, 1) if dt.startswith("door_") else None)
    for st in p.get("stairs", []):
        stairs(g, f, st)
    up = p.get("upper")
    if up:  # second storey (glass function room), set back by up['set']
        s = up.get("set", 0.0); uh = up.get("h", 3.4)
        box(g, f, x0 + up.get("inset", 0), x1 - up.get("inset", 0), y0 + s, y1, h, h + uh,
            {"front": up.get("front", "glass_curtain"), "back": up.get("wall", wall), "left": up.get("wall", wall), "right": up.get("wall", wall)})
        A.quad(g, f(x0, y0, h), f(x1, y0, h), f(x1, y0 + s, h), f(x0, y0 + s, h), "concrete") if s > 0 else None
        roof(g, f, x0 + up.get("inset", 0) - ov, x1 - up.get("inset", 0) + ov, y0 + s - up.get("eave", 1.5), y1 + ov,
             h + uh + up.get("rise", 0.9), h + uh, up.get("roof_tex", rtex))
        if up.get("rail"):
            box(g, f, x0, x1, y0 + 0.02, y0 + 0.08, h, h + 1.0, "glass_curtain")


def stand(p):
    """Seated / bench grandstand: stepped treads on a base, back wall, end walls, skillion roof on posts."""
    f, *_ = place(p)
    L = p["len"]; rows = p["rows"]; tr = p.get("tread", 0.8); ri = p.get("riser", 0.4); base = p.get("base", 1.0)
    x0, x1 = -L / 2, L / 2
    g = p.get("group", "stands")
    seat = p.get("seat", "seats_maroon"); tm = TEX_M.get(seat, 4.0)
    for r in range(rows):
        y0 = r * tr; y1 = (r + 1) * tr; z = base + r * ri
        A.face(g, [f(x0, y0, z), f(x1, y0, z), f(x1, y1, z), f(x0, y1, z)],
               [(0, (r * tr) / tm), (L / tm, (r * tr) / tm), (L / tm, ((r + 1) * tr) / tm), (0, ((r + 1) * tr) / tm)], seat)
        A.quad(g, f(x0, y1, z), f(x1, y1, z), f(x1, y1, z + ri), f(x0, y1, z + ri), p.get("riser_tex", "concrete"))
    D = rows * tr; ztop = base + rows * ri
    front = p.get("front", "concrete")
    A.quad(g, f(x0, 0, 0), f(x1, 0, 0), f(x1, 0, base), f(x0, 0, base), front)
    back = p.get("back", "iron_cream")
    bh = ztop + p.get("back_h", 2.4)
    A.quad(g, f(x1, D, 0), f(x0, D, 0), f(x0, D, bh), f(x1, D, bh), back)
    A.quad(g, f(x0, D - 0.02, ztop), f(x1, D - 0.02, ztop), f(x1, D - 0.02, bh), f(x0, D - 0.02, bh), p.get("back_in", back))
    endt = p.get("ends", back)
    for xe, sgn in ((x0, -1), (x1, 1)):
        pts = [f(xe, 0, 0), f(xe, D, 0), f(xe, D, bh), f(xe, 0, base)]
        if sgn < 0:
            A.face(g, [pts[1], pts[0], pts[3], pts[2]],
                   [(0, 0), (D / TEX_M.get(endt, 2), 0), (D / TEX_M.get(endt, 2), base / TEX_M.get(endt, 2)), (0, bh / TEX_M.get(endt, 2))], endt)
        else:
            A.face(g, pts, [(0, 0), (D / TEX_M.get(endt, 2), 0), (D / TEX_M.get(endt, 2), bh / TEX_M.get(endt, 2)), (0, base / TEX_M.get(endt, 2))], endt)
    rf = p.get("roof", True)
    if rf == "gable":   # pitched roof, ridge along the stand, open gable ends showing the trusses
        ze = p["eave"]; zr = p["ridge"]; ov = p.get("roof_over", 1.0); yb = D + p.get("roof_back", 0.3)
        ym = (-ov + yb) / 2; rt = p.get("roof_tex", "iron_zinc"); xa, xb = x0 - p.get("roof_end", 0.6), x1 + p.get("roof_end", 0.6)
        A.quad(g, f(xa, -ov, ze), f(xb, -ov, ze), f(xb, ym, zr), f(xa, ym, zr), rt)
        A.quad(g, f(xb, yb, ze), f(xa, yb, ze), f(xa, ym, zr), f(xb, ym, zr), rt)
        A.quad(g, f(xb, -ov, ze - 0.12), f(xa, -ov, ze - 0.12), f(xa, ym, zr - 0.12), f(xb, ym, zr - 0.12), "iron_zinc")
        A.quad(g, f(xa, yb, ze - 0.12), f(xb, yb, ze - 0.12), f(xb, ym, zr - 0.12), f(xa, ym, zr - 0.12), "iron_zinc")
        A.quad(g, f(xa, -ov, ze - 0.3), f(xb, -ov, ze - 0.3), f(xb, -ov, ze), f(xa, -ov, ze), p.get("fascia", "white_paint"))
        for xe in (xa, xb):  # barge boards along the rakes
            for (ya, za), (yb2, zb2) in (((-ov, ze), (ym, zr)), ((ym, zr), (yb, ze))):
                A.quad(g, f(xe, ya, za - 0.25), f(xe, yb2, zb2 - 0.25), f(xe, yb2, zb2), f(xe, ya, za), "white_paint")
                A.quad(g, f(xe, yb2, zb2 - 0.25), f(xe, ya, za - 0.25), f(xe, ya, za), f(xe, yb2, zb2), "white_paint")
        n = max(2, int(L / p.get("bay", 4.0)) + 1)
        for i in range(n):   # trusses (each a tie beam + two rafters + a king post) over front posts
            px = x0 + L * i / (n - 1)
            for (ya, za), (yb2, zb2) in (((-ov, ze - 0.15), (ym, zr - 0.15)), ((ym, zr - 0.15), (yb, ze - 0.15)), ((0.0, ze - 0.4), (D, ze - 0.4))):
                A.quad(g, f(px - 0.06, ya, za - 0.18), f(px - 0.06, yb2, zb2 - 0.18), f(px - 0.06, yb2, zb2), f(px - 0.06, ya, za), p.get("truss", "steel_grey"))
                A.quad(g, f(px + 0.06, yb2, zb2 - 0.18), f(px + 0.06, ya, za - 0.18), f(px + 0.06, ya, za), f(px + 0.06, yb2, zb2), p.get("truss", "steel_grey"))
                A.quad(g, f(px - 0.06, ya, za - 0.18), f(px + 0.06, ya, za - 0.18), f(px + 0.06, yb2, zb2 - 0.18), f(px - 0.06, yb2, zb2 - 0.18), p.get("truss", "steel_grey"))
            pp = f(px, p.get("post_y", 0.2), base); post(g, pp[0], pp[1], base, ze - 0.3, 0.08, p.get("post", "white_paint"), 6)
        rf = False
    if rf:
        zf = p.get("roof_front", bh + 0.6); ov = p.get("roof_over", 1.5)
        roof(g, f, x0 - 0.3, x1 + 0.3, -ov, D + 0.3, zf, bh + 0.2, p.get("roof_tex", "iron_zinc"))
        n = max(2, int(L / p.get("bay", 6.0)) + 1)
        for i in range(n):
            px = x0 + L * i / (n - 1)
            pp = f(px, p.get("post_y", 0.2), 0); post(g, pp[0], pp[1], 0, zf - 0.2, 0.1, p.get("post", "white_paint"), 6)
    if p.get("sign"):
        sw = min(L * 0.55, 18); sh = sw / 6
        zf = p.get("roof_front", bh + 0.6); ov = p.get("roof_over", 1.5)
        A.quad(g, f(-sw / 2, -ov - 0.05, zf - 0.25 - sh * 0.4), f(sw / 2, -ov - 0.05, zf - 0.25 - sh * 0.4),
               f(sw / 2, -ov - 0.05, zf - 0.25 + sh * 0.6), f(-sw / 2, -ov - 0.05, zf - 0.25 + sh * 0.6), p["sign"], uvrect=(0, 0, 1, 1))
    if p.get("rail", True):
        A.quad(g, f(x0, -0.02, base), f(x1, -0.02, base), f(x1, -0.02, base + 1.0), f(x0, -0.02, base + 1.0), "chainlink")
        A.quad(g, f(x1, -0.04, base), f(x0, -0.04, base), f(x0, -0.04, base + 1.0), f(x1, -0.04, base + 1.0), "chainlink")
        box(g, f, x0, x1, -0.05, 0.0, base + 1.0, base + 1.06, "white_paint", top="white_paint")
    for d in p.get("doors", []):
        dx, dw, dh = d[:3]; dt = d[3] if len(d) > 3 else "door_white"
        A.quad(g, f(dx - dw / 2, -0.03, 0), f(dx + dw / 2, -0.03, 0), f(dx + dw / 2, -0.03, dh), f(dx - dw / 2, -0.03, dh), dt, uvrect=(0, 0, 1, 1))
    for st in p.get("stairs", []):
        stairs(g, f, st)


def stairs(g, f, st):
    """Open steel stair along the front face: top landing at local (x, z_top), running sideways by dir, `w` wide, at y."""
    xt, zt, dr = st["x"], st["top"], st.get("dir", 1); w = st.get("w", 1.0); y0 = st.get("y", -1.1)
    run = st.get("run", zt * 1.25); n = max(3, int(zt / 0.18))
    tex = st.get("tex", "white_paint")
    xb = xt + dr * run
    for yy in (y0, y0 + w):   # stringers + handrails
        for zo, th in ((0.0, 0.25), (1.0, 0.05)):
            A.quad(g, f(xt, yy, zt + zo - th), f(xb, yy, zo - th if zo else 0), f(xb, yy, zo + (0 if zo == 0 else 0)), f(xt, yy, zt + zo), tex)
            A.quad(g, f(xb, yy, zo - th if zo else 0), f(xt, yy, zt + zo - th), f(xt, yy, zt + zo), f(xb, yy, zo), tex)
        for k in range(0, 4):     # handrail balusters
            xx = xt + dr * run * k / 3; zz = zt * (1 - k / 3)
            pp = f(xx, yy, 0); post(g, pp[0], pp[1], zz, zz + 1.0, 0.025, tex, 4)
    for i in range(n):            # treads
        xx = xt + dr * run * (i + 0.5) / n; zz = zt * (1 - (i + 0.5) / n)
        box(g, f, xx - 0.14, xx + 0.14, y0, y0 + w, zz - 0.03, zz, "steel_grey", top="steel_grey", bottom="steel_grey")
    if st.get("landing", True):
        box(g, f, xt - dr * 1.0 if dr > 0 else xt, xt if dr > 0 else xt + 1.0, y0, y0 + w, zt - 0.1, zt, "steel_grey", top="steel_grey")


def coaches_box(p):
    f, *_ = place(p)
    w, d, h0, h1 = p.get("w", 4.0), p.get("dpt", 2.4), p.get("lift", 0.9), p.get("h", 3.4)
    g = "boxes"
    wall = p.get("wall", "iron_cream")
    box(g, f, -w / 2, w / 2, 0, d, 0, h0, wall)                         # base
    box(g, f, -w / 2, w / 2, 0.02, d, h0, h0 + 0.9, {"front": wall, "back": wall, "left": wall, "right": wall})
    A.quad(g, f(-w / 2, 0.0, h0 + 0.9), f(w / 2, 0.0, h0 + 0.9), f(w / 2, 0.0, h1 - 0.3), f(-w / 2, 0.0, h1 - 0.3), "glass_curtain")
    box(g, f, -w / 2, w / 2, 0.1, d, h0 + 0.9, h1, {"back": wall, "left": wall, "right": wall})
    roof(g, f, -w / 2 - 0.2, w / 2 + 0.2, -0.4, d + 0.2, h1 + 0.25, h1, p.get("roof_tex", "iron_zinc"), th=0.1)


def interchange(p):
    """Players' bench: open-front shelter on the boundary."""
    f, *_ = place(p)
    w, d, h = p.get("w", 8.0), p.get("d_in", p.get("dd", 1.8)), p.get("h", 2.2)
    g = "boxes"; wall = p.get("wall", "iron_cream")
    A.quad(g, f(w / 2, d, 0), f(-w / 2, d, 0), f(-w / 2, d, h), f(w / 2, d, h), wall)
    for xe in (-w / 2, w / 2):
        A.quad(g, f(xe, 0, 0), f(xe, d, 0), f(xe, d, h), f(xe, 0, h), wall)
        A.quad(g, f(xe, d, 0), f(xe, 0, 0), f(xe, 0, h), f(xe, d, h), wall)
    roof(g, f, -w / 2 - 0.1, w / 2 + 0.1, -0.3, d + 0.1, h + 0.2, h, p.get("roof_tex", "iron_zinc"), th=0.08)
    box(g, f, -w / 2 + 0.2, w / 2 - 0.2, d - 0.7, d - 0.3, 0, 0.45, "timber_deck", top="timber_deck")


def scoreboard(p):
    f, *_ = place(p)
    w, h, lift = p.get("w", 8.0), p.get("h", 4.0), p.get("lift", 2.5)
    g = "scoreboard"; tex = p.get("tex", "scoreboard_manual")
    A.quad(g, f(-w / 2, 0, lift), f(w / 2, 0, lift), f(w / 2, 0, lift + h), f(-w / 2, 0, lift + h), tex, uvrect=(0, 0, 1, 1))
    box(g, f, -w / 2 - 0.1, w / 2 + 0.1, 0.01, 1.2, lift - 0.1, lift + h + 0.1, {"back": p.get("back", "iron_green"), "left": p.get("back", "iron_green"), "right": p.get("back", "iron_green")}, top=p.get("roof_tex", "iron_zinc"), bottom="dark_metal")
    for lx in (-w / 2 + 0.4, w / 2 - 0.4):
        for ly in (0.3, 0.9):
            pp = f(lx, ly, 0); post(g, pp[0], pp[1], 0, lift, 0.08, p.get("leg", "steel_grey"), 6)
    if p.get("box"):  # operator hut under (manual boards)
        box(g, f, -w / 2 + 0.3, w / 2 - 0.3, 0.1, 1.1, 0, lift - 0.1, p.get("back", "iron_green"))


def light_tower(p):
    x, y = (ell(p["t"], p.get("d", 12)) if "t" in p else (p["x"], p["y"]))
    h = p.get("h", 30.0); g = "lights"
    led = p.get("led", False)
    taper(g, x, y, 0, h, p.get("r0", 0.35), p.get("r1", 0.18), "steel_grey" if not p.get("conc") else "concrete", 8)
    ang = math.atan2(-y, -x)
    f = frame(x, y, ang - math.pi / 2)
    if led:  # slim LED heads on a short bar
        nh = p.get("heads", 4)
        box(g, f, -1.2, 1.2, -0.3, 0.0, h - 0.15, h + 0.05, "steel_grey", top="steel_grey")
        for i in range(nh):
            lx = -1.0 + 2.0 * i / max(1, nh - 1)
            box(g, f, lx - 0.3, lx + 0.3, -0.7, -0.4, h - 0.6, h - 0.1, {"front": "white_paint", "back": "dark_metal", "left": "dark_metal", "right": "dark_metal"}, top="dark_metal")
    else:   # frame of floods
        rows, cols = p.get("rows", 2), p.get("cols", 4)
        W = cols * 0.9
        box(g, f, -W / 2, W / 2, 0.1, 0.3, h - rows * 0.9 - 0.2, h + 0.2, "steel_grey", top="steel_grey")
        for r in range(rows):
            for c in range(cols):
                lx = -W / 2 + 0.45 + c * 0.9; lz = h - 0.55 - r * 0.9
                box(g, f, lx - 0.32, lx + 0.32, -0.35, 0.1, lz - 0.3, lz + 0.3, {"front": "white_paint", "back": "dark_metal", "left": "dark_metal", "right": "dark_metal"}, top="dark_metal", bottom="dark_metal")


def tree(kind, x, y, h, rnd):
    g = "trees"
    if kind in ("gum", "gum_b"):
        crown = "gum_leaves" if kind == "gum" else "gum_leaves_b"
        tr = h * rnd.uniform(0.40, 0.55)
        lean = (rnd.uniform(-1, 1), rnd.uniform(-1, 1))
        taper(g, x, y, 0, tr, h * 0.022, h * 0.014, "bark_gum", 7, lean)
        # crown: 3-5 clumps of crossed cards
        cx0, cy0 = x + lean[0], y + lean[1]
        for k in range(rnd.randint(3, 5)):
            cx = cx0 + rnd.uniform(-0.18, 0.18) * h; cy = cy0 + rnd.uniform(-0.18, 0.18) * h
            cz = tr + rnd.uniform(0.0, 0.32) * h; s = h * rnd.uniform(0.26, 0.40)
            taper(g, cx0, cy0, tr * 0.8, cz, h * 0.012, h * 0.006, "bark_gum", 5, (cx - cx0, cy - cy0))
            a0 = rnd.uniform(0, math.pi)
            for j in range(4):
                a = a0 + j * math.pi / 4
                dx, dy = math.cos(a) * s, math.sin(a) * s
                A.quad(g, (cx - dx, cy - dy, cz - s * 0.9), (cx + dx, cy + dy, cz - s * 0.9), (cx + dx, cy + dy, cz + s * 1.1), (cx - dx, cy - dy, cz + s * 1.1), crown, uvrect=(0, 0, 1, 1))
    elif kind == "pine":   # cypress windbreak: dense tall cone of crossed cards
        taper(g, x, y, 0, h * 0.2, h * 0.025, h * 0.02, "bark_dark", 6)
        for j in range(4):
            a = j * math.pi / 4 + rnd.uniform(0, 0.3); s = h * 0.32
            dx, dy = math.cos(a) * s, math.sin(a) * s
            A.quad(g, (x - dx, y - dy, h * 0.08), (x + dx, y + dy, h * 0.08), (x + dx, y + dy, h), (x - dx, y - dy, h), "pine_leaves", uvrect=(0, 0, 1, 1))
    elif kind == "palm":
        lean = (rnd.uniform(-1.5, 1.5), rnd.uniform(-1.5, 1.5))
        taper(g, x, y, 0, h, 0.22, 0.17, "palm_trunk", 7, lean)
        tx, ty = x + lean[0], y + lean[1]
        nf = 14
        for k in range(nf):
            a = 2 * math.pi * k / nf + rnd.uniform(-0.15, 0.15)
            L = h * rnd.uniform(0.42, 0.52); up = rnd.uniform(0.2, 0.7)
            ca, sa = math.cos(a), math.sin(a)
            seg = 5; prev = None
            for i in range(seg + 1):
                t = i / seg
                px = tx + ca * L * t; py = ty + sa * L * t; pz = h + L * (up * t - 1.1 * t * t)
                wv = 1.4 * math.sin(math.pi * min(1, t * 1.15 + 0.05)) + 0.15
                lift = 0.55 * wv   # V-trough: leaflet edges raised so the frond reads from the side too
                cur = ((px - sa * wv, py + ca * wv, pz + lift), (px, py, pz), (px + sa * wv, py - ca * wv, pz + lift))
                if prev:
                    v0, v1 = (i - 1) / seg, i / seg
                    A.quad(g, prev[0], prev[1], cur[1], cur[0], "palm_frond", uvrect=(0, v0, 0.5, v1))
                    A.quad(g, prev[1], prev[2], cur[2], cur[1], "palm_frond", uvrect=(0.5, v0, 1, v1))
                prev = cur


def trees():
    rnd = random.Random(SPEC.get("seed", 1) * 7 + 3)
    for t in SPEC.get("trees", []):
        A.zl = t.get("z", 0.0)
        if "p0" in t or "t0" in t:  # a row
            n = t["n"]
            for i in range(n):
                u = (i + rnd.uniform(-0.3, 0.3) * t.get("jit", 1)) / max(1, n - 1)
                if "t0" in t:
                    x, y = ell(t["t0"] + (t["t1"] - t["t0"]) * u, t["d"] + rnd.uniform(-1, 1) * t.get("djit", 3))
                else:
                    x = t["p0"][0] + (t["p1"][0] - t["p0"][0]) * u + rnd.uniform(-1, 1) * t.get("djit", 1.5)
                    y = t["p0"][1] + (t["p1"][1] - t["p0"][1]) * u + rnd.uniform(-1, 1) * t.get("djit", 1.5)
                kind = t["kind"] if t["kind"] != "gum_mix" else rnd.choice(["gum", "gum_b"])
                tree(kind, x, y, t["h"] * rnd.uniform(0.8, 1.2), rnd)
        else:
            tree(t["kind"], t["x"], t["y"], t["h"], rnd)


CAR_COLS = ["rgb:236,236,234", "rgb:30,30,32", "rgb:160,164,168", "rgb:120,20,24", "rgb:40,62,110", "rgb:210,210,206",
            "rgb:70,74,78", "rgb:180,170,150", "rgb:236,236,234", "rgb:96,100,104", "rgb:22,64,44", "rgb:200,60,30"]


def car(x, y, ang, rnd, kind=None):
    g = "cars"
    kind = kind or rnd.choice(["sedan", "sedan", "ute", "suv", "suv"])
    col = rnd.choice(CAR_COLS)
    Lc = {"sedan": 4.7, "ute": 5.3, "suv": 4.8}[kind]; W = 1.85
    f = frame(x, y, ang)
    hb = 0.95 if kind != "sedan" else 0.85
    # body: x along car length, y across
    box(g, lambda lx, ly, z: f(ly, lx, z), -W / 2, W / 2, -Lc / 2, Lc / 2, 0.3, hb, col, top=None)
    if kind == "ute":
        cab = (-Lc / 2 + 1.0, 0.2); A.quad(g, f(-W / 2, 0.2, hb), f(W / 2, 0.2, hb), f(W / 2, Lc / 2, hb), f(-W / 2, Lc / 2, hb), "black_rubber")
    else:
        cab = (-Lc / 2 + 1.1, Lc / 2 - (0.6 if kind == "suv" else 1.0))
    A.quad(g, f(-W / 2, -Lc / 2, hb), f(W / 2, -Lc / 2, hb), f(W / 2, cab[0], hb), f(-W / 2, cab[0], hb), col)
    if kind == "sedan":
        A.quad(g, f(-W / 2, cab[1], hb), f(W / 2, cab[1], hb), f(W / 2, Lc / 2, hb), f(-W / 2, Lc / 2, hb), col)
    ht = hb + (0.65 if kind != "sedan" else 0.55)
    a, b = cab; i0, i1 = a + 0.5, b - 0.25; w2 = W / 2 - 0.12
    win = "rgb:28,36,44"
    A.quad(g, f(-w2, a, hb), f(w2, a, hb), f(w2, i0, ht), f(-w2, i0, ht), win)         # windscreen
    A.quad(g, f(w2, b, hb), f(-w2, b, hb), f(-w2, i1, ht), f(w2, i1, ht), win)
    A.quad(g, f(-w2, i0, ht), f(w2, i0, ht), f(w2, i1, ht), f(-w2, i1, ht), col)       # roof
    for s in (-1, 1):
        q = [f(s * W / 2, a, hb), f(s * W / 2, b, hb), f(s * w2, i1, ht), f(s * w2, i0, ht)]
        A.quad(g, *(q if s > 0 else [q[1], q[0], q[3], q[2]]), win)
    for lx in (-Lc / 2 + 0.85, Lc / 2 - 0.85):   # wheels
        for s in (-1, 1):
            c = f(s * (W / 2 + 0.01), lx, 0.33)
            pts = []
            for k in range(8):
                aa = 2 * math.pi * k / 8
                pts.append(f(s * (W / 2 + 0.01), lx + 0.33 * math.cos(aa), 0.33 + 0.33 * math.sin(aa)))
            A.face(g, pts if s > 0 else pts[::-1], [(0, 0)] * 8, "black_rubber")


def cars():
    rnd = random.Random(SPEC.get("seed", 1) * 13 + 5)
    for c in SPEC.get("cars", []):
        A.zl = c.get("z", 0.0)
        t0, t1, d = c["t0"], c["t1"], c.get("d", 6.0)
        # walk along the ellipse placing nose-in cars 2.8 m apart
        n = 600; ts = [t0 + (t1 - t0) * i / n for i in range(n + 1)]
        acc = 0.0; prev = ell(ts[0], d)
        for t in ts[1:]:
            p = ell(t, d); acc += math.dist(prev, p); prev = p
            if acc >= c.get("gap", 2.8):
                acc = 0.0
                if rnd.random() < c.get("fill", 0.85):
                    x, y = ell(t, d + 2.4)
                    nx, ny = x / AX ** 2, y / BY ** 2
                    ang = math.atan2(ny, nx) + math.pi / 2  # car +y (front) points to field
                    car(x, y, ang + math.pi + rnd.uniform(-0.06, 0.06), rnd)


def sails(p):
    """Shade-sail stand: tiered concrete seating + triangular / quad sails on tilted masts."""
    f, *_ = place(p)
    L = p["len"]; g = "sails"
    for r in range(p.get("rows", 4)):
        z = 0.3 + r * 0.35; y0 = r * 0.8
        box(g, f, -L / 2, L / 2, y0, y0 + 0.8, 0, z, "concrete", top=p.get("seat", "seats_white"))
    n = p.get("n", 3); bw = L / n
    for i in range(n):
        xa = -L / 2 + i * bw; xb = xa + bw
        hi, lo = p.get("hi", 6.5), p.get("lo", 4.2)
        c = [f(xa, -0.5, lo), f(xb, -0.5, hi), f(xb, 4.0, lo), f(xa, 4.0, hi)]
        A.quad(g, c[0], c[1], c[2], c[3], p.get("tex", "sail_white"))
        A.quad(g, c[3], c[2], c[1], c[0], p.get("tex", "sail_white"))
        for pt in c:
            post(g, pt[0], pt[1], 0, pt[2] + 0.3, 0.09, "steel_grey", 6)


def poles():
    for pl in SPEC.get("poles", []):
        post("lights", pl["x"], pl["y"], 0, pl["h"], pl.get("r", 0.06), pl.get("tex", "white_paint"), 8)


def panels():
    """flat textured face (printed board, scoreboard face, sign) facing the field, 'off' m in front of x,y"""
    for p in SPEC.get("panels", []):
        f, *_ = place(p); w = p["w"]; o = -p.get("off", 0.02); z0, z1 = p["z0"], p["z1"]
        A.quad("panels", f(-w / 2, o, z0), f(w / 2, o, z0), f(w / 2, o, z1), f(-w / 2, o, z1), p["tex"], uvrect=(0, 0, 1, 1))
        if p.get("back"):
            A.quad("panels", f(w / 2, o + 0.03, z0), f(-w / 2, o + 0.03, z0), f(-w / 2, o + 0.03, z1), f(w / 2, o + 0.03, z1), p["back"])


def misc_boxes():
    for b in SPEC.get("boxes", []):
        f, *_ = place(b)
        box("buildings", f, -b["w"] / 2, b["w"] / 2, 0, b["dpt"], b.get("z0", 0), b["h"], b["wall"], top=b.get("top", "iron_zinc"))


# ------------------------------------------------------------------ build all
# director 2026-11-18: "Leave field out" - the game draws its own grass inside the boundary fence.
# The field code stays; a spec can set field.draw true to get it back.
if F.get("draw", False):
    disc_field(); markings(); arcs50()
# Director 2026-11-18 "Posts out": the game draws its own posts; a spec can set posts.draw true to get them back.
if SPEC.get("posts", {}).get("draw", False):
    goalposts()
surround(); fence(); signs()
for p in SPEC.get("buildings", []):
    building(p)
for p in SPEC.get("stands", []):
    stand(p)
for p in SPEC.get("coaches", []):
    coaches_box(p)
for p in SPEC.get("benches", []):
    interchange(p)
for p in SPEC.get("scoreboards", []):
    scoreboard(p)
for p in SPEC.get("lights", []):
    light_tower(p)
for p in SPEC.get("sails", []):
    sails(p)
misc_boxes(); panels(); poles(); trees(); cars(); A.zl = 0.0

coll = bpy.data.collections.new(SPEC["name"]); scene.collection.children.link(coll)
objs = A.build(coll)
tris = sum(sum(len(pl.vertices) - 2 for pl in o.data.polygons) for o in objs)
os.makedirs(OUT, exist_ok=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, SPEC["name"] + ".blend"))
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, SPEC["name"] + ".glb"), export_format="GLB", use_selection=False,
                          export_apply=True, export_image_format="AUTO")
print("BUILT", SPEC["name"], "objects", len(objs), "tris", tris)
