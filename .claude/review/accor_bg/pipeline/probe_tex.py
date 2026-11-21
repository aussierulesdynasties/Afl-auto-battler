import bpy, sys
p = sys.argv[sys.argv.index('--') + 1]; mat = sys.argv[sys.argv.index('--') + 2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=p)
m = bpy.data.materials[mat]
for n in m.node_tree.nodes:
    if n.bl_idname == 'ShaderNodeTexImage':
        im = n.image; px = list(im.pixels); w, h = im.size
        s = [0, 0, 0]; c = 0
        for i in range(0, len(px), 4 * 7):
            s[0] += px[i]; s[1] += px[i + 1]; s[2] += px[i + 2]; c += 1
        lin = [v / c for v in s]
        srgb = [round(255 * ((1.055 * v ** (1 / 2.4) - 0.055) if v > 0.0031308 else 12.92 * v)) for v in lin]
        print('TEX', im.name, w, h, im.colorspace_settings.name, 'avg_srgb', srgb)
