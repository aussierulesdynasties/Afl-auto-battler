# Seats drawn as the game draws them (Oval3D._ground_model): seat_tmpl.bin triangles, seats_<colour>.bin row-major 3x4 per seat.
# Godot Y-up -> Blender Z-up: (x, y, z) -> (x, -z, y), the same conversion the glTF importer applied to the model.
import bpy, numpy as np, os
SEAT_COLOURS = {"seat_grey": (0.618, 0.618, 0.586), "seat_moss": (0.437, 0.594, 0.555), "seat_navy": (0.068, 0.311, 0.484),
                "seat_slate": (0.272, 0.39, 0.488), "seat_steel": (0.437, 0.484, 0.524)}
def add_seats(d):
    t = np.fromfile(os.path.join(d, 'seat_tmpl.bin'), '<f4').reshape(-1, 3)
    for c, rgb in SEAT_COLOURS.items():
        fp = os.path.join(d, 'seats_%s.bin' % c)
        if not os.path.exists(fp): continue
        m = np.fromfile(fp, '<f4').reshape(-1, 3, 4)
        v = np.einsum('nij,kj->nki', m[:, :, :3], t) + m[:, None, :, 3]   # Godot space, n seats x k verts
        v = v.reshape(-1, 3); v = np.stack([v[:, 0], -v[:, 2], v[:, 1]], 1)
        nf = len(v) // 3
        me = bpy.data.meshes.new('seats_' + c)
        me.vertices.add(len(v)); me.vertices.foreach_set('co', v.ravel().astype(np.float32))
        me.loops.add(len(v)); me.loops.foreach_set('vertex_index', np.arange(len(v), dtype=np.int32))
        me.polygons.add(nf); me.polygons.foreach_set('loop_start', np.arange(0, len(v), 3, dtype=np.int32))
        me.update(); me.validate()
        mat = bpy.data.materials.new('mat_' + c); mat.use_nodes = True
        mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (*rgb, 1)
        me.materials.append(mat)
        ob = bpy.data.objects.new('seats_' + c, me); bpy.context.scene.collection.objects.link(ob)
        print('seats', c, len(m))
