# Fremantle Oval exterior, built in metres (x east, y north, z up). Blender 5.2.
# Hand-made procedural materials only: no photo pixels anywhere.
import bpy, bmesh, json, math, sys, os
from mathutils import Vector, Matrix
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NO_ADS = True   # director 2026-11-19: no ads, banners, posters or sponsor boards on ground models
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
MODE = argv[0] if argv else 'a04'          # a04 | glb | turn | close
OUT = os.path.abspath(os.path.join(ROOT, argv[1])) if len(argv) > 1 else os.path.join(ROOT, 'build', 'out.png')

G = json.load(open(os.path.join(ROOT, 'osm', 'geo.json')))
E = json.load(open(os.path.join(ROOT, 'fit', 'sat_ellipse.json')))
CAM = json.load(open(os.path.join(ROOT, 'fit', 'cam_a04.json')))
CONTOUR = [tuple(p) for p in json.load(open(os.path.join(ROOT, 'fit', 'contour_v5.json')))['contour']]

bpy.ops.wm.read_factory_settings(use_empty=True)
scn = bpy.context.scene

# ---------------------------------------------------------------- materials
MATS = {}
def node_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs[0], out.inputs[0])
    tc = nt.nodes.new('ShaderNodeTexCoord')
    MATS[name] = m
    return m, nt, bsdf, tc

def rgb(nt, c):
    n = nt.nodes.new('ShaderNodeRGB'); n.outputs[0].default_value = (*c, 1); return n

def mix(nt, fac, a, b):
    n = nt.nodes.new('ShaderNodeMix'); n.data_type = 'RGBA'
    nt.links.new(fac, n.inputs[0])
    for i, c in ((6, a), (7, b)):
        if isinstance(c, tuple): n.inputs[i].default_value = (*c, 1)
        else: nt.links.new(c, n.inputs[i])
    return n.outputs[2]

def sep(nt, tc):
    s = nt.nodes.new('ShaderNodeSeparateXYZ'); nt.links.new(tc.outputs['Object'], s.inputs[0]); return s

def comb(nt, x, y, z=None):
    c = nt.nodes.new('ShaderNodeCombineXYZ')
    for i, v in enumerate((x, y, z)):
        if v is None: continue
        if isinstance(v, (int, float)): c.inputs[i].default_value = v
        else: nt.links.new(v, c.inputs[i])
    return c.outputs[0]

def math_n(nt, op, a, b=None):
    n = nt.nodes.new('ShaderNodeMath'); n.operation = op
    for i, v in enumerate((a, b)):
        if v is None: continue
        if isinstance(v, (int, float)): n.inputs[i].default_value = v
        else: nt.links.new(v, n.inputs[i])
    return n.outputs[0]

def noise(nt, vec, scale, detail=4, rough=0.55):
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail; n.inputs['Roughness'].default_value = rough
    nt.links.new(vec, n.inputs['Vector']); return n.outputs['Fac']

def bump(nt, bsdf, h, strength=0.4, dist=0.02):
    b = nt.nodes.new('ShaderNodeBump'); b.inputs['Strength'].default_value = strength
    b.inputs['Distance'].default_value = dist; nt.links.new(h, b.inputs['Height'])
    nt.links.new(b.outputs[0], bsdf.inputs['Normal'])

def wall_uv(nt, tc):
    # horizontal run = x+y (walls run along x or y), vertical = z
    s = sep(nt, tc)
    return comb(nt, math_n(nt, 'ADD', s.outputs[0], s.outputs[1]), s.outputs[2], 0.0), s

def flat(name, col, rough=0.6, metal=0.0, n_scale=0, n_amt=0.0):
    m, nt, b, tc = node_mat(name)
    if n_scale:
        f = noise(nt, tc.outputs['Object'], n_scale)
        dark = tuple(max(0, c * (1 - n_amt)) for c in col)
        nt.links.new(mix(nt, f, dark, col), b.inputs['Base Color'])
    else:
        b.inputs['Base Color'].default_value = (*col, 1)
    b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    return m

def corrugated(name, col, axis=0, pitch=0.076, metal=0.3, rough=0.5):
    m, nt, b, tc = node_mat(name)
    s = sep(nt, tc)
    w = nt.nodes.new('ShaderNodeTexWave'); w.wave_profile = 'SIN'
    w.inputs['Scale'].default_value = 1.0 / pitch / 6.283 * 6.283 / 1.0
    w.bands_direction = 'X'
    v = comb(nt, s.outputs[axis] if axis < 2 else math_n(nt, 'ADD', s.outputs[0], s.outputs[1]), 0.0, 0.0)
    nt.links.new(math_n(nt, 'MULTIPLY', v, 1.0) if False else v, w.inputs['Vector'])
    w.inputs['Scale'].default_value = 1.0 / pitch
    f = noise(nt, tc.outputs['Object'], 0.35)
    dark = tuple(c * 0.86 for c in col)
    nt.links.new(mix(nt, f, dark, col), b.inputs['Base Color'])
    b.inputs['Metallic'].default_value = metal; b.inputs['Roughness'].default_value = rough
    bump(nt, b, w.outputs['Fac'], 0.5, 0.03)
    return m

def brick(name, brick_col, mortar=(0.78, 0.74, 0.66), painted=False):
    m, nt, b, tc = node_mat(name)
    v, s = wall_uv(nt, tc)
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Color1'].default_value = (*brick_col, 1)
    br.inputs['Color2'].default_value = (*(c * 0.88 for c in brick_col), 1)
    br.inputs['Mortar'].default_value = (*mortar, 1)
    br.inputs['Scale'].default_value = 1.0
    br.inputs['Mortar Size'].default_value = 0.010
    br.inputs['Brick Width'].default_value = 0.23
    br.inputs['Row Height'].default_value = 0.076
    br.offset = 0.5
    nt.links.new(v, br.inputs['Vector'])
    br.inputs['Bias'].default_value = -0.3 if painted else 0.0
    nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.8
    bump(nt, b, br.outputs['Fac'], 0.35, 0.01)
    return m

def boards(name, col, gap=0.15, line=(0.0, 0.0, 0.0)):
    # weatherboard: horizontal boards every `gap` m with a shadow line
    m, nt, b, tc = node_mat(name)
    s = sep(nt, tc)
    z = math_n(nt, 'FRACT', math_n(nt, 'DIVIDE', s.outputs[2], gap))
    edge = math_n(nt, 'GREATER_THAN', z, 0.88)
    shade = mix(nt, z, tuple(c * 0.9 for c in col), col)
    nt.links.new(mix(nt, edge, shade, tuple(c * 0.62 for c in col)), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.55
    bump(nt, b, z, 0.3, 0.01)
    return m

def stone(name, col, block=(0.6, 0.3)):
    m, nt, b, tc = node_mat(name)
    v, s = wall_uv(nt, tc)
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Color1'].default_value = (*col, 1)
    br.inputs['Color2'].default_value = (*(c * 0.9 for c in col), 1)
    br.inputs['Mortar'].default_value = (*(c * 0.8 for c in col), 1)
    br.inputs['Scale'].default_value = 1.0; br.inputs['Mortar Size'].default_value = 0.012
    br.inputs['Brick Width'].default_value = block[0]; br.inputs['Row Height'].default_value = block[1]
    nt.links.new(v, br.inputs['Vector'])
    f = noise(nt, tc.outputs['Object'], 6)
    nt.links.new(mix(nt, f, br.outputs['Color'], tuple(c * 1.05 for c in col)), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.85
    bump(nt, b, br.outputs['Fac'], 0.3, 0.02)
    return m

def asphalt(name, col=(0.11, 0.115, 0.12)):
    m, nt, b, tc = node_mat(name)
    f = noise(nt, tc.outputs['Object'], 40, 6, 0.7)
    g = noise(nt, tc.outputs['Object'], 0.4, 3)
    c = mix(nt, f, tuple(x * 0.8 for x in col), tuple(x * 1.25 for x in col))
    nt.links.new(mix(nt, g, c, tuple(x * 1.1 for x in col)), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.9
    bump(nt, b, f, 0.15, 0.005)
    return m

def pavers(name, col=(0.45, 0.17, 0.12)):
    m, nt, b, tc = node_mat(name)
    s = sep(nt, tc)
    br = nt.nodes.new('ShaderNodeTexBrick')
    br.inputs['Color1'].default_value = (*col, 1)
    br.inputs['Color2'].default_value = (*(c * 0.85 for c in col), 1)
    br.inputs['Mortar'].default_value = (0.55, 0.5, 0.45, 1)
    br.inputs['Scale'].default_value = 1.0; br.inputs['Mortar Size'].default_value = 0.006
    br.inputs['Brick Width'].default_value = 0.2; br.inputs['Row Height'].default_value = 0.1
    nt.links.new(comb(nt, s.outputs[0], s.outputs[1], 0.0), br.inputs['Vector'])
    nt.links.new(br.outputs['Color'], b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.85
    return m

def concrete_steps(name, col=(0.62, 0.6, 0.56)):
    m, nt, b, tc = node_mat(name)
    f = noise(nt, tc.outputs['Object'], 12, 5, 0.6)
    g = noise(nt, tc.outputs['Object'], 0.8, 3)
    c = mix(nt, f, tuple(x * 0.9 for x in col), col)
    nt.links.new(mix(nt, g, c, tuple(x * 0.93 for x in col)), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.88
    bump(nt, b, f, 0.1, 0.004)
    return m

def glass(name, tint=(0.08, 0.12, 0.14)):
    m, nt, b, tc = node_mat(name)
    b.inputs['Base Color'].default_value = (*tint, 1)
    b.inputs['Metallic'].default_value = 0.0; b.inputs['Roughness'].default_value = 0.05
    b.inputs['Coat Weight'].default_value = 1.0
    return m

def leaves(name, col, col2):
    m, nt, b, tc = node_mat(name)
    vor = nt.nodes.new('ShaderNodeTexVoronoi'); vor.inputs['Scale'].default_value = 9
    nt.links.new(tc.outputs['Object'], vor.inputs['Vector'])
    f = noise(nt, tc.outputs['Object'], 2.2, 3)
    c = mix(nt, vor.outputs['Distance'], col2, col)
    nt.links.new(mix(nt, f, c, tuple(x * 0.7 for x in col)), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.7
    bump(nt, b, vor.outputs['Distance'], 0.9, 0.08)
    return m

def sign(name, bg, fg, rows=1):
    # plain hand-painted sign: background + lettering band pattern (no photo pixels)
    m, nt, b, tc = node_mat(name)
    b.inputs['Base Color'].default_value = (*bg, 1)
    b.inputs['Roughness'].default_value = 0.45
    return m

def fret(name):
    # green cast-iron lattice: two diagonal bar sets on dark backing
    m, nt, b, tc = node_mat(name)
    s = sep(nt, tc)
    u1 = math_n(nt, 'ADD', math_n(nt, 'ADD', s.outputs[0], s.outputs[1]), s.outputs[2])
    u2 = math_n(nt, 'SUBTRACT', math_n(nt, 'ADD', s.outputs[0], s.outputs[1]), s.outputs[2])
    f1 = math_n(nt, 'GREATER_THAN', math_n(nt, 'FRACT', math_n(nt, 'DIVIDE', u1, 0.35)), 0.72)
    f2 = math_n(nt, 'GREATER_THAN', math_n(nt, 'FRACT', math_n(nt, 'DIVIDE', u2, 0.35)), 0.72)
    bar = math_n(nt, 'MAXIMUM', f1, f2)
    nt.links.new(mix(nt, bar, (0.015, 0.03, 0.02), (0.05, 0.22, 0.11)), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.5
    return m

def chain_mesh(name):
    m, nt, b, tc = node_mat(name)
    s = sep(nt, tc)
    u1 = math_n(nt, 'ADD', math_n(nt, 'ADD', s.outputs[0], s.outputs[1]), s.outputs[2])
    u2 = math_n(nt, 'SUBTRACT', math_n(nt, 'ADD', s.outputs[0], s.outputs[1]), s.outputs[2])
    f1 = math_n(nt, 'GREATER_THAN', math_n(nt, 'FRACT', math_n(nt, 'DIVIDE', u1, 0.07)), 0.82)
    f2 = math_n(nt, 'GREATER_THAN', math_n(nt, 'FRACT', math_n(nt, 'DIVIDE', u2, 0.07)), 0.82)
    w = math_n(nt, 'MAXIMUM', f1, f2)
    nt.links.new(mix(nt, w, (0.018, 0.02, 0.02), (0.05, 0.17, 0.09)), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.7
    return m

def balustrade(name):
    # white balusters every 0.14 m on a dark backing, top and bottom rails (deck 2.7 m, top 3.85 m)
    m, nt, b, tc = node_mat(name)
    s = sep(nt, tc)
    h = math_n(nt, 'ADD', s.outputs[0], s.outputs[1])
    fr = math_n(nt, 'FRACT', math_n(nt, 'DIVIDE', h, 0.16))
    hole = math_n(nt, 'MULTIPLY', math_n(nt, 'GREATER_THAN', fr, 0.3), math_n(nt, 'LESS_THAN', fr, 0.7))
    band = math_n(nt, 'MULTIPLY', math_n(nt, 'GREATER_THAN', s.outputs[2], 2.9), math_n(nt, 'LESS_THAN', s.outputs[2], 3.25))
    v = math_n(nt, 'MULTIPLY', hole, band)
    nt.links.new(mix(nt, v, (0.86, 0.86, 0.83), (0.03, 0.035, 0.04)), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.5
    return m

def corr_h(name, col, pitch=0.076):
    # corrugated sheet laid with its ribs horizontal (wave runs up the sheet)
    m, nt, b, tc = node_mat(name)
    s = sep(nt, tc)
    w = nt.nodes.new('ShaderNodeTexWave'); w.wave_profile = 'SIN'; w.bands_direction = 'X'
    nt.links.new(comb(nt, s.outputs[2], 0.0, 0.0), w.inputs['Vector'])
    w.inputs['Scale'].default_value = 1.0 / pitch
    nt.links.new(mix(nt, w.outputs['Fac'], tuple(c * 0.8 for c in col), col), b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = 0.5
    bump(nt, b, w.outputs['Fac'], 0.6, 0.03)
    return m

def chain_see(name):
    # see-through chain-wire: galvanised diamond wires, open between them
    m, nt, b, tc = node_mat(name)
    s = sep(nt, tc)
    u1 = math_n(nt, 'ADD', math_n(nt, 'ADD', s.outputs[0], s.outputs[1]), s.outputs[2])
    u2 = math_n(nt, 'SUBTRACT', math_n(nt, 'ADD', s.outputs[0], s.outputs[1]), s.outputs[2])
    f1 = math_n(nt, 'GREATER_THAN', math_n(nt, 'FRACT', math_n(nt, 'DIVIDE', u1, 0.07)), 0.85)
    f2 = math_n(nt, 'GREATER_THAN', math_n(nt, 'FRACT', math_n(nt, 'DIVIDE', u2, 0.07)), 0.85)
    w = math_n(nt, 'MAXIMUM', f1, f2)
    b.inputs['Base Color'].default_value = (0.42, 0.44, 0.45, 1)
    b.inputs['Metallic'].default_value = 0.6; b.inputs['Roughness'].default_value = 0.5
    nt.links.new(math_n(nt, 'ADD', math_n(nt, 'MULTIPLY', w, 0.85), 0.12), b.inputs['Alpha'])
    return m

M = dict(
    roof_zinc_pav=corrugated('roof_zinc_pav', (0.05, 0.17, 0.32), axis=1, metal=0.0, rough=0.75),
    fret=fret('fret'),
    balustrade=balustrade('balustrade'),
    seat_timber=flat('seat_timber', (0.032, 0.032, 0.022), 0.8, 0, 6, 0.2),
    roof_zinc=corrugated('roof_zinc', (0.42, 0.48, 0.52), axis=1),
    roof_zinc_x=corrugated('roof_zinc_x', (0.42, 0.48, 0.52), axis=0),
    roof_white=corrugated('roof_white', (0.86, 0.87, 0.85), axis=0, metal=0.2, rough=0.5),
    roof_ns=flat('roof_ns', (0.36, 0.34, 0.31), 0.9, 0.0, 3, 0.04),   # matte: the 0.55/0.1 roof threw sun glints (white) where a04 is a flat 175-188 grey-beige
    silver=flat('silver', (0.72, 0.74, 0.76), 0.3, 0.9),
    galv=flat('galv', (0.62, 0.64, 0.65), 0.35, 0.85, 3, 0.15),
    green=flat('green_steel', (0.035, 0.16, 0.08), 0.45, 0.3),
    white=flat('white_paint', (0.86, 0.86, 0.83), 0.5, 0.0, 2, 0.05),
    cream_boards=boards('cream_boards', (0.86, 0.80, 0.62)),
    red_brick=brick('red_brick', (0.42, 0.11, 0.07), painted=True),
    brick=brick('brick', (0.50, 0.24, 0.15)),
    cream=flat('cream_quoin', (0.84, 0.77, 0.6), 0.6, 0, 3, 0.06),
    limestone=stone('limestone', (0.78, 0.70, 0.55)),
    render_white=flat('render_white', (0.88, 0.88, 0.86), 0.6, 0, 1.5, 0.06),
    asphalt=asphalt('asphalt', (0.30, 0.27, 0.24)),
    pavers=pavers('pavers'),
    concrete=concrete_steps('concrete'),
    glass=glass('glass'),
    dark=flat('shade_interior', (0.04, 0.045, 0.05), 0.9),
    seat_green=flat('seat_green', (0.05, 0.3, 0.14), 0.4),
    seat_white=flat('seat_white', (0.85, 0.86, 0.84), 0.4),
    seat_navy=flat('seat_navy', (0.03, 0.07, 0.12), 0.4),
    seat_plank=flat('seat_plank', (0.25, 0.225, 0.18), 0.8),
    seat_pavchair=flat('seat_pavchair', (0.30, 0.28, 0.23), 0.7, 0, 9, 0.35),
    maroon=flat('maroon_fascia', (0.32, 0.04, 0.12), 0.45),
    red=flat('club_red', (0.62, 0.04, 0.05), 0.45),
    mural_red=flat('mural_red', (0.22, 0.006, 0.009), 0.45),
    fig=leaves('fig', (0.05, 0.13, 0.04), (0.11, 0.22, 0.07)),
    pine=leaves('pine', (0.04, 0.12, 0.06), (0.09, 0.2, 0.09)),
    bark=flat('bark', (0.22, 0.18, 0.14), 0.9, 0, 8, 0.3),
    lamp=flat('lamp', (0.9, 0.9, 0.85), 0.2, 0.0),
    grass_edge=flat('kerb_grass', (0.12, 0.3, 0.06), 0.9, 0, 5, 0.2),
    solar=flat('solar', (0.04, 0.06, 0.12), 0.15, 0.3),
    screen=flat('led_screen', (0.02, 0.02, 0.025), 0.2),
    sign_white=flat('sign_white', (0.9, 0.9, 0.9), 0.4),
    dirt=flat('dirt', (0.30, 0.22, 0.15), 0.95, 0, 4, 0.25),
    black=flat('black_paint', (0.025, 0.025, 0.028), 0.55, 0, 2, 0.04),
    roof_dark=corrugated('roof_dark', (0.12, 0.13, 0.14), axis=1, metal=0.2, rough=0.6),
    cream_letters=flat('cream_letters', (0.88, 0.84, 0.72), 0.5),
    mural_pink=flat('mural_pink', (0.93, 0.42, 0.62), 0.6),
    corr_white_h=corr_h('corr_white_h', (0.88, 0.88, 0.86)),
    brick_pink=brick('brick_pink', (0.86, 0.76, 0.76), mortar=(0.9, 0.88, 0.86), painted=True),
    chain_see=chain_see('chain_see'),
    skylight=flat('skylight', (0.80, 0.82, 0.80), 0.35),
    glass_green=glass('glass_green', (0.10, 0.20, 0.17)),
    steel_dark=flat('steel_dark', (0.06, 0.065, 0.07), 0.5, 0.4),
    roof_cream=corrugated('roof_cream', (0.80, 0.78, 0.71), axis=0, metal=0.15, rough=0.55),
    soffit=corrugated('soffit', (0.09, 0.095, 0.10), axis=0, metal=0.1, rough=0.7),
    aircon=flat('aircon', (0.80, 0.80, 0.78), 0.45, 0.1),
    mid_grey=flat('mid_grey', (0.40, 0.41, 0.42), 0.6),
    step_dark=flat('step_dark', (0.13, 0.13, 0.135), 0.8),
)

# ---------------------------------------------------------------- geometry helpers
def obj_from(bm, name, mat):
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me); scn.collection.objects.link(ob)
    if isinstance(mat, (list, tuple)):
        for mm in mat: me.materials.append(M[mm])
    else:
        me.materials.append(M[mat])
    return ob

def prism(poly, z0, z1, name, mat, top=True):
    bm = bmesh.new()
    lo = [bm.verts.new((x, y, z0)) for x, y in poly]
    hi = [bm.verts.new((x, y, z1)) for x, y in poly]
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
    if top: bm.faces.new(hi)
    bm.normal_update(); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return obj_from(bm, name, mat)

def box(c, size, name, mat, rot=0.0):
    cx, cy, cz = c; sx, sy, sz = size
    ca, sa = math.cos(rot), math.sin(rot)
    pts = [(-sx/2, -sy/2), (sx/2, -sy/2), (sx/2, sy/2), (-sx/2, sy/2)]
    poly = [(cx + x*ca - y*sa, cy + x*sa + y*ca) for x, y in pts]
    return prism(poly, cz - sz/2, cz + sz/2, name, mat)

def faces_obj(quads, name, mat):
    bm = bmesh.new(); cache = {}
    def V(p):
        k = tuple(round(c, 4) for c in p)
        if k not in cache: cache[k] = bm.verts.new(k)
        return cache[k]
    for q in quads:
        try: bm.faces.new([V(p) for p in q])
        except ValueError: pass
    bm.normal_update()
    return obj_from(bm, name, mat)

def cyl(p0, p1, r, name, mat, seg=12):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    bpy.ops.mesh.primitive_cylinder_add(vertices=seg, radius=r, depth=d.length, location=(p0 + p1) / 2)
    ob = bpy.context.object; ob.name = name
    ob.rotation_euler = d.to_track_quat('Z', 'Y').to_euler()
    ob.data.materials.append(M[mat]); return ob

def polyline_offset(pts, d):
    pts = np.array(pts, float); out = []
    for i in range(len(pts)):
        a = pts[i - 1]; b = pts[(i + 1) % len(pts)]
        t = b - a; t /= np.linalg.norm(t) + 1e-9
        nrm = np.array([t[1], -t[0]])
        out.append(pts[i] + nrm * d)
    return out

# outward normal sign: contour is listed clockwise or ccw?
cn = np.array(CONTOUR)
area = 0.5 * np.sum(cn[:, 0] * np.roll(cn[:, 1], -1) - np.roll(cn[:, 0], -1) * cn[:, 1])
OUTSIGN = 1.0 if area > 0 else -1.0   # (t1,-t0) points right of travel; ccw -> right is outward

def off(d):
    return polyline_offset(CONTOUR, OUTSIGN * d)

# ---------------------------------------------------------------- ground surfaces
# outer edge of the ground: the limestone boundary wall (OSM 225638069) from the south-east round to the north, then
# the north-west car park, the pavilion rear and the south buildings
SITE = [(-125, 55), (-125, -20), (-112, -35), (-95, -60), (-75, -95), (-60, -128),
        (60.2, -126.5), (80.8, -110.0), (89.7, -102.9), (102.0, -93.1), (100.7, -82.0), (97.3, -51.6), (93.9, -22.1),
        (92.2, -7.3), (88.1, 20.8), (85.7, 42.2), (81.6, 75.6), (78.2, 93.8), (76.3, 96.9), (56.3, 110.8),
        (52.8, 112.0), (22.0, 109.3), (-16.2, 103.9), (-57.1, 99.5), (-60, 104), (-100, 85), (-118, 70)]
def clip_cell(x0, y0, x1, y1):
    # SITE clipped to one convex grid cell (Sutherland-Hodgman)
    out = list(SITE)
    for inside, cut in ((lambda p: p[0] >= x0, lambda a, b: (x0, a[1] + (b[1] - a[1]) * (x0 - a[0]) / (b[0] - a[0]))),
                        (lambda p: p[0] <= x1, lambda a, b: (x1, a[1] + (b[1] - a[1]) * (x1 - a[0]) / (b[0] - a[0]))),
                        (lambda p: p[1] >= y0, lambda a, b: (a[0] + (b[0] - a[0]) * (y0 - a[1]) / (b[1] - a[1]), y0)),
                        (lambda p: p[1] <= y1, lambda a, b: (a[0] + (b[0] - a[0]) * (y1 - a[1]) / (b[1] - a[1]), y1))):
        src, out = out, []
        for i in range(len(src)):
            a, b = src[i - 1], src[i]
            if inside(b):
                if not inside(a): out.append(cut(a, b))
                out.append(b)
            elif inside(a): out.append(cut(a, b))
        if not out: return []
    return out
def in_site(pt):
    x, y = pt; c = False; n = len(SITE)
    for i in range(n):
        x1, y1 = SITE[i]; x2, y2 = SITE[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): c = not c
    return c

PAV_G = 1.8
def zg(x, y):
    fx = -107.5 + 0.16 * y
    t = min(max((-80.0 - x) / (-80.0 - fx), 0.0), 1.0)
    w = min(max(min(y + 16.0, 58.0 - y) / 8.0, 0.0), 1.0)
    return PAV_G * t * w

def ground():
    # apron ring around the grass (game owns the grass), car park asphalt, brick paving to the south
    inner = off(0.0); outer = off(6.0)
    q = []
    n = len(inner)
    for i in range(n):
        j = (i + 1) % n
        q.append([(*inner[i], 0.0), (*inner[j], 0.0), (*outer[j], 0.0), (*outer[i], 0.0)])
    faces_obj(q, 'apron', 'concrete')
    # big asphalt base under everything, outside the apron (simple grid of quads, skipping the oval)
    poly = np.array(outer)
    def inside(pt):
        x, y = pt; c = False; n = len(poly)
        for i in range(n):
            x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
            if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1): c = not c
        return c
    q = []; qp = []
    FM = np.load(os.path.join(ROOT, 'build', 'ground_fine.npy'))   # 0.5 m paver mask, row 0 = y 140, col 0 = x -135
    def fm(xa, ya, s):
        c0, r0 = int(round((xa + 135) * 2)), int(round((140 - ya - s) * 2)); k = int(round(s * 2))
        blk = FM[max(r0, 0):r0 + k, max(c0, 0):c0 + k]
        return blk.mean() if blk.size else 0.0
    def cell(xa, ya, s, out):
        c = [(xa, ya), (xa + s, ya), (xa + s, ya + s), (xa, ya + s)]
        if all(inside(p) for p in c): return
        cl = c if all(in_site(p) for p in c) else clip_cell(xa, ya, xa + s, ya + s)
        if len(cl) < 3: return
        out.append([(a, b, zg(a, b) - 0.02) for a, b in cl])
    step = 2.0
    for x in np.arange(-135, 115, step):
        for y in np.arange(-135, 140, step):
            f = fm(x, y, step)
            if f <= 0.0 or f >= 1.0:
                cell(x, y, step, qp if f >= 1.0 else q)
            else:   # paver edge: split into 0.5 m cells so the edge follows the satellite outline
                for sx in np.arange(x, x + step, 0.5):
                    for sy in np.arange(y, y + step, 0.5):
                        cell(sx, sy, 0.5, qp if fm(sx, sy, 0.5) >= 0.5 else q)
    faces_obj(q, 'ground_asphalt', 'asphalt'); faces_obj(qp, 'ground_pavers', 'pavers')   # cover from the satellite, 0.5 m at paver edges
    # red brick paving: SFFC forecourt / south walk (satellite 2025-12-06: red band south-west to south)
    q = []
    o1 = off(6.0); o2 = off(16.0)
    for i in range(len(o1)):
        j = (i + 1) % len(o1)
        x, y = CONTOUR[i]
        if y < -40 and x < 45:
            q.append([(*o1[i], 0.0), (*o1[j], 0.0), (*o2[j], 0.0), (*o2[i], 0.0)])
    faces_obj(q, 'south_pavers', 'pavers')
    faces_obj([[(-76.0, 93.1, 0.01), (-68.3, 87.0, 0.01), (-63.9, 93.0, 0.01), (-68.4, 98.2, 0.01)]], 'nw_sand', 'dirt')

# ---------------------------------------------------------------- boundary fence
def fence():
    p = off(0.6); n = len(p)
    q = []
    for i in range(n):
        j = (i + 1) % n
        for z0, z1 in ((0.85, 0.92), (0.08, 0.14)):
            q.append([(*p[i], z0), (*p[j], z0), (*p[j], z1), (*p[i], z1)])
    faces_obj(q, 'fence_rail', 'maroon')
    acc = 0.0; nxt = 0.0; k = 0
    for i in range(n):
        a_ = np.array(p[i]); b_ = np.array(p[(i + 1) % n]); seg = np.linalg.norm(b_ - a_)
        while acc + seg >= nxt:
            t = (nxt - acc) / max(seg, 1e-9); x, y = a_ + (b_ - a_) * t
            cyl((x, y, 0), (x, y, 0.92), 0.03, f'fence_post_{k}', 'maroon', 6); k += 1; nxt += 3.1
        acc += seg
    # white bollards on the asphalt behind the north-west fence (a04 u 1743-1909, v 1933-1961: 1.4 m)
    for k, (x, y) in enumerate(((-67.9, 58.7), (-66.5, 61.0), (-65.5, 63.5), (-63.4, 65.4))):
        cyl((x, y, 0), (x, y, 1.4), 0.06, f'bollard_{k}', 'white', 8)

# ---------------------------------------------------------------- terraces (east side)
def in_terrace(x, y):
    return (y > 74 and x > -12) or (y <= 74 and x > 28 and y > -84)

def terrace(rows=11, tread=0.85, rise=0.40, start=1.6):
    idx = [i for i, (x, y) in enumerate(CONTOUR) if in_terrace(x, y)]
    # keep contiguous run order around the contour
    q = []; risers = []
    for r in range(rows):
        a = off(start + r * tread); b = off(start + (r + 1) * tread)
        z = (r + 1) * rise
        for k in range(len(idx) - 1):
            i, j = idx[k], idx[k + 1]
            if (j - i) % len(CONTOUR) != 1: continue
            q.append([(*a[i], z), (*a[j], z), (*b[j], z), (*b[i], z)])
            risers.append([(*a[i], z - rise), (*a[j], z - rise), (*a[j], z), (*a[i], z)])
    faces_obj(q + risers, 'east_terrace', 'concrete')
    # earth bank under the figs behind the top step (g08, a04): level with the top step, then down to the street
    zt = rows * rise; d0 = start + rows * tread
    top = off(d0); far = off(d0 + 14.0); foot = off(d0 + 18.0)
    bank = []
    for k in range(len(idx) - 1):
        i, j = idx[k], idx[k + 1]
        if (j - i) % len(CONTOUR) != 1: continue
        bank.append([(*top[i], zt), (*top[j], zt), (*far[j], zt), (*far[i], zt)])
        bank.append([(*far[i], zt), (*far[j], zt), (*foot[j], 0.0), (*foot[i], 0.0)])
    faces_obj(bank, 'terrace_bank', 'dirt')
    # sign boards on white posts along the top (a04: post 3.75 m, posts 6.4 m apart; g08: boards face the oval)
    pl = off(d0 + 0.45)
    pts = [np.array(pl[i]) for i in idx]
    acc = 0.0; nxt = 2.0; posts = []
    for k in range(len(pts) - 1):
        if (idx[k + 1] - idx[k]) % len(CONTOUR) != 1: continue
        seg = np.linalg.norm(pts[k + 1] - pts[k])
        while acc + seg >= nxt:
            t = (nxt - acc) / seg; posts.append((pts[k] + (pts[k + 1] - pts[k]) * t, pts[k + 1] - pts[k])); nxt += 6.4
        acc += seg
    for n_, (pp, tv) in enumerate([] if NO_ADS else posts):   # advertising boards: none on a ground model (no ads rule)
        x, y = pp; rot = math.atan2(tv[1], tv[0])
        cyl((x, y, zt), (x, y, zt + 3.75), 0.06, f'tsign_post_{n_}', 'white', 8)
        box((x, y, zt + 3.15), (3.0, 0.06, 1.1), f'tsign_board_{n_}', 'sign_white', rot=rot)
    # crush barrier rails every 3 rows
    for r in range(3, rows, 3):
        a = off(start + r * tread)
        for k in range(len(idx) - 1):
            i, j = idx[k], idx[k + 1]
            if (j - i) % len(CONTOUR) != 1: continue
            pass
    # perimeter advertising boards at the front of the terrace (satellite & a04: boards at grass edge)
    fb = off(1.0); q = []
    for k in range(len(idx) - 1):
        i, j = idx[k], idx[k + 1]
        if (j - i) % len(CONTOUR) != 1: continue
        if fb[i][1] > 80 and fb[j][0] < 12.7: continue
        q.append([(*fb[i], 0), (*fb[j], 0), (*fb[j], 0.9), (*fb[i], 0.9)])
    if not NO_ADS: faces_obj(q, 'terrace_boards', 'seat_white')   # perimeter ad boards: none (no ads rule)

# ---------------------------------------------------------------- Victoria Pavilion (a04 fit 2026-11-18)
# Front line (oval side) x = -107.5 + 0.16 y. Seven gables, ridges every 6.79 m from y 0.42.
# Front edge: ridge 10.4 m, valley 8.9 m (slope 0.44 per m); the end slopes run on to y -6.7 and 49.9.
# Roof rises 0.107 m per metre toward the street. Depth 13.0 m at y 0, 11.6 m at y 45 (satellite).
K = 0.16
BN = Vector((-1.0, K, 0.0)).normalized()
RIDGES = [0.42 + 6.79 * i for i in range(7)]
Y_S, Y_N = -6.7, 49.9
def front_x(y): return -107.5 + K * y
def pdepth(y): return 13.0 - 0.031 * y
def zfront(y):
    d = min(abs(y - r) for r in RIDGES); return 10.4 - 0.44 * d
def PF(y, s=0.0, z=0.0):   # point at front line y, s metres back toward the street
    return (front_x(y) + BN.x * s, y + BN.y * s, z)
def rise(s): return 0.107 * s

def pavilion():
    ys = [Y_S, Y_N]
    for r in RIDGES:
        ys += [r, r + 3.395]
    ys = sorted(set(round(y, 3) for y in ys if Y_S <= y <= Y_N))
    q = []
    for a, b in zip(ys[:-1], ys[1:]):
        da, db = pdepth(a), pdepth(b)
        q.append([PF(a, -0.5, zfront(a) - 0.05), PF(b, -0.5, zfront(b) - 0.05),
                  PF(b, db, zfront(b) + rise(db)), PF(a, da, zfront(a) + rise(da))])
    faces_obj(q, 'pav_roof', 'roof_zinc_pav')
    q = []
    for a, b in zip(ys[:-1], ys[1:]):
        q.append([PF(a, -0.5, zfront(a) - 0.35), PF(b, -0.5, zfront(b) - 0.35), PF(b, -0.5, zfront(b) - 0.05), PF(a, -0.5, zfront(a) - 0.05)])
    faces_obj(q, 'pav_barge', 'white')
    zv = 10.4 - 0.44 * 3.395
    gab = []
    for r in RIDGES:
        ya, yb = max(r - 3.395, Y_S), min(r + 3.395, Y_N)
        gab.append([PF(ya, 0.3, zv), PF(yb, 0.3, zv), PF(r, 0.3, zfront(r) - 0.35)])
    faces_obj(gab, 'pav_fretwork', 'fret')
    cyl(PF(Y_S + 0.4, 0.2, zv - 0.15), PF(Y_N - 0.4, 0.2, zv - 0.15), 0.12, 'pav_beam', 'green', 8)
    posts = [Y_S + 0.4, RIDGES[0] - 3.395] + [r + 3.395 for r in RIDGES] + [Y_N - 0.4]
    for i, y in enumerate(posts):
        cyl(PF(y, 0.2, 2.7), PF(y, 0.2, zv - 0.1), 0.13, f'pav_post_{i}', 'green', 8)
    q = []
    for i in range(9):
        z = 2.7 + i * 0.45; s0 = 1.2 + i * 1.0; s1 = s0 + 1.0
        q.append([PF(Y_S, s0, z), PF(Y_N, s0, z), PF(Y_N, s1, z), PF(Y_S, s1, z)])
        q.append([PF(Y_S, s1, z), PF(Y_N, s1, z), PF(Y_N, s1, z + 0.45), PF(Y_S, s1, z + 0.45)])
    faces_obj(q, 'pav_tiers', 'seat_timber')
    def bx6(pts):   # pts: 4 plan corners (x, y) + z0, z1 -> 6 quads
        (c, z0, z1) = pts; lo = [(*v, z0) for v in c]; hi = [(*v, z1) for v in c]
        return [hi, lo[::-1]] + [[lo[k], lo[(k + 1) % 4], hi[(k + 1) % 4], hi[k]] for k in range(4)]
    pl = []; br = []   # g39: long timber plank benches, three 100 mm planks with 20 mm gaps, on white cast brackets every 1.0 m
    for i in range(9):
        z = 2.7 + i * 0.45; s1 = 1.2 + i * 1.0 + 1.0; b0 = s1 - 0.62
        for k in range(3):
            u0 = b0 + k * 0.12; u1 = u0 + 0.10
            pl += bx6(([PF(Y_S, u0)[:2], PF(Y_N, u0)[:2], PF(Y_N, u1)[:2], PF(Y_S, u1)[:2]], z + 0.385, z + 0.42))
        for y_ in np.arange(Y_S + 0.5, Y_N - 0.3, 1.0):
            Q = lambda u, w: [PF(y_, u)[:2], PF(y_ + w, u)[:2], PF(y_ + w, u + 0.03)[:2], PF(y_, u + 0.03)[:2]]
            br += bx6((Q(b0 + 0.12, 0.03), z, z + 0.385))                       # upright under the middle plank
            br += bx6(([PF(y_, b0 + 0.02)[:2], PF(y_ + 0.03, b0 + 0.02)[:2], PF(y_ + 0.03, b0 + 0.30)[:2], PF(y_, b0 + 0.30)[:2]], z + 0.355, z + 0.385))  # arm under the planks
            br += bx6(([PF(y_, b0 + 0.12)[:2], PF(y_ + 0.03, b0 + 0.12)[:2], PF(y_ + 0.03, b0 + 0.26)[:2], PF(y_, b0 + 0.26)[:2]], z, z + 0.03))     # foot to the back
    faces_obj(pl, 'pav_seats', 'seat_plank'); faces_obj(br, 'pav_seat_legs', 'white')
    M.setdefault('mesh_dark', chain_mesh('mesh_dark'))
    prism([PF(Y_S, -0.2)[:2], PF(Y_N, -0.2)[:2], PF(Y_N, 1.2)[:2], PF(Y_S, 1.2)[:2]], 0, 2.6, 'pav_plinth', 'mesh_dark', top=False)
    faces_obj([[PF(Y_S, -0.2, 2.6), PF(Y_N, -0.2, 2.6), PF(Y_N, 1.2, 2.6), PF(Y_S, 1.2, 2.6)]], 'pav_deck', 'concrete')
    faces_obj([[PF(Y_S, -0.23, 2.45), PF(Y_N, -0.23, 2.45), PF(Y_N, -0.23, 2.75), PF(Y_S, -0.23, 2.75)]], 'pav_fascia', 'white')
    faces_obj([[PF(Y_S, -0.23, 0.0), PF(Y_N, -0.23, 0.0), PF(Y_N, -0.23, PAV_G + 0.25), PF(Y_S, -0.23, PAV_G + 0.25)]], 'pav_kerb', 'maroon')
    GAPS = [(6.1, 8.6), (19.9, 22.0), (33.9, 36.9)]   # g09 stairs at x 295-345, 590-632, 870-930 (y = -2.975 + (x - 132) / 20); first one a04 u 392-442
    edges = [Y_S] + [v for g in GAPS for v in g] + [Y_N]
    q = []
    for a, b in zip(edges[0::2], edges[1::2]):
        q.append([PF(a, 0.0, 2.75), PF(b, 0.0, 2.75), PF(b, 0.0, 3.4), PF(a, 0.0, 3.4)])
    faces_obj(q, 'pav_balustrade', 'balustrade')
    for gi, (a, b) in enumerate(GAPS):
        for k in range(4):
            z1 = PAV_G + (k + 1) * (2.6 - PAV_G) / 4
            s0, s1 = -0.2 - (4 - k) * 0.3, -0.2 - (3 - k) * 0.3
            prism([PF(a, s0)[:2], PF(b, s0)[:2], PF(b, s1)[:2], PF(a, s1)[:2]], 0, z1, f'pav_stair_{gi}_{k}', 'concrete')
        for y in (a + 0.08, b - 0.08):
            cyl(PF(y, -1.35, PAV_G + 1.1), PF(y, -0.15, 3.5), 0.03, f'pav_stair_rail_{gi}_{y:.1f}', 'green', 6)
            cyl(PF(y, -1.35, PAV_G), PF(y, -1.35, PAV_G + 1.1), 0.03, f'pav_stair_post_{gi}_{y:.1f}', 'green', 6)
    ARMCO = [(-5.8, 4.2), (8.9, 18.7), (22.4, 25.4), (29.4, 33.2), (37.7, 47.4)]   # g09 x 75-275, 370-565, 640-700, 780-855, 945-1140
    q = []
    for a, b in ARMCO:
        q.append([PF(a, -1.8, PAV_G + 0.42), PF(b, -1.8, PAV_G + 0.42), PF(b, -1.8, PAV_G + 0.76), PF(a, -1.8, PAV_G + 0.76)])
        for k, y in enumerate(np.arange(a + 0.3, b, 2.0)):
            cyl(PF(y, -1.65, PAV_G - 0.3), PF(y, -1.65, PAV_G + 0.7), 0.05, f'pav_armco_post_{a}_{k}', 'galv', 6)
    faces_obj(q, 'pav_armco', 'white')
    q = []; q2 = []
    for a, b in zip(ys[:-1], ys[1:]):
        da, db = pdepth(a), pdepth(b)
        q.append([PF(a, da, 0), PF(b, db, 0), PF(b, db, 5.0), PF(a, da, 5.0)])
        q2.append([PF(a, da, 5.0), PF(b, db, 5.0), PF(b, db, zfront(b) + rise(db) - 0.05), PF(a, da, zfront(a) + rise(da) - 0.05)])
    faces_obj(q, 'pav_rear_brick', 'red_brick')
    faces_obj(q2, 'pav_rear_boards', 'cream_boards')
    for y, nm in ((Y_S, 's'), (Y_N, 'n')):
        d = pdepth(y)
        faces_obj([[PF(y, 0, 0), PF(y, d, 0), PF(y, d, zfront(y) + rise(d)), PF(y, 0, zfront(y))]], f'pav_end_{nm}', 'cream_boards')
    rot = math.atan2(BN.y, BN.x)
    c = PF(-6.6, 2.3)
    box((c[0], c[1], 5.8), (4.4, 4.4, 11.6), 'pav_turret_s', 'cream', rot=rot)
    box((c[0], c[1], 11.75), (5.0, 5.0, 0.3), 'pav_turret_s_cornice', 'white', rot=rot)
    dome((c[0], c[1], 11.9), 2.5, 2.6, 'pav_turret_s_dome', ogee=True)
    cyl((c[0], c[1], 14.5), (c[0], c[1], 15.6), 0.08, 'pav_turret_s_finial', 'silver', 8)
    tx, ty = -109.5, 49.5
    box((tx, ty, 3.75), (4.6, 4.6, 7.5), 'pav_tower', 'red_brick', rot=rot)
    for dx in (-2.35, 2.35):
        for dy in (-2.35, 2.35):
            box((tx + dx * math.cos(rot) - dy * math.sin(rot), ty + dx * math.sin(rot) + dy * math.cos(rot), 3.75), (0.45, 0.45, 7.5), f'pav_quoin_{dx}_{dy}', 'cream', rot=rot)
    box((tx, ty, 8.75), (4.7, 4.7, 2.5), 'pav_tower_upper', 'cream', rot=rot)
    box((tx, ty, 10.1), (5.3, 5.3, 0.3), 'pav_tower_cornice', 'white', rot=rot)
    dome((tx, ty, 10.25), 2.7, 3.1, 'pav_tower_dome', ogee=True)
    cyl((tx, ty, 13.3), (tx, ty, 17.5), 0.05, 'pav_tower_flag', 'white', 6)
    # north verandah (g36 2023-12-11: balcony with white balustrade, blue hip roof on green posts, fenced
    # under-croft; a04 2024-07-15: stair from the balcony down toward the oval). Depth 4.5 m north of the stand.
    tv = Vector((tx, ty, 0.0)) - Vector(PF(Y_N, 0.0)); st = tv.dot(BN) - 2.4      # back edge = tower's east face
    ya, yb, sa, sb = Y_N, Y_N + 4.5, -0.2, st
    prism([PF(ya, sa)[:2], PF(yb, sa)[:2], PF(yb, sb)[:2], PF(ya, sb)[:2]], 2.45, 2.6, 'pav_ann_deck', 'concrete')
    faces_obj([[PF(ya, sa, 0.0), PF(yb, sa, 0.0), PF(yb, sa, 2.45), PF(ya, sa, 2.45)],
               [PF(yb, sa, 0.0), PF(yb, sb, 0.0), PF(yb, sb, 2.45), PF(yb, sa, 2.45)]], 'pav_ann_fence', 'mesh_dark')
    SG = (yb - 1.3, yb - 0.1)     # stair opening at the NE corner of the balcony
    faces_obj([[PF(ya, sa, 2.75), PF(SG[0], sa, 2.75), PF(SG[0], sa, 3.4), PF(ya, sa, 3.4)],
               [PF(yb, sa + 0.0, 2.75), PF(yb, sb, 2.75), PF(yb, sb, 3.4), PF(yb, sa, 3.4)]], 'pav_ann_balustrade', 'balustrade')
    for k, (y_, s_) in enumerate(((ya, sa), (yb, sa), (yb, sb), (ya + (yb - ya) / 2, sa))):
        cyl(PF(y_, s_, 2.6), PF(y_, s_, 5.4), 0.1, f'pav_ann_post_{k}', 'green', 8)
    e = 0.4; zr, ze = 6.9, 5.4
    c0, c1, c2, c3 = PF(ya - 0.2, sa - e, ze), PF(yb + e, sa - e, ze), PF(yb + e, sb + e, ze), PF(ya - 0.2, sb + e, ze)
    ym = (ya + yb) / 2; r0, r1 = PF(ym, sa + 2.2, zr), PF(ym, sb - 2.2, zr)
    faces_obj([[c0, c1, r0], [c1, c2, r1, r0], [c2, c3, r1], [c3, c0, r0, r1]], 'pav_ann_roof', 'roof_zinc_pav')
    faces_obj([[PF(ya - 0.2, sa - e, ze - 0.25), PF(yb + e, sa - e, ze - 0.25), PF(yb + e, sa - e, ze), PF(ya - 0.2, sa - e, ze)],
               [PF(yb + e, sa - e, ze - 0.25), PF(yb + e, sb + e, ze - 0.25), PF(yb + e, sb + e, ze), PF(yb + e, sa - e, ze)]], 'pav_ann_fascia', 'green')
    for k in range(13):     # stair down toward the oval, 13 risers of 0.2 m
        z1 = 2.6 - k * 0.2; s0_ = sa - (k + 1) * 0.28
        prism([PF(SG[0], s0_)[:2], PF(SG[1], s0_)[:2], PF(SG[1], s0_ + 0.28)[:2], PF(SG[0], s0_ + 0.28)[:2]], 0.0, z1, f'pav_ann_step_{k}', 'concrete')
    for y_ in SG:
        cyl(PF(y_, sa, 3.5), PF(y_, sa - 13 * 0.28, 0.9), 0.03, f'pav_ann_rail_{y_:.1f}', 'green', 6)


def dome(c, r, h, name, ogee=False, seg=24):
    cx, cy, cz = c; rings = 10
    bm = bmesh.new(); vs = []
    for i in range(rings + 1):
        t = i / rings
        if ogee:
            rr = r * (1 - t) ** 0.6 * (1 + 0.35 * math.sin(math.pi * t)) if t < 1 else 0
        else:
            rr = r * math.cos(t * math.pi / 2)
        z = cz + h * t
        vs.append([bm.verts.new((cx + rr * math.cos(a), cy + rr * math.sin(a), z))
                   for a in np.linspace(0, 2 * math.pi, seg, endpoint=False)])
    for i in range(rings):
        for j in range(seg):
            k = (j + 1) % seg
            try: bm.faces.new((vs[i][j], vs[i][k], vs[i + 1][k], vs[i + 1][j]))
            except ValueError: pass
    bm.normal_update()
    return obj_from(bm, name, 'silver')

# ---------------------------------------------------------------- other buildings from OSM footprints
def way(k): return [tuple(p) for p in G['ways'][k]][:-1]

def buildings():
    # north stand (Fremantle Community Bank Oval fascia, Bendigo Bank): roof 8 m
    # North stand (a04 2024-07-15 rays meet the satellite front line at 9.5 m; g33 shows a skillion
    # falling to the back). Main bay x -34..-12.5, then the roof bends back along the boundary to (-3.4, 97.1).
    def nfr(x): return 82.4 + (x + 40.8) * 0.184
    # a04 sign corners (z_sign.jpg) meet the satellite front line: maroon band x -32.3..-14.5, white Bendigo
    # panel to x -8.4; the fascia rises to the right (top 10.36 -> 11.38 -> 11.62, bottom 9.42 -> 10.02 -> 9.83)
    SL, SR, SB = (-32.3, nfr(-32.3)), (-14.5, nfr(-14.5)), (-8.4, nfr(-8.4))
    F0, F1, F2 = (-34.0, nfr(-34.0)), SB, (-3.4, 97.1)
    B0, B1, B2 = (-34.0, nfr(-34.0) + 13.2), (-8.7, nfr(-8.4) + 12.8), (-4.6, 101.6)
    ZB = 8.3
    def zin(x, xs, zs):
        if x <= xs[0]: return zs[0] + (x - xs[0]) * (zs[1] - zs[0]) / (xs[1] - xs[0])
        for k in range(len(xs) - 1):
            if x <= xs[k + 1]: return zs[k] + (x - xs[k]) * (zs[k + 1] - zs[k]) / (xs[k + 1] - xs[k])
        return zs[-1]
    XS = (-32.3, -14.5, -8.4)
    # re-read 2026-11-18 by colour runs down each a04 column (band top 1819 -> 1866, bottom 1842 -> 1884 over u 2640-2930;
    # blue panel top 1878 -> 1888, bottom 1899 -> 1910 over u 2990-3050): the fascia is near level, about 1 m deep
    def zbot(x): return zin(x, XS, (9.25, 9.7, 9.58))
    def ztop(x): return zin(x, XS, (10.34, 10.55, 10.57))
    # a04 colours: the band is the Community Bank purple (shaded 55-60, 30-35, 70), the Bendigo panel pale blue with
    # navy-purple lettering and mark
    M.setdefault('bank_purple', flat('bank_purple', (0.30, 0.105, 0.205), 0.45))   # maroon-magenta, hue from g33/a04 sign pixels
    M.setdefault('bendigo_blue', flat('bendigo_blue', (0.50, 0.74, 0.92), 0.4))
    M.setdefault('bendigo_ink', flat('bendigo_ink', (0.05, 0.04, 0.16), 0.45))
    ZF2 = 9.5                                  # roof edge where it bends back (a04 white edge falls past u 3065)
    faces_obj([[(*F0, zbot(F0[0])), (*SL, zbot(SL[0])), (*B0, ZB)],
               [(*SL, zbot(SL[0])), (*SR, zbot(SR[0])), (*F1, zbot(F1[0])), (*B1, ZB), (*B0, ZB)],
               [(*F1, zbot(F1[0])), (*F2, ZF2), (*B2, ZB), (*B1, ZB)]], 'nstand_roof', 'roof_ns')
    def lerp(a, b, t): return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
    def band(pts, z0, z1, name, mat):
        faces_obj([[(*a, z0), (*b, z0), (*b, z1), (*a, z1)] for a, b in zip(pts[:-1], pts[1:])], name, mat)
    def plate(pa, pb, name, mat):
        faces_obj([[(*pa, zbot(pa[0])), (*pb, zbot(pb[0])), (*pb, ztop(pb[0])), (*pa, ztop(pa[0]))]], name, mat)
    plate(SL, SR, 'nstand_sign_maroon', 'bank_purple')
    plate(SR, SB, 'nstand_sign_white', 'white')   # sponsor panel painted out (no ads)
    faces_obj([[(*F0, zbot(F0[0]) - 0.15), (*SL, zbot(SL[0]) - 0.15), (*SL, zbot(SL[0])), (*F0, zbot(F0[0]))]], 'nstand_eave_l', 'white')
    faces_obj([[(*F1, zbot(F1[0]) - 0.3), (*F2, ZF2 - 0.3), (*F2, ZF2), (*F1, zbot(F1[0]))]], 'nstand_edge', 'white')
    faces_obj([[(*F2, ZB - 0.3), (*B2, ZB - 0.3), (*B2, ZB), (*F2, ZF2)]], 'nstand_end_r', 'white')
    faces_obj([[(*F0, ZB - 0.3), (*B0, ZB - 0.3), (*B0, ZB), (*F0, zbot(F0[0]))]], 'nstand_end_l', 'white')
    # sign lettering, modelled, tilted with the rising fascia
    import math as _m
    def letters(text, a, b, size, mat, name):
        bpy.ops.object.text_add(location=(0, 0, 0))
        ob = bpy.context.object; ob.name = name
        ob.data.body = text; ob.data.align_x = 'CENTER'; ob.data.align_y = 'CENTER'
        ob.data.size = size; ob.data.extrude = 0.01
        dx, dy = b[0] - a[0], b[1] - a[1]; L = _m.hypot(dx, dy)
        bpy.ops.object.convert(target='MESH')
        w = ob.dimensions.x
        if w > L * 0.94: s_ = L * 0.94 / w; ob.scale = (s_, s_, 1)
        za = (zbot(a[0]) + ztop(a[0])) / 2; zb_ = (zbot(b[0]) + ztop(b[0])) / 2
        nx, ny = dy / L, -dx / L          # outward (toward the oval)
        ob.location = ((a[0] + b[0]) / 2 + nx * 0.05, (a[1] + b[1]) / 2 + ny * 0.05, (za + zb_) / 2)
        tilt = _m.atan2(zb_ - za, L)
        ob.rotation_euler = (Matrix.Rotation(_m.atan2(dy, dx), 4, 'Z') @ Matrix.Rotation(_m.pi / 2, 4, 'X')
                             @ Matrix.Rotation(tilt, 4, 'Z')).to_euler()
        ob.data.materials.clear(); ob.data.materials.append(M[mat])
    letters('Fremantle Community Bank Oval', SL, SR, 0.85, 'white', 'nstand_txt1')
    letters('Bendigo Bank', lerp(SR, SB, 0.22), SB, 0.95, 'bendigo_ink', 'nstand_txt2')
    # Bendigo "B" mark: maroon square at the white panel's left end (a04 u 2958-2985)
    lx = lerp(SR, SB, 0.09)
    box((lx[0], lx[1] - 0.06, (zbot(lx[0]) + ztop(lx[0])) / 2), (0.9, 0.04, 0.8), 'nstand_logo', 'bendigo_ink',
        rot=_m.atan2(SB[1] - SR[1], SB[0] - SR[0]))
    # front posts (a04: under the fascia at u 2710, 2905, 3075 and the ends)
    nstand_posts = [-34.0, -25.08, -15.11]
    # back wall (white panels, a04 behind the right bay) and the limestone base along the front
    band([B0, B1, B2], 0, ZB, 'nstand_back', 'render_white')
    # tiered bench seats from the fence back to the wall: 12 rows rising 0.42 m
    # a04: the first row sits right behind the fence boards (board tops v 2035 at u 2980, rows above them), so the
    # rows start on the fence line + 0.4 m (boards are on +1.0) and run back to the B line
    fl = [tuple(v) for v in off(1.4)[160:206] if -39.0 <= v[0] <= -3.4]
    fl.sort(key=lambda v: v[0])
    fl = [(-39.0, fl[0][1])] + fl + [(-3.4, fl[-1][1])]
    # a04: the rows run on west past the roof; their ends step back from x -39.0 (front row) to -36.1 (top row)
    def row_fl(i):
        xl = -39.0 + 2.9 * i / 11.0
        out = []
        for a, b in zip(fl[:-1], fl[1:]):
            if b[0] <= xl: continue
            if a[0] < xl: a = (xl, a[1] + (b[1] - a[1]) * (xl - a[0]) / (b[0] - a[0]))
            if not out: out.append(a)
            out.append(b)
        return out
    def bk(x):
        if x <= B1[0]: t = (x - B0[0]) / (B1[0] - B0[0]); return lerp(B0, B1, t)
        t = (x - B1[0]) / (B2[0] - B1[0]); return lerp(B1, B2, t)
    q = []; r = []; nose = []
    for i in range(12):
        t0, t1 = i / 12.0, (i + 1) / 12.0
        z = 0.45 + i * 0.42
        rf = row_fl(i)
        for fa, fb in zip(rf[:-1], rf[1:]):
            ba, bb = bk(fa[0]), bk(fb[0])
            a0, b0 = lerp(fa, ba, t0), lerp(fb, bb, t0)
            a1, b1 = lerp(fa, ba, t1), lerp(fb, bb, t1)
            q.append([(*a0, z), (*b0, z), (*b1, z), (*a1, z)])
            r.append([(*a0, z - 0.42), (*b0, z - 0.42), (*b0, z - 0.06), (*a0, z - 0.06)])
            nose.append([(*a0, z - 0.06), (*b0, z - 0.06), (*b0, z + 0.003), (*a0, z + 0.003)])
    # 3D empty navy seats (g33): level, all square to one stand axis, in straight rows every 0.5 m on each tread
    def inq(P4, c):   # point inside a convex quad (either winding)
        sg = [np.cross(P4[(k + 1) % 4] - P4[k], c - P4[k]) for k in range(4)]
        return all(v >= 0 for v in sg) or all(v <= 0 for v in sg)
    fvs = []
    for t in q:
        a0, b0, b1, a1 = [np.array(v[:2]) for v in t]; L = np.linalg.norm(b0 - a0)
        if L < 0.3: continue
        e = (b0 - a0) / L; nv = np.array([-e[1], e[0]]); f0 = (a0 + b0) / 2 - (a1 + b1) / 2
        fvs.append((nv if nv @ f0 > 0 else -nv) * L)
    fv = np.sum(fvs, axis=0); fv /= np.linalg.norm(fv); ax = np.array([-fv[1], fv[0]])
    rows = {}
    for t in q: rows.setdefault(round(t[0][2], 2), []).append(t)
    ch = []
    for z, ts in rows.items():
        segs = []
        for t in ts:
            a0, b0, b1, a1 = [np.array(v[:2]) for v in t]
            p0, p1 = a0 * 0.55 + a1 * 0.45, b0 * 0.55 + b1 * 0.45
            if (p1 - p0) @ ax < 0: p0, p1 = p1, p0
            if np.linalg.norm(p1 - p0) > 0.05: segs.append((p0 @ ax, p0, p1))
        segs.sort(key=lambda r: r[0]); carry = 0.25; prev = None; done = []; dirs = []
        for _, p0, p1 in segs:     # walk the row's seat line by arc length, 0.5 m pitch, across the tread pieces
            if prev is not None and np.linalg.norm(p0 - prev) > 0.3: carry = 0.25   # a stair or gap: restart the row
            L = np.linalg.norm(p1 - p0); e = (p1 - p0) / L; nv = np.array([-e[1], e[0]]); nv = nv if nv @ fv > 0 else -nv
            k = carry
            while k <= L - 0.0:
                c_ = p0 + e * k
                if all(np.hypot(*(c_ - d_)) >= 0.45 for d_ in done[-40:]):   # tread pieces overlap at the west corner
                    done.append(c_); dirs.append(nv)
                k += 0.5
            carry = k - L; prev = p1
        if done:   # facing turns smoothly along the row (tread pieces kink up to 23 deg at the west end): 4 m moving average
            D = np.array(dirs); K = 8
            for m_, c_ in enumerate(done):
                f_ = D[max(0, m_ - K):m_ + K + 1].mean(0); f_ /= np.linalg.norm(f_)
                ch += chair_q(c_, f_, z, h=0.40, hb=0.38)
    faces_obj(q, 'nstand_treads', 'concrete')
    faces_obj(ch, 'nstand_seats', 'seat_navy')
    faces_obj(r, 'nstand_risers', 'concrete')
    faces_obj(nose, 'nstand_nosing', 'concrete')
    # posts on the seat front line, up to the roof underside there (front edge -> back line B)
    def fy(x):
        for a, b in zip(fl[:-1], fl[1:]):
            if a[0] <= x <= b[0]: return a[1] + (b[1] - a[1]) * (x - a[0]) / max(b[0] - a[0], 1e-9)
        return fl[0][1] if x < fl[0][0] else fl[-1][1]
    def roof_front(x):
        if x <= F1[0]: return nfr(x), zbot(x)
        t = (x - F1[0]) / (F2[0] - F1[0]); return F1[1] + (F2[1] - F1[1]) * t, zbot(F1[0]) + (ZF2 - zbot(F1[0])) * t
    for i, x in enumerate(nstand_posts):
        y = fy(x); yf, zf = roof_front(x); yb = bk(x)[1]
        zc = zf + (ZB - zf) * (y - yf) / (yb - yf)
        cyl((x, y, 0), (x, y, zc), 0.12, f'nstand_col_{i}', 'seat_navy', 8)

    # "WISH YOU WERE HERE" gate (a04 2024-07-15, front face from the pillar-foot rays u 1360..1745 at v 1870)
    import math as _m
    GA = Vector((-97.1, 54.9, 0.0)); GB = Vector((-86.5, 71.6, 0.0))
    gd = (GB - GA).normalized(); gn = Vector((gd.y, -gd.x, 0.0))      # gn points out toward the oval
    GL = (GB - GA).length
    grot = _m.atan2(gd.y, gd.x)
    def GP(s_, t_, z_):
        v = GA + gd * s_ + gn * t_; return (v.x, v.y, z_)
    def gbox(s0, s1, t0, t1, z0, z1, name, mat):
        faces = []
        c = [GP(s0, t0, z0), GP(s1, t0, z0), GP(s1, t1, z0), GP(s0, t1, z0),
             GP(s0, t0, z1), GP(s1, t0, z1), GP(s1, t1, z1), GP(s0, t1, z1)]
        for f in ((0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7), (4, 5, 6, 7), (0, 3, 2, 1)):
            faces.append([c[i] for i in f])
        faces_obj(faces, name, mat)
    def gflat(pts2d, name, mat, t_=0.03):        # flat shape on the front face, points in (s, z)
        faces_obj([[GP(s_, t_, z_) for s_, z_ in pts2d]], name, mat)
    S_L, S_C0, S_C1, S_R = 2.6, 2.6, 15.4, 19.8
    # end blocks: black painted render, 4.9 m; right block with a curved Dutch parapet and a pier
    gbox(0.0, S_L, -5.0, 0.0, 0, 4.9, 'gate_block_l', 'black')
    gbox(S_C1, S_R, -5.0, 0.0, 0, 4.9, 'gate_block_r', 'black')
    par = [(17.7, 4.9)] + [(17.7 + 1.7 * k / 10, 4.9 + 1.5 * _m.sin(_m.pi * k / 10) ** 0.6) for k in range(1, 10)] + [(19.4, 4.9)]
    faces_obj([[GP(s_, 0.0, z_) for s_, z_ in par], [GP(s_, -0.3, z_) for s_, z_ in reversed(par)]], 'gate_parapet', 'black')
    gbox(19.35, S_R, -0.4, 0.0, 0, 6.7, 'gate_pier', 'black')
    # centre: dark hip roof on pillars, eaves 2.4 m, ridge 4.6 m
    E0, E1, RZ = 2.4, 4.6, 4.6
    faces_obj([[GP(S_C0, 0.3, E0), GP(S_C1, 0.3, E0), GP(S_C1 - 2.0, -2.5, RZ), GP(S_C0 + 2.0, -2.5, RZ)],
               [GP(S_C0, -5.3, E0), GP(S_C0 + 2.0, -2.5, RZ), GP(S_C1 - 2.0, -2.5, RZ), GP(S_C1, -5.3, E0)],
               [GP(S_C0, 0.3, E0), GP(S_C0 + 2.0, -2.5, RZ), GP(S_C0, -5.3, E0)],
               [GP(S_C1, 0.3, E0), GP(S_C1, -5.3, E0), GP(S_C1 - 2.0, -2.5, RZ)]], 'gate_roof', 'roof_dark')
    gbox(S_C0, S_C1, 0.0, 0.3, E0 - 0.25, E0, 'gate_beam', 'black')
    # lettered pillars (W-I-S-H, Y-O-U, W-E-R-E, H-E-R-E) and plain posts behind
    PIL = [(3.86, 0.7, 'WISH'), (6.17, 0.8, 'YOU'), (11.8, 0.8, 'WERE'), (14.1, 0.7, 'HERE')]
    for k, (sc, w, word) in enumerate(PIL):
        gbox(sc - w / 2, sc + w / 2, -0.6, 0.0, 0, E0 - 0.25, f'gate_pillar_{k}', 'black')
        for j, ch in enumerate(word):
            bpy.ops.object.text_add(location=(0, 0, 0))
            ob = bpy.context.object; ob.name = f'gate_letter_{k}_{j}'
            ob.data.body = ch; ob.data.align_x = 'CENTER'; ob.data.align_y = 'CENTER'
            ob.data.size = 0.42; ob.data.extrude = 0.01
            bpy.ops.object.convert(target='MESH')
            ob.location = GP(sc, 0.04, 1.95 - j * 0.46)
            ob.rotation_euler = (_m.pi / 2, 0, grot)
            ob.data.materials.clear(); ob.data.materials.append(M['cream_letters'])
    for k, sc in enumerate((5.0, 8.9, 13.0)):
        cyl(GP(sc, -4.6, 0), GP(sc, -4.6, E0), 0.12, f'gate_post_back_{k}', 'black', 8)
    # centre gable porch: eaves 2.3 m, apex 4.0 m, white bargeboards, white beam
    P0, P1, PT = 6.8, 11.1, 0.8
    pm = (P0 + P1) / 2
    faces_obj([[GP(P0, PT, 2.3), GP(pm, PT, 4.0), GP(pm, -1.5, 4.0), GP(P0, -1.5, 2.3)],
               [GP(pm, PT, 4.0), GP(P1, PT, 2.3), GP(P1, -1.5, 2.3), GP(pm, -1.5, 4.0)]], 'gate_porch_roof', 'roof_dark')
    faces_obj([[GP(P0 + 0.2, PT - 0.05, 2.45), GP(P1 - 0.2, PT - 0.05, 2.45), GP(pm, PT - 0.05, 3.8)]], 'gate_porch_tympanum', 'black')
    for a_, b_ in (((P0, 2.3), (pm, 4.0)), ((pm, 4.0), (P1, 2.3))):
        cyl(GP(a_[0], PT + 0.02, a_[1]), GP(b_[0], PT + 0.02, b_[1]), 0.09, f'gate_barge_{a_[0]:.0f}', 'white', 6)
    cyl(GP(P0, PT, 2.3), GP(P1, PT, 2.3), 0.1, 'gate_porch_beam', 'white', 6)
    for sc in (P0 + 0.15, P1 - 0.15):
        cyl(GP(sc, PT - 0.1, 0), GP(sc, PT - 0.1, 2.3), 0.1, f'gate_porch_post_{sc:.0f}', 'black', 8)
    gbox(7.2, 10.8, 0.8, 3.2, 0, 0.2, 'gate_step_1', 'concrete')
    gbox(7.2, 10.8, 0.8, 2.0, 0.2, 0.4, 'gate_step_2', 'concrete')
    # pink palm murals (hand-drawn shapes): one on the left block, two on the right block
    def palm(cs, cz, fl, base_s, tag):
        fr_ = []
        for k in range(9):
            a = _m.radians(-15 + k * 210 / 8 - 15)
            ex, ez = cs + fl * _m.cos(a), cz + fl * 0.7 * _m.sin(a) - (0.25 * fl if abs(_m.cos(a)) > 0.6 else 0)
            px, pz = -_m.sin(a) * 0.13 * fl, _m.cos(a) * 0.13 * fl
            fr_.append([(cs + px, cz + pz), (cs + (ex - cs) * 0.5 + px * 1.3, cz + (ez - cz) * 0.5 + pz * 1.3), (ex, ez),
                        (cs + (ex - cs) * 0.5 - px, cz + (ez - cz) * 0.5 - pz)])
        for k, f in enumerate(fr_):
            gflat(f, f'gate_palm_{tag}_frond_{k}', 'mural_pink', 0.03 + 0.001 * k)
        n = 8; tr = []
        for k in range(n + 1):
            u_ = k / n; s_ = cs + (base_s - cs) * u_ + 0.25 * _m.sin(_m.pi * u_); z_ = cz - (cz - 0.15) * u_
            tr.append((s_, z_, 0.09 + 0.07 * u_))
        q = []
        for (s0, z0, w0), (s1, z1, w1) in zip(tr[:-1], tr[1:]):
            q.append([GP(s0 - w0, 0.025, z0), GP(s0 + w0, 0.025, z0), GP(s1 + w1, 0.025, z1), GP(s1 - w1, 0.025, z1)])
        faces_obj(q, f'gate_palm_{tag}_trunk', 'mural_pink')
    palm(1.3, 3.9, 1.0, 1.7, 'l')
    palm(16.6, 3.9, 1.35, 17.4, 'r1')
    palm(17.9, 3.0, 0.95, 18.3, 'r2')
    # round FREO logo, top right of the right block
    ring = [(18.75 + 0.55 * _m.cos(2 * _m.pi * k / 24), 4.05 + 0.55 * _m.sin(2 * _m.pi * k / 24)) for k in range(24)]
    gflat(ring, 'gate_logo_disc', 'sign_white', 0.035)
    bpy.ops.object.text_add(location=(0, 0, 0))
    ob = bpy.context.object; ob.name = 'gate_logo_text'
    ob.data.body = 'FREO'; ob.data.align_x = 'CENTER'; ob.data.align_y = 'CENTER'; ob.data.size = 0.3; ob.data.extrude = 0.005
    bpy.ops.object.convert(target='MESH')
    ob.location = GP(18.75, 0.045, 4.05); ob.rotation_euler = (_m.pi / 2, 0, grot)
    ob.data.materials.clear(); ob.data.materials.append(M['black'])
    # limestone wall running on past the right block
    gbox(S_R, S_R + 2.2, -0.5, 0.0, 0, 3.0, 'gate_wall_r', 'limestone')

    # George Grljusich media box (OSM 225638050): 3 storeys cream weatherboard, green trim, twin gables
    mb = way('225638050')
    xs = [p[0] for p in mb]; ys = [p[1] for p in mb]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    W_ = y1 - y0
    global MB_EYE, MB_AT, MB_EYE2
    MB_EYE = (x1 + 22, (y0 + y1) / 2 - 6, 5.0); MB_AT = (x1, (y0 + y1) / 2, 6.5); MB_EYE2 = (x0 - 28, (y0 + y1) / 2 + 4, 3.0)
    def rect(xa, xb, ya, yb): return [(xa, ya), (xb, ya), (xb, yb), (xa, yb)]
    def yf(f): return y0 + f * W_
    # g22 (oval face, x1): three glazed levels, cream weatherboard bands, two cantilevered floor slabs with green fascias
    prism(mb, 0, 10.0, 'media_walls', 'cream_boards')
    for k, (z0, z1) in enumerate(((3.75, 4.35), (7.1, 7.75))):
        prism(rect(x1, x1 + 0.7, y0 - 0.15, y1 + 0.15), z0, z1, f'media_slab_{k}', 'cream_boards')
        faces_obj([[(x1 + 0.71, y0 - 0.15, z1 - 0.3), (x1 + 0.71, y1 + 0.15, z1 - 0.3), (x1 + 0.71, y1 + 0.15, z1), (x1 + 0.71, y0 - 0.15, z1)]], f'media_slab_fascia_{k}', 'green')
    gl, mu, wm = [], [], []
    for (za, zb, fa, fb) in ((1.0, 3.6, 0.03, 0.97), (5.3, 6.95, 0.03, 0.97), (8.55, 9.8, 0.40, 0.97)):
        gl.append([(x1 + 0.02, yf(fa), za), (x1 + 0.02, yf(fb), za), (x1 + 0.02, yf(fb), zb), (x1 + 0.02, yf(fa), zb)])
        nb = 3 if za > 8 else 4
        for i in range(nb + 1):
            f = fa + (fb - fa) * i / nb
            (mu if i in (0, nb) else wm).append([(x1 + 0.04, yf(f) - 0.06, za), (x1 + 0.04, yf(f) + 0.06, za), (x1 + 0.04, yf(f) + 0.06, zb), (x1 + 0.04, yf(f) - 0.06, zb)])
        mu.append([(x1 + 0.04, yf(fa), za - 0.1), (x1 + 0.04, yf(fb), za - 0.1), (x1 + 0.04, yf(fb), za), (x1 + 0.04, yf(fa), za)])
        mu.append([(x1 + 0.04, yf(fa), zb), (x1 + 0.04, yf(fb), zb), (x1 + 0.04, yf(fb), zb + 0.1), (x1 + 0.04, yf(fa), zb + 0.1)])
    faces_obj(gl, 'media_glaze', 'glass')
    faces_obj(mu, 'media_mullions', 'green')
    faces_obj(wm, 'media_mullions_white', 'white')
    # green name board with a white edge on the band under the middle level (g22)
    faces_obj([[(x1 + 0.03, yf(0.35), 4.52), (x1 + 0.03, yf(0.64), 4.52), (x1 + 0.03, yf(0.64), 5.14), (x1 + 0.03, yf(0.35), 5.14)]], 'media_name_edge', 'white')
    faces_obj([[(x1 + 0.04, yf(0.355), 4.56), (x1 + 0.04, yf(0.635), 4.56), (x1 + 0.04, yf(0.635), 5.10), (x1 + 0.04, yf(0.355), 5.10)]], 'media_name_board', 'green')
    for k, (txt, z) in enumerate((('GEORGE GRLJUSICH', 4.95), ('MEDIA BOX', 4.71))):
        bpy.ops.object.text_add(location=(0, 0, 0))
        ob = bpy.context.object; ob.name = f'media_name_text_{k}'
        ob.data.body = txt; ob.data.font = bpy.data.fonts.load('C:/Windows/Fonts/arialbd.ttf', check_existing=True)
        ob.data.align_x = 'CENTER'; ob.data.align_y = 'CENTER'; ob.data.size = 0.24; ob.data.extrude = 0.01
        bpy.ops.object.convert(target='MESH')
        mt = Matrix(((0, 1, 0), (0, 0, 1), (1, 0, 0))).transposed().to_4x4(); mt.translation = Vector((x1 + 0.06, yf(0.495), z))
        ob.matrix_world = mt
        ob.data.materials.clear(); ob.data.materials.append(M['sign_white'])
    # top-level open balcony on the left with a netted rail (g22)
    faces_obj([[(x1 + 0.01, yf(0.08), 7.75), (x1 + 0.01, yf(0.38), 7.75), (x1 + 0.01, yf(0.38), 9.8), (x1 + 0.01, yf(0.08), 9.8)]], 'media_balcony_void', 'dark')
    faces_obj([[(x1 + 0.9, yf(0.06), 7.9), (x1 + 0.9, yf(0.39), 7.9), (x1 + 0.9, yf(0.39), 8.9), (x1 + 0.9, yf(0.06), 8.9)]], 'media_balcony_net', 'chain_see')
    cyl((x1 + 0.9, yf(0.06), 8.9), (x1 + 0.9, yf(0.39), 8.9), 0.03, 'media_balcony_rail', 'galv', 8)
    # green corner posts and eave band
    for k, y in enumerate((y0, y1)):
        prism(rect(x1 - 0.05, x1 + 0.2, y - 0.12, y + 0.12), 0, 10.0, f'media_post_{k}', 'green')
    faces_obj([[(x1 + 0.03, y0, 9.85), (x1 + 0.03, y1, 9.85), (x1 + 0.03, y1, 10.0), (x1 + 0.03, y0, 10.0)]], 'media_eave_band', 'green')
    # twin gables (apex 1.9 m above the eave, g22) with white bargeboards and finials
    for k, (ya, yb) in enumerate(((y0, (y0 + y1) / 2), ((y0 + y1) / 2, y1))):
        ym = (ya + yb) / 2
        faces_obj([[(x0 - 0.3, ya - 0.2, 9.85), (x1 + 0.4, ya - 0.2, 9.85), (x1 + 0.4, ym, 11.9), (x0 - 0.3, ym, 11.9)],
                   [(x0 - 0.3, ym, 11.9), (x1 + 0.4, ym, 11.9), (x1 + 0.4, yb + 0.2, 9.85), (x0 - 0.3, yb + 0.2, 9.85)]], f'media_roof_{k}', 'roof_zinc_x')
        faces_obj([[(x1 + 0.02, ya, 10), (x1 + 0.02, yb, 10), (x1 + 0.02, ym, 11.75)]], f'media_gable_{k}', 'cream_boards')
        faces_obj([[(x0 - 0.02, yb, 10), (x0 - 0.02, ya, 10), (x0 - 0.02, ym, 11.75)]], f'media_gable_back_{k}', 'cream_boards')
        faces_obj([[(x1 + 0.42, ya - 0.2, 9.75), (x1 + 0.42, ym, 11.8), (x1 + 0.42, ym, 12.0), (x1 + 0.42, ya - 0.2, 9.95)],
                   [(x1 + 0.42, ym, 11.8), (x1 + 0.42, yb + 0.2, 9.75), (x1 + 0.42, yb + 0.2, 9.95), (x1 + 0.42, ym, 12.0)]], f'media_barge_{k}', 'white')
        cyl((x1 + 0.42, ym, 11.9), (x1 + 0.42, ym, 12.9), 0.05, f'media_finial_{k}', 'white', 8)
    # LED screen on the street side (g13): dark frame, nearly full width, from 3 m up to the eave
    prism(rect(x0 - 0.45, x0, y0 + 0.2, y1 - 0.2), 3.0, 10.3, 'media_screen_frame', 'black')
    faces_obj([[(x0 - 0.46, y1 - 0.4, 3.2), (x0 - 0.46, y0 + 0.4, 3.2), (x0 - 0.46, y0 + 0.4, 10.1), (x0 - 0.46, y1 - 0.4, 10.1)]], 'media_screen', 'screen')

    griff_john()
    # toilet block (OSM 292154260)
    tw = way('292154260'); prism(tw, 0, 3.4, 'toilets', 'limestone')
    M.setdefault('roof_green', corrugated('roof_green', (0.27, 0.40, 0.29), axis=1, metal=0.2, rough=0.5))
    q0, q1, q2, q3 = [Vector(v) for v in tw[:4]]
    if (q1 - q0).length < (q2 - q1).length: q0, q1, q2, q3 = q1, q2, q3, q0
    ld = (q1 - q0).normalized(); hw = (q2 - q1).length / 2; zt, zrr = 3.4, 3.4 + 1.6
    ra = (q0 + q3) / 2 + ld * hw; rb = (q1 + q2) / 2 - ld * hw
    V3 = lambda v, z: (v.x, v.y, z)
    faces_obj([[V3(q0, zt), V3(q1, zt), V3(rb, zrr), V3(ra, zrr)], [V3(q2, zt), V3(q3, zt), V3(ra, zrr), V3(rb, zrr)],
               [V3(q1, zt), V3(q2, zt), V3(rb, zrr)], [V3(q3, zt), V3(q0, zt), V3(ra, zrr)]], 'toilets_roof', 'roof_green')
    # boundary wall 3 m (OSM 225638069), limestone
    bw = [tuple(p) for p in G['ways']['225638069']]
    q = []
    for k_, (a, b) in enumerate(zip(bw[:-1], bw[1:])):
        spans = [(0.0, 0.616), (0.736, 1.0)] if k_ == len(bw) - 2 else [(0.0, 1.0)]
        for t0, t1 in spans:
            A = (a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0); B = (a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
            q.append([(A[0], A[1], 0), (B[0], B[1], 0), (B[0], B[1], 3.0), (A[0], A[1], 3.0)])
    faces_obj(q, 'boundary_wall', 'limestone')
    # retaining walls north
    # the north side is cut into the hill: a04 puts the wall tops at 7-10 m behind the north stand (ray meets the
    # OSM wall line at u 2920-3375); the west end is hidden by the fig and meets the 3 m street wall
    WALL_Z = {'225638065': [8.9, 6.85, 7.25, 7.8], '225638067': [8.3, 6.55, 6.0, 3.5, 3.0]}
    for k, zs in WALL_Z.items():
        w = [tuple(p) for p in G['ways'][k]]
        q = [[(a[0], a[1], 0), (b[0], b[1], 0), (b[0], b[1], zb), (a[0], a[1], za)]
             for a, b, za, zb in zip(w[:-1], w[1:], zs[:-1], zs[1:])]
        q += [[(a[0], a[1], za), (b[0], b[1], zb), (b[0], b[1], zb + 0.25), (a[0], a[1], za + 0.25)]
              for a, b, za, zb in zip(w[:-1], w[1:], zs[:-1], zs[1:])]
        faces_obj(q, f'retain_{k}', 'limestone')
    # path ramp down the face of wall 065 (a04 u 3110-3400 v 1850-1895: white rails about 5-6 m up, a limestone
    # parapet under them); surface 2.5 m wide, rails 1.0 and 0.5 m above it
    A_ = np.array(G['ways']['225638065'][0]); B_ = np.array(G['ways']['225638065'][1]); dv = B_ - A_
    nv = np.array([-dv[1], dv[0]]) / np.linalg.norm(dv)
    if np.dot(nv, -A_) < 0: nv = -nv
    def rz(t):
        return 4.2 + (t - 0.89) * (4.8 - 4.2) / (0.78 - 0.89) if t > 0.78 else 4.8 + (t - 0.78) * (4.8 - 3.8) / (0.78 - 0.26)
    ts = [0.0, 0.26, 0.55, 0.78, 0.89]
    def wp(t, o): return tuple(A_ + dv * t + nv * o)
    deck = []; face = []; rails = []
    for t0, t1 in zip(ts[:-1], ts[1:]):
        z0, z1 = rz(t0), rz(t1)
        deck.append([(*wp(t0, 0.0), z0), (*wp(t1, 0.0), z1), (*wp(t1, 2.5), z1), (*wp(t0, 2.5), z0)])
        face.append([(*wp(t0, 2.5), 0.0), (*wp(t1, 2.5), 0.0), (*wp(t1, 2.5), z1), (*wp(t0, 2.5), z0)])
        for h in (1.0, 0.5):
            rails.append([(*wp(t0, 2.4), z0 + h), (*wp(t1, 2.4), z1 + h), (*wp(t1, 2.4), z1 + h + 0.06), (*wp(t0, 2.4), z0 + h + 0.06)])
    faces_obj(deck, 'wall_ramp_deck', 'concrete')
    faces_obj(face, 'wall_ramp_face', 'limestone')
    faces_obj(rails, 'wall_ramp_rails', 'white')
    for k, t in enumerate(np.arange(0.0, 0.89, 0.05)):
        x, y = wp(t, 2.4); z = rz(t)
        cyl((x, y, z), (x, y, z + 1.06), 0.03, f'wall_ramp_post_{k}', 'white', 6)

# ---------------------------------------------------------------- Griff John Pavilion (SFFC clubrooms + members' stand)
# Plan: OSM 48745873 + the 2025-12 satellite rectified onto the pavilion's own axes (u along the front, toward the
# SE end; v toward the oval). Heights: g23 (2019) read with the 1.0 m balustrade and the 1.07 m wheelie bin as scales
# (estimates). Layout of the stand: a02 (2020), g05 (2025), g11 (2021); NW entrance: g12 (2021).
GJ_U = (0.65481635, -0.75578803); GJ_V = (0.75578803, 0.65481635); GJ_O = (-83.0, -37.3)
GJ_DECK = 1.35          # members' deck level (top of the 6 terrace steps)
GJ_FASCIA = (5.9, 7.3)  # white fascia band, bottom and top at the front edge (v 0)
GJ_ROOF_BACK = 8.4      # front roof top at its back edge (v -12.5); monopitch rising away from the oval
GJ_SOFFIT_BACK = 8.0

def GJ(u, v, z=0.0):
    return (GJ_O[0] + u * GJ_U[0] + v * GJ_V[0], GJ_O[1] + u * GJ_U[1] + v * GJ_V[1], z)

def gj_box(u0, u1, v0, v1, z0, z1, name, mat, top=True):
    return prism([GJ(u0, v0)[:2], GJ(u1, v0)[:2], GJ(u1, v1)[:2], GJ(u0, v1)[:2]], z0, z1, name, mat, top)

def gj_wall_u(u0, u1, v, z0, z1):   # vertical face along u at constant v
    return [GJ(u0, v, z0), GJ(u1, v, z0), GJ(u1, v, z1), GJ(u0, v, z1)]

def gj_wall_v(u, v0, v1, z0, z1):   # vertical face along v at constant u
    return [GJ(u, v0, z0), GJ(u, v1, z0), GJ(u, v1, z1), GJ(u, v0, z1)]

def gj_text(txt, u_c, v, z_c, size, mat, name, facing=1, width=None):
    # modelled lettering on a face of constant v; facing=1 reads from the oval (left = SE end), -1 from behind
    import math as _m
    bpy.ops.object.text_add(location=(0, 0, 0))
    ob = bpy.context.object; ob.name = name
    ob.data.body = txt; ob.data.font = GJ_FONT
    ob.data.align_x = 'CENTER'; ob.data.align_y = 'CENTER'; ob.data.size = size; ob.data.extrude = 0.02
    if width:
        for _ in range(5):
            bpy.context.view_layer.update()
            w0 = ob.dimensions.x
            if w0 <= 0: break
            ob.data.space_character *= 1.0 + (width / w0 - 1.0) * 1.15
    bpy.ops.object.convert(target='MESH')
    X = Vector((-GJ_U[0] * facing, -GJ_U[1] * facing, 0)); Y = Vector((0, 0, 1)); Zn = Vector((GJ_V[0] * facing, GJ_V[1] * facing, 0))
    mt = Matrix((X, Y, Zn)).transposed().to_4x4(); mt.translation = Vector(GJ(u_c, v, z_c))
    ob.matrix_world = mt
    ob.data.materials.clear(); ob.data.materials.append(M[mat])
    print('GJTEXT', name, round(ob.dimensions.x, 2), round(ob.dimensions.y, 2))
    return ob

def gj_text_u(txt, u, v_c, z_c, size, mat, name):
    # lettering on a face of constant u (the NW end), read from the NW
    bpy.ops.object.text_add(location=(0, 0, 0))
    ob = bpy.context.object; ob.name = name
    ob.data.body = txt; ob.data.font = GJ_FONT
    ob.data.align_x = 'CENTER'; ob.data.align_y = 'CENTER'; ob.data.size = size; ob.data.extrude = 0.02
    bpy.ops.object.convert(target='MESH')
    X = Vector((GJ_V[0], GJ_V[1], 0)) * -1; Y = Vector((0, 0, 1)); Zn = Vector((-GJ_U[0], -GJ_U[1], 0))
    mt = Matrix((X, Y, Zn)).transposed().to_4x4(); mt.translation = Vector(GJ(u, v_c, z_c))
    ob.matrix_world = mt
    ob.data.materials.clear(); ob.data.materials.append(M[mat])
    return ob

def gj_disc(u, v, z, r, name, mat, seg=28, face='v', flip=1):
    import math as _m
    if face == 'v':
        pts = [GJ(u + r * _m.cos(2 * _m.pi * k / seg), v, z + r * _m.sin(2 * _m.pi * k / seg)) for k in range(seg)]
    else:
        pts = [GJ(u, v + r * _m.cos(2 * _m.pi * k / seg), z + r * _m.sin(2 * _m.pi * k / seg)) for k in range(seg)]
    return faces_obj([pts], name, mat)

def gj_badge(u, v, z, r, face, red='red'):
    # club badge, simplified by hand: white disc, red ring, red V, grey bulldog head (ears up)
    import math as _m
    n = f'gj_badge_{face}{abs(u):.0f}'
    if face == 'v':
        P = lambda a, b, d: GJ(u - a, v + d, z + b)
    else:
        P = lambda a, b, d: GJ(u - d, v + a, z + b)
    ring = lambda rr, d: [P(rr * _m.cos(2 * _m.pi * i / 32), rr * _m.sin(2 * _m.pi * i / 32), d) for i in range(32)]
    faces_obj([ring(r, 0.0)], n + '_ring', red)
    faces_obj([ring(r * 0.86, 0.015)], n + '_disc', 'sign_white')
    w = r * 0.62; t = r * 0.16
    faces_obj([[P(-w, r * 0.45, 0.03), P(-w + t * 1.4, r * 0.45, 0.03), P(0, -r * 0.35, 0.03), P(0, -r * 0.62, 0.03)],
               [P(w - t * 1.4, r * 0.45, 0.03), P(w, r * 0.45, 0.03), P(0, -r * 0.62, 0.03), P(0, -r * 0.35, 0.03)]], n + '_v', red)
    hd = [P(r * 0.30 * _m.cos(2 * _m.pi * i / 20), -r * 0.05 + r * 0.26 * _m.sin(2 * _m.pi * i / 20), 0.045) for i in range(20)]
    faces_obj([hd, [P(-r * 0.30, r * 0.12, 0.045), P(-r * 0.12, r * 0.18, 0.045), P(-r * 0.26, r * 0.36, 0.045)],
               [P(r * 0.12, r * 0.18, 0.045), P(r * 0.30, r * 0.12, 0.045), P(r * 0.26, r * 0.36, 0.045)]], n + '_head', 'mid_grey')

def chair_q(c, f, z, w=0.40, d=0.40, h=0.42, hb=0.40):
    # one empty moulded seat on a tread: pan, raked back and a front skirt; c = pan centre (x, y), f = unit vector
    # toward the field, z = tread top. Neighbours are placed with a gap, so each seat reads on its own.
    c = np.array(c[:2], float); f = np.array(f[:2], float); f = f / np.linalg.norm(f); sd = np.array([-f[1], f[0]])
    P = lambda a, b, zz: (*(c + f * a + sd * b), zz)
    hw = w / 2
    return [[P(d / 2, -hw, z + h), P(d / 2, hw, z + h), P(-d / 2, hw, z + h), P(-d / 2, -hw, z + h)],
            [P(-d / 2, -hw, z + h), P(-d / 2, hw, z + h), P(-d / 2 - 0.08, hw, z + h + hb), P(-d / 2 - 0.08, -hw, z + h + hb)],
            [P(d / 2 - 0.02, -hw + 0.02, z), P(d / 2 - 0.02, hw - 0.02, z), P(d / 2 - 0.02, hw - 0.02, z + h), P(d / 2 - 0.02, -hw + 0.02, z + h)]]

def griff_john():
    global GJ_FONT
    import math as _m
    try:
        GJ_FONT = bpy.data.fonts.load('C:/Windows/Fonts/arialbd.ttf')
    except Exception:
        GJ_FONT = bpy.data.fonts[0] if bpy.data.fonts else None
    D = GJ_DECK
    # --- six concrete terrace steps in front of the members' deck (OSM bump u 10.7-46.4, v 0-4.3)
    for k in range(6):
        vf = 4.3 - k * 4.3 / 6.0
        gj_box(10.7, 41.5, -0.3, vf, 0.0, (k + 1) * D / 6.0, f'gj_step_{k}', 'concrete')
    # white-painted brick plant enclosure at the SE end of the steps (g11, a02), air-conditioners behind it
    gj_box(41.5, 46.4, -0.3, 3.8, 0.0, 1.05, 'gj_enclosure', 'brick_pink')
    for k, uc in enumerate((42.6, 44.2)):
        gj_box(uc - 0.45, uc + 0.45, -0.25, 0.1, D, D + 0.7, f'gj_aircon_front_{k}', 'aircon')
    # chain-wire fence at the foot of the steps: galvanised posts and rails, see-through mesh
    fq = [gj_wall_u(10.7, 41.5, 4.55, 0.05, 1.25)]
    faces_obj(fq, 'gj_fence_mesh', 'chain_see')
    for k, u in enumerate(np.arange(10.7, 41.6, 2.6)):
        cyl(GJ(u, 4.55, 0), GJ(u, 4.55, 1.3), 0.03, f'gj_fence_post_{k}', 'galv', 8)
    for k, z in enumerate((1.28, 0.08)):
        cyl(GJ(10.7, 4.55, z), GJ(41.5, 4.55, z), 0.025, f'gj_fence_rail_{k}', 'galv', 8)
    # NW end of the deck front (no steps): white render to deck level
    gj_box(0.0, 10.7, -0.3, 0.0, 0.0, D, 'gj_front_nw', 'render_white')
    # --- members' deck: seven raked tiers under the roof, white plastic chairs (green ones at the front, g05)
    tread, rise_ = 0.85, 0.18
    for i in range(7):
        v0 = -0.3 - tread * i; v1 = v0 - tread
        gj_box(0.0, 46.4, v1, v0, 0.0, D + rise_ * i, f'gj_tier_{i}', 'concrete')
    back_v = -0.3 - tread * 7
    chairs_w, chairs_g = [], []
    for i in range(7):
        zt = D + rise_ * i; vc = -0.3 - tread * i - 0.5
        for u in np.arange(0.6, 45.9, 0.55):
            q = [[GJ(u - 0.22, vc + 0.2, zt + 0.45), GJ(u + 0.22, vc + 0.2, zt + 0.45), GJ(u + 0.22, vc - 0.2, zt + 0.45), GJ(u - 0.22, vc - 0.2, zt + 0.45)],
                 [GJ(u - 0.22, vc - 0.2, zt + 0.45), GJ(u + 0.22, vc - 0.2, zt + 0.45), GJ(u + 0.22, vc - 0.28, zt + 0.88), GJ(u - 0.22, vc - 0.28, zt + 0.88)],
                 [GJ(u - 0.2, vc + 0.18, zt), GJ(u + 0.2, vc + 0.18, zt), GJ(u + 0.2, vc + 0.18, zt + 0.45), GJ(u - 0.2, vc + 0.18, zt + 0.45)]]
            (chairs_g if (i < 2 and 18.0 < u < 30.0) else chairs_w).extend(q)
    faces_obj(chairs_w, 'gj_chairs_white', 'seat_white')
    faces_obj(chairs_g, 'gj_chairs_green', 'seat_green')
    # white corrugated balustrade along the deck front, one aisle gap (g23)
    bq = []
    for ua, ub in ((0.0, 36.4), (37.3, 46.4)):
        bq += [gj_wall_u(ua, ub, -0.12, D, D + 1.0), gj_wall_u(ua, ub, -0.18, D, D + 1.0)[::-1],
               [GJ(ua, -0.12, D + 1.0), GJ(ub, -0.12, D + 1.0), GJ(ub, -0.18, D + 1.0), GJ(ua, -0.18, D + 1.0)]]
    faces_obj(bq, 'gj_balustrade', 'corr_white_h')
    # back of the deck: tinted glazing to the clubrooms
    zb_back = D + rise_ * 6
    faces_obj([gj_wall_u(0.0, 46.4, back_v, zb_back, GJ_SOFFIT_BACK - 0.6)], 'gj_deck_glass', 'glass')
    # --- front roof: monopitch rising away from the oval, cream corrugated top, charcoal soffit, white fascia
    f0, f1 = GJ_FASCIA
    def rtop(v): return f1 + (GJ_ROOF_BACK - f1) * (-v / 12.5)
    def rsof(v): return f0 + (GJ_SOFFIT_BACK - f0) * (-v / 12.5)
    faces_obj([[GJ(0.0, 0.0, rtop(0)), GJ(56.9, 0.0, rtop(0)), GJ(56.9, -12.5, rtop(-12.5)), GJ(0.0, -12.5, rtop(-12.5))]], 'gj_roof_front', 'roof_cream')
    faces_obj([[GJ(0.0, -0.05, rsof(0)), GJ(0.0, -12.5, rsof(-12.5)), GJ(56.9, -12.5, rsof(-12.5)), GJ(56.9, -0.05, rsof(0))]], 'gj_soffit', 'soffit')
    faces_obj([gj_wall_u(0.0, 56.9, 0.0, f0, f1),
               gj_wall_v(0.0, 0.0, -12.5, f0, f1), gj_wall_v(56.9, 0.0, -12.5, f0, f1)], 'gj_fascia', 'sign_white')
    faces_obj([[GJ(0.0, 0.0, f0), GJ(0.0, -12.5, rsof(-12.5)), GJ(0.0, -12.5, rtop(-12.5)), GJ(0.0, 0.0, f1)],
               [GJ(56.9, 0.0, f0), GJ(56.9, -12.5, rsof(-12.5)), GJ(56.9, -12.5, rtop(-12.5)), GJ(56.9, 0.0, f1)]], 'gj_roof_ends', 'sign_white')
    # four translucent roof-light strips on the front roof (satellite u 33-52)
    sk = []
    for vv in (-2.2, -5.25, -8.2, -11.2):
        sk.append([GJ(33.0, vv + 0.25, rtop(vv) + 0.06), GJ(52.0, vv + 0.25, rtop(vv) + 0.06),
                   GJ(52.0, vv - 0.25, rtop(vv) + 0.06), GJ(33.0, vv - 0.25, rtop(vv) + 0.06)])
    faces_obj(sk, 'gj_rooflights', 'skylight')
    # steel: rafters under the soffit, columns at the deck front and back
    raf = []
    for u in np.arange(2.0, 56.0, 6.0):
        raf += [[GJ(u - 0.12, -0.3, rsof(-0.3) - 0.35), GJ(u - 0.12, -12.3, rsof(-12.3) - 0.35), GJ(u - 0.12, -12.3, rsof(-12.3)), GJ(u - 0.12, -0.3, rsof(-0.3))],
                [GJ(u + 0.12, -0.3, rsof(-0.3) - 0.35), GJ(u + 0.12, -12.3, rsof(-12.3) - 0.35), GJ(u + 0.12, -12.3, rsof(-12.3)), GJ(u + 0.12, -0.3, rsof(-0.3))],
                [GJ(u - 0.12, -0.3, rsof(-0.3) - 0.35), GJ(u + 0.12, -0.3, rsof(-0.3) - 0.35), GJ(u + 0.12, -12.3, rsof(-12.3) - 0.35), GJ(u - 0.12, -12.3, rsof(-12.3) - 0.35)]]
    faces_obj(raf, 'gj_rafters', 'steel_dark')
    for k, u in enumerate((11.0, 20.0, 29.0, 38.0)):
        gj_box(u - 0.12, u + 0.12, -1.15, -0.9, D + rise_, rsof(-1.0), f'gj_column_{k}', 'steel_dark')
    # lettering: SOUTH FREMANTLE   FOOTBALL CLUB, red on the white fascia, bulldog badge at the SE end
    zc = (f0 + f1) / 2
    # positions read off g34 (2023) through the fitted camera fit/cam_g34g.json: SOUTH FREMANTLE u 41.5-32.5, FOOTBALL CLUB
    # u 31.0-23.0, a badge at each end (u 44.8, 19.7); letter height 0.58 of the band
    gj_text('SOUTH FREMANTLE', 37.0, 0.03, zc - 0.05, 1.3, 'red', 'gj_text_sf', width=9.1)
    gj_text('FOOTBALL CLUB', 27.0, 0.03, zc - 0.05, 1.3, 'red', 'gj_text_fc', width=8.0)
    gj_badge(44.8, 0.03, zc, 0.55, 'v'); gj_badge(19.7, 0.03, zc, 0.55, 'v')
    # --- function room at the SE end (OSM front v -0.5, u 46.4-56.9): painted brick, white render, four glass bays
    gj_box(46.4, 56.9, -12.5, -0.5, 0.0, 1.2, 'gj_fr_brick', 'brick_pink', top=False)
    gj_box(46.4, 56.9, -12.5, -0.5, 1.2, 2.4, 'gj_fr_render', 'render_white', top=False)
    faces_obj([gj_wall_u(46.4, 56.9, -0.5, 2.4, f0), gj_wall_v(46.4, -0.5, back_v, D + 0.9, f0),
               gj_wall_v(56.9, -0.5, -12.5, 2.4, f0)], 'gj_fr_glass', 'glass')
    mul = []
    for u in np.linspace(46.4, 56.9, 5):
        mul.append([GJ(u - 0.06, -0.47, 2.4), GJ(u + 0.06, -0.47, 2.4), GJ(u + 0.06, -0.47, f0), GJ(u - 0.06, -0.47, f0)])
    mul.append([GJ(46.4, -0.47, 2.36), GJ(56.9, -0.47, 2.36), GJ(56.9, -0.47, 2.48), GJ(46.4, -0.47, 2.48)])
    faces_obj(mul, 'gj_fr_mullions', 'silver')
    # downpipe at the corner (g11)
    cyl(GJ(46.2, -0.35, 0.0), GJ(46.2, -0.35, f0), 0.06, 'gj_downpipe', 'white', 8)
    # --- SE block (OSM u 56.9-64.9, v -6.9 to -32.9): single storey, white render on a painted brick base
    gj_box(56.9, 64.9, -32.9, -6.9, 0.0, 1.0, 'gj_se_base', 'brick_pink', top=False)
    gj_box(56.9, 64.9, -32.9, -6.9, 1.0, 4.2, 'gj_se_walls', 'render_white', top=False)
    gj_box(56.6, 65.2, -33.2, -6.6, 4.2, 4.45, 'gj_se_roof', 'roof_white')
    # --- clubrooms behind the stand: three roof levels (satellite edges v -12.5 and -19.5, u 28.8)
    gj_box(28.8, 56.9, -35.0, -12.5, 0.0, 1.0, 'gj_rear_e_base', 'brick_pink', top=False)
    gj_box(28.8, 56.9, -35.0, -12.5, 1.0, 9.0, 'gj_rear_e_walls', 'render_white', top=False)
    gj_box(28.6, 57.1, -35.2, -12.3, 9.0, 9.2, 'gj_rear_e_roof', 'roof_cream')
    gj_box(0.4, 28.8, -19.5, -12.5, 0.0, 8.8, 'gj_rear_m_walls', 'render_white', top=False)
    gj_box(0.2, 28.8, -19.7, -12.3, 8.8, 9.0, 'gj_rear_m_roof', 'roof_cream')
    gj_box(0.4, 28.8, -31.1, -19.5, 0.0, 1.0, 'gj_rear_w_base', 'brick_pink', top=False)
    gj_box(0.4, 28.8, -31.1, -19.5, 1.0, 7.6, 'gj_rear_w_walls', 'render_white', top=False)
    gj_box(0.2, 29.0, -31.3, -19.5, 7.6, 7.8, 'gj_rear_w_roof', 'roof_cream')
    # solar strips (satellite): six flat on the low west roof, two tilted on the east roof
    sol = []
    for ua, ub in ((0.7, 2.3), (4.2, 5.8), (7.9, 9.6), (11.3, 12.9), (22.2, 23.8), (25.7, 27.3)):
        sol.append([GJ(ua, -20.5, 7.9), GJ(ub, -20.5, 7.9), GJ(ub, -29.3, 7.9), GJ(ua, -29.3, 7.9)])
    for ua, ub in ((42.3, 44.0), (45.7, 47.3)):
        sol.append([GJ(ua, -13.4, 9.3), GJ(ub, -13.4, 9.75), GJ(ub, -24.7, 9.75), GJ(ua, -24.7, 9.3)])
    faces_obj(sol, 'gj_solar', 'solar')
    for k, (u, v) in enumerate(((6.0, -14.5), (16.0, -14.5), (24.0, -14.5), (34.0, -27.0), (50.0, -28.0), (38.0, -14.0))):
        zr = 9.0 if u < 28.8 else 9.2
        gj_box(u - 0.5, u + 0.5, v - 0.4, v + 0.4, zr, zr + 0.8, f'gj_roof_aircon_{k}', 'aircon')
    # --- NW entrance (g12): glazed lobby under a flat canopy, twin white gables over the doors, BULLDOGS mural wall
    gj_box(-6.0, 0.0, -11.9, -1.0, 4.9, 5.2, 'gj_canopy', 'roof_white')
    for k, v in enumerate((-1.3, -4.6, -8.0, -11.6)):
        cyl(GJ(-5.7, v, 0.0), GJ(-5.7, v, 4.9), 0.08, f'gj_canopy_post_{k}', 'silver', 10)
    faces_obj([gj_wall_v(0.0, -1.0, -11.9, 0.0, 4.9)], 'gj_lobby_glass', 'glass_green')
    for g in range(2):
        va, vb = -11.9 - 3.85 * g, -11.9 - 3.85 * (g + 1); vm = (va + vb) / 2
        gj_box(-0.8, 6.0, vb, va, 0.0, 5.2, f'gj_gable_walls_{g}', 'render_white', top=False)
        faces_obj([[GJ(-2.4, va, 5.2), GJ(-2.4, vm, 7.2), GJ(6.0, vm, 7.2), GJ(6.0, va, 5.2)],
                   [GJ(-2.4, vm, 7.2), GJ(-2.4, vb, 5.2), GJ(6.0, vb, 5.2), GJ(6.0, vm, 7.2)]], f'gj_gable_roof_{g}', 'roof_white')
        faces_obj([[GJ(-0.81, va, 5.2), GJ(-0.81, vb, 5.2), GJ(-0.81, vm, 7.2)]], f'gj_gable_face_{g}', 'render_white')
        tr = []
        for (a_, za), (b_, zb) in (((va, 5.2), (vm, 7.2)), ((vm, 7.2), (vb, 5.2))):
            tr.append([GJ(-2.42, a_, za - 0.22), GJ(-2.42, b_, zb - 0.22), GJ(-2.42, b_, zb + 0.05), GJ(-2.42, a_, za + 0.05)])
            tr.append([GJ(-2.42, a_, za + 0.05), GJ(-2.42, b_, zb + 0.05), GJ(-1.9, b_, zb + 0.05), GJ(-1.9, a_, za + 0.05)])
        faces_obj(tr, f'gj_gable_trim_{g}', 'mid_grey')
    for k, v in enumerate((-12.0, -15.75, -19.5)):
        cyl(GJ(-2.2, v, 0.0), GJ(-2.2, v, 5.2), 0.09, f'gj_porch_post_{k}', 'silver', 10)
    gj_box(-2.6, -1.8, -12.4, -11.6, 0.0, 1.0, 'gj_porch_plinth', 'render_white')
    faces_obj([gj_wall_v(-0.82, -12.4, -15.3, 1.0, 3.6)], 'gj_entry_doors', 'glass')
    for k in range(5):
        gj_box(-3.3 + 0.5 * k, -0.8, -16.5, -12.4, 0.0, 0.2 * (k + 1), f'gj_entry_step_{k}', 'step_dark')
    gj_box(-1.0, -0.82, -17.6, -16.9, 0.0, 3.3, 'gj_porch_red', 'mural_red')
    # BULLDOGS mural wall (hand-made): white panel with an arched top and grey edge, red arched lettering,
    # round club badge on grey, two portrait panels left as plain grey (photo portraits not reproduced)
    va, vb = -19.6, -26.5; vc = (va + vb) / 2; R = (va - vb) / 2; zs = 5.0
    gj_box(-2.3, 0.4, vb, va, 0.0, zs, 'gj_mural_wall', 'render_white')
    arch = [GJ(-2.31, va, zs)] + [GJ(-2.31, vc + R * _m.cos(_m.pi * k / 24), zs + 1.1 * _m.sin(_m.pi * k / 24)) for k in range(25)] + [GJ(-2.31, vb, zs)]
    faces_obj([arch[::-1]], 'gj_mural_arch', 'render_white')
    edge = []
    for k in range(24):
        a0, a1 = _m.pi * k / 24, _m.pi * (k + 1) / 24
        edge.append([GJ(-2.33, vc + R * _m.cos(a0), zs + 1.1 * _m.sin(a0)), GJ(-2.33, vc + R * _m.cos(a1), zs + 1.1 * _m.sin(a1)),
                     GJ(-2.33, vc + (R - 0.12) * _m.cos(a1), zs + 0.98 * _m.sin(a1)), GJ(-2.33, vc + (R - 0.12) * _m.cos(a0), zs + 0.98 * _m.sin(a0))])
    faces_obj(edge, 'gj_mural_edge', 'mid_grey')
    for i, ch in enumerate('BULLDOGS'):
        th = _m.pi * (i - 3.5) / 8
        ob = gj_text_u(ch, -2.34, vc - (i - 3.5) * 0.74, zs - 0.35 + 0.35 * _m.cos(th), 1.3, 'mural_red', f'gj_mural_l{i}')
        ob.matrix_world = ob.matrix_world @ Matrix.Rotation(_m.atan(-0.35 * _m.pi / 8 * _m.sin(th) / 0.74), 4, 'Z')
    disc = [GJ(-2.325, vc + 0.95 * _m.cos(2 * _m.pi * i / 28), 3.55 + 0.95 * _m.sin(2 * _m.pi * i / 28)) for i in range(28)]
    faces_obj([disc], 'gj_mural_badge_bg', 'mid_grey')
    gj_badge(-2.345, vc, 3.55, 0.78, 'u', red='mural_red')
    for k, (v0, v1) in enumerate(((va - 0.35, va - 2.15), (vb + 2.15, vb + 0.35))):
        faces_obj([gj_wall_v(-2.32, v0, v1, 1.0, 4.2)], f'gj_mural_portrait_{k}', 'mid_grey')
    faces_obj([gj_wall_v(-2.325, va - 0.05, va - 0.35, 0.6, 4.6), gj_wall_v(-2.325, vb + 0.35, vb + 0.05, 0.6, 4.6)], 'gj_mural_redband', 'mural_red')

# ---------------------------------------------------------------- light towers
TOWERS = [  # base x, y, head-centre height (from a04 + satellite shadows)
    (84.4, -31.9, 31.0), (55.0, 55.0, 30.0), (-90.1, 48.1, 23.5), (-87.7, -36.4, 23.5)]
def towers():
    for i, (x, y, h) in enumerate(TOWERS):
        cyl((x, y, 0), (x, y, h - 1.8), 0.32, f'tower_pole_{i}', 'galv', 16)
        cyl((x, y, h - 2.5), (x, y, h + 1.5), 0.2, f'tower_mast_{i}', 'galv', 12)
        # head faces the oval centre
        ang = math.atan2(-y, -x)
        ux, uy = -math.sin(ang), math.cos(ang)   # along the head (horizontal, across view)
        fx, fy = math.cos(ang), math.sin(ang)
        for r in range(3):
            z = h - 1.2 + r * 1.2
            a = (x - ux * 2.6 + fx * 0.4, y - uy * 2.6 + fy * 0.4, z)
            b = (x + ux * 2.6 + fx * 0.4, y + uy * 2.6 + fy * 0.4, z)
            cyl(a, b, 0.06, f'tower_bar_{i}_{r}', 'galv', 8)
            for c in range(4):
                t = -1.95 + c * 1.3
                px, py = x + ux * t + fx * 0.7, y + uy * t + fy * 0.7
                bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=0.42, depth=0.35, location=(px, py, z))
                ob = bpy.context.object; ob.name = f'tower_lamp_{i}_{r}_{c}'
                ob.rotation_euler = Vector((fx, fy, -0.35)).to_track_quat('Z', 'Y').to_euler()
                ob.data.materials.append(M['galv']); ob.data.materials.append(M['lamp'])

# ---------------------------------------------------------------- trees (satellite canopies + a04 heights)
TREES = [  # x, y, canopy radius, height, kind
    (-63.0, 94.0, 18.0, 23.0, 'fig', 2.5),
    (35.5, 142.0, 15.0, 17.0, 'fig'), (68.5, 142.0, 15.0, 17.0, 'fig'), (87.5, 147.0, 7.5, 11.0, 'fig'),
    (36.0, 86.0, 16.0, 29.0, 'fig'), (12.0, 114.0, 11.0, 20.0, 'fig'), (48.0, 112.0, 13.0, 24.0, 'fig'),
    (66.0, 84.9, 16.0, 18.0, 'fig'), (73.6, 65.9, 17.0, 18.0, 'fig'),
    (85.0, 27.8, 5.5, 11.0, 'fig'), (87.5, -7.7, 5.0, 18.5, 'fig'),
    (87.5, -23.0, 7.0, 22.5, 'fig'), (85.0, -40.7, 7.5, 12.0, 'fig'), (90.0, -53.0, 7.0, 12.0, 'fig'),
    (81.5, -29.0, 6.0, 21.5, 'fig'), (82.0, -16.0, 4.5, 20.5, 'fig'), (81.5, -7.0, 3.5, 16.5, 'fig'),
    (67.2, -83.9, 10.0, 14.0, 'fig'), (91.3, -81.3, 11.0, 15.0, 'fig'), (82.5, -97.8, 9.0, 13.0, 'fig'),
    (45.7, -113.0, 4.6, 8.0, 'fig'),
    (-130.7, -30.6, 6.4, 9.0, 'fig'),
    (-123.0, -105.0, 4.5, 8.0, 'fig'), (-115.5, -114.0, 4.5, 8.0, 'fig'), (-108.7, -123.0, 4.5, 8.0, 'fig'),
    (86.3, 10.0, 4.5, 11.0, 'fig'),
    (-109.3, 73.0, 6.2, 24.5, 'npine'), (-104.0, 97.0, 2.6, 13.0, 'pine'),
]
def trees():
    rng = np.random.default_rng(7)
    for i, tr_ in enumerate(TREES):
        x, y, r, h, kind = tr_[:5]
        if kind == 'fig':
            trunk_h = tr_[5] if len(tr_) > 5 else h * 0.35
            cyl((x, y, 0), (x, y, trunk_h + 1.0), max(0.3, r * 0.06), f'tree_trunk_{i}', 'bark', 10)
            n = int(10 + r * 1.6); lumps = []
            for k in range(n):
                a = rng.uniform(0, 2 * math.pi); d = rng.uniform(0, r * 0.7) ** 1.0
                zz = trunk_h + (h - trunk_h) * (0.25 + 0.55 * rng.uniform()) * (1 - 0.35 * d / r)
                rr = r * rng.uniform(0.28, 0.45); sz = rng.uniform(0.55, 0.8)
                lumps.append((a, d, zz, rr, sz))
            top = max(zz + rr * sz * 1.15 for a, d, zz, rr, sz in lumps)
            st_ = (h - trunk_h) / max(top - trunk_h, 0.1)
            for k, (a, d, zz, rr, sz) in enumerate(lumps):
                zz = trunk_h + (zz - trunk_h) * st_
                bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rr, location=(x + d * math.cos(a), y + d * math.sin(a), zz))
                ob = bpy.context.object; ob.name = f'tree_{i}_{k}'
                ob.scale = (1, 1, sz)
                ob.data.materials.append(M['fig'])
                tex = bpy.data.textures.new(f'tx_{i}_{k}', 'CLOUDS'); tex.noise_scale = rr * 0.35
                dm = ob.modifiers.new('d', 'DISPLACE'); dm.texture = tex; dm.strength = rr * 0.35
        elif kind == 'npine':   # Norfolk Island pine: a broad column of branch tiers, rounded over the top 25%
            cyl((x, y, 0), (x, y, h), 0.45, f'pine_trunk_{i}', 'bark', 10)
            z0 = 2.0; tiers = int((h - z0) / 1.0)
            for k in range(tiers):
                z = z0 + k * (h - z0) / tiers; fr = (z - z0) / (h - z0)
                rr = r * min(1.0, ((1 - fr) / 0.24) ** 0.5) + 0.3
                bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=rr, radius2=rr * 0.55, depth=0.9, location=(x, y, z),
                                                rotation=(0, 0, k * 0.7))
                ob = bpy.context.object; ob.name = f'pine_{i}_{k}'
                ob.data.materials.append(M['pine'])
        else:
            cyl((x, y, 0), (x, y, h), 0.35, f'pine_trunk_{i}', 'bark', 10)
            tiers = int(h / 1.4)
            for k in range(tiers):
                z = h * 0.25 + k * (h * 0.75 / tiers)
                rr = r * (1 - (z - h * 0.25) / (h * 0.8)) + 0.4
                bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=rr, radius2=rr * 0.3, depth=0.8, location=(x, y, z))
                ob = bpy.context.object; ob.name = f'pine_{i}_{k}'
                ob.data.materials.append(M['pine'])


# ---------------------------------------------------------------- north perimeter boards (a04 u 2500-3400)
def north_boards():
    for nm, col in (('bd_black', (0.02, 0.02, 0.025)), ('bd_wa', (0.04, 0.22, 0.58)), ('bd_navy', (0.03, 0.06, 0.20)),
                    ('bd_pale', (0.80, 0.83, 0.86)), ('bd_paleblue', (0.52, 0.70, 0.84)), ('bd_lightblue', (0.45, 0.68, 0.90)),
                    ('bd_pink', (0.85, 0.55, 0.70))):
        M[nm] = flat(nm, col, 0.5)
    fb = np.array(off(1.0)); dense = []
    for i in range(160, 206):
        a, b = fb[i], fb[i + 1]
        for t in np.linspace(0, 1, 40, endpoint=False): dense.append(a + (b - a) * t)
    dense = np.array(dense)
    def near(x, y): return int(np.argmin(np.hypot(dense[:, 0] - x, dense[:, 1] - y)))
    # (start xy, end xy, colour, text, text colour, text size)
    B = [((-43.74, 86.12), (-43.13, 86.55), 'bd_paleblue', None, None, 0),
         ((-43.13, 86.55), (-38.80, 89.12), 'maroon', 'Community Bank Fremantle', 'bd_lightblue', 0.42),
         ((-38.80, 89.12), (-36.18, 90.42), 'bd_paleblue', 'Bendigo Bank', 'bd_navy', 0.42),
         ((-36.18, 90.42), (-31.98, 92.16), 'maroon', 'Community Bank Fremantle', 'bd_lightblue', 0.42),
         ((-31.98, 92.16), (-26.81, 93.76), 'bd_black', 'HS  HOMESTYLE salads', 'bd_pale', 0.45),
         ((-26.81, 93.76), (-24.63, 94.28), 'bd_black', 'HS  EST. 1987', 'bd_pale', 0.30),
         ((-24.63, 94.28), (-20.70, 94.95), 'bd_wa', 'The West Australian', 'bd_pale', 0.42),
         ((-20.70, 94.95), (-18.97, 95.15), 'bd_black', 'ISC', 'sign_white', 0.50),
         ((-18.97, 95.15), (-17.47, 95.29), 'bd_black', 'ISC', 'sign_white', 0.50),
         ((-17.47, 95.29), (-15.92, 95.35), 'bd_black', 'ISC', 'sign_white', 0.50),
         ((-15.92, 95.35), (-8.13, 94.97), 'bd_navy', 'LIFESPAN MORTGAGE SERVICES', 'bd_lightblue', 0.48),
         ((-8.13, 94.97), (-4.20, 94.26), 'sign_white', 'HOLDFAST', 'bd_navy', 0.55),
         ((-4.20, 94.26), (-1.00, 93.45), 'bd_paleblue', None, None, 0),
         ((-1.00, 93.45), (8.54, 89.78), 'bd_pale', None, None, 0),
         ((8.54, 89.78), (12.63, 87.64), 'maroon', None, None, 0)]
    for n_, (a, b, mat, txt, tmat, size) in enumerate(B):
        i0, i1 = near(*a), near(*b)
        pts = dense[i0:i1 + 1] if i0 <= i1 else dense[i1:i0 + 1][::-1]   # contour runs east to west here
        q = [[(*pts[k], 0), (*pts[k + 1], 0), (*pts[k + 1], 0.9), (*pts[k], 0.9)] for k in range(len(pts) - 1)]
        faces_obj(q, f'nboard_{n_}', mat)
        if not txt: continue
        A, Bp = pts[0], pts[-1]; dx, dy = Bp[0] - A[0], Bp[1] - A[1]; L = math.hypot(dx, dy)
        bpy.ops.object.text_add(location=(0, 0, 0))
        ob = bpy.context.object; ob.name = f'nboard_txt_{n_}'
        ob.data.body = txt; ob.data.align_x = 'CENTER'; ob.data.align_y = 'CENTER'
        ob.data.size = size; ob.data.extrude = 0.005
        bpy.ops.object.convert(target='MESH')
        if ob.dimensions.x > L * 0.92: s_ = L * 0.92 / ob.dimensions.x; ob.scale = (s_, s_, 1)
        nx, ny = dy / L, -dx / L
        ob.location = ((A[0] + Bp[0]) / 2 + nx * 0.08, (A[1] + Bp[1]) / 2 + ny * 0.08, 0.45)
        ob.rotation_euler = (Matrix.Rotation(math.atan2(dy, dx), 4, 'Z') @ Matrix.Rotation(math.pi / 2, 4, 'X')).to_euler()
        ob.data.materials.clear(); ob.data.materials.append(M[tmat])

# ---------------------------------------------------------------- build

# ---------------------------------------------------------------- former Dockers HQ (OSM 292154259), south end
# Ruled IN by the lead 2026-11-18 (via the secretary). Read from g18 (2019, from the field), g34 (2023, frontal from
# the north) and a02 (2020 drone): a sawtooth row of eight steep gables plus one wide entrance gable along the curved
# front. Gables 1-4 (east) are the single tall glass hall; gables 5-8 sit over two storeys (cream render ground floor,
# balcony, glass upper floor); the wide gable is the glass entrance hall with the purple porch at its west end.
# Solar panels on the west slope of gables 2-6 (g18 and g34 agree). Widths from g34 (std gable 125 px, wide 390 px)
# fitted to the OSM front arc; heights from the floor heights (estimates, flagged).
HQ_FRONT = [(31.0, -98.1), (27.3, -98.9), (22.9, -99.3), (17.9, -99.5), (12.2, -99.3), (7.6, -98.9), (2.9, -98.2),
            (-2.8, -97.0), (-7.7, -95.2), (-13.5, -92.9), (-18.0, -90.3), (-21.4, -88.1)]
HQ_ZB = 0.9            # floor on top of the grass bank (g18)
HQ_ZE = HQ_ZB + 7.24   # two-storey eaves (g18 fit)
HQ_RISE = 2.35         # gable rise above the eaves (g34 and a02 fits: apex picks sit on the outer barge edge)
HQ_ZE_LOW = HQ_ZB + 5.38  # glass-hall gables 1-4: eaves (g18 fit)
HQ_RISE_LOW = 1.96
HQ_WIDTHS = [5.79] * 4 + [8.09] + [5.73] * 4   # g18/g34 fit: hall 5.79, first two-storey 8.09, four more at 5.73
HQ_WBIG = 7.0    # entrance section past gable 9: ridge along the front, west-facing gable end (g34 pW fit)
HQ_DBIG = 8.0   # its depth front to back (ridge at half depth)

def hq_at(s):
    pts = HQ_FRONT; acc = 0.0
    for i in range(len(pts) - 1):
        a, b = Vector(pts[i]), Vector(pts[i + 1]); L = (b - a).length
        if s <= acc + L or i == len(pts) - 2:
            t = (s - acc) / L
            p = a + (b - a) * t
            return (p.x, p.y)
        acc += L

def hq():
    M.setdefault('roof_white', corrugated('roof_white', (0.86, 0.86, 0.84), axis=1, metal=0.15, rough=0.5))
    M.setdefault('render_cream', flat('render_cream', (0.78, 0.72, 0.56), 0.7, 0, 2, 0.05))
    M.setdefault('club_purple', flat('club_purple', (0.16, 0.04, 0.32), 0.45))
    M.setdefault('sb_yellow', flat('sb_yellow', (0.75, 0.55, 0.03), 0.45))
    M.setdefault('hq_glass', glass('hq_glass', (0.012, 0.018, 0.016)))   # near-black tinted glazing (g18, g34)
    zb, ZE_HI = HQ_ZB, HQ_ZE
    lowcut = []
    acc_ = [0.0]
    for w_ in HQ_WIDTHS: acc_.append(acc_[-1] + w_)
    spans = [(acc_[k], acc_[k + 1]) for k in range(9)] + [(acc_[9], acc_[9] + HQ_WBIG)]
    roof, sof, barge, glassq, cols, mull, solar, cream, dark, slab, rail, railg, plinth, bank, roofb, sky = ([] for _ in range(16))
    for k, (s0, s1) in enumerate(spans):
        A = Vector(hq_at(s0)); B = Vector(hq_at(s1))
        w = (B - A).length; u = (B - A) / w; n = Vector((-u.y, u.x))   # n points into the building (away from the oval)
        def P(a, d, z): p = A + u * a + n * d; return (p.x, p.y, z)
        big = k == 9
        low = k < 4
        ze = HQ_ZE_LOW if low else ZE_HI
        rise = HQ_RISE_LOW if low else (1.4 if big else HQ_RISE)   # big: the low blue-grey entrance roof (a02)
        depth = HQ_DBIG if big else (13.0 if low else 8.0)
        oh = 1.0                                   # roof overhang in front of the front line
        zr_ = ze + rise; h = w / 2
        zl = HQ_ZE_LOW if k == 4 else ze           # east eave: the first two-storey gable drops to the low eaves (g18)
        if low:
            lowcut.append((P(0, -oh - 0.5, 0)[:2], P(0, depth, 0)[:2]))
            if k == 3: lowcut.append((P(w, -oh - 0.5, 0)[:2], P(w, depth, 0)[:2]))
        if big:
            zr_ = ze + rise; dm = depth / 2
            roofb += [[P(0, -oh, ze), P(w + oh * 0.6, -oh, ze), P(w + oh * 0.6, dm, zr_), P(0, dm, zr_)],
                     [P(0, dm, zr_), P(w + oh * 0.6, dm, zr_), P(w + oh * 0.6, depth, ze), P(0, depth, ze)]]
            sof += [[P(0, -oh, ze - 0.12), P(0, dm, zr_ - 0.12), P(w + oh * 0.6, dm, zr_ - 0.12), P(w + oh * 0.6, -oh, ze - 0.12)],
                    [P(0, dm, zr_ - 0.12), P(0, depth, ze - 0.12), P(w + oh * 0.6, depth, ze - 0.12), P(w + oh * 0.6, dm, zr_ - 0.12)],
                    [P(w, -oh, ze - 0.12), P(w, depth, ze - 0.12), P(w, dm, zr_ - 0.2)],      # white gable infill, west end
                    [P(0, -oh, ze - 0.12), P(0, dm, zr_ - 0.2), P(0, depth, ze - 0.12)]]      # east end, above gable 9's slope
            wb = w + oh * 0.6
            barge += [[P(wb, -oh, ze - 0.3), P(wb, dm, zr_ - 0.3), P(wb, dm, zr_ + 0.02), P(wb, -oh, ze + 0.02)],
                      [P(wb, dm, zr_ - 0.3), P(wb, depth, ze - 0.3), P(wb, depth, ze + 0.02), P(wb, dm, zr_ + 0.02)],
                      [P(0, -oh - 0.02, ze - 0.3), P(wb, -oh - 0.02, ze - 0.3), P(wb, -oh - 0.02, ze + 0.02), P(0, -oh - 0.02, ze + 0.02)]]
        else:
          # roof slopes (white corrugated) and white soffit just under them
          roof += [[P(0, -oh, zl), P(h, -oh, zr_), P(h, depth, zr_), P(0, depth, zl)],
                 [P(h, -oh, zr_), P(w, -oh, ze), P(w, depth, ze), P(h, depth, zr_)]]
          sof += [[P(0, -oh, zl - 0.12), P(0, depth, zl - 0.12), P(h, depth, zr_ - 0.12), P(h, -oh, zr_ - 0.12)],
                [P(h, -oh, zr_ - 0.12), P(h, depth, zr_ - 0.12), P(w, depth, ze - 0.12), P(w, -oh, ze - 0.12)]]
          # white gable infill set back under the open front rake (g18, g34: white triangles, not glass)
          dvi = 0.6
          sof.append([P(0, dvi, zl - 0.12), P(w, dvi, ze - 0.12), P(h, dvi, zr_ - 0.2)])
          if low: sof.append([P(0, depth - 0.05, zl - 0.12), P(h, depth - 0.05, zr_ - 0.2), P(w, depth - 0.05, ze - 0.12)])
          # green bargeboards on the front rake and the back rake
          for dd in (-oh, depth):
            barge += [[P(0, dd, zl - 0.3), P(h, dd, zr_ - 0.3), P(h, dd, zr_ + 0.02), P(0, dd, zl + 0.02)],
                      [P(h, dd, zr_ - 0.3), P(w, dd, ze - 0.3), P(w, dd, ze + 0.02), P(h, dd, zr_ + 0.02)]]
        # green valley columns at the front line, full height to the eaves
        for a in ((0.0, w) if k in (0, 9) else (0.0,)):
            c = A + u * a
            cols.append(((c.x, c.y), zb - 0.4, zl if a == 0.0 else ze))
        # solar panels on the west slope (a h..w) of gables 2-6 (k 1..5): portrait panels in a grid, small gaps
        if 1 <= k <= 5:
            Ls = math.hypot(h, rise)
            for i in range(int((Ls - 0.5) / 1.02)):
                f0 = (0.25 + i * 1.02) / Ls; f1 = f0 + 0.98 / Ls
                for j in range(int((depth - 1.6) / 1.72)):
                    d0 = -oh + 0.5 + j * 1.72; d1 = d0 + 1.68
                    def SP(f, d): return P(h + h * f, d, zr_ - rise * f + 0.05)
                    solar.append([SP(f0, d0), SP(f1, d0), SP(f1, d1), SP(f0, d1)])
        if 4 <= k <= 6:
            Ls = math.hypot(h, rise)
            for j in range(int((depth - 1.6) / 1.72)):
                d0 = -oh + 0.5 + j * 1.72; d1 = d0 + 1.68
                def KP(f, d): return P(h * f, d, zl + (zr_ - zl) * f + 0.04)
                sky.append([KP(0.18, d0), KP(0.82, d0), KP(0.82, d1), KP(0.18, d1)])
        if k < 4 or big:
            dv = 1.0 if big else 0.0                  # the entrance hall glazing sits a metre back
            glassq.append([P(0, dv, zb), P(w, dv, zb), P(w, dv, ze - 0.12), P(0, dv, ze - 0.12)])
            nm = 6 if big else 3
            for i in range(1, nm):
                a = w * i / nm; zt = ze - 0.12
                mull.append([P(a - 0.05, dv - 0.03, zb), P(a + 0.05, dv - 0.03, zb), P(a + 0.05, dv - 0.03, zt), P(a - 0.05, dv - 0.03, zt)])
            for zt in (zb + 2.3, zb + 4.6):
                mull.append([P(0, dv - 0.03, zt - 0.05), P(w, dv - 0.03, zt - 0.05), P(w, dv - 0.03, zt + 0.05), P(0, dv - 0.03, zt + 0.05)])
            plinth.append([P(0, -0.3, zb - 0.9), P(w, -0.3, zb - 0.9), P(w, -0.3, zb), P(0, -0.3, zb)])
            plinth.append([P(0, -0.3, zb), P(w, -0.3, zb), P(w, dv, zb), P(0, dv, zb)])
            if big:
                glassq.append([P(w, dv, zb), P(w, depth, zb), P(w, depth, ze - 0.12), P(w, dv, ze - 0.12)])
        else:
            # two storeys: cream ground floor set back 2 m under the balcony, glass upper floor behind the rail
            sb = 2.0; zf = zb + 3.6   # balcony floor halfway up (g18)
            a0 = 2.7 if k == 4 else 0.0
            if k == 4:
                glassq.append([P(0, 0, zb), P(a0, 0, zb), P(a0, 0, HQ_ZE_LOW - 0.12), P(0, 0, HQ_ZE_LOW - 0.12)])
                mull.append([P(0, -0.03, zb + 2.3 - 0.05), P(a0, -0.03, zb + 2.3 - 0.05), P(a0, -0.03, zb + 2.35), P(0, -0.03, zb + 2.35)])
                plinth.append([P(0, -0.3, zb), P(a0, -0.3, zb), P(a0, 0, zb), P(0, 0, zb)])
                c = A + u * a0; cols.append(((c.x, c.y), zb - 0.4, ze))
                faces_obj([[P(a0, 0, zb), P(a0, sb, zb), P(a0, sb, zf + 0.3), P(a0, 0, zf + 0.3)]], 'hq_hall_end', 'hq_glass')
            cream.append([P(a0, sb, zb), P(w, sb, zb), P(w, sb, zf), P(a0, sb, zf)])
            dark.append([P(w * 0.30, sb - 0.02, zb), P(w * 0.30 + 1.2, sb - 0.02, zb), P(w * 0.30 + 1.2, sb - 0.02, zb + 2.3), P(w * 0.30, sb - 0.02, zb + 2.3)])
            dark.append([P(w * 0.62, sb - 0.02, zb + 1.0), P(w * 0.62 + 1.3, sb - 0.02, zb + 1.0), P(w * 0.62 + 1.3, sb - 0.02, zb + 2.3), P(w * 0.62, sb - 0.02, zb + 2.3)])
            slab += [[P(a0, -0.2, zf), P(w, -0.2, zf), P(w, -0.2, zf + 0.3), P(a0, -0.2, zf + 0.3)],
                     [P(a0, -0.2, zf + 0.3), P(w, -0.2, zf + 0.3), P(w, sb, zf + 0.3), P(a0, sb, zf + 0.3)],
                     [P(a0, -0.2, zf), P(a0, sb, zf), P(w, sb, zf), P(w, -0.2, zf)]]
            rail.append([P(a0, -0.1, zf + 1.3), P(w, -0.1, zf + 1.3), P(w, -0.1, zf + 1.38), P(a0, -0.1, zf + 1.38)])
            rail.append([P(a0, -0.1, zf + 0.3), P(w, -0.1, zf + 0.3), P(w, -0.1, zf + 0.36), P(a0, -0.1, zf + 0.36)])
            for a in np.arange(a0 + 0.06, w, 0.14):
                railg.append([P(a - 0.015, -0.1, zf + 0.36), P(a + 0.015, -0.1, zf + 0.36), P(a + 0.015, -0.1, zf + 1.3), P(a - 0.015, -0.1, zf + 1.3)])
            glassq.append([P(a0, sb, zf + 0.3), P(w, sb, zf + 0.3), P(w, sb, ze - 0.12), P(a0, sb, ze - 0.12)])
            for a in (w / 3, 2 * w / 3):
                mull.append([P(a - 0.05, sb - 0.03, zf + 0.3), P(a + 0.05, sb - 0.03, zf + 0.3), P(a + 0.05, sb - 0.03, ze), P(a - 0.05, sb - 0.03, ze)])
            plinth.append([P(0, -0.3, zb - 0.9), P(w, -0.3, zb - 0.9), P(w, -0.3, zb), P(0, -0.3, zb)])
            plinth.append([P(a0, -0.3, zb), P(w, -0.3, zb), P(w, sb, zb), P(a0, sb, zb)])
        # grass bank in front, from the paving up to the plinth (g18)
        bank.append([P(0, -7.5, 0.02), P(w, -7.5, 0.02), P(w, -0.3, zb - 0.9 + 0.9 * 0.0 + 0.0), P(0, -0.3, zb - 0.9)])
        if k == 4:   # the small scoreboard on the ground floor front by the glass hall (g18, g34)
            hq_sb = [P(3.7, -0.25, zb + 1.7), P(6.4, -0.25, zb + 1.7), P(6.4, -0.25, zb + 3.35), P(3.7, -0.25, zb + 3.35)]
            hq_sbi = [P(3.85, -0.27, zb + 1.85), P(6.25, -0.27, zb + 1.85), P(6.25, -0.27, zb + 3.2), P(3.85, -0.27, zb + 3.2)]
    for k2, ((x, y), z0, z1) in enumerate(cols):
        box((x, y, (z0 + z1) / 2), (0.26, 0.26, z1 - z0), f'hq_col_{k2}', 'green')
    ncol_ = len(cols)
    faces_obj(roof, 'hq_roof', 'roof_white'); faces_obj(sof, 'hq_soffit', 'sign_white')
    M.setdefault('roof_blue', corrugated('roof_blue', (0.50, 0.56, 0.62), axis=1, metal=0.2, rough=0.5))
    M.setdefault('sky_amber', flat('sky_amber', (0.78, 0.52, 0.16), 0.25))
    M.setdefault('vine', leaves('vine', (0.10, 0.22, 0.06), (0.22, 0.34, 0.10)))
    faces_obj(roofb, 'hq_entrance_roof', 'roof_blue'); faces_obj(sky, 'hq_skylights', 'sky_amber')
    faces_obj(barge, 'hq_bargeboards', 'green'); faces_obj(glassq, 'hq_glass', 'hq_glass')
    faces_obj(mull, 'hq_mullions', 'green'); faces_obj(solar, 'hq_solar', 'solar')
    faces_obj(cream, 'hq_ground_floor', 'render_cream'); faces_obj(dark, 'hq_doors', 'dark')
    faces_obj(slab, 'hq_balcony', 'render_white'); faces_obj(rail, 'hq_rail', 'green')
    faces_obj(railg, 'hq_balusters', 'green'); faces_obj(plinth, 'hq_plinth', 'concrete')
    faces_obj(bank, 'hq_bank', 'grass_edge')
    faces_obj([hq_sb], 'hq_scoreboard_frame', 'sb_yellow'); faces_obj([hq_sbi], 'hq_scoreboard_face', 'black')
    # the rest of the footprint: flat metal roof just under the eaves, cream render walls round the back and the west
    fp = [tuple(p) for p in G['ways']['292154259']][:-1]
    ze = ZE_HI
    fr = faces_obj([[(x, y, ze - 0.3) for x, y in fp]], 'hq_flat_roof', 'roof_cream')
    front = [lc[0] for lc in lowcut]; back = [lc[1] for lc in lowcut]
    ring_ = front + back[::-1]
    bmc = bmesh.new()
    lo = [bmc.verts.new((x, y, ze - 2.0)) for x, y in ring_]; hi = [bmc.verts.new((x, y, ze + 2.0)) for x, y in ring_]
    for i in range(len(ring_)):
        j = (i + 1) % len(ring_); bmc.faces.new((lo[i], lo[j], hi[j], hi[i]))
    bmc.faces.new(hi); bmc.faces.new(lo[::-1]); bmesh.ops.recalc_face_normals(bmc, faces=bmc.faces)
    cut = obj_from(bmc, 'hq_cutter', 'concrete')
    md = fr.modifiers.new('cut', 'BOOLEAN'); md.operation = 'DIFFERENCE'; md.object = cut; md.solver = 'EXACT'
    bpy.context.view_layer.objects.active = fr; bpy.ops.object.modifier_apply(modifier='cut')
    bpy.data.objects.remove(cut, do_unlink=True)
    step = []
    for (x1, y1), (x2, y2) in zip(back[:-1], back[1:]):
        step.append([(x1, y1, HQ_ZE_LOW - 0.12), (x2, y2, HQ_ZE_LOW - 0.12), (x2, y2, ze - 0.3), (x1, y1, ze - 0.3)])
    (x1, y1), (x2, y2) = front[-1], back[-1]
    step.append([(x1, y1, HQ_ZE_LOW), (x2, y2, HQ_ZE_LOW), (x2, y2, ze - 0.3), (x1, y1, ze - 0.3)])
    faces_obj(step, 'hq_hall_step', 'render_cream')
    wq = []
    for i in range(len(fp)):
        (x1, y1), (x2, y2) = fp[i], fp[(i + 1) % len(fp)]
        if y1 > -100.5 and y2 > -100.5 and x1 > -22.0 and x2 > -22.0: continue   # the gabled front
        wq.append([(x1, y1, 0.0), (x2, y2, 0.0), (x2, y2, ze - 0.3), (x1, y1, ze - 0.3)])
    faces_obj(wq, 'hq_walls', 'render_cream')
    O_ = Vector((-20.0, -90.0)); U_ = Vector((0.857, -0.515)); V_ = Vector((-0.515, -0.857))
    def F(u, v, z): q = O_ + U_ * u + V_ * v; return (q.x, q.y, z)
    zt = HQ_ZB + 1.0
    # entrance box (OSM pts 4-5-6, u -8..-2.2, v 0.7..7.5): low blue-grey hipped roof, glazed oval face (a02)
    ze2, zr2 = ZE_HI - 0.6, ZE_HI + 0.9
    faces_obj([[F(-8.6, 0.1, ze2), F(-1.6, 0.1, ze2), F(-3.2, 4.1, zr2), F(-7.0, 4.1, zr2)],
               [F(-1.6, 0.1, ze2), F(-1.6, 8.0, ze2), F(-3.2, 4.1, zr2)],
               [F(-1.6, 8.0, ze2), F(-8.6, 8.0, ze2), F(-7.0, 4.1, zr2), F(-3.2, 4.1, zr2)],
               [F(-8.6, 8.0, ze2), F(-8.6, 0.1, ze2), F(-7.0, 4.1, zr2)]], 'hq_entry_roof', 'roof_blue')
    faces_obj([[F(-8.0, 0.7, zb), F(-2.2, 0.7, zb), F(-2.2, 0.7, ze2), F(-8.0, 0.7, ze2)],
               [F(-8.2, 7.4, zb), F(-8.0, 0.7, zb), F(-8.0, 0.7, ze2), F(-8.2, 7.4, ze2)]], 'hq_entry_glass', 'hq_glass')
    for a in (-8.0, -6.1, -4.1, -2.2):
        q = F(a, 0.68, 0); cols.append(((q[0], q[1]), zb, ze2))
    box(F(-5.1, 0.66, zb + 3.0), (5.8, 0.12, 0.14), 'hq_entry_transom', 'green', rot=math.atan2(U_.y, U_.x))
    # tall cross-gable behind it: ridge along U, gable end facing west over the notch (g34+a02 apex (-28.46,-97.45,11.64))
    gv0, gv1, gez, gaz, gu0, gu1 = 7.9, 13.7, 9.2, 11.64, -4.8, 4.0
    gvm = (gv0 + gv1) / 2
    faces_obj([[F(gu0, gv0 - 0.3, gez - 0.1), F(gu1, gv0 - 0.3, gez - 0.1), F(gu1, gvm, gaz), F(gu0, gvm, gaz)],
               [F(gu0, gvm, gaz), F(gu1, gvm, gaz), F(gu1, gv1 + 0.3, gez - 0.1), F(gu0, gv1 + 0.3, gez - 0.1)]], 'hq_cross_roof', 'roof_white')
    faces_obj([[F(gu0 + 0.3, gv0, gez - 0.12), F(gu0 + 0.3, gvm, gaz - 0.15), F(gu0 + 0.3, gv1, gez - 0.12)]], 'hq_cross_gable', 'sign_white')
    faces_obj([[F(gu0 - 0.01, gv0 - 0.3, gez - 0.35), F(gu0 - 0.01, gvm, gaz - 0.25), F(gu0 - 0.01, gvm, gaz + 0.02), F(gu0 - 0.01, gv0 - 0.3, gez - 0.08)],
               [F(gu0 - 0.01, gvm, gaz - 0.25), F(gu0 - 0.01, gv1 + 0.3, gez - 0.35), F(gu0 - 0.01, gv1 + 0.3, gez - 0.08), F(gu0 - 0.01, gvm, gaz + 0.02)]], 'hq_cross_barge', 'green')
    faces_obj([[F(gu0 + 0.3, gv0, zb), F(gu0 + 0.3, gv0, gez - 0.12), F(gu0 + 0.3, gv1, gez - 0.12), F(gu0 + 0.3, gv1, zb)]], 'hq_cross_glass', 'hq_glass')
    faces_obj([[F(gu0 + 0.3, gv0, gez - 0.12), F(gu1, gv0, gez - 0.12), F(gu1, gv0, ZE_HI - 0.3), F(gu0 + 0.3, gv0, ZE_HI - 0.3)],
               [F(gu1, gv1, gez - 0.12), F(gu0 + 0.3, gv1, gez - 0.12), F(gu0 + 0.3, gv1, ZE_HI - 0.3), F(gu1, gv1, ZE_HI - 0.3)]], 'hq_cross_sides', 'render_cream')
    for v in (gv0, gv1):
        q = F(gu0 + 0.25, v, 0); cols.append(((q[0], q[1]), zb, gez))
    # purple porch in the notch (OSM pts 2-3, u -6, v 7.6..11.3), facing west under the gable end (g34)
    pv0, pv1 = 7.7, 11.2; pvm = (pv0 + pv1) / 2; pz, pr = zb + 3.0, zb + 4.3; pu = -7.3
    faces_obj([[F(pu, pv0 - 0.2, pz), F(-4.5, pv0 - 0.2, pz), F(-4.5, pvm, pr), F(pu, pvm, pr)],
               [F(pu, pvm, pr), F(-4.5, pvm, pr), F(-4.5, pv1 + 0.2, pz), F(pu, pv1 + 0.2, pz)]], 'hq_porch_roof', 'roof_white')
    faces_obj([[F(pu - 0.02, pv0 + 0.1, pz + 0.05), F(pu - 0.02, pvm, pr - 0.1), F(pu - 0.02, pv1 - 0.1, pz + 0.05)]], 'hq_porch_sign', 'club_purple')
    for v in (pv0, pv1):
        q = F(pu + 0.15, v, 0); cols.append(((q[0], q[1]), zb, pz))
    # cream west block (OSM pts 0-1-2 + the back), 1.9 m above the flat roof (g34 roof line), punched windows west face
    zc_ = ZE_HI - 0.3 + 1.9
    prism([F(-9.5, 11.2, 0)[:2], F(-4.5, 11.3, 0)[:2], F(-4.5, 30.8, 0)[:2], (-37.9, -115.2), (-44.5, -110.8)],
          0.0, zc_, 'hq_west_block', 'render_cream')
    faces_obj([[F(-9.9, 11.0, zc_ + 0.02), F(-4.3, 11.0, zc_ + 0.02), F(-4.3, 31.0, zc_ + 0.02), F(-10.5, 31.0, zc_ + 0.02)]], 'hq_west_roof', 'roof_cream')
    win = []
    pa_, pb_ = Vector((-33.9, -94.7)), Vector((-44.5, -110.8)); t_ = (pb_ - pa_).normalized(); nn = Vector((t_.y, -t_.x))
    for zc in (2.2, 5.4):
        for s_ in np.arange(1.6, (pb_ - pa_).length - 1.0, 2.2):
            c = pa_ + t_ * s_ + nn * 0.03
            win.append([(c.x - t_.x * 0.5, c.y - t_.y * 0.5, zc - 0.55), (c.x + t_.x * 0.5, c.y + t_.y * 0.5, zc - 0.55),
                        (c.x + t_.x * 0.5, c.y + t_.y * 0.5, zc + 0.55), (c.x - t_.x * 0.5, c.y - t_.y * 0.5, zc + 0.55)])
    faces_obj(win, 'hq_west_windows', 'hq_glass')
    # green pergola in front of the west block: 4 small gabled bays, ridges across the face, vines on top (g34, a02)
    pg = []; pgv = []
    for i in range(4):
        v0, v1 = 12.2 + i * 2.4, 12.2 + (i + 1) * 2.4; vm = (v0 + v1) / 2; ua, ub = -13.4, -10.3
        for u in (ua, ub):
            for v in (v0, v1):
                q = F(u, v, 0); box((q[0], q[1], (zb + 1.5) / 2), (0.14, 0.14, zb + 1.5), f'hq_perg_post_{i}_{u}_{v}', 'green')
        pg += [[F(ua - 0.03, v0, zb + 1.5), F(ua - 0.03, vm, zb + 2.4), F(ua - 0.03, vm, zb + 2.25), F(ua - 0.03, v0 + 0.15, zb + 1.4)],
               [F(ua - 0.03, vm, zb + 2.4), F(ua - 0.03, v1, zb + 1.5), F(ua - 0.03, v1 - 0.15, zb + 1.4), F(ua - 0.03, vm, zb + 2.25)]]
        pgv += [[F(ua, v0, zb + 1.5), F(ub, v0, zb + 1.5), F(ub, vm, zb + 2.35), F(ua, vm, zb + 2.35)],
                [F(ua, vm, zb + 2.35), F(ub, vm, zb + 2.35), F(ub, v1, zb + 1.5), F(ua, v1, zb + 1.5)]]
    faces_obj(pg, 'hq_pergola_frame', 'green'); faces_obj(pgv, 'hq_pergola_vines', 'vine')
    for k2, ((x, y), z0, z1) in enumerate(cols[ncol_:]):
        box((x, y, (z0 + z1) / 2), (0.26, 0.26, z1 - z0), f'hq_colw_{k2}', 'green')
    # rooftop plant on the flat roof (a02)
    for k2, (x, y) in enumerate(((-10, -112), (-2, -115), (6, -118), (-18, -108), (14, -116))):
        box((x, y, ze - 0.3 + 0.4), (1.4, 1.0, 0.8), f'hq_plant_{k2}', 'aircon')

ground(); fence(); terrace(); pavilion(); buildings(); towers(); hq()   # trees() deferred to the background scene pass (director 2026-11-18, via the secretary)

# ---------------------------------------------------------------- texture pass (hand-painted maps from tex/paint_fo.py)
# glTF exports image textures, not procedural nodes: every material with a painted map gets Image Texture (UVMap)
# -> Base Color (roughness and metal kept; procedural colour and bump nodes removed). UVs are world metres / repeat
# size per face: walls and roofs run u along the horizontal, v up the face (image top = up, so rain streaks run
# down and roof ribs run down the slope); flat faces use world x / y, except seat treads, which run u along the
# tread's long edge so the seats follow each row.
def texture_pass():
    TD = os.path.join(ROOT, 'tex'); TL = json.load(open(os.path.join(TD, 'tiles.json')))
    # text signs become meshes first (a text object has no UV map to carry the painted map)
    fonts = [o for o in scn.objects if o.type == 'FONT']
    if fonts:
        bpy.ops.object.select_all(action='DESELECT')
        for o in fonts: o.select_set(True)
        bpy.context.view_layer.objects.active = fonts[0]; bpy.ops.object.convert(target='MESH')
    for m in bpy.data.materials:
        p = os.path.join(TD, m.name + '.png')
        if m.name not in TL or not os.path.exists(p) or not m.use_nodes: continue
        nt = m.node_tree; bs = next((n for n in nt.nodes if n.type == 'BSDF_PRINCIPLED'), None)
        if bs is None: continue
        for inp in ('Base Color', 'Normal'):
            for l in list(bs.inputs[inp].links): nt.links.remove(l)
        it = nt.nodes.new('ShaderNodeTexImage'); it.image = bpy.data.images.load(p); it.interpolation = 'Linear'
        uvn = nt.nodes.new('ShaderNodeUVMap'); uvn.uv_map = 'UVMap'
        nt.links.new(uvn.outputs['UV'], it.inputs['Vector']); nt.links.new(it.outputs['Color'], bs.inputs['Base Color'])
        live = set(); stack = [n for n in nt.nodes if n.type == 'OUTPUT_MATERIAL']
        while stack:
            n = stack.pop()
            if n in live: continue
            live.add(n); stack += [l.from_node for i_ in n.inputs for l in i_.links]
        for n in [n for n in nt.nodes if n not in live]: nt.nodes.remove(n)
    Z = Vector((0, 0, 1))
    for ob in list(scn.objects):
        if ob.type != 'MESH' or not ob.data.materials: continue
        me = ob.data; mw = ob.matrix_world; nmx = mw.to_3x3().inverted_safe().transposed()
        for l_ in list(me.uv_layers): me.uv_layers.remove(l_)
        bm = bmesh.new(); bm.from_mesh(me); uv = bm.loops.layers.uv.new('UVMap')
        for f in bm.faces:
            mt = me.materials[f.material_index] if f.material_index < len(me.materials) else None
            tw, th = TL.get(mt.name, [4.0, 4.0]) if mt else (4.0, 4.0)
            n = (nmx @ f.normal).normalized()
            if abs(n.z) > 0.98:
                if mt and mt.name.startswith('seat_'):
                    e = max(f.edges, key=lambda e_: e_.calc_length())
                    d = (mw @ e.verts[1].co) - (mw @ e.verts[0].co); d.z = 0
                    tv = d.normalized() if d.length > 1e-6 else Vector((1, 0, 0)); bv = Z.cross(tv)
                else: tv, bv = Vector((1, 0, 0)), Vector((0, 1, 0))
            else:
                tv = Z.cross(n).normalized(); bv = n.cross(tv)
            for l in f.loops:
                p = mw @ l.vert.co; l[uv].uv = (p.dot(tv) / tw, p.dot(bv) / th)
        bm.to_mesh(me); bm.free()
        me.uv_layers.active = me.uv_layers['UVMap']

texture_pass()

# ---------------------------------------------------------------- light + world
sun = bpy.data.lights.new('sun', 'SUN'); sun.energy = 5.0; sun.angle = math.radians(0.6)
sun.color = (1.0, 0.93, 0.82)
so = bpy.data.objects.new('sun', sun); scn.collection.objects.link(so)
# a04 2024-07-15 afternoon: shadows fall south-east on the grass -> sun in the north-west, low
# a04 sun from the T2 head shadow at (-52.2, 9.1): azimuth 316 deg (north-west), elevation 23 deg
so.rotation_euler = Vector((0.64, -0.66, -0.40)).to_track_quat('-Z', 'Y').to_euler()
w = bpy.data.worlds.new('w'); scn.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = (0.46, 0.52, 0.60, 1); bg.inputs[1].default_value = 0.30

# ---------------------------------------------------------------- camera
def a04_camera():
    import mathutils
    p = CAM['p']; W, H = CAM['W'], CAM['H']
    yaw, pit, rol = p[3:6]
    cy_, sy_ = math.cos(yaw), math.sin(yaw); cp, sp = math.cos(pit), math.sin(pit); cr, sr = math.cos(rol), math.sin(rol)
    f = np.array([cy_ * cp, sy_ * cp, sp]); r = np.array([sy_, -cy_, 0.0]); u = np.cross(r, f)
    right = cr * r + sr * u; up = -sr * r + cr * u
    rot = mathutils.Matrix([[right[0], up[0], -f[0]], [right[1], up[1], -f[1]], [right[2], up[2], -f[2]]])
    cam = bpy.data.cameras.new('cam'); cam.sensor_fit = 'HORIZONTAL'; cam.sensor_width = 36.0
    cam.lens = p[6] * 36.0 / W; cam.clip_end = 3000
    co = bpy.data.objects.new('cam', cam); scn.collection.objects.link(co)
    co.matrix_world = mathutils.Matrix.Translation(p[:3]) @ rot.to_4x4()
    scn.camera = co
    scn.render.resolution_x, scn.render.resolution_y = W, H
    scn.render.resolution_percentage = int(os.environ.get('RPCT', '100'))
    return co

scn.render.engine = 'BLENDER_EEVEE'
scn.view_settings.view_transform = 'Standard'
scn.render.film_transparent = True
# no lettering on any ground model (lead via the secretary, 2026-11-18): every text object goes; boards stay blank
# director 2026-11-19 "Yes, ground's own signs" + no ads: the ground's name, gate, media box and club signs stay; sponsor lettering goes
LETTER_PREFIXES = ('nstand_txt2', 'nstand_logo', 'nboard_txt_')
_gone = [o for o in list(scn.objects) if o.name.startswith(LETTER_PREFIXES)]
print('LETTERING_REMOVED', len(_gone), sorted({o.name.rstrip('0123456789_') for o in _gone}))
for o in _gone: bpy.data.objects.remove(o, do_unlink=True)
if MODE == 'a04':
    a04_camera()
    scn.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
elif MODE in ('turn', 'close'):
    import mathutils
    os.makedirs(OUT, exist_ok=True)
    # review renders only: a plain grass fill where the game's own pitch goes (never exported in the GLB)
    M['review_grass'] = flat('review_grass', (0.12, 0.3, 0.06), 0.9)   # own plain material: never the bank's painted map
    faces_obj([[(*pt, -0.04) for pt in off(0.0)]], 'review_pitch_fill', 'review_grass')
    scn.render.film_transparent = False
    cam = bpy.data.cameras.new('tcam'); cam.lens = 35; cam.clip_end = 3000
    co = bpy.data.objects.new('tcam', cam); scn.collection.objects.link(co); scn.camera = co
    tgt = bpy.data.objects.new('tgt', None); scn.collection.objects.link(tgt)
    tc_ = co.constraints.new('TRACK_TO'); tc_.target = tgt; tc_.track_axis = 'TRACK_NEGATIVE_Z'; tc_.up_axis = 'UP_Y'
    if MODE == 'close':
        # facade close-ups from the oval: north stand sign, gate, pavilion
        shots = {'close_nstand': ((-20.0, 60.0, 6.0), (-20.0, 97.0, 8.0)),
                 'close_gate': ((-60.0, 40.0, 4.0), (-95.0, 70.0, 4.0)),
                 'pav_annex': ((-78.0, 66.0, 8.0), (-101.0, 50.0, 3.5)),
                 'close_pavilion': ((-70.0, 20.0, 6.0), (-108.0, 20.0, 6.0)),
                 'close_terrace': ((40.0, 0.0, 5.0), (80.0, 0.0, 3.0)),
                 'gj_front': (GJ(22, 19, 1.6), GJ(22, 0, 4.0)),
                 'gj_se': (GJ(64, 14, 1.6), GJ(24, 0, 4.0)),
                 'gj_nw': (GJ(-25, -19, 1.6), GJ(0, -19, 4.0)),
                 'gj_air': (GJ(30, 75, 45), GJ(30, -10, 2.0)),
                 'gj_fascia': (GJ(32, 30, 4.0), GJ(32, 0, 6.6)),
                 'media_oval': (MB_EYE, MB_AT),
                 'media_street': (MB_EYE2, MB_AT),
                 'hq_g18': ((-36.0, -46.0, 1.7), (14.0, -100.0, 4.5)),
                 'hq_g34': ((-58.0, 30.0, 1.5), (-5.0, -96.0, 4.0)),
                 'hq_front': ((5.0, -62.0, 2.0), (5.0, -98.0, 5.0)),
                 'hq_air': ((-12.0, -30.0, 38.0), (-2.0, -100.0, 3.0)),
                 'hq_facade': ((12.0, -82.0, 2.5), (12.0, -99.0, 5.0)),
                 'seat_nstand': ((-14.0, 82.0, 3.5), (-22.0, 93.0, 3.0)),
                 'seat_gj': (GJ(18, 7, 6.5), GJ(24, -3.5, 2.2)),
                 'seat_pav': (tuple(PF(10.0, 3.3, 5.4)), tuple(PF(13.5, 3.1, 4.0)))}
        if len(sys.argv) > sys.argv.index('--') + 3:
            only = sys.argv[sys.argv.index('--') + 3].split(',')
            shots = {k: v for k, v in shots.items() if k in only}
        scn.render.resolution_x, scn.render.resolution_y = 1920, 1080
        for nm, (eye, at) in shots.items():
            co.location = eye; tgt.location = at
            scn.render.filepath = os.path.join(OUT, nm + '.png'); bpy.ops.render.render(write_still=True)
    else:
        R, Z = 230.0, 95.0
        scn.render.resolution_x, scn.render.resolution_y = 1920, 1080
        for a in (0, 90, 180, 270):
            t = math.radians(a - 45)
            co.location = (R * math.cos(t), R * math.sin(t), Z)
            scn.render.filepath = os.path.join(OUT, f'still_{a:03d}.png'); bpy.ops.render.render(write_still=True)
        scn.render.resolution_x, scn.render.resolution_y = 1280, 720
        N = 60
        for f in range(N):
            t = math.radians(-45) + 2 * math.pi * f / N
            co.location = (R * math.cos(t), R * math.sin(t), Z)
            scn.render.filepath = os.path.join(OUT, f'turn_{f:03d}.png'); bpy.ops.render.render(write_still=True)
elif MODE == 'photo':
    import mathutils
    PC = json.load(open(os.path.join(ROOT, sys.argv[sys.argv.index('--') + 3])))
    dz = float(sys.argv[sys.argv.index('--') + 4]) if len(sys.argv) > sys.argv.index('--') + 4 else 0.0
    p = list(PC['p']); p[2] += dz; W_, H_ = PC['W'], PC['H']
    yaw, pit, rol = p[3:6]
    f_ = np.array([math.cos(yaw) * math.cos(pit), math.sin(yaw) * math.cos(pit), math.sin(pit)]); r_ = np.array([math.sin(yaw), -math.cos(yaw), 0.0]); u_ = np.cross(r_, f_)
    right = math.cos(rol) * r_ + math.sin(rol) * u_; up = -math.sin(rol) * r_ + math.cos(rol) * u_
    rot = mathutils.Matrix([[right[0], up[0], -f_[0]], [right[1], up[1], -f_[1]], [right[2], up[2], -f_[2]]])
    cam = bpy.data.cameras.new('pcam'); cam.sensor_fit = 'HORIZONTAL'; cam.sensor_width = 36.0
    cam.lens = p[6] * 36.0 / W_; cam.clip_end = 3000
    co = bpy.data.objects.new('pcam', cam); scn.collection.objects.link(co)
    co.matrix_world = mathutils.Matrix.Translation(p[:3]) @ rot.to_4x4(); scn.camera = co
    scn.render.resolution_x, scn.render.resolution_y = W_, H_; scn.render.resolution_percentage = 100
    scn.render.filepath = OUT; bpy.ops.render.render(write_still=True)
elif MODE == 'photos':
    import mathutils
    args_ = sys.argv[sys.argv.index('--') + 2:]
    for i_ in range(0, len(args_), 3):
        out_, js_, dz_ = args_[i_], args_[i_ + 1], float(args_[i_ + 2])
        PC = json.load(open(os.path.join(ROOT, js_)))
        p = list(PC['p']); p[2] += dz_; W_, H_ = PC['W'], PC['H']
        yaw, pit, rol = p[3:6]
        f_ = np.array([math.cos(yaw) * math.cos(pit), math.sin(yaw) * math.cos(pit), math.sin(pit)]); r_ = np.array([math.sin(yaw), -math.cos(yaw), 0.0]); u_ = np.cross(r_, f_)
        right = math.cos(rol) * r_ + math.sin(rol) * u_; up = -math.sin(rol) * r_ + math.cos(rol) * u_
        rot = mathutils.Matrix([[right[0], up[0], -f_[0]], [right[1], up[1], -f_[1]], [right[2], up[2], -f_[2]]])
        cam = bpy.data.cameras.new('pcam%d' % i_); cam.sensor_fit = 'HORIZONTAL'; cam.sensor_width = 36.0
        cam.lens = p[6] * 36.0 / W_; cam.clip_end = 5000; cam.clip_start = float(os.environ.get('CLIPS', '0.1'))
        co = bpy.data.objects.new('pcam%d' % i_, cam); scn.collection.objects.link(co)
        co.matrix_world = mathutils.Matrix.Translation(p[:3]) @ rot.to_4x4(); scn.camera = co
        scn.render.resolution_x, scn.render.resolution_y = W_, H_; scn.render.resolution_percentage = 100
        if os.environ.get('BORDER'):
            bx0, by0, bx1, by1 = [float(v) for v in os.environ['BORDER'].split(',')]   # pixels, y down
            scn.render.use_border = True; scn.render.use_crop_to_border = False
            scn.render.border_min_x, scn.render.border_max_x = bx0 / W_, bx1 / W_
            scn.render.border_min_y, scn.render.border_max_y = 1 - by1 / H_, 1 - by0 / H_
        scn.render.filepath = os.path.join(ROOT, out_); bpy.ops.render.render(write_still=True)
elif MODE == 'top':
    # straight-down orthographic render of a box in model metres: -- top out.png x0 y0 x1 y1 px_per_m
    x0_, y0_, x1_, y1_, ppm_ = [float(v) for v in argv[2:7]]
    cam = bpy.data.cameras.new('topcam'); cam.type = 'ORTHO'; cam.clip_end = 1000
    cam.ortho_scale = max(x1_ - x0_, y1_ - y0_)
    co = bpy.data.objects.new('topcam', cam); scn.collection.objects.link(co); scn.camera = co
    co.location = ((x0_ + x1_) / 2, (y0_ + y1_) / 2, 400.0); co.rotation_euler = (0, 0, 0)
    scn.render.resolution_x = int(round((x1_ - x0_) * ppm_)); scn.render.resolution_y = int(round((y1_ - y0_) * ppm_))
    scn.render.resolution_percentage = 100
    scn.render.filepath = OUT; bpy.ops.render.render(write_still=True)
elif MODE == 'glb':
    bpy.ops.export_scene.gltf(filepath=OUT, export_format='GLB', export_apply=True, export_image_format='JPEG', export_jpeg_quality=90)   # maps are RGB only
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT, 'build', 'fremantle_oval.blend'))
