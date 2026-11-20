# Blender: unlit photo materials on stage1.blend, render the matched view, export GLB.
# Usage: blender -b MV/stage1.blend --python stage2.py -- MVDIR OUT.glb RENDER.png
import bpy,sys,os
argv=sys.argv[sys.argv.index('--')+1:];MV,GLB,PNG=argv[0],argv[1],argv[2]
sc=bpy.context.scene
TEAL=(75/255,109/255,109/255);TAN=(121/255,103/255,84/255)   # medians of the truss / rail pixels (sRGB)
def srgb2lin(c):return tuple(((x+0.055)/1.055)**2.4 if x>0.04045 else x/12.92 for x in c)
def unlit(name,img=None,col=None):
    m=bpy.data.materials.new(name);m.use_nodes=True;nt=m.node_tree;N=nt.nodes;L=nt.links;N.clear()
    lp=N.new('ShaderNodeLightPath');tr=N.new('ShaderNodeBsdfTransparent');em=N.new('ShaderNodeEmission')
    mix=N.new('ShaderNodeMixShader');out=N.new('ShaderNodeOutputMaterial')
    if img:
        t=N.new('ShaderNodeTexImage');t.image=bpy.data.images.load(img);t.interpolation='Linear';L.new(t.outputs['Color'],em.inputs['Color'])
    else:em.inputs['Color'].default_value=(*srgb2lin(col),1)
    L.new(lp.outputs['Is Camera Ray'],mix.inputs[0]);L.new(tr.outputs[0],mix.inputs[1]);L.new(em.outputs[0],mix.inputs[2]);L.new(mix.outputs[0],out.inputs[0])
    return m
for o in list(sc.objects):
    if o.type=='LIGHT':bpy.data.objects.remove(o)
for g in ('front','sym','roof'):
    ob=sc.objects[g];ob.data.materials.clear();ob.data.materials.append(unlit('m_'+g,img=os.path.join(MV,'tex_%s.png'%g)))
for g,c in (('teal',TEAL),('tan',TAN)):
    ob=sc.objects[g];ob.data.materials.clear();ob.data.materials.append(unlit('m_'+g,col=c))
sc.render.film_transparent=True;sc.cycles.samples=16;sc.render.filepath=PNG
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGBA'
bpy.ops.render.render(write_still=True)
bpy.ops.object.select_all(action='DESELECT')
for o in sc.objects:o.select_set(o.type=='MESH')
bpy.ops.export_scene.gltf(filepath=GLB,export_format='GLB',use_selection=True,export_apply=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(MV,'stage2.blend'))
print('done stage2')
