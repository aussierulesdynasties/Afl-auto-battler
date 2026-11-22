f='scene.py'; s=open(f,newline='').read()
def rep(a,b):
    global s; assert a in s, a[:60]; s=s.replace(a,b,1)
rep("""    verts, faces, cols, uvs = [], [], [], []
    walls = [lin(c) for c in PAL['walls_' + cls]]""","""    verts, faces, cols, uvs = [], [], [], []
    RF = {'metal': [[], [], [], []], 'tile': [[], [], [], []]}   # roof meshes: verts, faces, cols, uvs
    walls = [lin(c) for c in PAL['walls_' + cls]]""")
rep("""        if pitched:
            apex = len(verts); verts.append((cxy[0], cxy[1], top + rh))
            for i in range(k):
                faces.append((s0 + k + i, s0 + k + (i + 1) % k, apex)); cols += [rc] * 3; uvs += [(0.01, 0.01)] * 3
        else:
            faces.append(tuple(s0 + k + i for i in range(k))); cols += [rc] * k; uvs += [(0.01, 0.01)] * k""","""        # roof: own mesh, hand-made texture, planar UVs along the building's longest side (one tile = 3.04 m)
        E = np.diff(np.vstack([P, P[:1]]), axis=0); e = E[np.argmax(np.hypot(E[:, 0], E[:, 1]))]; th_ = math.atan2(e[1], e[0])
        ct, st = math.cos(th_), math.sin(th_)
        src = b.get('roof_c'); kind = 'tile' if (cls == 'house' and PAL['roofs_house'][b['roof'] % len(PAL['roofs_house'])][0] > 1.3 * PAL['roofs_house'][b['roof'] % len(PAL['roofs_house'])][1]) else 'metal'
        rv, rf, rcl, ruv = RF[kind]; r0 = len(rv)
        def ruv_(x, y): return ((x * ct + y * st) / 3.04, (-x * st + y * ct) / 3.04)
        for x, y in P: rv.append((x, y, top)); ruv.append(ruv_(x, y))
        if pitched:
            rv.append((cxy[0], cxy[1], top + rh)); ruv.append(ruv_(cxy[0], cxy[1]))
            for i in range(k):
                rf.append((r0 + i, r0 + (i + 1) % k, r0 + k)); rcl += [rc] * 3
        else:
            rf.append(tuple(r0 + i for i in range(k))); rcl += [rc] * k""")
rep("""    if not faces: return
    ob = mk_obj('bg_bld_' + cls, verts, faces, mat_facade('facade_' + cls, os.path.join(HERE, 'tex', tex)))
    set_corner_col(ob.data, np.concatenate([np.array(cols), np.ones((len(cols), 1))], 1))
    set_uv(ob.data, uvs)""","""    if not faces: return
    ob = mk_obj('bg_bld_' + cls, verts, faces, mat_facade('facade_' + cls, os.path.join(HERE, 'tex', tex)))
    set_corner_col(ob.data, np.concatenate([np.array(cols), np.ones((len(cols), 1))], 1))
    set_uv(ob.data, uvs)
    for kind, (rv, rf, rcl, ruv) in RF.items():
        if not rf: continue
        ro = mk_obj('bg_roof_%s_%s' % (cls, kind), rv, rf, mat_facade('roof_%s_%s' % (cls, kind), os.path.join(HERE, 'tex', 'roof_%s.png' % kind)))
        set_corner_col(ro.data, np.concatenate([np.array(rcl), np.ones((len(rcl), 1))], 1))
        set_uv(ro.data, [ruv[i] for f_ in rf for i in f_])""")
open(f,'w',newline='').write(s); print('ok')
