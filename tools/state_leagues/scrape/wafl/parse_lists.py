# WAFL scrape helper: footyinfo club list pages -> fi.json.
# Kept as the record of how tools/state_leagues/staging/ was made; tools/state_leagues/build.py
# rebuilds data/state_leagues/ from staging/ without them.
import json,sys
sys.path.insert(0,'.')
from tables import tables
clubs=['claremont','east-fremantle','east-perth','peel','perth','south-fremantle','subiaco','swan-districts','west-perth','west-coast-wafl','west-coast','fremantle']
out={}
for c in clubs:
    t=tables(f'dl/list_{c}.html')[0]
    hdr=t[0]; rows=[]
    for r in t[1:]:
        name,slug=r[1].split('|')
        rows.append(dict(num=r[0],name=name,slug=slug.split('/')[-1],age=r[2],ht=r[3],wt=r[4],g_pre=r[6],g_szn=r[7],gl_szn=r[10],recruited=r[12]))
    st=tables(f'dl/stats_{c}.html')[0]
    stats=[]
    for r in st[1:]:
        name,slug=r[0].split('|')
        stats.append(dict(name=name,slug=slug.split('/')[-1],gm=r[1],gb=r[2],di=r[3],ki=r[4],hb=r[5],ma=r[6],ta=r[7],ho=r[8],cl=r[9],i50=r[10]))
    out[c]=dict(list=rows,stats=stats)
json.dump(out,open('fi.json','w'),indent=0)
afl=set(r['slug'] for c in ['west-coast','fremantle'] for r in out[c]['list'])
for c in clubs[:10]:
    L=out[c]['list']; S=out[c]['stats']; ls=set(r['slug'] for r in L)
    print(c,len(L),'withage',sum(r['age']!='-' for r in L),'afl-on-list',sum(r['slug'] in afl for r in L),'stats',len(S),'stats-not-on-list',[s['slug'] for s in S if s['slug'] not in ls][:12])
