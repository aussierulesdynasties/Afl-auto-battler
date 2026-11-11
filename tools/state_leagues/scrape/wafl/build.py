# WAFL scrape (stage A). Reads footyinfo.com lists and stats (fi.json from parse_lists.py, ts.json from parse_ts.py) and the wafl.com.au player pages cached under dl/, and writes wafl_players_2026.csv, wafl_afl_listed_appearances_2026.csv and wafl_clubs_2026.csv (copied into ../staging/). The downloads are not in the repo.
# Kept as the record of how tools/state_leagues/staging/ was made; tools/state_leagues/build.py
# rebuilds data/state_leagues/ from staging/ without them.
import json,csv,os,re,sys,unicodedata,html
sys.path.insert(0,'.')
from tables import tables
from nuxt import load
from collections import Counter,defaultdict
REPO='C:/Users/DANTE/Documents/GitHub/Afl-auto-battler/.claude/worktrees/interview-every-mode-931d7d/data/'
OUT='C:/kt/state_leagues/'
os.makedirs(OUT,exist_ok=True)
fi=json.load(open('fi.json'))
FETCH='--fetch' in sys.argv
CL={'claremont':('CLA','Claremont'),'east-fremantle':('EFR','East Fremantle'),'east-perth':('EPR','East Perth'),'peel':('PEL','Peel Thunder'),
    'perth':('PER','Perth'),'south-fremantle':('SFR','South Fremantle'),'subiaco':('SUB','Subiaco'),'swan-districts':('SWA','Swan Districts'),
    'west-perth':('WPR','West Perth'),'west-coast-wafl':('WCR','West Coast')}
def slug(n):
    n=unicodedata.normalize('NFKD',n).encode('ascii','ignore').decode().lower().replace("'",'')
    return re.sub(r'[^a-z0-9]+','-',n).strip('-')
def norm(n): return slug(n).replace('-','')
# AFL lists
afl={}
for r in csv.DictReader(open(REPO+'players_2026.csv',encoding='utf8')):
    afl.setdefault(norm(r['first']+' '+r['last']),[]).append(r)
ENR={(r['club'],r['num'],r['last']):r for r in csv.DictReader(open(REPO+'players_enriched_2026.csv',encoding='utf8'))}
fi_afl={}
for c,code in (('west-coast','WCE'),('fremantle','FRE')):
    for r in fi[c]['list']: fi_afl[r['slug']]=code
# wafl profile parse
import urllib.request,urllib.error,time
FAIL=set(l.split()[0] for f in ['dl/wp2/_fail.txt'] if os.path.exists(f) for l in open(f) if l.strip())
def wprof(s):
    p=f'dl/wp2/{s}.html'
    if not os.path.exists(p):
        if s in FAIL or not FETCH: return None
        try:
            r=urllib.request.urlopen(urllib.request.Request('https://wafl.com.au/player/'+s,headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130'}),timeout=30)
            open(p,'wb').write(r.read()); time.sleep(0.4)
        except Exception as e:
            FAIL.add(s); open('dl/wp2/_fail.txt','a').write(f'{s} {getattr(e,"code","ERR")}'+chr(10)); return None
    try: d=load(p)['data']
    except Exception: return None
    prof=next((v for v in d.values() if isinstance(v,dict) and 'height' in v and 'first' in v),None)
    seasons=[]
    for t in tables(p):
        if t and t[0][:4]==['Season','Competition','Club','Matches']:
            seasons=[r for r in t[1:]]
    return dict(prof=prof,seasons=seasons,url=f'https://wafl.com.au/player/{s}')
def fborn(s):
    p=f'dl/fp2/{s}.html'
    if not os.path.exists(p): return None,None
    t=open(p,encoding='utf8',errors='replace').read()
    t=html.unescape(re.sub(r'<[^>]+>',' ',t)); t=re.sub(r'\s+',' ',t)
    m=re.search(r'Born (\d{1,2}) ([A-Za-z]{3})[a-z]* (\d{4})',t); h=re.search(r'Height (\d{3}) cm',t)
    dob=None
    if m:
        mon='Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec'.split().index(m.group(2))+1
        dob=f'{m.group(3)}-{mon:02d}-{int(m.group(1)):02d}'
    return dob,(h.group(1) if h else None)
def find_wafl(name,clubname,num):
    base=slug(name)
    for s in [base]+[f'{base}-{i}' for i in range(1,6)]:
        w=wprof(s)
        if not w or not w['prof']: continue
        clubs26={r[2] for r in w['seasons'] if r[0]=='2026'}
        if clubname in clubs26: return w,'club2026'
        if not clubs26 and str(w['prof'].get('number'))==str(num): return w,'number'
    return None,None
def sumcomp(w,comp,clubname=None):
    rows=[r for r in w['seasons'] if r[0]=='2026' and r[1]==comp and (clubname is None or r[2]==clubname)]
    if not rows: return None
    tot=[0]*11
    for r in rows:
        for i,v in enumerate(r[3:4]+r[4:7]+r[8:]):
            try: tot[i]+=int(v)
            except: pass
    return dict(zip(['gm','ki','hb','di','mk','tk','ho','ff','fa','gl','bh'],tot))
POSMAP={'full-back':'DEF','left-full-back':'DEF','right-full-back':'DEF','half-back':'DEF','left-half-back':'DEF','right-half-back':'DEF',
 'centre':'MID','left-centre':'MID','right-centre':'MID','follower-1':'RUC','follower-2':'MID','follower-3':'MID',
 'half-forward':'FWD','left-half-forward':'FWD','right-half-forward':'FWD','full-forward':'FWD','left-full-forward':'FWD','right-full-forward':'FWD'}
ts=json.load(open('ts.json'))
sel={}
for r in ts:
    if r['selected'] and r['snap']=='live_GF':
        sel[(r['club'],norm(r['first']+' '+r['last']))]=r['pos']
def statsfor(c,s):
    for x in fi[c]['stats']:
        if x['slug']==s: return x
    return None
HDR=['club','first','last','num','dob','age','height_cm','weight_kg','pos','pos_detail',
 'lg_gm','lg_gl','lg_bh','lg_di','lg_ki','lg_hb','lg_mk','lg_tk','lg_ho','lg_cl','lg_i50','lg_ff','lg_fa',
 'res_gm','res_gl','res_di','res_ki','res_hb','res_mk','res_tk','res_ho',
 'colts_gm','colts_gl','colts_di','colts_ki','colts_hb','colts_mk','colts_tk','colts_ho',
 'lg_career_gm_before_2026','afl_listed','afl_club','afl_link','note','src_list','src_stats','src_profile','src_dob']
def split_name(full,w):
    if w and w['prof'] and w['prof'].get('first') and w['prof'].get('last'):
        f,l=w['prof']['first'].strip(),w['prof']['last'].strip()
        if norm(f+' '+l)==norm(full): return f,l
    parts=full.split(' ',1); return parts[0],parts[1] if len(parts)>1 else ''
def mkrow(c,code,clubname,r,st,listed):
    w,how=find_wafl(r['name'],clubname,r['num'])
    first,last=split_name(r['name'],w)
    dob,fh=(None,None)
    if r.get('age','-')!='-' : dob,fh=fborn(r['slug'])
    prof=w['prof'] if w else {}
    ht=r['ht'].replace('cm','') if r.get('ht','-')!='-' else (fh or (str(prof.get('height')) if prof.get('height') else ''))
    wt=r['wt'].replace('kg','') if r.get('wt','-') not in ('-',None) else (str(prof.get('weight')) if prof.get('weight') else '')
    age=str(prof.get('age')) if prof.get('age') else ''
    lg=sumcomp(w,'League',clubname) if w else None
    res=sumcomp(w,'Reserves',clubname) if w else None
    co=sumcomp(w,'Colts',clubname) if w else None
    p=sel.get((clubname,norm(r['name'])))
    row=dict(club=code,first=first,last=last,num=(r.get('num') if r.get('num')!='-' else '') or (str(prof.get('number')) if prof.get('number') else ''),dob=dob or '',age=age,height_cm=ht,weight_kg=wt,
        pos=POSMAP.get(p,'') if p else '',pos_detail=(p+' (2026 Grand Final team sheet)') if p else '')
    if st:
        g,b=st['gb'].split('.')
        row.update(lg_gm=st['gm'],lg_gl=g,lg_bh=b,lg_di=st['di'],lg_ki=st['ki'],lg_hb=st['hb'],lg_mk=st['ma'],lg_tk=st['ta'],lg_ho=st['ho'],lg_cl=st['cl'],lg_i50=st['i50'])
        if lg: row.update(lg_ff=lg['ff'],lg_fa=lg['fa'])
    elif listed and r.get('g_szn')=='0':
        row.update(lg_gm='0',lg_gl='0')
    elif listed and r.get('g_szn') not in (None,'-'):
        row['note']=f"footyinfo shows {r['g_szn']} league games in 2026, none for this club"
        row['lg_gm']='0'
    if res: row.update(res_gm=res['gm'],res_gl=res['gl'],res_di=res['di'],res_ki=res['ki'],res_hb=res['hb'],res_mk=res['mk'],res_tk=res['tk'],res_ho=res['ho'])
    if co: row.update(colts_gm=co['gm'],colts_gl=co['gl'],colts_di=co['di'],colts_ki=co['ki'],colts_hb=co['hb'],colts_mk=co['mk'],colts_tk=co['tk'],colts_ho=co['ho'])
    if w and not (res) : row.setdefault('res_gm','0')
    if w and not (co) : row.setdefault('colts_gm','0')
    if listed and r.get('g_pre') not in (None,'-'): row['lg_career_gm_before_2026']=r['g_pre']
    sl=fi_afl.get(r.get('slug') or st['slug'])
    m=afl.get(norm(r['name']),[])
    if code=='PEL': m=[x for x in m if x['club']=='FRE'] or ([] if not sl else m)
    if code=='WCR': m=[x for x in m if x['club']=='WCE'] or ([] if not sl else m)
    if sl or (m and code in('PEL','WCR')):
        row['afl_listed']='Y'; row['afl_club']=sl or m[0]['club']
        if m: row['afl_link']=f"players_2026.csv:{m[0]['club']}#{m[0]['num']} {m[0]['first']} {m[0]['last']}"
    else:
        row['afl_listed']='N'
        if m: row['note']='name also in players_2026.csv ('+', '.join(x['club'] for x in m)+'); not linked: different club'
    if row['afl_listed']=='Y' and m:
        e=ENR.get((m[0]['club'],m[0]['num'],m[0]['last']))
        if e:
            if not row['dob'] and e.get('dob'): row['dob']=e['dob']; row['src_dob']='data/players_enriched_2026.csv'
            if not row['height_cm'] and e.get('height_cm'): row['height_cm']=e['height_cm']
            if not row['weight_kg'] and e.get('weight_kg'): row['weight_kg']=e['weight_kg']
    row['src_list']=f'https://www.footyinfo.com/team/{c}/2026' if listed else ''
    row['src_stats']=f'https://www.footyinfo.com/team/{c}/stats/2026' if st else ''
    row['src_profile']=w['url'] if w else ''
    row.setdefault('src_dob',f"https://www.footyinfo.com/player/{r['slug']}" if dob else '')
    return row
players=[];aflrows=[]
for c,(code,clubname) in CL.items():
    L=fi[c]['list']; ls={x['slug'] for x in L}
    seen={(norm(x['name'])) for x in L if x['num']!='-'}
    for r in L:
        if r['num']=='-' and norm(r['name']) in seen: continue
        players.append(mkrow(c,code,clubname,r,statsfor(c,r['slug']),True))
    for st in fi[c]['stats']:
        if st['slug'] in ls: continue
        r=dict(name=st['name'],slug=st['slug'],num='',age='-',ht='-',wt='-')
        aflrows.append(mkrow(c,code,clubname,r,st,False))
from collections import defaultdict as DD
byp=DD(list)
for x in players:
    if x['src_profile']: byp[x['src_profile']].append(x)
for k,v in byp.items():
    cl={x['club'] for x in v}
    if len(cl)>1:
        for x in v: x['note']=((x.get('note','')+'; ') if x.get('note') else '')+'same player also listed by footyinfo at '+'/'.join(sorted(cl-{x['club']}))
for x in players:
    if x['first']=='Osacr': x['note']=((x.get('note','')+'; ') if x.get('note') else '')+'first name as spelled by source (footyinfo); likely Oscar, unverified'
for rows,fn in ((players,'wafl_players_2026.csv'),(aflrows,'wafl_afl_listed_appearances_2026.csv')):
    with open(OUT+fn,'w',newline='',encoding='utf8') as f:
        wr=csv.DictWriter(f,HDR); wr.writeheader(); [wr.writerow({k:x.get(k,'') for k in HDR}) for x in rows]
print(len(players),len(aflrows))
fill={k:sum(1 for x in players if str(x.get(k,'')).strip()!='') for k in HDR}
print({k:f'{100*v/len(players):.0f}%' for k,v in fill.items()})
print(Counter(x['club'] for x in players)); print(Counter(x['afl_listed'] for x in aflrows), [ (x['first'],x['last']) for x in aflrows if x['afl_listed']!='Y'])
