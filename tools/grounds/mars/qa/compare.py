"""Mars Stadium's Google Earth side-by-sides through the shared compare tool (tools/grounds/ge_compare.py, #2015).

  python3 tools/grounds/mars/qa/compare.py plan|level|sheet <workdir> [out.jpg] [title]

Same steps as ge_compare.py's docstring, with Mars's entry: the model origin is the OpenStreetMap pitch centroid
(model/build.py, surrounds/data.py), views in views.json are aimed at the field centre (the fit's centre), and
ge_alt is Google Earth's own turf height read with ge_shoot.js --level."""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', '..'))
import ge_compare as G

FIT = [-5.4, 5.43, 0.0, -58.1, 84.07, 69.23]          # GroundModels.FIT["mars"]
G.GROUNDS['mars'] = {'lat': -37.539307, 'lon': 143.848166, 'ge_alt': float(os.environ.get('MARS_GE_ALT', 452.0)), 'fit': FIT}

if __name__ == '__main__':
    cmd, work = sys.argv[1], sys.argv[2]
    views = json.load(open(os.path.join(HERE, 'views.json')))
    for v in views:                                     # aim at the field centre: model (x, z) = FIT[0], FIT[1] -> east, north
        a = v.get('at', [0, 0, 0]); v['at'] = [a[0] + FIT[0], a[1] - FIT[1], a[2]]
    if cmd == 'plan':
        G.plan('mars', views, work)
    elif cmd == 'level':
        G.level('mars', work)
    else:
        G.sheet('mars', views, work, sys.argv[3], sys.argv[4] if len(sys.argv) > 4 else '')
