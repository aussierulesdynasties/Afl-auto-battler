s=open('accor_landmarks.py',newline='').read()
def rep(a,b):
    global s; assert a in s,a[:40]; s=s.replace(a,b)
# arena roof 33 -> 39 m (sources), fascia 20 -> 33
rep("z0 + 30 + 6 * (1 - f0 ** 2), z0 + 30 + 6 * (1 - f1 ** 2)","z0 + 33 + 6 * (1 - f0 ** 2), z0 + 33 + 6 * (1 - f1 ** 2)")
rep("(*q, z0 + 30), (*p, z0 + 30), [(0, 0), (1, 0), (1, 1.2), (0, 1.2)]","(*q, z0 + 33), (*p, z0 + 33), [(0, 0), (1, 0), (1, 1.2), (0, 1.2)]")
# 18 masts (Wikipedia: 18 steel masts, cables from each mast top to the roof centre): 9 a side
rep("for m in range(6):\n                s = -0.62 * hl + m * (1.24 * hl / 5)","for m in range(9):\n                s = -0.66 * hl + m * (1.32 * hl / 8)")
rep("_beam2('white', (f_[0], f_[1], z0 + 30), top, 0.8)\n                for f in (0.75, 0.45): q = c + ax_ * s * f + nx_ * side * hw * f; _beam2('white', top, (q[0], q[1], z0 + 30 + 6 * (1 - f ** 2)), 0.2)",
    "_beam2('white', (f_[0], f_[1], z0 + 33), top, 0.8)\n                _beam2('white', top, (c[0], c[1], z0 + 39), 0.12)\n                for f in (0.75, 0.45): q = c + ax_ * s * f + nx_ * side * hw * f; _beam2('white', top, (q[0], q[1], z0 + 33 + 6 * (1 - f ** 2)), 0.15)")
# Dome: smooth sheeting with 5 ring steps, blue drum with 16 white pilasters, dark glass band + wide flat cap (ausleisure photo 2026-11-20)
rep("""            for (rr, za, zb) in ((Rr, z0, z0 + 12), (8.4, z0 + 38, z0 + 42)):
                p0 = (c[0] + rr * math.cos(t0), c[1] + rr * math.sin(t0)); p1 = (c[0] + rr * math.cos(t1), c[1] + rr * math.sin(t1))
                _quadm('dome', (*p0, za), (*p1, za), (*p1, zb), (*p0, zb), [(0, 0), (0.6, 0), (0.6, 1), (0, 1)])""",
"""            for (rr, za, zb, km) in ((Rr, z0, z0 + 12, 'drum'), (15.0, z0 + 37, z0 + 40, 'glass')):
                p0 = (c[0] + rr * math.cos(t0), c[1] + rr * math.sin(t0)); p1 = (c[0] + rr * math.cos(t1), c[1] + rr * math.sin(t1))
                _quadm(km, (*p0, za), (*p1, za), (*p1, zb), (*p0, zb), [(0, 0), (1, 0), (1, 1), (0, 1)] if km == 'drum' else [(0, 0), (0.3, 0), (0.3, 0.4), (0, 0.4)])
            p0 = (c[0] + 16.5 * math.cos(t0), c[1] + 16.5 * math.sin(t0)); p1 = (c[0] + 16.5 * math.cos(t1), c[1] + 16.5 * math.sin(t1))
            _quadm('white', (*p0, z0 + 40), (*p1, z0 + 40), (c[0], c[1], z0 + 42), (c[0], c[1], z0 + 42), [(0, 0), (1, 0), (1, 1), (0, 1)])
            _quadm('white', (*p0, z0 + 39.4), (*p1, z0 + 39.4), (*p1, z0 + 40), (*p0, z0 + 40), [(0, 0), (1, 0), (1, 1), (0, 1)])
        for i in range(16):   # white pilasters on the drum
            t = 2 * math.pi * i / 16; q = (c[0] + (Rr + 0.6) * math.cos(t), c[1] + (Rr + 0.6) * math.sin(t)); _beam2('white', (*q, z0), (*q, z0 + 13), 1.4)""")
# dome stops at the glass band r 15 m (z 37)
rep("ph = ph * (80 / 90); r_ = Rr * math.cos(ph) / math.cos(0)","ph = ph * (72 / 90); r_ = Rr * math.cos(ph)")
rep("z0 + 12 + 26 * math.sin(ph) / math.sin(math.radians(80)))","z0 + 12 + 25 * math.sin(ph) / math.sin(math.radians(72)))")
# station: separate vaults - each shell bulges along its length too, gap 1.2 m between shells
rep("s0 = -L / 2 + k * seg - 2.0; s1 = s0 + seg + 4.0      # shells overlap 2 m each end","s0 = -L / 2 + k * seg + 0.6; s1 = s0 + seg - 1.2      # separate shells, 1.2 m gap (aerial: 18 distinct vaults)")
rep("""            for e in range(16):
                a0, a1 = math.pi * e / 16, math.pi * (e + 1) / 16
                def sp(s, a): q = c + ax * s + nx * (-W / 2 * math.cos(a)); return (q[0], q[1], z0 + 8 + 12 * math.sin(a))
                _quadm('shell', sp(s0, a0), sp(s1, a0), sp(s1, a1), sp(s0, a1), [(0, a0 * W / 16), (seg / 8, a0 * W / 16), (seg / 8, a1 * W / 16), (0, a1 * W / 16)])""",
"""            for g in range(6):
              sa, sb = s0 + (s1 - s0) * g / 6, s0 + (s1 - s0) * (g + 1) / 6
              for e in range(16):
                a0, a1 = math.pi * e / 16, math.pi * (e + 1) / 16
                def sp(s, a): t_ = (s - s0) / (s1 - s0); q = c + ax * s + nx * (-W / 2 * math.cos(a)); return (q[0], q[1], z0 + 8 + (9 + 3 * math.sin(math.pi * t_)) * math.sin(a) + 1.5 * math.sin(math.pi * t_))
                _quadm('shell', sp(sa, a0), sp(sb, a0), sp(sb, a1), sp(sa, a1), [(sa / 8, a0 * W / 16), (sb / 8, a0 * W / 16), (sb / 8, a1 * W / 16), (sa / 8, a1 * W / 16)])""")
rep("'white': mat_img(","'drum': mat_img('acc_drum', os.path.join(HERE, 'tex', 'acc_drum.png'), 0.3),\n             'white': mat_img(")
open('accor_landmarks.py','w',newline='').write(s); print('ok')
t=open('mk_accor_lm_tex.py',newline='').read()
t=t.replace("for x in range(0, 512, 128): a[:, x:x + 6] *= 0.82\nfor y in range(0, 512, 256): a[y:y + 4] *= 0.88","for y in range(0, 512, 256): a[y:y + 5] *= 0.86   # ring steps only, no meridian ribs (photo)")
t=t.replace("save(a, 'acc_glass')","save(a, 'acc_glass')\n# Dome drum: blue cladding panels, 3 m panel lines\na = np.full((256, 256, 3), (70, 104, 140), np.float32) + rng.normal(0, 2, (256, 256, 1))\nfor x in range(0, 256, 96): a[:, x:x + 2] *= 0.8\nsave(a, 'acc_drum')")
open('mk_accor_lm_tex.py','w',newline='').write(t)
