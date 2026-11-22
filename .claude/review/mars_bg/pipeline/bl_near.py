import json, sys, math
B = json.load(open('data/mcg/prep/buildings.json'))
for nm, x, y, r in [('A108', -1713, -347, 40), ('Eureka', -1662, -174, 40), ('Rialto', -2265, 140, 45), ('Spire', -1320, -164, 40), ('Shrine', -880, -1162, 60), ('Skip', 2413, 983, 40)]:
    print('==', nm)
    for i, b in enumerate(B):
        cx = sum(p[0] for p in b['p']) / len(b['p']); cy = sum(p[1] for p in b['p']) / len(b['p'])
        if math.hypot(cx - x, cy - y) < r:
            xs = [p[0] for p in b['p']]; ys = [p[1] for p in b['p']]
            print(i, b['c'], 'h', round(b['h'], 1), 'n', len(b['p']), 'c', round(cx), round(cy), 'bbox', round(max(xs) - min(xs)), round(max(ys) - min(ys)), {k: v for k, v in b.items() if k not in ('p', 'c', 'h')})
