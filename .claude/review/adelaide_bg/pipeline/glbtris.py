import json,struct,sys
f=open(sys.argv[1],'rb').read(); n=struct.unpack('<I',f[12:16])[0]; j=json.loads(f[20:20+n])
t=0
for m in j['meshes']:
    for p in m['primitives']:
        if 'indices' in p: t+=j['accessors'][p['indices']]['count']//3
print('triangles',t)
