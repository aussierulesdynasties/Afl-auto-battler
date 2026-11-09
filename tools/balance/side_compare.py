"""Paired margin of side i%2 (the side tools/balance.sh's --coach and --side-plan set),
arm B against arm A on the same seeds: python3 side_compare.py <run dir>."""
import glob, json, math, sys

D = sys.argv[1]
KEYS = ["tackles", "clangers", "frees_against", "metres_gained", "inside50", "clearances", "goals", "score"]


def load(arm):
    d = {}
    for f in glob.glob(f"{D}/{arm}_*.jsonl"):
        for line in open(f):
            if line.strip().endswith("}"):
                o = json.loads(line)
                d[o["i"]] = (o["teams"][o["i"] % 2], o["teams"][1 - o["i"] % 2])
    return d


A, B = load("a"), load("b")
ids = [i for i in B if i in A]
if len(ids) < 2:
    sys.exit("side_compare: no paired matches")
dm = [(B[i][0]["score"] - B[i][1]["score"]) - (A[i][0]["score"] - A[i][1]["score"]) for i in ids]
m = sum(dm) / len(dm)
se = math.sqrt(sum((x - m) ** 2 for x in dm) / (len(dm) - 1) / len(dm))
win = lambda t: 1 if t[0]["score"] > t[1]["score"] else 0.5 if t[0]["score"] == t[1]["score"] else 0
wa = sum(win(A[i]) for i in ids) / len(ids)
wb = sum(win(B[i]) for i in ids) / len(ids)
st = []
for k in KEYS:
    x = sum(A[i][0].get(k, 0) for i in ids) / len(ids)
    y = sum(B[i][0].get(k, 0) for i in ids) / len(ids)
    if x:
        st.append(f"{k} {100 * (y / x - 1):+.1f}%")
print(f"b (v a) n={len(ids)} margin {m:+.2f} se {se:.2f} win {100 * wa:.1f}->{100 * wb:.1f} | " + " ".join(st))
