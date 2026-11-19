import numpy as np, sys, cv2
from PIL import Image
Image.MAX_IMAGE_PIXELS=None
CODE, CELL, ATLAS = sys.argv[1], int(sys.argv[2]), sys.argv[3]
GX = 4
def filled(side, erode=5):
    im = np.array(Image.open(f'design_{CODE}_{side}.png').convert('RGBA')).astype(np.float32)
    a = im[..., 3] > 250                       # fully opaque only: no anti-aliased edge
    a = cv2.erode(a.astype(np.uint8), np.ones((2*erode+1,)*2, np.uint8)) > 0
    from scipy import ndimage
    _, (iy, ix) = ndimage.distance_transform_edt(~a, return_indices=True)
    rgb = im[..., :3][iy, ix]
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
