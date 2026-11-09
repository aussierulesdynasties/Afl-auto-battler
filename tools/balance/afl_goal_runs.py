"""Real AFL goal sequences from AFL Tables' scoring progressions (audit 29).

Fetches each season page, then each match page's "Scoring progression" table, and writes
tools/balance/afl_goal_runs.json: for every match, its goal order as a string ("H" home goal,
"A" away goal, "|" a quarter break) and the final scores. Behinds are left out: a run of goals is
unanswered goals, as the game counts it (MatchSim._run).

    python -I tools/balance/afl_goal_runs.py --years 2024 2025 --cache <dir>

Pages are cached in --cache and fetched a second apart. Measurement data only.
"""
import argparse
import json
import os
import re
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
UA = {"User-Agent": "Mozilla/5.0 (aussie-rules-dynasties balance research)"}


def get(url, cache, name):
    path = os.path.join(cache, name)
    if os.path.exists(path):
        return open(path, encoding="utf-8").read()
    html = urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read().decode("latin-1")
    open(path, "w", encoding="utf-8").write(html)
    time.sleep(1.0)
    return html


def parse(html):
    """The goal order from one match page, or None when it has no scoring progression."""
    i = html.rfind("Scoring progression")
    if i < 0:
        return None
    body = html[i:]
    end = body.find("</table>")
    body = body[:end] if end > 0 else body
    seq = []
    for row in re.split(r"<tr>", body):
        if "quarter" in row and "colspan=5" in row:
            if seq:
                seq.append("|")
            continue
        cells = re.findall(r"<td[^>]*>(.*?)(?=<td|</tr>|$)", row, re.S)
        if len(cells) < 5:
            continue
        home, away = re.sub(r"<[^>]+>", "", cells[0]), re.sub(r"<[^>]+>", "", cells[4])
        if home.strip().endswith("goal"):
            seq.append("H")
        elif away.strip().endswith("goal"):
            seq.append("A")
    final = re.findall(r"(\d+)\.(\d+)\.<b>(\d+)</b> - (\d+)\.(\d+)\.<b>(\d+)", body)
    if not final:
        return None
    hg, _, hs, ag, _, as_ = (int(x) for x in final[-1])
    s = "".join(seq).strip("|")
    # Keep a match only when the goals read off the rows add up to the final score.
    if s.count("H") != hg or s.count("A") != ag:
        return None
    return {"seq": s, "h": hs, "a": as_}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--years", nargs="+", type=int, default=[2024, 2025])
    ap.add_argument("--cache", required=True)
    ap.add_argument("--out", default=os.path.join(HERE, "afl_goal_runs.json"))
    o = ap.parse_args()
    os.makedirs(o.cache, exist_ok=True)
    games = []
    for y in o.years:
        season = get(f"https://afltables.com/afl/seas/{y}.html", o.cache, f"seas_{y}.html")
        links = list(dict.fromkeys(re.findall(r'href="\.\./stats/games/%d/([0-9]+\.html)"' % y, season)))
        for name in links:
            g = parse(get(f"https://afltables.com/afl/stats/games/{y}/{name}", o.cache, f"{y}_{name}"))
            if g and g["seq"]:
                g["id"] = f"{y}/{name[:-5]}"
                games.append(g)
        print(y, len(links), "pages", len(games), "games so far", flush=True)
    json.dump({"source": "AFL Tables scoring progressions (afltables.com/afl/stats/games), "
               "home-and-away and finals", "years": o.years, "games": games},
              open(o.out, "w", encoding="utf-8"), indent=0)
    print("wrote", o.out, len(games))


if __name__ == "__main__":
    main()
