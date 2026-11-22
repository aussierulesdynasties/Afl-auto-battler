import json
p='spec/adelaide.json'; s=json.load(open(p))
s['paint_poly']=[q for q in s['paint_poly'] if q[0]!='court_blue']
s['palette'].pop('court_blue',None); s.pop('water_tex',None)
s['palette']['court_navy']=[52,66,120]; s['palette']['court_play']=[40,90,150]
s['court_slabs']=True; s['court_col']='court_navy'
json.dump(s,open(p,'w'),indent=1); print([q[0] for q in s['paint_poly']])
