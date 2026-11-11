# SANFL scrape helper: turns rows.py's positioned PDF fragments into roster records (rosters.json).
# Kept as the record of how tools/state_leagues/staging/ was made; tools/state_leagues/build.py
# rebuilds data/state_leagues/ from staging/ without them.
import re, glob, json, os, sys
# Parse rows_*.txt (positioned fragments) into roster records.
HDRS = ["#", "First", "Last", "DOB", "Age", "Cm", "L Gm", "L Gl", "AFL"]
PAT = {
    "#": r"^\d{1,3}$", "First": r"^[A-Za-z][A-Za-z'\-\. ]*$", "Last": r"^[A-Za-z][A-Za-z'\-\. ]*$",
    "DOB": r"^\d{1,2}/\d{1,2}/\d{4}$", "Age": r"^\d{2}$", "Cm": r"^\d{3}$",
    "L Gm": r"^\d{1,3}$", "L Gl": r"^\d{1,3}$", "AFL": r"^[yY]$",
}
out = {}
for f in sorted(glob.glob(os.path.join(sys.argv[1], "rows_*.txt"))):
    club = os.path.basename(f)[5:-4]
    recs = []
    hdr = None
    for line in open(f, encoding="utf-8", errors="replace"):
        if line.startswith("==="):
            hdr = None
            continue
        parts = line.rstrip("\n").split(" | ")
        frags = []
        for p in parts[1:]:
            m = re.match(r"^(-?\d+):(.*)$", p)
            if m:
                frags.append((int(m.group(1)), m.group(2).strip()))
        texts = [t for _, t in frags]
        if "First" in texts and "Last" in texts and "DOB" in texts:
            hdr = {t: x for x, t in frags if t in HDRS}
            continue
        if not hdr or not frags:
            continue
        maxx = max(hdr.values()) + 40
        row = {}
        for x, t in frags:
            if x > maxx:
                continue
            col = min(hdr, key=lambda h: abs(hdr[h] - x))
            # dates sit left of the DOB header; first/last left-aligned
            if re.match(PAT["DOB"], t):
                col = "DOB"
            if not re.match(PAT[col], t):
                continue
            if col in row:
                continue
            row[col] = t
        if "First" in row and "Last" in row and "DOB" in row:
            recs.append(row)
    out[club] = recs
    print(club, len(recs), file=sys.stderr)
json.dump(out, open(os.path.join(sys.argv[1], "rosters.json"), "w"), indent=1)
