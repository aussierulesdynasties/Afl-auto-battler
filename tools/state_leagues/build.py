"""Rebuild data/state_leagues/ from the sourced state league files (TODO row 128, step 1).

    python tools/state_leagues/build.py           # writes data/state_leagues/*.csv
    python tools/state_leagues/build.py --check   # fails if the files on disk differ

Inputs, all in the repo:
  tools/state_leagues/staging/   the three leagues' scraped files, one per source family
                                 (written by tools/state_leagues/scrape/, see README.md)
  tools/state_leagues/sources/   the 2026 VFL, SANFL and WAFL season pages (Wikipedia
                                 wikitext): fixtures, scores, ladders, finals, coaches
  data/players_enriched_2026.csv, data/list_additions_2026.csv   the AFL lists (links)

Outputs (one schema across the leagues):
  {vfl,sanfl,wafl}_clubs_2026.csv     clubs, kind, AFL club, ground, colours, 2026 senior coach
  {vfl,sanfl,wafl}_players_2026.csv   state-listed men only (no AFL-listed man), 2026 stats
  afl_links_2026.csv                  AFL-listed men's 2026 state games, keyed by the GameDB id
  leagues.csv                         league shape and scoring, from the season pages
  ladders_2026.csv, finals_2026.csv   the real 2026 ladders and finals (step 5 bracket test)
"""
import csv, datetime, io, os, re, statistics, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.normpath(os.path.join(HERE, '..', '..'))
STG = os.path.join(HERE, 'staging')
SRC = os.path.join(HERE, 'sources')
OUT = os.path.join(REPO, 'data', 'state_leagues')
WIKI = 'https://en.wikipedia.org/wiki/2026_%s_season'
SNAPSHOT = datetime.date(2026, 11, 12)  # footyinfo ages were read on this day
LIST_CAP = 50  # senior list cap, every club (design: "a cap of 50")

STATS = ['gm', 'gl', 'bh', 'di', 'ki', 'hb', 'mk', 'tk', 'ho', 'cl', 'if50', 'rb', 'cm', 'ff', 'fa']
# Columns each league's source records; the rest stay blank (not zero) for that league.
RECORDED = {
    'VFL': {'gm', 'gl', 'bh', 'di', 'ki', 'hb', 'mk', 'tk', 'ho'},
    'SANFL': set(STATS),
    'WAFL': {'gm', 'gl', 'bh', 'di', 'ki', 'hb', 'mk', 'tk', 'ho', 'cl', 'if50', 'ff', 'fa'},
}


def rd(path):
    with open(path, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def norm(s):
    return re.sub(r'[^a-z]', '', (s or '').lower())


def slug(s):
    return re.sub(r'[^a-z0-9]+', '_', (s or '').lower()).strip('_')


def num(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return 0


# Nicknames and spellings seen between state and AFL sources (from the VFL scrape).
FIRST = {'stu': 'stuart', 'seb': 'sebastian', 'tom': 'thomas', 'solly': 'solomon', 'will': 'william',
         'matt': 'matthew', 'mathew': 'matthew', 'kal': 'kallan', 'cam': 'cameron', 'jet': 'jett',
         'lachie': 'lachlan', 'lochlan': 'lachlan', 'ben': 'benjamin', 'mitch': 'mitchell', 'dom': 'dominic',
         'nick': 'nicholas', 'nic': 'nicholas', 'josh': 'joshua', 'dan': 'daniel', 'sam': 'samuel',
         'max': 'maxwell', 'jake': 'jacob', 'alex': 'alexander', 'harry': 'harrison', 'joe': 'joseph',
         'charlie': 'charles', 'fred': 'frederick', 'zac': 'zachary', 'zach': 'zachary', 'ned': 'edward',
         'ollie': 'oliver', 'olly': 'oliver', 'jed': 'jedd', 'jono': 'jonathan', 'chris': 'christopher',
         'tony': 'toby', 'finbar': 'finn', 'caidan': 'caiden', 'damien': 'damon', 'alixzander': 'alix'}
LAST = {'sofrinidis': 'sofronidis', 'mcginniss': 'mcginnis', 'elliott': 'elliot', 'coughlan': 'coghlan',
        'bromell': 'brommell', 'galimberti': 'mcgeegalimberti', 'oea': 'pauloea'}


def fk(f):
    f = norm(f.split()[0]) if (f or '').strip() else ''
    return FIRST.get(f, f)


def lk(l):
    l = norm(re.sub(r'^[A-Za-z]\.\s+', '', (l or '').strip()))  # footyinfo: "Bailey" "J. Williams"
    return LAST.get(l, l)


# ---------------------------------------------------------------- AFL pool (GameDB ids)
def afl_pool():
    pool = []
    seen = set()
    for r in rd(os.path.join(REPO, 'data', 'players_enriched_2026.csv')):
        pid = '%s_%d' % (r['club'], num(r['num']))
        d = 2
        while pid in seen:  # GameDB._load_players: later duplicates get a suffix
            pid = '%s_%d_%d' % (r['club'], num(r['num']), d)
            d += 1
        seen.add(pid)
        pool.append(dict(id=pid, club=r['club'], first=r['first'], last=r['last'], dob=r['dob']))
    n = 0
    for r in rd(os.path.join(REPO, 'data', 'list_additions_2026.csv')):
        if not r['club']:
            continue
        n += 1  # GameDB._load_list_additions: L<season>_<club>_<row>
        pool.append(dict(id='L2026_%s_%03d' % (r['club'], n), club=r['club'], first=r['first'],
                         last=r['last'], dob=r['dob']))
    return pool


POOL = afl_pool()
BY_DOB = defaultdict(list)
BY_CLUB_NAME = defaultdict(list)
BY_NAME = defaultdict(list)
for _a in POOL:
    if _a['dob']:
        BY_DOB[(_a['dob'], lk(_a['last']))].append(_a)
    BY_CLUB_NAME[(_a['club'], fk(_a['first']), lk(_a['last']))].append(_a)
    BY_NAME[(fk(_a['first']), lk(_a['last']))].append(_a)


def afl_match(first, last, dob, affiliate, flagged_club=''):
    """The AFL man this state row is, or None. Name and date of birth first; with no date,
    name at the club's own AFL club (reserves and aligned sides) or at the club the source
    named. A same-named man at another club stays unlinked (WAFL rule)."""
    if dob:
        hit = BY_DOB.get((dob, lk(last)), [])
        if len(hit) == 1 and fk(hit[0]['first'])[:1] == fk(first)[:1]:
            return hit[0], 'name+dob'
    for club, how in ((affiliate, 'name+affiliate'), (flagged_club, 'name+source club')):
        if not club:
            continue
        hit = BY_CLUB_NAME.get((club, fk(first), lk(last)), [])
        if len(hit) == 1 and not (dob and hit[0]['dob'] and hit[0]['dob'] != dob):
            return hit[0], how
        if len(hit) == 1 and club == flagged_club:
            # The source itself names his AFL club; only the two sites' dates differ.
            return hit[0], how + ' (dob differs: state %s)' % dob
    return None, ''


# ---------------------------------------------------------------- season pages
def page(league):
    with open(os.path.join(SRC, '2026_%s_season.wiki' % league), encoding='utf-8') as f:
        return f.read()


def section(text, start, end):
    a = text.index(start)
    return text[a:text.index(end, a + len(start))]


TOKENS = {
    'VFL': {'Box': 'BOX', 'Bri': 'BRLR', 'Car': 'CARR', 'Cas': 'CAS', 'CasD': 'CAS', 'Cob': 'COB',
            'Col': 'COLR', 'Ess': 'ESSR', 'Foo': 'FOO', 'Fra': 'FRA', 'GC': 'GCSR', 'GWS': 'GWSR',
            'Gee': 'GEER', 'Geeres': 'GEER', 'NM': 'NTHR', 'PtM': 'PTM', 'PM': 'PTM', 'Ric': 'RICR',
            'San': 'SAN', 'Sou': 'SOU', 'StK': 'STKR', 'Syd': 'SYDR', 'Wer': 'WER', 'Wil': 'WIL', 'Tas': 'TASD',
            # ladder codes
            'GEE': 'GEER', 'WER': 'WER', 'BOX': 'BOX', 'TAS': 'TASD', 'ESS': 'ESSR', 'POR': 'PTM',
            'SYD': 'SYDR', 'WIL': 'WIL', 'CAR': 'CARR', 'FRA': 'FRA', 'COB': 'COB', 'GWS': 'GWSR',
            'SOU': 'SOU', 'FOO': 'FOO', 'STK': 'STKR', 'COL': 'COLR', 'NOR': 'NTHR', 'BRI': 'BRLR',
            'CAS': 'CAS', 'SAN': 'SAN', 'RIC': 'RICR', 'GCS': 'GCSR'},
    'SANFL': {'Adel': 'ADR', 'Ade': 'ADR', 'CD': 'CTD', 'Cen': 'CTD', 'Gle': 'GLG', 'NA': 'NAD',
              'NthA': 'NAD', 'Nor': 'NWD', 'Por': 'PAM', 'SA': 'SAD', 'SthA': 'SAD', 'Stu': 'STU',
              'WWT': 'WWT', 'WestA': 'WAD'},
    'WAFL': {'Cla': 'CLA', 'EF': 'EFR', 'EP': 'EPR', 'PT': 'PEL', 'Per': 'PER', 'SD': 'SWA', 'SF': 'SFR',
             'Sub': 'SUB', 'WC': 'WCR', 'WCE': 'WCR', 'WP': 'WPR'},
}
# Display names used in the finals' links ([[Club article|Name]]).
NAMES = {
    'VFL': {'Sydney': 'SYDR', 'Frankston': 'FRA', 'Williamstown': 'WIL', 'Carlton': 'CARR', 'Geelong': 'GEER',
            'Tasmania': 'TASD', 'Werribee': 'WER', 'Box Hill': 'BOX', 'Essendon': 'ESSR',
            'Port Melbourne': 'PTM'},
    'SANFL': {'Glenelg': 'GLG', 'Sturt': 'STU', 'Norwood': 'NWD', 'Woodville-West Torrens': 'WWT',
              'West Adelaide': 'WAD'},
    'WAFL': {'Claremont': 'CLA', 'Perth': 'PER', 'South Fremantle': 'SFR', 'East Perth': 'EPR',
             'Peel Thunder': 'PEL'},
}


def team(league, s):
    s = s.strip()
    m = re.match(r'\{\{(?:VFL|SANFL|AFL|WAFL)[ |]([A-Za-z]+)\}\}', s)
    if m:
        return TOKENS[league][m.group(1)]
    m = re.match(r'\[\[[^|\]]*\|([^\]]+)\]\]', s) or re.match(r'\[\[([^\]]+)\]\]', s)
    if m:
        return NAMES[league][m.group(1).strip()]
    raise ValueError('unknown team %r' % s)


SCORE = re.compile(r'(\d+)\.(\d+) \((\d+)\)?')  # one SANFL line lacks its ')'; g*6+b is checked


def game_line(league, line):
    """home, away, (g, b, pts) x2 from one {{AFLGame ...}} line, named or positional."""
    body = line.strip()[len('{{AFLGame|'):-2]
    if 'home team=' in body:
        f = dict(re.findall(r'(home team|away team)=(\{\{[^}]*\}\}|\[\[[^\]]*\]\])', body))
        home, away = team(league, f['home team']), team(league, f['away team'])
    else:
        parts = re.findall(r'(\{\{[^{}]*\}\}|\[\[[^\]]*\]\])', body)
        teams = [p for p in parts if not p.startswith('{{cite') and not p.startswith('{{hlist')]
        home, away = team(league, teams[0]), team(league, teams[1])
    s = SCORE.findall(body)
    return home, away, tuple(map(int, s[0])), tuple(map(int, s[1]))


def detailed_blocks(text):
    out = []
    for blk in re.findall(r'\{\{AFLGameDetailed(.*?)\n\}\}', text, flags=re.S):
        f = {}
        for m in re.finditer(r'^\s*\|\s*([a-z ]+?)\s*=\s*(.*)$', blk, flags=re.M):
            f[m.group(1)] = m.group(2).strip()
        out.append(f)
    return out


def home_away(league):
    t = section(page(league), '==Home-and-away season==', '==Ladder==')
    rounds = re.split(r'^===\s*Round\s+(\d+)\s*===', t, flags=re.M)
    games = []
    for i in range(1, len(rounds), 2):
        rnd = int(rounds[i])
        for line in rounds[i + 1].splitlines():
            if line.startswith('{{AFLGame|'):
                h, a, hs, as_ = game_line(league, line)
                games.append(dict(round=rnd, home=h, away=a, hs=hs, as_=as_))
    return games, (len(rounds) - 1) // 2


def ladder(league):
    t = section(page(league), '==Ladder==', '}}</onlyinclude>')
    src = re.search(r'\|source=\[(\S+)', t).group(1)
    rows = {}
    for m in re.finditer(r'win_(\w+)=(\d+)\s*\|loss_\1=(\d+)\s*\|draw_\1=(\d+)\s*\|pf_\1=(\d+)\s*\|pa_\1=(\d+)', t):
        rows[m.group(1)] = [int(x) for x in m.groups()[1:]]
    order = re.search(r'\|team_order=([^\n]+)', t)
    if order:
        keys = [k.strip() for k in order.group(1).split(',')]
    else:
        keys = [m.group(2) for m in sorted(re.finditer(r'\|team(\d+)=\s*(\w+)', t), key=lambda m: int(m.group(1)))]
    out = []
    for pos, k in enumerate(keys, 1):
        w, l, d, pf, pa = rows[k]
        out.append(dict(league=league, pos=pos, club=TOKENS[league][k], w=w, l=l, d=d, pts=4 * w + 2 * d,
                        pf=pf, pa=pa, pct='%.1f' % (100.0 * pf / pa), source_url=src + ' ; ' + WIKI % league))
    return out


FINAL_NAMES = {'wildcard': 'WC', 'qualifying': 'QF', 'elimination': 'EF', 'first semi': 'SF', 'second semi': 'SF',
               'semi': 'SF', 'preliminary': 'PF', 'grand': 'GF'}


def final_kind(title):
    t = title.lower()
    for k, v in FINAL_NAMES.items():
        if k in t:
            return v
    raise ValueError(title)


def finals(league):
    text = page(league)
    a = text.index('==Finals series==')
    t = text[a:a + 5 + re.search(r'\n==[^=]', text[a + 5:]).start()]
    out, title, lines, i = [], '', t.splitlines(), 0
    while i < len(lines):
        line = lines[i]
        m = re.match(r'\{\{AFLGameHeader\|title=([^{}|]+)', line) or re.match(r'===\s*([^=]+?)\s*===', line)
        if m:
            title = m.group(1)
        if line.startswith('{{AFLGame|'):
            h, a_, hs, as_ = game_line(league, line)
            out.append((final_kind(title), h, a_, hs, as_))
        elif line.startswith('{{AFLGameDetailed'):
            j = i
            while lines[j].strip() != '}}':
                j += 1
            f = detailed_blocks('\n'.join(lines[i:j + 1]))[0]
            hs = tuple(map(int, SCORE.search(f['home final']).groups()))
            as_ = tuple(map(int, SCORE.search(f['away final']).groups()))
            out.append((final_kind(f.get('title', title)), team(league, f['home team']),
                        team(league, f['away team']), hs, as_))
            i = j
        i += 1
    rows = []
    for i, (kind, h, a, hs, as_) in enumerate(out, 1):
        rows.append(dict(league=league, seq=i, final=kind, home=h, away=a, home_score=hs[2], away_score=as_[2],
                         winner=h if hs[2] > as_[2] else a, source_url=WIKI % league))
    return rows


def coaches(league):
    text = page(league)
    head = '===Club leadership===' if league == 'VFL' else '===Venues and leadership==='
    t = section(text, head, '|}')
    out = {}
    for blk in re.split(r'^!\s*style="text-align:left"\s*\|', t, flags=re.M)[1:]:
        lines = blk.splitlines()
        code = team(league, re.sub(r'<small>.*', '', lines[0]).strip())
        cell = lines[1].lstrip('| ').strip()
        cell = re.sub(r'<ref.*?(</ref>|/>)', '', cell)
        names = re.findall(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', cell) or [cell]
        note = ''
        if len(names) > 1:  # a mid-season change: the coach at season's end
            note = re.sub(r'<[^>]+>|\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', lambda m: m.group(1) or ' ', cell)
            note = re.sub(r'\s+', ' ', note).strip()
        out[code] = (names[-1].strip(), note)
    return out


# ---------------------------------------------------------------- clubs
# Colours: the club's own website (hex in its page or stylesheet, read 2026-11-12) where it has
# them, else the club's Wikipedia infobox; a reserves side wears its AFL club's colours
# (data/clubs.csv). (primary, secondary, accent, source)
SITE = 'club website stylesheet, read 2026-11-12: '
COLOURS = {
    'BOX': ('#351C0F', '#FDC82F', '#FFFFFF', SITE + 'https://boxhillhawks.com.au/'),
    'CAS': ('#061A33', '#DE0316', '#FFFFFF', 'https://en.wikipedia.org/wiki/Casey_Demons (infobox hex)'),
    'COB': ('#01245E', '#E3173E', '#FFFFFF', SITE + 'https://coburgfc.com.au/'),
    'FRA': ('#000000', '#FFFFFF', '#FF0000', SITE + 'https://frankstonfc.com.au/'),
    'PTM': ('#203D7A', '#FFFFFF', '#FF0000', SITE + 'https://portmelbournefc.com.au/ ; red: https://en.wikipedia.org/wiki/Port_Melbourne_Football_Club'),
    'SAN': ('#104992', '#FBB529', '#231F20', SITE + 'https://www.sandringhamfc.com.au/'),
    'SOU': ('#262626', '#FFFFFF', '', SITE + 'https://southportsharks.com.au/ ; https://en.wikipedia.org/wiki/Southport_Sharks'),
    'TASD': ('#285D50', '#C00D44', '#FFC94F', 'https://tasmaniafc.com/ (theme colour) ; https://en.wikipedia.org/wiki/Tasmania_Football_Club'),
    'WER': ('#181818', '#FEC625', '', SITE + 'https://werribeefc.com.au/'),
    'WIL': ('#224B8E', '#F5C751', '', 'https://en.wikipedia.org/wiki/Williamstown_Football_Club (infobox hex)'),
    'CTD': ('#072E9D', '#DE1F26', '#FFFFFF', SITE + 'https://cdfc.com.au/'),
    'PEL': ('#022942', '#009783', '#FFFFFF', SITE + 'https://peelthunder.com.au/'),
    'WPR': ('#B42125', '#000A84', '#FFFFFF', SITE + 'https://westperthfc.com.au/'),
}
# SANFL Adelaide's reserves have no designated home ground (SANFL season page).
GROUND_NOTE = {'ADR': 'no designated home ground (2026 SANFL season page)'}
# Ruling 2026-11-12 (row 128 open question 2): the Tasmania Devils VFL side becomes the
# Tasmania AFL club's reserves side when it enters (2028).
FUTURE = {'TASD': 'TAS'}

CLUB_HDR = ['code', 'name', 'short', 'league', 'kind', 'afl_club', 'future_afl_club', 'ground', 'primary',
            'secondary', 'accent', 'coach', 'coach_note', 'source_url', 'colour_source', 'coach_source']


def afl_colours():
    return {r['code']: r for r in rd(os.path.join(REPO, 'data', 'clubs.csv'))}


def build_clubs():
    aflc = afl_colours()
    out = {}
    raw = {
        'VFL': [dict(code=r['id'], name=r['name'], short=r['short'], kind=r['kind'], afl_club=r['afl_affiliation'],
                     ground=r['ground'], src=r['source_url']) for r in rd(os.path.join(STG, 'vfl_clubs_2026.csv'))],
        'SANFL': [dict(code=r['code'], name=r['name'], short=r['short'], kind=r['kind'], afl_club=r['afl_club'],
                       ground=r['ground'], src=r['src'], prim=(r['primary'], r['secondary'], r['accent'], r['colour_src']))
                  for r in rd(os.path.join(STG, 'sanfl_clubs_2026.csv'))],
        'WAFL': [dict(code=r['code'], name=r['name'], short=r['short'], kind=r['kind'], afl_club=r['afl_affiliation'],
                      ground=r['home_ground_2026_name'], src=r['src'].replace(' ', ' ; '),
                      prim=(r['primary'], r['secondary'], r['accent'], r['src'].split()[0]))
                 for r in rd(os.path.join(STG, 'wafl_clubs_2026.csv'))],
    }
    for league, rows in raw.items():
        co = coaches(league)
        res = []
        for r in rows:
            c = r['code']
            if c in COLOURS:
                p, s, a, csrc = COLOURS[c]
            elif r['kind'] == 'reserves':
                x = aflc[r['afl_club']]
                p, s, a, csrc = x['primary'], x['secondary'], x['accent'], 'data/clubs.csv (%s, the AFL club)' % r['afl_club']
            else:
                p, s, a, csrc = r['prim']
            coach, note = co[c]
            res.append(dict(code=c, name=r['name'], short=r['short'], league=league, kind=r['kind'],
                            afl_club=r['afl_club'], future_afl_club=FUTURE.get(c, ''), ground=r['ground'],
                            primary=p.upper(), secondary=s.upper(), accent=a.upper(), coach=coach,
                            coach_note=note,
                            source_url=r['src'] + ((' ; ' + GROUND_NOTE[c]) if c in GROUND_NOTE else ''),
                            colour_source=csrc, coach_source=WIKI % league))
        out[league] = res
    return out


# ---------------------------------------------------------------- players
# Source corrections, each with its evidence.
FIXES = {
    # SANFL API lists him surname "Seb", first name "Wauer"; SANFL's 2024 U18 Future Stars
    # list and Rookie Me's 2023 scouting notes name him Seb Wauer (185 cm midfielder).
    ('SANFL', 'CTD', 'Wauer', 'Seb'): dict(
        first='Seb', last='Wauer', height_cm='185', height_src='source',
        note='name order fixed (SANFL API had it reversed); height 185 cm from Rookie Me 2023 U18 scouting notes',
        source_url='https://sanfl.com.au/league/news/2024-sanfl-u18-future-stars/ ; '
                   'https://central.rookieme.com/afl/2023/05/16/scouting-notes-south-australia-vs-giants-swans-academies/'),
}

PLAYER_HDR = ['sid', 'league', 'club', 'list', 'num', 'first', 'last', 'dob', 'dob_src', 'height_cm', 'height_src',
              'weight_kg', 'pos'] + STATS + ['res_gm', 'res_gl', 'colts_gm', 'colts_gl', 'career_gm_pre2026',
                                              'junior_club', 'note', 'source_url']
LINK_HDR = ['league', 'state_club', 'afl_id', 'afl_club', 'first', 'last', 'dob'] + STATS + ['match', 'source_url']


def vfl_rows(clubs):
    aff = {c['code']: c['afl_club'] for c in clubs}
    rows = []
    for r in rd(os.path.join(STG, 'vfl_players_2026.csv')):
        st = dict(gm=r['games'], gl=r['goals'], bh=r['behinds'], di=r['disposals'], ki=r['kicks'],
                  hb=r['handballs'], mk=r['marks'], tk=r['tackles'], ho=r['hitouts'])
        rows.append(dict(league='VFL', club=r['club'], num=r['num'], first=r['first'], last=r['last'], dob=r['dob'],
                         height_cm=r['height_cm'], weight_kg=r['weight_kg'], pos=r['real_pos'], stats=st,
                         junior_club=r['community_club'], note='stats only: not on the club\'s pre-season list'
                         if r['list_type'] == 'stats_only' else ('moved club during 2026' if r['list_type'] == 'moved' else ''),
                         source_url=r['source_url'], affiliate=aff[r['club']], flagged=''))
    for r in rd(os.path.join(STG, 'vfl_afl_links_2026.csv')):
        st = dict(gm=r['games'], gl=r['goals'], bh=r['behinds'], di=r['disposals'], ki=r['kicks'],
                  hb=r['handballs'], mk=r['marks'], tk=r['tackles'], ho=r['hitouts'])
        rows.append(dict(league='VFL', club=r['vfl_club'], num='', first=r['first'], last=r['last'], dob='',
                         height_cm='', weight_kg='', pos='', stats=st, junior_club='', note='',
                         source_url=r['source_url'], affiliate=aff[r['vfl_club']], flagged=r['afl_club']))
    return rows


def sanfl_rows(clubs):
    aff = {c['code']: c['afl_club'] for c in clubs}
    rows = []
    for fn in ('sanfl_players_2026.csv', 'sanfl_afl_listed_2026.csv'):
        for r in rd(os.path.join(STG, fn)):
            st = {k: r[k] for k in STATS}
            if r['sanfl_id'] and st['gm'] == '':
                st['gm'] = '0'
            rows.append(dict(league='SANFL', club=r['club'], num=r['num'], first=r['first'], last=r['last'],
                             dob=r['dob'], height_cm=r['height_cm'], weight_kg=r['weight_kg'], pos=r['real_pos'],
                             stats=st, res_gm=r['res_gm'], res_gl=r['res_gl'],
                             career_gm_pre2026=r['career_league_gm'], note='',
                             source_url=' ; '.join(x for x in (r['src_roster'], r['src_stats']) if x),
                             affiliate=aff[r['club']], flagged=r['afl_club'] if r['afl_listed'] else ''))
    return rows


def wafl_rows(clubs):
    aff = {c['code']: c['afl_club'] for c in clubs}
    rows = []
    for fn in ('wafl_players_2026.csv', 'wafl_afl_listed_appearances_2026.csv'):
        for r in rd(os.path.join(STG, fn)):
            st = dict(gm=r['lg_gm'], gl=r['lg_gl'], bh=r['lg_bh'], di=r['lg_di'], ki=r['lg_ki'], hb=r['lg_hb'],
                      mk=r['lg_mk'], tk=r['lg_tk'], ho=r['lg_ho'], cl=r['lg_cl'], if50=r['lg_i50'],
                      ff=r['lg_ff'], fa=r['lg_fa'])
            age = r['age']
            rows.append(dict(league='WAFL', club=r['club'], num=r['num'], first=r['first'], last=r['last'],
                             dob=r['dob'], age=age, height_cm=r['height_cm'], weight_kg=r['weight_kg'], pos=r['pos'],
                             stats=st, res_gm=r['res_gm'], res_gl=r['res_gl'], colts_gm=r['colts_gm'],
                             colts_gl=r['colts_gl'], career_gm_pre2026=r['lg_career_gm_before_2026'],
                             note=r['note'], source_url=' ; '.join(x for x in (r['src_list'], r['src_stats'],
                                                                            r['src_profile'], r['src_dob']) if x),
                             affiliate=aff[r['club']], flagged=r['afl_club'] if r['afl_listed'] == 'Y' else '',
                             appearance_only=fn.startswith('wafl_afl')))
    # A colt listed at his own club who played League for West Coast's reserves: one row,
    # at his own club, with the West Coast League games added (footyinfo lists him twice).
    out = []
    by = defaultdict(list)
    for r in rows:
        by[(norm(r['first']), norm(r['last']))].append(r)
    drop = set()
    for k, rs in by.items():
        wcr = [r for r in rs if r['club'] == 'WCR' and not r['appearance_only']]
        home = [r for r in rs if r['club'] != 'WCR' and 'also listed by footyinfo at WCR' in r['note']]
        if wcr and len(home) == 1:
            h, w = home[0], wcr[0]
            for s, v in w['stats'].items():
                if v not in ('', None):
                    h['stats'][s] = str(num(h['stats'].get(s)) + num(v))
            h['note'] = re.sub(r'; same player also listed.*', '', h['note'])
            h['note'] = re.sub(r'footyinfo shows \d+ league games in 2026, none for this club',
                               '%s League games for West Coast (WAFL) in 2026' % w['stats']['gm'], h['note'])
            h['source_url'] += ' ; ' + w['source_url']
            drop.add(id(w))
    return [r for r in rows if id(r) not in drop]


def coarse_role(r):
    if r['pos'] in ('DEF', 'MID', 'FWD', 'RUC'):
        return r['pos']
    g = num(r['stats'].get('gm'))
    if g:
        if num(r['stats'].get('ho')) / g >= 5:
            return 'RUC'
        if num(r['stats'].get('gl')) / g >= 0.8:
            return 'FWD'
    return 'GEN'


def build_players(clubs):
    links, players = [], []
    unlinked_flag = []
    for league, fn in (('VFL', vfl_rows), ('SANFL', sanfl_rows), ('WAFL', wafl_rows)):
        for r in fn(clubs[league]):
            fx = FIXES.get((league, r['club'], r['first'], r['last']))
            if fx:
                r.update({k: v for k, v in fx.items() if k != 'note' and k != 'source_url'})
                r['note'] = fx['note']
                r['source_url'] = fx['source_url'] + ' ; ' + r['source_url']
            a, how = afl_match(r['first'], r['last'], r['dob'], r['affiliate'], r['flagged'])
            if a:
                rec = r['stats']
                links.append(dict(league=league, state_club=r['club'], afl_id=a['id'], afl_club=a['club'],
                                  first=a['first'], last=a['last'], dob=a['dob'], match=how,
                                  source_url=r['source_url'], **{s: rec.get(s, '') for s in STATS}))
                continue
            if r['flagged'] or r.get('appearance_only'):
                unlinked_flag.append('%s %s %s %s (source: AFL %s)' % (league, r['club'], r['first'], r['last'], r['flagged']))
                # Not on the AFL lists in data/, so he plays as a state man; the note says why.
                extra = 'source marks him AFL-listed (%s); not on the 2026 AFL lists in data/' % r['flagged']
                r['note'] = r['note'] + '; ' + extra if r['note'] else extra
            players.append(r)
    return links, players, unlinked_flag


def finish_players(players):
    """Stats in the league's recorded columns, lists, ids, and flagged imputations."""
    for r in players:
        rec = RECORDED[r['league']]
        st = r['stats']
        st['gm'] = str(num(st.get('gm')))
        for s in STATS:
            r[s] = (str(num(st.get(s))) if st.get(s) not in (None, '') or s in ('gm',) else ('0' if st['gm'] == '0' else '')) if s in rec else ''
        for k in ('res_gm', 'res_gl', 'colts_gm', 'colts_gl', 'career_gm_pre2026', 'junior_club', 'num', 'weight_kg'):
            r.setdefault(k, '')
    # date of birth: source; else from the source's age; else the league median, flagged.
    for league in ('VFL', 'SANFL', 'WAFL'):
        known = sorted(r['dob'] for r in players if r['league'] == league and r['dob'])
        median = known[len(known) // 2]
        for r in players:
            if r['league'] != league:
                continue
            if r['dob']:
                r['dob_src'] = 'source'
            elif r.get('age'):
                d = SNAPSHOT - datetime.timedelta(days=round(365.25 * (num(r['age']) + 0.5)))
                r['dob'], r['dob_src'] = d.isoformat(), 'age'
            else:
                r['dob'], r['dob_src'] = median, 'league_median'
    # height: source; else the median of the league's men in the same coarse role, flagged.
    for league in ('VFL', 'SANFL', 'WAFL'):
        med = defaultdict(list)
        for r in players:
            if r['league'] == league and str(r['height_cm']).isdigit():
                med[coarse_role(r)].append(int(r['height_cm']))
                med['ALL'].append(int(r['height_cm']))
        for r in players:
            if r['league'] != league:
                continue
            if str(r['height_cm']).isdigit():
                r.setdefault('height_src', 'source')
            else:
                role = coarse_role(r)
                vals = med[role] if role != 'GEN' and med[role] else med['ALL']
                r['height_cm'], r['height_src'] = str(int(statistics.median(vals))), 'role_median_' + (role if role != 'GEN' else 'all')
    # lists: League and Reserves men to the senior cap (most League, then Reserves games);
    # WAFL Colts-only men are juniors; the rest stay on the club's books as "extra".
    byclub = defaultdict(list)
    for r in players:
        byclub[r['club']].append(r)
    for club, rs in byclub.items():
        cand = []
        for r in rs:
            if r['league'] == 'WAFL' and num(r['colts_gm']) and not num(r['gm']) and not num(r['res_gm']):
                r['list'] = 'junior'
            else:
                cand.append(r)
        cand.sort(key=lambda r: (-num(r['gm']), -num(r['res_gm']), -num(r['di']), r['last'], r['first']))
        for i, r in enumerate(cand):
            r['list'] = 'senior' if i < LIST_CAP else 'extra'
    seen = Counter()
    order = {}
    for r in players:
        base = '%s_%s_%s' % (r['club'], slug(r['first']), slug(r['last']))
        seen[base] += 1
        r['sid'] = base if seen[base] == 1 else '%s_%d' % (base, seen[base])
    return players


# ---------------------------------------------------------------- leagues
SHAPE = {  # finals format and Grand Final venue: season pages (Finals series sections)
    'VFL': dict(name='Victorian Football League', finals_teams=10, finals_format='wildcard_top10', gf_venue='Ikon Park'),
    'SANFL': dict(name='South Australian National Football League', finals_teams=5, finals_format='final_five', gf_venue='Adelaide Oval'),
    'WAFL': dict(name='West Australian Football League', finals_teams=5, finals_format='final_five', gf_venue='Optus Stadium'),
}
LEAGUE_HDR = ['league', 'name', 'clubs', 'rounds', 'games_each', 'byes_each', 'finals_teams', 'finals_format',
              'gf_venue', 'points_per_team_game', 'points_sd', 'goal_accuracy', 'premiers', 'runners_up', 'source_url']


def build_leagues(clubs, fin):
    rows = []
    for league in ('VFL', 'SANFL', 'WAFL'):
        games, nrounds = home_away(league)
        per = Counter()
        scores, gl, bh = [], 0, 0
        for g in games:
            per[g['home']] += 1
            per[g['away']] += 1
            for s in (g['hs'], g['as_']):
                scores.append(s[2])
                gl += s[0]
                bh += s[1]
                assert s[0] * 6 + s[1] == s[2], (league, g)
        each = set(per.values())
        assert len(each) == 1 and len(per) == len(clubs[league]), (league, per)
        each = each.pop()
        gf = [f for f in fin if f['league'] == league and f['final'] == 'GF'][0]
        rows.append(dict(league=league, clubs=len(clubs[league]), rounds=nrounds, games_each=each,
                         byes_each=nrounds - each, points_per_team_game='%.1f' % statistics.mean(scores),
                         points_sd='%.1f' % statistics.pstdev(scores), goal_accuracy='%.3f' % (gl / (gl + bh)),
                         premiers=gf['winner'], runners_up=gf['home'] if gf['winner'] == gf['away'] else gf['away'],
                         source_url=WIKI % league + ' (home-and-away scores, %d matches; finals)' % len(games),
                         **SHAPE[league]))
    return rows


# ---------------------------------------------------------------- write
def to_csv(hdr, rows):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=hdr, lineterminator='\n', extrasaction='ignore')
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, '') for k in hdr})
    return buf.getvalue()


def main():
    check = '--check' in sys.argv
    clubs = build_clubs()
    links, players, flagged = build_players(clubs)
    players = finish_players(players)
    lad = [r for lg in ('VFL', 'SANFL', 'WAFL') for r in ladder(lg)]
    fin = [r for lg in ('VFL', 'SANFL', 'WAFL') for r in finals(lg)]
    files = {}
    for lg in ('VFL', 'SANFL', 'WAFL'):
        files['%s_clubs_2026.csv' % lg.lower()] = to_csv(CLUB_HDR, clubs[lg])
        order = {c['code']: i for i, c in enumerate(clubs[lg])}
        rs = sorted((p for p in players if p['league'] == lg),
                    key=lambda p: (order[p['club']], ['senior', 'extra', 'junior'].index(p['list']), p['last'], p['first']))
        files['%s_players_2026.csv' % lg.lower()] = to_csv(PLAYER_HDR, rs)
    links.sort(key=lambda l: (['VFL', 'SANFL', 'WAFL'].index(l['league']), l['state_club'], l['afl_id']))
    files['afl_links_2026.csv'] = to_csv(LINK_HDR, links)
    files['leagues.csv'] = to_csv(LEAGUE_HDR, build_leagues(clubs, fin))
    files['ladders_2026.csv'] = to_csv(['league', 'pos', 'club', 'w', 'l', 'd', 'pts', 'pf', 'pa', 'pct', 'source_url'], lad)
    files['finals_2026.csv'] = to_csv(['league', 'seq', 'final', 'home', 'away', 'home_score', 'away_score', 'winner',
                                       'source_url'], fin)
    os.makedirs(OUT, exist_ok=True)
    bad = []
    for name, text in files.items():
        path = os.path.join(OUT, name)
        if check:
            cur = open(path, encoding='utf-8', newline='').read() if os.path.exists(path) else None
            if cur != text:
                bad.append(name)
        else:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(text)
            imp = path + '.import'
            with open(imp, 'w', encoding='utf-8', newline='\n') as f:
                f.write('[remap]\n\nimporter="keep"\n\n[deps]\n\nsource_file="res://data/state_leagues/%s"\n' % name)
    if check:
        print('out of date:', bad if bad else 'none')
        sys.exit(1 if bad else 0)
    for lg in ('VFL', 'SANFL', 'WAFL'):
        ps = [p for p in players if p['league'] == lg]
        print(lg, 'clubs', len(clubs[lg]), 'players', len(ps), Counter(p['list'] for p in ps),
              'links', sum(1 for l in links if l['league'] == lg),
              'dob', Counter(p['dob_src'] for p in ps), 'height', Counter(p['height_src'][:4] for p in ps))
    print('source-flagged AFL men not on the AFL lists (kept as state men):', len(flagged))
    for f in flagged:
        print('  ', f)


if __name__ == '__main__':
    main()
