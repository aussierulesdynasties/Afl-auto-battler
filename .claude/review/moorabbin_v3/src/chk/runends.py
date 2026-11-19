import bpy,math,json
O=json.load(open(bpy.path.abspath('//build.json')));P=O['pitch'];P=P[:-1] if P[0]==P[-1] else P
cx=sum(p[0] for p in P)/len(P);cy=sum(p[1] for p in P)/len(P)
o=bpy.data.objects['crest_posts'];M=o.matrix_world
for tgt in (93.6,100.8,103.7,138.8,139.5):
    V=[(M@v.co) for v in o.data.vertices if abs(math.degrees(math.atan2((M@v.co).y-cy,(M@v.co).x-cx))%360-tgt)<0.15]
    print('END',tgt,round(sum(v.x for v in V)/len(V),2),round(sum(v.y for v in V)/len(V),2))
