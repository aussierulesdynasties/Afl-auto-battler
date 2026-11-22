# Adds the traced reference polygons (aerial positions only) to the spec: 5 golf ponds, 2 blue tennis courts,
# the synthetic 5-a-side pitches; measures each one's median aerial colour for the palette entry (tone only).
import json, numpy as np
from PIL import Image, ImageDraw
S = 'spec/peoplefirst.json'; s = json.load(open(S))
A = np.asarray(Image.open('data/peoplefirst/sat.png').convert('RGB'))
def med(poly):
    px = [((x + 1500) * 2, (1500 - y) * 2) for x, y in poly]
    m = Image.new('L', (A.shape[1], A.shape[0])); ImageDraw.Draw(m).polygon(px, fill=1); m = np.asarray(m, bool)
    return [int(v) for v in np.median(A[m], 0)]
def g(X, Y): return [round(X / 8 - 220, 1), round(-380 - Y / 8, 1)]
tennis = [g(165, 495), g(440, 435), g(515, 720), g(210, 775)]
synth_d = [g(435, 330), g(725, 265), g(720, 165), g(870, 140), g(905, 450), g(790, 460), g(795, 565), g(505, 615)]
synth_l = [g(870, 140), g(1035, 165), g(1060, 405), g(905, 430)]
s['paint_poly'] = [p for p in s['paint_poly'] if p[0] not in ('water', 'court_blue', 'synth_dark', 'synth')]
for p in json.load(open('out/peoplefirst/ov/ponds.json')): s['paint_poly'].append(p)
s['paint_poly'] += [['court_blue', tennis], ['synth_dark', synth_d], ['synth', synth_l]]
s['palette']['court_blue'] = med(tennis); s['palette']['synth_dark'] = med(synth_d); s['palette']['synth'] = med(synth_l)
print({k: s['palette'][k] for k in ('court_blue', 'synth_dark', 'synth', 'water')})
json.dump(s, open(S, 'w'), indent=2); print(len(s['paint_poly']))
