"""Trace every club's clash photos (fitted to the home cut by warp_clash.py) into flat designs with trace.py:
cloth = the cut's own outline (mask/CODE_side.png), palette and sponsor boxes from clash_specs.json.

    python trace_clash.py [CODE ...]      (run in the work folder; writes design_CODE_side.png)

Spec per club: rows = the photos' armpit rows (front, back) for warp_clash.py; palette = trace.py's palette
("#src=#dst" draws a lit or shaded shade as its colour); front/back = boxes over the sponsors, the maker's
and the AFL's logos and the maker's tag (club marks stay); hole_front/hole_back = the photo's lining seen
through the neck or under the hem; edge = the photo's bindings taken off by edge_clean.py: a width (px), or {width,
front/back: the binding's colours, above_front/back: a row in place of the armpit}.
Without holes, nothing light is taken for lining (a white guernsey's cloth would be). A club whose clash is
its home guernsey re-coloured (from_home) is not traced: build_atlas.py makes it from the home cell.
Each club's own fixes (fixes/<code>_*.py) run after its trace."""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
SPEC = json.load(open(os.path.join(HERE, 'clash_specs.json')))
NOHOLE = '0,0;1,0;1,1'


def run(job):
    code, side = job
    s = SPEC[code]
    env = dict(os.environ, CLOTH=f'mask/{code}_{side}.png')
    cmd = [sys.executable, os.path.join(HERE, '..', 'trace.py'), code, side, s['palette'], s[side],
           f'design_{code}_{side}.png', s.get('hole_' + side, NOHOLE)]
    r = subprocess.run(cmd, env=env, capture_output=True, text=True)
    out = (r.stdout + r.stderr).strip().splitlines()[-1:]
    e = s.get('edge')
    e = e if isinstance(e, dict) or e is None else {'width': e, side: []}
    if e and side in e:     # the photo's bindings off; the shader draws them on the cut's edges
        cmd = [sys.executable, os.path.join(HERE, 'edge_clean.py'), code, side, str(e['width'])] + e.get(side, [])
        if 'above_' + side in e:
            cmd += ['--above', str(e['above_' + side])]
        r = subprocess.run(cmd, capture_output=True, text=True)
        out += (r.stdout + r.stderr).strip().splitlines()[-1:]
    return code, side, out


if __name__ == '__main__':
    codes = [c for c in (sys.argv[1:] or sorted(SPEC)) if 'from_home' not in SPEC[c]]
    with ThreadPoolExecutor(2) as ex:  # each trace holds a few GB at 4x
        for code, side, out in ex.map(run, [(c, s) for c in codes for s in ('front', 'back')]):
            print(code, side, *out)
    # then each club's own fixes (fixes/<code>_*.py), for what a trace can't see (a band under a sponsor box)
    for code in codes:
        for f in sorted(os.listdir(os.path.join(HERE, 'fixes'))):
            if f.startswith(code.lower() + '_') and f.endswith('.py'):
                r = subprocess.run([sys.executable, os.path.join(HERE, 'fixes', f)], capture_output=True, text=True)
                print(code, f, *(r.stdout + r.stderr).strip().splitlines()[-1:])
