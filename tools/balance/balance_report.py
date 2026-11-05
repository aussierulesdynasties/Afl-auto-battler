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
    duel_section(A, B)
    print(f"\nOUT of real range (A): {', '.join(outs) if outs else 'none'}")


if __name__ == "__main__":
    main()
