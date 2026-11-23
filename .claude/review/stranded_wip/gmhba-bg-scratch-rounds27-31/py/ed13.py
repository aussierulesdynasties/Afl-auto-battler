import sys
p = sys.argv[1]; s = open(p, newline='').read()
o = "            _sub[_sel] = md.astype(np.int16)\n"
assert o in s
s = s.replace(o, """            _sub[_sel] = md.astype(np.int16)
            if not _sel.any(): continue
            _jj, _ii = np.nonzero(_sel); _X = (u0 + _ii + 0.5) * PX - NEAR; _Y = NEAR - (v0 + _jj + 0.5) * PX   # MCG _lots structure, in world metres
            _Q = np.array(pts, float); _E = np.diff(_Q, axis=0); _e = _E[np.argmax(np.hypot(_E[:, 0], _E[:, 1]))]; _th = math.atan2(_e[1], _e[0])
            _vv = -_X * math.sin(_th) + _Y * math.cos(_th); _uu = _X * math.cos(_th) + _Y * math.sin(_th)
            if tg.get('amenity') == 'parking':
                _ph = np.mod(_vv, 16.0); _f = np.where(_ph < 6.0, 0.82, 1.08)            # 6 m aisle darker, then two 5 m bay rows
                _f = np.where(np.abs(_ph - 11.0) < 0.5, 1.45, _f)                        # pale line between the bay rows
                _f = np.where((_ph >= 6.0) & (np.mod(_uu, 2.6) < 0.5), _f * 1.12, _f)    # bay ends
            else:
                _kk = (np.floor(_uu / 6.0) * 7919 + np.floor(_vv / 6.0) * 104729).astype(np.int64); _f = 0.94 + 0.12 * ((_kk * 2654435761) % 1000) / 1000.0
                _f = np.where((np.mod(_uu, 6.0) < 0.5) | (np.mod(_vv, 6.0) < 0.5), _f * 0.86, _f)   # 6 m slabs
            _sub[_jj, _ii] = np.clip(_sub[_jj, _ii] * _f[:, None], 0, 255).astype(np.int16)
""")
open(p, 'w', newline='').write(s); print('ok')
