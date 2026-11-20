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

def gj_text(txt, u_c, v, z_c, size, mat, name, facing=1):
    # modelled lettering on a face of constant v; facing=1 reads from the oval (left = SE end), -1 from behind
    import math as _m
    bpy.ops.object.text_add(location=(0, 0, 0))
    ob = bpy.context.object; ob.name = name
    ob.data.body = txt; ob.data.font = GJ_FONT
    ob.data.align_x = 'CENTER'; ob.data.align_y = 'CENTER'; ob.data.size = size; ob.data.extrude = 0.02
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
    gj_text('SOUTH FREMANTLE', 31.6, 0.03, zc, 1.15, 'red', 'gj_text_sf')
    gj_text('FOOTBALL CLUB', 14.8, 0.03, zc, 1.15, 'red', 'gj_text_fc')
    gj_disc(41.2, 0.03, zc, 0.62, 'gj_badge_ring', 'red')
    gj_disc(41.2, 0.05, zc, 0.52, 'gj_badge_disc', 'sign_white')
    faces_obj([[GJ(41.65, 0.07, zc + 0.3), GJ(40.75, 0.07, zc + 0.3), GJ(41.2, 0.07, zc - 0.42)]], 'gj_badge_v', 'red')
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
        gj_box(-2.3, 6.0, vb, va, 0.0, 5.2, f'gj_gable_walls_{g}', 'render_white', top=False)
        faces_obj([[GJ(-2.3, va, 5.2), GJ(-2.3, vm, 7.2), GJ(6.0, vm, 7.2), GJ(6.0, va, 5.2)],
                   [GJ(-2.3, vm, 7.2), GJ(-2.3, vb, 5.2), GJ(6.0, vb, 5.2), GJ(6.0, vm, 7.2)]], f'gj_gable_roof_{g}', 'roof_white')
        faces_obj([[GJ(-2.31, va, 5.2), GJ(-2.31, vb, 5.2), GJ(-2.31, vm, 7.2)]], f'gj_gable_face_{g}', 'render_white')
        tr = []
        for (a, za), (b, zb) in (((va, 5.2), (vm, 7.2)), ((vm, 7.2), (vb, 5.2))):
            tr.append([GJ(-2.33, a, za - 0.25), GJ(-2.33, b, zb - 0.25), GJ(-2.33, b, zb), GJ(-2.33, a, za)])
        faces_obj(tr, f'gj_gable_trim_{g}', 'black')
    faces_obj([gj_wall_v(-2.33, -12.6, -15.4, 0.9, 3.3)], 'gj_entry_doors', 'glass')
    for k in range(5):
        gj_box(-3.3 + 0.2 * k, -2.3, -15.6, -12.4, 0.0, 0.18 * (k + 1), f'gj_entry_step_{k}', 'concrete')
    # BULLDOGS mural wall (hand-made: white arched panel, red lettering, club badge, red edge panels)
    va, vb = -19.6, -26.5
    gj_box(-2.3, 0.4, vb, va, 0.0, 5.4, 'gj_mural_wall', 'render_white')
    arch = [GJ(-2.31, va, 5.4)] + [GJ(-2.31, (va + vb) / 2 + (vb - va) / 2 * _m.cos(_m.pi * k / 16), 5.4 + 0.8 * _m.sin(_m.pi * k / 16)) for k in range(17)] + [GJ(-2.31, vb, 5.4)]
    faces_obj([arch[::-1]], 'gj_mural_arch', 'render_white')
    faces_obj([gj_wall_v(-2.32, va - 0.1, va - 0.7, 0.3, 4.0), gj_wall_v(-2.32, vb + 0.7, vb + 0.1, 0.3, 4.0)], 'gj_mural_red', 'red')
    gj_text_u('BULLDOGS', -2.33, (va + vb) / 2, 5.25, 0.85, 'red', 'gj_mural_text')
    gj_disc(-2.33, (va + vb) / 2, 3.6, 0.75, 'gj_mural_badge', 'silver', face='u')
    faces_obj([[GJ(-2.35, (va + vb) / 2 - 0.45, 3.95), GJ(-2.35, (va + vb) / 2 + 0.45, 3.95), GJ(-2.35, (va + vb) / 2, 3.1)]], 'gj_mural_badge_v', 'red')
