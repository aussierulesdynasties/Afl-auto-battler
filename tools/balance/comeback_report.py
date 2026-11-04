"""Believable comebacks (TODO row 42): sim vs real AFL comeback rates.

Reads quarter-by-quarter scores and prints, for each break (QT, HT, 3QT) and
margin band, how often the side in front went on to win, plus the last-quarter
swing tail. Real rates come from tools/balance/afl_comebacks.json (AFL Tables,
2010-2025 home-and-away and finals; draws count half).

  python tools/balance/comeback_report.py                 # real only
  python tools/balance/comeback_report.py audit.log ...   # C| lines from comeback_impl, base arm
  python tools/balance/comeback_report.py --arm base A.log --arm2 tuned B.log

The sim lines are C|arm|mode|seed|home|away|weather|h1|a1|h2|a2|h3|a3|h4|a4|...
"""
import json, math, os, sys

BANDS = [(1, 6), (7, 12), (13, 18), (19, 24), (25, 30), (31, 36), (37, 999)]
BREAKS = ["QT", "HT", "3QT"]
SWINGS = [20, 30, 40, 50]
HERE = os.path.dirname(os.path.abspath(__file__))


def table(games):
    """games: list of (h[4], a[4]) cumulative scores; index 3 = final."""
    out = {}
    for bi, br in enumerate(BREAKS):
        for lo, hi in BANDS:
            n = w = 0.0
            for h, a in games:
                m = h[bi] - a[bi]
                if not (lo <= abs(m) <= hi):
                    continue
                f = h[3] - a[3]
                n += 1
                if f == 0:
                    w += 0.5
                elif (f > 0) == (m > 0):
                    w += 1
            out["%s %d-%d" % (br, lo, hi)] = (w, n)
    for s in SWINGS:
        k = sum(1 for h, a in games if abs((h[3] - a[3]) - (h[2] - a[2])) >= s)
        out["Q4 swing >=%d" % s] = (k, len(games))
    # The headline: won from 4+ goals down at three-quarter time.
    k = sum(1 for h, a in games if abs(h[2] - a[2]) >= 24 and (h[3] - a[3]) * (h[2] - a[2]) < 0)
    out["won from 24+ down at 3QT"] = (k, len(games))
    return out


def real():
    g = json.load(open(os.path.join(HERE, "afl_comebacks.json")))
    return [(x["h"], x["a"]) for x in g["games"]]


def sim(paths, arm):
    games = []
    for p in paths:
        for line in open(p, encoding="utf-8", errors="replace"):
            i = line.find("C|")
            if i < 0:
                continue
            f = line[i:].strip().split("|")
            if len(f) < 15 or f[1] != arm:
                continue
            v = [int(x) for x in f[7:15]]
            games.append(([v[0], v[2], v[4], v[6]], [v[1], v[3], v[5], v[7]]))
    return games


def pct(w, n):
    return "%5.1f%%" % (100.0 * w / n) if n else "   - "


def se(w, n):
    if not n:
        return 0.0
    p = w / n
    return 100.0 * math.sqrt(max(p * (1 - p), 1e-9) / n)


def verdict(rw, rn, sw, sn):
    if not rn or not sn:
        return ""
    d = 100.0 * (sw / sn - rw / rn)
    e = math.hypot(se(rw, rn), se(sw, sn))
    return "IN" if abs(d) <= 2 * e else ("NEAR" if abs(d) <= 3 * e + 3 else "OUT")


def main(argv):
    arms = []
    i = 0
    cur = ["base", []]
    while i < len(argv):
        if argv[i] in ("--arm", "--arm2"):
            if cur[1]:
                arms.append(cur)
            cur = [argv[i + 1], []]
            i += 2
            continue
        cur[1].append(argv[i])
        i += 1
    if cur[1]:
        arms.append(cur)
    r = table(real())
    sims = [(a, table(sim(p, a))) for a, p in arms]
    head = "| Moment | Real AFL | " + " | ".join("%s (n)" % a for a, _ in sims) + (" | " if sims else "") + " | ".join("%s vs real" % a for a, _ in sims) + " |"
    print(head)
    print("|" + "---|" * (2 + 2 * len(sims)))
    for k, (rw, rn) in r.items():
        row = ["%s (%d)" % (pct(rw, rn), rn)]
        row += ["%s (%d)" % (pct(t[k][0], t[k][1]), t[k][1]) for _, t in sims]
        row += [verdict(rw, rn, t[k][0], t[k][1]) for _, t in sims]
        print("| %s | %s |" % (k, " | ".join(row)))
    print("\nLeader rows: how often the side in front at that break won. Swing rows: share of matches whose last-quarter margin change was at least that size.")


if __name__ == "__main__":
    main(sys.argv[1:])
