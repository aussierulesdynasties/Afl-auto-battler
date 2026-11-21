import json
f='prep.py'; s=open(f,newline='').read(); nl='\r\n' if '\r\n' in s else '\n'
a="for px_, py_, pk in spec.get('paint_at', []):"; assert a in s
new=("# surfaces traced from the straight-down satellite (metres, scene frame): [palkey, [[x, y], ...]]"+nl+
"for pk, poly in spec.get('paint_poly', []): dr.polygon(P([tuple(q) for q in poly]), fill=tuple(PAL[pk]))"+nl)
s=s.replace(a,new+a,1)
# courts: each cluster of same-colour courts is one continuous slab (hull), then white court lines
b="# baseball: dirt infield"; assert b in s
court=("# tennis courts: courts within 6 m of each other share one slab (as built), white lines on top"+nl+
"def _hull(pts):"+nl+
"    pts = sorted(set(pts))"+nl+
"    def cr(o, a, b): return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])"+nl+
"    lo, up = [], []"+nl+
"    for p in pts:"+nl+
"        while len(lo) >= 2 and cr(lo[-2], lo[-1], p) <= 0: lo.pop()"+nl+
"        lo.append(p)"+nl+
"    for p in reversed(pts):"+nl+
"        while len(up) >= 2 and cr(up[-2], up[-1], p) <= 0: up.pop()"+nl+
"        up.append(p)"+nl+
"    return lo[:-1] + up[:-1]"+nl+
"if spec.get('court_slabs'):"+nl+
"    CT = []"+nl+
"    for el in js:"+nl+
"        if el['type'] == 'way' and el.get('tags', {}).get('sport') == 'tennis' and 'geometry' in el:"+nl+
"            pts = ring(el)"+nl+
"            if len(pts) >= 4 and pts[0] == pts[-1] and math.hypot(*pts[0]) < 400:"+nl+
"                cx = sum(q[0] for q in pts[:-1]) / (len(pts) - 1); cy = sum(q[1] for q in pts[:-1]) / (len(pts) - 1)"+nl+
"                col = 'court_green'"+nl+
"                for px_, py_, pk in spec.get('paint_at', []):"+nl+
"                    if math.hypot(cx - px_, cy - py_) < 8: col = pk"+nl+
"                CT.append([pts[:-1], col])"+nl+
"    grp = list(range(len(CT)))"+nl+
"    def find(i):"+nl+
"        while grp[i] != i: i = grp[i]"+nl+
"        return i"+nl+
"    for i in range(len(CT)):"+nl+
"        for j in range(i + 1, len(CT)):"+nl+
"            if CT[i][1] == CT[j][1] and min(math.hypot(p[0] - q[0], p[1] - q[1]) for p in CT[i][0] for q in CT[j][0]) < 6: grp[find(i)] = find(j)"+nl+
"    for r in set(find(i) for i in range(len(CT))):"+nl+
"        mem = [CT[i] for i in range(len(CT)) if find(i) == r]"+nl+
"        dr.polygon(P(_hull([p for m in mem for p in m[0]])), fill=tuple(PAL[mem[0][1]]))"+nl+
"    for pts, col in CT:   # boundary line of each court, 5 cm-ish (1 px) white"+nl+
"        dr.line(P(pts + [pts[0]]), fill=(236, 236, 230), width=1)"+nl+
"    print('court slabs', len(set(find(i) for i in range(len(CT)))), 'courts', len(CT))"+nl)
s=s.replace(b,court+b,1)
open(f,'w',newline='').write(s)
f='spec/traeger.json'; d=json.load(open(f))
d['court_slabs']=True
d['paint_poly']=[
 ["lawn", [[-40,108],[0,110],[40,105],[65,90],[82,65],[90,30],[90,-10],[82,-40],[70,-60],[50,-80],[20,-90],[-20,-92],[-55,-85],[-80,-70],[-95,-45],[-98,-10],[-95,20],[-85,60],[-65,90]]],
 ["parking", [[-298,-12],[-250,-22],[-200,-36],[-150,-52],[-138,-60],[-138,-97],[-200,-80],[-250,-67],[-298,-57]]],
 ["lawn", [[-115,-57],[-60,-57],[-60,-97],[-115,-97]]]]
json.dump(d,open(f,'w'),indent=1); print('ok')
