p='meas_table.py'; s=open(p,encoding='utf-8').read()
a=s[s.index('def ws_(a):'):s.index('\n',s.index('def ws_(a):'))]
b=("def ws_(a):\n"
   "    L = a.mean(2); sd = np.sqrt(np.clip(ndimage.uniform_filter(L**2, 7) - ndimage.uniform_filter(L, 7)**2, 0, None))\n"
   "    smooth = ndimage.median_filter(sd, 5) < 4; low_gb = ndimage.median_filter(a[..., 1] - a[..., 2], 5) < 6   # water is smooth or blue-dark; canopy is rough and green\n"
   "    return ndimage.binary_closing(ndimage.binary_opening((L < 60) & (a[..., 2] >= a[..., 0] - 4) & (smooth | low_gb), iterations=2), iterations=3)")
s=s.replace(a,b)
a2="W1, W2 = ws_(s), wm_(t0)\n"
b2=a2+("_bm = Image.new('L', (1400, 1400)); _d = ImageDraw.Draw(_bm)   # roofs and the stadium are not water in either image\n"
       "for _b in json.load(open('data/peoplefirst/prep/buildings.json')): _d.polygon(px(_b['p']), fill=1)\n"
       "_d.polygon(px(json.load(open('data/peoplefirst/prep/footprint.json'))), fill=1)\n"
       "_bm = ndimage.binary_dilation(np.asarray(_bm, bool), iterations=2); W1 &= ~_bm; W2 &= ~_bm\n")
assert s.count(a2)==1; s=s.replace(a2,b2); open(p,'w',encoding='utf-8').write(s); print('ok')
