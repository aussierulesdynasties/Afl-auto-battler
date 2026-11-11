# WAFL scrape helper: footyinfo team-stats pages (dl/wb/ts_*.html) -> ts.json.
# Kept as the record of how tools/state_leagues/staging/ was made; tools/state_leagues/build.py
# rebuilds data/state_leagues/ from staging/ without them.
import sys,json,glob; sys.path.insert(0,'.')
from nuxt import load
from collections import Counter,defaultdict
recs=[]
for f in sorted(glob.glob('dl/wb/ts_*.html')):
    try: d=load(f)['data']
    except Exception as e: print(f,'ERR',e); continue
    s=[v for v in d.values() if isinstance(v,dict) and 'competitions' in v]
    if not s: print(f,'no comps'); continue
    s=s[0]
    for c in s['competitions']:
        if c['name']!='League': continue
        rnd=c['round']['name'] if c.get('round') else None
        for m in c.get('matches') or []:
            for side in ('home','away'):
                t=m[side]
                for p in t.get('selections') or []:
                    recs.append(dict(snap=f.split('ts_')[1][:-5],season=s['season']['name'],round=rnd,match=m['slug'],club=t['name'],id=p['id'],first=p['first'],last=p['last'],num=p['number'],pos=p['position'],selected=p['selected'],squad=p['squad']))
        print(f,s['season']['name'],rnd,len(c.get('matches') or []))
json.dump(recs,open('ts.json','w'))
print(len(recs), Counter(r['pos'] for r in recs).most_common(30))
