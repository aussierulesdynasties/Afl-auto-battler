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
if g in ('blacktown',): s['trees_to_footprint'] = True   # the model has its own measured bank: trees stand right up to it
# map outlines of buildings the ground model builds itself from measurement (local metres): left out of the scene
# roofs the model builds (its detail.py SOUTH), so no crown stands on them
if g in ('blacktown',): s['own_roofs'] = [[(-113.9, -101.4), (-101.0, -104.0), (-104.9, -124.9), (-117.9, -122.3)], [(-101.8, -108.0), (-91.1, -115.4), (-95.9, -122.3), (-103.6, -117.5)],
                                          [(-95.9, -122.3), (-103.3, -127.5), (-103.3, -132.3)], [(-103.0, -132.3), (-90.8, -115.4), (-67.6, -131.6), (-80.5, -148.7)]]
# the car park west of the indoor centre: the model has it (bays from the NSW aerial), the scene draws no cars or lines there
if g in ('blacktown',): s['own_lots'] = [[(-190, -60), (-140, -60), (-125, -200), (-170, -205)]]
# the three baseball diamonds round the ground: home plates and facings off a straight-down Google Earth shot (2025-07-24,
# 3.2 px a metre), the dirt warning track 5 m wide inside each fence; infield colour sampled from the same shot
if g in ('blacktown',):
    s['baseball_list'] = [{'home': [-298.5, -62.8], 'dir': -43.5, 'track': 5.0}, {'home': [-342.7, -212.7], 'dir': -40.0, 'track': 5.0},
                          {'home': [-421.6, -90.0], 'dir': -54.5, 'track': 5.0}]
    if os.environ.get('BG_REAL'): s['palette']['infield'] = [188, 120, 86]
# the path from the car park north-west past the baseball fields: mapped as a service road, a 3 m concrete footpath on the
# NSW aerial and Google Earth 2025
if g in ('blacktown',): s['osm_retag'] = {'979754558': {'highway': 'footway', 'surface': 'concrete'}}
# NSW grounds, real place: the state's 5 m ground model (dem_nsw.py) for the terrain
if g in ('blacktown',) and os.environ.get('BG_REAL'): s['dem_nsw'] = True
# the small trees on the model's own ground south of the stand (crown centres on the NSW aerial, 2026-11-23)
if g in ('blacktown',): s['extra_trees'] = [[-120.8, -76.0], [-114.8, -87.6], [-108.1, -95.7], [-82.6, -117.8], [-74.3, -123.2]]
if g in ('blacktown',): s['drop_buildings'] = [[(-125, -97), (-98, -99), (-60, -128), (-80, -156), (-112, -140), (-125, -126)],
                                                [(-241, -154), (-198, -154), (-198, -186), (-241, -186)]]   # the shade sails (map: two roofed buildings)
s.update(name=g, lat=F['origin'][0], lon=F['origin'][1], glb=glb, landmarks=[], yaw=F['yaw'])
json.dump(s, open('spec/%s.json' % g, 'w'), indent=1)
print(g, s['lat'], s['lon'], 'yaw', F['yaw'])
