"""Heights from the open Terrarium elevation tiles (Mapzen / AWS open data: SRTM and others, public domain / open),
cached in work/dem. Dem(z, radius_m).at_en(e, n) gives metres above sea level at plan points (E, N) round the fence centre."""
import math
import os
import urllib.request

import numpy as np
from PIL import Image

from plan import LAT0, LON0

CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "work", "dem")


def txy(lat, lon, z):
    n = 2 ** z
    return (lon + 180) / 360 * n, (1 - math.log(math.tan(math.radians(lat)) + 1 / math.cos(math.radians(lat))) / math.pi) / 2 * n


class Dem:
    def __init__(self, z, radius):
        os.makedirs(CACHE, exist_ok=True)
        self.z = z
        dl = radius / (111320 * math.cos(math.radians(LAT0)))
        x0, y0 = txy(LAT0 + radius / 110900, LON0 - dl, z)
        x1, y1 = txy(LAT0 - radius / 110900, LON0 + dl, z)
        self.tx0, self.ty0 = int(x0), int(y0)
        nx, ny = int(x1) - self.tx0 + 1, int(y1) - self.ty0 + 1
        self.h = np.zeros((ny * 256, nx * 256), np.float32)
        for i in range(nx):
            for j in range(ny):
                p = os.path.join(CACHE, "%d_%d_%d.png" % (z, self.tx0 + i, self.ty0 + j))
                if not os.path.exists(p):
                    urllib.request.urlretrieve("https://s3.amazonaws.com/elevation-tiles-prod/terrarium/%d/%d/%d.png"
                                               % (z, self.tx0 + i, self.ty0 + j), p)
                a = np.asarray(Image.open(p).convert("RGB"), np.float32)
                self.h[j * 256:(j + 1) * 256, i * 256:(i + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768

    def at_en(self, e, n):
        e, n = np.asarray(e, float), np.asarray(n, float)
        lat = LAT0 + n / 110900.0
        lon = LON0 + e / (111320 * math.cos(math.radians(LAT0)))
        n2 = 2 ** self.z
        x = (lon + 180) / 360 * n2
        y = (1 - np.log(np.tan(np.radians(lat)) + 1 / np.cos(np.radians(lat))) / math.pi) / 2 * n2
        fx, fy = (x - self.tx0) * 256 - 0.5, (y - self.ty0) * 256 - 0.5
        x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
        ax, ay = fx - x0, fy - y0
        H = self.h
        x0 = np.clip(x0, 0, H.shape[1] - 2)
        y0 = np.clip(y0, 0, H.shape[0] - 2)
        return (H[y0, x0] * (1 - ax) * (1 - ay) + H[y0, x0 + 1] * ax * (1 - ay)
                + H[y0 + 1, x0] * (1 - ax) * ay + H[y0 + 1, x0 + 1] * ax * ay)
