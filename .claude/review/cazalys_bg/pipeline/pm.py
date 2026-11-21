"""Photo match: pm.py name photo.jpg x y h yaw_compass_deg pitch_deg fov_h [roll] -> renders scene from that camera, writes side + 50% blend."""
import sys, json, math, subprocess, os
from PIL import Image
n, ph = sys.argv[1], sys.argv[2]; x, y, h, yaw, pit, fov = map(float, sys.argv[3:9]); roll = float(sys.argv[9]) if len(sys.argv) > 9 else 0
W, H = Image.open(ph).size; R = [1280, round(1280 * H / W)]
a = math.radians(90 - yaw); p = math.radians(pit)
look = [x + 100 * math.cos(p) * math.cos(a), y + 100 * math.cos(p) * math.sin(a), h + 100 * math.sin(p)]
J = {"out": os.path.abspath("out/cazalys/photo"), "res": R, "samples": 24, "sun": {"az": 110, "el": 45, "power": 4.5},
     "sky": [[0.0, [0.77, 0.84, 0.89]], [0.45, [0.25, 0.49, 0.77]]], "views": [{"name": n, "cam": [x, y, h], "look": look, "fov_h": fov, "roll": roll}]}
json.dump(J, open('out/cazalys/photo/job_%s.json' % n, 'w'))
subprocess.run(['C:/Python314/python.exe', '-E', 'ground_job.py', 'cazalys', 'out/cazalys/photo/job_%s.json' % n, 'out/cazalys/photo/job_%s_g.json' % n], capture_output=True)
subprocess.run(['C:/Program Files/Blender Foundation/Blender 5.2/blender.exe', '-b', 'out/cazalys/scene.blend', '-P', 'render.py', '--', 'out/cazalys/photo/job_%s_g.json' % n], capture_output=True)
r = Image.open('out/cazalys/photo/%s.png' % n).convert('RGB'); q = Image.open(ph).convert('RGB').resize(r.size)
Image.blend(r, q, 0.5).save('out/cazalys/photo/%s_blend.jpg' % n, quality=85)
s = Image.new('RGB', (r.width * 2, r.height)); s.paste(q, (0, 0)); s.paste(r, (r.width, 0)); s.resize((r.width, r.height // 2)).save('out/cazalys/photo/%s_side.jpg' % n, quality=85)
print('done', n, R)
