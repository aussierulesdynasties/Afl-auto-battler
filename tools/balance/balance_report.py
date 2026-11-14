"""One-page balance report for tools/balance.sh runs.

Reads <run>/a_*.jsonl (and b_*.jsonl when paired), averages each team stat per
team-match, and marks it against real AFL 2026 rates (afl_team_rates.json):
IN when inside the 18 clubs' lowest..highest, NEAR when within mean +-2 sd,
else OUT. Paired runs also show B - A with its standard error over seeds, so a
change is real when |delta| > 2 se.
"""
import argparse, csv, glob, json, math, os, re, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
# sim stat -> afl_team_rates key (score is computed from goals/behinds there)
MAP = {"disposals": "disposals", "kicks": "kicks", "handballs": "handballs",
       "marks": "marks", "contested_marks": "contested_marks", "tackles": "tackles",
       "inside50": "inside_50s", "clearances": "clearances", "hitouts": "hitouts",
       "frees_for": "frees_for", "goals": "goals", "behinds": "behinds",
       "rebound50": "rebound_50s", "rebounds": "rebound_50s"}
EXTRA = ["score", "clangers", "intercepts", "one_percenters", "metres_gained", "strength", "draftees",
         "contested_possessions", "ground_ball_gets", "pressure_acts", "ball_ups", "throw_ins", "stoppages"]
# Real weather against a perfect day, AFL 2016-25 without 2020 (afl_weather_rates.json,
# built by build_weather_rates.py from AFL Tables match totals and Open-Meteo weather at
# the ground). Shown for a paired run when B is a weather arm and A is not, so it reads
# as the real reference for B against A. sim stat -> afl_weather_rates key.
WEATHER_KEYS = {"disposals": "disposals", "kicks": "kicks", "handballs": "handballs",
                "marks": "marks", "contested_marks": "contested_marks", "tackles": "tackles",
                "contested_possessions": "contested_possessions",
                "uncontested_possessions": "uncontested_possessions", "clangers": "clangers",
                "one_percenters": "one_percenters", "inside50": "inside_50s",
                "clearances": "clearances", "frees_for": "frees_for", "hitouts": "hitouts",
                "running_bounces": "bounces", "goal_assists": "goal_assists",
                "rebounds": "rebound_50s", "marks_inside_50": "marks_inside_50",
                "goals": "goals", "behinds": "behinds", "score": "score",
                "ground_ball_gets": None, "stoppages": None, "ball_ups": None}
# [ABC] wet against dry 2022-25 for ground-ball gets, which AFL Tables does not count.
REAL_WET_ABC = {"ground_ball_gets": (0.09, 0.03)}


def weather_ref():
    p = os.path.join(HERE, "afl_weather_rates.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def weather_mark(sim, sim_se, real, real_se):
    """IN within 2 combined standard errors of the real change, NEAR within 4, else OUT."""
    s = math.sqrt(sim_se ** 2 + real_se ** 2)
    if abs(sim - real) <= 2 * s:
        return "IN"
    return "NEAR" if abs(sim - real) <= 4 * s else "OUT"


def odd_even(r):
    """Margin in the odd quarters less the even ones, from both teams' quarter scores."""
    q = [[t["q_score"][k] - (t["q_score"][k - 1] if k else 0) for k in range(4)] for t in r["teams"]]
    m = [q[0][k] - q[1][k] for k in range(4)]
    return (m[0] + m[2]) - (m[1] + m[3])


def q4_share(r):
    tot = sum(t["q_score"][3] for t in r["teams"])
    return 100.0 * sum(t["q_score"][3] - t["q_score"][2] for t in r["teams"]) / tot if tot else None


def breeze_size(sa, sb, n_boot=1000):
    """Breeze worth B points of margin a quarter: Var(odd-even, B) - Var(odd-even, A) = 16 B^2.
    Returns B and its bootstrap standard error (seeded, so the report is stable)."""
    import random
    rng = random.Random(61)

    def b_of(x, y):
        return math.sqrt(max(0.0, st.variance(x) - st.variance(y))) / 4.0
    boots = [b_of(rng.choices(sb, k=len(sb)), rng.choices(sa, k=len(sa))) for _ in range(n_boot)]
    return b_of(sb, sa), st.stdev(boots)


def load(run, arm):
    rows = {}
    for f in glob.glob(os.path.join(run, arm + "_*.jsonl")):
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    r = json.loads(line)
                    rows[r["i"]] = r
    return rows


def per_match(rows, key):
    """Seed -> mean of both teams' value (one team-match average per match)."""
    return {i: sum(float(t.get(key, 0)) for t in r["teams"]) / 2 for i, r in rows.items()}


def margins(rows):
    m = [abs(r["teams"][0]["score"] - r["teams"][1]["score"]) for r in rows.values()]
    h = [r["teams"][0]["score"] - r["teams"][1]["score"] for r in rows.values()]
    return m, h


# Set shots against real AFL (docs/research/SET_SHOT_EVIDENCE.md): share of shots
# from the Champion Data expected-score shot counts [WH] (2026: 5,951 set of
# 10,859, 55%); goals per shot by distance [ABC] 2021-25, the straight-in-front
# column (Director Bible #62 names these as the targets), set / general play.
# [ABC]'s "straight" is within 30 degrees, so the sim's 45 m "slight angle" spot
# is a straight-column shot. The sim's pocket (15 m, tight angle) is its own row
# against the 10-20 m wide cells: set 66% and 55% (mean 60.5%), general 21% and 22%.
REAL_SET_SHARE = 0.55
# Real shots that score (goals + behinds per shot at goal, [WH] 2026: 9,047 of
# 10,860). Set and general-play no-score rates are not published apart.
REAL_SCORING_PER_SHOT = 0.833
SHOT_BANDS = ["0-10", "10-20", "20-30", "30-40", "40-50", "50+", "pocket"]
REAL_SET_ACC = {"0-10": 1.00, "10-20": 0.96, "20-30": 0.85, "30-40": 0.71, "40-50": 0.54, "50+": 0.33, "pocket": 0.605}
REAL_GP_ACC = {"0-10": 0.89, "10-20": 0.63, "20-30": 0.51, "30-40": 0.38, "40-50": 0.39, "50+": 0.34, "pocket": 0.215}


def pooled(R, key):
    return sum(float(t.get(key, 0)) for r in R.values() for t in r["teams"])


def share_by_seed(R, scoring=False):
    """Seed -> set-shot share of that match's shots (both teams), in percent.
    scoring=True counts only shots that scored (goal or behind) on both sides."""
    def cnt(t, pre):
        if scoring:
            return float(t.get(pre + "_g", 0)) + float(t.get(pre + "_b", 0))
        return float(t.get(pre + "_n", 0))
    out = {}
    for i, r in R.items():
        n = sum(cnt(t, "sshot") + cnt(t, "gshot") for t in r["teams"])
        if n:
            out[i] = 100 * sum(cnt(t, "sshot") for t in r["teams"]) / n
    return out


def shots_section(A, B):
    """Set-shot share, conversion by distance and scoring shots, per arm."""
    if not any("sshot_n" in t for r in A.values() for t in r["teams"]):
        return
    arms = [("A", A)] + ([("B", B)] if B else [])
    print("\n## Shots\n")
    head = "| per team-match | real |" + "".join(f" {k} |" for k, _ in arms) + (" B-A | se |" if B else "")
    print(head)
    print("|" + "---|" * (head.count("|") - 1))

    def row(label, real, vals, a=None, b=None, fmt="{:.1f}"):
        line = f"| {label} | {real} |" + "".join(" " + fmt.format(v) + " |" for v in vals)
        if a is not None and b is not None:
            common = [i for i in a if i in b]
            d = [b[i] - a[i] for i in common]
            se = st.stdev(d) / math.sqrt(len(d)) if len(d) > 1 else 0.0
            line += " " + ("{:+.2f}".format(st.mean(d))) + f" | {se:.2f} |"
        print(line)
    n = {k: len(R) * 2 for k, R in arms}
    for key, label in (("sshot_n", "set shots"), ("gshot_n", "general-play shots")):
        row(label, "-", [pooled(R, key) / n[k] for k, R in arms],
            per_match(A, key) if B else None, per_match(B, key) if B else None)
    sc = {k: {i: sum(float(t.get("goals", 0)) + float(t.get("behinds", 0)) for t in r["teams"]) / 2
              for i, r in R.items()} for k, R in arms}
    row("scoring shots (goals + behinds)", "22.4", [st.mean(sc[k].values()) for k, _ in arms],
        sc["A"] if B else None, sc.get("B"))
    sh = {k: share_by_seed(R) for k, R in arms}
    row("set-shot share of shots (general play counted only when it scores)", f"{100 * REAL_SET_SHARE:.0f}%",
        [100 * pooled(R, "sshot_n") / max(1, pooled(R, "sshot_n") + pooled(R, "gshot_n")) for k, R in arms],
        sh["A"] if B else None, sh.get("B"), fmt="{:.1f}")

    def scoring_share(R):
        ss = pooled(R, "sshot_g") + pooled(R, "sshot_b")
        return 100 * ss / max(1, ss + pooled(R, "gshot_g") + pooled(R, "gshot_b"))
    sc_sh = {k: share_by_seed(R, True) for k, R in arms}
    row("set-shot share of scoring shots", "~55%*", [scoring_share(R) for k, R in arms],
        sc_sh["A"] if B else None, sc_sh.get("B"), fmt="{:.1f}")
    print("\nThe sim logs a general-play shot only when it scores, so the first share has a short"
          " denominator; the scoring-shot share counts both kinds alike. *Real: "
          f"{100 * REAL_SET_SHARE:.0f}% of shots are set shots and {100 * REAL_SCORING_PER_SHOT:.0f}% of"
          " shots score [WH]; if both kinds score equally often, set shots are 55% of scoring shots too"
          " (the two no-score rates are not published apart).")
    print("\nGoals per shot, pooled over every shot of the arm. Real: [ABC] 2021-25, straight in front"
          " (within 30 degrees); the pocket row against the 10-20 m wide cells.\n")
    head = "| shots | real set | real general |" + "".join(f" {k} goals/shot | {k} a team |" for k, _ in arms)
    print(head)
    print("|" + "---|" * (head.count("|") - 1))
    for band in SHOT_BANDS:
        label = "set, pocket (15 m, tight angle)" if band == "pocket" else f"set, {band} m"
        line = f"| {label} | {100 * REAL_SET_ACC[band]:.1f}% | {100 * REAL_GP_ACC[band]:.1f}% |"
        for k, R in arms:
            sn = pooled(R, f"sshot_{band}_n")
            line += (f" {100 * pooled(R, f'sshot_{band}_g') / sn:.0f}% |" if sn else " - |") + f" {sn / n[k]:.2f} |"
        print(line)
    for key, label in (("sshot", "all set shots"), ("gshot", "general play (no distance in the sim)")):
        line = f"| {label} | - | - |"
        for k, R in arms:
            sn = pooled(R, key + "_n")
            line += (f" {100 * pooled(R, key + '_g') / sn:.0f}% |" if sn else " - |") + f" {sn / n[k]:.2f} |"
        print(line)
def duel_section(A, B):
    """Key forward v key defender (row 94): contests per duel per match from the
    engine's duel log, as the full-time line reads them. A duel is one key
    forward's match: [contests, marks, most against one defender, verdict]."""
    if not any("duels" in r for r in A.values()):
        return
    arms = [("A", A)] + ([("B", B)] if B else [])
    stats = {}
    for name, R in arms:
        rows = [d for r in R.values() for d in r.get("duels", [])]
        n = max(1, len(rows))
        c = sorted(d[0] for d in rows)
        stats[name] = {
            "contests": st.mean(c) if c else 0.0,
            "median": st.median(c) if c else 0.0,
            "pair": st.mean(d[2] for d in rows) if rows else 0.0,
            "6+": 100 * sum(d[0] >= 6 for d in rows) / n,
            "shown": 100 * sum(d[0] >= 4 for d in rows) / n,
            "mark%": 100 * sum(d[1] for d in rows) / max(1, sum(c)),
            "beat": 100 * sum(d[0] >= 4 and d[3] > 0 for d in rows) / n,
            "even": 100 * sum(d[0] >= 4 and d[3] == 0 for d in rows) / n,
            "held": 100 * sum(d[0] >= 4 and d[3] < 0 for d in rows) / n,
            "duels": len(rows)}
    print("\n## Key forward v key defender (contests per duel per match)\n")
    print("A duel is one key forward's match against his direct opponent(s), from MatchSim.duel_log "
          "(what the full-time line counts; MatchNotes shows a line from 4 contests). "
          "beat / even / held: the line's verdict, as a share of all duels.\n")
    head = "| arm | duels | contests mean | median | v one defender | 6+ contests | line shown (4+) | forward marks | beat / even / held |"
    print(head)
    print("|" + "---|" * (head.count("|") - 1))
    for name, _ in arms:
        s = stats[name]
        print(f"| {name} | {s['duels']} | {s['contests']:.2f} | {s['median']:.0f} | {s['pair']:.2f} | {s['6+']:.0f}% | "
              f"{s['shown']:.0f}% | {s['mark%']:.1f}% | {s['beat']:.0f} / {s['even']:.0f} / {s['held']:.0f} |")
    if B:
        def per(R):
            return {i: st.mean(d[0] for d in r["duels"]) for i, r in R.items() if r.get("duels")}
        a, b = per(A), per(B)
        d = [b[i] - a[i] for i in a if i in b]
        if len(d) > 1:
            print(f"\nContests per duel B-A {st.mean(d):+.2f} (se {st.stdev(d) / math.sqrt(len(d)):.2f}, paired by seed).")


TAIL = (40, 60, 80, 100, 120)
ROOT = os.path.dirname(os.path.dirname(HERE))


def real_margins():
    """Real AFL 2026 home-and-away margins from data/raw/fixtures_2026.json (finals left out)."""
    path = os.path.join(ROOT, "data", "raw", "fixtures_2026.json")
    if not os.path.exists(path):
        return []
    games = json.load(open(path, encoding="utf-8"))["games"]
    return [abs(g["hscore"] - g["ascore"]) for g in games
            if g.get("complete") == 100 and not g.get("is_final")]


def real_history():
    """Real AFL 2010-2025, every match with finals (afl_comebacks.json, AFL Tables): (h[4], a[4])."""
    path = os.path.join(HERE, "afl_comebacks.json")
    if not os.path.exists(path):
        return []
    return [(g["h"], g["a"]) for g in json.load(open(path, encoding="utf-8"))["games"]]


def came_back(h, a, k):
    """The winner was k or more points down at a quarter break (QT, HT or 3QT)."""
    if h[3] == a[3]:
        return False
    s = 1 if h[3] > a[3] else -1
    return any(s * (a[q] - h[q]) >= k for q in range(3))


def wilson(k, n, z=1.96):
    if n == 0:
        return 0.0, 0.0
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * (c - h), 100 * (c + h)


def margin_tail(A, B):
    """The margin distribution's tail: share of matches at 40+ .. 120+ points, mean, p90, p99,
    max, against real AFL 2026; paired runs add B - A per seed with its standard error."""
    real = real_margins()
    hist = real_history()
    hm = [abs(h[3] - a[3]) for h, a in hist]
    common = [i for i in A if i in B] if B else list(A)
    ma = {i: abs(A[i]["teams"][0]["score"] - A[i]["teams"][1]["score"]) for i in common}
    mb = {i: abs(B[i]["teams"][0]["score"] - B[i]["teams"][1]["score"]) for i in common} if B else {}
    n = len(common)
    print(f"\n## Margin tail ({n} matches{' per arm, paired' if B else ''})\n")
    head = f"| margin | real AFL 2026 ({len(real)} H&A games, 95% CI) | real 2010-25 ({len(hm)}) | A |"
    if B:
        head += " B | B-A | se | sig |"
    print(head)
    print("|" + "---|" * (head.count("|") - 1))

    def row(label, f_real, f_hist, fa, fb, fmt):
        line = f"| {label} | {f_real} | {f_hist} | {fmt(st.mean(fa))} |"
        if B:
            d = [b - a for a, b in zip(fa, fb)]
            md = st.mean(d)
            se = st.stdev(d) / math.sqrt(len(d)) if len(d) > 1 else 0.0
            sig = "yes" if se > 0 and abs(md) > 2 * se else ""
            line += f" {fmt(st.mean(fb))} | {fmt(md, True)} | {fmt(se)} | {sig} |"
        print(line)
    for t in TAIL:
        k = sum(x >= t for x in real)
        lo, hi = wilson(k, len(real))
        rr = f"{100*k/len(real):.1f}% ({k}; {lo:.1f}-{hi:.1f})" if real else "-"
        fa = [100.0 * (ma[i] >= t) for i in common]
        fb = [100.0 * (mb[i] >= t) for i in common] if B else []
        hh = f"{100*sum(x >= t for x in hm)/len(hm):.1f}%" if hm else "-"
        row(f"{t}+", rr, hh, fa, fb, lambda v, s=False: (f"{v:+.2f}%" if s else f"{v:.2f}%"))
    rr = f"{st.mean(real):.1f}" if real else "-"
    row("mean margin", rr, f"{st.mean(hm):.1f}" if hm else "-", [float(ma[i]) for i in common], [float(mb[i]) for i in common] if B else [],
        lambda v, s=False: (f"{v:+.2f}" if s else f"{v:.2f}"))
    # Upsets and comebacks (bible principle 2: decisions move the odds, never the certainty).
    if common and "q_score" in A[common[0]]["teams"][0]:
        def stronger_won(R, i):
            t = R[i]["teams"]
            if t[0]["strength"] == t[1]["strength"] or t[0]["score"] == t[1]["score"]:
                return None
            return 100.0 * ((t[0]["strength"] > t[1]["strength"]) == (t[0]["score"] > t[1]["score"]))

        def cb(R, i, k):
            t = R[i]["teams"]
            return 100.0 * came_back(t[0]["q_score"], t[1]["q_score"], k)
        ids = [i for i in common if stronger_won(A, i) is not None and (not B or stronger_won(B, i) is not None)]
        fmt = lambda v, s=False: (f"{v:+.2f}%" if s else f"{v:.2f}%")
        row("stronger list wins", "-", "-", [stronger_won(A, i) for i in ids],
            [stronger_won(B, i) for i in ids] if B else [], fmt)
        for k in (18, 24, 30):
            hh = f"{100*sum(came_back(h, a, k) for h, a in hist)/len(hist):.1f}%" if hist else "-"
            row(f"winner {k}+ down at a break", "-", hh, [cb(A, i, k) for i in common],
                [cb(B, i, k) for i in common] if B else [], fmt)
    for name, R in (("A", ma), ("B", mb)):
        if not R:
            continue
        v = sorted(R.values())
        print(f"\n{name}: p90 {v[int(0.9*(len(v)-1))]}, p99 {v[int(0.99*(len(v)-1))]}, max {v[-1]}"
              + (f" (real 2026 p90 {sorted(real)[int(0.9*(len(real)-1))]}, max {max(real)}; 2010-25 p99 "
                 f"{sorted(hm)[int(0.99*(len(hm)-1))]}, max {max(hm)})" if real and hm and name == "A" else ""))
ROLES = ["DEF", "MID", "FWD", "RUCK"]
ROLE_REF = {"disposals": "disposals", "kicks": "kicks", "handballs": "handballs", "marks": "marks",
            "rebounds": "rebound_50s", "inside50": "inside_50s", "clearances": "clearances", "goals": "goals",
            "tackles": "tackles"}


def role_rate(r, role, key):
    """One match's per player-game rate for a line (both sides pooled), or None."""
    pg = sum(t.get("roles", {}).get(role, {}).get("pg", 0) for t in r["teams"])
    if pg == 0:
        return None
    return sum(t.get("roles", {}).get(role, {}).get(key, 0.0) for t in r["teams"]) / pg


def role_share(r, role):
    """One match's share of both sides' disposals that went to a line."""
    tot = sum(t.get("roles", {}).get(x, {}).get("disposals", 0.0) for t in r["teams"] for x in t.get("roles", {}))
    if tot == 0:
        return None
    return sum(t.get("roles", {}).get(role, {}).get("disposals", 0.0) for t in r["teams"]) / tot


def zone_share(R, zone, role):
    """Pooled share of a zone's carrier picks that went to a slot role."""
    n = d = 0
    for r in R.values():
        for t in r["teams"]:
            cz = t.get("carry_zone", {})
            n += cz.get(f"{zone}|{role}", 0)
            d += sum(v for k, v in cz.items() if k.startswith(zone + "|"))
    return None if d == 0 else n / d


def paired(A, B, fn):
    a = {i: fn(r) for i, r in A.items()}
    a = {i: v for i, v in a.items() if v is not None}
    if not B:
        return st.mean(a.values()), None, None, None
    b = {i: fn(r) for i, r in B.items()}
    common = [i for i in a if b.get(i) is not None]
    d = [b[i] - a[i] for i in common]
    se = st.stdev(d) / math.sqrt(len(d)) if len(d) > 1 else 0.0
    return st.mean(a.values()), st.mean(b[i] for i in common), st.mean(d), se


def reb_route_section(A, B):
    """Rebound 50s a team a game by how the ball left defensive 50 (MatchSim.rebound_log:
    a kick, a handball, or carried out through a broken tackle). No real reference:
    Champion Data does not publish the split. An arm whose checkout has no rebound_log
    (main before the D50 change) shows "-"."""
    routes = ("kick", "handball", "tackle")

    def per(r, k):
        ts = r["teams"]
        if not all("reb_route" in t for t in ts):
            return None
        if k == "all":
            return sum(t["reb_route"].get(x, 0) for t in ts for x in routes) / len(ts)
        return sum(t["reb_route"].get(k, 0) for t in ts) / len(ts)

    has = {n: bool(R) and any(per(r, "all") is not None for r in R.values()) for n, R in (("A", A), ("B", B))}
    if not (has["A"] or has["B"]):
        return
    both = has["A"] and has["B"]
    print("\n## Rebound 50s by exit route (a team a game; no real reference)\n")
    head = "| route | A | share A |" + (" B | share B |" if B else "") + (" B-A | se | sig |" if both else "")
    print(head)
    print("|" + "---|" * (head.count("|") - 1))
    mean = lambda R, k: st.mean(v for v in (per(r, k) for r in R.values()) if v is not None)
    for k in routes + ("all",):
        line = "| " + k + " |"
        for n, R in (("A", A), ("B", B)):
            if n == "B" and not B:
                continue
            line += f" {mean(R, k):.2f} | {100 * mean(R, k) / mean(R, 'all'):.0f}% |" if has[n] else " - | - |"
        if both:
            _, _, d, se = paired(A, B, lambda r, k=k: per(r, k))
            line += f" {d:+.2f} | {se:.2f} | {'yes' if se and abs(d) > 2 * se else ''} |"
        print(line)


def role_report(A, B):
    """Each line's box score per player-game against real 2026 (afl_role_rates.json, grouped by
    the player's own position as the game derives it) and its share of the side's disposals;
    then who takes the ball by zone (carrier picks by slot role, no real reference)."""
    if not any("roles" in t for r in A.values() for t in r["teams"]):
        return
    ref = json.load(open(os.path.join(HERE, "afl_role_rates.json")))["roles"]
    pooled = {x: ref[x]["per_game"]["disposals"] * ref[x]["player_games"] for x in ROLES}
    real_share = {x: pooled[x] / sum(pooled.values()) for x in ROLES}
    print("\n## By line, per player-game (real 2026: tools/balance/afl_role_rates.json)\n")
    head = "| line | stat | real | A |" + (" B | B-A | se | sig |" if B else "")
    print(head)
    print("|" + "---|" * (head.count("|") - 1))
    for role in ROLES:
        rows = [(k, ref[role]["per_game"][ROLE_REF[k]], lambda r, k=k, role=role: role_rate(r, role, k)) for k in ROLE_REF]
        rows.append(("share of disposals", real_share[role], lambda r, role=role: role_share(r, role)))
        for k, real_v, fn in rows:
            ma, mb, dm, se = paired(A, B, fn)
            pct = k.startswith("share")
            f = (lambda v: f"{100*v:.1f}%") if pct else (lambda v: f"{v:.2f}")
            line = f"| {role} | {k} | {f(real_v)} | {f(ma)} |"
            if B:
                sig = "yes" if se and abs(dm) > 2 * se else ""
                line += f" {f(mb)} | {(100*dm if pct else dm):+.2f}{'pp' if pct else ''} | {(100*se if pct else se):.2f} | {sig} |"
            print(line)
    print("\nReal share of disposals pools 2026 player-games by line (DEF %.1f%% of player-games)." %
          (100 * ref["DEF"]["player_games"] / sum(ref[x]["player_games"] for x in ROLES)))
    print("\n## Who takes the ball, by zone (share of carrier picks by slot role; no real reference)\n")
    zones = ["back", "middle", "attack", "inside"]
    head = "| zone | " + " | ".join(f"{x} A" + (f" | {x} B" if B else "") for x in ROLES) + " |"
    print(head)
    print("|" + "---|" * (head.count("|") - 1))
    for z in zones:
        cells = []
        for x in ROLES:
            a = zone_share(A, z, x)
            cells.append("-" if a is None else f"{100*a:.1f}%")
            if B:
                b = zone_share(B, z, x)
                cells.append("-" if b is None else f"{100*b:.1f}%")
        print(f"| {z} | " + " | ".join(cells) + " |")


TYPE_STATS = ["disposals", "kicks", "handballs", "marks", "rebounds", "kick_ins"]
TOP_TYPES = ["Key defender"]
SEASON_GAMES = 23


def type_report(A, B):
    """Disposals a player-game by each man's type as the game names it (Roles.label), against
    real 2026 (afl_role_rates.json "types": IN = inside the 18 clubs' lowest..highest pooled rate
    for that type, NEAR = within the mean +-2 sd, else OUT); then the top key defenders by
    disposals a game over the run, as a SEASON_GAMES-game season."""
    if not any("types" in t for r in A.values() for t in r["teams"]):
        # Arm A's checkout (main, before this harness logged types) has none: show B alone.
        if B and any("types" in t for r in B.values() for t in r["teams"]):
            print("\n(Arm A's checkout does not log types; the by-type table below is arm B alone.)")
            type_report(B, None)
        return
    ref = json.load(open(os.path.join(HERE, "afl_role_rates.json"))).get("types", {})
    names = sorted({k for r in A.values() for t in r["teams"] for k in t.get("types", {}) if k != "pl"},
                   key=lambda k: -ref.get(k, {}).get("player_games", 0))

    def rate(r, ty, k):
        pg = sum(t.get("types", {}).get(ty, {}).get("pg", 0) for t in r["teams"])
        return None if pg == 0 else sum(t.get("types", {}).get(ty, {}).get(k, 0.0) for t in r["teams"]) / pg
    print("\n## By type, per player-game (real 2026: afl_role_rates.json types; Roles.label)\n")
    head = "| type | real di | clubs range | A di | mark | A kicks | A hb | A marks | A reb50 | A kick-ins |" \
        + (" B di | mark | B-A | se | sig |" if B else "")
    print(head)
    print("|" + "---|" * (head.count("|") - 1))
    for ty in names:
        rr = ref.get(ty)
        ma, mb, dm, se = paired(A, B, lambda r, ty=ty: rate(r, ty, "disposals"))
        def mark(v, rr=rr):
            if not rr:
                return "-"
            c = rr["disposals_clubs"]
            return "IN" if c["min"] <= v <= c["max"] else                 ("NEAR" if abs(v - rr["per_game"]["disposals"]) <= 2 * c["sd"] else "OUT")
        if rr:
            c = rr["disposals_clubs"]
            real = rr["per_game"]["disposals"]
            line = f"| {ty} | {real:.2f} | {c['min']:.1f}-{c['max']:.1f} | {ma:.2f} | {mark(ma)} |"
        else:
            line = f"| {ty} | - | - | {ma:.2f} | - |"
        for k in TYPE_STATS[1:]:
            v = [x for x in (rate(r, ty, k) for r in A.values()) if x is not None]
            line += f" {st.mean(v):.2f} |"
        if B:
            sig = "yes" if se and abs(dm) > 2 * se else ""
            line += f" {mb:.2f} | {mark(mb)} | {dm:+.2f} | {se:.2f} | {sig} |"
        print(line)
    for arm, R in (("A", A), ("B", B)):
        if not R or not any("type_src" in t for r in R.values() for t in r["teams"]):
            continue
        rx_all = sum(t.get("type_src", {}).get(ty, {}).get("rx", 0)
                     for r in R.values() for t in r["teams"] for ty in names)
        print(f"\n## Where each type's disposals happen (run {arm}, event log: share by zone from his side's view,"
              " share that were his first touch after his own rebound 50, and who takes the ball straight after"
              " a rebound 50: a game, share of all, and where he takes it; then his touches a game anywhere"
              " later in a chain that had a rebound 50, all and by zone; no real reference)\n")
        print("| type | per game (events) | back | middle | attack | inside | after own reb50 |"
              " takes the exit (a game) | share of exits | exit taken back | middle | attack |"
              " after a reb50 (a game) | back | middle | attack | inside |")
        print("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for ty in names:
            tot = {}
            pg = 0
            for r in R.values():
                for t in r["teams"]:
                    pg += t.get("types", {}).get(ty, {}).get("pg", 0)
                    for k, v in t.get("type_src", {}).get(ty, {}).items():
                        tot[k] = tot.get(k, 0) + v
            ev = tot.get("ev", 0)
            if not ev or not pg:
                continue
            cells = " | ".join(f"{100*tot.get(z, 0)/ev:.0f}%" for z in ["back", "middle", "attack", "inside", "reb"])
            rx = tot.get("rx", 0)
            rxc = " | ".join(f"{100*tot.get('rx_' + z, 0)/rx:.0f}%" if rx else "-" for z in ["back", "middle", "attack"])
            print(f"| {ty} | {ev/pg:.2f} | {cells} | {rx/pg:.2f} | "
                  f"{(100*rx/rx_all) if rx_all else 0:.0f}% | {rxc} | {tot.get('px', 0)/pg:.2f} | "
                  + " | ".join(f"{tot.get('px_' + z, 0)/pg:.2f}" for z in ["back", "middle", "attack", "inside"]) + " |")
    for ty in TOP_TYPES:
        acc = {}
        for r in A.values():
            for t in r["teams"]:
                for row in t.get("types", {}).get("pl", []):
                    if row[1] != ty:
                        continue
                    a = acc.setdefault(row[0], [0] * 7)
                    a[0] += 1
                    for j in range(6):
                        a[j + 1] += row[2 + j]
        real = {}
        try:
            with open(os.path.join(HERE, "..", "..", "data", "players_2026.csv"), encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    real[f"{row['club']}_{row['num']}"] = row
        except OSError:
            pass
        # Men who played at least a quarter of the run's games for their club.
        need = max(1, len(A) * 2 // 18 // 4)
        top = sorted(((k, v) for k, v in acc.items() if v[0] >= need), key=lambda kv: -kv[1][1] / kv[1][0])[:10]
        print(f"\n## Top 10 by disposals a game, {ty} (run A), as a {SEASON_GAMES}-game season\n")
        print("| # | player | games | di/g | season di | real 2026 di/g | kicks/g | hb/g | marks/g | reb50/g | kick-ins/g |")
        print("|---|---|---|---|---|---|---|---|---|---|---|")
        for n, (pid, a) in enumerate(top, 1):
            g = a[0]
            rw = real.get(pid)
            nm = f"{rw['first']} {rw['last']} ({pid})" if rw else pid
            rdi = f"{int(rw['di'])/int(rw['gm']):.1f} ({rw['gm']} gm)" if rw and int(rw["gm"] or 0) > 0 else "-"
            print(f"| {n} | {nm} | {g} | {a[1]/g:.1f} | {SEASON_GAMES*a[1]/g:.0f} | {rdi} | {a[2]/g:.1f} | {a[3]/g:.1f} |"
                  f" {a[4]/g:.1f} | {a[5]/g:.1f} | {a[6]/g:.1f} |")


# Champion Data 2025 (Wheelo), intercepts a game per player by position
# (docs/research/INTERCEPT_EVIDENCE.md; tools/audit/intercept_impl.gd REAL).
ROLE_REAL = {"DEF": 4.9, "MID": 2.5, "FWD": 1.1, "RUCK": 2.2}


def ic_role_rate(rows, role):
    """Seed -> intercepts per player-game for one role (both teams pooled)."""
    out = {}
    for i, r in rows.items():
        ic = sum(float(t.get("ic_" + role, 0)) for t in r["teams"])
        pg = sum(float(t.get("pg_" + role, 0)) for t in r["teams"])
        if pg > 0:
            out[i] = (ic, pg)
    return out


def role_table(A, B):
    """Intercepts a game per player by listed position, against Champion Data."""
    if not any("pg_MID" in t for r in A.values() for t in r["teams"]):
        return
    print("\nIntercepts a game per player, by listed position (Champion Data 2025):\n")
    head = "| role | real | A | share A |" + (" B | share B | B-A | se | sig |" if B else "")
    print(head)
    print("|" + "---|" * (head.count("|") - 1))
    tot = {}
    for arm, R in (("A", A), ("B", B)):
        tot[arm] = sum(float(t.get("intercepts", 0)) for r in R.values() for t in r["teams"]) or 1.0
    for role, real in ROLE_REAL.items():
        a = ic_role_rate(A, role)
        if not a:
            continue
        ra = sum(v[0] for v in a.values()) / sum(v[1] for v in a.values())
        sa = 100 * sum(v[0] for v in a.values()) / tot["A"]
        line = f"| {role} | {real:.1f} | {ra:.2f} | {sa:.0f}% |"
        if B:
            b = ic_role_rate(B, role)
            common = [i for i in a if i in b]
            rb = sum(b[i][0] for i in common) / sum(b[i][1] for i in common)
            sb = 100 * sum(b[i][0] for i in common) / tot["B"]
            d = [b[i][0] / b[i][1] - a[i][0] / a[i][1] for i in common]
            se = st.stdev(d) / math.sqrt(len(d)) if len(d) > 1 else 0.0
            sig = "yes" if se > 0 and abs(st.mean(d)) > 2 * se else ""
            line += f" {rb:.2f} | {sb:.0f}% | {rb - ra:+.2f} | {se:.2f} | {sig} |"
        print(line)
    print("\nReal shares (Champion Data 2025): DEF 57%, MID 23%, FWD 15%, RUCK 4%; a team intercepts about 63.4 a game.")


def spoil_zone_rate(rows, keys):
    """Seed -> spoils a team-match in the zone keys (from each team's spoil_zone)."""
    return {i: sum(float(t.get("spoil_zone", {}).get(k, 0)) for t in r["teams"] for k in keys) / 2
            for i, r in rows.items()}


def spoils_section(A, B):
    """Spoils a team a game by zone and by listed position (T2.29, TODO row 11), against
    Champion Data 2026 (afl_spoil_zones.json; the zone split is an estimate, see its source)."""
    if not any("spoil_zone" in t for r in A.values() for t in r["teams"]):
        return
    ref = json.load(open(os.path.join(HERE, "afl_spoil_zones.json")))
    real = ref["per_team_match"]

    def mark(v, b):
        if b["lo"] <= v <= b["hi"]:
            return "IN"
        return "NEAR" if abs(v - b["mean"]) <= 2 * b["sd"] else "OUT"
    print("\n\n## Spoils a team a game, by zone (spoiling side's end; real zones are an estimate)\n")
    head = "| zone | AFL mean | AFL range | A | A/real | mark |" + (" B | mark | B-A | se | sig |" if B else "")
    print(head)
    print("|" + "---|" * (head.count("|") - 1))
    rows = [("total", ["d50_entry", "d50_play", "mid", "f50"], "total"),
            ("d50 (all)", ["d50_entry", "d50_play"], "d50"),
            ("  d50: entries and packs", ["d50_entry"], None),
            ("  d50: general play", ["d50_play"], None),
            ("mid (between the arcs)", ["mid"], "mid"),
            ("f50 (own forward 50)", ["f50"], "f50"),
            ("outside d50 (mid + f50)", ["mid", "f50"], None)]
    for label, keys, rk in rows:
        a = spoil_zone_rate(A, keys)
        ma = st.mean(a.values())
        b0 = real.get(rk) if rk else None
        if rk is None and keys == ["mid", "f50"]:
            b0 = {"mean": real["mid"]["mean"] + real["f50"]["mean"], "lo": real["mid"]["lo"] + real["f50"]["lo"],
                  "hi": real["mid"]["hi"] + real["f50"]["hi"], "sd": math.hypot(real["mid"]["sd"], real["f50"]["sd"])}
        line = (f"| {label} | {b0['mean']:.1f} | {b0['lo']:.1f}-{b0['hi']:.1f} | {ma:.1f} | {ma / b0['mean']:.2f} | {mark(ma, b0)} |"
                if b0 else f"| {label} | - | - | {ma:.1f} | - | - |")
        if B:
            b = spoil_zone_rate(B, keys)
            common = [i for i in a if i in b]
            d = [b[i] - a[i] for i in common]
            mb = st.mean(b[i] for i in common)
            se = st.stdev(d) / math.sqrt(len(d)) if len(d) > 1 else 0.0
            sig = "yes" if se > 0 and abs(st.mean(d)) > 2 * se else ""
            line += f" {mb:.1f} | {mark(mb, b0) if b0 else '-'} | {st.mean(d):+.2f} | {se:.2f} | {sig} |"
        print(line)
    print("\nSpoils a game per player, by listed position (measured, Champion Data 2026):\n")
    print("| role | real | A | real share | share A |")
    print("|---|---|---|---|---|")
    tot = sum(float(t.get("sp_" + r_, 0)) for r in A.values() for t in r["teams"] for r_ in ref["by_role"]) or 1.0
    for role, rr in ref["by_role"].items():
        sp = sum(float(t.get("sp_" + role, 0)) for r in A.values() for t in r["teams"])
        pg = sum(float(t.get("pg_" + role, 0)) for r in A.values() for t in r["teams"])
        if pg <= 0:
            continue
        print(f"| {role} | {rr['per_player_game']:.2f} | {sp / pg:.2f} | {100 * rr['share']:.0f}% | {100 * sp / tot:.0f}% |")
    print(f"\nReal: {ref['source']}")


def weather_section(A, B, cond):
    """Paired change in percent (B / A - 1), plus accuracy in points, the last
    quarter's share of the scoring and the breeze split (row 61). The real column
    shows only when B is a weather arm (cond = wet, windy or hot) and A is not, so no
    other screen is read against it; each row is then marked IN/NEAR/OUT by
    weather_mark."""
    if not B:
        return
    common = [i for i in A if i in B]
    if not common:
        return
    ref = weather_ref() if cond else None
    col = ref["change_vs_perfect"][cond] if ref else None
    real = col is not None
    print("\n## Change B against A, percent" + (f" (real column: {cond} against a perfect day, "
          "AFL 2016-25, afl_weather_rates.json)" if real else "") + "\n")
    print("| stat | A | B | B/A-1 | se |" + (" real | se | mark |" if real else ""))
    print("|---|---|---|---|---|" + ("---|---|---|" if real else ""))
    for k, rk in WEATHER_KEYS.items():
        a = per_match(A, k)
        b = per_match(B, k)
        ma = st.mean(a[i] for i in common)
        if ma == 0:
            continue
        mb = st.mean(b[i] for i in common)
        d = [(b[i] - a[i]) / ma for i in common]
        se = st.stdev(d) / math.sqrt(len(d)) if len(d) > 1 else 0.0
        line = f"| {k} | {ma:.1f} | {mb:.1f} | {100 * (mb / ma - 1):+.1f}% | {100 * se:.1f}% |"
        if real:
            rv = col.get(rk) if rk else None
            if rv is None and cond == "wet" and k in REAL_WET_ABC:
                rv = {"change": REAL_WET_ABC[k][0], "se": REAL_WET_ABC[k][1]}
            if rv is None:
                line += " - | - | - |"
            else:
                line += (f" {100 * rv['change']:+.1f}% | {100 * rv['se']:.1f}% |"
                         f" {weather_mark(mb / ma - 1, se, rv['change'], rv['se'])} |")
        print(line)

    def counts(rows, ids, g, n):
        """Goals (g) and their base over both teams of the matches in ids: shots of
        that kind (n), or goals and behinds when n is None."""
        gg = sum(float(t.get(g, 0)) for i in ids for t in rows[i]["teams"])
        nn = sum(float(t.get(n or "behinds", 0)) for i in ids for t in rows[i]["teams"])
        return gg, (nn + gg if n is None else nn)

    def ratio(rows, ids, g, n):
        gg, nn = counts(rows, ids, g, n)
        return 100 * gg / nn if nn else None
    # The set-shot and general-play rows (balance_body's sshot_* and gshot_*) have no
    # real weather column: the reference counts goals and behinds, not shots by kind.
    for label, g, n, rkey in (("accuracy, goals per scoring shot (points)", "goals", None, "accuracy"),
                              ("set-shot goals per set shot (points)", "sshot_g", "sshot_n", None),
                              ("general-play goals per logged shot (points)", "gshot_g", "gshot_n", None)):
        if n is not None and not any(n in t for i in common for t in A[i]["teams"]):
            continue
        fa = {i: ratio(A, [i], g, n) for i in common}
        fb = {i: ratio(B, [i], g, n) for i in common}
        d = [fb[i] - fa[i] for i in common if fa[i] is not None and fb[i] is not None]
        m, se = _mse(d)
        pa, pb = ratio(A, common, g, n) or 0.0, ratio(B, common, g, n) or 0.0
        line = f"| {label} | {pa:.1f} | {pb:.1f} | {m:+.1f} pts | {se:.1f} |"
        if real and rkey and rkey in col:
            rv = col[rkey]
            line += f" {rv['change_points']:+.1f} pts | {rv['se']:.1f} | {weather_mark(m, se, rv['change_points'], rv['se'])} |"
        elif real:
            line += " - | - | - |"
        print(line)
    if "q_score" not in A[common[0]]["teams"][0]:
        return
    qa = {i: q4_share(A[i]) for i in common}
    qb = {i: q4_share(B[i]) for i in common}
    d = [qb[i] - qa[i] for i in common if qa[i] is not None and qb[i] is not None]
    m, se = _mse(d)
    line = (f"| last quarter's share of the scoring (points) | {st.mean(v for v in qa.values() if v is not None):.1f}% | "
            f"{st.mean(v for v in qb.values() if v is not None):.1f}% | {m:+.2f} pts | {se:.2f} |")
    if real:
        rv = col["q4_share"]
        line += f" {rv['change_points']:+.2f} pts | {rv['se']:.2f} | {weather_mark(m, se, rv['change_points'], rv['se'])} |"
    print(line)
    sa = [odd_even(A[i]) for i in common]
    sb = [odd_even(B[i]) for i in common]
    bz, bse = breeze_size(sa, sb)
    line = (f"| breeze, margin points a quarter to the side kicking with it | sd {st.stdev(sa):.1f} | "
            f"sd {st.stdev(sb):.1f} | {bz:.2f} | {bse:.2f} |")
    if real:
        rv = col["breeze"]
        line += f" {rv['points_a_quarter']:.2f} | {rv['se']:.2f} | {weather_mark(bz, bse, rv['points_a_quarter'], rv['se'])} |"
    print(line)


def _mse(d):
    d = list(d)
    if not d:
        return 0.0, 0.0
    return st.mean(d), (st.stdev(d) / math.sqrt(len(d)) if len(d) > 1 else 0.0)


def _fmt(d):
    m, se = _mse(d)
    sig = " *" if se > 0 and abs(m) > 2 * se else ""
    return f"{m:+.2f} ({se:.2f}){sig}"


LEGS_ROWS = ([("legs at Q%d siren" % (q + 1), "legs_q", q) for q in range(4)]
             + [("under 40 at Q%d siren" % (q + 1), "tank_q", q) for q in range(4)]
             + [("interchanges", "interchanges", None), ("exertion", "exertion", None)])


def _lv(t, key, q):
    v = t.get(key)
    if v is None:
        return None
    return float(v[q]) if q is not None else float(v)


def legs_section(A, B):
    """Fatigue parity (T3.F-defects): each side's legs by venue and, under
    --setup coached, your coached side against the rival; a paired run also
    gives the coached side and the rival each against the same side, same seed, in A."""
    if not any("legs_q" in t for r in A.values() for t in r["teams"]):
        return
    print("\n## Legs (fatigue parity)\n")
    print("Legs: mean energy (0-100) of the 18 on the ground. Under 40: how many of them (fit 0.90 or less)."
          " Exertion: energy spent on the ground, whole side. Differences are per match, mean (se); * past 2 se.\n")
    for name, R in (("A", A), ("B", B)):
        if not R:
            continue
        coached = any(t.get("coached") for r in R.values() for t in r["teams"])
        head = f"| {name} | home | away | home-away |" + (" coached | rival | coached-rival |" if coached else "")
        print(head)
        print("|" + "---|" * (head.count("|") - 1))
        for label, key, q in LEGS_ROWS:
            rows = [r for r in R.values() if _lv(r["teams"][0], key, q) is not None]
            if not rows:
                continue
            h = [_lv(r["teams"][0], key, q) for r in rows]
            a = [_lv(r["teams"][1], key, q) for r in rows]
            line = f"| {label} | {st.mean(h):.2f} | {st.mean(a):.2f} | {_fmt(x - y for x, y in zip(h, a))} |"
            if coached:
                c = [_lv(t, key, q) for r in rows for t in r["teams"] if t.get("coached")]
                o = [_lv(t, key, q) for r in rows for t in r["teams"] if not t.get("coached")]
                line += f" {st.mean(c):.2f} | {st.mean(o):.2f} | {_fmt(x - y for x, y in zip(c, o))} |"
            print(line)
        print()
    if B and any(t.get("coached") for r in B.values() for t in r["teams"]):
        print("Same team, same seed, B against A: the side coached in B, and its rival.\n")
        print("| stat | coached B-A | rival B-A | (coached - rival) B-A |")
        print("|---|---|---|---|")
        for label, key, q in LEGS_ROWS:
            dc, dr, dd = [], [], []
            for i, rb in B.items():
                ra = A.get(i)
                if ra is None:
                    continue
                cs = [s for s in range(2) if rb["teams"][s].get("coached")]
                if not cs or _lv(ra["teams"][0], key, q) is None:
                    continue
                c = cs[0]
                x = _lv(rb["teams"][c], key, q) - _lv(ra["teams"][c], key, q)
                y = _lv(rb["teams"][1 - c], key, q) - _lv(ra["teams"][1 - c], key, q)
                dc.append(x)
                dr.append(y)
                dd.append(x - y)
            if dc:
                print(f"| {label} | {_fmt(dc)} | {_fmt(dr)} | {_fmt(dd)} |")


# Ruck integrity (T2.31): hit-outs per team and per number-one ruck, hit-outs to
# advantage, the club spread and the match duel spread, against Champion Data 2025 and
# 2026 (afl_ruck_rates.json, built by build_ruck_rates.py from the Wheelo cache).
RUCK_DUEL = (10, 20, 30)


def _ratio(num, den):
    def f(r):
        d = sum(den(t) for t in r["teams"])
        return None if d == 0 else 100 * sum(num(t) for t in r["teams"]) / d
    return f


RUCK_ROWS = [
    ("team hit-outs", "team_hitouts", lambda r: sum(float(t.get("hitouts", 0)) for t in r["teams"]) / 2, ""),
    ("team hit-outs to advantage", "team_hta", lambda r: sum(float(t.get("hitouts_adv", 0)) for t in r["teams"]) / 2, ""),
    ("to advantage, % of hit-outs", "team_hta_pct",
     _ratio(lambda t: float(t.get("hitouts_adv", 0)), lambda t: float(t.get("hitouts", 0))), "%"),
    ("number-one ruck: hit-outs", "ruck1_hitouts", lambda r: sum(t["ruck1"][0] for t in r["teams"]) / 2, ""),
    ("number-one ruck: to advantage", "ruck1_hta", lambda r: sum(t["ruck1"][1] for t in r["teams"]) / 2, ""),
    ("number-one ruck: to advantage %", "ruck1_hta_pct", _ratio(lambda t: t["ruck1"][1], lambda t: t["ruck1"][0]), "%"),
    ("number-one ruck: share of team hit-outs", "ruck1_share",
     _ratio(lambda t: t["ruck1"][0], lambda t: float(t.get("hitouts", 0))), "%"),
    ("number-one ruck: ruck contests*", "ruck1_contests", lambda r: sum(t["ruck1"][2] for t in r["teams"]) / 2, ""),
    ("number-one ruck: hit-outs per ruck contest*", "ruck1_win_pct",
     _ratio(lambda t: t["ruck1"][0], lambda t: t["ruck1"][2]), "%"),
]


def _mark(v, rr):
    if rr["min"] <= v <= rr["max"]:
        return "IN"
    return "NEAR" if abs(v - rr["mean"]) <= 2 * rr["sd"] else "OUT"


def ruck_section(A, B):
    if not any("ruck1" in t for r in A.values() for t in r["teams"]):
        return
    path = os.path.join(HERE, "afl_ruck_rates.json")
    if not os.path.exists(path):
        return
    ref = json.load(open(path, encoding="utf-8"))
    r26, r25 = ref["2026"]["league"], ref["2025"]["league"]
    print("\n## Rucks (T2.31; real: Champion Data via Wheelo, tools/balance/afl_ruck_rates.json)\n")
    print("Number-one ruck: the side's man with the most hit-outs in the match (real: the club's listed ruck with "
          "the most season hit-outs, per game he played). Mark against 2026's 18 clubs: IN inside lowest..highest, "
          "NEAR within mean +-2 sd, OUT.\n")
    head = "| per team-match | real 2026 mean | 2026 range | real 2025 mean | A | mark |" + (" B | B-A | se | sig |" if B else "")
    print(head)
    print("|" + "---|" * (head.count("|") - 1))
    for label, key, fn, unit in RUCK_ROWS:
        ma, mb, dm, se = paired(A, B, fn)
        rr = r26[key]
        line = (f"| {label} | {rr['mean']:.1f}{unit} | {rr['min']:.1f}-{rr['max']:.1f} | {r25[key]['mean']:.1f}{unit} |"
                f" {ma:.1f}{unit} | {_mark(ma, rr)} |")
        if B:
            sig = "yes" if se and abs(dm) > 2 * se else ""
            line += f" {mb:.1f}{unit} | {dm:+.2f} | {se:.2f} | {sig} |"
        print(line)
    print("\n*The sim counts a ruck contest only when someone wins the tap, so its hit-outs per contest is the"
          " share of won taps (the two rucks sum to 100%); real ruck contests include taps nobody wins."
          " Read those two rows' marks with this in mind.")
    ruck_clubs(A, B, ref)
    ruck_duels(A, B)


def ruck_clubs(A, B, ref):
    """Feast or famine at club level: each club's sim average against the real 18 clubs' spread."""
    r26 = ref["2026"]["league"]
    names = {}
    with open(os.path.join(ROOT, "data", "clubs.csv"), encoding="utf-8") as f:
        for line in f.read().splitlines()[1:]:
            c = line.split(",")
            names[c[1]] = c[0]
    real_club = {names.get(k, k): v for k, v in ref["2026"]["clubs"].items()}
    for name, R in (("A", A), ("B", B)):
        if not R:
            continue
        acc = {}
        for r in R.values():
            for t in r["teams"]:
                c = acc.setdefault(t.get("club", "?"), [0, 0.0, 0, 0, 0])
                c[0] += 1
                c[1] += float(t.get("hitouts", 0))
                c[2] += t["ruck1"][0]
                c[3] += t["ruck1"][2]
                c[4] += t["ruck1"][3]
        club = {k: {"team_hitouts": v[1] / v[0], "ruck1_hitouts": v[2] / v[0],
                    "ruck1_win_pct": 100 * v[2] / max(1, v[3]), "rating": v[4] / v[0]} for k, v in acc.items()}
        common = [k for k in club if k in real_club]
        print(f"\n### Club spread, arm {name} (each club over {min(acc[k][0] for k in common)}+ team-matches)\n")
        print("| club average | real lowest | real highest | real sd | sim lowest | sim highest | sim sd | r with real club |")
        print("|---|---|---|---|---|---|---|---|")
        for key, label in (("team_hitouts", "team hit-outs"), ("ruck1_hitouts", "number-one ruck hit-outs"),
                           ("ruck1_win_pct", "number-one ruck hit-outs per contest*")):
            v = [club[k][key] for k in common]
            rv = [real_club[k][key] for k in common]
            rr = r26[key]
            corr = st.correlation(v, rv) if len(v) > 2 and st.pstdev(v) > 0 else float("nan")
            print(f"| {label} | {rr['min']:.1f} | {rr['max']:.1f} | {rr['sd']:.2f} | {min(v):.1f} | {max(v):.1f} |"
                  f" {st.pstdev(v):.2f} | {corr:+.2f} |")
        if name == "A":
            print("\n| club | sim no.1 ruck rating | sim team hit-outs | real 2026 | sim no.1 ruck | real no.1 ruck |")
            print("|---|---|---|---|---|---|")
            for k in sorted(common, key=lambda k: -club[k]["team_hitouts"]):
                rc = real_club[k]
                print(f"| {k} | {club[k]['rating']:.0f} | {club[k]['team_hitouts']:.1f} | {rc['team_hitouts']:.1f} |"
                      f" {club[k]['ruck1_hitouts']:.1f} | {rc['ruck1_hitouts']:.1f} ({rc['ruck1']}) |")


def ruck_duels(A, B):
    """How often one side wins the match's hit-outs by a big margin (sim only)."""
    arms = [R for R in (A, B) if R]
    print("\n### Duel spread per match (no real per-match reference in the repo)\n")
    head = "| per match | A |" + (" B |" if B else "")
    print(head)
    print("|" + "---|" * (head.count("|") - 1))

    def tm(r):
        return abs(float(r["teams"][0].get("hitouts", 0)) - float(r["teams"][1].get("hitouts", 0)))

    def rm(r):
        return abs(r["teams"][0]["ruck1"][0] - r["teams"][1]["ruck1"][0])

    def top(r):
        h = [float(t.get("hitouts", 0)) for t in r["teams"]]
        return max(h) / sum(h) if sum(h) else 0.5

    def share(R, test):
        return 100 * sum(test(r) for r in R.values()) / len(R)
    print("| mean team hit-out margin |" + "".join(f" {st.mean(tm(r) for r in R.values()):.1f} |" for R in arms))
    for k in RUCK_DUEL:
        print(f"| team hit-out margin {k}+ |" + "".join(f" {share(R, lambda r: tm(r) >= k):.1f}% |" for R in arms))
    for k in RUCK_DUEL[:2]:
        print(f"| number-one rucks {k}+ hit-outs apart |" + "".join(f" {share(R, lambda r: rm(r) >= k):.1f}% |" for R in arms))
    for s in (0.60, 0.65, 0.70):
        print(f"| one side wins {100 * s:.0f}%+ of the match's hit-outs |"
              + "".join(f" {share(R, lambda r: top(r) >= s):.1f}% |" for R in arms))
    print("\nReal per-match hit-out splits are not in the repo; the club spread above is the sourced check.")


BLOCK = 22      # per-player rates are taken over 22-game blocks of the run, as a season is
MIN_BLOCK = 12  # a block counts with 12+ games, as the real reference counts 12+ game seasons


def _q(v, q):
    s = sorted(v)
    if not s:
        return 0.0
    i = q * (len(s) - 1)
    lo = int(i)
    hi = min(len(s) - 1, lo + 1)
    return s[lo] + (s[hi] - s[lo]) * (i - lo)


def _block_seasons(R, idx):
    """Per-player rate of stat idx (0 tackles, 1 pressure acts) over 22-game blocks, in seed order,
    grouped as seasons: block k of every man is season k, so each season holds about as many men
    as a real one (about 420 with 12+ games) and its max and tail compare like for like. Returns
    [{role: [rates], "ALL": [...]}], one per season, leaving out a last season with under 80% of
    the men of the fullest."""
    games = {}
    for i in sorted(R):
        for t in R[i]["teams"]:
            for pid, v in t.get("tp", {}).items():
                games.setdefault(pid, [v[2], []])[1].append(v[idx])
    seasons = []
    for role, g in games.values():
        for b, k in enumerate(range(0, len(g), BLOCK)):
            blk = g[k:k + BLOCK]
            if len(blk) >= MIN_BLOCK:
                while len(seasons) <= b:
                    seasons.append({"ALL": []})
                r = sum(blk) / len(blk)
                seasons[b]["ALL"].append(r)
                seasons[b].setdefault(role, []).append(r)
    full = max((len(x["ALL"]) for x in seasons), default=0)
    return [x for x in seasons if len(x["ALL"]) >= 0.8 * full]


def _season_q(seasons, role, q, qv):
    """The mean over the run's seasons of one quantile of one line."""
    v = [(max(x[role]) if q == "max" else _q(x[role], qv)) for x in seasons if x.get(role)]
    return st.mean(v) if v else 0.0


def _range_mark(v, rr):
    """IN inside the real seasons' lowest..highest; NEAR within mean +-2 sd; OUT (as _mark)."""
    return _mark(v, rr)


def _tops(R):
    return [max((v[0] for v in t.get("tp", {}).values()), default=0) for r in R.values() for t in r["teams"]]


def _pgs(R):
    return [v[0] for r in R.values() for t in r["teams"] for v in t.get("tp", {}).values()]


def tackle_section(A, B):
    """How tackles and pressure acts are spread over the players (Brownlow realism, 2026-11-08):
    per-player rates a game by line against real 2025-26, and each side's top tackler a match
    against real 2023-25 match lines (tools/balance/afl_brownlow.json)."""
    if not any("tp" in t for r in A.values() for t in r["teams"]):
        return
    path = os.path.join(HERE, "afl_brownlow.json")
    if not os.path.exists(path):
        return
    ref = json.load(open(path, encoding="utf-8"))
    pool = ref["pooled"]
    print("\n## Tackles and pressure acts per player (real: tools/balance/afl_brownlow.json)\n")
    sa_, sb_ = _block_seasons(A, 0), (_block_seasons(B, 0) if B else [])
    print(f"Per player a game over 22-game blocks of the run (a block counts with 12+ games), by listed line;"
          f" block k of every man makes season k ({len(sa_)} seasons in A"
          + (f", {len(sb_)} in B" if B else "") + f", about {st.mean(len(x['ALL']) for x in sa_):.0f} men each),"
          " and each figure is the mean over those seasons. Real: every player with 12+ games, ALL 2021-26"
          " (AFL Tables), by line 2025-26 (Champion Data positions and pressure acts via Wheelo)."
          " IN inside the real seasons' range, NEAR within mean +-2 sd, OUT.\n")
    head = "| stat | line | quantile | real range | A | mark |" + (" B | mark | B-A |" if B else "")
    print(head)
    print("|" + "---|" * (head.count("|") - 1))
    for label, idx, key in (("tackles", 0, "tackles_pg_by_role"), ("pressure acts", 1, "pressure_acts_pg_by_role")):
        ra = _block_seasons(A, idx)
        rb = _block_seasons(B, idx) if B else []
        for role in ("ALL", "MID", "FWD", "DEF", "RUCK"):
            for q, qv in (("max", 1.0), ("p99", 0.99), ("p90", 0.90), ("p50", 0.50)):
                rr = pool[key][role][q]
                va = _season_q(ra, role, q, qv)
                line = f"| {label} | {role} | {q} | {rr['min']:.2f}-{rr['max']:.2f} | {va:.2f} | {_range_mark(va, rr)} |"
                if B:
                    vb = _season_q(rb, role, q, qv)
                    line += f" {vb:.2f} | {_range_mark(vb, rr)} | {vb - va:+.2f} |"
                print(line)
    seasons = ref["matches"].get("by_season", {})
    if not seasons:
        return
    print("\nEach side's top tackler a match, and tackles per player-game (real: every 2023-25 home-and-away"
          " match line, players with 50%+ game time).\n")
    head = "| per match | real 2023-25 range | A | mark |" + (" B | mark | B-A |" if B else "")
    print(head)
    print("|" + "---|" * (head.count("|") - 1))
    rows = (("top tackler, mean", "top_tackler_mean", lambda R: st.mean(_tops(R))),
            ("top tackler, p90", "top_tackler_p90", lambda R: _q(_tops(R), 0.9)),
            ("top tackler, max", "top_tackler_max", lambda R: max(_tops(R))),
            ("player-game, p90", "player_game_p90", lambda R: _q(_pgs(R), 0.9)),
            ("player-game, p99", "player_game_p99", lambda R: _q(_pgs(R), 0.99)))
    for label, k, fn in rows:
        v = [float(x[k]) for x in seasons.values()]
        rr = {"min": min(v), "max": max(v), "mean": st.mean(v), "sd": st.pstdev(v)}
        va = fn(A)
        line = f"| {label} | {rr['min']:.2f}-{rr['max']:.2f} | {va:.2f} | {_range_mark(va, rr)} |"
        if B:
            vb = fn(B)
            line += f" {vb:.2f} | {_range_mark(vb, rr)} | {vb - va:+.2f} |"
        print(line)
    print("\nThe sim's player-game counts every man who played; the real one counts men with 50%+ game time.")


def familiarity_section(A, B):
    """--arrivals N: the carrying side's margin, B-A on the same seeds, per Round 1-6."""
    def carried(r):
        for s, t in enumerate(r["teams"]):
            if t.get("fam_carry"):
                return t, t["score"] - r["teams"][1 - s]["score"]
        return None, 0
    if not B or not any(carried(r)[0] for r in A.values()):
        return
    print("\n## Team familiarity: the side carrying the arrivals (B-A, same seeds)\n")
    print("| round | matches | team cut A | team cut B | A margin | B margin | B-A | se | A win% | B win% |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    pairs = [(A[i], B[i]) for i in A if i in B and carried(A[i])[0]]
    rounds = sorted({carried(a)[0]["fam_round"] for a, _ in pairs})
    means = []
    for rd in rounds + [None]:
        rows = [(a, b) for a, b in pairs if rd is None or carried(a)[0]["fam_round"] == rd]
        ma = [carried(a)[1] for a, _ in rows]
        mb = [carried(b)[1] for _, b in rows]
        d = [y - x for x, y in zip(ma, mb)]
        se = st.stdev(d) / math.sqrt(len(d)) if len(d) > 1 else 0.0
        win = lambda m: 100 * sum(x > 0 for x in m) / len(m)
        cut = lambda k: st.mean(carried(p[k])[0].get("team_cut", 0) for p in rows)
        if rd is not None:
            means.append(st.mean(d))
        print(f"| {rd if rd is not None else 'all'} | {len(rows)} | {cut(0):.3f} | {cut(1):.3f} | {st.mean(ma):+.1f} | "
              f"{st.mean(mb):+.1f} | {st.mean(d):+.2f} | {se:.2f} | {win(ma):.1f} | {win(mb):.1f} |")


def tag_section(A, B):
    """--tag (row 120): what each midfielder's tag would leave his man, and what the tag did. Each match line's
    "tag" names the tagged man and the tagger; B-A is paired by seed on the matches where B set
    a tag, so B = a tag and A = --tag none is what that tag does against no tag."""
    tagged = [r for r in A.values() if "tag" in r] + [r for r in B.values() if "tag" in r]
    if not tagged:
        return
    keeps = sorted(x for r in A.values() if "tag" in r for x in r["tag"]["keeps"])
    print("\n## Tags (row 120)\n")
    if keeps:
        n = len(keeps)
        print(f"The tag multiplier on his chance to carry, on fresh legs, over {n} starting midfield slots: lowest {100 * keeps[0]:.0f}%, "
              f"median {100 * keeps[n // 2]:.0f}%, highest {100 * keeps[-1]:.0f}%; at a Tagger's 42%: {100 * sum(x <= 0.42 for x in keeps) / n:.1f}%, "
              f"at 55% or more: {100 * sum(x >= 0.55 for x in keeps) / n:.1f}%. "
              f"Sides with a Tagger: {100 * sum(r['tag']['has_tagger'] for r in A.values() if 'tag' in r) / max(1, sum('tag' in r for r in A.values())):.1f}%.\n")
    rows = [("tagged man's disposals", lambda t: t["target_line"]["di"]),
            ("tagged man's clearances", lambda t: t["target_line"]["cl"]),
            ("tagged man's goals", lambda t: t["target_line"]["g"]),
            ("tagging side's margin", lambda t: t["margin"])]
    tagger_rows = [("tagger's disposals", lambda t: t["tagger_line"]["di"])]
    common = [i for i in A if "tag" in A[i] and i in B and "tag" in B[i] and B[i]["tag"]["set"]]
    if not B:
        common = [i for i in A if "tag" in A[i] and A[i]["tag"]["set"]]
    if not common:
        print("No match played a tag in this comparison.")
        return
    print("| | A | B | B-A | se |")
    print("|---|---|---|---|---|")
    for name, fn in rows + tagger_rows:
        a = [fn(A[i]["tag"]) for i in common]
        if B:
            b = [fn(B[i]["tag"]) for i in common]
            d = [y - x for x, y in zip(a, b)]
            se = st.stdev(d) / math.sqrt(len(d)) if len(d) > 1 else 0.0
            print(f"| {name} | {st.mean(a):.2f} | {st.mean(b):.2f} | {st.mean(d):+.2f} | {se:.2f} |")
        elif a:
            print(f"| {name} | {st.mean(a):.2f} | - | - | - |")
    source = B if B else A
    keep = [source[i]["tag"].get("keep", 1.0) for i in common]
    if keep:
        print(f"\nMatches compared {len(common)}; the tag multiplies his chance to carry by {100 * st.mean(keep):.1f}% on the tagger's first "
              f"legs (lowest {100 * min(keep):.1f}%, highest {100 * max(keep):.1f}%); "
              f"tagger is a Tagger in {100 * sum(source[i]['tag']['specialist'] for i in common) / len(common):.1f}%.")
        wins = [source[i]["tag"]["margin"] > 0 for i in common]
        print(f"Tagging side wins {100 * sum(wins) / len(wins):.1f}%.")


def year_ref(o):
    """The real per-team-match rates to mark against, and their label: 2026
    (afl_team_rates.json), or a past season's (afl_year_rates.json, legacy row 142 L5)
    when --year or an arm's own --year names one. A stat that season did not record
    is absent, so it reads "-" rather than being marked against another year."""
    year = o.year
    if not year:
        for arm in (o.b, o.a):
            m = re.search(r"--year\s+(\d{4})", arm or "")
            if m:
                year = int(m.group(1))
                break
    if year and year != 2026:
        years = json.load(open(os.path.join(HERE, "afl_year_rates.json"), encoding="utf-8"))["years"]
        if str(year) not in years:
            raise SystemExit(f"no real rates for {year} in afl_year_rates.json")
        return years[str(year)]["per_team_match"], f"real {year} (afl_year_rates.json, AFL Tables season totals)"
    return (json.load(open(os.path.join(HERE, "afl_team_rates.json")))["per_team_match"],
            "real 2026 (afl_team_rates.json)")


# Pressure a team a game, from the presser's end (afl_pressure_rates.json, Champion Data
# 2025-26 via build_pressure_rates.py). (label, real key, team-match fn, ratio?)
PRESSURE_ROWS = [
    ("pressure acts", "pressure_acts", lambda t: float(t.get("pressure_acts", 0)), None),
    ("  in his defensive half", "pressure_acts_dhalf", lambda t: float(t.get("pressure_acts_dhalf", 0)), None),
    ("tackles", "tackles", lambda t: float(t.get("tackles", 0)), None),
    ("  inside his forward 50", "tackles_i50", lambda t: float(t.get("tackles_i50", 0)), None),
    ("defensive-half share of pressure acts", "dhalf_share", "pressure_acts_dhalf", "pressure_acts"),
    ("tackles per pressure act", "tackles_per_act", "tackles", "pressure_acts"),
    ("forward-50 share of tackles", "i50_share", "tackles_i50", "tackles"),
]


def _press_fn(fn, num, den):
    if den is None:
        return lambda r: sum(fn(t) for t in r["teams"]) / 2
    def f(r):
        d = sum(float(t.get(den, 0)) for t in r["teams"])
        return None if d == 0 else sum(float(t.get(num, 0)) for t in r["teams"]) / d
    return f


def pressure_section(A, B):
    """Where and how a side applies pressure, against Champion Data 2025-26: pressure acts and
    tackles a team a game, the share of pressure acts in the presser's defensive half, tackles
    per pressure act and tackles inside his forward 50 (MatchSim._press_where)."""
    if not any("pressure_acts_dhalf" in t for r in A.values() for t in r["teams"]):
        return
    ref = json.load(open(os.path.join(HERE, "afl_pressure_rates.json")))
    real = ref["per_team_match"]
    print("

## Pressure a team a game (presser's end; real: Champion Data 2025-26 club-seasons)
")
    head = "| stat | AFL mean | AFL range | A | A/real | mark |" + (" B | mark | B-A | se | sig |" if B else "")
    print(head)
    print("|" + "---|" * (head.count("|") - 1))
    for label, key, fn, den in PRESSURE_ROWS:
        rr = real[key]
        pct = den is not None
        f = _press_fn(fn, fn, den)
        ma, mb, dm, se = paired(A, B, f)
        k = 100 if pct else 1
        u = "%" if pct else ""
        line = (f"| {label} | {k * rr['mean']:.1f}{u} | {k * rr['min']:.1f}-{k * rr['max']:.1f}{u} |"
                f" {k * ma:.1f}{u} | {ma / rr['mean']:.2f} | {_mark(ma, rr)} |")
        if B:
            sig = "yes" if se and abs(dm) > 2 * se else ""
            line += f" {k * mb:.1f}{u} | {_mark(mb, rr)} | {k * dm:+.2f} | {k * se:.2f} | {sig} |"
        print(line)
    print(f"
Real: {ref['source']} The sim counts a tackle, a rushed disposal and a smother as a"
          " pressure act; Champion Data also counts chases and corrals that do not touch the disposal.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--n", type=int, default=0)
    ap.add_argument("--secs", type=int, default=0)
    ap.add_argument("--a", default="base")
    ap.add_argument("--b", default=None)
    ap.add_argument("--year", type=int, default=0,
                    help="mark against this season's real rates (afl_year_rates.json);"
                         " default: the --year in B's or A's args, else 2026")
    o = ap.parse_args()
    real, ref_label = year_ref(o)
    A = load(o.run, "a")
    B = load(o.run, "b") if o.b else {}
    keys = sorted({k for r in A.values() for t in r["teams"] for k in t if isinstance(t[k], (int, float))})
    shown = [k for k in MAP if k in keys] + [k for k in EXTRA if k in keys]
    rate = len(A) * (2 if B else 1) / max(1, o.secs)
    print(f"# Balance run: {len(A)} matches{' x2 arms' if B else ''}, {o.secs}s ({rate:.1f} matches/s)\n")
    print(f"A = `{o.a}`" + (f", B = `{o.b}` (same seeds)" if B else "") + "\n")
    print(f"Real reference: {ref_label}\n")
    head = "| stat (per team-match) | AFL mean | AFL range | A | mark |"
    if B:
        head += " B | mark | B-A | se | sig |"
    print(head)
    print("|" + "---|" * (head.count("|") - 1))
    outs = []
    for k in shown:
        a = per_match(A, k)
        ma = st.mean(a.values())
        ref = real.get(MAP.get(k, ""), None)

        def mark(v):
            if not ref:
                return "-"
            if ref["min"] <= v <= ref["max"]:
                return "IN"
            return "NEAR" if abs(v - ref["mean"]) <= 2 * ref["sd"] else "OUT"
        line = f"| {k} | {ref['mean']:.1f} | {ref['min']:.1f}-{ref['max']:.1f} |" if ref else f"| {k} | - | - |"
        line += f" {ma:.1f} | {mark(ma)} |"
        if mark(ma) == "OUT":
            outs.append(k)
        if B:
            b = per_match(B, k)
            common = [i for i in a if i in b]
            d = [b[i] - a[i] for i in common]
            mb = st.mean(b[i] for i in common)
            se = st.stdev(d) / math.sqrt(len(d)) if len(d) > 1 else 0.0
            sig = "yes" if se > 0 and abs(st.mean(d)) > 2 * se else ("yes" if se == 0 and st.mean(d) != 0 else "")
            line += f" {mb:.1f} | {mark(mb)} | {st.mean(d):+.2f} | {se:.2f} | {sig} |"
        print(line)
    # The real column reads B's weather against a perfect day, so A must be one:
    # no --weather (the worker's default) or --weather perfect.
    a_perfect = "--weather" not in (o.a or "") or "--weather perfect" in (o.a or "")
    cond = (next((c for c in ("wet", "windy", "hot") if f"--weather {c}" in (o.b or "")), None)
            if a_perfect else None)
    weather_section(A, B, cond)
    role_table(A, B)
    spoils_section(A, B)
    for name, R in (("A", A), ("B", B)):
        if not R:
            continue
        m, h = margins(R)
        n = len(m)
        print(f"\n{name} margins: mean {st.mean(m):.1f}, median {st.median(m):.0f}, "
              f"60+ {100*sum(x >= 60 for x in m)/n:.1f}%, 100+ {100*sum(x >= 100 for x in m)/n:.1f}%, "
              f"draws {100*sum(x == 0 for x in m)/n:.1f}%, home win {100*sum(x > 0 for x in h)/n:.1f}%, home margin {st.mean(h):+.1f} "
              f"(se {st.stdev(h)/math.sqrt(n):.1f})")
    print("\nReal AFL (docs/LEAGUE_BALANCE.md): 60+ about 15.5%, 100+ about 1.9%, home win 59.3%.")
    shots_section(A, B)
    duel_section(A, B)
    ruck_section(A, B)
    margin_tail(A, B)
    familiarity_section(A, B)
    role_report(A, B)
    type_report(A, B)
    reb_route_section(A, B)
    tackle_section(A, B)
    pressure_section(A, B)
    legs_section(A, B)
    tag_section(A, B)
    print(f"\nOUT of real range (A): {', '.join(outs) if outs else 'none'}")


if __name__ == "__main__":
    main()
