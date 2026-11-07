"""Turn audit.yml logs of tools/audit/balance_match_impl.gd into a balance.sh run.

    python tools/balance/from_audit.py --run .balance/gh-x --arm a run_1/audit.log run_2/audit.log
    python tools/balance/from_audit.py --run .balance/gh-x --arm b run_3/audit.log ...
    python tools/balance/balance_report.py --run .balance/gh-x --a main --b branch

Each "BAL <json>" line becomes one row of <run>/<arm>_<k>.jsonl (k = the log's
position), so the report pairs the arms seed by seed as it does a local run.
"""
import argparse, json, os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--arm", required=True, choices=["a", "b"])
    ap.add_argument("logs", nargs="+")
    o = ap.parse_args()
    os.makedirs(o.run, exist_ok=True)
    open(os.path.join(o.run, ".gdignore"), "a").close()
    total = 0
    for k, log in enumerate(o.logs):
        n = 0
        with open(log, encoding="utf-8", errors="replace") as fh, \
                open(os.path.join(o.run, f"{o.arm}_{k}.jsonl"), "w", encoding="utf-8") as out:
            for line in fh:
                if line.startswith("BAL {"):
                    json.loads(line[4:])
                    out.write(line[4:].rstrip("\n") + "\n")
                    n += 1
        print(f"{log}: {n} matches")
        total += n
    print(f"arm {o.arm}: {total} matches into {o.run}")


if __name__ == "__main__":
    main()
