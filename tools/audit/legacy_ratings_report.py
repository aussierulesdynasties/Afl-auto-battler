"""Read the legacy_ratings audit dump and list the players it rates against
their real standing (director 2026-11-15: "audit every legacy player to make
sure theyre rated properly and in the right positions").

  godot --headless --path . --script tools/audit/run_audit.gd -- legacy_ratings_impl > dump.txt
  python tools/audit/legacy_ratings_report.py dump.txt

For each start it prints the role counts, the overall spread per role among
regulars (12+ games), every player honoured (All-Australian, team of the
year or club best and fairest) in the three seasons before the start or the
start season itself who rates below his role's median (an honour in the
start season is one the game cannot know yet: a hint, not a fault), and every player whose
game role differs from his listed position in data/legacy/positions.csv.
Reads; changes nothing.
"""
import csv
import os
import sys
from collections import Counter, defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HON = os.path.join(ROOT, "data", "legacy", "honours")
POS_LINE = {"FWD": "FWD", "MID": "MID", "DEF": "DEF", "RUC": "RUCK"}


def norm(s):
    return "".join(c for c in s.lower() if c.isalpha())


def honours():
    """{name key: [(year, label)]}."""
    out = defaultdict(list)
    for fname, label in (("all_australian.csv", "AA"), ("team_of_the_year.csv", "TOTY"), ("club_bf.csv", "B&F")):
        with open(os.path.join(HON, fname), encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                out[norm(r["first"] + r["last"])].append((int(r["year"]), label))
    return out


def listed():
    """{name key: pos} from positions.csv, leaving out a name two players
    share (the dump has no birth date to tell Josh Kennedy from Josh Kennedy)."""
    path = os.path.join(ROOT, "data", "legacy", "positions.csv")
    out, seen = {}, Counter()
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                k = norm(r["first"] + r["last"])
                seen[k] += 1
                if r.get("pos"):
                    out[k] = POS_LINE.get(r["pos"], r["pos"])
    return {k: v for k, v in out.items() if seen[k] == 1}


def pct(v, q):
    return v[min(len(v) - 1, int(len(v) * q))]


def main(path):
    rows = defaultdict(list)
    with open(path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if not line.startswith("ROW "):
                continue
            f = line[4:].rstrip("\n").split("|")
            rows[f[0]].append({"id": f[1], "club": f[2], "name": f[3], "age": int(f[4]), "role": f[5],
                               "ovr": int(f[7]), "gm": int(f[10]), "gl": int(f[11]), "flags": f[13]})
    hon, pos = honours(), listed()
    for start in sorted(rows):
        ps, y = rows[start], int(start)
        print("== %s: %d players, roles %s" % (start, len(ps), dict(Counter(p["role"] for p in ps))))
        med = {}
        for role in ("MID", "DEF", "FWD", "RUCK"):
            v = sorted(p["ovr"] for p in ps if p["role"] == role and p["gm"] >= 12)
            if v:
                med[role] = pct(v, 0.5)
                print("  %-4s regulars %3d  p25 %d  median %d  p90 %d" % (role, len(v), pct(v, .25), med[role], pct(v, .9)))
        low = []
        for p in ps:
            h = [f"{lab} {yr}" for yr, lab in hon.get(norm(p["name"]), []) if y - 3 <= yr <= y]
            if h and p["ovr"] < med.get(p["role"], 0):
                low.append((p["ovr"], p, h))
        print("  honoured, below role median: %d" % len(low))
        for o, p, h in sorted(low, key=lambda t: t[0]):
            print("    %-24s %s %-4s %2d  %2d gm %3d gl  %s %s" % (p["name"], p["club"], p["role"], o, p["gm"], p["gl"],
                                                              ", ".join(h), p["flags"]))
        off = [p for p in ps if pos.get(norm(p["name"])) and pos[norm(p["name"])] != p["role"]]
        print("  role differs from listed position: %d" % len(off))
        for p in sorted(off, key=lambda p: -p["ovr"])[:40]:
            print("    %-24s %s listed %-4s plays %-4s %2d" % (p["name"], p["club"], pos[norm(p["name"])], p["role"], p["ovr"]))


if __name__ == "__main__":
    main(sys.argv[1])
