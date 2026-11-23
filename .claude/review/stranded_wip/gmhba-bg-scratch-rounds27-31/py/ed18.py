p='py_mk_shed2.py'; s=open(p,newline='').read()
o1="M = 512; MH = 1536; u = (np.arange(M) + 0.5) / M * 4.0"
assert o1 in s; s=s.replace(o1,"M = 1536; MH = 1536; u = (np.arange(M) + 0.5) / M * 12.0")
o2="w = np.clip(w + R.normal(0, 3, (MH, M)), 0, 255)"
n2="""U2 = np.tile(u[None, :], (MH, 1))
def box(u0, u1, h0, h1): return (U2 >= u0) & (U2 < u1) & (H2 >= h0) & (H2 < h1)
rd = box(4.0, 8.0, 0.0, 4.5); w[rd] = 118 * np.where(np.mod(H2[rd], 0.1) < 0.02, 0.78, 1.0)     # roller door, horizontal slats
w[box(3.88, 4.0, 0, 4.6) | box(8.0, 8.12, 0, 4.6)] = 62; w[box(3.88, 8.12, 4.5, 4.85)] = 150; w[box(3.88, 8.12, 4.85, 4.9)] = 60   # guides + hood box
w[box(9.6, 10.5, 0.0, 2.1)] = 92; w[box(9.52, 9.6, 0, 2.18) | box(10.5, 10.58, 0, 2.18) | box(9.52, 10.58, 2.1, 2.18)] = 48   # personnel door + frame
for u0 in (0.25, 11.55):   # downpipes: lit round pipe with a cast shadow, brackets
    w[box(u0, u0 + 0.12, 0.15, 12.0)] = 200; w[box(u0 + 0.12, u0 + 0.18, 0.15, 12.0)] *= 0.5
    for hb in np.arange(1.0, 12.0, 2.0): w[box(u0 - 0.02, u0 + 0.14, hb, hb + 0.05)] = 120
w = np.clip(w + R.normal(0, 3, (MH, M)), 0, 255)"""
assert o2 in s; s=s.replace(o2,n2); open(p,'w',newline='').write(s)
p='scene.py'; s=open(p,newline='').read(); o="TW, TH = (4.0, 12.0) if shed"; assert o in s; s=s.replace(o,"TW, TH = (12.0, 12.0) if shed"); open(p,'w',newline='').write(s)
