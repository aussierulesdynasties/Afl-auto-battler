p='meas_table.py'; s=open(p,newline='',encoding='utf-8').read()
i=s.index("_Wg = "); j=s.index("\n",i)
new=("_gL = _g.mean(2); _gsd = ndimage.median_filter(np.sqrt(np.clip(ndimage.uniform_filter(_gL**2, 7) - ndimage.uniform_filter(_gL, 7)**2, 0, None)), 5)\n"
"_Wg = (_gsd < 4.5) & (ndimage.median_filter(_gL, 5) < 130)   # water is flat in both aerials; canopy shadow is rough")
s=s[:i]+new+s[j:]; open(p,'w',newline='',encoding='utf-8').write(s); print('ok')
