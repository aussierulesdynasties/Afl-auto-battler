p='mk_pave_mask.py'; s=open(p,newline='').read()
a="dflt=(np.abs(g-S['ground_default']).max(2)<=34)&(np.abs(g-S['ballast']).max(2)>12)"
b=("ry=Image.new('L',(n,n),0); rd=ImageDraw.Draw(ry)   # v3: never pave the railway land\n"
   "for e in js:\n"
   "    if e['type']=='way' and e.get('tags',{}).get('landuse')=='railway' and e.get('geometry'):\n"
   "        q=[(((g_['lon']-lon0)*KX+NE)/px,(NE-(g_['lat']-lat0)*KY)/px) for g_ in e['geometry'] if g_]\n"
   "        if len(q)>2: rd.polygon(q,fill=255)\n"
   "dflt=(np.abs(g-S['ground_default']).max(2)<=34)&(np.asarray(ry)==0)")
assert s.count(a)==1; open(p,'w',newline='').write(s.replace(a,b)); print('ok')
