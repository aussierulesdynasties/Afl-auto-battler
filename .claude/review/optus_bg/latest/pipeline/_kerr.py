# kiosk slab edge error: model outline vs Canny edges of aerial lightness (sigma 2 px) within 3 m of the slab
import json, numpy as np
from PIL import Image
from skimage import color, feature
from scipy import ndimage as ndi
from shapely.geometry import Polygon
R = 0.125; AX0, AY1 = 80, 135
L = color.rgb2lab(np.asarray(Image.open('data/optus/sat_hi_plaza.png').convert('RGB')) / 255.0)[..., 0]
ed = feature.canny(L, sigma=2); dd = ndi.distance_transform_edt(~ed) * R
H = json.load(open('spec/optus_fc_hand.json'))
for bi in (12, 13):
    r = Polygon(H['bands'][bi]['pts']).exterior
    ev = [dd[int((AY1 - y) / R), int((x - AX0) / R)] for x, y in (r.interpolate(t).coords[0] for t in np.linspace(0, r.length, 600))]
    print('F%d edge error vs aerial edges: median %.2f p90 %.2f max %.2f m' % (bi, np.median(ev), np.percentile(ev, 90), max(ev)))
