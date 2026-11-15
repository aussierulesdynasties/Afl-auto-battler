"""Grey a downloaded hair asset's strand texture so the game can tint it any hair colour.

python grey_hair_tex.py OUT_DIR STYLE=ASSET [...]   (ASSET: a folder in MPFB's data/hair)
Keeps the strands' light and dark (luminance, ranked between LOW and 1) and their
alpha, at SIZE px: Oval3D multiplies it by Appearance.HAIR[i], so a blond and a black player
wear the same strands. Writes OUT_DIR/STYLE.png.
"""
import os, re, sys
from PIL import Image, ImageOps

LOW = 0.45
SIZE = 512
HAIR = os.path.join(os.environ["APPDATA"], "Blender Foundation", "Blender", "5.2", "extensions", ".user",
                    "user_default", "mpfb", "data", "hair")

out = sys.argv[1]
os.makedirs(out, exist_ok=True)
for pair in sys.argv[2:]:
    style, asset = pair.split("=", 1)
    d = os.path.join(HAIR, asset)
    mat = next(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".mhmat"))
    tex = re.search(r"^diffuseTexture\s+(\S+)", open(mat, encoding="utf-8", errors="ignore").read(), re.M).group(1)
    im = Image.open(os.path.join(d, os.path.basename(tex))).convert("RGBA")
    w, h = im.size
    k = SIZE / max(w, h)
    im = im.resize((max(1, round(w * k)), max(1, round(h * k))), Image.LANCZOS)
    lum = ImageOps.grayscale(im)
    a = im.getchannel("A")
    # By rank, not by scale: a near-black texture (afro01) scaled up turns its noise to white
    # specks, while ranks keep each strand's place between the darkest and the lightest.
    hist = [0] * 256
    for l, al in zip(lum.get_flattened_data(), a.get_flattened_data()):
        if al > 127:
            hist[l] += 1
    n = max(1, sum(hist))
    lut, acc = [], 0
    for v in range(256):
        lut.append(round(255 * (LOW + (1.0 - LOW) * (acc + hist[v] * 0.5) / n)))
        acc += hist[v]
    lum = lum.point(lut)
    mean = sum(l * h for l, h in zip(lut, hist)) / n / 255.0
    Image.merge("LA", (lum, a)).save(os.path.join(out, style + ".png"))
    print(f"TEX {style} <- {asset}/{tex}: {im.size}, mean {mean:.2f}")
