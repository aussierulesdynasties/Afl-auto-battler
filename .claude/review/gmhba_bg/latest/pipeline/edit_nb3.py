import json, math
g=json.load(open('spec/gmhba.json')); P=[]
for _,x,y,a,L,W in g['netball_courts']['courts']:
    u=(math.cos(a),math.sin(a)); w=(-u[1],u[0]); X,Y=L/2+2.5,W/2+2.5
    P+=[(x+u[0]*s*X+w[0]*t*Y, y+u[1]*s*X+w[1]*t*Y) for s in(-1,1) for t in(-1,1)]
P=sorted(set(P))
def cr(o,a,b): return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
lo=[];up=[]
for p in P:
    while len(lo)>=2 and cr(lo[-2],lo[-1],p)<=0: lo.pop()
    lo.append(p)
for p in reversed(P):
    while len(up)>=2 and cr(up[-2],up[-1],p)<=0: up.pop()
    up.append(p)
H=[[round(a,2),round(b,2)] for a,b in lo[:-1]+up[:-1]]
g['netball_courts']['slab']=H
g['paint_poly']=[['court_blue',H] if p[0]=='court_blue' else p for p in g['paint_poly']]
json.dump(g,open('spec/gmhba.json','w'),indent=1); print(len(H))
