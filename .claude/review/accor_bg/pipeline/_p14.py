p='accor_landmarks.py'; s=open(p,newline='').read()
a="        _ob = mk_obj('bg_acc_lm_' + _k, _V, _F, _MATS[_k]); set_uv(_ob.data, [_U[i] for f_ in _F for i in f_])\n"
b=a+"""        if _k == 'roof':   # weld and smooth the arena roof (flat facets showed a radial crease); fascia stays sharp at 40 deg
            import bmesh; _bm = bmesh.new(); _bm.from_mesh(_ob.data); bmesh.ops.remove_doubles(_bm, verts=_bm.verts, dist=0.05)
            _bm.to_mesh(_ob.data); _bm.free(); _ob.data.shade_smooth_by_angle(angle=0.7)
"""
assert a in s and 'weld and smooth' not in s; s=s.replace(a,b); s=s.replace('rings = 8','rings = 16'); open(p,'w',newline='').write(s)
p='mk_accor_lm_tex.py'; s=open(p,newline='').read(); s=s.replace('a[y:y + 3] *= 0.85   # panel joints','a[y:y + 4] *= 0.7   # panel joints'); open(p,'w',newline='').write(s); print('ok')
