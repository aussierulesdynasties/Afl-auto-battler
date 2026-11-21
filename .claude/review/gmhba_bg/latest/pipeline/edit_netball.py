import json, math, numpy as np
g=json.load(open('spec/gmhba.json'))
navy=[p[1] for p in g['paint_poly'] if p[0]=='court_navy']; slab=[p[1] for p in g['paint_poly'] if p[0]=='court_blue'][0]
C=[]
for b in navy:
    b=np.array(b); c=b.mean(0); e=b[1]-b[0]; ang=math.atan2(e[1],e[0]); C.append(['netball',round(float(c[0]),2),round(float(c[1]),2),ang,30.5,15.25])
g['paint_poly']=[p for p in g['paint_poly'] if p[0]!='court_navy']
g['netball_courts']={'slab':slab,'courts':C}; g['palette']['netball']=[60,80,118]
json.dump(g,open('spec/gmhba.json','w'),indent=1)
p='prep.py'; s=open(p,encoding='utf-8',newline='').read()
a="# tennis courts: courts within 6 m"
b="""if spec.get('netball_courts'):   # Kardinia netball block (outline traced on the satellite; not mapped in OSM): slab + courts as geometry
    _nb = spec['netball_courts']; json.dump({'slabs': [['court_blue', _nb['slab']]], 'courts': _nb['courts'], 'pal': {'court_blue': PAL['court_blue'], 'netball': PAL['netball']}}, open(os.path.join(OUT, 'courts.json'), 'w'))
"""
assert a in s; s=s.replace(a,b+a,1); open(p,'w',encoding='utf-8',newline='').write(s)
p='scene.py'; s=open(p,encoding='utf-8',newline='').read()
a="        if L_ < 23.5 or W_ < 10.8: continue"
b="""        if k == 'netball':   # netball (INF): 30.5 x 15.25 m, thirds, 0.9 m centre circle, 4.9 m goal semicircles; navy court on the blue slab
            ux, uy = math.cos(ang), math.sin(ang); wx, wy = -uy, ux; z = float(height(np.array([cx]), np.array([cy]))[0]) + 0.08; nc += 1
            X, Y = 15.25, 7.625
            mk_obj('bg_netball_%d' % nc, [(cx + ux * a_ * X + wx * b_ * Y, cy + uy * a_ * X + wy * b_ * Y, z - 0.02) for a_, b_ in [(-1, -1), (1, -1), (1, 1), (-1, 1)]], [[0, 1, 2, 3]], mats['netball'])
            for a_, b_, c_, d_ in [(-X, -Y, X, -Y), (-X, Y, X, Y), (-X, -Y, -X, Y), (X, -Y, X, Y), (-X / 3, -Y, -X / 3, Y), (X / 3, -Y, X / 3, Y)]:
                seg(cx, cy, ux, uy, a_, b_, c_, d_, z)
            for r_, x0_, t0, t1 in [(0.45, 0, 0, 2 * math.pi), (4.9, -X, -math.pi / 2, math.pi / 2), (4.9, X, math.pi / 2, 3 * math.pi / 2)]:
                pts = [(x0_ + r_ * math.cos(t), r_ * math.sin(t)) for t in np.linspace(t0, t1, 24)]
                for (a_, b_), (c_, d_) in zip(pts, pts[1:]): seg(cx, cy, ux, uy, a_, b_, c_, d_, z)
            continue
""" + a
assert a in s; s=s.replace(a,b,1); open(p,'w',encoding='utf-8',newline='').write(s); print('ok')
