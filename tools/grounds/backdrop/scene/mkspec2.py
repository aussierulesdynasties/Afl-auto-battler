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
if os.environ.get('BG_REAL'): s['cover'].append(['leisure', 'track', 'sand'])
if os.environ.get('BG_REAL'):   # building sites: bare sand or fill, coloured from the aerial, not paving
    s['cover'] = [[k, v.replace('|construction', ''), c] if k == 'landuse' else [k, v, c] for k, v, c in s['cover']] + [['landuse', 'construction', 'park_dry']]   # race and trotting tracks: their own patch, coloured from the aerial
# real place: how far out the city's towers (30 m and up, Overture) still stand on the skyline; the CBD is in view from these
s['city_r_m'] = {'ikon_park': 5500, 'whitten': 8000, 'windy_hill': 8500}.get(g, 4000)
# real place among mountains (kunanyi over Hobart, the Brindabellas, the Adelaide Hills, Wellington's ridges): the far
# land on an 80 m grid, not 250 m, so a ridge keeps its real line instead of sawtooth facets (reduce.py thins it by shape)
if os.environ.get('BG_REAL') and g in ('north_hobart', 'macpoint', 'bruce', 'summit', 'sky', 'bellerive', 'york_park', 'manuka'): s['far_step_m'] = 80
if os.environ.get('BG_REAL'): s['tree_lod_m'] = [300.0, 700.0]   # real place: every crown kept, simpler sooner
if os.environ.get('BG_REAL'): s['real'] = True   # real place: aerial colours, Sentinel-2, canopy, Overture heights (real.py)
_lmj = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'real_lm.json')
if os.environ.get('BG_REAL') and os.path.exists(_lmj): s['real_lm'] = json.load(open(_lmj)).get(g, [])   # landmarks (real_lm.py)
s.update(name=g, lat=F['origin'][0], lon=F['origin'][1], glb=glb, landmarks=[], yaw=F['yaw'])
json.dump(s, open('spec/%s.json' % g, 'w'), indent=1)
print(g, s['lat'], s['lon'], 'yaw', F['yaw'])
