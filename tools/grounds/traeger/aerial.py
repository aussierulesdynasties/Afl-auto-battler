import bpy,os
sc=bpy.context.scene;O=os.path.dirname(bpy.data.filepath);sc.render.film_transparent=True
g=bpy.data.collections['ground']
sc.render.filepath=os.path.join(O,'render_ground.png');bpy.ops.render.render(write_still=True)
for o in g.objects:o.hide_render=True
sc.render.filepath=os.path.join(O,'render_model.png');bpy.ops.render.render(write_still=True);print('AERIAL OK')
