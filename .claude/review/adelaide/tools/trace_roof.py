"""Trace a roof outline from the Esri mosaic and write it to spec roofs[NAME].poly (+ valleys).
Esri tops lean ~ +0.82 px/m east, +0.26 px/m south: each outline point is moved back by its height H (m).
usage: H=30 python tools/trace_roof.py east   (box and seams below, Esri px)"""
import numpy as np, json, math, os, sys
from PIL import Image
from scipy import ndimage
from skimage import measure
sys.path.insert(0, 'tools'); import esri
name = sys.argv[1]; H = float(os.environ.get('H', 30))
CFG = {'east': dict(box=(1050, 720, 1440, 1470),
                    seams=[(1222, 869.5), (1289.5, 996), (1327, 1171), (1311, 1311)])}[name]
x0, y0, x1, y1 = CFG['box']
a = np.asarray(Image.open('esri/mosaic.jpg').convert('RGB')).astype(int)[y0:y1, x0:x1]
m = (a.min(2) > 185) & (a.max(2) - a.min(2) < 35)
m = ndimage.binary_closing(ndimage.binary_opening(m, iterations=1), iterations=4)
lab, n = ndimage.label(m); m = lab == 1 + np.argmax(np.bincount(lab.ravel())[1:])
m = ndimage.binary_fill_holes(m)
Image.fromarray((m * 255).astype(np.uint8)).save('grid/esri_%smask.png' % name)
c = max(measure.find_contours(m.astype(float), 0.5), key=len)[:, ::-1] + [x0, y0]   # (px, py)
lean = np.array([0.82, 0.26]) * H
P = np.array([esri.px2m(*(p - lean)) for p in c])
# resample at 2 m along the closed loop, smooth (sigma 1.5 m), ccw
L = np.r_[0, np.cumsum(np.linalg.norm(np.diff(np.r_[P, P[:1]], axis=0), axis=1))]
s = np.arange(0, L[-1], 2.0); Q = np.c_[np.interp(s, L, np.r_[P[:, 0], P[0, 0]]), np.interp(s, L, np.r_[P[:, 1], P[0, 1]])]
Q = ndimage.gaussian_filter1d(Q, 0.75, axis=0, mode='wrap')
if np.sum(Q[:, 0] * np.roll(Q[:, 1], -1) - np.roll(Q[:, 0], -1) * Q[:, 1]) < 0: Q = Q[::-1]
sp = json.load(open('spec.json', encoding='utf-8')); rf = [r for r in sp['roofs'] if r['name'] == name][0]
exec(open('tools/gen.py').read().split('PC =')[0][:0])  # (PC below)
PC = np.array(json.loads(os.environ['PC']))
ang = lambda V: (np.arctan2(V[:, 1] - PC[1], V[:, 0] - PC[0]) - rf['amid'] + math.pi) % (2 * math.pi) - math.pi
aa = ang(Q); a0, a1 = aa.min(), aa.max()
sv = sorted(float((ang(np.array([esri.px2m(*(np.array(p) - lean))]))[0] - a0) / (a1 - a0)) for p in CFG['seams'])
rf['poly'] = [[round(float(x), 2), round(float(y), 2)] for x, y in Q]; rf['valleys'] = [0.0] + [round(v, 3) for v in sv] + [1.0]
rf['lobes'] = len(sv) + 1; rf.pop('off', None)
json.dump(sp, open('spec.json', 'w', encoding='utf-8', newline=''), indent=1)
print(name, len(Q), 'pts; valleys', rf['valleys'], 'area m2', round(abs(np.sum(Q[:, 0] * np.roll(Q[:, 1], -1) - np.roll(Q[:, 0], -1) * Q[:, 1])) / 2))
