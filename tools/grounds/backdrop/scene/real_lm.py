# Landmarks that make a ground's surroundings read as the real place (exec'd by scene.py before saving; shares its
# globals: bpy, np, math, mk_obj, spec, height, ZSEA, HERE). Per-ground entries in spec['real_lm']:
#   ["stadium", glb, x, y, yaw_deg, keep]  another ground's own model (its pitch centre at x, y), decimated to keep
#   ["arch_bridge", [[x, y], ...piers incl. both abutments], [peak above deck per span], deck_above_water, colour]
def _mat_plain(nm, col, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(nm); m.use_nodes = True; b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*[c / 255.0 for c in col], 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    return m

def _lm_stadium(glb, x, y, yaw, keep):
    if not os.path.isabs(glb): glb = os.path.join(os.environ.get('REPO', '/home/user/Afl-auto-battler'), glb)   # repo-relative
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=glb)
    new = [o for o in bpy.data.objects if o not in before]
    # the field level: the terrain's median in a ring just outside the bowl (the DEM's own bowl is unreliable)
    ang = np.linspace(0, 2 * math.pi, 48, endpoint=False)
    z0 = float(np.median(height(x + 190 * np.cos(ang), y + 190 * np.sin(ang))))
    R = __import__('mathutils').Matrix.Translation((x, y, z0)) @ __import__('mathutils').Matrix.Rotation(math.radians(yaw), 4, 'Z')
    roots = [o for o in new if o.parent is None]
    for o in roots: o.matrix_world = R @ o.matrix_world
    tri = 0
    for o in new:
        if o.type != 'MESH': continue
        o.name = 'bg_lm_' + os.path.basename(glb).split('.')[0] + '_' + o.name
        if keep < 1.0:
            m = o.modifiers.new('d', 'DECIMATE'); m.ratio = keep; m.use_collapse_triangulate = True
            bpy.context.view_layer.objects.active = o; bpy.ops.object.modifier_apply(modifier='d')
        tri += sum(len(p.vertices) - 2 for p in o.data.polygons)
    print('landmark stadium', os.path.basename(glb), 'at', round(x), round(y), 'z', round(z0, 1), 'triangles', tri)

def _tube(V, F, path, w, h):
    """square tube w x h along a 3D polyline"""
    P = np.array(path, float)
    for i in range(len(P)):
        t = P[min(i + 1, len(P) - 1)] - P[max(i - 1, 0)]; t /= np.linalg.norm(t) + 1e-9
        s = np.cross(t, [0, 0, 1.0]); s /= np.linalg.norm(s) + 1e-9; u = np.cross(s, t)
        n = len(V)
        for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)): V.append(tuple(P[i] + s * a * w / 2 + u * b * h / 2))
        if i:
            for k in range(4): F.append((n - 4 + k, n - 4 + (k + 1) % 4, n + (k + 1) % 4, n + k))

def _lm_arch_bridge(piers, peaks, deck, col):
    zd = ZSEA + 1.2 + deck; V, F, CV, CF = [], [], [], []
    for (a, b), pk in zip(zip(piers, piers[1:]), peaks):
        a = np.array(a, float); b = np.array(b, float); L = np.linalg.norm(b - a)
        ts = np.linspace(0, 1, 41)
        # each span's arch springs from its two piers below the deck and peaks over mid-span (a sine profile)
        path = [(*(a + (b - a) * t), zd - 2 + (pk + 2) * math.sin(math.pi * t)) for t in ts]
        _tube(V, F, path, 2.4 if pk > 40 else 1.8, 2.8 if pk > 40 else 2.0)
        # hangers: the deck hangs on cables from the arch every 8 m, to both deck edges
        d = (b - a) / L; nrm = np.array([-d[1], d[0]])
        for t in np.arange(8 / L, 1 - 8 / L, 8 / L):
            p = a + (b - a) * t; ztop = zd - 2 + (pk + 2) * math.sin(math.pi * t)
            if ztop - zd < 4: continue
            for sgn in (-1, 1):
                q = p + nrm * sgn * 4.5; _tube(CV, CF, [(p[0], p[1], ztop), (q[0], q[1], zd)], 0.12, 0.12)
    mk_obj('bg_lm_bridge_arches', V, F, _mat_plain('lm_bridge_steel', col, 0.55, 0.3))
    if CV: mk_obj('bg_lm_bridge_cables', CV, CF, _mat_plain('lm_bridge_cable', (70, 72, 76), 0.5, 0.5))
    print('landmark arch bridge', len(piers) - 1, 'spans, deck', round(zd, 1))

for _e in spec.get('real_lm', []):
    if _e[0] == 'stadium': _lm_stadium(*_e[1:])
    elif _e[0] == 'arch_bridge': _lm_arch_bridge(*_e[1:])
