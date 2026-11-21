import json
from shapely.geometry import Polygon
p='spec/peoplefirst.json'; s=json.load(open(p))
s['palette']['court_blue']=[104,152,203]; s['palette']['synth']=[38,82,32]; s['palette']['synth_dark']=[39,51,29]
n=0
for e in s['paint_poly']:
    if (e[0]=="water" if isinstance(e,list) else e.get("kind")=="water") and n<5:
        pts=e[1] if isinstance(e,list) else e['pts']
        g=Polygon(pts).buffer(5.5 if n==4 else 3.5,join_style=2)
        q=[[round(x,1),round(y,1)] for x,y in list(g.exterior.coords)[:-1]]
        if isinstance(e,list): e[1]=q
        else: e['pts']=q
        n+=1
json.dump(s,open(p,'w'),indent=1); print('ponds',n)
