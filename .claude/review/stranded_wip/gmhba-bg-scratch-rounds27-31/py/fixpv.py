import sys
p=sys.argv[1]; t=open(p,newline='').read()
old="""        _mk = Image.new('L', (N, N), 0); ImageDraw.Draw(_mk).polygon(P(pts), fill=255)
        _ar = np.asarray(img).astype(np.int16); _m = np.asarray(_mk) > 0
        for _k in ('paved', 'parking'):
            _sel = _m & (np.abs(_ar - np.array(PAL[_k])).max(-1) < 6)
            _ar[_sel] = md.astype(np.int16)
        img = Image.fromarray(_ar.astype(np.uint8)); _np += 1
    print"""
new="""        Q_ = P(pts); u0, v0 = [max(0, int(min(c))) for c in zip(*Q_)]; u1, v1 = [min(N, int(max(c)) + 2) for c in zip(*Q_)]
        if u1 <= u0 or v1 <= v0: continue
        _mk = Image.new('L', (u1 - u0, v1 - v0), 0); ImageDraw.Draw(_mk).polygon([(u - u0, v - v0) for u, v in Q_], fill=255)
        _sub = _AR[v0:v1, u0:u1]; _m = np.asarray(_mk) > 0
        for _k in ('paved', 'parking'):
            _sel = _m & (np.abs(_sub - np.array(PAL[_k])).max(-1) < 6)
            _sub[_sel] = md.astype(np.int16)
        _np += 1
    img = Image.fromarray(np.clip(_AR, 0, 255).astype(np.uint8))
    print"""
assert old in t; t=t.replace(old,new)
t=t.replace("    _dr2 = ImageDraw.Draw(img); _np = 0\n","    _AR = np.asarray(img).astype(np.int16).copy(); _np = 0\n")
open(p,'w',newline='').write(t); print('ok')
