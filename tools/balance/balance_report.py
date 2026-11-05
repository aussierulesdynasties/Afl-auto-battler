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


ROLES = ["DEF", "MID", "FWD", "RUCK"]
ROLE_REF = {"disposals": "disposals", "kicks": "kicks", "handballs": "handballs", "marks": "marks",
            "rebounds": "rebound_50s", "inside50": "inside_50s", "clearances": "clearances", "goals": "goals"}


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
    role_report(A, B)
    print(f"\nOUT of real range (A): {', '.join(outs) if outs else 'none'}")


if __name__ == "__main__":
    main()
