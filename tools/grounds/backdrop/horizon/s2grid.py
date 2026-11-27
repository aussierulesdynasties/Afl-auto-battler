"""Real land colours for a ground's horizon: Sentinel-2 (Digital Earth Australia ARD, CC BY 4.0, contains modified
Copernicus Sentinel data), the median of the clearest footy-season (April to September) scenes of every tile over the
area, on the ground's local metre grid (x east, y north of the centre circle, rows north -> south). The same reading as
scene/s2far.py, at any size and step, and saved where horizon.py looks.

    python3 s2grid.py <slug> <half_m> <step_m> <name>     -> $HORIZON_WORK/<slug>/<name>.npy (H, W, 3) reflectance x 10000
                                                              (NaN where no clear look), <name>_water.npy, <name>.json
"""
import collections, json, math, os, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import rasterio
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.windows import from_bounds
from scipy.ndimage import map_coordinates

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.environ.get("HORIZON_WORK", os.path.expanduser("~/.cache/afl_horizon"))
os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
os.environ.setdefault("AWS_NO_SIGN_REQUEST", "YES")
os.environ.setdefault("GDAL_HTTP_MAX_RETRY", "5")
os.environ.setdefault("GDAL_HTTP_RETRY_DELAY", "2")
PER_TILE = 5


def centre(slug):
    g = json.load(open(os.path.join(HERE, "..", "..", "terrain", "grounds.json")))[slug]
    return g["lat"], g["lon"]


def main(slug, half, step, name):
    lat, lon = centre(slug)
    kx, ky = 111320 * math.cos(math.radians(lat)), 110540
    d = half * 1.03
    bb = (lon - d / kx, lat - d / ky, lon + d / kx, lat + d / ky)
    feats, url = [], ("https://explorer.dea.ga.gov.au/stac/search?collections=ga_s2am_ard_3,ga_s2bm_ard_3,ga_s2cm_ard_3"
                      "&bbox=%f,%f,%f,%f&datetime=2024-04-01/2026-11-20&limit=500" % bb)
    while url:
        page = json.load(urllib.request.urlopen(url, timeout=180))
        feats += page["features"]
        url = next((l["href"] for l in page.get("links", []) if l.get("rel") == "next"), None)
    feats = [f for f in feats if (f["properties"].get("eo:cloud_cover") or 100) < 5
             and int(f["properties"]["datetime"][5:7]) in (4, 5, 6, 7, 8, 9)]
    by = collections.defaultdict(list)
    for f in feats:
        by[f["properties"].get("odc:region_code", f["id"][:12])].append(f)
    pick = []
    for fs in by.values():
        fs.sort(key=lambda f: f["properties"]["eo:cloud_cover"])
        pick += fs[:PER_TILE]
    print("tiles", sorted(by), "scenes", len(pick), flush=True)
    n = int(round(2 * half / step))
    xs = -half + (np.arange(n) + 0.5) * step
    ys = half - (np.arange(n) + 0.5) * step
    GX, GY = np.meshgrid(xs, ys)
    LON, LAT = lon + GX / kx, lat + GY / ky
    rgb_sum = np.zeros((n, n, 3), np.float32)

    def one(f):
        a = f["assets"]
        epsg = f["properties"]["proj:epsg"]
        EX, EY = Transformer.from_crs(4326, epsg, always_xy=True).transform(LON, LAT)
        bands = []
        try:
            for k in ("nbart_red", "nbart_green", "nbart_blue", "oa_fmask"):
                href = a[k]["href"].replace("s3://dea-public-data/", "https://dea-public-data.s3.ap-southeast-2.amazonaws.com/")
                with rasterio.open("/vsicurl/" + href) as src:
                    b = src.bounds
                    x0, x1 = max(EX.min() - 200, b.left), min(EX.max() + 200, b.right)
                    y0, y1 = max(EY.min() - 200, b.bottom), min(EY.max() + 200, b.top)
                    if x0 >= x1 or y0 >= y1:
                        return None
                    w = from_bounds(x0, y0, x1, y1, src.transform)
                    fac = max(1.0, step / abs(src.transform.a))
                    oh, ow = max(1, int(w.height / fac)), max(1, int(w.width / fac))
                    arr = src.read(1, window=w, boundless=True, fill_value=0, out_shape=(oh, ow),
                                   resampling=Resampling.nearest if k == "oa_fmask" else Resampling.average).astype(np.float32)
                    t = src.window_transform(w)
                    sx, sy = w.width / ow, w.height / oh
                    col = (EX - t.c) / (t.a * sx) - 0.5
                    row = (EY - t.f) / (t.e * sy) - 0.5
                    bands.append(map_coordinates(arr, [row, col], order=0 if k == "oa_fmask" else 1, mode="constant", cval=0))
        except Exception as e:   # a scene that will not read is left out (said so), the others still make the median
            print("skip", f["id"], e, flush=True)
            return None
        rgb = np.stack(bands[:3], -1)
        raw = np.where(rgb.min(-1, keepdims=True) > 0, rgb, np.nan)
        fm = bands[3]
        clear = (fm == 1) & (rgb.min(-1) > 0) | (fm == 5) & (rgb.min(-1) > 0)
        rgb[~clear] = np.nan
        wv = np.where(clear, (fm == 5).astype(np.float32), np.nan)
        print(f["properties"]["datetime"][:10], f["properties"].get("odc:region_code"), "clear", round(float(clear.mean()), 3), flush=True)
        return rgb.astype(np.float32), wv.astype(np.float32), raw.astype(np.float32)

    with ThreadPoolExecutor(6) as ex:
        got = [r for r in ex.map(one, pick) if r is not None]
    M = np.nanmedian(np.stack([g[0] for g in got]), 0)
    # A pixel no look calls clear (fmask reads a bright roof as cloud in every scene, scenes chosen under 5 % cloud):
    # the median of every look there.
    hole = np.isnan(M).any(-1)
    M[hole] = np.nanmedian(np.stack([g[2] for g in got]), 0)[hole]
    W = np.nanmean(np.stack([g[1] for g in got]), 0)
    out = os.path.join(WORK, slug)
    os.makedirs(out, exist_ok=True)
    np.save(os.path.join(out, name + ".npy"), M.astype(np.float32))
    np.save(os.path.join(out, name + "_water.npy"), W.astype(np.float32))
    json.dump({"half_m": half, "m_per_px": step, "scenes": [f["id"] for f in pick],
               "source": "Digital Earth Australia Sentinel-2 ARD (CC BY 4.0); contains modified Copernicus Sentinel data"},
              open(os.path.join(out, name + ".json"), "w"))
    print("saved", M.shape, "filled from every look", int(hole.sum()), "still empty", int(np.isnan(M).any(-1).sum()))


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4])
