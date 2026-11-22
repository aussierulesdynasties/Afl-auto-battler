p='scene.py'; s=open(p,newline='').read()
old="""        for _ in range(12):   # split long fan triangles (UVs interpolate) so the cut follows the mask, not a face centre
            long_ = [e for e in bm.edges if (M @ e.verts[0].co - M @ e.verts[1].co).length > 3.0]"""
new="""        def _band(p):   # within ~4 m of the trim line: refine there so the cut edge follows the mask, not a 3 m sawtooth
            i, j = int((260 - p.y) / 0.5), int((p.x + 260) / 0.5)
            return 0 <= i < FN and 0 <= j < FN and FB[i, j]
        for _ in range(16):   # split long fan triangles (UVs interpolate) so the cut follows the mask, not a face centre
            long_ = []
            for e in bm.edges:
                a_, b_ = M @ e.verts[0].co, M @ e.verts[1].co; L_ = (a_ - b_).length
                if L_ > 3.0 or (L_ > 0.6 and _band((a_ + b_) / 2)): long_.append(e)"""
assert old in s; s=s.replace(old,new)
old2="    FM = np.load(FO); FN = FM.shape[0]\n"
new2="""    FM = np.load(FO); FN = FM.shape[0]
    _p = np.pad(FM, 8, mode='edge'); _dil = np.zeros_like(FM); _ero = np.ones_like(FM)
    for di in range(-8, 9, 2):
        for dj in range(-8, 9, 2):
            sh = _p[8 + di:8 + di + FN, 8 + dj:8 + dj + FN]; _dil |= sh; _ero &= sh
    FB = _dil & ~_ero
"""
assert old2 in s; s=s.replace(old2,new2); open(p,'w',newline='').write(s); print('ok')
