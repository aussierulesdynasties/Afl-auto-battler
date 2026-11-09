#!/usr/bin/env python3
"""Row 120: disposals a tagged man keeps, from tag_keep_impl logs, paired on match.

    python tools/audit/tag_keep_report.py <log> <log> ...

Each log is one arm's audit.log; the arm is read from its SUMMARY line, and logs of
one arm pool. Kept = sum(tagged) / sum(untagged) over the same matches, se by the
delta method on the paired differences.
"""
import math
import re
import sys


def load(paths):
    arms = {}
    for path in paths:
        rows = {}
        arm = None
        with open(path, encoding="utf8", errors="replace") as fh:
            for line in fh:
                m = re.match(r"TK (\d+) (\S+) (\S+) (\d) (\d+) ([\d.]+)", line)
                if m:
                    rows[int(m[1])] = (m[2], m[3], m[4] == "1", int(m[5]), float(m[6]))
                m = re.match(r"SUMMARY tag_keep arm (\S+)", line)
                if m:
                    arm = m[1]
        if arm is None:
            print(f"{path}: no SUMMARY line, left out", file=sys.stderr)
            continue
        arms.setdefault(arm, {}).update(rows)
    return arms


def kept(base, arm):
    """(share, se, disposals lost, n, base mean, mean multiplier) over matches in both."""
    keys = [k for k in arm if k in base and arm[k][0] == base[k][0]]
    n = len(keys)
    b = [base[k][3] for k in keys]
    t = [arm[k][3] for k in keys]
    mb, mt = sum(b) / n, sum(t) / n
    share = mt / mb
    # Var(T/B) by the delta method on the per-match residual t - share * b.
    res = [x - share * y for x, y in zip(t, b)]
    var = sum(r * r for r in res) / (n - 1)
    return share, math.sqrt(var / n) / mb, mb - mt, n, mb, sum(arm[k][4] for k in keys) / n


def main():
    arms = load(sys.argv[1:])
    base = arms["none"]
    print("| Arm | Mean multiplier | Base disposals | Tagged disposals | Kept | se | Lost | Matches |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for name in sorted((a for a in arms if a != "none"), key=lambda a: (not a[0].isdigit(), a)):
        s, se, lost, n, mb, mm = kept(base, arms[name])
        print(f"| {name} | {mm:.3f} | {mb:.2f} | {mb - lost:.2f} | {s * 100:.1f}% | {se * 100:.2f} | {lost:.2f} | {n} |")


main()
