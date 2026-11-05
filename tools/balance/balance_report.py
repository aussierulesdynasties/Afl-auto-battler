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
    shots_section(A, B)
    print(f"\nOUT of real range (A): {', '.join(outs) if outs else 'none'}")


if __name__ == "__main__":
    main()
