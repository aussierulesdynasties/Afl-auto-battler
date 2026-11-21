p='prep.py'; s=open(p,encoding='utf-8',newline='').read()
old="        md.line(P(pts), fill=0, width=max(1, int(14 / PX)))"
new="""        _hw = t.get('highway'); _dl = {'motorway': 4, 'trunk': 4, 'primary': 4, 'secondary': 4}.get(_hw, 2)
        try: _ln = int(str(t.get('lanes', _dl)).split(';')[0])
        except Exception: _ln = _dl
        _w = 14 if t.get('railway') else _ln * 7.5   # director 2026-11-20: clear the full road width (4 lanes ~ 30 m)
        md.line(P(pts), fill=0, width=max(1, int(_w / PX))); rd.line(P(pts), fill=255, width=max(1, int(_w / PX)))"""
assert old in s; s=s.replace(old,new)
old2="# keep trees off roads, rails, buildings and water\n"
assert old2 in s; s=s.replace(old2,old2+"rdm = Image.new('L', (N, N), 0); rd = ImageDraw.Draw(rdm)\n")
old3="mv = np.asarray(mask).astype(np.float32)"
new3="""_RD = np.asarray(rdm); _n0 = len(TR)
TR = [q for q in TR if not (abs(q[0]) < NEAR and abs(q[1]) < NEAR and _RD[min(N - 1, int((NEAR - q[1]) / PX)), min(N - 1, int((q[0] + NEAR) / PX))])]
print('mapped trees on roads removed', _n0 - len(TR))
""" + old3
assert s.count(old3)==1; s=s.replace(old3,new3)
open(p,'w',encoding='utf-8',newline='').write(s); print('ok')
