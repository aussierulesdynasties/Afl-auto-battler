# SANFL scrape helper: dumps a club guide PDF's roster pages as (x, text) fragments grouped by line.
# Kept as the record of how tools/state_leagues/staging/ was made; tools/state_leagues/build.py
# rebuilds data/state_leagues/ from staging/ without them.
import sys, pypdf, json, re
# Dump roster pages as rows of (x, text) fragments, grouped by y.
path = sys.argv[1]
r = pypdf.PdfReader(path)
out = []
for pi, page in enumerate(r.pages):
    txt = page.extract_text() or ""
    if "2026 ROSTER" not in txt and "ROSTER" not in txt.upper():
        continue
    if "ROSTER" not in txt:
        continue
    frags = []
    def v(text, cm, tm, fd, fs):
        if text.strip():
            x = tm[4] * cm[0] + tm[5] * cm[2] + cm[4]
            y = tm[4] * cm[1] + tm[5] * cm[3] + cm[5]
            frags.append((round(y, 1), round(x, 1), text))
    page.extract_text(visitor_text=v)
    frags.sort(key=lambda f: (-f[0], f[1]))
    rows = []
    for y, x, t in frags:
        if rows and abs(rows[-1][0] - y) < 3:
            rows[-1][1].append((x, t))
        else:
            rows.append([y, [(x, t)]])
    print("=== PAGE", pi + 1)
    for y, items in rows:
        items.sort()
        print(f"{y:7.1f} | " + " | ".join(f"{x:.0f}:{t.strip()}" for x, t in items))
