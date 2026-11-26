exec(open('meas.py').read())
J=json.load(open('osm/geo.json'))
for k in ['4000006','387975057','195513203','195513197','195513200','659304331','659304332','195513198','195513202','598232975','598232976','598232977','840868333']:
    P=polar(G[k]);ok=~np.isnan(P[:,0]);idx=np.where(ok)[0]
    if len(idx)==0:print(k,'none');continue
    # find contiguous ranges
    angs=idx/2.0
    rngs=[];s=angs[0];pv=angs[0]
    for a in angs[1:]:
        if a-pv>1:rngs.append((s,pv));s=a
        pv=a
    rngs.append((s,pv))
    print(k,J['tags'].get(k,{}).get('name',''),[(round(a-0 if a<=180 else a-360),round(b if b<=180 else b-360)) for a,b in rngs],'r %.0f-%.0f / %.0f-%.0f'%(np.nanmin(P[:,0]),np.nanmax(P[:,0]),np.nanmin(P[:,1]),np.nanmax(P[:,1])))
