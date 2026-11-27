"""The measured OVR weights from a tools/balance/weights.sh run (docs/RATING_REBUILD.md §3).

For each AFL position and attribute: side i % 2's margin with every player at that
position +N on it, against the shared unbumped run on the same seeds (paired
mean and standard error). Within a position, an attribute's weight is its margin's
share of the position's positive margins, out of 100; a margin no more than two
standard errors from 0, or below it, buys nothing and weighs 0.

    python3 weights_report.py --run <weights run dir> [--bump 10]
Stdlib only.
"""
import argparse
import glob
import json
import math
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "wheelo"))
import review_lists as R  # noqa: E402

KEYS = ["speed", "endurance", "strength", "work_rate", "kicking", "handballing", "marking", "contested_marking",
        "one_on_one", "contested_ball", "goalkicking", "ruck", "vision", "reading_play", "pressure",
        "forward_craft", "discipline", "durability"]
POSITIONS = ["Key Defender", "Gen. Defender", "Midfielder", "Mid-Forward", "Gen. Forward", "Key Forward", "Ruck"]


def margins(d):
    """{i: side i % 2's margin} from a run folder's a_*.jsonl."""
    out = {}
    for f in glob.glob(os.path.join(d, "a_*.jsonl")):
        for line in open(f, encoding="utf-8"):
            if line.strip().endswith("}"):
                o = json.loads(line)
                t = o["teams"]
                out[o["i"]] = t[o["i"] % 2]["score"] - t[1 - o["i"] % 2]["score"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--bump", type=int, default=10)
    a = ap.parse_args()
    base = margins(os.path.join(a.run, "base"))
    if len(base) < 2:
        sys.exit("weights_report: no base run in %s" % a.run)
    print("# Measured OVR weights (+%d on one attribute for every player at a position, side i %% 2)\n" % a.bump)
    print("%d matches a pair against one unbumped run on the same seeds. Margin = points a match the bumped side "
          "gains; se its standard error; measured weight = its share of the position's real gains (margin "
          "more than 2 se above 0), out of 100; start = the starting weight (RATING_REBUILD §3).\n" % len(base))
    for pos in POSITIONS:
        rows = []
        for k in KEYS:
            d = os.path.join(a.run, "%s__%s" % (pos.replace(" ", "_"), k))
            b = margins(d)
            ids = [i for i in b if i in base]
            if len(ids) < 2:
                rows.append((k, None, None))
                continue
            dm = [b[i] - base[i] for i in ids]
            m = sum(dm) / len(dm)
            se = math.sqrt(sum((x - m) ** 2 for x in dm) / (len(dm) - 1) / len(dm))
            rows.append((k, m, se))
        real = {k: m for k, m, se in rows if m is not None and m > 2 * se}
        total = sum(real.values())
        start = R.WEIGHTS.get(pos, {})
        print("## %s\n" % pos)
        print("| Attribute | Margin | se | Measured | Start |")
        print("|---|---|---|---|---|")
        for k, m, se in rows:
            if m is None:
                print("| %s | not run | | | %s |" % (k, start.get(k, "")))
                continue
            w = round(100 * real[k] / total) if k in real and total > 0 else 0
            print("| %s | %+.2f | %.2f | %d | %s |" % (k, m, se, w, start.get(k, "")))
        print()


if __name__ == "__main__":
    main()
