"""Texture session 2026-11-20 request on dc8e55dc: People First texture set (asphalt road + car park meshes with the
repeat break, lines) and no repeated glass: 12 extra curtain-wall variants (tint x bay x spandrel)."""
import json
def sub(path, pairs, add=''):
    s = open(path, newline='').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, a[:60]); s = s.replace(a, b)
    open(path, 'w', newline='').write(s + add)
TINTS = [('navy', (30, 40, 58)), ('slate', (62, 70, 80)), ('green', (60, 84, 76)), ('blue', (52, 78, 110)),
         ('smoke', (48, 50, 54)), ('silver', (118, 126, 134))]
LAY = [('a', 1.5, 3.6, 0.9, 0.08), ('b', 2.25, 3.8, 1.3, 0.12)]
add = '\n'.join("curtain('glass_%s_%s', %r, %s, %s, %s, %s)" % (t, l, c, bw, fh, sp, mu) for t, c in TINTS for l, bw, fh, sp, mu in LAY)
if 'glass_navy_a' not in open('mk_facades.py').read(): sub('mk_facades.py', [("json.dump(SIZES, open('tex/fc_sizes.json', 'w'), indent=1); print(SIZES)\n", add + "\njson.dump(SIZES, open('tex/fc_sizes.json', 'w'), indent=1); print(SIZES)\n")])
sub('facade_mix.py', [("GLASS = [(0.36, 'glass_dark'), (0.22, 'glass_teal'), (0.14, 'glass_bronze'), (0.28, 'glass_grey')]\n",
     "GLASS = [(1.0 / 16, f_) for f_ in ['glass_dark', 'glass_teal', 'glass_bronze', 'glass_grey'] + ['glass_' + t + '_' + l for t in " + repr([t for t, _ in TINTS]) + " for l in 'ab']]\n")])
sub('scene.py', [("# ---------- export background, then add the ground model for renders ----------\n",
     "exec(open(os.path.join(HERE, 'roads_pf.py'), encoding='utf-8').read())   # People First asphalt set (texture session)\n"
     "# ---------- export background, then add the ground model for renders ----------\n")])
J = json.load(open('spec/marvel.json')); J['road_mesh'] = True; json.dump(J, open('spec/marvel.json', 'w'), indent=1); print('ok')
