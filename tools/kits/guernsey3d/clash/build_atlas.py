"""Put every traced clash design (trace_clash.py) into the clash atlas, in the club's own cell of
data/kits_today.csv (the clash atlas has kits_today.png's layout, 4 cells a row, front square + back square).

    python build_atlas.py OUT_ATLAS [CODE ...]      (run in the work folder)

A club whose cut carries a flat pattern (North, St Kilda: uv/unwrap_CODE.json from dump_uv.gd) has its two
pictures put in a scratch atlas first and baked onto the pattern (bake_unwrap.py), as its home guernsey was."""
import csv, json, os, shutil, subprocess, sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
UP = os.path.join(HERE, '..')
ROOT = os.path.join(UP, '..', '..', '..')
SPEC = json.load(open(os.path.join(HERE, 'clash_specs.json')))
CELLS = {r['code']: int(r['cell']) for r in csv.DictReader(open(os.path.join(ROOT, 'data', 'kits_today.csv')))}
out = sys.argv[1]
codes = sys.argv[2:] or sorted(SPEC)
if not os.path.exists(out):
    Image.new('RGB', (8192, 5120), (0, 0, 0)).save(out)
env = dict(os.environ, COLFILL='1')
HOME = os.path.join(ROOT, 'assets', 'oval3d', 'kits_today.png')


def from_home(code, cell, spec):
    """the home cell as it is, with the back square's yoke (rows above spec's back_white_above) made white"""
    home = np.array(Image.open(HOME).convert('RGB'))
    at = np.array(Image.open(out).convert('RGB'))
    x0, y0 = (cell % 4) * 2048, (cell // 4) * 1024
    c = home[y0:y0 + 1024, x0:x0 + 2048].copy()
    back = c[:spec['back_white_above'], 1024:]
    white = c[spec['back_white_above']:, 1024:].reshape(-1, 3)
    white = white[white.astype(int).sum(-1) > 600].mean(0).round().astype(np.uint8)
    back[:] = white
    at[y0:y0 + 1024, x0:x0 + 2048] = c
    Image.fromarray(at).save(out)


for code in codes:
    cell = CELLS[code]
    if 'from_home' in SPEC[code]:
        from_home(code, cell, SPEC[code]['from_home'])
        continue
    if os.path.exists(f'uv/unwrap_{code}.json'):
        shutil.copy(f'uv/unwrap_{code}.json', f'unwrap_{code}.json')
        planar = f'planar_{code}.png'
        Image.new('RGB', (8192, 5120), (0, 0, 0)).save(planar)
        subprocess.run([sys.executable, os.path.join(UP, 'fillcell.py'), code, str(cell), planar], env=env, check=True)
        subprocess.run([sys.executable, os.path.join(UP, 'bake_unwrap.py'), code, str(cell), planar, out], check=True)
    else:
        subprocess.run([sys.executable, os.path.join(UP, 'fillcell.py'), code, str(cell), out], env=env, check=True)
print('clash atlas', out, 'cells', {c: CELLS[c] for c in codes})
