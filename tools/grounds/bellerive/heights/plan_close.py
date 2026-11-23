"""The 5-point roof heights again from 200 m up instead of 800 m (2026-11-23). From 800 m Google Earth streams a coarse
mesh and flattens a roof: houses read 1.4 to 2.7 m above the street and two-storey townhouses as cottages (PC check
r5, st_house). Same points as plan.py (points5.json), regrouped into views 120 by 70 m:
  python3 plan_close.py                              # $BELLERIVE_WORK/hgt/points5.json -> hgt/plan6.json
  node ge_hover.js $BELLERIVE_WORK/hgt/plan6.json $BELLERIVE_WORK/hgt6/hgt/s5
  BELLERIVE_WORK=$BELLERIVE_WORK/hgt6 python3 read.py   # (copy points5.json into hgt6/hgt first)"""
import json, math, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import houses_ge as H
W = os.environ['BELLERIVE_WORK']
RANGE = 200.0
K = H.K * 800.0 / RANGE                  # pixels a metre at RANGE (plan.py's scale is for 800 m)
LAT0, LON0 = -42.8773092, 147.3737365    # surrounds.py's origin
P = json.load(open(W + '/hgt/points5.json'))
views = {}
for name, e in P.items():
    c = [sum(v[0] for v in e['pts'].values()) / 5, sum(v[1] for v in e['pts'].values()) / 5]
    views.setdefault((round(c[0] / 120.0), round(c[1] / 70.0)), []).append((name, e))
plan = []
for (i, j), hs in sorted(views.items()):
    ce, cz = i * 120.0, j * 70.0          # the view's centre, model x and z (z south)
    lat = LAT0 - cz / 110574.0
    lon = LON0 + ce / (111320.0 * math.cos(math.radians(LAT0)))
    url = 'https://earth.google.com/web/@%.7f,%.7f,10.0a,%.1fd,35y,0h,0t,0r' % (lat, lon, RANGE)
    pts = [[name + '__' + k, round(640 + (x - ce) * K, 1), round(360 + (z - cz) * K + 140, 1)]
           for name, e in hs for k, (x, z) in e['pts'].items()]
    plan.append([url, pts])
json.dump(plan, open(W + '/hgt/plan6.json', 'w'))
print(len(plan), 'views', sum(len(p) for _, p in plan), 'points')
