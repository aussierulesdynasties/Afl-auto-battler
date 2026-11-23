import sys
p=sys.argv[1]; t=open(p,newline='').read()
a="""for s in (0, 125):                                    # street grid 125 m
    d.rectangle([0, s * m, N, s * m + 9 * m], fill=(118, 116, 112)); d.rectangle([s * m, 0, s * m + 9 * m, N], fill=(118, 116, 112))
"""
assert a in t; t=t.replace(a,"")
t=t.replace("cx, cy = x0 + 6 + i * 18.5 + rng.uniform(-2, 2), y0 + 8 + j * 28 + rng.uniform(-3, 3)","cx, cy = rng.uniform(0, 236), rng.uniform(0, 236)")
t=t.replace("F = Image.new('RGB', (N, N), (150, 156, 120))","F = Image.new('RGB', (N, N), (128, 138, 104))")
open(p,'w',newline='').write(t); print('ok')
