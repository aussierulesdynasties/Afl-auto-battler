import bpy,numpy as np,sys
out=sys.argv[sys.argv.index('--')+1];D={}
for o in bpy.data.objects:
    if o.type=='MESH':D[o.name]=np.array([(o.matrix_world@x.co)[:] for x in o.data.vertices])
np.savez(out,**D)
