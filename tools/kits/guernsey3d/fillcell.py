import numpy as np, sys, cv2, os
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
CODE, CELL, ATLAS = sys.argv[1], int(sys.argv[2]), sys.argv[3]
GX = 4
def filled(side, erode=5):
    im = np.array(Image.open(f'design_{CODE}_{side}.png').convert('RGBA')).astype(np.float32)
    a = im[..., 3] > 250                       # fully opaque only: no anti-aliased edge
    a = cv2.erode(a.astype(np.uint8), np.ones((2*erode+1,)*2, np.uint8)) > 0
    from scipy import ndimage
    rgb = im[..., :3].copy()
    if os.environ.get('COLFILL'):
        # above the cloth's top and below its hem, each column carries its own edge colour straight on: the
        # body past the photo's top edge (the shoulder by the neck) and under the hem shows the panel it
        # continues, not a colour pulled in on a slant from the nearest panel
        for c in np.nonzero(a.any(0))[0]:
            ys = np.nonzero(a[:, c])[0]
            rgb[:ys[0], c] = rgb[ys[0], c]; rgb[ys[-1] + 1:, c] = rgb[ys[-1], c]
            a[:ys[0], c] = True; a[ys[-1] + 1:, c] = True
    _, (iy, ix) = ndimage.distance_transform_edt(~a, return_indices=True)
    rgb = rgb[iy, ix]
    return np.clip(rgb, 0, 255).astype(np.uint8)
at = np.array(Image.open(ATLAS).convert('RGB'))
c = at.shape[1] // (GX * 2)
r, k = divmod(CELL, GX)
for j, side in enumerate(('front', 'back')):
    f = cv2.resize(filled(side), (c, c), interpolation=cv2.INTER_AREA)
    old = at[r*c:(r+1)*c, (k*2+j)*c:(k*2+j+1)*c]
    print(side, 'mean abs diff vs old', np.abs(old.astype(int) - f.astype(int)).mean())
    at[r*c:(r+1)*c, (k*2+j)*c:(k*2+j+1)*c] = f
Image.fromarray(at).save(ATLAS)
Image.fromarray(at[r*c:(r+1)*c, k*2*c:(k*2+2)*c]).save(f'z_cell_{CODE}.png')
