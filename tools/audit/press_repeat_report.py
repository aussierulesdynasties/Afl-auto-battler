"""Collects press_repeat_impl logs into the tables of the 19/60 evidence doc.

Usage: python tools/audit/press_repeat_report.py <audit.log> [<audit.log> ...]
Prints markdown: per-season pressers and question/note variety (averaged over
seeds), and the repeat offenders by data id with their counts and gaps.
"""
import re
import sys
from collections import defaultdict
from statistics import median


def parse(paths):
    seasons, gaps, summaries = [], [], []
    for p in paths:
        for line in open(p, encoding="utf-8", errors="replace"):
            line = line.rstrip("\n")
            if line.startswith("PR_SEASON "):
                t = line.split()
                d = {t[i]: t[i + 1] for i in range(1, len(t) - 1, 2)}
                seasons.append(d)
            elif line.startswith("PR_GAPS "):
                m = re.match(r"PR_GAPS seed (\d+) kind (\w) id (\S+) count (\d+) gaps (\S+) text (.*)", line)
                if m:
                    g = [] if m.group(5) == "-" else [int(x) for x in m.group(5).split(",")]
                    gaps.append({"seed": int(m.group(1)), "kind": m.group(2), "id": m.group(3),
                                 "count": int(m.group(4)), "gaps": g, "text": m.group(6)})
            elif line.startswith("SUMMARY "):
                summaries.append(line)
    return seasons, gaps, summaries


def main():
    seasons, gaps, summaries = parse(sys.argv[1:])
    seeds = sorted({int(s["seed"]) for s in seasons})
    by_idx = defaultdict(list)
    first_year = {}
    for s in seasons:
        sd = int(s["seed"])
        first_year.setdefault(sd, int(s["year"]))
        by_idx[int(s["year"]) - first_year[sd] + 1].append(s)
    print(f"Seeds: {len(seeds)} ({', '.join(map(str, seeds))})\n")
    print("| Season | Careers | Games | Pressers | Questions distinct / asked | Repeats | Notes distinct / shown |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    for i in sorted(by_idx):
        rows = by_idx[i]
        n = len(rows)
        avg = lambda k: sum(int(r[k]) for r in rows) / n
        print(f"| {i} | {n} | {avg('games'):.1f} | {avg('pressers'):.1f} | {avg('q_distinct'):.1f} / {avg('q_total'):.1f}"
              f" | {avg('q_repeats'):.1f} | {avg('notes_distinct'):.1f} / {avg('notes_total'):.1f} |")
    for kind, name in (("q", "Press questions (qid)"), ("n", "Coaching notes (text, numbers as #)")):
        pooled = defaultdict(lambda: {"count": 0, "gaps": [], "seeds": 0, "text": ""})
        for g in gaps:
            if g["kind"] != kind:
                continue
            p = pooled[g["id"]]
            p["count"] += g["count"]
            p["gaps"] += g["gaps"]
            p["seeds"] += 1
            p["text"] = p["text"] or g["text"]
        total = sum(p["count"] for p in pooled.values())
        print(f"\n### {name}: {len(pooled)} distinct, {total} shown over all careers\n")
        print("| Id | Times (all careers) | Per career | Share | Median gap (rounds) | Shortest gap | Example |")
        print("| --- | --- | --- | --- | --- | --- | --- |")
        for k, p in sorted(pooled.items(), key=lambda kv: -kv[1]["count"])[:25]:
            mg = f"{median(p['gaps']):.0f}" if p["gaps"] else "-"
            sg = str(min(p["gaps"])) if p["gaps"] else "-"
            ex = p["text"][:90].replace("|", "/")
            print(f"| `{k}` | {p['count']} | {p['count'] / len(seeds):.1f} | {100 * p['count'] / max(1, total):.1f}% | {mg} | {sg} | {ex} |")
    print("\n```")
    for s in summaries:
        print(s)
    print("```")


if __name__ == "__main__":
    main()
