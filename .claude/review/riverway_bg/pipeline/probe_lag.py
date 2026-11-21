import bpy, json
s=json.load(open('spec/riverway.json')); P=[p for k,p in s['paint_poly'] if k=='lagoon'][0]
def pip(x,y):
    c=False; j=len(P)-1
    for i in range(len(P)):
        xi,yi=P[i]; xj,yj=P[j]
        if (yi>y)!=(yj>y) and x<(xj-xi)*(y-yi)/(yj-yi)+xi: c=not c
        j=i
    return c
for o in bpy.data.objects:
    if o.type!='MESH': continue
    mw=o.matrix_world; n=0; zs=[]
    for v in o.data.vertices:
        w=mw@v.co
        if w.z>2 and pip(w.x,w.y): n+=1; zs.append(round(w.z,1))
    if n: print('HIT',o.name,n,min(zs),max(zs))
print('PROBE DONE')
