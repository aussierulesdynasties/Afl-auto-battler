"""Photo overlay jobs for optus. photo_ov.py writes out/optus/job_ph_<n>.json from VIEWS (cam/look z above terrain)."""
import json, math
VIEWS = json.load(open('out/optus/ph_views.json'))
for n, v in VIEWS.items():
    w, h = v['res']
    json.dump({'out': 'photo', 'res': [w, h], 'samples': 16, 'sun': v.get('sun', {'az': 60, 'el': 50, 'power': 4.5}),
               'sky': [[0.0, [0.77, 0.84, 0.89]], [0.45, [0.25, 0.49, 0.77]]],
               'views': [{'name': n, 'cam': v['cam'], 'look': v['look'], 'fov_h': v['fov_h']}]}, open('out/optus/job_ph_%s.json' % n, 'w'))
