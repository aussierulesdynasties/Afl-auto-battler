"""The far gums' pictures: four of trees.py's own near gums, drawn in Blender side on (the atlas' top row) and
from straight above (its bottom row) into a 2048 x 1024 atlas (RGBA, the sky cut out, the colour only: the
game lights the cards), for the cards that stand for every gum past trees.MID_R. gum_far.json gives each
picture's tree height, side picture's side and top picture's side in metres. The picture is of
our own model, so a far gum reads as the same tree as a near one.

    /path/to/bpy-python impostor.py tex/gum_far.png        (pip bpy 5.2.4)
"""
import math
import os
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import glb  # noqa: E402
import trees as T  # noqa: E402

CELL = 512
VARIANTS = [(12.0, 5.5, 101), (15.0, 7.0, 202), (9.0, 4.5, 303), (13.0, 6.5, 404)]   # height, crown radius, seed


def build(path):
    w = glb.Glb()
    for k, (h, rad, seed) in enumerate(VARIANTS):
        F = T.Forest()
        F.add(0.0, 0.0, 0.0, h, rad, seed, 0.0)    # r = 0: a near gum
        for name, b, mat in (("leaf%d" % k, F.leaf, w.material("gum_leaf", image=open(os.path.join(HERE, "tex", "leaves.png"), "rb").read(),
                                                                   mime="image/png", double=False, alpha_cut=0.5)),
                             ("bark%d" % k, F.bark, w.material("gum_bark"))):
            P, N, Fc, UV, C = b.arrays()
            P = P + np.array([k * 100.0, 0, 0])
            w.mesh(name, P, N, Fc, mat, uv=UV if name.startswith("leaf") else None, col=C)
    w.save(path)


def render(glb_path, out):
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=glb_path)
    sc = bpy.context.scene
    for o in sc.objects:                 # vertex colours into the base colour, as the game draws them
        if o.type != "MESH":
            continue
        for m in o.data.materials:
            nt = m.node_tree
            bsdf = nt.nodes.get("Principled BSDF")
            if bsdf is None:
                continue
            vc = nt.nodes.new("ShaderNodeVertexColor")
            mix = nt.nodes.new("ShaderNodeMix")
            mix.data_type = "RGBA"
            mix.blend_type = "MULTIPLY"
            mix.inputs[0].default_value = 1.0
            src = bsdf.inputs["Base Color"].links[0].from_socket if bsdf.inputs["Base Color"].links else None
            if src is not None:
                nt.links.new(src, mix.inputs[6])
            else:
                mix.inputs[6].default_value = (1, 1, 1, 1)
            nt.links.new(vc.outputs[0], mix.inputs[7])
            # The picture holds the tree's colour, not its lighting: the game lights the card. Only the
            # crown's own occlusion is kept (0.65 deep inside to 1 at the edge), as a gum's inner leaves
            # are darker.
            ao = nt.nodes.new("ShaderNodeAmbientOcclusion")
            ao.inputs["Distance"].default_value = 2.0
            k = nt.nodes.new("ShaderNodeMapRange")
            k.inputs["To Min"].default_value = 0.65
            nt.links.new(ao.outputs["AO"], k.inputs["Value"])
            shade = nt.nodes.new("ShaderNodeMix")
            shade.data_type = "RGBA"
            shade.blend_type = "MULTIPLY"
            shade.inputs[0].default_value = 1.0
            nt.links.new(mix.outputs[2], shade.inputs[6])
            nt.links.new(k.outputs[0], shade.inputs[7])
            em = nt.nodes.new("ShaderNodeEmission")
            nt.links.new(shade.outputs[2], em.inputs["Color"])
            tr = nt.nodes.new("ShaderNodeBsdfTransparent")
            ms = nt.nodes.new("ShaderNodeMixShader")
            alpha = bsdf.inputs["Alpha"].links[0].from_socket if bsdf.inputs["Alpha"].links else None
            if alpha is not None:
                nt.links.new(alpha, ms.inputs[0])
            else:
                ms.inputs[0].default_value = 1.0
            nt.links.new(tr.outputs[0], ms.inputs[1])
            nt.links.new(em.outputs[0], ms.inputs[2])
            mout = [n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"][0]
            nt.links.new(ms.outputs[0], mout.inputs["Surface"])
    sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", "SUN"))
    sun.data.energy = 3.5
    sun.data.use_shadow = False      # the game draws the backdrop with no shadows; the picture matches
    sun.rotation_euler = (math.radians(35), 0, math.radians(20))
    sc.collection.objects.link(sun)
    world = bpy.data.worlds.new("w")
    sc.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.55, 0.62, 0.7, 1)
    world.node_tree.nodes["Background"].inputs[1].default_value = 2.0
    sc.render.engine = "CYCLES"
    sc.cycles.samples = 48
    sc.cycles.device = "CPU"
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = CELL, CELL
    sc.view_settings.view_transform = "Standard"
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam"))
    cam.data.type = "ORTHO"
    sc.collection.objects.link(cam)
    sc.camera = cam
    tiles, sides = [], []
    for k, (h, rad, seed) in enumerate(VARIANTS):
        # the tree's own extent (glTF x, y, z -> Blender x, -z, y): it stands at x = 100 k on z = 0
        vs = [o.matrix_world @ v.co for o in sc.objects if o.type == "MESH" for v in o.data.vertices
              if abs((o.matrix_world @ v.co).x - k * 100.0) < 40]
        wx = max(max(abs(v.x - k * 100.0) for v in vs), max(abs(v.y) for v in vs)) * 2
        top = max(v.z for v in vs)
        size = max(top, wx) * 1.03
        sides.append([h, round(size, 3), round(wx * 1.03, 3)])
        cam.data.ortho_scale = size
        cam.location = (k * 100.0, -60.0, size / 2 - 0.3)
        cam.rotation_euler = (math.radians(90), 0, 0)
        tmp = os.path.join(tempfile.gettempdir(), "gum_far_%d.png" % k)
        sc.render.filepath = tmp
        bpy.ops.render.render(write_still=True)
        tiles.append(tmp)
    # the same four from straight above (the crown as a blimp or a high camera sees it), north up
    for k, (h, rad, seed) in enumerate(VARIANTS):
        cam.data.ortho_scale = sides[k][2]
        cam.location = (k * 100.0, 0.0, 80.0)
        cam.rotation_euler = (0, 0, 0)
        tmp = os.path.join(tempfile.gettempdir(), "gum_top_%d.png" % k)
        sc.render.filepath = tmp
        bpy.ops.render.render(write_still=True)
        tiles.append(tmp)
    from PIL import Image
    atlas = Image.new("RGBA", (CELL * len(VARIANTS), CELL * 2), (0, 0, 0, 0))
    for k, t in enumerate(tiles):
        atlas.paste(Image.open(t).convert("RGBA"), ((k % len(VARIANTS)) * CELL, (k // len(VARIANTS)) * CELL))
    # under transparent texels, the mean leaf colour (no dark fringe when the texture is filtered)
    a = np.asarray(atlas).astype(np.float32)
    m = a[..., 3] > 128
    mean = a[m][:, :3].mean(0)
    a[~m, :3] = mean
    a[..., 3] = np.where(m, 255, 0)
    Image.fromarray(a.astype(np.uint8)).save(out)
    import json
    json.dump(sides, open(out[:-4] + ".json", "w"))
    print("impostor atlas", out, sides)


if __name__ == "__main__":
    tmp = os.path.join(tempfile.gettempdir(), "gums_for_impostor.glb")
    build(tmp)
    render(tmp, sys.argv[1])
