import json, re
p='model/build.py'; s=open(p,encoding='utf-8',newline='').read()
def rep(a,b):
    global s
    assert s.count(a)==1, a[:60]; s=s.replace(a,b)
# roof edge per sector: (drop of outer top below h, fascia bottom below h)
rep("def in_screen(b):", '''def edge(b):
    for b0, b1, dt, db in D.get('roof_edge', []):
        if b0 <= b % 360 < b1: return dt, db
    return 2.0, 4.5


def back_bands(b, z0, z1):
    """Upper back wall bands at bearing b from z0 to z1: dark glass unless a measured block says otherwise."""
    cuts = [(max(z0, a), min(z1, c), m) for b0, b1, a, c, m in D.get('backwall', []) if b0 <= b % 360 < b1 and min(z1, c) > max(z0, a)]
    cuts.sort(); out = []; z = z0
    for a, c, m in cuts:
        if a > z: out.append((z, a, 'glass'))
        out.append((max(a, z), c, m)); z = max(z, c)
    if z < z1: out.append((z, z1, 'glass'))
    return out


def in_screen(b):''')
rep("(rout - 8, zback, matat('t3', b)), (rout - 8, h - 4.5, 'conc_grey'),\n             (min(rfp, rout), h - 4.5, 'roof_soffit')]",
    "(rout - 8, zback, matat('t3', b)), (rout - 8, h - edge(b)[1], 'conc_grey'),\n             (min(rfp, rout), h - edge(b)[1], 'roof_soffit')]")
rep("secs.append(dict(b=b, S=S,", "secs.append(dict(b=b, S=S, ed=edge(b), dk=matat('deck', b) if 'deck' in mats else 'conc_light',")
rep("        mb.face([c0, a1, b1, c1][::-1], 'conc_light')\n",
'''        mb.face([c0, a1, b1, c1][::-1], A['dk'])
        # upper back wall: deck up to the roof's outer fascia, set 1.5 m in from the roof edge
        wa = min(A['rfp'], A['rout']) - 1.5; wb = min(Bs['rfp'], Bs['rout']) - 1.5
        for za, zb, m in back_bands(A['b'], fz, A['h'] - A['ed'][1]):
            mb.face([(*pol(A['b'], wa), za), (*pol(A['b'], wa), zb), (*pol(Bs['b'], wb), zb), (*pol(Bs['b'], wb), za)], m)
''')
rep("zr = lambda s, r: s['h'] - 2.0 * (r - s['rin']) / (s['rout'] - s['rin'])",
    "zr = lambda s, r: s['h'] - s['ed'][0] * (r - s['rin']) / (s['rout'] - s['rin'])")
rep("lambda s: s['rout'], lambda s: s['h'] - 2.0, matat('roof', A['b'])),\n                                     (lambda s: s['rout'], lambda s: s['h'] - 2.0, lambda s: s['rout'], lambda s: s['h'] - 4.5, 'roof_fascia'),\n                                     (lambda s: s['rout'], lambda s: s['h'] - 4.5,",
    "lambda s: s['rout'], lambda s: s['h'] - s['ed'][0], matat('roof', A['b'])),\n                                     (lambda s: s['rout'], lambda s: s['h'] - s['ed'][0], lambda s: s['rout'], lambda s: s['h'] - s['ed'][1], 'roof_fascia'),\n                                     (lambda s: s['rout'], lambda s: s['h'] - s['ed'][1],")
# trusses
rep("""        a, o, h = ri(b)[0], ro(b)[0], rh(b)[0]; return h - 2.0 * (r - a) / (o - a)""",
    """        a, o, h = ri(b)[0], ro(b)[0], rh(b)[0]; return h - edge(b)[0] * (r - a) / (o - a)""")
rep("""    for b in T['b']:
        o = ro(b)[0]; h = rh(b)[0]; r0 = rs(b)[0]; top = P3(b, o - 1.0, h - 2.0 + T['up'])
        mb.beam(P3(b, r0, zroof(b, r0) + 0.3), top, 0.9, 0.9, 'steel_blue')
        for sg in (-1, 1):  # A-frame legs splayed 2.5 m each side along the roof edge
            db = sg * math.degrees(2.5 / o); mb.beam(P3(b + db, o - 1.0, h - 2.0 - T['down']), top, 0.7, 0.7, 'steel_blue')
        mb.beam(P3(b, r0 + 0.5 * (o - r0), zroof(b, r0 + 0.5 * (o - r0)) + 0.2), P3(b, o - 1.0, h - 2.0 - T['down'] * 0.5), 0.5, 0.5, 'steel_blue')
""", """    feet = []
    for b in T['b']:
        o = ro(b)[0]; h = rh(b)[0]; r0 = rs(b)[0]; top = P3(b, o - 1.0, h + T['top'])
        mb.beam(P3(b, r0, zroof(b, r0) + 0.3), top, 0.9, 0.9, 'steel_blue')
        sp = T['splay']; zf = h - T['foot']
        for sg in (-1, 1):  # A-frame legs splayed along the roof edge
            db = sg * math.degrees(sp / o); mb.beam(P3(b + db, o - 1.0, zf), top, 0.7, 0.7, 'steel_blue')
        mb.beam(P3(b, r0 + 0.5 * (o - r0), zroof(b, r0 + 0.5 * (o - r0)) + 0.2), P3(b, o - 1.0, 0.5 * (zf + h + T['top'])), 0.5, 0.5, 'steel_blue')
        feet.append((b, o, zf, h))
    for (b1, o1, z1, h1), (b2, o2, z2, h2) in zip(feet, feet[1:]):  # V ties between neighbouring feet
        bm = 0.5 * (b1 + b2); om = 0.5 * (o1 + o2); zm = 0.5 * (h1 + h2) - T['tie']
        mb.beam(P3(b1 + math.degrees(T['splay'] / o1), o1 - 1.0, z1), P3(bm, om - 1.0, zm), 0.35, 0.35, 'steel_blue')
        mb.beam(P3(b2 - math.degrees(T['splay'] / o2), o2 - 1.0, z2), P3(bm, om - 1.0, zm), 0.35, 0.35, 'steel_blue')
""")
open(p,'w',encoding='utf-8',newline='').write(s)
q='model/mcg.json'; D=json.load(open(q,encoding='utf-8'))
T=D['trusses']; T.pop('up'); T.pop('down'); T.update(top=7.0, foot=5.0, splay=1.4, tie=2.5)
D['roof_edge']=[[60,240,0.8,3.5]]
D['backwall']=[[89,110,0,28,'fac_white'],[129,150,20,28,'fac_grey'],[170,180,0,99,'fac_grey']]
D['mats']['deck']=[[0,330,'conc_light'],[330,360,'roof_grey']]
D['mats']['deck'].insert(0,[0,60,'roof_grey']); D['mats']['deck'][1]=[60,330,'conc_light']
for f in D['facade']:
    if f[0]==250: f[2]=21.0
s=json.dumps(D,indent=1)
open(q,'w',encoding='utf-8',newline='').write(s)
print('ok')
