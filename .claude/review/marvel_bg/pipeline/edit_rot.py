p='scene.py';s=open(p,newline='').read()
a="bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'scene_bg.glb'), export_format='GLB', use_selection=False)\nglb = os.path.normpath(os.path.join(HERE, spec['glb']))\nbpy.ops.import_scene.gltf(filepath=glb)\n"
b="""MROT = math.radians(spec.get('model_rot_deg', 0.0))   # ground GLB is in the stadium's own axes: true-north scene = GLB turned by MROT
_bg = [o for o in bpy.data.objects if o.parent is None]
for o in _bg: o.rotation_euler[2] -= MROT; o.location = Vector((math.cos(-MROT) * o.location.x - math.sin(-MROT) * o.location.y, math.sin(-MROT) * o.location.x + math.cos(-MROT) * o.location.y, o.location.z))
bpy.context.view_layer.update()
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT, 'scene_bg.glb'), export_format='GLB', use_selection=False)   # exported in the ground GLB's frame
for o in _bg: o.rotation_euler[2] += MROT; o.location = Vector((math.cos(MROT) * o.location.x - math.sin(MROT) * o.location.y, math.sin(MROT) * o.location.x + math.cos(MROT) * o.location.y, o.location.z))
glb = os.path.normpath(os.path.join(HERE, spec['glb']))
_pre = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=glb)
for o in [o for o in bpy.data.objects if o not in _pre and o.parent is None]:
    o.rotation_euler[2] += MROT; o.location = Vector((math.cos(MROT) * o.location.x - math.sin(MROT) * o.location.y, math.sin(MROT) * o.location.x + math.cos(MROT) * o.location.y, o.location.z))
bpy.context.view_layer.update()
"""
assert a in s; s=s.replace(a,b.replace('\n','\r\n') if '\r\n' in s else b);open(p,'w',newline='').write(s)
