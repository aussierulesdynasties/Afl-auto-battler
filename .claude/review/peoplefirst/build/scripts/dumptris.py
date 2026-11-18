import bpy,numpy as np,os
ob=bpy.data.objects['PeopleFirstStadium'];me=ob.data;me.calc_loop_triangles()
V=np.array([v.co[:] for v in me.vertices]);T=np.array([t.vertices[:] for t in me.loop_triangles]);M=np.array([t.material_index for t in me.loop_triangles])
np.savez(os.path.abspath('tris.npz'),V=V,T=T,M=M,names=np.array([m.name for m in me.materials]));print('TRIS',len(T),[m.name for m in me.materials])
