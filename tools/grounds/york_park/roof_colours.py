"""Each modelled Invermay shed's roof colour, measured: python3 roof_colours.py

The sheds neighbours.py builds without a hand-written spec took a roof from a fixed cycle. Here each one's
footprint is laid on the Esri World Imagery tile (surrounds.ortho, 1 m a pixel), the pixels well inside it
(1.5 m in from the edge) give a median colour, and the nearest of our painted roof sheets by that colour is
kept. Only the chosen sheet's name is written (neighbours_roofs.json); no imagery is kept or shipped.
"""
import json, os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import surrounds as SR   # noqa: E402

SHEETS = ('roof_pale', 'roof_white', 'roof_grey', 'roof_rust', 'roof_red', 'roof_flat')


def sheet_colours():
    out = {}
    for s in SHEETS:
        a = np.asarray(Image.open(os.path.join(HERE, 'model', 'tex', s + '.png')).convert('RGB'), float)
        out[s] = np.median(a.reshape(-1, 3), axis=0)
    return out


def main():
    foot = json.load(open(os.path.join(HERE, 'neighbours_osm.json')))
    M, r = SR.ortho()
    H, W = M.shape[:2]
    cols = sheet_colours()
    res = {}
    for b in foot:
        pts = [((e + r), (r - n)) for e, n in b['pts']]
        mask = Image.new('L', (W, H), 0); ImageDraw.Draw(mask).polygon(pts, fill=255)
        mask = np.asarray(mask.filter(ImageFilter.MinFilter(5))) > 0      # 2 px (about 1.5 m) in from the edge
        if mask.sum() < 30:
            continue
        med = np.median(M[mask], axis=0)
        # Aerial colour runs darker and greyer than a sheet's albedo: compare chroma and relative lightness.
        def d(c):
            return float(np.linalg.norm((med / med.mean()) - (c / c.mean())) * 2.0 + abs(np.log(med.mean() / c.mean())) * 0.6)
        if med[0] / med[1] > 1.15:      # a red or rust roof: the aerial bleaches its colour, so the hue decides
            best = 'roof_red' if med[1] / med[2] < 1.05 and med[0] > 150 else 'roof_rust'
        else:
            best = min((s for s in cols if s not in ('roof_red', 'roof_rust')), key=lambda s: d(cols[s]))
        res['b_%d_%d' % (round(b['c'][0]), round(b['c'][1]))] = {'sheet': best, 'median_rgb': [round(x) for x in med]}
    json.dump(res, open(os.path.join(HERE, 'neighbours_roofs.json'), 'w'), indent=0)
    from collections import Counter
    print(len(res), 'footprints;', Counter(v['sheet'] for v in res.values()))


if __name__ == '__main__':
    main()
