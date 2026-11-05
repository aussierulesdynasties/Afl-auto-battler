"""One-page balance report for tools/balance.sh runs.

Reads <run>/a_*.jsonl (and b_*.jsonl when paired), averages each team stat per
team-match, and marks it against real AFL 2026 rates (afl_team_rates.json):
IN when inside the 18 clubs' lowest..highest, NEAR when within mean +-2 sd,
else OUT. Paired runs also show B - A with its standard error over seeds, so a
change is real when |delta| > 2 se.
"""
import argparse, glob, json, math, os, statistics as st

HERE = os.path.dirname(os.path.abspath(__file__))
# sim stat -> afl_team_rates key (score is computed from goals/behinds there)
MAP = {"disposals": "disposals", "kicks": "kicks", "handballs": "handballs",
       "marks": "marks", "contested_marks": "contested_marks", "tackles": "tackles",
       "inside50": "inside_50s", "clearances": "clearances", "hitouts": "hitouts",
       "frees_for": "frees_for", "goals": "goals", "behinds": "behinds",
       "rebound50": "rebound_50s", "rebounds": "rebound_50s"}
EXTRA = ["score", "clangers", "intercepts", "one_percenters", "metres_gained"]


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
# Champion Data 2025 (Wheelo), intercepts a game per player by position
# (docs/research/INTERCEPT_EVIDENCE.md; tools/audit/intercept_impl.gd REAL).
ROLE_REAL = {"DEF": 4.9, "MID": 2.5, "FWD": 1.1, "RUCK": 2.2}


def role_rate(rows, role):
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
        a = role_rate(A, role)
        if not a:
            continue
        ra = sum(v[0] for v in a.values()) / sum(v[1] for v in a.values())
        sa = 100 * sum(v[0] for v in a.values()) / tot["A"]
        line = f"| {role} | {real:.1f} | {ra:.2f} | {sa:.0f}% |"
        if B:
            b = role_rate(B, role)
            common = [i for i in a if i in b]
            rb = sum(b[i][0] for i in common) / sum(b[i][1] for i in common)
            sb = 100 * sum(b[i][0] for i in common) / tot["B"]
            d = [b[i][0] / b[i][1] - a[i][0] / a[i][1] for i in common]
            se = st.stdev(d) / math.sqrt(len(d)) if len(d) > 1 else 0.0
            sig = "yes" if se > 0 and abs(st.mean(d)) > 2 * se else ""
            line += f" {rb:.2f} | {sb:.0f}% | {rb - ra:+.2f} | {se:.2f} | {sig} |"
        print(line)
    print("\nReal shares (Champion Data 2025): DEF 57%, MID 23%, FWD 15%, RUCK 4%; a team intercepts about 63.4 a game.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--n", type=int, default=0)
    ap.add_argument("--secs", type=int, default=0)
    ap.add_argument("--a", default="base")
    ap.add_argument("--b", default=None)
    o = ap.parse_args()
    real = json.load(open(os.path.join(HERE, "afl_team_rates.json")))["per_team_match"]
    A = load(o.run, "a")
    B = load(o.run, "b") if o.b else {}
    keys = sorted({k for r in A.values() for t in r["teams"] for k in t if isinstance(t[k], (int, float))})
    shown = [k for k in MAP if k in keys] + [k for k in EXTRA if k in keys]
    rate = len(A) * (2 if B else 1) / max(1, o.secs)
    print(f"# Balance run: {len(A)} matches{' x2 arms' if B else ''}, {o.secs}s ({rate:.1f} matches/s)\n")
    print(f"A = `{o.a}`" + (f", B = `{o.b}` (same seeds)" if B else "") + "\n")
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
    role_table(A, B)
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
    margin_tail(A, B)
    print(f"\nOUT of real range (A): {', '.join(outs) if outs else 'none'}")


if __name__ == "__main__":
    main()
