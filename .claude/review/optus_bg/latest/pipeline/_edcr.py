p='prep.py';s=open(p,newline='').read()
a=s.index("    for _yy in np.arange(-40, 126, 5.0):"); b=s.index("    print('plaza bed trees'")
new='''    # one tree per z19 crown: crown centres = local maxima of the canopy's distance transform (>= 1.2 m radius, 3 m apart)
    _dt = ndimage.distance_transform_edt(_cv) * 0.125
    _pk = (_dt == ndimage.maximum_filter(_dt, size=25)) & (_dt >= 1.2)
    _pl, _pn = ndimage.label(_pk); _cc = ndimage.center_of_mass(_pk, _pl, range(1, _pn + 1)) if _pn else []
    _CR = []
    for _r0, _c0 in _cc:
        _x, _y = 80 + _c0 * 0.125, 135 - _r0 * 0.125
        if _y < -40 or not _op.contains_point((_x, _y)) or any(q.contains_point((_x, _y)) for q in _pps): continue
        TR.append([round(_x, 1), round(_y, 1)]); _CR.append([round(_x, 1), round(_y, 1), round(float(_dt[int(_r0), int(_c0)]), 1)])
    json.dump(_CR, open(os.path.join(OUT, 'plaza_crowns.json'), 'w'))
'''
s=s[:a]+new+s[b:]; open(p,'w',newline='').write(s)
