"""Row 84: what each Togetherness band does on match day, from balance_match_impl
logs run with --together BAND (one side a match carries the band, in turn).

    python tools/audit/together_report.py mid=a.log,b.log tight=c.log,d.log ...

Each arm plays the same seeded matches; "mid" (no --together) is the baseline.
Prints, for the side that carries the band: win %, mean margin, share of
clearances and of contested possessions, and the points credited to
togetherness, each against mid on the same matches. Measurement only.
"""
import json
import math
import sys


def load(paths):
    rows = {}
    for path in paths.split(","):
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                at = line.find("BAL {")
                if at < 0:
                    continue
                r = json.loads(line[at + 4:])
                rows[int(r["i"])] = r
    return rows


def side_line(r):
    s = int(r["i"]) % 2
    me, them = r["teams"][s], r["teams"][1 - s]
    margin = int(me["score"]) - int(them["score"])
    win = 1.0 if margin > 0 else 0.5 if margin == 0 else 0.0
    cl = float(me.get("clearances", 0)), float(them.get("clearances", 0))
    cc = float(me.get("contested_possessions", 0)), float(them.get("contested_possessions", 0))
    return {
        "win": win,
        "margin": margin,
        "cl": cl[0] / max(1.0, cl[0] + cl[1]),
        "cc": cc[0] / max(1.0, cc[0] + cc[1]),
        "pts": float(me.get("together_pts", 0.0)),
    }


def mean_se(xs):
    n = len(xs)
    m = sum(xs) / n
    v = sum((x - m) ** 2 for x in xs) / max(1, n - 1)
    return m, math.sqrt(v / n)


def main():
    arms = dict(a.split("=", 1) for a in sys.argv[1:])
    data = {k: load(v) for k, v in arms.items()}
    base = data.get("mid")
    print("| Band | Matches | Win % (B-A, se) | Margin (B-A, se) | Clearance share | Contested possession share | Credited pts/match |")
    print("|---|---|---|---|---|---|---|")
    for band in ["very", "tight", "mid", "cliques", "split"]:
        if band not in data:
            continue
        rows = data[band]
        ids = sorted(set(rows) & set(base)) if base else sorted(rows)
        b = [side_line(rows[i]) for i in ids]
        a = [side_line(base[i]) for i in ids] if base else b
        def cell(key, scale=1.0, fmt="%.1f"):
            mb, _ = mean_se([x[key] * scale for x in b])
            if band == "mid" or not base:
                return fmt % mb
            d, se = mean_se([(x[key] - y[key]) * scale for x, y in zip(b, a)])
            return (fmt + " (%+.2f, %.2f)") % (mb, d, se)
        pts, _ = mean_se([x["pts"] for x in b])
        print("| %s | %d | %s | %s | %s | %s | %+.2f |" % (
            band, len(ids), cell("win", 100.0), cell("margin"), cell("cl", 100.0),
            cell("cc", 100.0), pts))


if __name__ == "__main__":
    main()
