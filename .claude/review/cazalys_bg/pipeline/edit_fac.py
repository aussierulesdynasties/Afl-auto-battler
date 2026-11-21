s=open('scene.py',newline='').read()
old="""        per = 0.0
        for i in range(k):
            j = (i + 1) % k
            L = float(np.hypot(*(P[j] - P[i])))
            faces.append((s0 + i, s0 + j, s0 + k + j, s0 + k + i))
            cols += [wc] * 4
            u0, u1 = per / tw, (per + L) / tw
            v0, v1 = -1.0 / th, (top + par - base - 1.0) / th
            uvs += [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
            per += L
"""
new="""        per = 0.0
        if ATLAS:   # own facade: one hand-painted atlas cell per building, walls split into bays x storeys mapped to it
            del verts[s0:]; cell = (b.get('id', len(verts)) * 7919 + int(rng.integers(0, 8))) % 8 + (0 if cls == 'house' else 8)
            cu, cv_ = (cell % 4) / 4, 1 - (cell // 4 + 1) / 4; e_ = 2 / 1024
            ns = max(1, int(round((top + par - base - 1.0) / 3.2)))
            for i in range(k):
                j = (i + 1) % k; L = float(np.hypot(*(P[j] - P[i])))
                if L < 0.05: continue
                nb = max(1, int(round(L / 3.6)))
                for bi in range(nb):
                    a0 = P[i] + (P[j] - P[i]) * (bi / nb); a1 = P[i] + (P[j] - P[i]) * ((bi + 1) / nb)
                    for si in range(ns):
                        z0 = base + 1.0 + (top + par - base - 1.0) * si / ns; z1 = base + 1.0 + (top + par - base - 1.0) * (si + 1) / ns
                        if si == 0: z0 = base
                        o = len(verts); verts += [(a0[0], a0[1], z0), (a1[0], a1[1], z0), (a1[0], a1[1], z1), (a0[0], a0[1], z1)]
                        faces.append((o, o + 1, o + 2, o + 3)); cols += [wc] * 4
                        u0, u1 = cu + e_, cu + 0.25 - e_; v0, v1 = cv_ + e_, cv_ + 0.25 - e_
                        uvs += [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
        else:
          for i in range(k):
            j = (i + 1) % k
            L = float(np.hypot(*(P[j] - P[i])))
            faces.append((s0 + i, s0 + j, s0 + k + j, s0 + k + i))
            cols += [wc] * 4
            u0, u1 = per / tw, (per + L) / tw
            v0, v1 = -1.0 / th, (top + par - base - 1.0) / th
            uvs += [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
            per += L
"""
assert old in s; s=s.replace(old,new,1)
s=s.replace("def build_class(cls, tex, tw, th):\n","def build_class(cls, tex, tw, th):\n    ATLAS = spec.get('facade_atlas') and cls in ('house', 'block')\n    if ATLAS: tex = spec['facade_atlas']\n",1)
open('scene.py','w',newline='').write(s)
