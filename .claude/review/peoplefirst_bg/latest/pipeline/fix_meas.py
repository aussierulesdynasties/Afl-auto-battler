p='meas_table.py'; s=open(p,encoding='utf-8').read()
s=s.replace("t = np.asarray(Image.open('out/peoplefirst/ortho/top.png').convert('RGB')).astype(float)",
"t0 = np.asarray(Image.open('out/peoplefirst/ortho/top.png').convert('RGB')).astype(float)\nGAIN = s.reshape(-1, 3).mean(0) / t0.reshape(-1, 3).mean(0)   # render lighting vs satellite: one global gain per channel\nt = np.clip(t0 * GAIN, 0, 255)")
s=s.replace("tm = (exg > 10) & (L < 95) & ~wm_(t)",
"RAD = {'ghost_gum': 4.6, 'red_gum': 7.0, 'paperbark': 4.2}; KN = spec['tree_kinds']\n_ti = Image.new('L', (1400, 1400)); _td = ImageDraw.Draw(_ti)\nfor x, y, k in json.load(open('data/peoplefirst/prep/trees.json')):\n    if abs(x) < 705 and abs(y) < 705: r = RAD[KN[int(k)]]; _td.ellipse([x + 700 - r, 700 - y - r, x + 700 + r, 700 - y + r], fill=1)\ntm = np.asarray(_ti, bool)   # model crowns rasterised from the placed trees")
s=s.replace("rows.append(('Overlay error","rows.append(('Render-to-satellite colour gain (R,G,B)', '', ', '.join('%.2f' % g for g in GAIN), 'applied to all model colours'))\nrows.append(('Overlay error")
s=s.replace("(m²)","(m2)")
open(p,'w',encoding='utf-8').write(s); print('patched', s.count('GAIN'), s.count('RAD'))
