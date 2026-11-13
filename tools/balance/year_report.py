#!/usr/bin/env python3
"""Year mode report (tools/balance.sh year N --years "1990 2000 2010 2020"; legacy, row 142 L5).

Each <run>/<year>/ holds one arm played in that season (worker --year Y), so it
plays that era's football (EraFootball). Every stat a team makes a match is set
against that season's real rates (afl_year_rates.json): IN inside the season's
clubs' lowest..highest, NEAR within mean +-2 sd, OUT. When 2026 is one of the
years, a second table gives each season's shift against 2026, sim against real,
which is what the era rows are fitted to (a stat the sim already plays off in
2026 stays off by about the same share in every season).

    python tools/balance/year_report.py --run .balance/<run>
"""
import argparse, json, math, os, statistics as st

from balance_report import HERE, MAP, load, per_match


def mark(v, ref):
    if ref["min"] <= v <= ref["max"]:
        return "IN"
    return "NEAR" if abs(v - ref["mean"]) <= 2 * ref["sd"] else "OUT"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    o = ap.parse_args()
    years_ref = json.load(open(os.path.join(HERE, "afl_year_rates.json"), encoding="utf-8"))["years"]
    years = sorted(int(d) for d in os.listdir(o.run) if d.isdigit() and os.path.isdir(os.path.join(o.run, d)))
    sims = {y: load(os.path.join(o.run, str(y)), "a") for y in years}
    stats = []
    for k, ref_key in MAP.items():
        if ref_key in [s[1] for s in stats]:
            continue
        if any(sims[y] and k in sims[y][next(iter(sims[y]))]["teams"][0] for y in years):
            stats.append((k, ref_key))
    n = {y: len(sims[y]) for y in years}
    print(f"# Year mode: {', '.join(f'{y} ({n[y]} matches)' for y in years)}\n")
    print("Each cell: sim per team-match / real that season, and its mark against the season's clubs "
          "(IN inside lowest..highest, NEAR within mean +-2 sd, OUT; - where AFL Tables did not record it).\n")
    head = "| stat | " + " | ".join(str(y) for y in years) + " |"
    print(head)
    print("|" + "---|" * (len(years) + 1))
    outs = {y: [] for y in years}
    mean = {}
    for k, rk in stats:
        cells = []
        for y in years:
            if not sims[y]:
                cells.append("-")
                continue
            v = per_match(sims[y], k)
            m = st.mean(v.values())
            se = st.stdev(v.values()) / math.sqrt(len(v)) if len(v) > 1 else 0.0
            mean[(k, y)] = (m, se)
            ref = years_ref[str(y)]["per_team_match"].get(rk)
            if not ref:
                cells.append(f"{m:.1f} / -")
                continue
            mk = mark(m, ref)
            if mk == "OUT":
                outs[y].append(k)
            cells.append(f"{m:.1f} / {ref['mean']:.1f} {mk}")
        print(f"| {k} | " + " | ".join(cells) + " |")
    for y in years:
        print(f"\nOUT in {y}: {', '.join(outs[y]) if outs[y] else 'none'}")
    if 2026 in years and len(years) > 1:
        print("\n## Shift against 2026 (sim / real, per cent)\n")
        print("| stat | " + " | ".join(str(y) for y in years if y != 2026) + " |")
        print("|" + "---|" * len(years))
        r26 = years_ref["2026"]["per_team_match"]
        for k, rk in stats:
            cells = []
            for y in years:
                if y == 2026:
                    continue
                ref = years_ref[str(y)]["per_team_match"].get(rk)
                if (k, y) not in mean or (k, 2026) not in mean or not ref or rk not in r26:
                    cells.append("-")
                    continue
                s = 100 * (mean[(k, y)][0] / mean[(k, 2026)][0] - 1)
                r = 100 * (ref["mean"] / r26[rk]["mean"] - 1)
                cells.append(f"{s:+.0f} / {r:+.0f}")
            print(f"| {k} | " + " | ".join(cells) + " |")


if __name__ == "__main__":
    main()
