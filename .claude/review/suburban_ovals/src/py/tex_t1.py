"""Type 1 (bare council oval, ref photo grid/t1_council_grid.jpg) hand-painted textures.
Every face is drawn in PHOTO pixel coordinates (2000-px copy) so the layout copies the photo exactly; no photo
pixels are used. Real brand names are replaced by generic ones. Merges into tex/tex_m.json.
    python py/tex_t1.py
"""
import json, math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = "tex"
TM = json.load(open(os.path.join(OUT, "tex_m.json")))
rng = np.random.default_rng(11)
PXM_SB = 58.0      # scoreboard face: photo px per metre (brick courses, 5.0 px = 86 mm)
PXM_F = 65.6       # fence line: photo px per metre


def F(px, style="bd"):
    name = {"bd": "arialbd.ttf", "bi": "arialbi.ttf", "r": "arial.ttf", "i": "ariali.ttf", "blk": "ariblk.ttf"}[style]
    for f in (name, "C:/Windows/Fonts/" + name, "C:/Windows/Fonts/arialbd.ttf"):
        try:
            return ImageFont.truetype(f, int(px))
        except Exception:
            pass
    return ImageFont.load_default()


class Face:
    """Canvas addressed in photo pixels: rect u0..u1, v0..v1, drawn at K texels per photo pixel."""
    def __init__(self, u0, v0, u1, v1, K=4, bg=(0, 0, 0), mode="RGB"):
        self.u0, self.v0, self.K = u0, v0, K
        self.im = Image.new(mode, (int((u1 - u0) * K), int((v1 - v0) * K)), bg if mode == "RGB" else bg + (255,))
        self.d = ImageDraw.Draw(self.im)

    def P(self, u, v):
        return ((u - self.u0) * self.K, (v - self.v0) * self.K)

    def rect(self, u0, v0, u1, v1, fill, outline=None, w=1):
        self.d.rectangle([self.P(u0, v0), self.P(u1, v1)], fill=fill, outline=outline, width=int(w * self.K) if outline else 0)

    def line(self, u0, v0, u1, v1, fill, w=1):
        self.d.line([self.P(u0, v0), self.P(u1, v1)], fill=fill, width=max(1, int(w * self.K)))

    def text(self, u, v, s, hpx, fill, style="bd", anchor="mm"):
        self.d.text(self.P(u, v), s, font=F(hpx * self.K, style), fill=fill, anchor=anchor)

    def fit_text(self, uc, vc, s, wpx, hpx, fill, style="bd"):
        """largest font that fits wpx x hpx photo pixels, centred at (uc, vc)"""
        k = hpx
        while k > 2:
            bb = self.d.textbbox((0, 0), s, font=F(k * self.K, style))
            if bb[2] - bb[0] <= wpx * self.K and bb[3] - bb[1] <= hpx * self.K:
                break
            k -= 0.5
        self.text(uc, vc, s, k, fill, style)

    def bricks(self, u0, v0, u1, v1, col=(146, 66, 50), mortar=(176, 160, 150), course=5.0, blen=13.9, seed=5):
        r = np.random.default_rng(seed)
        self.rect(u0, v0, u1, v1, mortar)
        rows = int((v1 - v0) / course) + 1
        for ri in range(rows):
            off = (blen / 2) * (ri % 2)
            vb = v1 - ri * course
            u = u0 - off
            while u < u1:
                c = np.array(col, float) * (1 + 0.14 * (r.random() * 2 - 1))
                c[0] *= 1 + 0.05 * (r.random() - 0.5)
                a, b = max(u + 0.35, u0), min(u + blen - 0.35, u1)
                if b > a:
                    self.rect(a, vb - course + 0.6, b, vb - 0.0, tuple(int(x) for x in c))
                u += blen

    def save(self, name, metres):
        self.im.save(os.path.join(OUT, name + ".png")); TM[name] = metres
        return self.im.size


# ---------------- scoreboard face (u 742-1233, v 452-805) ----------------
S = Face(742, 452, 1233, 805, K=4)
S.bricks(742, 452, 1233, 805)
DK = (30, 34, 34); BLK = (16, 18, 18)
S.rect(742, 452, 1233, 540, DK)                       # top board band
S.rect(742, 452, 985, 615, DK)                        # left board
S.rect(742, 452, 760, 615, (58, 62, 62))              # left frame edge
S.rect(1218, 455, 1233, 610, (96, 100, 98))           # right frame edge (lit side)
S.line(746, 534, 1216, 534, (60, 64, 64), 0.8)        # board seam under the sign
S.rect(870, 516, 975, 534, BLK, outline=(230, 230, 228), w=0.8)
LETTERS = False   # director 2026-11-18 "C: no lettering"
if LETTERS: S.fit_text(922.5, 525, "HOME", 90, 13, (236, 236, 234))
for u, s in ((847, "G"), (892, "B"), (946, "TOTAL")):
    if LETTERS: S.fit_text(u, 546, s, 34 if s == "TOTAL" else 10, 9, (214, 214, 210))
for (a, b) in ((827, 873), (873, 918), (918, 975)):
    for (c, d) in ((553, 572), (573, 592), (593, 613)):
        S.rect(a + 1, c, b - 1, d, BLK, outline=(64, 68, 68), w=0.6)
S.rect(873, 573, 975, 592, (10, 10, 10), outline=(150, 150, 146), w=0.7)
S.rect(763, 563, 815, 612, (236, 236, 234))           # club crest panel (generic crest)
S.d.polygon([S.P(774, 572), S.P(804, 572), S.P(804, 592), S.P(789, 605), S.P(774, 592)], outline=(140, 30, 44), width=int(1.2 * S.K))
if LETTERS: S.fit_text(789, 587, "CLUB", 24, 8, (140, 30, 44))
S.line(790, 556, 790, 615, (40, 42, 42), 1.0)         # window mullion in front of the crest
S.rect(755, 613, 822, 655, (22, 24, 24))              # lower-left black board
for (u, v) in ((761, 618), (816, 618), (761, 650), (781, 650)):
    S.rect(u - 0.7, v - 0.7, u + 0.7, v + 0.7, (220, 220, 220))
S.rect(1022, 540, 1055, 647, BLK)                     # right: black door panel
S.rect(1055, 540, 1215, 647, (28, 30, 30))
for u in (1082, 1110, 1150, 1185):
    S.line(u, 541, u, 646, (44, 46, 46), 0.6)
S.rect(1070, 592, 1203, 645, None, outline=(120, 116, 106), w=1.0)   # grille frame
for v in (603, 615, 628):
    S.line(1071, v, 1202, v, (70, 72, 70), 0.6)
S.line(1136, 592, 1136, 645, (120, 116, 106), 1.0)
SPONSORS = False   # director 2026-11-18: no sponsor boards at any ground; kept for later
if SPONSORS:
    # sponsor 1 (white with purple sweep): u 797-935, v 700-752
    S.rect(797, 700, 935, 752, (238, 238, 236))
    S.d.polygon([S.P(u, 700 + 52 * ((u - 900) / 35) ** 2) for u in range(900, 936)] + [S.P(935, 700)], fill=(126, 40, 110))
    S.rect(797, 700, 935, 752, None, outline=(200, 200, 198), w=0.5)
    S.text(803, 706, "Proudly supported by", 3.2, (120, 110, 120), "r", "lm")
    S.text(803, 714, "Community Bank", 5.5, (70, 60, 70), "r", "lm")
    S.rect(803, 734, 811, 746, (126, 40, 110)); S.text(815, 740, "Community Bank", 7.0, (90, 40, 84), "bd", "lm")
    # sponsor 2 (framed beige board): u 1012-1173, v 700-755
    S.rect(1012, 700, 1173, 755, (40, 44, 44))
    S.rect(1022, 707, 1163, 752, (178, 168, 140))
    S.fit_text(1092, 722, "MANAGEMENT", 120, 14, (54, 54, 50), "bi")
    S.fit_text(1092, 742, "9555 0000  -  0400 000 000", 110, 5, (80, 78, 70), "r")
print("scoreboard face", S.save("t1_scoreboard", 8.47))

# ---------------- top sign (u 775-1193, v 436-505) ----------------
T = Face(775, 436, 1193, 505, K=4)
T.rect(775, 436, 855, 505, (238, 238, 236))
T.fit_text(815, 470, "Go", 60, 34, (200, 34, 40), "bi")
T.rect(855, 436, 1090, 505, (204, 38, 44))
T.fit_text(972, 472, "LOCALS", 215, 52, (244, 244, 242), "bd")
T.rect(1090, 436, 1193, 505, (226, 228, 228))
T.fit_text(1141, 486, "Real Estate", 80, 12, (206, 208, 208), "bd")
T.line(775, 504, 1193, 504, (60, 60, 60), 1.0)
print("top sign", T.save("t1_topsign", 7.2))

# ---------------- shed front (u 205-435, v 650-848) ----------------
H = Face(205, 650, 435, 848, K=4)
H.rect(205, 650, 435, 740, (30, 92, 108))
H.fit_text(320, 683, "TIMBER", 150, 34, (240, 240, 236), "blk")
H.line(268, 704, 372, 704, (196, 170, 90), 1.2)
H.fit_text(320, 716, "BUILDING PRODUCTS", 120, 9, (236, 236, 232))
H.fit_text(320, 729, "1800 000 000", 60, 7, (236, 236, 232))
H.rect(205, 740, 435, 836, (226, 228, 226))
for i in range(40):   # weathering smudges on the white panel (hand-made, faint)
    u = rng.uniform(210, 430); v = rng.uniform(745, 832); s = rng.uniform(2, 7)
    H.d.ellipse([H.P(u - s, v - s * 0.5), H.P(u + s, v + s * 0.5)], fill=(206, 210, 216))
H.fit_text(250, 762, "health", 50, 16, (36, 80, 140), "r")
H.fit_text(345, 762, "GO LOCALS", 120, 20, (110, 96, 170), "bd")
H.line(255, 793, 400, 793, (40, 90, 160), 1.5)
H.rect(205, 836, 435, 848, (30, 40, 56))
H.rect(205, 650, 209, 848, (24, 30, 36))
print("shed front", H.save("t1_shed_front", 3.5))

# ---------------- LED screen (u 1473-1843, v 497-740), off ----------------
L = Face(1473, 497, 1843, 740, K=2, bg=(18, 20, 22))
L.rect(1473, 497, 1843, 740, None, outline=(36, 38, 40), w=3)
for u in range(1473, 1843, 46):
    L.line(u, 500, u, 737, (22, 24, 26), 0.5)
print("led", L.save("t1_led", 7.0))

# ---------------- fence sponsor boards (fence line, v 785-848) ----------------
def board(name, u0, u1, bg, draw):
    B = Face(u0, 785, u1, 848, K=6, bg=bg)
    draw(B, u0, u1)
    B.rect(u0, 785, u1, 848, None, outline=tuple(max(0, c - 40) for c in bg), w=0.6)
    B.save(name, (u1 - u0) / PXM_F)


def b1(B, a, b):
    B.d.rounded_rectangle([B.P(a + 22, 790), B.P(b - 22, 830)], radius=3 * B.K, outline=(240, 236, 232), width=int(1.2 * B.K))
    B.fit_text((a + b) / 2, 806, "BUILD", 100, 22, (240, 236, 232), "bd")
    B.fit_text((a + b) / 2, 825, "LOCAL BUILDING GROUP", 80, 4, (240, 236, 232))
    B.fit_text((a + b) / 2, 839, "localbuilding.com.au", 130, 9, (244, 240, 236))


def b3(B, a, b):
    B.fit_text(a + 45, 800, "WORK", 80, 9, (20, 20, 24), "bd")
    B.fit_text(a + 45, 813, "Need work? Let's talk", 80, 5, (40, 40, 44), "r")
    B.fit_text(a + 45, 828, "\u201cLet's chat\u201d", 80, 10, (40, 40, 44), "r")
    for (du, dv, col) in ((115, 805, (40, 120, 200)), (132, 803, (220, 60, 120)), (118, 826, (60, 170, 80)), (134, 828, (240, 150, 40))):
        B.d.ellipse([B.P(a + du - 10, dv - 10), B.P(a + du + 10, dv + 10)], fill=col)


def b4(B, a, b):
    B.fit_text((a + b) / 2, 815, "Dessert Co.", 120, 24, (240, 228, 228), "bi")
    B.fit_text((a + b) / 2, 834, "DESSERT BAR", 60, 5, (230, 210, 210))


def b5(B, a, b):
    B.d.ellipse([B.P(a + 8, 795), B.P(a + 30, 817)], outline=(30, 44, 70), width=int(1.4 * B.K))
    B.fit_text(a + 90, 800, "inspect", 100, 13, (30, 44, 70), "bd")
    B.fit_text(a + 90, 813, "property inspections", 100, 6, (60, 110, 160), "r")
    B.fit_text((a + b) / 2, 830, "Pre-purchase building and timber pest inspections", 135, 4, (40, 44, 50), "r")


def b6(B, a, b):
    B.fit_text(a + 25, 805, "care", 34, 10, (40, 70, 110), "r")
    B.fit_text(a + 110, 800, "We're here for", 110, 9, (30, 40, 60), "bd")
    B.fit_text(a + 110, 813, "health & wellbeing.", 110, 9, (30, 40, 60), "bd")
    B.rect(a + 5, 838, b - 5, 846, (40, 70, 110))


def b7(B, a, b):
    B.fit_text((a + b) / 2, 812, "CAFE", 40, 16, (240, 240, 240), "blk")


def b8(B, a, b):
    cols = [(200, 40, 50), (120, 60, 150), (230, 230, 228), (150, 150, 150), (220, 180, 60), (200, 40, 50), (90, 90, 96)]
    for i, c in enumerate(cols):
        u = a + 10 + i * 13
        B.d.rounded_rectangle([B.P(u, 800), B.P(u + 10, 838)], radius=2 * B.K, fill=c, outline=(60, 60, 60), width=2)


def b9(B, a, b):
    B.fit_text(a + 50, 808, "Community", 80, 10, (40, 40, 44), "r")
    B.rect(a + 10, 818, a + 22, 834, (190, 30, 50)); B.fit_text(a + 60, 826, "Local Bank", 70, 9, (40, 40, 44), "bd")


BOARDS = [("t1_s1", 25, 187, (196, 48, 46), b1), ("t1_s3", 768, 920, (240, 240, 238), b3),
          ("t1_s4", 1320, 1462, (110, 36, 48), b4), ("t1_s5", 1465, 1615, (240, 240, 238), b5),
          ("t1_s6", 1618, 1788, (236, 236, 236), b6), ("t1_s7", 1790, 1838, (16, 16, 18), b7),
          ("t1_s8", 1838, 1940, (236, 236, 234), b8), ("t1_s9", 1940, 2060, (238, 238, 236), b9)]
for nm, a, b, bg, fn in BOARDS:
    board(nm, a, b, bg, fn)


# ---------------- black chainlink and worn turf ----------------
def chainlink(name, col, n=512, metres=1.0):
    ppm = n / metres; a = np.zeros((n, n, 4)); cell = 0.06 * ppm
    xx, yy = np.meshgrid(np.arange(n), np.arange(n))
    p1 = (xx + yy) % cell; p2 = (xx - yy) % cell
    d1 = np.minimum(p1, cell - p1) / 1.414; d2 = np.minimum(p2, cell - p2) / 1.414
    m = np.minimum(d1, d2) < 1.3
    a[m, :3] = col; a[m, 3] = 255
    Image.fromarray(a.astype(np.uint8), "RGBA").save(os.path.join(OUT, name + ".png")); TM[name] = metres


chainlink("chainlink_black", (26, 28, 28))


def worn(n=512, seed=3):
    """sandy worn patch, soft-edged blob (RGBA), 1:4 aspect drawn square; stretched by the decal quad"""
    r = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:n, 0:n] / n
    m = np.zeros((n, n))
    for _ in range(14):
        cx, cy = r.uniform(0.2, 0.8), r.uniform(0.35, 0.65); s = r.uniform(0.06, 0.16)
        m = np.maximum(m, np.exp(-(((xx - cx) / (s * 1.6)) ** 2 + ((yy - cy) / s) ** 2)))
    m *= (r.random((n, n)) * 0.5 + 0.75)
    a = np.zeros((n, n, 4)); a[..., 0] = 196; a[..., 1] = 180; a[..., 2] = 136
    a[..., :3] *= (0.92 + 0.16 * r.random((n, n)))[..., None]
    a[..., 3] = np.where(m > 0.55, 255, 0)
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA").save(os.path.join(OUT, "turf_worn.png")); TM["turf_worn"] = 4.0


worn()
json.dump(TM, open(os.path.join(OUT, "tex_m.json"), "w"), indent=1)
print("ok", len(TM))
