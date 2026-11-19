exec(open('geo.py').read())
o={'g':[None if np.isnan(rr_at(GR,d/2)[1]) else float(rr_at(GR,d/2)[1]) for d in range(720)],'out':{str(k):[float(x) for x in v_[:4]]+[v_[4]] for k,v_ in OUT.items()},
   'stands':{k:[a0,a1,[float(rf(d)) if not np.isnan(rf(d)) else None for d in np.arange(a0,a1+0.01,0.5)],[float(ro(d)) if not np.isnan(ro(d)) else None for d in np.arange(a0,a1+0.01,0.5)]] for k,(a0,a1,rf,zf,ro,zo) in STANDS.items()}}
json.dump(o,open('sat/model.json','w'));print('ok')
