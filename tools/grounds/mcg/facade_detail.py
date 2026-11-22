"""MCG facade detail pass (MCG flagship, 2026-11-21).

The MCG model's facade textures are one bay each (a vertical strip, 24 m tall, tiled along the
wall), drawn as flat colour blocks at ~21 px/m. Against Google Earth they read too white and
too flat. This keeps each texture's layout (where the glass, panels and bands are) and redraws
it at 32 px/m with what Google Earth shows: mid-grey precast with panel joints and weathering,
dark glass with aluminium mullions, a sky reflection and a shadow under every slab edge.

Reads the originals from tools/grounds/mcg/facade_src/ (kept so the pass can be rerun) and
writes the game's textures in assets/grounds/mcg/. Metres per texture width come from the
model's UVs (measured 2026-11-21).

    python3 tools/grounds/mcg/facade_detail.py
"""
import os, shutil
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "facade_src")
DST = os.path.normpath(os.path.join(ROOT, "../../../assets/grounds/mcg"))
PPM = 32            # pixels per metre
TALL = 24.0         # every facade texture spans 24 m of height
# metres of wall across each texture (u = 0..1), from the model's UVs
MU = {"backclad": 6.0, "backglass": 6.3, "fac_balc": 9.8, "fac_box": 29.0, "fac_east": 3.7,
      "fac_eglass": 6.5, "fac_eglass2": 6.7, "fac_endpale": 6.9, "fac_eslot": 4.1, "fac_gate": 10.0,
      "fac_gate2": 12.2, "fac_gss": 2.1, "fac_louvre": 2.1, "fac_mcc": 6.7, "fac_mcc_win": 8.8,
      "fac_mural": 7.4, "fac_neblock": 19.0, "fac_nebox": 22.0, "fac_nefins": 12.8,
      "fac_nwblock": 24.3, "fac_nwdark": 49.6, "fac_nwglass": 9.3, "fac_nwrecess": 3.1,
      "fac_plant": 9.7, "fac_podium": 8.3, "fac_posterblk": 32.0, "fac_se": 3.0, "fac_se_p": 3.3,
      "fac_stair": 9.9, "fac_swdark": 3.1, "fac_swpale": 3.3, "fac_wgrey": 6.6, "uc_back": 11.7}
# corner strips (cs_*) are 0.6 m wide: recoloured only
SOLID_SCALE = 0.72  # Google Earth's concrete is mid grey; the originals are near white
rng = np.random.default_rng(7)


def detail(name: str, img: Image.Image) -> Image.Image:
    mu = MU.get(name)
    a0 = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    if mu is None:                      # a corner strip: same colours, no new detail
        return Image.fromarray(np.clip(_tone(a0, a0.mean(2) < 0.36) * 255, 0, 255).astype(np.uint8))
    h = int(TALL * PPM)
    w = int(np.clip(round(mu * PPM), 16, 1024))
    lay = np.asarray(img.convert("RGB").resize((w, h), Image.NEAREST), dtype=np.float32) / 255.0
    lum = lay.mean(2)
    glass = lum < 0.36
    out = _tone(lay, glass)
    yy, xx = np.mgrid[0:h, 0:w]
    # solid: precast joints every 3 m across and 1.5 m up, fine grain, rain streaks
    joint = ((xx % (3 * PPM)) < 2) | ((yy % int(1.5 * PPM)) < 2)
    grain = rng.normal(0, 0.018, (h, w))
    streak = np.repeat(rng.normal(0, 0.025, (1, w)), h, 0) * np.linspace(0.4, 1.0, h)[:, None]
    s = ~glass
    out[s] *= (1 + grain[s] + streak[s])[:, None]
    out[s & joint] *= 0.82
    # glass: mullions every 1.5 m, a transom 1.1 m up each pane run, sky in the top of each run
    g = glass
    mull = (xx % int(1.5 * PPM)) < 3
    run_top = _run_start(g)             # rows since the glass run began, per column
    refl = np.exp(-run_top / (1.2 * PPM)) * 0.22
    out[g] = out[g] * (1 - refl[g])[:, None] + np.array([0.62, 0.70, 0.78]) * refl[g][:, None]
    pane = rng.normal(0, 0.03, (h // 16 + 1, w // 48 + 1))
    out[g] *= (1 + np.kron(pane, np.ones((16, 48)))[:h, :w][g])[:, None]
    out[g & mull] = np.array([0.55, 0.57, 0.6])
    tran = (run_top > 0) & ((run_top % int(3.6 * PPM)) < 3) 
    out[g & tran] = np.array([0.5, 0.52, 0.55])
    # a slab shadow: the first 0.25 m of glass under a solid band is darker
    out[g & (run_top < 8)] *= 0.6
    return Image.fromarray(np.clip(out * 255, 0, 255).astype(np.uint8))


def _tone(a: np.ndarray, glass: np.ndarray) -> np.ndarray:
    out = a.copy()
    out[~glass] = out[~glass] * SOLID_SCALE + np.array([0.01, 0.01, 0.0])   # a touch warm, as GE
    out[glass] = out[glass] * 0.85 + np.array([0.02, 0.03, 0.05])
    return out


def _run_start(g: np.ndarray) -> np.ndarray:
    h, w = g.shape
    r = np.zeros((h, w), np.float32)
    for y in range(1, h):
        r[y] = np.where(g[y] & g[y - 1], r[y - 1] + 1, 0)
    return r


def main() -> None:
    os.makedirs(SRC, exist_ok=True)
    for f in sorted(os.listdir(DST)):
        if not (f.startswith("mcg_") and f.endswith(".webp")):
            continue
        name = f[4:-5]
        if not ("fac" in name or name in ("backclad", "backglass", "cs_backglass", "uc_back")):
            continue
        src = os.path.join(SRC, f)
        if not os.path.exists(src):
            shutil.copy(os.path.join(DST, f), src)
        out = detail(name, Image.open(src))
        out.save(os.path.join(DST, f), "WEBP", quality=88, method=6)
        print(f, Image.open(src).size, "->", out.size)


if __name__ == "__main__":
    main()
