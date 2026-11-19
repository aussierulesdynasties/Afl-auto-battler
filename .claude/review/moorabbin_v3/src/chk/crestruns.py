import bpy,math,json
O=json.load(open(bpy.path.abspath('//build.json')));P=O['pitch'];P=P[:-1] if P[0]==P[-1] else P
cx=sum(p[0] for p in P)/len(P);cy=sum(p[1] for p in P)/len(P)
o=bpy.data.objects['crest_posts'];M=o.matrix_world
A=sorted({round(math.degrees(math.atan2((M@v.co).y-cy,(M@v.co).x-cx))%360,1) for v in o.data.vertices})
runs=[[A[0],A[0]]]
for a in A[1:]:
    if a-runs[-1][1]>2.0:runs.append([a,a])
    else:runs[-1][1]=a
print('RUNS',runs)
for lo_,hi_ in ((103.0,104.0),(138.5,140.0)):
    V=[(M@v.co) for v in o.data.vertices if lo_<=math.degrees(math.atan2((M@v.co).y-cy,(M@v.co).x-cx))%360<=hi_]
    print('END',lo_,round(sum(v.x for v in V)/len(V),2),round(sum(v.y for v in V)/len(V),2),round(max(v.z for v in V),2))
