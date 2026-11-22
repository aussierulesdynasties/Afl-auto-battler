"""Self-check after v2c orbit: Docklands still reads grey (concrete dominates untagged blocks, small windows);
station vent cowls read as white polka dots. Shift the mix to panels and tinted glass, darker/warmer concrete,
larger windows; drop the cowls."""
def sub(path, pairs):
    s = open(path, newline='').read()
    for a, b in pairs:
        assert s.count(a) == 1, (path, a[:60]); s = s.replace(a, b)
    open(path, 'w', newline='').write(s)
sub('facade_mix.py', [
 ("elif b['c'] == 'tower': f = _pick(r, [(0.62, None), (0.2, 'panel'), (0.18, 'concrete')]) or _pick(r2, GLASS)",
  "elif b['c'] == 'tower': f = _pick(r, [(0.66, None), (0.22, 'panel'), (0.12, 'concrete')]) or _pick(r2, GLASS)"),
 ("f = _pick(r, [(0.35, 'brick'), (0.35, 'concrete'), (0.3, 'panel')])",
  "f = _pick(r, [(0.4, 'panel'), (0.3, None), (0.15, 'brick'), (0.15, 'concrete')]) or _pick(r2, GLASS)"),
 ("f = _pick(r, [(0.35, 'concrete'), (0.25, 'brick'), (0.25, 'panel'), (0.15, 'glass_grey')])",
  "f = _pick(r, [(0.35, 'panel'), (0.25, None), (0.2, 'brick'), (0.2, 'concrete')]) or _pick(r2, GLASS)"),
 ("'concrete': [(196, 192, 184), (170, 168, 162), (214, 208, 196), (150, 150, 146), (186, 176, 160)],",
  "'concrete': [(176, 168, 150), (140, 138, 132), (196, 186, 166), (120, 118, 114), (168, 150, 128)],"),
 ("    for iu in range(int((u1 - u0) / HUMP_U) + 1):", "    for iu in range(0):"),
])
sub('mk_facades.py', [("punched('concrete', 3.0, 3.2, 1.8, 1.7, 0.8)", "punched('concrete', 3.0, 3.2, 2.3, 1.9, 0.7)")])
print('ok')
