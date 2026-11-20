import sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
sys.argv = ['x', 'west']
exec(open('tools/roofit_h.py').read().split('def clean')[0].replace("ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))", "").replace("os.chdir(ROOT)", ""))
rf = {r['name']: r for r in SPEC['roofs']}
for nm in ('west', 'east'):
    P = way(rf[nm]['way']) + rf[nm].get('off', [0, 0])
    for k in CAMS:
        U = proj(CAMS[k][0], np.c_[P, np.full(len(P), 25.0)]); print(nm, k, U.min(0).round(), U.max(0).round())
