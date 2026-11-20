# Normals float32 -> int8 normalized (KHR_mesh_quantization); everything else copied byte for byte.
import json,struct,sys,numpy as np
src,dst=sys.argv[1],sys.argv[2];b=open(src,'rb').read()
n=struct.unpack('<I',b[12:16])[0];j=json.loads(b[20:20+n]);o=20+n;bl=struct.unpack('<I',b[o:o+4])[0];bin_=b[o+8:o+8+bl]
A=j['accessors'];BV=j['bufferViews'];norm=set(p['attributes']['NORMAL'] for m in j['meshes'] for p in m['primitives'] if 'NORMAL' in p['attributes'])
out=bytearray();nbv=[];remap={}
for i,v in enumerate(BV):
    data=bin_[v.get('byteOffset',0):v.get('byteOffset',0)+v['byteLength']]
    acc=[k for k in norm if A[k]['bufferView']==i]
    if acc:
        a=A[acc[0]];f=np.frombuffer(data,dtype='<f4').reshape(-1,3)
        q=np.zeros((len(f),4),np.int8);q[:,:3]=np.clip(np.round(f*127),-127,127);data=q.tobytes()
        a['componentType']=5120;a['normalized']=True;a.pop('min',None);a.pop('max',None);v=dict(v);v['byteStride']=4
    while len(out)%4:out.append(0)
    v=dict(v);v['byteOffset']=len(out);v['byteLength']=len(data);out+=data;nbv.append(v)
while len(out)%4:out.append(0)
j['bufferViews']=nbv;j['buffers'][0]['byteLength']=len(out)
for k in('extensionsUsed','extensionsRequired'):j[k]=sorted(set(j.get(k,[]))|{'KHR_mesh_quantization'})
js=json.dumps(j,separators=(',',':')).encode();js+=b' '*((4-len(js)%4)%4)
f=open(dst,'wb');f.write(struct.pack('<III',0x46546C67,2,12+8+len(js)+8+len(out)));f.write(struct.pack('<II',len(js),0x4E4F534A));f.write(js);f.write(struct.pack('<II',len(out),0x004E4942));f.write(out)
print(len(b),'->',12+8+len(js)+8+len(out))
