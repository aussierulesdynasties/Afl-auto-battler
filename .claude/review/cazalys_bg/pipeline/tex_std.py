import bpy, numpy as np, os
for im in bpy.data.images:
    if not im.filepath or im.size[0] == 0: continue
    a = np.array(im.pixels[:], np.float32).reshape(-1, im.channels)[:, :3]
    g = (a @ np.array([0.299, 0.587, 0.114])) * 255
    print('STD %-40s %5dpx %6.1f' % (os.path.basename(im.filepath), im.size[0], g.std()))
