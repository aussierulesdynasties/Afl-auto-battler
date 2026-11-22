# GMHBA post pass (the MCG standard, docs/MCG_STANDARD.md): from the Joel Selwood Stand model
# (tools/grounds/gmhba/gmhba.glb) to the match model, with the faults Google Earth 3D shows fixed
# (tools/grounds/gmhba/qa, 2026-11-22):
#   - the north stand's outer roof plates carry their solar panel field (dark rows on the outer 60 % of each plate);
#   - the north stands' outside wall: white fluted cladding, a white band, a dark glazed band behind white V struts;
#   - the Reg Hickey Stand's wall on Moorabool Street: pale grey panels, white pilasters, window strips.
# Textures are drawn by mktex.py (no photo pixels). Blender 5.2 (pip bpy works):
#   python3 tools/grounds/gmhba/post/mktex.py tools/grounds/gmhba/post/tex
#   python3 -c "import runpy,sys; sys.argv=['post', SRC, OUT, TEXDIR]; runpy.run_path('tools/grounds/gmhba/post/post.py')"
import bpy, math, sys

SRC, OUT, TEX = sys.argv[-3:]
TEX = TEX.rstrip('/') + '/'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=SRC)
o = bpy.data.objects['gmhba']
me = o.data
PC = (-8.89, -11.85)   # the field's centre in the model (GroundModels.FIT)


def mat(n, img, rough):
    m = bpy.data.materials.new(n)
    m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    t = m.node_tree.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(TEX + img)
    t.image.name = n
    m.node_tree.links.new(t.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = 0.0
    return m


def slot(m):
    me.materials.append(m)
    return len(me.materials) - 1


S_SOLAR = slot(mat('solar', 'solar.png', 0.55))
S_NORTH = slot(mat('fac_north', 'fac_north.png', 0.8))
S_EAST = slot(mat('fac_east', 'fac_east.png', 0.8))
names = [m.name for m in me.materials]
uv = me.uv_layers.active.data


def ang(x, y):
    return math.degrees(math.atan2(y - PC[1], x - PC[0])) % 360


def ang_u(x, y):
    """Angle in radians, unwrapped round east (the east wall spans 0)."""
    a = math.atan2(y - PC[1], x - PC[0])
    return a


# Solar: the outer roof plates of the north stands, 25-125 degrees (east 0, north 90). The plate's depth runs
# from its leading edge (nearest the field) to its back: measured per 3 degrees from the faces themselves.
sol = []
for p in me.polygons:
    if names[p.material_index] not in ('roof', 'roofg'):
        continue
    c = p.center
    a = ang(c.x, c.y)
    if 25.0 <= a <= 125.0 and abs(p.normal.z) > 0.3 and c.z > 12.0:
        sol.append(p)
lo, hi = {}, {}
for p in sol:
    for i in p.vertices:
        v = me.vertices[i].co
        k = int(ang(v.x, v.y) // 3)
        r = math.hypot(v.x - PC[0], v.y - PC[1])
        lo[k] = min(lo.get(k, 1e9), r)
        hi[k] = max(hi.get(k, -1e9), r)


def depth(x, y):
    a = ang(x, y)
    k = int(a // 3)
    f = a / 3 - k - 0.5
    k2 = k + (1 if f > 0 else -1)
    r = math.hypot(x - PC[0], y - PC[1])
    l0, h0 = lo.get(k), hi.get(k)
    l1, h1 = lo.get(k2, l0), hi.get(k2, h0)
    w = abs(f)
    l, h = l0 * (1 - w) + l1 * w, h0 * (1 - w) + h1 * w
    return min(1.0, max(0.0, (r - l) / max(1.0, h - l)))


for p in sol:
    p.material_index = S_SOLAR
    for li in p.loop_indices:
        v = me.vertices[me.loops[li].vertex_index].co
        uv[li].uv = (ang_u(v.x, v.y) * 120.0 / 6.0, 1.0 - depth(v.x, v.y))

# Walls: vertical faces of the plain 'wall' material on the outside.
nn = ne = 0
for p in me.polygons:
    if names[p.material_index] != 'wall' or abs(p.normal.z) > 0.3:
        continue
    c = p.center
    r = math.hypot(c.x - PC[0], c.y - PC[1])
    a = ang(c.x, c.y)
    radial = abs((p.normal.x * (c.x - PC[0]) + p.normal.y * (c.y - PC[1])) / r)
    if radial < 0.3:
        continue
    if 22.0 <= a <= 112.0 and r > 80.0:
        p.material_index = S_NORTH
        nn += 1
        for li in p.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = (ang_u(v.x, v.y) * 140.0 / 12.0, v.z / 25.0)
    elif (a >= 285.0 or a < 22.0) and r > 80.0 and c.z < 17.5:
        p.material_index = S_EAST
        ne += 1
        for li in p.loop_indices:
            v = me.vertices[me.loops[li].vertex_index].co
            uv[li].uv = (ang_u(v.x, v.y) * 90.0 / 7.5, v.z / 17.0)
print('solar faces', len(sol), 'north wall', nn, 'east wall', ne)
bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB')
print('DONE')
