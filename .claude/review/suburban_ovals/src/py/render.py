"""Render views of a built oval.
    blender -b BLEND -P render.py -- JOB.json
JOB: {"out": dir, "res": [w,h], "sun": {"az": deg (0 = +x, ccw), "el": deg, "power": W},
      "views": [{"name":..., "cam": [x,y,z], "look": [x,y,z], "fov_h": deg, "roll": deg} |
                {"name":..., "orbit": {"r":m, "z":m, "look":[..], "frames": N, "start_deg": a, "fov_h": deg}}]}
"""
import bpy, json, math, os, sys
from mathutils import Vector, Euler

JP = sys.argv[sys.argv.index("--") + 1]
job = json.load(open(JP))
job["out"] = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(JP)), job["out"])) if not os.path.isabs(job["out"]) else job["out"]
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE" if "BLENDER_EEVEE" in [e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE_NEXT"
w, h = job.get("res", [1600, 900])
sc.render.resolution_x, sc.render.resolution_y = w, h
sc.render.resolution_percentage = 100
sc.render.film_transparent = False
sc.view_settings.view_transform = "Standard"
sc.view_settings.look = "None"
try:
    sc.eevee.taa_render_samples = job.get("samples", 32)
    sc.eevee.use_shadows = True
    sc.eevee.shadow_ray_count = 2
except Exception:
    pass

# world: plain daylight sky gradient (blue overhead, pale at horizon)
world = bpy.data.worlds.new("sky"); sc.world = world; world.use_nodes = True
nt = world.node_tree; nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputWorld"); bg = nt.nodes.new("ShaderNodeBackground")
sep = nt.nodes.new("ShaderNodeSeparateXYZ"); tc = nt.nodes.new("ShaderNodeTexCoord")
ramp = nt.nodes.new("ShaderNodeValToRGB")
sky = job.get("sky", [[0.0, (0.80, 0.86, 0.92)], [0.45, (0.42, 0.62, 0.86)]])
ramp.color_ramp.elements[0].position = sky[0][0]; ramp.color_ramp.elements[0].color = (*sky[0][1], 1)
ramp.color_ramp.elements[1].position = sky[1][0]; ramp.color_ramp.elements[1].color = (*sky[1][1], 1)
nt.links.new(tc.outputs["Generated"], sep.inputs["Vector"]); nt.links.new(sep.outputs["Z"], ramp.inputs["Fac"])   # view direction z = up
nt.links.new(ramp.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = job.get("sky_strength", 1.0)
nt.links.new(bg.outputs["Background"], out.inputs["Surface"])

s = job.get("sun", {"az": 120, "el": 50, "power": 4.5})
sun = bpy.data.lights.new("sun", "SUN"); sun.energy = s.get("power", 4.5); sun.angle = math.radians(1.0)
so = bpy.data.objects.new("sun", sun); sc.collection.objects.link(so)
az, el = math.radians(s["az"]), math.radians(s["el"])
d = Vector((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))  # toward the sun
so.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()

cam = bpy.data.cameras.new("cam"); co = bpy.data.objects.new("cam", cam); sc.collection.objects.link(co); sc.camera = co
cam.clip_start = 0.5; cam.clip_end = 3000; cam.sensor_fit = "HORIZONTAL"; cam.sensor_width = 36


def aim(pos, look, fov_h, roll=0.0, shift=(0, 0)):
    co.location = Vector(pos)
    q = (Vector(look) - Vector(pos)).to_track_quat("-Z", "Y")
    co.rotation_euler = q.to_euler()
    if roll:
        co.rotation_euler.rotate_axis("Z", math.radians(roll))
    cam.lens = 18.0 / math.tan(math.radians(fov_h) / 2)
    cam.shift_x, cam.shift_y = shift


os.makedirs(job["out"], exist_ok=True)
for v in job["views"]:
    if "orbit" in v:
        o = v["orbit"]; n = o.get("frames", 4)
        fr = o.get("only")  # list of frame indices to render
        for i in range(n):
            if fr is not None and i not in fr:
                continue
            a = math.radians(o.get("start_deg", 0)) + 2 * math.pi * i / n
            pos = (o["look"][0] + o["r"] * math.cos(a), o["look"][1] + o["r"] * math.sin(a), o["z"])
            aim(pos, o["look"], o.get("fov_h", 40))
            sc.render.filepath = os.path.join(job["out"], "%s_%03d.png" % (v["name"], i))
            bpy.ops.render.render(write_still=True)
    elif "video" in v:   # turntable mp4: camera keyframed round the orbit, written by Blender's own encoder
        o = v["video"]; n = o.get("frames", 96)
        sc.frame_start, sc.frame_end = 1, n; sc.render.fps = o.get("fps", 24)
        rx, ry = sc.render.resolution_x, sc.render.resolution_y
        sc.render.resolution_x, sc.render.resolution_y = o.get("res", [1280, 720])
        cam.lens = 18.0 / math.tan(math.radians(o.get("fov_h", 50)) / 2)
        for i in range(n):
            a = math.radians(o.get("start_deg", 0)) + 2 * math.pi * i / n
            co.location = Vector((o["look"][0] + o["r"] * math.cos(a), o["look"][1] + o["r"] * math.sin(a), o["z"]))
            co.rotation_euler = (Vector(o["look"]) - co.location).to_track_quat("-Z", "Y").to_euler()
            co.keyframe_insert("location", frame=i + 1); co.keyframe_insert("rotation_euler", frame=i + 1)
        try:
            sc.eevee.taa_render_samples = o.get("samples", 12)
        except Exception:
            pass
        # PNG frames; mp4 encoded outside Blender (py/enc.py) - Blender's encoder left empty files under load
        fd = os.path.join(job["out"], v["name"] + "_frames"); os.makedirs(fd, exist_ok=True)
        sc.render.image_settings.file_format = "PNG"
        sc.render.filepath = os.path.join(fd, "f_")
        bpy.ops.render.render(animation=True)
        sc.render.resolution_x, sc.render.resolution_y = rx, ry
    elif "rt" in v:   # camera from rotation matrix (OpenCV convention) + centre
        import mathutils
        Rcv = mathutils.Matrix(v["rt"]["R"]); C = Vector(v["rt"]["C"])
        # OpenCV camera: x right, y down, z forward. Blender camera: x right, y up, -z forward.
        Rw = Rcv.transposed() @ mathutils.Matrix(((1, 0, 0), (0, -1, 0), (0, 0, -1)))
        co.matrix_world = mathutils.Matrix.Translation(C) @ Rw.to_4x4()
        cam.lens = 18.0 / math.tan(math.radians(v["fov_h"]) / 2)
        cam.shift_x, cam.shift_y = v.get("shift", (0, 0))
        sc.render.filepath = os.path.join(job["out"], v["name"] + ".png")
        bpy.ops.render.render(write_still=True)
    else:
        aim(v["cam"], v["look"], v.get("fov_h", 40), v.get("roll", 0), v.get("shift", (0, 0)))
        sc.render.filepath = os.path.join(job["out"], v["name"] + ".png")
        bpy.ops.render.render(write_still=True)
print("RENDERED", len(job["views"]))
