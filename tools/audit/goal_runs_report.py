"""Audit 29 report: runs of goals, the margin spread and close-finish scene reach, sim vs real AFL.

    python tools/audit/goal_runs_report.py <audit.log> [<audit.log> ...]

Reads the G| lines of tools/audit/goal_runs_impl.gd. Real references:
  - tools/balance/afl_goal_runs.json  goal order of every match, AFL Tables scoring progressions
  - tools/balance/afl_comebacks.json  final scores 2010-2025 (AFL Tables), for margins
  - data/raw/fixtures_2026.json       real 2026 home-and-away margins
A run is unanswered goals by one side, behinds ignored, carried across quarter breaks (as the
game's own run of goals is, MatchSim._run).

Marks: IN when the sim is within 2 combined standard errors of real, NEAR within 4, else OUT
(the rule tools/balance/balance_report.py uses for paired changes). Sim-only rows get no mark.
"""
import json
import math
import os
import random
import statistics as st
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
BAL = os.path.join(ROOT, "tools", "balance")


def runs(seq):
    """Lengths of every run of goals in a goal-order string ('|' ignored)."""
    s = seq.replace("|", "")
    out, cur, prev = [], 0, ""
    for c in s:
        if c == prev:
            cur += 1
        else:
            if cur:
                out.append(cur)
            cur, prev = 1, c
    if cur:
        out.append(cur)
    return out


def shuffled_max(seq, rng, reps=20):
    """Mean longest run when the match's own goals are put in random order (no momentum)."""
    g = list(seq.replace("|", ""))
    t = 0
    for _ in range(reps):
        rng.shuffle(g)
        t += max(runs("".join(g)) or [0])
    return t / reps


def load_sim(paths):
    out = {"ai": [], "coach": []}
    for p in paths:
        for line in open(p, encoding="utf-8", errors="replace"):
            if not line.startswith("G|"):
                continue
            f = line.rstrip("\n").split("|")
            # G|mode|seed|home|away|weather|hs|as|seq(with |)|siren|m100|bwin|calls: seq holds 3 bars.
            mode, seed, home, away, weather, hs, as_ = f[1], f[2], f[3], f[4], f[5], int(f[6]), int(f[7])
            seq = "|".join(f[8:12])
            siren, m100, bwin, calls = int(f[12]), int(f[13]), int(f[14]), f[15] if len(f) > 15 else ""
            out[mode].append({"seed": seed, "h": hs, "a": as_, "seq": seq, "siren": siren, "m100": m100,
                              "bwin": bwin, "calls": [c for c in calls.split(";") if c]})
    return out


def se_p(p, n):
    return math.sqrt(max(p * (1 - p), 1e-9) / n) if n else 0.0


def mark(sim, s_se, real, r_se):
    if real is None:
        return ""
    c = math.sqrt(s_se ** 2 + r_se ** 2)
    if abs(sim - real) <= 2 * c:
        return "IN"
    return "NEAR" if abs(sim - real) <= 4 * c else "OUT"


def share_row(label, sim_vals, real_vals):
    ns, k = len(sim_vals), sum(sim_vals)
    ps = k / ns if ns else 0
    if real_vals is None:
        return f"| {label} | - | {100*ps:.1f}% ({ns}) | |"
    nr, kr = len(real_vals), sum(real_vals)
    pr = kr / nr
    return f"| {label} | {100*pr:.1f}% ({nr}) | {100*ps:.1f}% ({ns}) | {mark(ps, se_p(ps, ns), pr, se_p(pr, nr))} |"


def mean_row(label, sim_vals, real_vals, fmt="{:.2f}"):
    ms = st.mean(sim_vals)
    ss = st.stdev(sim_vals) / math.sqrt(len(sim_vals))
    if real_vals is None:
        return f"| {label} | - | {fmt.format(ms)} | |"
    mr = st.mean(real_vals)
    sr = st.stdev(real_vals) / math.sqrt(len(real_vals))
    return f"| {label} | {fmt.format(mr)} | {fmt.format(ms)} | {mark(ms, ss, mr, sr)} |"


def main():
    sim = load_sim(sys.argv[1:])
    real_runs = json.load(open(os.path.join(BAL, "afl_goal_runs.json"), encoding="utf-8"))
    rg = real_runs["games"]
    hist = json.load(open(os.path.join(BAL, "afl_comebacks.json"), encoding="utf-8"))["games"]
    hm = [abs(g["h"][3] - g["a"][3]) for g in hist]
    fx = json.load(open(os.path.join(ROOT, "data", "raw", "fixtures_2026.json"), encoding="utf-8"))["games"]
    r26 = [abs(g["hscore"] - g["ascore"]) for g in fx if g.get("complete") == 100 and not g.get("is_final")]
    rng = random.Random(29)

    for mode in ("ai", "coach"):
        S = sim[mode]
        if not S:
            continue
        n = len(S)
        print(f"\n## {mode}: {n} sim matches\n")
        # Margins.
        sm = [abs(g["h"] - g["a"]) for g in S]
        print(f"### Margins (real 2010-25: {len(hm)} matches; real 2026 H&A: {len(r26)})\n")
        print("| stat | real 2010-25 | sim | mark | real 2026 H&A | mark |")
        print("|---|---|---|---|---|---|")

        def two(label, f):
            vs, v1, v2 = [f(x) for x in sm], [f(x) for x in hm], [f(x) for x in r26]
            ps, p1, p2 = st.mean(vs), st.mean(v1), st.mean(v2)
            print(f"| {label} | {100*p1:.1f}% | {100*ps:.1f}% | {mark(ps, se_p(ps, len(vs)), p1, se_p(p1, len(v1)))} "
                  f"| {100*p2:.1f}% | {mark(ps, se_p(ps, len(vs)), p2, se_p(p2, len(v2)))} |")
        ms, ss = st.mean(sm), st.stdev(sm) / math.sqrt(n)
        m1, s1 = st.mean(hm), st.stdev(hm) / math.sqrt(len(hm))
        m2, s2 = st.mean(r26), st.stdev(r26) / math.sqrt(len(r26))
        print(f"| mean margin | {m1:.1f} | {ms:.1f} | {mark(ms, ss, m1, s1)} | {m2:.1f} | {mark(ms, ss, m2, s2)} |")
        print(f"| median margin | {st.median(hm):.0f} | {st.median(sm):.0f} | | {st.median(r26):.0f} | |")
        for lo, hi in ((0, 6), (7, 12), (13, 24), (25, 39), (40, 59), (60, 79), (80, 99)):
            two(f"{lo}-{hi}", lambda x, lo=lo, hi=hi: lo <= x <= hi)
        for t in (60, 100):
            two(f"{t}+", lambda x, t=t: x >= t)
        two("draw", lambda x: x == 0)
        # Goal runs.
        rl = [runs(g["seq"]) for g in rg]
        sl = [runs(g["seq"]) for g in S]
        print(f"\n### Runs of goals (real: {len(rg)} matches, AFL Tables {min(real_runs['years'])}-{max(real_runs['years'])})\n")
        print("| stat | real | sim | mark |")
        print("|---|---|---|---|")
        print(mean_row("goals a match (both sides)", [sum(r) for r in sl], [sum(r) for r in rl], "{:.1f}"))
        print(mean_row("longest run a match", [max(r or [0]) for r in sl], [max(r or [0]) for r in rl]))
        for k in (3, 4, 5, 6, 7, 8):
            print(share_row(f"match has a run of {k}+", [max(r or [0]) >= k for r in sl], [max(r or [0]) >= k for r in rl]))
        for k in (3, 4, 5):
            print(mean_row(f"runs of {k}+ a match", [sum(x >= k for x in r) for r in sl], [sum(x >= k for x in r) for r in rl]))
        print(mean_row("goals a run (mean run length)", [st.mean(r) for r in sl if r], [st.mean(r) for r in rl if r]))
        # Streakiness against each match's own goals in random order.
        so = st.mean(max(r or [0]) for r in sl)
        sr_ = st.mean(shuffled_max(g["seq"], rng) for g in S)
        ro = st.mean(max(r or [0]) for r in rl)
        rr_ = st.mean(shuffled_max(g["seq"], rng) for g in rg)
        print(f"\nLongest run against the same goals in random order (1.00 = no clustering): "
              f"real {ro:.2f} / {rr_:.2f} = {ro/rr_:.3f}; sim {so:.2f} / {sr_:.2f} = {so/sr_:.3f}.")
        # Close finishes.
        print(f"\n### Close finishes ({mode})\n")
        print("| stat | real 2010-25 | sim | mark |")
        print("|---|---|---|---|")
        print(share_row("final margin within 6", [x <= 6 for x in sm], [x <= 6 for x in hm]))
        print(share_row("final margin within 12", [x <= 12 for x in sm], [x <= 12 for x in hm]))
        timed = [g for g in rg if "ev" in g and len(g.get("qlen", [])) >= 4]
        print(share_row("within 12 at 30% into Q4 (sim minute 100)", [abs(g["m100"]) <= 12 for g in S],
                        [abs(real_margin_at(g)) <= 12 for g in timed] if timed else None))
        print(share_row("late bounce window: a goal after 30% of Q4 leaves it within 12", [g["bwin"] == 1 for g in S],
                        [real_window(g) for g in timed] if timed else None))
        print(share_row("after-the-siren scene shown", [g["siren"] == 1 for g in S], None))
        if mode == "coach":
            def has(g, kind, pred=lambda p: True):
                for c in g["calls"]:
                    k, rest = c.split("@", 1)
                    p = rest.split(":")
                    if k == kind and pred(p):
                        return True
                return False
            b = [has(g, "bounce") for g in S]
            print(share_row("late centre-bounce call asked", b, None))
            win = [g for g in S if g["bwin"] == 1]
            if win:
                print(share_row("  of matches with the window", [has(g, "bounce") for g in win], None))
            close12 = [g for g in S if abs(g["m100"]) <= 12]
            if close12:
                print(share_row("  of matches within 12 entering minute 100", [has(g, "bounce") for g in close12], None))
            print(share_row("close Q4 set-shot call asked (within 18)",
                            [has(g, "set_shot", lambda p: int(p[0]) >= 4 and abs(int(p[2])) <= 18) for g in S], None))
            print(share_row("run-of-goals card asked", [has(g, "momentum") for g in S], None))
            agst = [sum(1 for x in runs_side(g["seq"], "A") if x >= 3) for g in S]
            card = [sum(1 for c in g["calls"] if c.startswith("momentum@")) for g in S]
            print(f"| runs of 3+ against side 0 a match / cards asked a match | - | {st.mean(agst):.2f} / {st.mean(card):.2f} | |")
            kinds = {}
            for g in S:
                for c in g["calls"]:
                    k = c.split("@")[0]
                    kinds[k] = kinds.get(k, 0) + 1
            print("\nCalls asked a match by kind: " + ", ".join(f"{k} {v/n:.2f}" for k, v in sorted(kinds.items())))


# The sim's minute 100 is 30% of the way through Q4 (minutes 91-120); real quarters are timed
# against each quarter's own length, so the same point is 30% of the real Q4.
Q4_FRAC = 0.30


def real_margin_at(g, frac=Q4_FRAC):
    cut = g["qlen"][3] * frac
    m = 0
    for q, side, pts, secs in g["ev"]:
        if q < 4 or (q == 4 and secs < cut):
            m += pts if side == "H" else -pts
    return m


def real_window(g, frac=Q4_FRAC):
    cut = g["qlen"][3] * frac
    m = 0
    for q, side, pts, secs in g["ev"]:
        m += pts if side == "H" else -pts
        if q == 4 and pts == 6 and secs >= cut and abs(m) <= 12:
            return True
    return False


def runs_side(seq, side):
    s = seq.replace("|", "")
    out, cur = [], 0
    for c in s + "#":
        if c == side:
            cur += 1
        else:
            if cur:
                out.append(cur)
            cur = 0
    return out


if __name__ == "__main__":
    main()
