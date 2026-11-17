"""Fit a cut Tripo head (bust_pilot cut.py output) onto the MetaHuman body for the 3D oval (row 202, 2d).

blender -b --python fit_head.py -- SRC.glb OUT.glb EYE_Y [TEX_PX]

The head is scaled so his eye-to-crown height matches the base body's (eyes 1.7675 m, crown 1.893 m
on player_mh.glb at 188 cm) and centred on the base body's skull (x 0, skull middle z 0.0236), in
the body's rest space (glTF: y up, face toward +z). The game hangs it on the head bone, so it
follows each man's height. EYE_Y: his eye line in the source's units (bust_pilot README: Gawn
0.679). The texture is cut to TEX_PX (default 2048) and stored as JPEG to keep the APK small.
"""
import bpy, sys
from mathutils import Vector, Matrix
a = sys.argv[sys.argv.index("--") + 1:]
src, out, eye_y = a[0], a[1], float(a[2])
tex_px = int(a[3]) if len(a) > 3 else 2048
MH_EYE, MH_CROWN, MH_Z = 1.7675, 1.893, 0.0236
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src)
ob = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
for o in bpy.context.scene.objects:
    o.select_set(o == ob)
bpy.context.view_layer.objects.active = ob
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
# Blender z up = glTF y; Blender -y = glTF +z.
co = [v.co.copy() for v in ob.data.vertices]
crown = max(c.z for c in co)
top = [c for c in co if c.z > eye_y]
mid_fwd = (min(-c.y for c in top) + max(-c.y for c in top)) / 2.0
s = (MH_CROWN - MH_EYE) / (crown - eye_y)
print("crown", crown, "scale", s, "skull mid (glTF z)", mid_fwd)
m = Matrix.Translation(Vector((0.0, -MH_Z, MH_EYE))) @ Matrix.Scale(s, 4) @ Matrix.Translation(Vector((0.0, mid_fwd, -eye_y)))
ob.data.transform(m)
# Behind the jaw his head's lower rim is wider than the body's neck (Gawn at 1.64 m: 8.6 cm each side
# against 6.0), which showed as a ledge from behind. Below 1.70 m the back half of the rim is drawn
# in across, to the body's neck width at 1.64 m (the beard in front is left as it is), and the back of
# his neck in to the body's (5.5 cm behind the middle against his 6.3).
NECK_TOP, NECK_LOW, NECK_HALF, NECK_BACK = 1.70, 1.64, 0.060, 0.055
low = [c for c in (v.co for v in ob.data.vertices) if NECK_LOW - 0.01 <= c.z < NECK_LOW + 0.01 and -c.y < 0.03]
rim = max((abs(c.x) for c in low), default=NECK_HALF)
for v in ob.data.vertices:
    c = v.co
    if c.z < NECK_TOP and rim > NECK_HALF:
        dy = min(1.0, (NECK_TOP - c.z) / (NECK_TOP - NECK_LOW))
        back = min(1.0, max(0.0, (0.03 - (-c.y)) / 0.04))
        c.x *= 1.0 - dy * back * (1.0 - NECK_HALF / rim)
        if -c.y < 0.0:
            c.y *= 1.0 - dy * (1.0 - NECK_BACK / 0.063)
print("neck rim", rim)
# His skin colour, for the body under his head: the texture under the back of his neck (below the
# ears, behind the skull middle, clear of any beard), averaged.
img = next((i for i in bpy.data.images if i.size[0] > 0), None)
if img is not None:
    w, h = img.size
    px = img.pixels[:]
    uv = ob.data.uv_layers.active.data
    acc, n = [0.0, 0.0, 0.0], 0
    for poly in ob.data.polygons:
        for li in poly.loop_indices:
            c = ob.data.vertices[ob.data.loops[li].vertex_index].co
            if 1.60 < c.z < 1.68 and -c.y < MH_Z - 0.04:
                u, v = uv[li].uv
                i = (min(h - 1, max(0, int(v * h))) * w + min(w - 1, max(0, int(u * w)))) * 4
                for k in range(3):
                    acc[k] += px[i + k]
                n += 1
    if n:
        print("SKIN #%02x%02x%02x from %d" % (*(round(255 * acc[k] / n) for k in range(3)), n))
for img in bpy.data.images:
    if img.size[0] > tex_px:
        img.scale(tex_px, tex_px)
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_image_format="JPEG",
                          export_jpeg_quality=90, export_yup=True)
lo = [min(v.co[i] for v in ob.data.vertices) for i in range(3)]
hi = [max(v.co[i] for v in ob.data.vertices) for i in range(3)]
print("OUT bbox (blender xyz)", lo, hi, "tris", sum(len(p.vertices) - 2 for p in ob.data.polygons))
