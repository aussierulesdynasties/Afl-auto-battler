# model_in6.json: plan from satellite (fence ellipse fit, roof ring ellipse fits on Wayback 11135 + current, booms from 11135)
import json, math, numpy as np
d = json.load(open('model_in5.json'))
C = (2.47, -3.47)
def ell(A, B, th, n=720):
    th = math.radians(th); a = [-math.pi + 2 * math.pi * i / n for i in range(n)]
    r = [1 / math.sqrt((math.cos(x - th) / A) ** 2 + (math.sin(x - th) / B) ** 2) for x in a]
    return [a, r]
d['Cc'] = list(C)
d['RI'] = ell(92.7, 81.5, 7.8)          # boom tips: membrane edge fit minus mean scallop (2 m * 2/3)
d['RO'] = ell(115.0, 103.67, 7.0)
d['RF'] = [d['RO'][0], [r - 2.6 for r in d['RO'][1]]]
d['pitch'] = ell(86.88, 73.71, 5.0)     # seat front / fence line
d['knobs']['fence'] = 0.0
b = np.load('sat/booms_obs.npy'); b = sorted(((x + math.pi) % (2 * math.pi)) - math.pi for x in b)
d['booms'] = [float(x) for x in b]
old = d['towers']
base = [(80.8, -97.1), (-99.0, -78.0), (96.6, 76.5), (-77.0, 105.5)]   # SE SW NE NW, pole bases on 11135 + current
d['towers'] = [[x, y, h] for (x, y), (_, _, h) in zip(base, old)]
d['t411'] = None
json.dump(d, open('model_in6.json', 'w'))
print(len(d['booms']), d['towers'])
# south screen: face 2.5 m on the field side of the seat front (satellite 11135: top edge at y -76 leaned 2.2 m),
# same ends as the photo fit (x -0.9 and -22.2), ends on the seat-front line
import numpy as np
A, R = d['pitch']; pts = []
for X in (-0.9, -22.2):
    best = min(((abs(C[0] + r * math.cos(a) - X), (C[0] + r * math.cos(a), C[1] + r * math.sin(a))) for a, r in zip(A, R) if math.sin(a) < 0))
    pts.append(list(best[1]))
d['screen'] = pts
json.dump(d, open('model_in6.json', 'w'))
print('screen', pts)
