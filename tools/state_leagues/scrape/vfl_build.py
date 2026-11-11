# VFL scrape (stage A). Reads the downloaded VFL pages under raw/ (Zero Hanger's 2026 list article, vfl.aflmstats.com team stats, Coburg's player page) and writes vfl_players_2026.csv, vfl_afl_links_2026.csv and vfl_clubs_2026.csv, which are copied into ../staging/. Paths are the original scrape folder (C:/kt/state_leagues); the downloads are not in the repo.
# Kept as the record of how tools/state_leagues/staging/ was made; tools/state_leagues/build.py
# rebuilds data/state_leagues/ from staging/ without them.
import csv, re, os, datetime, glob
R = 'C:/kt/state_leagues/raw/'
OUT = 'C:/kt/state_leagues/'
REPO = 'C:/Users/DANTE/Documents/GitHub/Afl-auto-battler/data/'
ZH = 'https://www.zerohanger.com/every-vfl-playing-list-for-the-2026-season-174359'
COBURL = 'https://coburgfc.com.au/football/mens-football/players/'
GROUNDS_URL = 'https://wikimili.com/en/2026_VFL_season'
ST = 'https://vfl.aflmstats.com/team/%s/players/2026'
# id, name, short, zh name, afl code, kind, stats code, home ground (2026 VFL season article, first listed)
CLUBS = [
 ('BOX','Box Hill Hawks','Box Hill','Box Hill','HAW','aligned','haw','Box Hill City Oval'),
 ('BRLR','Brisbane Lions VFL','Brisbane','Brisbane','BRL','reserves','brl','Brighton Homes Arena'),
 ('CARR','Carlton VFL','Carlton','Carlton','CAR','reserves','car','Ikon Park'),
 ('CAS','Casey Demons','Casey','Casey','MEL','aligned','csy','Casey Fields'),
 ('COB','Coburg','Coburg','Coburg','','standalone','cob','Barry Plant Park'),
 ('COLR','Collingwood VFL','Collingwood','Collingwood','COL','reserves','col','Victoria Park'),
 ('ESSR','Essendon VFL','Essendon','Essendon','ESS','reserves','ess','NEC Hangar'),
 ('FOO','Footscray','Footscray','Footscray','WBD','reserves','wbd','Mission Whitten Oval'),
 ('FRA','Frankston','Frankston','Frankston','','standalone','frn','Kinetic Stadium'),
 ('GEER','Geelong VFL','Geelong','Geelong','GEE','reserves','gee','GMHBA Stadium'),
 ('GCSR','Gold Coast Suns VFL','Gold Coast','Gold Coast','GCS','reserves','gcs','People First Stadium'),
 ('GWSR','GWS Giants VFL','GWS','GWS','GWS','reserves','gws','Tom Wills Oval'),
 ('NTHR','North Melbourne VFL','North Melbourne','North Melbourne','NTH','reserves','kan','Arden Street Oval'),
 ('PTM','Port Melbourne','Port Melbourne','Port Melbourne','','standalone','pmb','ETU Stadium'),
 ('RICR','Richmond VFL','Richmond','Richmond','RIC','reserves','ric','Holm Park'),
 ('SAN','Sandringham','Sandringham','Sandringham','','standalone','san','Trevor Barker Beach Oval'),
 ('SOU','Southport','Southport','Southport','','standalone','sth','Fankhauser Reserve'),
 ('STKR','St Kilda VFL','St Kilda','St Kilda','STK','reserves','stk','RSEA Park'),
 ('SYDR','Sydney Swans VFL','Sydney','Sydney','SYD','reserves','syd','Tramway Oval'),
 ('TASD','Tasmania Devils','Tasmania','Tasmania','','standalone','tas','Ninja Stadium'),
 ('WER','Werribee','Werribee','Werribee','','standalone','wer','Avalon Airport Oval'),
 ('WIL','Williamstown','Williamstown','Williamstown','','standalone','wil','DSV Stadium'),
]
FIRST = {'stu':'stuart','seb':'sebastian','tom':'thomas','solly':'solomon','will':'william','matt':'matthew',
 'mathew':'matthew','kal':'kallan','damien':'damon','finbar':'finn','cam':'cameron','tony':'toby','jet':'jett',
 'lachie':'lachlan','lochlan':'lachlan','ben':'benjamin','mitch':'mitchell','caidan':'caiden','dom':'dominic',
 'nick':'nicholas','josh':'joshua','dan':'daniel','sam':'samuel','max':'maxwell','jake':'jacob','alex':'alexander',
 'harry':'harrison','joe':'joseph','charlie':'charles','fred':'frederick','zac':'zachary','zach':'zachary',
 'ned':'edward','jack':'jack','alixzander':'alix','ollie':'oliver','olly':'oliver','jed':'jedd','jono':'jonathan','chris':'christopher'}
LAST = {'sofrinidis':'sofronidis','mcginniss':'mcginnis','elliott':'elliot','coughlan':'coghlan','vandam':'vandam',
 'bromell':'brommell','galimberti':'mcgeegalimberti','oea':'pauloea','gardiner':'gardiner'}
def nz(s): return re.sub(r'[^a-z]', '', s.lower())
def fk(f):
    f = nz(f.split()[0]) if f.strip() else ''
    return FIRST.get(f, f)
def lk(l):
    l = nz(l); return LAST.get(l, l)
def title(s):
    if s.isupper() or s.islower():
        s = ' '.join(w.capitalize() for w in s.split())
        s = re.sub(r"(?<=[ '-])([a-z])", lambda m: m.group(1).upper(), s)
        s = re.sub(r"\b(Mc|O')([a-z])", lambda m: m.group(1)+m.group(2).upper(), s)
        s = s[0].upper()+s[1:] if s else s
    return s
MON = {m: i+1 for i, m in enumerate(['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec'])}
def dob(s):
    s = s.strip()
    if not s or s.startswith('BAD'): return ''
    m = re.match(r'(\d{1,2})[-/ ]([A-Za-z]+|\d{1,2})[-/ ](\d{2,4})$', s)
    if not m: return ''
    d, mo, y = m.groups()
    mo = int(mo) if mo.isdigit() else MON.get(mo[:3].lower())
    y = int(y)
    if y < 100: y = 1900+y if y >= 80 else 2000+y
    try:
        dt = datetime.date(y, mo, int(d))
    except Exception: return ''
    if not (1985 <= y <= 2009): return ''
    return dt.isoformat()
def ht(s):
    try:
        v = float(s); return str(int(round(v))) if 150 <= v <= 215 else ''
    except Exception: return ''
def comm(s):
    s = re.sub(r'\s+(FOOTBALL (& NETBALL )?CLUB|FOOTBALL NETBALL CLUB|FC|FNC)$', '', s.strip(), flags=re.I)
    return title(s)
byzh = {c[3]: c for c in CLUBS}
players = []
for f in sorted(glob.glob(R+'zh_*.csv')):
    for row in csv.reader(open(f, encoding='utf-8')):
        if len(row) < 7 or row[0] not in byzh or row[0] == 'Coburg': continue
        c = byzh[row[0]]
        players.append(dict(club=c[0], list_type=row[1], num=row[2].strip(), first=title(row[3].strip()),
            last=title(row[4].strip()), dob=dob(row[5]), height_cm=ht(row[6]),
            community_club=comm(row[7]) if len(row) > 7 else '', src=ZH))
cobzh = {}
for row in csv.reader(open(R+'zh_2.csv', encoding='utf-8')):
    if row and row[0] == 'Coburg': cobzh[(fk(row[3]), lk(row[4]))] = row
for row in csv.reader(open(R+'coburg_list.csv', encoding='utf-8')):
    z = cobzh.get((fk(row[1]), lk(row[2])))
    players.append(dict(club='COB', list_type='', num=row[0], first=row[1], last=row[2],
        dob=dob(z[5]) if z else '', height_cm=ht(z[6]) if z else '', community_club=comm(z[7]) if z and len(z) > 7 else '',
        src=COBURL + (' ; ' + ZH if z else '')))
# AFL lists
afl = {}
for r in csv.DictReader(open(REPO+'players_2026.csv', encoding='utf-8')):
    afl.setdefault(r['club'], []).append(r)
def afl_match(code, first, last):
    for r in afl.get(code, []):
        if lk(r['last']) == lk(last) and fk(r['first']) == fk(first): return r
    return None
def goals(sb):
    m = re.match(r'(\d+)\.(\d+)', sb.strip()); return (m.group(1), m.group(2)) if m else ('0', '0')
links = []
unmatched = []
for c in CLUBS:
    rows = [p for p in players if p['club'] == c[0]]
    idx = {}
    for p in rows: idx.setdefault((fk(p['first']), lk(p['last'])), p)
    byl = {}
    for p in rows: byl.setdefault(lk(p['last']), []).append(p)
    for s in csv.reader(open(R+'stats_%s.csv' % c[6], encoding='utf-8')):
        if len(s) < 9: continue
        name = s[0].strip(); parts = name.split(' ', 1)
        if len(parts) < 2: continue
        fn, ln = parts
        g, b = goals(s[9] if len(s) > 9 else '')
        st = dict(games=s[1], kicks=s[2], handballs=s[3], disposals=s[4], marks=s[5], tackles=s[6], hitouts=s[7], goals=g, behinds=b)
        p = idx.get((fk(fn), lk(ln)))
        if not p:
            cand = [q for q in byl.get(lk(ln), []) if fk(q['first'])[:1] == fk(fn)[:1]]
            if len(cand) == 1: p = cand[0]
        if not p and c[0] == 'COB' and name == 'Daniel Johnston': p = idx.get(('daniel', 'johnston'))
        if p:
            p.update(st); p['src'] += ' ; ' + ST % c[6]; continue
        a = afl_match(c[4], fn, ln) if c[4] else None
        if a:
            links.append(dict(vfl_club=c[0], afl_club=a['club'], afl_num=a['num'], first=a['first'], last=a['last'], src=ST % c[6], **st))
            continue
        np = dict(club=c[0], list_type='stats_only', num='', first=fn, last=' '.join(ln.split()) , dob='', height_cm='', community_club='', src=ST % c[6])
        np.update(st); players.append(np); unmatched.append(c[0]+':'+name)
for p in players:
    a = afl_match(dict((x[0], x[4]) for x in CLUBS)[p['club']], p['first'], p['last']) if dict((x[0], x[4]) for x in CLUBS)[p['club']] else None
    if not a and p['list_type'] == 'stats_only':
        for code in afl:
            a = afl_match(code, p['first'], p['last'])
            if a: break
    p['afl_listed'] = '1' if a else ('' if p['list_type'] == 'stats_only' else '0')
    p['afl_club'] = a['club'] if a else ''; p['afl_num'] = a['num'] if a else ''
# --- Review fixes (2026-11-12) ---
# 2026 mid-season rookie draft (26 May): these VFL players joined AFL lists. They leave the
# players file; each VFL club they played for becomes a link row. Source names each pick.
MSD_URL = 'https://www.afl.com.au/news/1528009/who-did-your-club-just-take-full-profile-details-bio-of-every-pick-at-the-2026-mid-season-draft'
MSD = {('jaxon','artemis'):'ESS', ('kye','annand'):'RIC', ('flynn','riley'):'CAR', ('xavier','bamert'):'PAD',
       ('oliver','griffin'):'NTH', ('campbell','lake'):'STK', ('harrison','coe'):'COL', ('hugo','hallkahan'):'ADE',
       ('marcus','herbert'):'WCE', ('joel','fitzgerald'):'MEL', ('mitch','podhajski'):'COL', ('max','mapley'):'MEL'}
# Same person on one club's pre-season list and in another club's 2026 stats (aflmstats player
# pages show the move). One row: the club of his last 2026 game, list bio kept, stats summed.
PROFILE = 'https://vfl.aflmstats.com/player/%s_%s'
MOVED = {('deacon','kalpakis'):'ESSR', ('cooper','hamilton'):'SOU', ('ethan','phillips'):'STKR',
         ('ryan','eyre'):'PTM', ('zai','millane'):'SOU'}
SK = ['games','goals','behinds','disposals','kicks','handballs','marks','tackles','hitouts']
def key(p): return (nz(p['first']), nz(p['last']))
keep = []
for p in players:
    k = key(p)
    if k in MSD or p['afl_listed'] == '1':
        code = MSD.get(k, p['afl_club'])
        a = afl_match(code, p['first'], p['last'])
        if p.get('games'):
            links.append(dict(vfl_club=p['club'], afl_club=code, afl_num=a['num'] if a else p.get('afl_num', ''),
                first=a['first'] if a else p['first'], last=a['last'] if a else p['last'],
                src=p['src'] + (' ; ' + MSD_URL if k in MSD else ''), **{s: p[s] for s in SK}))
        continue
    keep.append(p)
players = keep
for k, club in MOVED.items():
    rows = [p for p in players if key(p) == k]
    base = next(p for p in rows if p['list_type'] != 'stats_only')
    played = [p for p in rows if p.get('games')]
    for s in SK: base[s] = str(sum(int(p[s]) for p in played)) if played else ''
    base['src'] = ' ; '.join(dict.fromkeys(u for p in rows for u in p['src'].split(' ; '))) + ' ; ' + PROFILE % (base['first'], base['last'].replace("'", ''))
    base['club'] = club; base['num'] = ''; base['list_type'] = 'moved'
    players = [p for p in players if key(p) != k or p is base]
F = ['club','num','first','last','dob','height_cm','weight_kg','real_pos','list_type','community_club','afl_listed','afl_club','afl_num',
     'games','goals','behinds','disposals','kicks','handballs','marks','tackles','hitouts','source_url']
order = {c[0]: i for i, c in enumerate(CLUBS)}
players.sort(key=lambda p: (order[p['club']], p['list_type'] == 'stats_only', p['last'], p['first']))
with open(OUT+'vfl_players_2026.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh); w.writerow(F)
    for p in players:
        p['source_url'] = p['src']; w.writerow([p.get(k, '') for k in F])
LF = ['vfl_club','afl_club','afl_num','first','last','games','goals','behinds','disposals','kicks','handballs','marks','tackles','hitouts','src']
with open(OUT+'vfl_afl_links_2026.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh); w.writerow(LF[:-1] + ['source_url'])
    for l in links: w.writerow([l.get(k, '') for k in LF])
with open(OUT+'vfl_clubs_2026.csv', 'w', newline='', encoding='utf-8') as fh:
    w = csv.writer(fh); w.writerow(['id','name','short','ground','afl_affiliation','kind','primary','secondary','stats_code','source_url'])
    for c in CLUBS: w.writerow([c[0], c[1], c[2], c[7], c[4], c[5], '', '', c[6], GROUNDS_URL + ' ; ' + ST % c[6]])
n = len(players)
print('players', n, 'links', len(links), 'stats_only', len(unmatched))
for k in F:
    print(k, round(100*sum(1 for p in players if str(p.get(k, '')).strip())/n))
print('dups', [k for k in set((p['club'], p['num']) for p in players if p['num']) if sum(1 for p in players if (p['club'], p['num']) == k) > 1])
print('unmatched sample', unmatched[:80])
