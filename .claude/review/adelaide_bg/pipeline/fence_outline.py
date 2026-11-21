# fence_mask.npy (0.5 m grid, +-260 m, filled, 2 m past the model) -> its outline as one smooth ring (scene frame metres),
# for the exact boolean trim in scene.py. Contour at the 0.5 level, then a 1 m open/close and a 0.2 m simplify take out the pixel steps.
import json, sys
import numpy as np
from skimage import measure
from shapely.geometry import Polygon
m = np.load(sys.argv[1]).astype(float); S, R = 0.5, 260.0
C = max(measure.find_contours(np.pad(m, 1), 0.5), key=len) - 1   # (row, col) in px
ring = [((c + 0.5) * S - R, R - (r + 0.5) * S) for r, c in C]
g = Polygon(ring).buffer(1.0).buffer(-1.0).simplify(0.2)
g = max(g.geoms, key=lambda q: q.area) if hasattr(g, 'geoms') else g
out = [[round(x, 3), round(y, 3)] for x, y in list(g.exterior.coords)[:-1]]
json.dump(out, open(sys.argv[2], 'w')); print('outline', len(out), 'pts, area', round(g.area), 'mask area', m.sum() * S * S)
