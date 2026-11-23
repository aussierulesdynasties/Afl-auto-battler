import sys
p = sys.argv[1]; s = open(p, newline='').read()
for a, b in [("M = 512; u = (np.arange(M) + 0.5) / M * 4.0; h = (np.arange(M)[::-1] + 0.5) / M * 4.0", "M = 512; MH = 1536; u = (np.arange(M) + 0.5) / M * 4.0; h = (np.arange(MH)[::-1] + 0.5) / MH * 12.0"),
             ("w = np.tile(pr[None, :] * 170.0, (M, 1))", "w = np.tile(pr[None, :] * 170.0, (MH, 1))"),
             ("H2 = np.tile(h[:, None], (1, M))", "H2 = np.tile(h[:, None], (1, M))"),
             ("w = np.clip(w + R.normal(0, 3, (M, M)), 0, 255)", "w = np.clip(w + R.normal(0, 3, (MH, M)), 0, 255)"),
             ("512 px = 4 m wall", "512 x 1536 px = 4 m wide x 12 m high wall (one tile covers the whole wall height)")]:
    assert a in s, a; s = s.replace(a, b)
open(p, 'w', newline='').write(s)
p = sys.argv[2]; s = open(p, newline='').read()
for a, b in [("TW, TH = (4.0, 4.0) if shed else (tw, th)", "TW, TH = (4.0, 12.0) if shed else (tw, th)"),
             ("kind, RT = 'far', 6.0   # sheds", "kind, RT = 'far', 12.0   # sheds"),
             ("kind, RT = 'far', 6.0   # big", "kind, RT = 'far', 12.0   # big"),
             ("'clad_rib.png'), 0.55, 1 / 0.455)", "'clad_rib.png'), 0.55, 1 / float(open(os.path.join(HERE, 'tex', 'mt', 'clad_rib.mean')).read()))")]:
    assert a in s, a; s = s.replace(a, b)
open(p, 'w', newline='').write(s); print('ok')
