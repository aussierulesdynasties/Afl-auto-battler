p = 'scene.py'; s = open(p, newline='', encoding='utf-8').read()
old = "        rv, rf, rcl, ruv = RF[kind]; r0 = len(rv)\n"
new = ("        if src and not b.get('solar'):   # measured roof tone (satellite median, reference) tints the hand-made texture\n"
       "            kind = 'tile' if (src[0] > src[2] + 30 and src[0] > src[1] + 15) else 'shed' if cls == 'block' else 'metal'\n"
       "            rc = np.clip(lin(src) / np.maximum(lin(ROOF_TM[kind]), 0.02), 0, 0.85 / np.maximum(lin(ROOF_TM[kind]), 0.02))\n"
       "        rv, rf, rcl, ruv = RF[kind]; r0 = len(rv)\n")
assert s.count(old) == 1; s = s.replace(old, new)
old2 = "BL = json.load(open(os.path.join(D, 'buildings.json')))"
assert s.count(old2) == 1
s = s.replace(old2, old2 + "\nROOF_TM = json.load(open(os.path.join(D, 'roof_tex_mean.json'))) if os.path.exists(os.path.join(D, 'roof_tex_mean.json')) else {}")
open(p, 'w', newline='', encoding='utf-8').write(s); print('ok')
