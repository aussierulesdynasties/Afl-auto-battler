"""Hand-made ground detail (no photo pixels): grey multiplier, one tile = 4 m, 512 px. Blade/pebble speckle,
small clumps, worn patches. Mean ~0.9; the shader lifts value back by 1/mean."""
import os, sys
import numpy as np
from PIL import Image, ImageFilter
rng = np.random.default_rng(11); N = 512
def tile_noise(cells, blur):
    a = rng.random((cells, cells)); a = np.tile(a, (3, 3))
    im = Image.fromarray((a * 255).astype(np.uint8)).resize((N * 3, N * 3), Image.BICUBIC).filter(ImageFilter.GaussianBlur(blur))
    return np.asarray(im, float)[N:2 * N, N:2 * N] / 255
fine = rng.random((N, N))                       # blade / grit speckle (8 mm)
clump = tile_noise(64, 2)                       # 6 cm clumps
patch = tile_noise(8, 6)                        # 0.5 m worn / lush patches
D = 0.62 + 0.18 * fine + 0.14 * clump + 0.10 * patch
D = np.clip(D, 0, 1)
Image.fromarray((D * 255).astype(np.uint8), 'L').convert('RGB').save(os.path.join(sys.argv[1], 'ground_detail.png'))
print('ground_detail grey std', round(float((D * 255).std()), 1), 'mean', round(float(D.mean()), 3))
