"""Print the estimated shard seconds; after a run, report observed shard imbalance (a warning, never a failure).

The layout is tools/ci_shards.py's: a suite with no timing yet counts as DEFAULT_SECONDS.
"""
import argparse
import json
import pathlib
import sys

from ci_shards import DEFAULT_SECONDS, ROOT, layout, timings


def check(root=ROOT, observed=None):
    shards, _notes, errors = layout(root)
    for error in errors:
        print(f"::error::{error}")
    if errors:
        return False
    times = timings(root)
    groups = {key: names for key, names in shards if names}
    totals = {key: sum(times.get(s, DEFAULT_SECONDS) for s in names) for key, names in groups.items()}
    baseline = json.loads((root / "tools/ci_suite_timings.json").read_text()) if (root / "tools/ci_suite_timings.json").exists() else {}
    print(f"Estimated shard seconds: {totals}; source run {baseline.get('source_run')}, measured {baseline.get('measured_on')}")
    if observed:
        # The shards that ran are tools/ci_shards.py --matrix's, packed per run (not the
        # ci_shards.txt groups above), so each observed shard is compared with the estimate
        # for the suites its own timing file lists.
        rows = []
        drift = []
        for file in sorted(pathlib.Path(observed).glob("shard-*.tsv"), key=lambda f: int(f.stem.split("-")[1])):
            suites = [line.split("\t") for line in file.read_text().splitlines() if line.strip()]
            if not suites:
                continue
            est = sum(times.get(s, DEFAULT_SECONDS) for s, _ in suites)
            got = sum(int(sec) for _, sec in suites)
            rows.append((file.stem, est, got))
            drift.extend((s, times.get(s, DEFAULT_SECONDS), int(sec)) for s, sec in suites)
        print("Observed shards (estimated -> actual suite seconds): "
              + ", ".join(f"{k} {e}->{a}" for k, e, a in rows))
        if len(rows) >= 2:
            mean = sum(a for _, _, a in rows) / len(rows)
            worst = max(rows, key=lambda r: r[2])
            if worst[2] > mean * 1.35:
                print(f"::warning::{worst[0]} took {worst[2]} s, over 135% of the {mean:.0f} s average. Re-plan the "
                      "timings with tools/plan_ci_shards.py. Runner variability means this alone fails nothing.")
            off = [(k, e, a) for k, e, a in rows if e and abs(a - e) > max(60, 0.25 * e)]
            if off:
                print("::warning::Shards more than 25% off their estimate (stale tools/ci_suite_timings.json): "
                      + ", ".join(f"{k} {e}->{a}" for k, e, a in off))
        # The suites behind a shard's miss: the ones to re-time (artifacts cannot be read everywhere).
        moved = sorted((r for r in drift if abs(r[2] - r[1]) > max(30, 0.25 * r[1])), key=lambda r: -abs(r[2] - r[1]))
        if moved:
            print("Suites off their timing (estimated -> actual s): "
                  + ", ".join(f"{s} {e}->{a}" for s, e, a in moved))
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--observed")
    args = parser.parse_args()
    sys.exit(0 if check(observed=args.observed) else 1)
