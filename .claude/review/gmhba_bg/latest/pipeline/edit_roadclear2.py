p='prep.py'; s=open(p,encoding='utf-8',newline='').read()
a="""_RD = np.asarray(rdm); _n0 = len(TR)
TR = [q for q in TR if not (abs(q[0]) < NEAR and abs(q[1]) < NEAR and _RD[min(N - 1, int((NEAR - q[1]) / PX)), min(N - 1, int((q[0] + NEAR) / PX))])]
print('mapped trees on roads removed', _n0 - len(TR))
"""
assert a in s; s=s.replace(a,'')
s=s.replace("""            nx, ny = -(y2 - y1) / L, (x2 - x1) / L
""","""            nx, ny = -(y2 - y1) / L, (x2 - x1) / L
            try: _ow = int(str(t.get('lanes', 4 if t.get('highway') == 'secondary' else 2)).split(';')[0]) * 3.75 + 2
            except Exception: _ow = 9.5
""")
s=s.replace("qx, qy = px + sd * nx * 7.5, py + sd * ny * 7.5","qx, qy = px + sd * nx * _ow, py + sd * ny * _ow")
b="TR = [[x, y, int(rng.integers(0, len(spec['tree_kinds'])))]"
assert s.count(b)==1; s=s.replace(b,a+b)
open(p,'w',encoding='utf-8',newline='').write(s); print('ok')
