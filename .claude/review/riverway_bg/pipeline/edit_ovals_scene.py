p = 'scene.py'
s = open(p, encoding='utf-8', newline='').read()
nl = '\r\n' if '\r\n' in s else '\n'
blk = r'''# AFL ovals outside the model: OSM outline = boundary line; AFL Laws markings (centre square 50 m, circles 3 m / 10 m with the
# dividing line parallel to the goal lines, goal squares 9 x 6.4 m, 50 m arcs from the centre of each goal line); goal and behind posts 6.4 m apart, no nets
OJ = os.path.join(D, 'ovals.json')
if os.path.exists(OJ):
    ovs = json.load(open(OJ))
    wm = bpy.data.materials.new('oval_line'); wm.use_nodes = True; wm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.86, 0.86, 0.84, 1)
    pm = bpy.data.materials.new('oval_post'); pm.use_nodes = True; pm.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.9, 0.9, 0.88, 1)
    OLV, OLF, PV, PF = [], [], [], []
    def wseg(P0, P1, z, w=0.10):
        dx, dy = P1[0] - P0[0], P1[1] - P0[1]; L = math.hypot(dx, dy)
        if L < 1e-6: return
        nx, ny = -dy / L * w / 2, dx / L * w / 2; n = len(OLV)
        OLV.extend([(P0[0] + nx, P0[1] + ny, z), (P1[0] + nx, P1[1] + ny, z), (P1[0] - nx, P1[1] - ny, z), (P0[0] - nx, P0[1] - ny, z)]); OLF.append([n, n + 1, n + 2, n + 3])
    def inside(x, y, poly):
        c = False; n = len(poly)
        for i in range(n):
            (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): c = not c
        return c
    def post(x, y, z, h, r=0.15):
        n = len(PV); k = 8
        for zz in (z, z + h):
            PV.extend([(x + r * math.cos(2 * math.pi * i / k), y + r * math.sin(2 * math.pi * i / k), zz) for i in range(k)])
        PF.extend([[n + i, n + (i + 1) % k, n + k + (i + 1) % k, n + k + i] for i in range(k)]); PF.append([n + k + i for i in range(k)])
    for (cx, cy, ang, L_, W_), poly in ovs:
        ux, uy = math.cos(ang), math.sin(ang); wx, wy = -uy, ux
        z = float(height(np.array([cx]), np.array([cy]))[0]) + 0.03
        def W(a, b): return (cx + ux * a + wx * b, cy + uy * a + wy * b)
        def L(a, b, c_, d): wseg(W(a, b), W(c_, d), z)
        for i in range(len(poly)): wseg(poly[i], poly[(i + 1) % len(poly)], z)   # boundary line
        hl = L_ / 2
        for a, b, c_, d in [(-25, -25, 25, -25), (25, -25, 25, 25), (25, 25, -25, 25), (-25, 25, -25, -25), (0, -5, 0, 5)]: L(a, b, c_, d)
        for r in (1.5, 5.0):
            pts = [(r * math.cos(t), r * math.sin(t)) for t in np.linspace(0, 2 * math.pi, 33)]
            for (a, b), (c_, d) in zip(pts, pts[1:]): L(a, b, c_, d)
        for sg in (-1, 1):
            g = sg * hl
            for a, b, c_, d in [(g, -3.2, g - sg * 9, -3.2), (g - sg * 9, -3.2, g - sg * 9, 3.2), (g - sg * 9, 3.2, g, 3.2), (g, -9.6, g, 9.6)]: L(a, b, c_, d)
            arc = [(g - sg * 50 * math.cos(t), 50 * math.sin(t)) for t in np.linspace(-math.pi / 2, math.pi / 2, 61)]
            for (a, b), (c_, d) in zip(arc, arc[1:]):
                if inside(*W(a, b), poly) and inside(*W(c_, d), poly): L(a, b, c_, d)
            for b, h in [(-9.6, 6.5), (-3.2, 12.0), (3.2, 12.0), (9.6, 6.5)]: post(*W(g, b), z - 0.03, h)
        print('afl oval', round(cx), round(cy), 'length', round(L_, 1), 'width', round(W_, 1))
    if OLV: mk_obj('bg_oval_lines', OLV, OLF, wm)
    if PV: mk_obj('bg_oval_posts', PV, PF, pm)
'''.replace('\n', nl)
anchor = "bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'scene.blend'))"
assert s.count(anchor) == 1
s = s.replace(anchor, blk + anchor)
open(p, 'w', encoding='utf-8', newline='').write(s)
print('ok')
