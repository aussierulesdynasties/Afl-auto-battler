# layoutC6.json: C's plan re-read from the 2018-10 Esri image (Wayback 18820) turned into the old model frame and
# corrected for the satellite's lean (image point = ground point + K*h, K=(0.353,0.098), from the four light towers).
# Roof edge d (metres beyond the fence) read by hand on o22_*.png strips; heights z kept from layoutC5 until refit on 03.
import json, math, numpy as np
C5 = json.load(open('layoutC5.json')); A = json.load(open('layoutA.json')); B = json.load(open('layoutB.json'))
co = A['fence']['co']; K = A['fence']['K']; C0 = A['C0']
def rf(a):
    t = math.radians(a); return sum(co[k] * math.cos(k * t) for k in range(K + 1)) + sum(co[K + k] * math.sin(k * t) for k in range(1, K + 1))
def unwrap(a, ref):
    while a < ref - 180: a += 360
    while a > ref + 180: a -= 360
    return a
def fz(S, ref=-40):
    S = sorted((unwrap(s[0], ref), s[2]) for s in S); return lambda a: float(np.interp(unwrap(a, ref), [s[0] for s in S], [s[1] for s in S]))
rfz, rbz = fz(C5['RF']), fz(C5['RB'])
# heights read on photo 03 through camC13 with zrule.py rulers (2026-11-19); the east end (-40..50.5) keeps C5's values
ZF = [(116.7, 18), (150, 18), (180, 18), (-150, 18.3), (-145, 18), (-140, 18.8), (-135, 17.4), (-130, 16.8), (-120, 17), (-110, 17.2),
      (-100, 15.2), (-90, 16), (-80, 16.6), (-70, 15.6), (-60, 14.9), (-50, 14.2)]
ZB = [(116.7, 18), (150, 19), (180, 19), (-150, 19.5), (-145, 18.2), (-140, 18.3), (-135, 19.5), (-130, 18.2), (-110, 16.8),
      (-100, 14.5), (-90, 15.9), (-80, 17.1), (-70, 16.9), (-60, 16.3), (-50, 16.5), (-40, 18), (-30, 18.5), (50.5, 18.5)]
def zt(T, base, east):
    S = sorted((unwrap(a, -90), z) for a, z in T)
    def f(a):
        u = unwrap(a, -90)
        if east < unwrap(a, 0) <= 50.5: return base(a)
        return float(np.interp(u, [q[0] for q in S], [q[1] for q in S]))
    return f
rfz, rbz = zt(ZF, rfz, -50), zt(ZB, rbz, 99)
_rf0 = rfz; rfz = lambda a: min(_rf0(a), 18.0) if 30 <= unwrap(a, 0) <= 50.5 else _rf0(a)   # NE front no higher than the back
# east end -50..-20: back edge read on photo 03 (2018 satellite puts it up to 7 m further out; C copies photo 03)
# bowl, from the north-west corner (116.7) clockwise round the west, south and east to the north-east (46)
F = [(116.7, 15), (120, 16), (125, 17), (135, 17), (150, 17.5), (160, 17.5), (170, 17.5), (180, 18), (-170, 17.5), (-160, 16.5),
     (-150, 15.5), (-140, 15), (-130, 14.5), (-120, 15), (-100, 15), (-80, 15), (-60, 15), (-50, 15.5), (-40, 16.5), (-30, 17),
     (-20, 17), (-10, 17.5), (-7, 17.5), (-6, 22), (0, 21), (10, 21), (19, 21), (21, 18.5), (30, 18), (40, 17), (46, 17), (50.5, 14.7)]
Bk = [(116.7, 27), (120, 27), (124, 27), (126, 33), (135, 33), (140, 33), (150, 34), (160, 35), (170, 36), (180, 38), (-170, 38),
      (-160, 38), (-150, 38), (-140, 37), (-132, 34), (-130, 33), (-120, 32), (-110, 31), (-100, 30), (-90, 30), (-80, 30),
      (-70, 30.5), (-60, 31), (-50, 32.5), (-45, 32.2), (-40, 31.1), (-30, 29.8), (-20, 29.1), (-10, 34), (-7, 34), (-6, 40), (0, 40),
      (10, 40), (20, 39), (30, 39), (40, 38), (46, 37), (48, 35), (50.5, 30)]
C6 = dict(C5)
C6['RF'] = [[a, d, round(rfz(a), 2)] for a, d in F]
C6['RB'] = [[a, d, round(rbz(a), 2)] for a, d in Bk]
# north stand (46..116.7): roof deck front and back, heights from layoutB
def fzb(S, ref=100):
    S = sorted((unwrap(s[0], ref), s[2]) for s in S); return lambda a: float(np.interp(unwrap(a, ref), [s[0] for s in S], [s[1] for s in S]))
bfz, bbz = fzb(B['BF']), fzb(B['BB'])
NF = [(50.5, 14), (55, 14), (60, 12), (70, 12), (80, 13), (90, 12), (100, 11), (110, 12), (116.7, 14)]
NB = [(50.5, 25), (55, 25), (60, 24), (70, 24), (80, 22), (90, 23), (100, 24), (110, 27), (116.7, 27)]
C6['BF'] = [[a, d, round(bfz(a), 2)] for a, d in NF]
C6['BB'] = [[a, d, round(bbz(a), 2)] for a, d in NB]
# light towers: head seen in 2018-10, base = head - K*TH (TH from the photo fit)
TH = C5['TH']; kx, ky = 0.353, 0.098
heads = [(-24.0, 99.5), (90.0, 99.5), (-25.0, -66.5), (73.0, -70.5)]
tow = []
for hx, hy in heads:
    bx, by = hx - kx * TH, hy - ky * TH; a = math.degrees(math.atan2(by - C0[1], bx - C0[0]))
    d = math.hypot(bx - C0[0], by - C0[1]) - rf(a); tow.append([round(a, 1), round(d, 1)]); print('tower base', round(bx, 1), round(by, 1), '->', tow[-1])
C6['TOW'] = tow
json.dump(C6, open('layoutC6.json', 'w', newline=''), indent=0)
# podium and lift cores, read in image xy on pod1810/core1810.png, minus K*h for their height
def ad(x, y):
    a = math.degrees(math.atan2(y - C0[1], x - C0[0])); return [round(a, 2), round(math.hypot(x - C0[0], y - C0[1]) - rf(a), 2)]
def true(pts, h): return [ad(x - kx * h, y - ky * h) for x, y in pts]
C6['POD'] = true([(-100, -76), (-64, -76), (-64, -64), (-84, -56), (-97, -58)], 10.5)
core = true([(-128, -56), (-122, -50), (-119, -53), (-125, -59)], 25.1)
C6['COREP'] = core
# south-west tower (old frame): photo 03 puts it 22 m west of the 2018-10 satellite base; C copies photo 03
C6['TOW'][2] = ad(-74.4, -81.6); print('tower 3 from photo 03', C6['TOW'][2])
# near-side buildings under the roof lid, read on photo 03 through camC13 (feet cast to z 0, tops read over the feet)
from camlib import at_z
cam = json.load(open('camC13.json'))['p'][:7]
def foot(u, v, z=0.0):
    p = at_z(cam, u, v, 512, 314.5, z); return ad(p[0], p[1])
def back(pts, d=18.0): return pts + [[a, d] for a, _ in reversed(pts)]
grey = [ad(-139.4, 15.5), ad(-133.2, -15.0)]                                   # SW grey block, top 13.3
bay = [ad(-132.8, -17.7), ad(-119.6, -34.1), ad(-109.3, -51.7)]                 # stepped bay, ledge 11.8, top band 14.4
brick = [ad(-109.3, -51.7), ad(-127.0, -74.2), ad(-104.9, -78.9)]          # brick end block, three storeys, top 10.4
colo = [ad(-104.9, -78.9), ad(-97.5, -80.9), ad(-93.1, -83.6), ad(-70.0, -86.1), ad(-46.4, -87.9), ad(-43.4, -86.6)]  # colonnade, top 7.0
cores = []
for (ul, vl), (ur, vr) in (((441.7, 496.7), (490.0, 496.7)), ((490.0, 488.3), (536.7, 488.3))):
    l, r = foot(ul, vl, 7.0), foot(ur, vr, 7.0); cores.append([l, r, [r[0], r[1] - 4.0], [l[0], l[1] - 4.0]])
C6['NEAR'] = [[back(grey), 0.0, 13.3, 'facc', 'pad'], [back(bay), 0.0, 11.8, 'facc', 'pad'],
              [back([[a, d - 2.0] for a, d in bay], 18.0), 11.8, 14.4, 'facc', 'pad'],
              [back(brick), 0.0, 10.4, 'brickr', 'pad'], [back(colo), 0.0, 3.5, 'arcade', 'pad'], [back(colo), 3.5, 7.0, 'brickr', 'pad']] + [[c, 7.0, 20.6, 'facc', 'roofd'] for c in cores]
print('NEAR', [[round(p[0], 1) for p in b[0]] for b in C6['NEAR']])
C6['ANNEX'] = [[-178.9, 37.0], [-167.3, 37.0], [-167.3, 30.0], [-178.9, 30.0]]
print('POD', C6['POD']); print('CORE', core)
json.dump(C6, open('layoutC6.json', 'w', newline=''), indent=0)
print('ok')
# far-junction sign block (a ~50.5, photo 03 px 513-530 x 168-196): plain blue, no text, d 2-14, z 15-21
C6['NEAR'].append([[[48.4, 2.0], [52.0, 2.0], [52.0, 14.0], [48.4, 14.0]], 15.0, 21.0, 'signb', 'signb'])
json.dump(C6, open('layoutC6.json', 'w', newline=''), indent=0)
