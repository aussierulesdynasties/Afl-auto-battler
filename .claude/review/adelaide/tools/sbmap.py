"""map sb_c11 crop pixels (big_c11 crop 864,680-3040,1760 shown at 1600 px) to the scoreboard face (s, z above zb),
by projecting the face through the c11 camera (camH11b.json) and inverting the plane homography"""
import json, math, sys, os, numpy as np
sys.argv = ['hill.py']; src = open('tools/hill.py', encoding='utf-8').read()
g = {'__file__': os.path.abspath('tools/hill.py'), '__name__': 'x'}
exec(compile(src[:src.index('# ---------------------------------------------------------------- heritage scoreboard')], 'hill', 'exec'), g)
SB, U, N = g['SB'], g['U'], g['N']; zb = float(g['hill_z'](np.array([SB[0] + U * np.linalg.norm(SB[3] - SB[0]) / 2]))[0])
T_F = 2.0
c = json.load(open('camH11b.json')); Cx, Cy, Cz, yaw, pt, roll, fo, cx, cy = c['p']
f = np.array([math.cos(yaw) * math.cos(pt), math.sin(yaw) * math.cos(pt), math.sin(pt)]); r = np.array([math.sin(yaw), -math.cos(yaw), 0])
u = np.cross(r, f); r2 = math.cos(roll) * r + math.sin(roll) * u; u2 = -math.sin(roll) * r + math.cos(roll) * u
def proj(P):
    d = P - np.array([Cx, Cy, Cz]); return np.c_[cx + fo * (d @ r2) / (d @ f), cy - fo * (d @ u2) / (d @ f)]
k = 3840 / c['W']
def tocrop(px): return np.c_[(px[:, 0] * k - 864) / 1.36, (px[:, 1] * k - 680) / 1.36]
S, Z = np.meshgrid(np.linspace(0, 17.4, 8), np.linspace(3, 12, 6)); S, Z = S.ravel(), Z.ravel()
P3 = np.c_[(SB[0] + np.outer(S, U) + T_F * N), zb + Z]
q = tocrop(proj(P3))
A = []
for (x, y), (s, z) in zip(q, zip(S, Z)):
    A.append([s, z, 1, 0, 0, 0, -x * s, -x * z, -x]); A.append([0, 0, 0, s, z, 1, -y * s, -y * z, -y])
H = np.linalg.svd(np.array(A))[2][-1].reshape(3, 3); Hi = np.linalg.inv(H)
def crop2sz(x, y):
    v = Hi @ [x, y, 1]; return v[0] / v[2], v[1] / v[2]
if __name__ == '__main__':
    for x, y in ((18, 760), (1560, 760), (18, 40), (1560, 40)): print((x, y), np.round(crop2sz(x, y), 2))

# lettering boxes traced on rend/pf/sb_c11.png (x0, y_top, x1, y_bottom), board yellow
WORDS = [('V', 958, 42, 996, 88), ('BOWLERS', 462, 105, 650, 165), ('WKTS', 668, 103, 765, 160), ('RUNS', 790, 102, 892, 158),
         ('BATSMEN', 918, 98, 1105, 152), ('OUT', 1133, 97, 1210, 148), ('B', 1220, 97, 1245, 148), ('RUNS', 1255, 96, 1347, 147),
         ('FALL', 1365, 93, 1430, 145), ('OF', 1433, 104, 1458, 128), ('WKTS', 1460, 90, 1550, 142),
         ('1', 42, 117, 60, 165), ('ST', 66, 118, 96, 141), ('INNINGS', 112, 115, 255, 163),
         ('2', 38, 170, 62, 215), ('ND', 65, 171, 97, 194), ('INNINGS', 112, 168, 255, 214),
         ('1', 42, 277, 60, 323), ('ST', 66, 278, 96, 301), ('INNINGS', 112, 275, 255, 322),
         ('2', 38, 330, 62, 375), ('ND', 65, 331, 97, 354), ('INNINGS', 112, 328, 255, 374),
         ('WICKETS', 46, 396, 246, 445), ('SUNDRIES', 38, 590, 248, 642), ('TOTAL', 58, 656, 246, 707), ('UMPIRES', 720, 698, 903, 745),
         ('1', 434, 173, 450, 218), ('2', 428, 226, 460, 272), ('3', 428, 279, 461, 325), ('4', 428, 331, 461, 377), ('5', 428, 385, 461, 432),
         ('6', 428, 438, 461, 486), ('7', 428, 491, 461, 539), ('8', 428, 544, 461, 592), ('9', 428, 598, 461, 645),
         ('1', 1380, 158, 1394, 197), ('FOR', 1398, 166, 1437, 195), ('2', 1370, 206, 1402, 252), ('3', 1372, 260, 1402, 307),
         ('4', 1372, 313, 1405, 360), ('5', 1372, 367, 1405, 413), ('6', 1373, 421, 1405, 468), ('7', 1374, 475, 1405, 522),
         ('8', 1374, 530, 1405, 578), ('9', 1374, 583, 1405, 630), ('OVERS', 1345, 632, 1435, 665), ("R'QD", 1357, 672, 1428, 705)]
if __name__ == '__main__':
    out = []
    for w, x0, y0, x1, y1 in WORDS:
        c = np.array([crop2sz(x, y) for x, y in ((x0, y0), (x1, y0), (x1, y1), (x0, y1))])
        out.append((w, *np.round([c[:, 0].min(), c[:, 1].min(), c[:, 0].max(), c[:, 1].max()], 2).tolist()))
    print(out)
