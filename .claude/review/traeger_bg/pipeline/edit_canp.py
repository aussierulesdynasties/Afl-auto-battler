p='prep.py'; s=open(p,newline='').read()
old="mask = Image.new('L', (N, N), 0 if not _td else max(1, min(255, int(40000 / _td)))); md = ImageDraw.Draw(mask)"
new="""_CN = os.path.join(OUT, 'canopy.npy'); CAN = np.load(_CN) if os.path.exists(_CN) else None   # trees traced from the satellite
if CAN is not None: _td = _td or 40000   # canopy mode: every untagged spot may hold a tree; the trace decides
mask = Image.new('L', (N, N), 0 if not _td else max(1, min(255, int(40000 / _td)))); md = ImageDraw.Draw(mask)"""
assert old in s; s=s.replace(old,new)
old2="keep = (rng.random(GX.shape) < np.clip(prob, 0, 1)) & (np.hypot(GX, GY) > skip_r) & (np.hypot(GX, GY) < spec['tree_r_m'])"
new2=old2+"""
if CAN is not None:   # inside the satellite's extent a tree stands where the trace shows crown in this 6 m cell
    _sj = json.load(open(os.path.join(HERE, 'data', spec['name'], 'sat.json'))); _h, _m = _sj['half_m'], _sj['m_per_px']
    _ci = ((_h - GY) / _m).astype(int); _cj = ((GX + _h) / _m).astype(int); _in = (np.abs(GX) < _h - 3) & (np.abs(GY) < _h - 3)
    _cs = np.cumsum(np.cumsum(np.pad(CAN.astype(np.float32), ((1, 0), (1, 0))), 0), 1); _r = int(3 / _m)
    _i0 = np.clip(_ci - _r, 0, CAN.shape[0]); _i1 = np.clip(_ci + _r, 0, CAN.shape[0]); _j0 = np.clip(_cj - _r, 0, CAN.shape[1]); _j1 = np.clip(_cj + _r, 0, CAN.shape[1])
    _frac = (_cs[_i1, _j1] - _cs[_i0, _j1] - _cs[_i1, _j0] + _cs[_i0, _j0]) / np.maximum(1, (_i1 - _i0) * (_j1 - _j0))
    keep = np.where(_in, (_frac > 0.2) & (v > 0) & (np.hypot(GX, GY) > skip_r), keep)
    print('canopy trees', int((_in & keep).sum()))"""
assert old2 in s; s=s.replace(old2,new2); open(p,'w',newline='').write(s); print('ok')
