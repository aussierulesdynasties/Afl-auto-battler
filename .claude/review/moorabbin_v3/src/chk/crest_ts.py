import bpy,math,json
O=json.load(open(bpy.path.abspath('//build.json')));P=O['pitch'];P=P[:-1] if P[0]==P[-1] else P
cx=sum(p[0] for p in P)/len(P);cy=sum(p[1] for p in P)/len(P)
R0=(-19.0,93.1);L=math.hypot(-48.1,-25.5);tv=(-48.1/L,-25.5/L);nf=(-tv[1],tv[0])
o=bpy.data.objects['crest_posts'];M=o.matrix_world;S=set()
for v in o.data.vertices:
    w=M@v.co;a=math.degrees(math.atan2(w.y-cy,w.x-cx))%360
    if 40<a<104 or 136<a<141:
        d=(w.x-R0[0],w.y-R0[1]);S.add((round(a),round(d[0]*tv[0]+d[1]*tv[1],1),round(d[0]*nf[0]+d[1]*nf[1],1)))
print('TS',sorted(S))
