"""Check a ground's land against Google Earth (proof/<slug>.md, .json).

    python3 ge_check.py <slug> <ge_elev.js> <workdir>

Reads Google Earth's height (status bar, whole metres) at the centre circle and at road spots from
ge_spots.py, OCRs it (tesseract), and compares heights relative to the centre circle with ours.
Google Earth reads the surface: a roof, tree or car under the spot reads high. A spot reading more
than 3 m ABOVE our land is counted as such and listed, not judged (bare earth cannot sit above the
surface); a spot reading lower than ours is always judged. Pass: every judged spot within 1.5 m."""
import json, os, re, subprocess, sys
import numpy as np
import terrain, ge_spots

slug, js, work = sys.argv[1], sys.argv[2], sys.argv[3]
g = terrain.grounds()[slug]; T = terrain.load(slug)
pts = ge_spots.spots(slug, 10)
out = os.path.join(work, slug); os.makedirs(out, exist_ok=True)
subprocess.run(['node', js, json.dumps(pts), str(g['lat']), str(g['lon']), out, str(T.meta['datum_source_m'])], timeout=1800)
def ocr(name):
    p = os.path.join(out, name + '.png')
    if not os.path.exists(p): return None
    t = subprocess.run(['tesseract', p, '-', '--psm', '7'], capture_output=True, text=True).stdout
    m = re.findall(r'(-?\d+)\s*m\b', t)
    return float(m[-1]) if m else None
ge = {n: ocr(n) for n, _, _ in pts}
c = ge.get('c00')
rows = []; judged = []
for n, x, y in pts[1:]:
    ours = float(T.height(x, y)); v = ge[n]
    if v is None or c is None:
        rows.append([n, x, y, None, round(ours, 2), None, 'no reading']); continue
    rel = v - c; d = ours - rel
    if d < -3.0: kind = 'surface (roof/tree/car), not judged'
    else: kind = 'judged'; judged.append(d)
    rows.append([n, x, y, rel, round(ours, 2), round(d, 2), kind])
J = np.array(judged)
res = {'ground': slug, 'source': T.meta['source'], 'licence': T.meta.get('licence', ''), 'ge_centre_m': c,
       'judged': len(J), 'spots': len(rows),
       'mean': round(float(J.mean()), 2) if len(J) else None, 'rms': round(float(np.sqrt((J ** 2).mean())), 2) if len(J) else None,
       'worst': round(float(np.abs(J).max()), 2) if len(J) else None,
       'passed': bool(len(J) >= 4 and np.abs(J).max() <= 1.5), 'rows': rows}
json.dump(res, open(f'proof/{slug}.json', 'w'), indent=1)
verdict = 'PASS' if res['passed'] else ('TOO FEW SPOTS' if len(J) < 4 else 'FAIL')
with open(f'proof/{slug}.md', 'w') as f:
    f.write(f"# {slug}: our land vs Google Earth\n\n**{verdict}.** {len(J)} judged spots of {len(rows)}; ours minus GE: mean {res['mean']} m, RMS {res['rms']} m, worst {res['worst']} m. Source: {res['licence']}.\n\n")
    f.write('Rule: every judged spot within 1.5 m (GE whole metres at the spot and the centre, plus 0.5 m). A spot where GE reads more than 3 m above our land is a roof, tree or car under the pointer and is listed, not judged.\n\n')
    f.write('| spot | x east | y north | GE rel. turf | ours | ours - GE | |\n|---|---|---|---|---|---|---|\n')
    for r in rows: f.write('| ' + ' | '.join('' if v is None else str(v) for v in r) + ' |\n')
print(slug, verdict, res['judged'], res['mean'], res['rms'], res['worst'])
