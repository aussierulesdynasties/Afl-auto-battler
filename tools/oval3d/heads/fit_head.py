"""Fit a cut Tripo head (bust_pilot cut.py output) onto the MetaHuman body for the 3D oval (row 202, 2d).

blender -b --python fit_head.py -- SRC.glb OUT.glb EYE_Y [TEX_PX] [GROW]

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
HEAD_GROW = float(a[4]) if len(a) > 4 else 1.0
MH_EYE, MH_CROWN, MH_Z = 1.7675, 1.893, 0.0236
HEAD_DEPTH = 0.2278  # Gawn: 0.4932 deep at his eye line x his eye-to-crown scale 0.4619
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
# Scale: his head's front-to-back depth at the eye line (nose tip to back of skull) is set to Gawn's
# fitted depth. Gawn is bald, so his eye-to-crown height was fitted to the base body's; a man with
# hair can't be fitted on his crown (the hair adds to it), but hair barely touches the eye-line depth.
band = [c for c in co if abs(c.z - eye_y) < 0.01]
depth = max(-c.y for c in band) - min(-c.y for c in band)
s = HEAD_DEPTH / depth
print("crown", crown, "depth", depth, "scale", s, "eye-to-crown (m)", s * (crown - eye_y), "skull mid (glTF z)", mid_fwd)
m = Matrix.Translation(Vector((0.0, -MH_Z, MH_EYE))) @ Matrix.Scale(s, 4) @ Matrix.Translation(Vector((0.0, mid_fwd, -eye_y)))
ob.data.transform(m)
# His head against his body, measured on a photo of him standing (Wikimedia Commons "Max Gawn
# 2018.12.jpg", crown to fingertips as the ruler): eye to crown 0.114 of it and ear to ear 0.172,
# against 0.105 and 0.144 on the fitted head over his body (x1.09, x1.19): GROW 1.12 for him. It grows
# from the middle of his neck at 1.64 m, then the whole head drops until the crown is back at the
# base body's, so he keeps his own height and his neck shortens by what the head grew.
GROW_Z = 1.64
crown0 = max(v.co.z for v in ob.data.vertices)
ob.data.transform(Matrix.Translation(Vector((0.0, -MH_Z, GROW_Z))) @ Matrix.Scale(HEAD_GROW, 4)
                  @ Matrix.Translation(Vector((0.0, MH_Z, -GROW_Z))))
drop = max(v.co.z for v in ob.data.vertices) - crown0
ob.data.transform(Matrix.Translation(Vector((0.0, 0.0, -drop))))
print("grow", HEAD_GROW, "drop (m)", drop)
# Behind the jaw his head's lower rim is wider than the body's neck (Gawn at 1.64 m: 8.6 cm each side
# against 6.0; Langford's sits 7 mm out at the back too), which showed as a ledge or a hanging hem.
# Below 1.70 m the back half of the rim is drawn in across, and the back of his neck in, to just
# inside the body's neck at 1.64 m (5.8 cm each side, 5.3 cm behind the middle, against the body's
# 6.0 and 5.5), so the body's neck covers the hem and the two meet in a clean line. Both are
# measured on his own head; the beard in front is left as it is.
NECK_TOP, NECK_LOW, NECK_HALF, NECK_BACK = 1.70, 1.64, 0.058, 0.053
low = [c for c in (v.co for v in ob.data.vertices) if NECK_LOW - 0.01 <= c.z < NECK_LOW + 0.01]
rim = max((abs(c.x) for c in low if -c.y < 0.03), default=NECK_HALF)
nape = max((c.y for c in low if abs(c.x) < 0.02), default=NECK_BACK)
for v in ob.data.vertices:
    c = v.co
    if c.z < NECK_TOP:
        dy = min(1.0, (NECK_TOP - c.z) / (NECK_TOP - NECK_LOW))
        back = min(1.0, max(0.0, (0.03 - (-c.y)) / 0.04))
        if rim > NECK_HALF:
            c.x *= 1.0 - dy * back * (1.0 - NECK_HALF / rim)
        if -c.y < 0.0 and nape > NECK_BACK:
            c.y *= 1.0 - dy * (1.0 - NECK_BACK / nape)
print("neck rim", rim, "nape", nape)
# His skin colour, for the body under his head, averaged from the texture in two places: under the
# back of his neck (below the ears, behind the skull middle, clear of any beard) and his cheeks
# (between eye and mouth, beside the nose). A beard darkens the cheeks and long hair at the back
# (a mullet) the neck, so both are printed and the clear one goes in heads.json by eye.
img = next((i for i in bpy.data.images if i.size[0] > 0), None)
if img is not None:
    w, h = img.size
    px = img.pixels[:]
    uv = ob.data.uv_layers.active.data
    places = {
        "neck": lambda c: 1.60 < c.z < 1.68 and -c.y < MH_Z - 0.04,
        "cheek": lambda c: 1.71 < c.z < 1.74 and 0.045 < abs(c.x) < 0.07 and -c.y > MH_Z + 0.03,
    }
    for name, inside in places.items():
        acc, n = [0.0, 0.0, 0.0], 0
        for poly in ob.data.polygons:
            for li in poly.loop_indices:
                if inside(ob.data.vertices[ob.data.loops[li].vertex_index].co):
                    u, v = uv[li].uv
                    i = (min(h - 1, max(0, int(v * h))) * w + min(w - 1, max(0, int(u * w)))) * 4
                    for k in range(3):
                        acc[k] += px[i + k]
                    n += 1
        if n:
            print("SKIN %s #%02x%02x%02x from %d" % (name, *(round(255 * acc[k] / n) for k in range(3)), n))
for img in bpy.data.images:
    if img.size[0] > tex_px:
        img.scale(tex_px, tex_px)
bpy.ops.export_scene.gltf(filepath=out, export_format="GLB", use_selection=True, export_image_format="JPEG",
                          export_jpeg_quality=90, export_yup=True)
lo = [min(v.co[i] for v in ob.data.vertices) for i in range(3)]
hi = [max(v.co[i] for v in ob.data.vertices) for i in range(3)]
print("OUT bbox (blender xyz)", lo, hi, "tris", sum(len(p.vertices) - 2 for p in ob.data.polygons))
