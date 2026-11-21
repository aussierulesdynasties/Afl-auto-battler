import bpy,sys
b=bpy.data.materials['roof_green'].node_tree.nodes['Principled BSDF'];b.inputs['Specular IOR Level'].default_value=0.1
bpy.ops.wm.save_as_mainfile(filepath=sys.argv[-1],relative_remap=True);print('SAVED9')
