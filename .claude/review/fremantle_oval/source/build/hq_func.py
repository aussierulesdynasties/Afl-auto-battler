
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
HQ_ZE = HQ_ZB + 6.6    # eaves (ground floor 3.3, upper floor to eaves 3.3)
HQ_RISE = 2.5          # gable rise above the eaves
HQ_W, HQ_WBIG = 5.2, 15.0

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
    zb, ze, zr = HQ_ZB, HQ_ZE, HQ_ZE + HQ_RISE
    spans = [(k * HQ_W, (k + 1) * HQ_W) for k in range(8)] + [(8 * HQ_W, 8 * HQ_W + HQ_WBIG)]
    roof, sof, barge, glassq, cols, mull, solar, cream, dark, slab, rail, railg, plinth, bank = ([] for _ in range(14))
    for k, (s0, s1) in enumerate(spans):
        A = Vector(hq_at(s0)); B = Vector(hq_at(s1))
        if k == 8:   # past the OSM front's end: carry on along the last chord
            a_, b_ = Vector(HQ_FRONT[-2]), Vector(HQ_FRONT[-1]); t_ = (b_ - a_).normalized()
            B = A + t_ * HQ_WBIG
        w = (B - A).length; u = (B - A) / w; n = Vector((-u.y, u.x))   # n points into the building (away from the oval)
        def P(a, d, z): p = A + u * a + n * d; return (p.x, p.y, z)
        big = k == 8
        rise = HQ_RISE + 0.6 if big else HQ_RISE
        depth = 10.0 if big else (13.0 if k < 4 else 8.0)
        oh = 1.0                                   # roof overhang in front of the front line
        zr_ = ze + rise; h = w / 2
        # roof slopes (white corrugated) and white soffit just under them
        roof += [[P(0, -oh, ze), P(h, -oh, zr_), P(h, depth, zr_), P(0, depth, ze)],
                 [P(h, -oh, zr_), P(w, -oh, ze), P(w, depth, ze), P(h, depth, zr_)]]
        sof += [[P(0, -oh, ze - 0.12), P(0, depth, ze - 0.12), P(h, depth, zr_ - 0.12), P(h, -oh, zr_ - 0.12)],
                [P(h, -oh, zr_ - 0.12), P(h, depth, zr_ - 0.12), P(w, depth, ze - 0.12), P(w, -oh, ze - 0.12)]]
        # green bargeboards on the front rake and the back rake
        for dd in (-oh, depth):
            barge += [[P(0, dd, ze - 0.3), P(h, dd, zr_ - 0.3), P(h, dd, zr_ + 0.02), P(0, dd, ze + 0.02)],
                      [P(h, dd, zr_ - 0.3), P(w, dd, ze - 0.3), P(w, dd, ze + 0.02), P(h, dd, zr_ + 0.02)]]
        # green valley columns at the front line, full height to the eaves
        for a in ((0.0, w) if k in (0, 8) else (0.0,)):
            c = A + u * a
            cols.append(((c.x, c.y), zb - 0.4, ze))
        # solar panels on the west slope (a h..w) of gables 2-6 (k 1..5): portrait panels in a grid, small gaps
        if 1 <= k <= 5:
            Ls = math.hypot(h, rise)
            for i in range(int((Ls - 0.5) / 1.02)):
                f0 = (0.25 + i * 1.02) / Ls; f1 = f0 + 0.98 / Ls
                for j in range(int((depth - 1.6) / 1.72)):
                    d0 = -oh + 0.5 + j * 1.72; d1 = d0 + 1.68
                    def SP(f, d): return P(h + h * f, d, zr_ - rise * f + 0.05)
                    solar.append([SP(f0, d0), SP(f1, d0), SP(f1, d1), SP(f0, d1)])
        if k < 4 or big:
            dv = 1.0 if big else 0.0                  # the entrance hall glazing sits a metre back
            glassq.append([P(0, dv, zb), P(w, dv, zb), P(w, dv, ze - 0.12), P(0, dv, ze - 0.12)])
            glassq.append([P(0, dv, ze - 0.12), P(w, dv, ze - 0.12), P(h, dv, zr_ - 0.2)])
            nm = 6 if big else 3
            for i in range(1, nm):
                a = w * i / nm; zt = ze - 0.12 + (zr_ - ze) * (1 - abs(a - h) / h) - 0.1
                mull.append([P(a - 0.05, dv - 0.03, zb), P(a + 0.05, dv - 0.03, zb), P(a + 0.05, dv - 0.03, zt), P(a - 0.05, dv - 0.03, zt)])
            for zt in (zb + 2.3, zb + 4.6):
                mull.append([P(0, dv - 0.03, zt - 0.05), P(w, dv - 0.03, zt - 0.05), P(w, dv - 0.03, zt + 0.05), P(0, dv - 0.03, zt + 0.05)])
            plinth.append([P(0, -0.3, zb - 0.9), P(w, -0.3, zb - 0.9), P(w, -0.3, zb), P(0, -0.3, zb)])
            plinth.append([P(0, -0.3, zb), P(w, -0.3, zb), P(w, dv, zb), P(0, dv, zb)])
        else:
            # two storeys: cream ground floor set back 2 m under the balcony, glass upper floor behind the rail
            sb = 2.0; zf = zb + 3.3
            cream.append([P(0, sb, zb), P(w, sb, zb), P(w, sb, zf), P(0, sb, zf)])
            dark.append([P(w * 0.30, sb - 0.02, zb), P(w * 0.30 + 1.2, sb - 0.02, zb), P(w * 0.30 + 1.2, sb - 0.02, zb + 2.3), P(w * 0.30, sb - 0.02, zb + 2.3)])
            dark.append([P(w * 0.62, sb - 0.02, zb + 1.0), P(w * 0.62 + 1.3, sb - 0.02, zb + 1.0), P(w * 0.62 + 1.3, sb - 0.02, zb + 2.3), P(w * 0.62, sb - 0.02, zb + 2.3)])
            slab += [[P(0, -0.2, zf), P(w, -0.2, zf), P(w, -0.2, zf + 0.3), P(0, -0.2, zf + 0.3)],
                     [P(0, -0.2, zf + 0.3), P(w, -0.2, zf + 0.3), P(w, sb, zf + 0.3), P(0, sb, zf + 0.3)],
                     [P(0, -0.2, zf), P(0, sb, zf), P(w, sb, zf), P(w, -0.2, zf)]]
            rail.append([P(0, -0.1, zf + 1.3), P(w, -0.1, zf + 1.3), P(w, -0.1, zf + 1.38), P(0, -0.1, zf + 1.38)])
            rail.append([P(0, -0.1, zf + 0.3), P(w, -0.1, zf + 0.3), P(w, -0.1, zf + 0.36), P(0, -0.1, zf + 0.36)])
            for a in np.arange(0.06, w, 0.14):
                railg.append([P(a - 0.015, -0.1, zf + 0.36), P(a + 0.015, -0.1, zf + 0.36), P(a + 0.015, -0.1, zf + 1.3), P(a - 0.015, -0.1, zf + 1.3)])
            glassq.append([P(0, sb, zf + 0.3), P(w, sb, zf + 0.3), P(w, sb, ze - 0.12), P(0, sb, ze - 0.12)])
            glassq.append([P(0, sb, ze - 0.12), P(w, sb, ze - 0.12), P(h, sb, zr_ - 0.2)])
            for a in (w / 3, 2 * w / 3):
                mull.append([P(a - 0.05, sb - 0.03, zf + 0.3), P(a + 0.05, sb - 0.03, zf + 0.3), P(a + 0.05, sb - 0.03, ze), P(a - 0.05, sb - 0.03, ze)])
            plinth.append([P(0, -0.3, zb - 0.9), P(w, -0.3, zb - 0.9), P(w, -0.3, zb), P(0, -0.3, zb)])
            plinth.append([P(0, -0.3, zb), P(w, -0.3, zb), P(w, sb, zb), P(0, sb, zb)])
        # grass bank in front, from the paving up to the plinth (g18)
        bank.append([P(0, -7.5, 0.02), P(w, -7.5, 0.02), P(w, -0.3, zb - 0.9 + 0.9 * 0.0 + 0.0), P(0, -0.3, zb - 0.9)])
        if k == 4:   # the small scoreboard on the ground floor front by the glass hall (g18, g34)
            hq_sb = (P(0.4, -0.25, zb + 1.4), P(2.9, -0.25, zb + 1.4), P(2.9, -0.25, zb + 3.1), P(0.4, -0.25, zb + 3.1))
        if big:      # purple entrance porch at the west end of the wide gable (g34): a small white gable on green posts
            pa, pb = w - 4.6, w - 0.8; ph = (pa + pb) / 2; pz, pr = zb + 3.0, zb + 4.3
            pq = [[P(pa, -1.8, pz), P(ph, -1.8, pr), P(ph, 1.0, pr), P(pa, 1.0, pz)],
                  [P(ph, -1.8, pr), P(pb, -1.8, pz), P(pb, 1.0, pz), P(ph, 1.0, pr)]]
            faces_obj(pq, 'hq_porch_roof', 'roof_white')
            faces_obj([[P(pa + 0.2, -1.82, pz + 0.05), P(pb - 0.2, -1.82, pz + 0.05), P(ph, -1.82, pr - 0.1)]], 'hq_porch_sign', 'club_purple')
            for k2, a in enumerate((pa + 0.15, pb - 0.15)):
                c = A + u * a + n * -1.7
                cols.append(((c.x, c.y), zb, pz))
            hq_bigP = P
    for k2, ((x, y), z0, z1) in enumerate(cols):
        box((x, y, (z0 + z1) / 2), (0.26, 0.26, z1 - z0), f'hq_col_{k2}', 'green')
    faces_obj(roof, 'hq_roof', 'roof_white'); faces_obj(sof, 'hq_soffit', 'sign_white')
    faces_obj(barge, 'hq_bargeboards', 'green'); faces_obj(glassq, 'hq_glass', 'glass')
    faces_obj(mull, 'hq_mullions', 'green'); faces_obj(solar, 'hq_solar', 'solar')
    faces_obj(cream, 'hq_ground_floor', 'render_cream'); faces_obj(dark, 'hq_doors', 'dark')
    faces_obj(slab, 'hq_balcony', 'render_white'); faces_obj(rail, 'hq_rail', 'green')
    faces_obj(railg, 'hq_balusters', 'green'); faces_obj(plinth, 'hq_plinth', 'concrete')
    faces_obj(bank, 'hq_bank', 'grass_edge')
    q = list(hq_sb)
    faces_obj([q], 'hq_scoreboard_frame', 'sb_yellow')
    c0 = Vector(q[0]); c2 = Vector(q[2]); inset = (c2 - c0) * 0.06
    faces_obj([[tuple(Vector(q[0]) + Vector((inset.x, inset.y, inset.z)) + Vector((0, 0, 0))),
                tuple(Vector(q[1]) + Vector((-inset.x, -inset.y, inset.z))),
                tuple(Vector(q[2]) - Vector((inset.x, inset.y, inset.z))),
                tuple(Vector(q[3]) + Vector((inset.x, inset.y, -inset.z)))]], 'hq_scoreboard_face', 'black')
    # the rest of the footprint: flat metal roof just under the eaves, cream render walls round the back and the west
    fp = [tuple(p) for p in G['ways']['292154259']][:-1]
    faces_obj([[(x, y, ze - 0.3) for x, y in fp]], 'hq_flat_roof', 'roof_cream')
    wq = []
    for i in range(len(fp)):
        (x1, y1), (x2, y2) = fp[i], fp[(i + 1) % len(fp)]
        if y1 > -100.5 and y2 > -100.5 and x1 > -22.0 and x2 > -22.0: continue   # the gabled front
        wq.append([(x1, y1, 0.0), (x2, y2, 0.0), (x2, y2, ze - 0.3), (x1, y1, ze - 0.3)])
    faces_obj(wq, 'hq_walls', 'render_cream')
    # punched windows on the west (cream office) face, two floors (g34)
    win = []
    a_, b_ = Vector((-27.3, -86.6)), Vector((-44.5, -110.8)); t_ = (b_ - a_).normalized(); nn = Vector((-t_.y, t_.x))
    for zc in (2.2, 5.4):
        for s in np.arange(9.0, 29.0, 2.6):
            c = a_ + t_ * s - nn * 0.04
            win.append([(c.x - t_.x * 0.5, c.y - t_.y * 0.5, zc - 0.6), (c.x + t_.x * 0.5, c.y + t_.y * 0.5, zc - 0.6),
                        (c.x + t_.x * 0.5, c.y + t_.y * 0.5, zc + 0.6), (c.x - t_.x * 0.5, c.y - t_.y * 0.5, zc + 0.6)])
    faces_obj(win, 'hq_windows', 'glass')
    # rooftop plant on the flat roof (a02)
    for k2, (x, y) in enumerate(((-10, -112), (-2, -115), (6, -118), (-18, -108), (14, -116))):
        box((x, y, ze - 0.3 + 0.4), (1.4, 1.0, 0.8), f'hq_plant_{k2}', 'aircon')
