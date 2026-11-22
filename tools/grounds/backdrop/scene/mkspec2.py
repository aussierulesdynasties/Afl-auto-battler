"""Spec for a ground's background scene from the GMHBA template, placed by geo/final.json. usage: mkspec2.py g"""
import json, sys, os, subprocess
g = sys.argv[1]
F = json.load(open(os.environ.get('WORK', '/home/user/work') + '/geo/final.json'))[g]
s = json.load(open('spec/gmhba.json'))
for k in ('netball_courts', 'paint_poly', 'coast_v2', 'horizon_v2', 'towers_v2'): s.pop(k, None)
glb = os.environ.get('WORK', '/home/user/work') + '/glb/%s.glb' % g
if F['yaw']:
    rg = os.environ.get('WORK', '/home/user/work') + '/glb/%s_rot.glb' % g
    if not os.path.exists(rg): subprocess.run(['python3', os.environ.get('WORK', '/home/user/work') + '/tools/rot_glb.py', '--', glb, rg, str(F['yaw'])], capture_output=True)
    glb = rg
s['palette'].update({'infield': [170, 128, 96], 'park_dry': [150, 138, 100], 'court_green': [58, 108, 80], 'turf_blue': [92, 150, 180], 'turf_runoff': [60, 104, 150]})
# rural grounds: open land OSM leaves untagged is paddock, not the town's grey-green verge (read as concrete from above)
if g in ('barossa', 'summit', 'bruce'): s['palette']['ground_default'] = [124, 132, 90]
s.update(name=g, lat=F['origin'][0], lon=F['origin'][1], glb=glb, landmarks=[], yaw=F['yaw'])
json.dump(s, open('spec/%s.json' % g, 'w'), indent=1)
print(g, s['lat'], s['lon'], 'yaw', F['yaw'])
