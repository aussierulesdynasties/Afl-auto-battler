import re
base=r'D:/Temp/claude/b5e56bf702cd3703/4ee81fc3-6cf4-400f-9ad6-28a5df4e19ee/scratchpad/proto/'
s=open(base+'prep.py',encoding='utf-8').read()
s=s.replace("PX = spec['ground_m_per_px']; N = int(2 * NEAR / PX)","SS = spec.get('ground_ss', 2); PX = spec['ground_m_per_px'] / SS; N = int(2 * NEAR / PX)")
s=s.replace("Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(os.path.join(OUT, 'ground.png'))","Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((N // SS, N // SS), Image.LANCZOS).save(os.path.join(OUT, 'ground.png'))")
open(base+'prep.py','w',encoding='utf-8',newline='').write(s)
s=open(base+'scene.py',encoding='utf-8').read()
s=s.replace(""" 'ghost_gum': (3.2, 8.0, 0.8, 6.0, 0.25, (104, 120, 70), (232, 226, 214), 1),
 'red_gum': (6.0, 13.0, 0.7, 9.0, 0.5, (88, 104, 68), (150, 144, 134), 2),
 'mulga': (1.6, 1.8, 0.75, 0.9, 0.12, (120, 128, 82), (90, 70, 56), 1),
 'elm': (7.0, 14.0, 0.85, 7.0, 0.5, (74, 112, 54), (76, 64, 54), 2),
 'plane': (6.0, 12.0, 0.9, 6.5, 0.4, (90, 128, 62), (150, 140, 120), 2),""",""" 'ghost_gum': (3.4, 8.0, 0.7, 6.5, 0.22, (132, 140, 96), (236, 230, 218), 1),
 'red_gum': (5.5, 12.0, 0.6, 9.0, 0.45, (112, 122, 86), (160, 152, 140), 1),
 'mulga': (1.5, 1.7, 0.7, 0.9, 0.1, (134, 132, 94), (96, 76, 60), 1),
 'elm': (6.5, 14.0, 0.85, 7.0, 0.5, (82, 116, 58), (76, 64, 54), 1),
 'plane': (5.5, 12.0, 0.9, 6.5, 0.4, (98, 130, 68), (150, 140, 120), 1),""")
# three-blob crowns
s=s.replace("""        o = len(verts)
        Cv = cv * [cr * s, cr * s, cr * s * sq]
        Cv = np.stack([Cv[:, 0] * c - Cv[:, 1] * sn, Cv[:, 0] * sn + Cv[:, 1] * c, Cv[:, 2]], 1) + [x, y, z0 + ch * s]
        verts += Cv.tolist(); faces += [tuple(o + q for q in f) for f in cf]
        tint = lin(ccol) * (1 + 0.16 * (rng.random() - 0.5))
        cols += [tint] * (3 * len(cf))""","""        tint = lin(ccol) * (1 + 0.16 * (rng.random() - 0.5))
        for bi in range(3):
            o = len(verts)
            br = cr * s * rng.uniform(0.45, 0.62)
            off = rng.normal(0, 0.42 * cr * s, 2); dz = rng.uniform(-0.25, 0.35) * cr * s
            Cv = cv * [br, br, br * sq]
            Cv = np.stack([Cv[:, 0] * c - Cv[:, 1] * sn, Cv[:, 0] * sn + Cv[:, 1] * c, Cv[:, 2]], 1) + [x + off[0], y + off[1], z0 + ch * s + dz]
            verts += Cv.tolist(); faces += [tuple(o + q for q in f) for f in cf]
            cols += [tint * rng.uniform(0.92, 1.08)] * (3 * len(cf))""")
open(base+'scene.py','w',encoding='utf-8',newline='').write(s)
print('ok')
