#!/usr/bin/env python3
"""Draft-class data check: data/draftees_2026.csv's header, ranks, names,
positions, states, heights, birth dates and under-18 stats.

The Python mirror of the old projection, development and rollover maths went
with the old rating code (docs/RATING_REBUILD.md): a draftee is now his type's
ranges at his talent, tested in GDScript (tests/test_intake.gd).

Usage:  python3 tools/intake_harness.py [--quiet]
"""
import argparse
import csv
from datetime import date
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")


def load_class(quiet=False):
    path = os.path.join(DATA, "draftees_2026.csv")
    errors = []
    rows = []
    with open(path, newline="") as f:
        rdr = csv.DictReader(f)
        expect = ["rank", "first", "last", "pos", "pos2", "pos_detail", "height_cm", "dob",
                  "state", "team", "league", "tied_club", "tied_type", "u18_gm", "u18_di",
                  "u18_gl", "u18_mk", "u18_tk", "u18_if50", "u18_ho", "note", "data_src"]
        if rdr.fieldnames != expect:
            errors.append("header mismatch: %s" % rdr.fieldnames)
        ranks = set()
        names = set()
        for r in rdr:
            rows.append(r)
            for col in ("note", "team", "first", "last"):
                if "," in (r.get(col) or ""):
                    errors.append("comma in %s: %r" % (col, r[col]))
            rk = int(r["rank"])
            if rk in ranks:
                errors.append("duplicate rank %d" % rk)
            ranks.add(rk)
            nm = (r["first"] + " " + r["last"]).lower()
            if nm in names:
                errors.append("duplicate name %s" % nm)
            names.add(nm)
            if r["pos"] not in ("MID", "DEF", "FWD", "RUC"):
                errors.append("bad pos %s" % r["pos"])
            if r["state"] not in ("SA", "WA", "VICM", "VICC", "QLD", "NSW", "TAS"):
                errors.append("bad state %s" % r["state"])
            h = int(r["height_cm"])
            if not 165 <= h <= 212:
                errors.append("implausible height %d for %s %s" % (h, r["first"], r["last"]))
            if r["dob"]:
                d = date(*map(int, r["dob"].split("-")))
                # A mature-age man taken at the real draft (afl-draft-nov26:
                # Wright, Johnston, Riding) is older than an U18 class.
                oldest = date(1998, 1, 1) if r.get("data_src") == "afl-draft-nov26" else date(2006, 1, 1)
                if not (oldest <= d <= date(2009, 6, 30)):
                    errors.append("dob out of class range: %s" % r["dob"])
            for k in ("u18_di", "u18_gl", "u18_mk", "u18_tk", "u18_if50", "u18_ho"):
                v = float(r[k])
                if v < 0 or v > 45:
                    errors.append("bad %s=%s" % (k, r[k]))
    rows.sort(key=lambda r: int(r["rank"]))
    if not quiet:
        print("CSV: %d rows; header/schema %s" % (len(rows), "OK" if not errors else "FAILED"))
    return rows, errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    rows, fails = load_class(args.quiet)
    rucks = [r for r in rows if r["pos"] == "RUC"]
    if len(rucks) < 3:
        fails.append("too few rucks in the class: %d" % len(rucks))
    if fails:
        print("FAILURES (%d):" % len(fails))
        for e in fails:
            print("  -", e)
        sys.exit(1)
    print("draft-class data: all checks passed (%d prospects, %d rucks)" % (len(rows), len(rucks)))


if __name__ == "__main__":
    main()
