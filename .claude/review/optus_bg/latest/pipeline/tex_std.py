"""List every image texture inside a GLB with its grey stddev. blender -b -P tex_std.py -- scene.glb"""
import bpy, sys, numpy as np
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=sys.argv[sys.argv.index('--') + 1])
for im in bpy.data.images:
    if im.size[0] == 0: continue
    a = np.empty(im.size[0] * im.size[1] * im.channels, np.float32); im.pixels.foreach_get(a); a = a.reshape(-1, im.channels)
    g = (a[:, :3] @ np.array([0.299, 0.587, 0.114]) if im.channels >= 3 else a[:, 0]) * 255
    print('TEX %-28s %5dx%-5d std %6.1f mean %6.1f' % (im.name, im.size[0], im.size[1], g.std(), g.mean()))
