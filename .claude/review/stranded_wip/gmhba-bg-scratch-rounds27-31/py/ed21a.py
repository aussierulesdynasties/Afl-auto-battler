import sys
p = sys.argv[1]; s = open(p, encoding='utf-8', newline='').read()
def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]; s = s.replace(a, b)
rep("for ki, kn in enumerate(kinds):", "if spec.get('trees_v2'): exec(open(os.path.join(HERE, 'trees21.py'), encoding='utf-8').read()); kinds = []\nfor ki, kn in enumerate(kinds):")
rep("exec(open(os.path.join(HERE, 'landmarks.py'), encoding='utf-8').read())", "if spec.get('roof_snap'): exec(open(os.path.join(HERE, 'roofsnap21.py'), encoding='utf-8').read())\nexec(open(os.path.join(HERE, 'landmarks.py'), encoding='utf-8').read())")
rep("src = b.get('roof_c'); kind = 'tile' if", "src = b.get('roof_c'); kind = ('tile' if b['_tile'] else 'metal') if '_tile' in b else 'tile' if")
rep("eL, eW = hL / 2 + 0.45, hW / 2 + 0.45; rr = max(0.0, eL - eW)", "eL, eW = hL / 2 + 0.45, hW / 2 + 0.45; rr = max(0.0, eL - eW); gab = b.get('_gable', False)\n            if gab: rr = eL - 0.45")
rep("rf.append(tuple(r0 + t_ for t_ in fc)); rcl += [tuple(_rc3 * _sh) + tuple(np.array(rc)[3:])] * len(fc)",
    "rf.append(tuple(r0 + t_ for t_ in fc)); rcl += [tuple((np.array(wc)[:3] * 0.92) if (gab and len(fc) == 3) else (_rc3 * _sh)) + tuple(np.array(rc)[3:])] * len(fc)")
open(p, 'w', encoding='utf-8', newline='').write(s); print('ok')
