#!/usr/bin/env python3
"""Report of the shape harness (tools/balance.sh shape, TODO row 201).

Reads the worker lines (<run>/a_*.jsonl, and b_*.jsonl for a paired run), each
with the "shape" block tools/balance/shape_probe.gd writes, and prints:

1. The team shape per phase (both sides pooled, one value per match and phase),
   each measure marked against afl_shape_rates.json:
   IN   inside the reference's range (lo..hi);
   NEAR within the reference's wider band (near_lo..near_hi; by default the
        range widened by half its span on each side);
   OUT  outside that;
   -    no published reference (the spec says why).
2. Kicks: length, share of 40 m and longer, switches, backward kicks.
3. A paired run: the called side's change, B - A, with its standard error over
   the paired matches, per phase and measure, and |B-A| > 2 se marked "sig".

Usage: python shape_report.py --run <run dir> [--a=label] [--b=label]
       python shape_report.py --a-run <baseline dir> --run <call dir> --a=label --b=label
         (a shared baseline: both single-arm runs on the same seeds)
"""
import argparse
import glob
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))

PHASES = [
    ("centre", "Centre bounce (at the bounce)"),
    ("stoppage", "Ball-up or throw-in (at the throw)"),
    ("kickin", "Kick-in (at the kick)"),
    ("set_shot", "Set shot (at the kick)"),
    ("att_d50", "Our ball, in our defensive 50"),
    ("att_dmid", "Our ball, our half outside the 50"),
    ("att_amid", "Our ball, their half outside the 50"),
    ("att_f50", "Our ball, in our forward 50"),
    ("def_d50", "Their ball, in our defensive 50"),
    ("def_dmid", "Their ball, our half outside the 50"),
    ("def_amid", "Their ball, their half outside the 50"),
    ("def_f50", "Their ball, in their defensive 50"),
    ("con_d50", "Loose ball, in our defensive 50"),
    ("con_dmid", "Loose ball, our half outside the 50"),
    ("con_amid", "Loose ball, their half outside the 50"),
    ("con_f50", "Loose ball, in our forward 50"),
]

MEASURES = [
    ("len", "Length, deepest to furthest man (m)"),
    ("wid", "Width, widest pair across (m)"),
    ("len_p", "Length, 10th-90th percentile (m)"),
    ("wid_p", "Width, 10th-90th percentile (m)"),
    ("area", "Area of the 18 (convex hull, m2)"),
    ("spread", "Spread, mean distance to the team's centre (m)"),
    ("cen_x", "Team centre on the ground (m from centre, + is toward our goal)"),
    ("cen_dx", "Team centre ahead of the ball (m, - is behind)"),
    ("cen_gap", "Distance between the two teams' centres (m)"),
    ("behind", "Men behind the ball (of 18)"),
    ("own_10", "Own men within 10 m of the ball"),
    ("opp_10", "Opponents within 10 m of the ball"),
    ("own_20", "Own men within 20 m of the ball"),
    ("in_zone", "Both teams' men in the ball's quarter of the ground"),
    ("near_opp", "Mean distance to nearest opponent (m)"),
    ("free_5", "Men with no opponent within 5 m"),
    ("carrier_opp", "Ball carrier: nearest opponent (m)"),
]


def load(run, arm):
    rows = {}
    for f in sorted(glob.glob(os.path.join(run, arm + "_*.jsonl"))):
        for line in open(f, encoding="utf-8"):
            line = line.strip()
            if line:
                try:
                    r = json.loads(line)
                except ValueError:  # a run stopped mid-write leaves half a line
                    continue
                if "shape" in r:
                    rows[r["i"]] = r
    return rows


def bucket_means(r, side):
    """{phase: {measure: mean}} for one side of one match."""
    out = {}
    for ph, pair in r["shape"]["buckets"].items():
        s = pair[side]
        n = s.get("n", 0)
        if n <= 0:
            continue
        m = {}
        for key, _ in MEASURES:
            if key == "carrier_opp":
                cn = s.get("carrier_n", 0)
                if cn > 0:
                    m[key] = s[key] / cn
            elif key in s:
                m[key] = s[key] / n
        m["_n"] = n
        out[ph] = m
    return out


def mean_sd(v):
    if not v:
        return float("nan"), float("nan")
    mu = sum(v) / len(v)
    sd = math.sqrt(sum((x - mu) ** 2 for x in v) / max(1, len(v) - 1))
    return mu, sd


def mark(value, ref):
    if not ref or ref.get("lo") is None:
        return "-"
    lo, hi = ref["lo"], ref["hi"]
    span = hi - lo
    nlo = ref.get("near_lo", lo - max(span * 0.5, abs(lo) * 0.1))
    nhi = ref.get("near_hi", hi + max(span * 0.5, abs(hi) * 0.1))
    if lo <= value <= hi:
        return "IN"
    if nlo <= value <= nhi:
        return "NEAR"
    return "OUT"


def fmt(x, nd=1):
    return "-" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{nd}f}"


def ref_text(ref):
    if not ref or ref.get("lo") is None:
        return "-"
    if ref["lo"] == ref["hi"]:
        return fmt(ref["lo"])
    return f"{fmt(ref['lo'])}..{fmt(ref['hi'])}"


def kick_summary(rows, sides=None):
    tot = {}
    for r in rows.values():
        for side in (sides(r) if sides else (0, 1)):
            for k, v in r["shape"]["kicks"][side].items():
                tot[k] = tot.get(k, 0) + v
    n = tot.get("n", 0)
    if n == 0:
        return {}
    mu = tot["len"] / n
    return {"n": n, "len": mu, "len_sd": math.sqrt(max(0.0, tot["len2"] / n - mu * mu)),
            "long40": tot["long40"] / n, "switch": tot["switch"] / n, "back": tot["back"] / n,
            "across": tot["across"] / n, "gain": tot["gain"] / n, "into_f50": tot["into_f50"] / n}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--a", default="base")
    ap.add_argument("--b", default="")
    ap.add_argument("--rates", default=os.path.join(HERE, "afl_shape_rates.json"))
    ap.add_argument("--a-run", default="", help="take arm A from another run dir (its a_*.jsonl) and arm B"
                    " from --run's a_*.jsonl: one shared baseline for many single-arm call runs")
    args = ap.parse_args()
    refs = json.load(open(args.rates, encoding="utf-8")) if os.path.exists(args.rates) else {}
    if args.a_run:
        A = load(args.a_run, "a")
        B = load(args.run, "a")
    else:
        A = load(args.run, "a")
        B = load(args.run, "b")
    print(f"# Team shape against real AFL ({len(A)} matches, arm A: {args.a})\n")
    print("Each value is the mean over matches of that match's mean in the phase, both sides pooled;"
          " sd is across matches. Reference: afl_shape_rates.json (each entry names its source).\n")
    counts = {"IN": 0, "NEAR": 0, "OUT": 0, "-": 0}
    for ph, title in PHASES:
        vals = {}
        for r in A.values():
            for side in (0, 1):
                m = bucket_means(r, side).get(ph)
                if m:
                    for key in m:
                        vals.setdefault(key, []).append(m[key])
        if not vals:
            continue
        print(f"## {title}\n")
        print("| measure | sim | sd | real | mark | source |")
        print("|---|---|---|---|---|---|")
        for key, label in MEASURES:
            if key not in vals:
                continue
            mu, sd = mean_sd(vals[key])
            ref = refs.get("phases", {}).get(ph, {}).get(key) or refs.get("phases", {}).get("*", {}).get(key)
            mk = mark(mu, ref)
            counts[mk] += 1
            print(f"| {label} | {fmt(mu)} | {fmt(sd)} | {ref_text(ref)} | {mk} | {(ref or {}).get('src', '')} |")
        print(f"\n_{sum(vals['_n']):.0f} snapshots._\n")
    ks = kick_summary(A)
    if ks:
        print("## Kicks in general play (and kick-ins)\n")
        print("| measure | sim | real | mark | source |")
        print("|---|---|---|---|---|")
        kref = refs.get("kicks", {})
        for key, label in [("len", "Mean kick length (m)"), ("len_sd", "Kick length sd (m)"),
                           ("long40", "Share 40 m and longer"), ("switch", "Share that switch play"),
                           ("back", "Share kicked backward"), ("across", "Mean move across the ground (m)"),
                           ("gain", "Mean ground made (m)"), ("into_f50", "Share that enter the forward 50")]:
            ref = kref.get(key)
            mk = mark(ks[key], ref)
            counts[mk] += 1
            nd = 3 if key in ("long40", "switch", "back", "into_f50") else 1
            print(f"| {label} | {fmt(ks[key], nd)} | {ref_text(ref)} | {mk} | {(ref or {}).get('src', '')} |")
        print(f"\n_{ks['n']} kicks. A switch: the ball crosses the centre line of the ground lengthways,"
              " from 10 m or more off it, moving 25 m or more across._\n")
    print(f"**Marks:** IN {counts['IN']}, NEAR {counts['NEAR']}, OUT {counts['OUT']}, no reference {counts['-']}.\n")
    if not B:
        return
    pairs = [i for i in A if i in B]
    print(f"# The call: B ({args.b}) against A ({args.a}), the called side, {len(pairs)} paired matches\n")
    print("B - A is the mean over paired matches of the called side's per-match mean; se from the"
          " paired differences; sig when |B-A| > 2 se.\n")
    for ph, title in PHASES:
        lines = []
        for key, label in MEASURES:
            d = []
            av = []
            for i in pairs:
                s = A[i].get("called", i % 2)
                ma = bucket_means(A[i], s).get(ph, {})
                mb = bucket_means(B[i], s).get(ph, {})
                if key in ma and key in mb:
                    d.append(mb[key] - ma[key])
                    av.append(ma[key])
            if len(d) < 3:
                continue
            mu, sd = mean_sd(d)
            se = sd / math.sqrt(len(d))
            lines.append(f"| {label} | {fmt(mean_sd(av)[0])} | {fmt(mean_sd(av)[0] + mu)} | {mu:+.2f} | {se:.2f} |"
                         f" {'sig' if abs(mu) > 2 * se else ''} |")
        if lines:
            print(f"## {title}\n")
            print("| measure | A | B | B-A | se | |")
            print("|---|---|---|---|---|---|")
            print("\n".join(lines) + "\n")
    called = lambda r: (r.get("called", r["i"] % 2),)
    ka = kick_summary({i: A[i] for i in pairs}, called)
    kb = kick_summary({i: B[i] for i in pairs}, called)
    if ka and kb:
        print("## The called side's kicks\n")
        print("| measure | A | B | B-A |")
        print("|---|---|---|---|")
        for key in ("len", "long40", "switch", "back", "across", "gain"):
            nd = 3 if key in ("long40", "switch", "back") else 1
            print(f"| {key} | {fmt(ka[key], nd)} | {fmt(kb[key], nd)} | {kb[key] - ka[key]:+.{nd}f} |")
        print()
    pa = [A[i]["shape"]["pair"] for i in pairs if "pair" in A[i]["shape"] and "pair" in B[i]["shape"]]
    pb = [B[i]["shape"]["pair"] for i in pairs if "pair" in A[i]["shape"] and "pair" in B[i]["shape"]]
    if pa:
        print("## The named pair (our man to his opponent, open play)\n")
        print("Our man: the tagger (in the no-tag arm, the man who would tag) or the defender switched on to"
              " their best forward (in the no-switch arm, the same defender).\n")
        print("| measure | A | B | B-A | se |")
        print("|---|---|---|---|---|")
        for key, lab in (("dist", "Distance to his man (m)"), ("within5", "Share of time within 5 m"),
                         ("goal", "Distance to the goal he defends (m)")):
            d = [b[key] / b["n"] - a[key] / a["n"] for a, b in zip(pa, pb) if a["n"] and b["n"]]
            av = [a[key] / a["n"] for a in pa if a["n"]]
            mu, sd = mean_sd(d)
            print(f"| {lab} | {fmt(mean_sd(av)[0], 2)} | {fmt(mean_sd(av)[0] + mu, 2)} | {mu:+.2f} |"
                  f" {sd / math.sqrt(max(1, len(d))):.2f} |")
        print()
    ta = [A[i]["shape"]["tag"][A[i].get("called", i % 2)] for i in pairs]
    tb = [B[i]["shape"]["tag"][B[i].get("called", i % 2)] for i in pairs]
    na, nb = sum(t["n"] for t in ta), sum(t["n"] for t in tb)
    if na or nb:
        print("## The tag (called side's tagger to his man, open play)\n")
        for lab, ts, n in (("A", ta, na), ("B", tb, nb)):
            if n:
                print(f"- {lab}: mean {sum(t['dist'] for t in ts) / n:.1f} m, within 5 m"
                      f" {sum(t['within5'] for t in ts) / n:.0%} of {n} samples")
            else:
                print(f"- {lab}: no tag on")
        print()


if __name__ == "__main__":
    main()
