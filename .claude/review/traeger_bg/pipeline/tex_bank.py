# Hand-made embankment cover: rough grass with dry patches and bare earth, 512 px = 8 m tile, seamless.
import numpy as np, sys
from PIL import Image
rng = np.random.default_rng(11); N = 512
def fbm(oct_):
    out = np.zeros((N, N))
    for o in range(oct_):
        f = 4 * 2 ** o; g = rng.standard_normal((f, f))
        k = np.fft.fft2(g, s=(f, f)); up = np.real(np.fft.ifft2(np.pad(np.fft.fftshift(k), ((N - f) // 2,) * 2)))  # band-limited, tiles
        up = np.fft.ifftshift(up) if False else up
        out += np.kron(g, np.ones((N // f, N // f))) * 0 + np.real(np.fft.ifft2(np.fft.ifftshift(np.pad(np.fft.fftshift(np.fft.fft2(g)), ((N - f) // 2, (N - f) // 2))))) * (0.55 ** o) * N / f
    return (out - out.mean()) / out.std()
big = fbm(4); fine = rng.standard_normal((N, N))
green = np.array([88, 112, 58]); dry = np.array([140, 130, 82]); earth = np.array([112, 96, 74])
t_dry = np.clip((big - 0.8) * 0.9, 0, 1)[..., None]; t_earth = np.clip((big - 2.0) * 1.5, 0, 1)[..., None]
c = green * (1 - t_dry) + dry * t_dry; c = c * (1 - t_earth) + earth * t_earth
blades = np.clip(fine, -2, 2)[..., None] * 9
img = np.clip(c + blades, 0, 255).astype(np.uint8)
Image.fromarray(img).save(sys.argv[1]); print('std', img.std())
