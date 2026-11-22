# Hand-made track textures (no photo pixels). Colours measured from the MCG aerial over the Jolimont yard:
# ballast median sRGB (104, 87, 80), 20th pct (91, 74, 68), 80th pct (116, 100, 93) -> rust-brown with grey stones.
#   argv[1] = track bed: 4.6 m across (256 px) x 5.2 m along (288 px), 8 concrete sleepers at 0.65 m, two 1.6 m-gauge rails
#   argv[2] = ballast only (same stones, no sleepers), 4 m x 4 m tile (256 px), fills the yard between tracks
import numpy as np, sys
from PIL import Image
rng = np.random.default_rng(7)

def stones(H, W, n):
    gy, gx = np.mgrid[0:H, 0:W]
    pts = rng.uniform([0, 0], [H, W], (n, 2))
    # each stone: rust-brown or blue-grey granite, tones spread to the aerial's 20-80th percentile
    kind = rng.random(n) < 0.35
    col = np.where(kind[:, None], np.array([128, 123, 119]), np.array([132, 104, 92])) / 255
    col = col * rng.uniform(0.82, 1.14, (n, 1))
    best = np.full((H, W), 1e9); second = np.full((H, W), 1e9); idx = np.zeros((H, W), int)
    for k, (py, px) in enumerate(pts):
        dy = np.minimum(abs(gy - py), H - abs(gy - py)); dx = np.minimum(abs(gx - px), W - abs(gx - px)); d = dy * dy + dx * dx
        m = d < best; second = np.where(m, best, np.minimum(second, d)); idx = np.where(m, k, idx); best = np.where(m, d, best)
    edge = np.clip((np.sqrt(second) - np.sqrt(best)) / 1.6, 0, 1)
    img = col[idx] * (0.62 + 0.38 * edge[..., None])
    img *= (1 + 0.04 * rng.standard_normal((H, W, 1)))
    return img, gx

def save(img, path):
    a = (np.clip(img, 0, 1) * 255).astype(np.uint8); Image.fromarray(a).save(path)
    print(path, a.shape[1], 'x', a.shape[0], 'mean', a.reshape(-1, 3).mean(0).round(), 'std', a.std().round(1))

# track bed
W, H = 256, 288; ppm = W / 4.6
img, gx = stones(H, W, 5200)
sl_w = int(2.6 * ppm); sl_h = max(3, int(0.26 * ppm)); x0 = (W - sl_w) // 2
for s in range(8):   # concrete sleepers every 0.65 m, pale weathered grey, shadow on the far edge
    y0 = int(s * H / 8 + (H / 8 - sl_h) / 2)
    blk = np.array([150, 146, 139]) / 255 * (1 + 0.04 * rng.standard_normal((sl_h, sl_w, 1)))
    img[y0:y0 + sl_h, x0:x0 + sl_w] = blk
    img[y0 + sl_h:y0 + sl_h + 2, x0:x0 + sl_w] *= 0.6
for rx in (-0.8, 0.8):   # rust stain each side of the rail, then the rail itself: dark web, bright worn head
    cx = W / 2 + rx * ppm
    img *= (1 - 0.22 * np.exp(-((gx - cx) / 7) ** 2))[..., None] * np.array([1, 0.97, 0.94])
    c = int(round(cx)); img[:, c - 3:c + 3] = np.array([70, 62, 56]) / 255; img[:, c - 1:c + 2] = np.array([196, 198, 200]) / 255
save(img, sys.argv[1])
# ballast only
W = H = 256
img, _ = stones(H, W, 6400)
save(img, sys.argv[2])
