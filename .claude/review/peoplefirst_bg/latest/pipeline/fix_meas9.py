p='meas_table.py'; s=open(p,newline='',encoding='utf-8').read()
a="_drop = 1 + np.nonzero((np.asarray(_fr) < 0.5) & (_sz < 600))[0]"; assert a in s
s=s.replace(a,a+"\n_tp = np.zeros((1400, 1400), bool)\nfor _q in json.load(open('spec/peoplefirst_pre10c.json'))['paint_poly']:\n    if _q[0] == 'water': _tp |= pmask(_q[1])\n_drop = np.setdiff1d(_drop, np.unique(_lb[_tp & (_lb > 0)]))   # traced golf ponds were checked on their own board: never dropped",1)
open(p,'w',newline='',encoding='utf-8').write(s); print('ok')
