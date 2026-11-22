# Optus seats in the #1843 loader format (Oval3D._ground_model): seat_tmpl.bin (one seat, triangles, glTF frame)
# and seats_<material>.bin (row-major 3x4 per seat, glTF frame), read back from the built seats3d mesh.
# Usage: blender -b optus.blend --python seatbin.py -- OUTDIR
import bpy,sys,os,numpy as np
out=sys.argv[sys.argv.index('--')+1];os.makedirs(out,exist_ok=True)
ob=bpy.data.objects['seats3d'];me=ob.data;n=len(me.vertices)
V=np.empty(n*3);me.vertices.foreach_get('co',V);V=V.reshape(-1,32,3)
mi=np.empty(len(me.polygons),int);me.polygons.foreach_get('material_index',mi);mi=mi.reshape(len(V),-1)[:,0]
side=V[:,1]-V[:,0];side/=np.linalg.norm(side,axis=1)[:,None];fwd=V[:,3]-V[:,0];fwd/=np.linalg.norm(fwd,axis=1)[:,None]
P=V[:,0]+0.22*side+0.22*fwd-np.array([0,0,0.40])
def bx(x0,x1,y0,y1,z0,z1):return [(x0,y0,z0),(x1,y0,z0),(x1,y1,z0),(x0,y1,z0),(x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1)]
T=np.array(bx(-0.22,0.22,-0.22,0.20,0.40,0.46)+bx(-0.22,0.22,-0.30,-0.24,0.46,0.86)+bx(-0.25,-0.21,-0.22,0.04,0.0,0.40)+bx(0.21,0.25,-0.22,0.04,0.0,0.40))
BF=[[0,3,2,1],[4,5,6,7],[0,1,5,4],[1,2,6,5],[2,3,7,6],[3,0,4,7]]
C=np.array([[1,0,0],[0,0,1],[0,-1,0.0]])
tri=[T[o+f[k]] for o in (0,8,16,24) for f in BF for i in (1,2) for k in (0,i,i+1)]
(np.array(tri)@C.T).astype('<f4').tofile(os.path.join(out,'seat_tmpl.bin'))
# check: template placed by the recovered frame reproduces every pan corner
err=np.abs((P[:,None,:]+T[None,:8,0,None]*side[:,None]+T[None,:8,1,None]*fwd[:,None]+T[None,:8,2,None]*np.array([0,0,1.0]))-V[:,:8]).max()
for m in np.unique(mi):
    s=mi==m;A=np.stack([side[s],fwd[s],np.tile([0,0,1.0],(s.sum(),1))],2)   # columns: local x,y,z in Blender
    G=np.einsum('ij,njk,kl->nil',C,A,C.T);O=P[s]@C.T
    xf=np.concatenate([G,O[:,:,None]],2).reshape(-1,12)
    name=me.materials[m].name;xf.astype('<f4').tofile(os.path.join(out,'seats_%s.bin'%name))
    c=me.materials[m].node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value
    print('SEATS',name,int(s.sum()),'linear rgb %.3f %.3f %.3f'%(c[0],c[1],c[2]))
print('SEATS total',len(V),'tmpl tris',len(tri)//3,'pan max err m %.4f'%err)
