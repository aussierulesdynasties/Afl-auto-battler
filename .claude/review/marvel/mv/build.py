# Blender: build the Marvel exterior from parts.json, texture it from the matched photo, render, export GLB.
# Usage: blender -b --python build.py -- MVDIR RES
import bpy,bmesh,json,sys,math,os
import numpy as np
from mathutils import Matrix,Vector
argv=sys.argv[sys.argv.index('--')+1:];MV=argv[0];RES=int(argv[1]) if len(argv)>1 else 2048
J=json.load(open(os.path.join(MV,'parts.json')));P=J['cam'];CW=J['C']
bpy.ops.wm.read_factory_settings(use_empty=True)
sc=bpy.context.scene
# ---------- camera from the fitted pinhole (photo mu.png is undistorted, principal point centred)
def Rm(yaw,pitch,roll):
    cy,sy=math.cos(yaw),math.sin(yaw);cp,sp=math.cos(pitch),math.sin(pitch);cr,sr=math.cos(roll),math.sin(roll)
    f=np.array([cy*cp,sy*cp,sp]);r=np.array([sy,-cy,0.0]);u=np.cross(r,f)
    return np.array([cr*r+sr*u,-sr*r+cr*u,f])
M=Rm(*P[3:6]);cd=bpy.data.cameras.new('cam');cam=bpy.data.objects.new('cam',cd);sc.collection.objects.link(cam)
cd.sensor_fit='HORIZONTAL';cd.sensor_width=36.0;cd.lens=P[6]*36.0/1920.0;cd.clip_start=1.0;cd.clip_end=5000
R=np.stack([M[0],M[1],-M[2]],1);mw=Matrix.Identity(4)
for i in range(3):
    for j in range(3):mw[i][j]=R[i,j]
    mw[i][3]=P[i]
cam.matrix_world=mw;sc.camera=cam
sc.render.resolution_x=1920;sc.render.resolution_y=1080;sc.render.resolution_percentage=100
sc.render.engine='CYCLES';sc.cycles.device='CPU';sc.cycles.samples=1;sc.cycles.use_denoising=False
sc.view_settings.view_transform='Standard';sc.view_settings.look='None'
# ---------- meshes
GROUPS={}
for p in J['parts']:
    me=bpy.data.meshes.new(p['name']);me.from_pydata([tuple(v) for v in p['V']],[],p['F']);me.update()
    ob=bpy.data.objects.new(p['name'],me);sc.collection.objects.link(ob)
    g={'teal':'teal','tan':'tan','roof':'roof'}.get(p['mat'],'sym' if p['sym'] else 'front')
    GROUPS.setdefault(g,[]).append(ob)
def join(obs,name):
    bpy.ops.object.select_all(action='DESELECT')
    for o in obs:o.select_set(True)
    bpy.context.view_layer.objects.active=obs[0];bpy.ops.object.join();ob=bpy.context.active_object;ob.name=name
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.remove_doubles(bm,verts=bm.verts,dist=0.01)
    bmesh.ops.recalc_face_normals(bm,faces=bm.faces);bm.to_mesh(ob.data);bm.free();return ob
OB={g:join(o,g) for g,o in GROUPS.items()}
# ---------- UV atlases for the photo-textured groups
TEX=['front','sym','roof']
for g in TEX:
    ob=OB[g];bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(60),island_margin=0.003,area_weight=0.0,correct_aspect=True,scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')
# ---------- bake helpers
def nodes_mat(name):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;nt.nodes.clear();return m,nt
def proj_uv_mat(twin):
    # emission = (u,v) photo coordinates (mu.png pixels / 1920,1080) of this point (or of its 180 deg twin)
    m,nt=nodes_mat('projuv'+('_tw' if twin else ''));N=nt.nodes;L=nt.links
    geo=N.new('ShaderNodeNewGeometry');pos=geo.outputs['Position']
    if twin:
        mul=N.new('ShaderNodeVectorMath');mul.operation='MULTIPLY_ADD';mul.inputs[1].default_value=(-1,-1,1);mul.inputs[2].default_value=(2*CW[0],2*CW[1],0)
        L.new(pos,mul.inputs[0]);pos=mul.outputs[0]
    vt=N.new('ShaderNodeVectorTransform');vt.vector_type='POINT';vt.convert_from='WORLD';vt.convert_to='CAMERA';L.new(pos,vt.inputs[0])
    sep=N.new('ShaderNodeSeparateXYZ');L.new(vt.outputs[0],sep.inputs[0])
    neg=N.new('ShaderNodeMath');neg.operation='MULTIPLY';neg.inputs[1].default_value=1;L.new(sep.outputs[2],neg.inputs[0])
    dx=N.new('ShaderNodeMath');dx.operation='DIVIDE';L.new(sep.outputs[0],dx.inputs[0]);L.new(neg.outputs[0],dx.inputs[1])
    dy=N.new('ShaderNodeMath');dy.operation='DIVIDE';L.new(sep.outputs[1],dy.inputs[0]);L.new(neg.outputs[0],dy.inputs[1])
    f=P[6]
    ux=N.new('ShaderNodeMath');ux.operation='MULTIPLY_ADD';ux.inputs[1].default_value=f/1920;ux.inputs[2].default_value=0.5;L.new(dx.outputs[0],ux.inputs[0])
    vy=N.new('ShaderNodeMath');vy.operation='MULTIPLY_ADD';vy.inputs[1].default_value=-f/1080;vy.inputs[2].default_value=0.5;L.new(dy.outputs[0],vy.inputs[0])
    # third channel: depth sign (1 if in front of camera)
    fr=N.new('ShaderNodeMath');fr.operation='GREATER_THAN';fr.inputs[1].default_value=0;L.new(neg.outputs[0],fr.inputs[0])
    cmb=N.new('ShaderNodeCombineXYZ');L.new(ux.outputs[0],cmb.inputs[0]);L.new(vy.outputs[0],cmb.inputs[1]);L.new(fr.outputs[0],cmb.inputs[2])
    em=N.new('ShaderNodeEmission');L.new(cmb.outputs[0],em.inputs[0]);out=N.new('ShaderNodeOutputMaterial');L.new(em.outputs[0],out.inputs[0])
    return m
def vis_mat():
    m,nt=nodes_mat('vis');N=nt.nodes;L=nt.links
    d=N.new('ShaderNodeBsdfDiffuse');d.inputs[0].default_value=(1,1,1,1);t=N.new('ShaderNodeBsdfTranslucent');t.inputs[0].default_value=(1,1,1,1)
    a=N.new('ShaderNodeAddShader');L.new(d.outputs[0],a.inputs[0]);L.new(t.outputs[0],a.inputs[1])
    out=N.new('ShaderNodeOutputMaterial');L.new(a.outputs[0],out.inputs[0]);return m
def light_at(name,pos):
    ld=bpy.data.lights.new(name,'POINT');ld.energy=1e9;ld.shadow_soft_size=0.0
    lo=bpy.data.objects.new(name,ld);lo.location=pos;sc.collection.objects.link(lo);return lo
Lcam=light_at('Lcam',P[:3]);Ltw=light_at('Ltw',(2*CW[0]-P[0],2*CW[1]-P[1],P[2]))
for g in ('teal','tan'):OB[g].visible_shadow=False   # trusses do not hide the deck below them
def set_mat(ob,m):
    ob.data.materials.clear();ob.data.materials.append(m)
def bake(ob,kind,img):
    nt=ob.active_material.node_tree;n=nt.nodes.new('ShaderNodeTexImage');n.image=img;nt.nodes.active=n
    bpy.ops.object.select_all(action='DESELECT');ob.select_set(True);bpy.context.view_layer.objects.active=ob
    if kind=='EMIT':bpy.ops.object.bake(type='EMIT',margin=4)
    else:bpy.ops.object.bake(type='DIFFUSE',pass_filter={'DIRECT'},margin=4)
    nt.nodes.remove(n)
    a=np.empty(img.size[0]*img.size[1]*4,np.float32);img.pixels.foreach_get(a);return a.reshape(img.size[1],img.size[0],4)
out={}
VM=vis_mat()
for g in TEX:
    ob=OB[g];r=RES
    res={}
    for twin in (False,True):
        set_mat(ob,proj_uv_mat(twin));img=bpy.data.images.new('uv',r,r,float_buffer=True);res['uv'+str(int(twin))]=bake(ob,'EMIT',img)
        set_mat(ob,VM);Lcam.hide_render=twin;Ltw.hide_render=not twin
        img=bpy.data.images.new('vis',r,r,float_buffer=True);res['vis'+str(int(twin))]=bake(ob,'DIFF',img)
        # coverage mask (where the atlas has faces): bake emit white
    np.savez_compressed(os.path.join(MV,'bake_%s.npz'%g),**{k:v[...,:3] for k,v in res.items()})
    print('baked',g,flush=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(MV,'stage1.blend'))
print('done stage1')
