p='meas_table.py'; s=open(p,newline='',encoding='utf-8').read()
a="W1, W2 = ws_(s), wm_(t0)"
assert a in s and 'sat2' not in s
add=a+("\n_g = np.asarray(Image.open('data/peoplefirst/sat2.png').convert('RGB')).astype(float)   # 2nd aerial (Google, other date): shadows move, water stays\n"
"_Wg = (ndimage.median_filter(_g.mean(2), 5) < 80) & (ndimage.median_filter(_g[..., 1] - _g[..., 2], 5) < 7) & (_g[..., 0] < 75)\n"
"W1 = W1 & ndimage.binary_dilation(_Wg, iterations=3)")
s=s.replace(a,add,1); open(p,'w',newline='',encoding='utf-8').write(s); print('ok')
