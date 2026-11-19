"""Hand-made procedural materials (no photo pixels). Every vertex carries its colour (read from the photos as a
material colour), a material kind in the alpha channel (kind * 20 / 255) and UVs in metres. The shader paints the
pattern of the real material at real size: seat rows, concrete panels, membrane seams, steel, glass, brick, grass."""
import bpy


class G:
    def __init__(s, nt): s.nt = nt; s.N = nt.nodes; s.L = nt.links; s.x = 0

    def node(s, t, **kw):
        n = s.N.new(t)
        for k, v in kw.items(): setattr(n, k, v)
        return n

    def link(s, a, b): s.L.new(a, b)

    def m(s, op, a, b=None):
        n = s.node('ShaderNodeMath', operation=op)
        for i, v in enumerate((a, b)):
            if v is None: continue
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: s.link(v, n.inputs[i])
        return n.outputs[0]

    def frac(s, x, period): return s.m('FRACT', s.m('DIVIDE', x, period))

    def band(s, x, lo, hi):  # 1 where lo <= x < hi
        return s.m('MULTIPLY', s.m('GREATER_THAN', x, lo), s.m('LESS_THAN', x, hi))

    def scale(s, col, k):
        n = s.node('ShaderNodeVectorMath', operation='SCALE')
        s.link(col, n.inputs[0])
        if isinstance(k, (int, float)): n.inputs[3].default_value = k
        else: s.link(k, n.inputs[3])
        return n.outputs[0]

    def rgb(s, c):
        n = s.node('ShaderNodeRGB'); n.outputs[0].default_value = (*c, 1); return n.outputs[0]

    def mix(s, fac, a, b):  # colour: fac 0 -> a, 1 -> b
        n = s.node('ShaderNodeMix', data_type='RGBA')
        if isinstance(fac, (int, float)): n.inputs[0].default_value = fac
        else: s.link(fac, n.inputs[0])
        s.link(a, n.inputs[6]); s.link(b, n.inputs[7]); return n.outputs[2]

    def mixf(s, fac, a, b):
        n = s.node('ShaderNodeMix', data_type='FLOAT'); s.link(fac, n.inputs[0])
        for i, v in ((2, a), (3, b)):
            if isinstance(v, (int, float)): n.inputs[i].default_value = v
            else: s.link(v, n.inputs[i])
        return n.outputs[0]

    def noise(s, vec, sc, detail=4.0):
        n = s.node('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = sc; n.inputs['Detail'].default_value = detail
        s.link(vec, n.inputs['Vector']); return n.outputs['Fac']


def build(obj):
    m = bpy.data.materials.new(obj.name); m.use_nodes = True
    nt = m.node_tree; g = G(nt); bs = nt.nodes.get('Principled BSDF')
    ca = g.node('ShaderNodeVertexColor')
    if obj.data.color_attributes: ca.layer_name = obj.data.color_attributes[0].name
    C = ca.outputs['Color']
    kind = g.m('ROUND', g.m('MULTIPLY', ca.outputs['Alpha'], 255 / 20))
    uvn = g.node('ShaderNodeUVMap'); sep = g.node('ShaderNodeSeparateXYZ'); g.link(uvn.outputs[0], sep.inputs[0])
    u, v = sep.outputs[0], sep.outputs[1]
    uvv = uvn.outputs[0]
    tc = g.node('ShaderNodeTexCoord'); obj_co = tc.outputs['Object']
    grain = g.noise(obj_co, 1.3, 6.0)                       # large-scale weathering, about 1 m
    fine = g.noise(uvv, 9.0, 3.0)                           # fine grain, about 10 cm
    wear = g.m('ADD', 0.9, g.m('MULTIPLY', g.m('ADD', grain, g.m('MULTIPLY', fine, 0.5)), 0.13))
    # texture pass (director 2026-11-19): blotching, rain streaks and grime, all procedural
    xyz = g.node('ShaderNodeSeparateXYZ'); g.link(obj_co, xyz.inputs[0]); wz = xyz.outputs[2]
    geo = g.node('ShaderNodeNewGeometry'); nsep = g.node('ShaderNodeSeparateXYZ'); g.link(geo.outputs['Normal'], nsep.inputs[0])
    wall = g.m('SUBTRACT', 1.0, g.m('ABSOLUTE', nsep.outputs[2]))            # 1 on a vertical face, 0 on a flat one
    sv = g.node('ShaderNodeCombineXYZ'); g.link(g.m('MULTIPLY', xyz.outputs[0], 6.0), sv.inputs[0])
    g.link(g.m('MULTIPLY', xyz.outputs[1], 6.0), sv.inputs[1]); g.link(g.m('MULTIPLY', wz, 0.3), sv.inputs[2])
    def nz(vec, sc, detail=3.0, lo=0.35, hi=0.65):  # noise stretched to 0..1
        return g.m('MINIMUM', 1.0, g.m('MAXIMUM', 0.0, g.m('DIVIDE', g.m('SUBTRACT', g.noise(vec, sc, detail), lo), hi - lo)))
    region = nz(obj_co, 0.22, 2.0, 0.45, 0.6)                                            # streaks only in some stretches of wall
    streak = g.m('MULTIPLY', nz(sv.outputs[0], 0.45, 2.0, 0.55, 0.7), region)              # sparse vertical runs, 10-30 cm wide
    blotch = g.m('ADD', 0.88, g.m('MULTIPLY', nz(obj_co, 0.35, 3.0), 0.24))                # weathered patches about 3 m across
    soft = g.m('ADD', 0.95, g.m('MULTIPLY', nz(obj_co, 0.35, 3.0), 0.1))                  # the same, gentler (membranes)
    GRIME = g.rgb((0.16, 0.15, 0.13))
    DUST = g.rgb((0.20, 0.19, 0.17))   # sun-bleached dust film: lifts dark paint, dulls white

    def wnoise(x):
        n = g.node('ShaderNodeTexWhiteNoise', noise_dimensions='1D'); g.link(x, n.inputs['W']); return n.outputs['Value']

    def under_ledge(period):  # 1 just under each ledge or joint every `period` m of height, fading to 0 at the next one down
        d = g.frac(wz, period); return g.m('MULTIPLY', d, d)

    out = {}  # kind -> (colour, roughness, metallic)
    # 0 plain: the material colour with fine weathering
    pg = g.m('MULTIPLY', g.m('MULTIPLY', streak, g.m('SUBTRACT', 1.0, g.frac(wz, 2.5))), g.m('MULTIPLY', wall, 0.5))
    chalky = g.m('ADD', 0.84, g.m('MULTIPLY', nz(obj_co, 0.5, 3.0), 0.32))                    # sun-faded, chalky paint
    qid = g.m('ADD', g.m('FLOOR', g.m('DIVIDE', u, 2.4)), g.m('MULTIPLY', g.m('FLOOR', g.m('DIVIDE', v, 1.2)), 41.0))
    qtone = g.m('ADD', 0.92, g.m('MULTIPLY', wnoise(qid), 0.16))                                # each painted sheet fades its own way
    pc = g.scale(C, g.m('MULTIPLY', g.m('MULTIPLY', wear, chalky), qtone))
    pc = g.mix(g.m('MULTIPLY', wnoise(g.m('ADD', qid, 5.0)), 0.15), pc, g.mix(0.45, C, g.rgb((0.6, 0.6, 0.58))))   # each sheet sun-bleached its own amount
    out[0] = (g.mix(pg, pc, g.scale(C, 0.6)), 0.8, 0.0)
    # 1 seats: rows every 0.8 m (step tread + seat back), seats 0.5 m wide, aisles every 14 m
    r = g.frac(v, 0.8); su = g.frac(u, 0.5); au = g.frac(u, 14.0)
    tread = g.scale(g.rgb((0.20, 0.20, 0.19)), g.m('MULTIPLY', g.m('ADD', 0.45, g.m('MULTIPLY', r, 1.6)), blotch))  # darkest under the seat in front
    seat = g.scale(C, g.m('ADD', 0.95, g.m('MULTIPLY', fine, 0.1)))
    seat = g.mix(g.band(su, 0.0, 0.08), seat, g.scale(C, 0.45))              # gap between seats
    seat = g.mix(g.band(r, 0.82, 0.9), seat, g.scale(C, 1.25))               # lit top of the seat back
    col = g.mix(g.band(r, 0.38, 0.9), tread, seat)
    col = g.mix(g.band(au, 0.0, 0.085), col, g.scale(g.rgb((0.30, 0.30, 0.29)), wear))  # concrete aisle steps
    out[1] = (col, 0.55, 0.0)
    # 2 concrete: panels 4 m x 3 m with dark joints, weathered grain
    j = g.m('MAXIMUM', g.band(g.frac(u, 4.0), 0.0, 0.006), g.band(g.frac(v, 3.0), 0.0, 0.008))
    pid = g.m('ADD', g.m('FLOOR', g.m('DIVIDE', u, 4.0)), g.m('MULTIPLY', g.m('FLOOR', g.m('DIVIDE', v, 3.0)), 37.0))
    ptone = g.m('ADD', 0.9, g.m('MULTIPLY', wnoise(pid), 0.2))                       # each panel cast a little different
    cc = g.scale(C, g.m('MULTIPLY', g.m('MULTIPLY', wear, blotch), ptone))
    cc = g.mix(g.m('MULTIPLY', wnoise(g.m('ADD', pid, 9.0)), 0.15), cc, g.scale(C, 0.55))   # some panels water-stained darker
    cc = g.mix(g.m('MULTIPLY', wnoise(g.m('ADD', pid, 5.0)), 0.15), cc, g.mix(0.3, C, g.rgb((0.55, 0.54, 0.50))))                    # each panel dusted its own amount
    rain = g.m('MULTIPLY', g.m('MULTIPLY', streak, under_ledge(3.0)), g.m('MULTIPLY', wall, 0.9))   # rain runs under each ledge
    cc = g.mix(rain, cc, g.scale(C, 0.45))   # rain darkens its own colour (grey grime would lighten dark concrete)
    agg = g.m('ADD', 0.84, g.m('MULTIPLY', nz(uvv, 30.0, 2.0), 0.32))                                 # aggregate and pitting, 3 cm
    cc = g.scale(cc, agg)
    out[2] = (g.mix(j, cc, g.scale(C, 0.5)), 0.9, 0.0)
    # 3 roof membrane (PTFE): seams every 1.6 m, faint lengthwise sheen
    fu = g.frac(u, 1.6); seam = g.band(fu, 0.0, 0.02)
    lap = g.band(fu, 0.02, 0.085)                                                          # 10 cm welded overlap beside each seam
    ds = g.m('MULTIPLY', g.m('MINIMUM', fu, g.m('SUBTRACT', 1.0, fu)), 1.6)               # metres to the nearest seam
    sg = g.m('MAXIMUM', 0.0, g.m('SUBTRACT', 1.0, g.m('DIVIDE', ds, 0.4)))
    sgr = g.m('MULTIPLY', g.m('MULTIPLY', sg, sg), g.m('ADD', 0.3, g.m('MULTIPLY', nz(obj_co, 2.5, 3.0), 0.7)))  # grime along seams
    tseam = g.band(g.frac(v, 4.0), 0.0, 0.006)                                             # cross welds every 4 m
    memb = g.scale(C, g.m('MULTIPLY', soft, g.m('ADD', 0.95, g.m('MULTIPLY', nz(uvv, 6.0, 4.0), 0.08))))   # creases and woven texture
    memb = g.mix(g.m('MULTIPLY', nz(obj_co, 0.12, 2.0, 0.5, 0.7), 0.2), memb, GRIME)           # broad dust drifts
    memb = g.mix(g.m('MULTIPLY', sgr, 0.7), memb, GRIME)
    memb = g.mix(lap, memb, g.scale(C, 0.93))
    out[3] = (g.mix(g.m('MAXIMUM', seam, tseam), memb, g.scale(C, 0.72)), 0.45, 0.0)
    # 4 steel: painted steel, purlins every 3 m on undersides
    pur = g.band(g.frac(u, 3.0), 0.0, 0.07)
    sh = g.m('MAXIMUM', g.band(g.frac(u, 1.2), 0.0, 0.012), g.band(g.frac(v, 2.4), 0.0, 0.006))   # sheet seams 1.2 m x 2.4 m
    sid = g.m('ADD', g.m('FLOOR', g.m('DIVIDE', u, 1.2)), g.m('MULTIPLY', g.m('FLOOR', g.m('DIVIDE', v, 2.4)), 43.0))
    st = g.scale(C, g.m('MULTIPLY', g.m('MULTIPLY', wear, blotch), g.m('ADD', 0.92, g.m('MULTIPLY', wnoise(sid), 0.16))))   # each sheet its own tone
    low = g.m('SUBTRACT', 1.0, g.frac(wz, 2.4)); low = g.m('MULTIPLY', low, low)            # grime toward each sheet's bottom edge
    sgm = g.m('MULTIPLY', g.m('ADD', g.m('MULTIPLY', low, 0.75), g.m('MULTIPLY', streak, 0.4)), g.m('MULTIPLY', wall, 0.5))
    st = g.mix(sgm, st, g.scale(C, 0.62))                                                  # grime darkens its own colour
    st = g.mix(g.m('MULTIPLY', wnoise(g.m('ADD', sid, 5.0)), 0.15), st, g.mix(0.3, C, g.rgb((0.40, 0.39, 0.37))))                   # each sheet faded its own amount
    st = g.scale(st, g.m('ADD', 0.93, g.m('MULTIPLY', nz(uvv, 2.0, 4.0), 0.14)))                  # scuffs and touch-up paint, about 50 cm
    st = g.mix(sh, st, g.scale(C, 0.6))
    out[4] = (g.mix(pur, st, g.scale(C, 0.6)), 0.35, 0.6)
    # 5 glass: dark tinted panes 1.5 m x 3.2 m in aluminium frames
    fr = g.m('MAXIMUM', g.band(g.frac(u, 1.5), 0.0, 0.045), g.band(g.frac(v, 3.2), 0.0, 0.03))
    pane = g.mix(0.25, g.rgb((0.035, 0.05, 0.065)), C)
    out[5] = (g.mix(fr, pane, g.rgb((0.32, 0.33, 0.34))), g.mixf(fr, 0.05, 0.4), g.mixf(fr, 0.0, 0.8))
    # 6 brick: 230 x 76 mm bricks, 10 mm mortar, stretcher bond
    br = g.node('ShaderNodeTexBrick'); g.link(uvv, br.inputs['Vector'])
    br.inputs['Scale'].default_value = 1.0; br.inputs['Mortar Size'].default_value = 0.01
    br.inputs['Brick Width'].default_value = 0.24; br.inputs['Row Height'].default_value = 0.086
    br.inputs['Bias'].default_value = 0.0
    g.link(C, br.inputs['Color1']); g.link(g.scale(C, 0.78), br.inputs['Color2'])
    br.inputs['Mortar'].default_value = (0.42, 0.40, 0.37, 1)
    out[6] = (g.scale(br.outputs['Color'], blotch), 0.85, 0.0)
    # 7 grass: mowing stripes 10 m wide across the ground (world x), fine blade noise
    wx = g.node('ShaderNodeSeparateXYZ'); g.link(obj_co, wx.inputs[0])
    stripe = g.m('ADD', 0.93, g.m('MULTIPLY', g.m('LESS_THAN', g.frac(wx.outputs[0], 10.0), 0.5), 0.14))
    blade = g.m('ADD', 0.9, g.m('MULTIPLY', g.noise(obj_co, 40.0, 2.0), 0.2))
    blade2 = g.m('ADD', 0.84, g.m('MULTIPLY', nz(obj_co, 40.0, 2.0), 0.3))                 # individual blades and clover leaves
    out[7] = (g.scale(C, g.m('MULTIPLY', stripe, blade)), 0.9, 0.0)
    # 8 fins: vertical copper/timber fins 0.45 m apart with dark gaps
    fin = g.band(g.frac(u, 0.45), 0.0, 0.5)
    out[8] = (g.mix(fin, g.scale(C, 0.35), g.scale(C, wear)), 0.5, 0.3)
    # 9 timber: boards 0.15 m with grain along u
    gr = g.noise(g.node('ShaderNodeCombineXYZ').outputs[0], 1.0)
    board = g.m('ADD', 0.88, g.m('MULTIPLY', g.band(g.frac(v, 0.15), 0.0, 0.92), 0.12))
    out[9] = (g.scale(C, g.m('MULTIPLY', board, wear)), 0.7, 0.0)

    # 10 copper cladding: vertical panels 0.6 m wide, each its own tone (hotel blocks), dark standing seams
    pid = g.m('FLOOR', g.m('DIVIDE', u, 0.6))
    tone = g.m('ADD', 0.68, g.m('MULTIPLY', wnoise(pid), 0.62))
    cop = g.scale(C, g.m('MULTIPLY', tone, g.m('ADD', 0.96, g.m('MULTIPLY', fine, 0.08))))
    cseam = g.band(g.frac(u, 0.6), 0.0, 0.035)
    out[10] = (g.mix(cseam, cop, g.scale(C, 0.35)), 0.42, 0.55)
    # 11 banded stone (hotel piers): courses 0.6 m high, each its own tone, fine joints, block joints every 1.2 m
    cid = g.m('FLOOR', g.m('DIVIDE', v, 0.6))
    ctone = g.m('ADD', 0.84, g.m('MULTIPLY', wnoise(g.m('ADD', cid, 17.0)), 0.32))
    sj = g.m('MAXIMUM', g.band(g.frac(v, 0.6), 0.0, 0.02), g.band(g.frac(g.m('ADD', u, g.m('MULTIPLY', cid, 0.6)), 1.2), 0.0, 0.006))
    out[11] = (g.mix(sj, g.scale(C, g.m('MULTIPLY', g.m('MULTIPLY', ctone, wear), blotch)), g.scale(C, 0.7)), 0.85, 0.0)

    # 12 turf (the Hill's grass patches): no mowing stripes, worn patches about 2 m across, blade noise
    worn = g.m('ADD', 0.68, g.m('MULTIPLY', nz(obj_co, 0.45, 3.0), 0.58))
    clump = g.m('ADD', 0.7, g.m('MULTIPLY', nz(obj_co, 3.0, 4.0), 0.6))                 # clumps and clover, about 30 cm
    bare = nz(obj_co, 0.7, 4.0, 0.56, 0.7)                                                # worn spots
    tf = g.scale(C, g.m('MULTIPLY', g.m('MULTIPLY', worn, clump), blade2))
    tf = g.mix(g.m('MULTIPLY', nz(obj_co, 0.25, 2.0, 0.5, 0.7), 0.35), tf, g.rgb((0.36, 0.38, 0.14)))     # dry yellowed stretches
    out[12] = (g.mix(g.m('MULTIPLY', bare, 0.6), tf, g.rgb((0.30, 0.27, 0.17))), 0.92, 0.0)
    # 13 scoreboard board: painted panels 1.2 m x 0.55 m with dark joints and slight tone changes
    bid = g.m('ADD', g.m('FLOOR', g.m('DIVIDE', u, 1.2)), g.m('MULTIPLY', g.m('FLOOR', g.m('DIVIDE', v, 0.55)), 37.0))
    btone = g.m('ADD', 0.78, g.m('MULTIPLY', wnoise(bid), 0.46))
    bj = g.m('MAXIMUM', g.band(g.frac(u, 1.2), 0.0, 0.03), g.band(g.frac(v, 0.55), 0.0, 0.05))
    chalk = g.m('MULTIPLY', streak, 0.2)                                                  # pale weathering runs (photo c11)
    bc = g.mix(chalk, g.scale(C, btone), g.rgb((0.30, 0.34, 0.33)))
    bc = g.mix(g.m('MULTIPLY', wnoise(g.m('ADD', bid, 5.0)), 0.45), bc, g.rgb((0.12, 0.15, 0.14)))   # panels faded unevenly (photo c11)
    out[13] = (g.mix(bj, bc, g.scale(C, 0.45)), 0.6, 0.0)

    col, rough, met = out[0]
    for k in range(1, 14):
        e = g.m('COMPARE', kind, float(k)); n = g.N[-1] if False else None
        ck, rk, mk = out[k]
        col = g.mix(e, col, ck)
        rough = g.mixf(e, rough, rk); met = g.mixf(e, met, mk)
    g.link(col, bs.inputs['Base Color'])
    for name, val in (('Roughness', rough), ('Metallic', met)):
        if isinstance(val, (int, float)): bs.inputs[name].default_value = val
        else: g.link(val, bs.inputs[name])
    obj.data.materials.append(m)
