"""Every triangle of a .glb as (mesh name, material name, triangles in world metres). No Blender needed."""
import json,struct,numpy as np,sys
def load(path):
    f=open(path,'rb').read()
    l=struct.unpack('<I',f[12:16])[0]; j=json.loads(f[20:20+l])
    off=20+l; bl=struct.unpack('<I',f[off:off+4])[0]; bin_=f[off+8:off+8+bl]
    def acc(i):
        a=j['accessors'][i]; bv=j['bufferViews'][a['bufferView']]
        n={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
        o=bv.get('byteOffset',0)+a.get('byteOffset',0)
        st=bv.get('byteStride',0); isz=np.dtype(dt).itemsize*n
        if st and st!=isz:
            raw=np.frombuffer(bin_,dtype='u1',count=st*(a['count']-1)+isz,offset=o)
            return np.lib.stride_tricks.as_strided(raw,(a['count'],isz),(st,1)).copy().view(dt).reshape(-1,n)
        return np.frombuffer(bin_,dtype=dt,count=a['count']*n,offset=o).reshape(-1,n)
    def mat(nd):
        if 'matrix' in nd: return np.array(nd['matrix']).reshape(4,4).T
        M=np.eye(4)
        if 'scale' in nd: M=np.diag(list(nd['scale'])+[1])@M
        if 'rotation' in nd:
            x,y,z,w=nd['rotation']; R=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
            R4=np.eye(4);R4[:3,:3]=R;M=R4@M
        if 'translation' in nd: T=np.eye(4);T[:3,3]=nd['translation'];M=T@M
        return M
    out=[]
    def walk(ni,P):
        nd=j['nodes'][ni]; M=P@mat(nd)
        if 'mesh' in nd:
            for pr in j['meshes'][nd['mesh']]['primitives']:
                p=acc(pr['attributes']['POSITION']).astype(np.float64)
                p=(np.c_[p,np.ones(len(p))]@M.T)[:,:3]
                idx=acc(pr['indices']).reshape(-1,3) if 'indices' in pr else np.arange(len(p)).reshape(-1,3)
                out.append((j['meshes'][nd['mesh']].get('name'),j['materials'][pr.get('material',0)]['name'],p[idx]))
        for c in nd.get('children',[]): walk(c,M)
    for r in j['scenes'][j.get('scene',0)]['nodes']: walk(r,np.eye(4))
    return j,out
