# rebake world position and object normal from baked.blend, dump float pixels straight to .npy (no EXR round trip)
import bpy,sys,os,numpy as np
RES=int(sys.argv[sys.argv.index('--')+1])
ob=bpy.data.objects['PeopleFirstStadium'];me=ob.data
bpy.context.view_layer.objects.active=ob;ob.select_set(True)
sc=bpy.context.scene;sc.render.engine='CYCLES';sc.cycles.device='GPU'
try:
    pr=bpy.context.preferences.addons['cycles'].preferences;pr.compute_device_type='OPTIX';pr.get_devices()
    for d in pr.devices:d.use=True
except Exception as e:print('gpu',e)
sc.cycles.samples=1;sc.render.bake.margin=4
def go(name,typ):
    im=bpy.data.images.new(name,RES,RES,float_buffer=True,alpha=True)
    im.colorspace_settings.name='Non-Color'
    for m in me.materials:
        nt=m.node_tree;n=nt.nodes['BAKE'];n.image=im;nt.nodes.active=n
    bpy.ops.object.bake(type=typ,uv_layer='atlas')
    a=np.empty(RES*RES*4,np.float32);im.pixels.foreach_get(a);a=a.reshape(RES,RES,4)[::-1]
    np.save(os.path.abspath(name+'.npy'),a);print('OK',name,[np.percentile(a[...,c][a[...,3]>0],[1,50,99]) for c in range(4)])
go('bake_pos','POSITION')
sc.render.bake.normal_space='OBJECT';go('bake_nrm','NORMAL')
