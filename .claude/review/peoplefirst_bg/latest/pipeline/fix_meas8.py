p='meas_table.py'; s=open(p,newline='',encoding='utf-8').read()
a="W1 = np.isin(_lb, 1 + np.nonzero(np.asarray(_fr) >= 0.5)[0])"; assert a in s
s=s.replace(a,"_sz = ndimage.sum(W1, _lb, range(1, _nb + 1)); _drop = 1 + np.nonzero((np.asarray(_fr) < 0.5) & (_sz < 600))[0]\nW1 = W1 & ~np.isin(_lb, _drop)   # drop small patches that are rough in aerial 2 (tree shadow); board: water_shadow.png",1)
open(p,'w',newline='',encoding='utf-8').write(s); print('ok')
