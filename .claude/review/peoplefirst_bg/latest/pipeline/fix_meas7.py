p='meas_table.py'; s=open(p,newline='',encoding='utf-8').read()
a="W1 = W1 & ndimage.binary_dilation(_Wg, iterations=3)"; assert a in s
s=s.replace(a,"_lb, _nb = ndimage.label(W1); _fr = ndimage.mean(_Wg, _lb, range(1, _nb + 1))\nW1 = np.isin(_lb, 1 + np.nonzero(np.asarray(_fr) >= 0.5)[0])   # keep a whole water patch when >=half of it is flat water in aerial 2",1)
open(p,'w',newline='',encoding='utf-8').write(s); print('ok')
