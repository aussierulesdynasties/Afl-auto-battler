#!/usr/bin/env python3
"""Real per-match ruck hit-out splits, 2023-2025, written to tools/balance/afl_ruck_splits.json.

Source: AFL Tables game pages (https://afltables.com/afl/stats/games/<year>/<id>.html), every
home-and-away and finals match of 2023, 2024 and 2025 (216 a season, 648 in all), fetched
2026-11-08 at one request a second into a local cache. Each page's "Match Statistics" tables
give every player's hit-outs (HO) and time on ground (%P).

Per team-match:
  ruck1 = the side's player with the most hit-outs in that match (the sim harness's definition);
  ruck2 = the side's next-most; rest = team total minus ruck1; share = ruck1 / team total.
The summed team total is checked against each page's own Totals row.

To refresh: list the game links on https://afltables.com/afl/seas/<year>.html
(stats/games/<year>/<id>.html), download each page into one folder (one request a second), then

    python3 tools/balance/build_ruck_splits.py <page folder> tools/balance/afl_ruck_splits.json [<sim run dir>]

With a sim run dir (tools/balance.sh match output, a_*.jsonl), it also writes the same summary
for the sim's team lines (team hit-outs and ruck1[0]) to <out>_sim_check.json; the sim does
not log a second ruck, so the sim side has no ruck2 rows.
"""
import glob, html, json, os, re, statistics as st, sys

TABLE_RE = re.compile(r'<th colspan=\d+>([^<]+?) Match Statistics.*?</thead><tbody>(.*?)</tbody>(.*?)</table>', re.S)
ROW_RE = re.compile(r'<tr>(.*?)</tr>', re.S)
CELL_RE = re.compile(r'<td[^>]*>(.*?)</td>', re.S)
HO, PCT_PLAYED = 8, 24  # cell index of HO and %P in a player row (header: # Player KI MK HB DI GL BH HO ...)


def num(s):
    s = re.sub(r'<[^>]+>', '', s).replace('&nbsp;', '')
    s = re.sub(r'[^0-9]', '', s)
    return int(s) if s else 0


def parse_game(path):
    txt = open(path, encoding='latin-1').read()
    base = os.path.basename(path)[:-5]
    year = int(base[4:8])  # <home id 2><away id 2><yyyymmdd>
    m = re.search(r'Round:\s*(?:<[^>]+>\s*)*([A-Za-z0-9 ]+?)\s*<', txt)
    rnd = m.group(1).strip() if m else '?'
    tables = TABLE_RE.findall(txt)
    if len(tables) != 2:
        raise ValueError(f'{base}: {len(tables)} stat tables')
    teams = []
    for club, body, foot in tables:
        players = []
        for r in ROW_RE.findall(body):
            c = CELL_RE.findall(r)
            if len(c) < 25:
                continue
            name = html.unescape(re.sub(r'<[^>]+>', '', c[1])).strip()
            players.append((num(c[HO]), num(c[PCT_PLAYED]), name))
        players.sort(key=lambda p: (-p[0], -p[1]))
        tot = sum(p[0] for p in players)
        tcells = CELL_RE.findall(ROW_RE.findall(foot)[0])
        page_tot = num(tcells[HO - 1]) if len(tcells) > HO - 1 else None  # Totals row: label spans # and Player
        teams.append({'club': html.unescape(club.strip()), 'ho': tot, 'page_total': page_tot,
                      'r1': players[0][0], 'r1_tog': players[0][1], 'r1_name': players[0][2],
                      'r2': players[1][0], 'r2_tog': players[1][1], 'r2_name': players[1][2],
                      'n_with_ho': sum(p[0] > 0 for p in players)})
    final = not rnd.isdigit()
    return [dict(t, y=year, r=rnd, final=final, g=base, opp=teams[1 - i]['club'], opp_ho=teams[1 - i]['ho'],
                 opp_r1=teams[1 - i]['r1']) for i, t in enumerate(teams)]


def pct(xs, p):
    xs = sorted(xs); k = (len(xs) - 1) * p / 100; f = int(k); c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def summ(xs):
    return {'n': len(xs), 'mean': round(st.mean(xs), 2), 'sd': round(st.pstdev(xs), 2),
            **{f'p{p}': round(pct(xs, p), 1) for p in (5, 10, 25, 50, 75, 90, 95)},
            'min': round(min(xs), 1), 'max': round(max(xs), 1)}


def share_of(rs, f):
    return round(100 * sum(1 for r in rs if f(r)) / len(rs), 1)


def block(rs, with_r2=True):
    """rs: team-match dicts with ho, r1, (r2), opp_ho, opp_r1, g."""
    seen, ms = set(), []
    for r in rs:  # one entry per match for the match-level spread
        if r['g'] not in seen:
            seen.add(r['g']); ms.append(r)
    out = {
        'team_hitouts': summ([r['ho'] for r in rs]),
        'ruck1_hitouts': summ([r['r1'] for r in rs]),
        'rest_hitouts': summ([r['ho'] - r['r1'] for r in rs]),
        'ruck1_share_pct': summ([100 * r['r1'] / r['ho'] for r in rs if r['ho']]),
        'ruck1_share_at_least_pct': {f'{t}%': share_of(rs, lambda r, t=t: r['ho'] and 100 * r['r1'] / r['ho'] >= t)
                                     for t in (60, 70, 80, 90, 95, 100)},
        'rest_at_most_pct': {str(t): share_of(rs, lambda r, t=t: r['ho'] - r['r1'] <= t) for t in (0, 2, 5)},
        'ruck1_at_least_pct': {str(t): share_of(rs, lambda r, t=t: r['r1'] >= t) for t in (30, 40, 50)},
        'match_hitout_margin': summ([abs(r['ho'] - r['opp_ho']) for r in ms]),
        'match_hitout_margin_at_least_pct': {str(t): share_of(ms, lambda r, t=t: abs(r['ho'] - r['opp_ho']) >= t)
                                             for t in (10, 20, 30)},
        'match_one_side_share_at_least_pct': {f'{t}%': share_of(ms, lambda r, t=t: (r['ho'] + r['opp_ho']) and
                                                                100 * max(r['ho'], r['opp_ho']) / (r['ho'] + r['opp_ho']) >= t)
                                              for t in (60, 65, 70)},
        'ruck1_head_to_head_gap': summ([abs(r['r1'] - r['opp_r1']) for r in ms]),
        'ruck1_head_to_head_gap_at_least_pct': {str(t): share_of(ms, lambda r, t=t: abs(r['r1'] - r['opp_r1']) >= t)
                                                for t in (10, 20)},
    }
    if with_r2:
        out['ruck2_hitouts'] = summ([r['r2'] for r in rs])
        out['ruck2_share_pct'] = summ([100 * r['r2'] / r['ho'] for r in rs if r['ho']])
        out['ruck2_at_most_pct'] = {str(t): share_of(rs, lambda r, t=t: r['r2'] <= t) for t in (1, 3, 5)}
        out['ruck2_at_least_pct'] = {str(t): share_of(rs, lambda r, t=t: r['r2'] >= t) for t in (10, 15, 20)}
        out['ruck1_tog_pct'] = summ([r['r1_tog'] for r in rs])
    return out


def sim_rows(run):
    rows = []
    for f in sorted(glob.glob(os.path.join(run, 'a_*.jsonl'))):
        for line in open(f, encoding='utf-8'):
            d = json.loads(line)
            a, b = d['teams']
            g = f"{os.path.basename(f)}:{d['i']}"
            for x, y in ((a, b), (b, a)):
                rows.append({'g': g, 'club': x['club'], 'ho': int(x['hitouts']), 'r1': int(x['ruck1'][0]),
                             'opp_ho': int(y['hitouts']), 'opp_r1': int(y['ruck1'][0])})
    return rows


def main():
    cache, out = sys.argv[1], sys.argv[2]
    rows = []
    for p in sorted(glob.glob(os.path.join(cache, '*.html'))):
        rows += parse_game(p)
    bad = [r['g'] + ' ' + r['club'] for r in rows if r['page_total'] is not None and r['page_total'] != r['ho']]
    zero = [r['g'] + ' ' + r['club'] for r in rows if r['ho'] == 0]
    print(len(rows), 'team-matches;', len(bad), 'total mismatches', bad[:5], ';', len(zero), 'zero-hit-out sides', zero[:5])
    years = sorted({r['y'] for r in rows})
    ref = {
        'source': 'AFL Tables game pages (https://afltables.com/afl/stats/games/<year>/<id>.html), the official '
                  'per-player match statistics, every 2023-2025 match including finals (216 a season, 648 matches, '
                  '1296 team-matches). ruck1 = the side\'s player with the most hit-outs in that match (the sim '
                  'harness\'s definition), ruck2 = the next most, rest = team total minus ruck1. Each team total is '
                  'checked against the page\'s Totals row. Percentiles are over team-matches; margins and gaps over '
                  'matches. Built by build_ruck_splits.py from a cache of the pages.',
        'fetched': '2026-11-08',
        'keys': {
            'team_hitouts': 'team hit-outs a match',
            'ruck1_hitouts': 'top ruck\'s hit-outs (most on his side that match)',
            'ruck2_hitouts': 'second-most hit-outs on the side',
            'rest_hitouts': 'team hit-outs not by the top ruck',
            'ruck1_share_pct': 'top ruck\'s share of his side\'s hit-outs, %',
            'ruck2_share_pct': 'second ruck\'s share of his side\'s hit-outs, %',
            'ruck1_share_at_least_pct': '% of team-matches where the top ruck took at least this share',
            'rest_at_most_pct': '% of team-matches where the rest of the side took at most N hit-outs',
            'ruck1_at_least_pct': '% of team-matches where the top ruck had at least N hit-outs',
            'ruck2_at_most_pct': '% of team-matches where the second ruck had at most N hit-outs',
            'ruck2_at_least_pct': '% of team-matches where the second ruck had at least N hit-outs',
            'ruck1_tog_pct': 'top ruck\'s time on ground, %',
            'match_hitout_margin': 'hit-out margin between the two sides (per match)',
            'match_hitout_margin_at_least_pct': '% of matches with a hit-out margin of at least N',
            'match_one_side_share_at_least_pct': '% of matches where one side took at least this share of all hit-outs',
            'ruck1_head_to_head_gap': 'gap between the two top rucks\' hit-outs (per match)',
            'ruck1_head_to_head_gap_at_least_pct': '% of matches where the two top rucks were at least N apart',
        },
    }
    for y in years:
        ref[str(y)] = block([r for r in rows if r['y'] == y])
    ref['2023-2025'] = block(rows)
    ref['2023-2025_home_and_away'] = block([r for r in rows if not r['final']])
    ref['team_matches_fields'] = ['year', 'round', 'game', 'club', 'team_hitouts', 'ruck1', 'ruck1_name', 'ruck1_tog',
                                  'ruck2', 'ruck2_name']
    ref['team_matches'] = [[r['y'], r['r'], r['g'], r['club'], r['ho'], r['r1'], r['r1_name'], r['r1_tog'],
                            r['r2'], r['r2_name']] for r in rows]
    rows_out = ref.pop('team_matches')
    with open(out, 'w', encoding='utf-8', newline='\n') as f:
        head = json.dumps(ref, indent=1, ensure_ascii=False)
        f.write(head[:-2] + ',\n "team_matches": [\n')  # one compact line per team-match
        f.write(',\n'.join('  ' + json.dumps(r, ensure_ascii=False) for r in rows_out))
        f.write('\n ]\n}\n')
    print('wrote', out)
    if len(sys.argv) > 3:
        sim = block(sim_rows(sys.argv[3]), with_r2=False)
        json.dump(sim, open(out.replace('.json', '_sim_check.json'), 'w'), indent=1)
        print('sim summary ->', out.replace('.json', '_sim_check.json'))


if __name__ == '__main__':
    main()
