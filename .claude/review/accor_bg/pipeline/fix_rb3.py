b = open('roads_block.py', newline='').read()
h = b[b.index('    lat0, lon0 = spec'):b.index('    # one texture:')]
s = open('scene.py', newline='').read()
k = "    def _tint(rgb, fn): return"
assert k in s and '_xy(p)' not in s.split(k)[0][-3000:]
s = s.replace(k, h + k); open('scene.py', 'w', newline='').write(s); print('ok')
