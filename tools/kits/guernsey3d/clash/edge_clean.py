"""Take the photo's neck and armhole bindings off a traced clash design, so the shader draws them clean on the
cut's own edges (data/kits_clash.csv collar / armholes, in the photo's colour).

    python edge_clean.py CODE side WIDTH [#colour ...] [--above ROW]      (work folder, after trace_clash.py)

Why: the photo's bindings land on the cut only roughly (the warp fits outlines, not seams), so traced they show
as ragged patches inside the cloth by the armpits and neck, and the atlas fill carries their colour on over the
shoulder seam. Only above the armpit (or ROW): below it the side seams keep the design as traced.
- No colours: every pixel within WIDTH of the cloth's edge (the neck, the shoulder, the armhole, a lining hole)
  takes the colour of the nearest pixel further in than that.
- Colours (the binding's, or the lining's): within WIDTH of the edge, only pixels of those colours are
  replaced, by the nearest pixel of any other colour, so the design's own panels that run to the edge stay."""
import os, sys
import numpy as np
from PIL import Image
from scipy import ndimage as nd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from warp_clash import cut_armpit, cut_mask

args = sys.argv[1:]
above = None
if '--above' in args:
    i = args.index('--above'); above = int(args[i + 1]); del args[i:i + 2]
code, side, width = args[0], args[1], float(args[2])
cols = [np.array([int(c[k:k + 2], 16) for k in (1, 3, 5)]) for c in args[3:]]
fn = f'design_{code}_{side}.png'
a = np.array(Image.open(fn).convert('RGBA'))
cloth = a[..., 3] > 0
d = nd.distance_transform_edt(cloth)
arm = above if above is not None else cut_armpit(cut_mask(code, 'front')) + 30
if cols:
    rgb = a[..., :3].astype(int)
    match = np.zeros(cloth.shape, bool)
    for c in cols:
        match |= np.abs(rgb - c).sum(-1) < 70
    match = nd.binary_dilation(match, iterations=3)   # and the anti-aliased fringe the trace left round them
    band = cloth & match & (d <= width)
    band[arm:] = False
    keep = cloth & ~band
else:
    keep = cloth & (d > width)
    band = cloth & ~keep
    band[arm:] = False
    keep = cloth & ~band
_, (iy, ix) = nd.distance_transform_edt(~keep, return_indices=True)
a[band, :3] = a[iy[band], ix[band], :3]
Image.fromarray(a).save(fn)
print(code, side, 'edge band recoloured', int(band.sum()), 'px above row', arm)
