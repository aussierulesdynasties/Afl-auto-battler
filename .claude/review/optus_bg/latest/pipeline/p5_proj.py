import json, math, numpy as np
H = np.load('data/optus/prep/near_h.npy'); print('near_h', H.shape)
v = json.load(open('out/optus/job_ph_p5_g.json'))['views'][0]; print(v)
def hz(x, y, flip):
    i, j = int(round((x + 1500) / 7.5)), int(round((y + 1500) / 7.5))
    return float(H[j, i] if not flip else H[400 - j, i])
C = np.array(v['cam'], float); L = np.array(v['look'], float)
f = L - C; f /= np.linalg.norm(f); r = np.cross(f, [0, 0, 1]); r /= np.linalg.norm(r); u = np.cross(r, f)
W, Hh = v.get('res', [1280, 960]) if 'res' in v else (1280, 960); k = (W / 2) / math.tan(math.radians(v['fov_h'] / 2))
def px(p):
    d = np.array(p) - C; return round(W / 2 + k * (d @ r) / (d @ f)), round(Hh / 2 - k * (d @ u) / (d @ f))
for flip in (False, True):
    print('flip', flip, 'ground at cam', hz(C[0], C[1], flip), 'tower base', hz(437, -908, flip), 'metropol base', hz(446, -1092, flip))
    zt = hz(437, -908, flip) - 1; zm = hz(446, -1092, flip) - 1
    print(' tower top', px((437, -908, zt + 105)), 'metropol top W/E', px((350, -1105, zm + 52)), px((470, -1100, zm + 52)), 'metropol east foot', px((505, -1085, zm)))
