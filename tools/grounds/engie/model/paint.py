# Hand-painted textures for ENGIE Stadium (no photo pixels): colours sampled by eye from Google Earth and the
# photo sphere in the east stand; only detail too small to model goes here (corrugation, panel joints, grain).
# python3 paint.py -> tex/<material>.png and tex/tiles.json (each tile's size in metres: u along, v up/across).
import numpy as np, json, os
from PIL import Image
R = np.random.default_rng(5); OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex') + '/'
os.makedirs(OUT, exist_ok=True)
PPM = 64; TILE = {}


def blotch(h, w, cells, amp):
    """soft periodic low-frequency variation (weathering)"""
    out = np.zeros((h, w))
    for k, c in enumerate((cells, cells * 2, cells * 4)):
        g = R.normal(0, 1, (c, c)); g = np.concatenate([g, g[:1]], 0); g = np.concatenate([g, g[:, :1]], 1)
        yi = np.linspace(0, c, h, endpoint=False); xi = np.linspace(0, c, w, endpoint=False)
        y0 = yi.astype(int); x0 = xi.astype(int); fy = (yi - y0)[:, None]; fx = (xi - x0)[None, :]
        fy = fy * fy * (3 - 2 * fy); fx = fx * fx * (3 - 2 * fx)
        a = g[y0][:, x0]; b = g[y0][:, x0 + 1]; cc = g[y0 + 1][:, x0]; d = g[y0 + 1][:, x0 + 1]
        out += (a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + cc * (1 - fx) * fy + d * fx * fy) * amp / (k + 1)
    return out


def canvas(W, H, col, noise=3.0, bl=4.0, cells=3):
    w, h = int(round(W * PPM)), int(round(H * PPM))
    a = np.ones((h, w, 3)) * np.array(col, float) + R.normal(0, noise, (h, w, 1))
    if bl:
        a += blotch(h, w, cells, bl)[:, :, None]
    return a


def save(name, a, W, H):
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(OUT + name + '.png'); TILE[name] = (W, H)


def plain(name, col, W=2.0, H=2.0, noise=3.0, bl=4.0):
    save(name, canvas(W, H, col, noise, bl), W, H)


def ribs(name, col, pitch, W, H, depth=0.12, vertical=True, joints=None):
    """corrugated or ribbed sheet: light and shade across each rib (ribs run along v when vertical)"""
    a = canvas(W, H, col, 2.0, 3.0)
    h, w = a.shape[:2]
    x = (np.arange(w) / PPM) if vertical else (np.arange(h) / PPM)
    prof = 1.0 + depth * np.sin(2 * np.pi * x / pitch)
    a *= prof[None, :, None] if vertical else prof[:, None, None]
    if joints:
        for j in np.arange(0, H, joints):
            y = int(j * PPM); a[max(0, y - 1):y + 1] *= 0.8
    save(name, a, W, H)


def panels(name, col, pw, ph, W, H, joint=0.8, noise=2.5, bl=5.0):
    """flat panels with recessed joints every pw x ph metres (joints too fine to model)"""
    a = canvas(W, H, col, noise, bl)
    for x in np.arange(0, W + 1e-6, pw):
        i = int(round(x * PPM)); a[:, max(0, i - 1):min(a.shape[1], i + 1)] *= joint
    for y in np.arange(0, H + 1e-6, ph):
        i = int(round(y * PPM)); a[max(0, i - 1):min(a.shape[0], i + 1)] *= joint
    save(name, a, W, H)


# concrete of the bowl (photo sphere: pale grey treads, slightly darker risers, grey walls)
plain('tread', (176, 174, 168), 2.0, 0.8, noise=4, bl=5)
plain('riser', (150, 148, 142), 2.0, 0.4, noise=4, bl=4)
plain('conc_light', (182, 180, 174), 2.0, 2.0, noise=4, bl=5)
plain('conc_back', (168, 166, 160), 3.0, 3.0, noise=3, bl=6)
plain('tier_wall', (128, 130, 132), 2.0, 1.0, noise=3, bl=3)
plain('parapet', (132, 133, 135), 2.0, 1.1, noise=3, bl=3)
plain('stand_front', (52, 54, 58), 3.0, 1.4, noise=2, bl=2)
plain('deck', (150, 148, 144), 2.0, 2.0)
plain('deck_pale', (198, 192, 180), 3.0, 3.0, noise=4, bl=6)
plain('step_edge', (192, 192, 186), 1.2, 0.4)
plain('race_floor', (96, 98, 96), 2.0, 2.0)
plain('vom_conc', (178, 176, 170), 2.0, 2.0)
plain('vom_dark', (30, 30, 32), 2.0, 2.0, noise=2, bl=2)
panels('paving', (172, 168, 160), 1.0, 1.0, 4.0, 4.0, joint=0.9, bl=7)
# the roofs: white-grey ribbed sheet (Google Earth), ribs running down the slope; underside beige corrugated deck
ribs('roof_top', (226, 228, 226), 0.25, 2.0, 2.0, depth=0.06, vertical=False)
ribs('roof_under', (184, 176, 160), 0.2, 2.0, 2.0, depth=0.14, vertical=False)
plain('fascia', (232, 233, 232), 3.0, 1.2, noise=2, bl=3)
plain('fascia_back', (214, 215, 214), 3.0, 1.2, noise=2, bl=3)
# steel
plain('steel_white', (232, 234, 234), 1.0, 1.0, noise=2, bl=2)
plain('steel_under', (150, 146, 136), 1.0, 1.0, noise=2, bl=2)
plain('steel_dark', (42, 42, 44), 1.0, 1.0, noise=2, bl=1)
plain('steel_grey', (156, 160, 164), 1.0, 1.0, noise=2, bl=2)
plain('steel_galv', (172, 174, 176), 1.0, 1.0, noise=2, bl=2)
plain('cable', (222, 222, 220), 1.0, 1.0, noise=1, bl=0)
plain('tower_red', (178, 44, 36), 1.0, 1.0, noise=3, bl=4)
plain('lamp_body', (60, 62, 64), 1.0, 1.0, noise=2, bl=1)
plain('lamp_face', (236, 236, 226), 1.0, 1.0, noise=2, bl=1)
# outside walls
panels('precast', (204, 202, 195), 3.0, 1.5, 6.0, 3.0, joint=0.86)
ribs('clad_grey', (168, 170, 172), 0.3, 3.0, 3.0, depth=0.08, vertical=True)
ribs('clad_charcoal', (64, 66, 70), 0.3, 3.0, 3.0, depth=0.1, vertical=True)
panels('clad_blue', (150, 182, 208), 2.0, 1.2, 4.0, 2.4, joint=0.85, bl=3)
plain('glass_dark', (40, 48, 58), 2.0, 2.0, noise=2, bl=6)
# level 3: the suites' tinted glazing between the tiers, the upper tier's soffit and fascia (photo sphere: dark band)
plain('suite_glass', (34, 40, 48), 2.0, 2.5, noise=2, bl=5)
plain('soffit', (120, 120, 118), 2.0, 0.6, noise=2, bl=3)
plain('tier_fascia', (30, 30, 32), 3.0, 0.6, noise=2, bl=2)
a = np.concatenate([canvas(2.0, 1.0, (200, 214, 218), 2, 2), np.full((64, 128, 1), 70.0)], 2)
save('balustrade_glass', a, 2.0, 1.0)
# the towers' mesh screen under the lamp frame (pale galvanised mesh)
plain('tower_mesh', (196, 198, 196), 1.0, 1.0, noise=3, bl=2)
plain('glass_shop', (58, 68, 78), 2.0, 2.0, noise=2, bl=6)
plain('concourse', (128, 122, 112), 2.0, 2.0, noise=3, bl=6)
plain('win_frame', (62, 64, 68), 1.0, 1.0)
plain('door_dark', (46, 50, 54), 1.0, 1.0)
# scoreboard
plain('sb_rim', (56, 166, 224), 2.0, 2.0, noise=2, bl=2)
plain('sb_edge', (236, 238, 240), 2.0, 2.0, noise=2, bl=1)
plain('sb_back', (196, 198, 202), 2.0, 2.0, noise=2, bl=3)
plain('sb_field', (238, 240, 242), 2.0, 2.0, noise=2, bl=1)
plain('screen', (16, 18, 22), 2.0, 2.0, noise=2, bl=1)
json.dump(TILE, open(OUT + 'tiles.json', 'w'), indent=0)
print(len(TILE), 'textures')
