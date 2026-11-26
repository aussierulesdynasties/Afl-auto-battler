"""Norwood Oval's model: every part from the geometry modules, textured with tex.py's tiles, written as a glb
(glTF: x east, y up, -z north) plus the instanced seats (seat templates and seats_<colour>.bin).

    ~/bpyenv/bin/python build.py glb <out_dir>             # pip bpy 5.2.4
    ~/bpyenv/bin/python build.py render <out.png> <cam>    # a quick Cycles still: cam = x,y,z,tx,ty,tz,lens

Run tex.py first."""
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy  # noqa: E402
import nwlib  # noqa: E402
import ses  # noqa: E402
import arena  # noqa: E402
import west  # noqa: E402
import north  # noqa: E402
import town  # noqa: E402
import frontage  # noqa: E402

TEX = os.path.join(HERE, "tex")
SPEC = json.load(open(os.path.join(TEX, "spec.json")))
ROUGH = {"window_dark": 0.12, "steel_dark": 0.5, "roof_red": 0.75, "flashing": 0.6, "pipe_brown": 0.5}
METAL = {"steel_dark": 0.4}
MODULES = [ses, west, north, arena, town, frontage]


def material(name, cache={}):
    if name in cache:
        return cache[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    s = SPEC[name]
    im = nt.nodes.new("ShaderNodeTexImage")
    img = bpy.data.images.load(os.path.join(TEX, s["img"]))
    img.pack()
    im.image = img
    nt.links.new(im.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = ROUGH.get(name, 0.85)
    b.inputs["Metallic"].default_value = METAL.get(name, 0.0)
    cache[name] = m
    return m


def face_uv(pts, mat, uv):
    s = SPEC[mat]
    if uv is not None:
        return [(u / s["tw"], v / s["th"]) for u, v in uv]
    P = np.array(pts)
    n = np.cross(P[1] - P[0], P[2] - P[0])
    if np.linalg.norm(n) < 1e-9 and len(P) > 3:
        n = np.cross(P[2] - P[0], P[3] - P[0])
    n = n / (np.linalg.norm(n) + 1e-12)
    if abs(n[2]) > 0.97:
        t, b = np.array([1.0, 0, 0]), np.array([0, 1.0, 0])
    else:
        t = np.cross([0, 0, 1.0], n)
        t /= np.linalg.norm(t)
        b = np.cross(n, t)
    return [(float(p @ t) / s["tw"], float(p @ b) / s["th"]) for p in P]


def make_object(name, faces):
    verts, polys, uvs, mats = [], [], [], []
    mat_index = {}
    for pts, mat, uv in faces:
        i0 = len(verts)
        verts.extend([tuple(map(float, p)) for p in pts])
        polys.append(list(range(i0, i0 + len(pts))))
        uvs.extend(face_uv(pts, mat, uv))
        mats.append(mat_index.setdefault(mat, len(mat_index)))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], polys)
    uvl = me.uv_layers.new(name="UVMap")
    for li, l in enumerate(me.loops):
        uvl.data[li].uv = uvs[l.vertex_index]
    for m in mat_index:
        me.materials.append(material(m))
    me.polygons.foreach_set("material_index", mats)
    me.validate()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.view_layer.objects.active = ob
    ob.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles(threshold=0.0005)
    bpy.ops.object.mode_set(mode="OBJECT")
    ob.select_set(False)
    return ob


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    nwlib.PARTS.clear()
    seats = {}
    for mod in MODULES:
        for col, lst in (mod.build() or {}).items():
            seats.setdefault(col, []).extend(lst)
    for name, faces in nwlib.PARTS.items():
        make_object(name, faces)
    return seats


SEAT_KINDS = {"green": "seat_nw_green", "blue": "seat_nw_blue", "timber": "seat_nw_timber", "ws_teal": "seat_nw_teal", "ws_red": "seat_nw_red"}


def seat_template(kind):
    """A seat as triangles in glTF space (facing -z, origin on the tread): a moulded plastic seat, or for
    the old stand's timber section a 0.5 m length of slatted bench with its backrest."""
    tri = []
    def boxq(x0, x1, y0, y1, z0, z1):
        c = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
        for a, b, cc, d in ((0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
            tri.extend([c[a], c[b], c[cc], c[a], c[cc], c[d]])
    if kind == "timber":
        for k in range(3):
            boxq(-0.25, 0.25, 0.43, 0.46, -0.2 + k * 0.11, -0.11 + k * 0.11)
        for k in range(2):
            boxq(-0.25, 0.25, 0.6 + k * 0.14, 0.7 + k * 0.14, 0.17, 0.2)
        boxq(-0.02, 0.02, 0.0, 0.43, -0.05, 0.05)
        boxq(-0.02, 0.02, 0.43, 0.88, 0.2, 0.23)
    else:
        boxq(-0.21, 0.21, 0.40, 0.46, -0.22, 0.18)        # seat pan
        boxq(-0.21, 0.21, 0.46, 0.86, 0.18, 0.24)         # back
        boxq(-0.03, 0.03, 0.0, 0.40, -0.03, 0.03)         # pedestal
    return np.array(tri, np.float32)


def write_seats(seats, out):
    for col, lst in seats.items():
        kind = SEAT_KINDS[col]
        seat_template(col).tofile(os.path.join(out, "seat_tmpl_%s.bin" % kind))
        rows = []
        for x, y, z, hd in lst:
            f = np.array([math.cos(hd), 0.0, -math.sin(hd)])      # facing, glTF (x, y up, z = -north)
            bz = -f
            by = np.array([0, 1.0, 0])
            bx = np.cross(by, bz)
            o = np.array([x, z, -y])
            m = np.stack([bx, by, bz], 1)
            rows.append(np.concatenate([np.c_[m, o]]).reshape(-1))
        np.array(rows, np.float32).tofile(os.path.join(out, "seats_%s.bin" % kind))
        print(kind, len(lst), "seats")


def export(out):
    os.makedirs(out, exist_ok=True)
    seats = build()
    bpy.ops.export_scene.gltf(filepath=os.path.join(out, "norwood.glb"), export_format="GLB", export_yup=True,
                              export_apply=True, export_image_format="AUTO", export_materials="EXPORT")
    write_seats(seats, out)


def render(out, cam):
    seats = build()
    sc = bpy.context.scene
    x, y, z, tx, ty, tz, lens = map(float, cam.split(","))
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cd.clip_end = 3000
    co = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(co)
    co.location = (x, y, z)
    d = np.array([tx - x, ty - y, tz - z])
    import mathutils
    co.rotation_euler = mathutils.Vector(d).to_track_quat("-Z", "Y").to_euler()
    sc.camera = co
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = 4.0
    so = bpy.data.objects.new("sun", sun)
    so.rotation_euler = (math.radians(40), 0, math.radians(30))
    sc.collection.objects.link(so)
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.68, 0.85, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.8
    sc.world = w
    # ground plane and seats as simple boxes for the preview
    bpy.ops.mesh.primitive_plane_add(size=600, location=(0, 0, -0.02))
    g = bpy.context.active_object
    gm = bpy.data.materials.new("g")
    gm.diffuse_color = (0.25, 0.32, 0.18, 1)
    g.data.materials.append(gm)
    cols = {"green": (0.12, 0.35, 0.22, 1), "blue": (0.12, 0.2, 0.42, 1), "timber": (0.42, 0.2, 0.1, 1), "ws_teal": (0.15, 0.35, 0.38, 1), "ws_red": (0.5, 0.06, 0.05, 1)}
    for col, lst in seats.items():
        tri = seat_template(col).reshape(-1, 3)
        me = bpy.data.meshes.new("s" + col)
        V, F = [], []
        for xx, yy, zz, hd in lst:
            f = np.array([math.cos(hd), math.sin(hd), 0])
            bz = -f
            bx = np.cross([0, 0, 1.0], bz)
            for k in range(0, len(tri), 3):
                i0 = len(V)
                for p in tri[k:k + 3]:
                    lx, ly, lz = p          # glTF local: x, y up, z back
                    V.append((xx + bx[0] * lx + bz[0] * lz, yy + bx[1] * lx + bz[1] * lz, zz + ly))
                F.append((i0, i0 + 1, i0 + 2))
        me.from_pydata(V, [], F)
        ob = bpy.data.objects.new("s" + col, me)
        mm = bpy.data.materials.new("m" + col)
        mm.use_nodes = True
        mm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = cols[col]
        ob.data.materials.append(mm)
        sc.collection.objects.link(ob)
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 24
    sc.cycles.use_denoising = False
    sc.render.resolution_x, sc.render.resolution_y = 1280, 720
    sc.render.filepath = out
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "glb":
        export(sys.argv[2])
    else:
        render(sys.argv[2], sys.argv[3])
