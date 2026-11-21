# Hand-painted textures for single buildings round the outside, one tile = the whole block front (u = metres from the
# block's lower-bearing edge, v = z / 24). Layouts read off the matched Google Earth views (work/segcmp.py crops);
# no photo pixels. Run after paint.py and paint2.py.
import numpy as np, json, os
from PIL import Image
R = np.random.default_rng(11); OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tex') + '/'
TILE = json.load(open(OUT + 'tiles.json')); H = 24.0; PPM = 96


def winspans(name, wins, W):
    """where the windows are along the tile (u metres), for wallcols.py: a corner may never cut one. Ribbon glazing
    that runs the full tile width is left out (it crosses every corner by design; the corner strip covers it)."""
    p = OUT + 'winspans.json'; J = json.load(open(p)) if os.path.exists(p) else {}
    J[name] = [[max(0.0, a), min(W, b)] for a, b in wins if b - a < 0.95 * W]
    json.dump(J, open(p, 'w', newline=''))


class T:
    def __init__(s, W, col, n=2.0):
        s.W = W; s.w = int(W * PPM); s.h = int(H * PPM); s.a = np.ones((s.h, s.w, 3)) * np.array(col, float)
        s.a += R.normal(0, n, (s.h, s.w, 1)); s.wins = []  # u spans of the windows drawn (tex/winspans.json)
    def Y(s, z): return int(round((H - z) * PPM))
    def X(s, u): return int(round(u * PPM))
    def rect(s, u0, u1, z0, z1, col=None, mul=None):
        y0, y1 = max(0, s.Y(z1)), min(s.h, s.Y(z0)); x0, x1 = max(0, s.X(u0)), min(s.w, s.X(u1))
        if y1 <= y0 or x1 <= x0: return
        if mul is not None: s.a[y0:y1, x0:x1] *= mul
        else: s.a[y0:y1, x0:x1] = np.array(col, float) + R.normal(0, 1.5, (y1 - y0, x1 - x0, 1))
    def hl(s, z, t, col=None, mul=0.7, u0=0, u1=None): s.rect(u0, s.W if u1 is None else u1, z - t / 2, z + t / 2, col, None if col else mul)
    def vl(s, u, t, z0=0, z1=H, col=None, mul=0.75): s.rect(u - t / 2, u + t / 2, z0, z1, col, None if col else mul)
    def win(s, u0, u1, z0, z1, col=(44, 74, 80), frame=(214, 218, 218), nx=2, ny=2, fw=0.07):
        s.rect(u0, u1, z0, z1, col); s.wins.append((u0 - fw, u1 + fw))
        y0, y1 = s.Y(z1), s.Y(z0); s.a[y0:y1, s.X(u0):s.X(u1)] *= np.linspace(1.18, 0.88, y1 - y0)[:, None, None]
        for k in range(nx + 1): s.vl(u0 + (u1 - u0) * k / nx, fw, z0, z1, frame)
        for k in range(ny + 1): s.hl(z0 + (z1 - z0) * k / ny, fw, frame, u0=u0, u1=u1)
        s.hl(z0 - 0.08, 0.16, None, 0.7, u0, u1)  # sill shadow
    def save(s, name):
        Image.fromarray(np.clip(s.a, 0, 255).astype(np.uint8)).save(OUT + name + '.png'); TILE[name] = (s.W, H)
        winspans(name, s.wins, s.W)


GREY = (150, 157, 164); LEDGE = (226, 228, 226); TEAL = (52, 86, 92)
# North-west block 342-350.5 (f000): mid-grey cladding raised on a 2.0 m open ground floor (pale slab edge at z 2.0,
# a pale post at each corner below it), white ledges at z 8.6 and 14.1, teal window columns (u from the 342 end):
# u 0.75-3.5 every floor, u 8.1-10.6 top floor only, u 18.2-21.4 top and ground floors with the wide window
# u 13.5-21.4 on the middle floor. Windows sit inside the 0.6 m corner strips (photo: glazing runs almost to the edges).
t = T(22.1, (72, 84, 98))  # photo wall reads dark blue-grey (66,90,112 in f000)
for u in np.arange(0, 22.1, 3.0): t.vl(u, 0.03, mul=0.92)
t.hl(2.0, 0.3, LEDGE)
for z in (8.6, 14.1): t.hl(z, 0.28, LEDGE); t.hl(z - 0.2, 0.12, mul=0.75)
fl = ((2.4, 8.1), (9.1, 13.6), (14.6, 22.4))
for z0, z1 in fl: t.win(0.75, 3.5, z0, z1, TEAL, nx=2, ny=3)
t.win(8.1, 10.6, 14.6, 22.4, TEAL, nx=1, ny=3)
t.win(18.2, 21.4, 14.6, 22.4, TEAL, nx=2, ny=3); t.win(13.5, 21.4, 9.1, 13.6, TEAL, nx=5, ny=2); t.win(18.2, 21.4, 2.4, 8.1, TEAL, nx=2, ny=2)
t.rect(19.4, 20.4, 3.8, 5.8, (210, 214, 220))  # the sign in the ground-floor window
t.hl(23.4, 0.25, (200, 204, 204))
t.save('fac_nwblock')
# Pale concrete end walls of the blocks (the sunlit east end of 342-350.5): plain off-white, faint joints.
t = T(6.0, (216, 216, 210))
for z in np.arange(0, 24, 3.0): t.hl(z, 0.03, mul=0.93)
t.save('fac_endpale')


# North gate 350.5-10 (f000 zoom): dark undercroft to z 7.0 with columns, pale glazing 7.0-11.6 (1.2 m mullions),
# dark window band 11.9-14.1 with white mullions, white ledge 14.1-14.8, pale glass balustrade 14.8-16.5.
def gate(side):
    t = T(10.0, (188, 198, 204))
    t.rect(0, 10, 0, 7.0, (38, 48, 62)); t.rect(4.7, 5.3, 0, 7.0, (176, 182, 186))
    t.a[t.Y(11.6):t.Y(7.0)] *= np.linspace(1.08, 0.92, t.Y(7.0) - t.Y(11.6))[:, None, None]
    for u in np.arange(0, 10, 1.2): t.vl(u, 0.06, 7.0, 11.6, (226, 230, 230))
    t.hl(9.3, 0.05, (226, 230, 230))
    if side: t.hl(10.6, 0.22, LEDGE)
    t.rect(0, 10, 11.6, 11.9, (150, 156, 160))
    t.rect(0, 10, 11.9, 14.1, (40, 54, 70))
    for u in np.arange(0, 10, 1.2): t.vl(u, 0.1, 11.9, 14.1, (214, 220, 222))
    t.rect(0, 10, 14.1, 14.8, LEDGE)
    t.rect(0, 10, 14.8, 16.5, (176, 192, 200))
    for u in np.arange(0, 10, 1.2): t.vl(u, 0.05, 14.8, 16.5, (220, 226, 228))
    t.save('fac_gate2' if side else 'fac_gate')


gate(False); gate(True)
# Metal box 10-17 on legs (f000): grey ribbed metal (ribs every 0.3 m), open undercroft z 0-4.6 (built as geometry), one wide window
# strip z 7.8-10.4 across most of the north face (u 11.2-17.9), a small window on the angled west face (u 2.4-3.7).
# One tile = the whole 27.2 m run along the footprint (10-17): angled faces s 0-19.5, front face s 19.5-27.2 (f022:
# window strip across the middle of the front, ~1.5 m plain each side).
t = T(27.2, (146, 156, 166))
for u in np.arange(0, 27.2, 0.3): t.vl(u, 0.05, 4.6, 24, mul=0.86)
t.rect(0, 27.2, 0, 4.6, (36, 44, 56)); t.hl(4.7, 0.2, (120, 128, 136))
t.win(21.0, 25.7, 7.8, 10.4, (40, 58, 66), frame=(196, 202, 206), nx=4, ny=1)
t.hl(7.7, 0.2, (200, 206, 210), u0=21.0, u1=25.7)
t.win(2.4, 3.7, 9.2, 11.9, (60, 84, 92), nx=1, ny=1)
t.save('fac_box')
# Poster block 17-24 (f000): grey cladding with paler pilasters, white ledges at z 8.2 and 15.4, two columns of
# four-pane teal windows on each floor.
t = T(18.4, (156, 164, 170))
for u0, u1 in ((0, 1.2), (7.8, 9.6), (17.2, 18.4)): t.rect(u0, u1, 0, 22.5, (180, 186, 190))
for z in (8.2, 15.4): t.hl(z, 0.3, LEDGE); t.hl(z - 0.22, 0.12, mul=0.75)
for z0, z1 in ((1.4, 7.4), (8.8, 14.6), (16.0, 21.4)):
    for u0, u1 in ((2.9, 9.0), (12.3, 17.6)): t.win(u0, u1, z0, z1, TEAL, nx=2, ny=2)
t.save('fac_posterblk')
# The mural on the block's angled east face 24-26.5: a hand-painted footballer artwork (white ground, black figure
# shapes, red and green blocks low down), not a copy of the real poster.
t = T(6.5, (226, 226, 222))
t.rect(0.4, 3.0, 12.0, 21.0, (34, 36, 40)); t.rect(1.0, 2.4, 17.0, 20.0, (226, 226, 222)); t.rect(3.4, 6.0, 9.0, 16.0, (40, 42, 46))
t.rect(0.0, 3.6, 2.0, 8.5, (196, 52, 40)); t.rect(3.6, 6.5, 0.6, 6.0, (88, 140, 70)); t.rect(4.2, 5.8, 17.5, 21.5, (34, 36, 40))
t.save('fac_mural')
# NE 26.5-39.5 (f045): dark glazing set back behind five pale horizontal sun-shade fins at z 3.8, 7.0, 10.8, 14.6,
# 18.4, a grey parapet from z 20.
t = T(12.0, (40, 52, 66))
for u in np.arange(0, 12, 1.5): t.vl(u, 0.06, 0, 20, (64, 78, 94))
for z in np.arange(0.9, 20, 1.9): t.hl(z, 0.04, (58, 72, 88))
for z in (3.8, 7.0, 10.8, 14.6, 18.4): t.rect(0, 12, z, z + 0.45, (196, 202, 206)); t.rect(0, 12, z - 0.5, z, None, 0.7)
t.rect(0, 12, 20, 24, (150, 157, 164))
t.save('fac_nefins')
# NE block 39.5-46 (f045): grey cladding, white ledges at z 8.0 and 13.4, the white sign panel u 0.3-4.6 (a green
# club crest high up), two columns of four-pane teal windows u 5.5-9.6 and 10.6-15.0.
t = T(17.0, GREY)
for z in (8.0, 13.4): t.hl(z, 0.3, LEDGE); t.hl(z - 0.22, 0.12, mul=0.75)
for z0, z1 in ((1.2, 6.5), (8.8, 13.0), (13.8, 19.2)):
    for u0, u1 in ((5.5, 9.6), (10.6, 15.0)): t.win(u0, u1, z0, z1, TEAL, nx=2, ny=2)
t.rect(0.3, 4.6, 0.8, 19.6, (232, 234, 232)); t.rect(1.2, 3.7, 16.0, 18.4, (40, 120, 92)); t.rect(1.8, 3.1, 16.6, 17.8, (232, 234, 232))
t.save('fac_neblock')
# NE metal box 46-54 on legs (f045, f090): open undercroft z 0-4.4 (built as geometry), a long dark window strip z 7.0-10.2 at
# u 12.0-20.7, grey panel grid (3 m) above with two dark slots at u 5.6-6.4, a shadowed recess u 0-2.6 at the join.
t = T(21.0, (156, 164, 172))
for u in np.arange(0, 21, 3.0): t.vl(u, 0.05, 4.4, 24, mul=0.84)
for z in np.arange(6.5, 24, 3.4): t.hl(z, 0.05, mul=0.84)
t.rect(2.6, 21, 0, 4.4, (34, 42, 54)); t.hl(4.47, 0.15, (120, 128, 136), u0=2.6)
t.win(12.0, 20.7, 7.0, 10.2, (38, 52, 62), frame=(190, 196, 200), nx=5, ny=1)
for u in (5.6, 6.1): t.rect(u, u + 0.3, 9.5, 15.0, (44, 52, 62))
t.rect(0, 2.6, 0, 24, (116, 124, 132))
t.save('fac_nebox')
# Northern Stand back seen above the blocks (f000, f045): light grey vertical cladding z 0-27.5, then blue-grey glazing
# (lighter than the old dark grid) with transoms every 2 m and mullions every 1.5 m.
t = T(6.0, (178, 184, 188))
for u in np.arange(0, 6, 0.75): t.vl(u, 0.04, mul=0.9)
t.save('backclad')
t = T(6.0, (92, 114, 136))
for u in np.arange(0, 6, 1.5): t.vl(u, 0.06, col=(140, 156, 170))
for z in np.arange(0, 24, 2.0): t.hl(z, 0.08, (150, 164, 176))
t.a[:] *= np.linspace(1.12, 0.92, t.h)[:, None, None]
t.save('backglass')
# Solar roof: rows of dark blue panels in light frames on a grey roof (6 x 6 m tile; two rows of 2 m panels).
# East glass wall 54-74 (f045, f090): one pale silver-blue curtain wall from the ground to z 27, mullions every 1.5 m,
# light transoms every 2 m and pale floor slabs every 6 m (periodic in z so the 27 m wall wraps cleanly).
t = T(6.0, (172, 186, 196))
for u in np.arange(0, 6, 1.5): t.vl(u, 0.07, col=(206, 212, 214))
for z in np.arange(0, 24, 2.0): t.hl(z, 0.05, (196, 204, 208))
for z in (0, 6, 12, 18, 24): t.hl(z, 0.45, (214, 218, 218)); t.hl(z - 0.3, 0.15, mul=0.8)
t.a[:] *= (1 + 0.04 * np.sin(np.linspace(0, 2 * np.pi, t.h)))[:, None, None]
t.save('fac_eglass')
# East stair towers 76.3-79.2 and 83.3-86 (f090): white precast standing ~6 m out from the glass, z 0-25, dark
# window strips every 3.3 m (z 3.5-22) with a pale margin each side, a grey door at the foot.
t = T(7.5, (224, 226, 222))
for z in np.arange(3.5, 22, 3.3): t.rect(0.7, 6.8, z, z + 1.1, (70, 84, 96)); t.hl(z - 0.06, 0.12, mul=0.75, u0=0.7, u1=6.8)
t.rect(2.8, 4.7, 0, 2.6, (96, 104, 112)); t.hl(24.6, 0.5, (238, 238, 234))
t.save('fac_stair')
# East podium 79.2-83.3 (f090): dark shopfront glazing z 0-4.3 under a grey slab edge 4.3-5.
t = T(6.0, (52, 64, 76))
for u in np.arange(0, 6, 1.5): t.vl(u, 0.08, 0, 4.3, (150, 158, 164))
t.rect(0, 6, 4.3, 5.2, (176, 182, 186)); t.hl(4.3, 0.1, mul=0.7)
t.save('fac_podium')
# East recessed glass 74-86 between the towers (f090): blue-grey curtain wall with pale floor slabs every 5 m.
t = T(6.0, (118, 138, 156))
for u in np.arange(0, 6, 1.5): t.vl(u, 0.07, col=(176, 186, 194))
for z in np.arange(0, 24, 2.5): t.hl(z, 0.05, (150, 166, 178))
for z in (0, 5, 10, 15, 20): t.hl(z + 0.25, 0.5, (210, 214, 214))
t.a[:] *= np.linspace(1.08, 0.94, t.h)[:, None, None]
t.save('fac_eglass2')
# East precast block 89-110 (f112): pale precast panels with joints every 3.6 m, thin dark window strips at z 4.8,
# 10.0, 15.2 and 20.2, parapet to z 22.5; stair slots (fac_eslot) of stacked dark windows at 89-91.5 and 101.4-102.4.
ES = (4.8, 10.0, 15.2, 20.2)
t = T(3.6, (222, 222, 216))
t.vl(0.02, 0.05, mul=0.82)
for z in ES: t.rect(0, 3.6, z, z + 0.8, (62, 70, 80)); t.hl(z - 0.05, 0.1, mul=0.8)
t.hl(22.3, 0.4, (234, 234, 230))
t.save('fac_east')
t = T(2.5, (222, 222, 216))
for z in np.arange(2.0, 21.5, 2.6): t.win(0.4, 2.1, z, z + 1.9, (58, 70, 84), frame=(206, 210, 210), nx=1, ny=1)
for z in ES: t.rect(0, 0.4, z, z + 0.8, (62, 70, 80)); t.rect(2.1, 2.5, z, z + 0.8, (62, 70, 80))
t.save('fac_eslot')
# Plant box on the east precast block 91-109 (f112): pale render, a grey coping at the top, set ~4 m back, top z 28.5.
t = T(6.0, (214, 214, 208))
t.vl(0.02, 0.05, mul=0.85); t.rect(0, 6, 27.8, 28.5, (168, 170, 168))
t.save('fac_plant')
# South-east block 130.5-150 (f135): pale grey precast, a panel grid (3 m joints, a joint at each floor), dark window
# strips under the floor lines at z 5.5, 10.5 and 15.5, a top band to z 21 with round portholes (z 19.4) along
# 140-150; a full-height dark glass slot at 139.4-140.2.
def se(name, port):
    t = T(3.0, (204, 208, 208))
    t.vl(0.02, 0.05, mul=0.82)
    for z in (5.0, 10.0, 15.0, 18.4): t.hl(z + 0.9, 0.06, mul=0.85)
    for z in (5.5, 10.5, 15.5): t.rect(0, 3.0, z - 0.9, z, (64, 74, 86)); t.hl(z - 0.95, 0.1, mul=0.75)
    t.hl(20.8, 0.4, (226, 228, 226))
    if port:
        yy, xx = np.mgrid[0:t.h, 0:t.w]; m = (xx - t.X(1.5)) ** 2 + (yy - t.Y(19.4)) ** 2 < (0.38 * PPM) ** 2
        t.a[m] = (58, 66, 76)
    t.save(name)
se('fac_se', False); se('fac_se_p', True)
# South stair towers 157-159.5, 165-169, 197.5-200, 204.5-206.5 (f180): pale concrete frames with stacked open
# balconies: slab edges every 4.3 m, dark recess between them behind a pale rail 1 m up, piers 0.6 m each side,
# parapet to z 24.
t = T(8.0, (200, 204, 204))
for z in np.arange(0.0, 21.6, 4.3):
    t.rect(0.6, 7.4, z + 0.5, z + 4.3, (58, 68, 80)); t.rect(0.6, 7.4, z + 0.5, z + 1.6, (88, 98, 108))
    t.hl(z + 1.55, 0.1, (214, 216, 214), u0=0.6, u1=7.4); t.rect(0, 8, z, z + 0.5, (216, 218, 216)); t.hl(z + 0.5, 0.12, mul=0.7, u0=0.6, u1=7.4)
t.rect(0, 8, 22.0, 24, (210, 212, 210))
t.save('fac_balc')
# Great Southern Stand block 172-194 (f180): pale grey precast, joints every 2 m, thin dark window strips at z 4.4,
# 9.4, 14.0, 18.6, parapet to z 21.
t = T(2.0, (198, 204, 208))
t.vl(0.02, 0.05, mul=0.85)
for z in (3.9, 7.9, 11.9, 15.6): t.rect(0, 2.0, z - 0.4, z + 0.4, (62, 72, 84)); t.hl(z - 0.45, 0.1, mul=0.75)
t.hl(17.3, 0.4, (222, 224, 224))
t.save('fac_gss')
# South-west wall 212-236 (f225): dark slate glazing in a grid of pale frames, pale spandrel bands at z 4.5, 9,
# 13.5, 18, mullions every 3 m.
t = T(3.0, (66, 80, 96))
t.vl(0.0, 0.12, col=(150, 160, 170)); t.vl(1.5, 0.06, col=(110, 122, 134))
for z in (4.5, 9.0, 13.5, 18.0): t.rect(0, 3.0, z, z + 0.6, (156, 166, 176)); t.hl(z - 0.05, 0.1, mul=0.7)
t.rect(0, 3.0, 0, 0.4, (150, 156, 160)); t.rect(0, 3.0, 21.4, 22, (170, 176, 180))
t.save('fac_swdark')
# Pale block under the south-west screen 236-250 (f225): pale grey precast with small dark windows in rows at z 3,
# 7.5, 12, 16.5, one per 3 m bay, joints between bays.
t = T(3.0, (204, 208, 210))
t.vl(0.02, 0.05, mul=0.85)
for z in (3.0, 7.5, 12.0, 16.5): t.rect(0.9, 2.1, z, z + 1.6, (70, 80, 92)); t.hl(z + 1.6, 0.08, (228, 230, 230), u0=0.85, u1=2.15)
t.rect(0, 3.0, 21.4, 22, (220, 222, 222))
t.save('fac_swpale')
# MCC louvre wall 268-282 (f270): pale vertical fins 1.1 m wide on a 2 m pitch over dark glazing, z 2.5-16.5, a pale
# rail at mid height (z 9.2), pale head and sill.
t = T(2.0, (198, 200, 198))
t.rect(0, 2.0, 2.5, 16.5, (46, 56, 68)); t.a[t.Y(16.5):t.Y(2.5)] *= np.linspace(1.12, 0.9, t.Y(2.5) - t.Y(16.5))[:, None, None]
t.rect(0.45, 1.55, 2.5, 16.5, (214, 218, 220)); t.vl(1.55, 0.1, z0=2.5, z1=16.5, mul=0.7)
for z in (2.5, 9.2, 16.5): t.hl(z, 0.3, (222, 224, 222))
t.save('fac_louvre')
# MCC window groups 264-267 and 283-286 (f270): three rows of four-pane windows at z 2.0-5.4, 6.6-10.0, 12.2-15.6.
t = T(8.8, (198, 200, 198))
for u in np.arange(0, 8.8, 1.5): t.vl(u, 0.04, mul=0.86)
for z0, z1 in ((2.0, 5.4), (6.6, 10.0), (12.2, 15.6)): t.win(0.8, 8.0, z0, z1, (46, 56, 68), (226, 228, 226), nx=4, ny=2, fw=0.1)
t.save('fac_mcc_win')
# North-west clad blocks 310-326.4 (f315), one layout for the whole run, u = metres from the 310 end (47.3 m):
# right building s 0-23.8 (two short faces, the angled face 7.9-13.2, then its front 13.2-23.8), a dark slot
# s 23.8-26.7, the left building s 26.7-47.3. Dark grey metal cladding, fine seams every 0.75 m. Open ground floor
# below z 4.0 (right building) and z 2.6 (left building); pale slab edge there. Right building: glazed band z 8.5-15.2
# on the angled face and the front (s 8.7-12.5, 13.9-19.8), pale lines at z 16.6 (front) and z 12.4 (s 19.8-23.8).
# Left building: pale ledges at z 9.35 and 15.0, windows top floor s 43.7-46.5, 36.9-39.2, 26.9-30.4; middle floor
# s 43.5-46.5, 26.9-34.7; lower floor s 43.5-46.5, 26.9-30.2. Parapet 22.7-23.5.
DK = (78, 86, 94); GL = (58, 80, 94); FR = (128, 138, 146)
t = T(47.3, DK)
for z in np.arange(0.75, 23.5, 0.75): t.hl(z, 0.03, (66, 74, 82))
for u in (7.92, 13.19): t.vl(u, 0.05, mul=0.8)
t.hl(4.0, 0.3, (150, 158, 164), u0=0, u1=23.8); t.hl(2.6, 0.3, (150, 158, 164), u0=26.7, u1=47.3)
t.hl(16.6, 0.22, (150, 158, 164), u0=13.19, u1=23.8); t.hl(12.4, 0.2, (150, 158, 164), u0=19.8, u1=23.8)
for u0, u1 in ((8.7, 12.5), (13.9, 19.8)): t.win(u0, u1, 8.5, 15.2, GL, FR, nx=3, ny=2, fw=0.08)
t.rect(23.8, 26.7, 0, 23.5, (40, 46, 54))  # recessed slot between the two buildings
for z in (9.35, 15.0): t.hl(z, 0.22, (150, 158, 164), u0=26.7, u1=47.3)
for u0, u1, z0, z1 in ((43.7, 46.5, 15.6, 22.3), (36.9, 39.2, 15.6, 22.3), (26.9, 30.4, 15.6, 22.3),
                       (43.5, 46.5, 9.9, 14.5), (26.9, 34.7, 9.9, 14.5), (43.5, 46.5, 3.1, 8.8), (26.9, 30.2, 3.1, 8.8)):
    t.win(u0, u1, z0, z1, GL, FR, nx=max(1, round((u1 - u0) / 1.6)), ny=2, fw=0.08)
t.rect(0, 47.3, 22.7, 23.5, (120, 128, 134))
t.save('fac_nwdark')
# North-west recess 296-310 (f315): dark recessed floors behind pale slab edges at z 5.0, 9.5, 14.0, 18.5, top 22.
t = T(3.0, (56, 64, 74))
t.a[t.Y(22):] *= np.linspace(0.9, 1.1, t.h - t.Y(22))[:, None, None]
for z in (5.0, 9.5, 14.0, 18.5): t.rect(0, 3.0, z, z + 0.6, (178, 184, 186)); t.hl(z - 0.05, 0.1, mul=0.6)
t.vl(0.0, 0.3, col=(150, 156, 160)); t.rect(0, 3.0, 21.4, 22.0, (186, 190, 192))
t.save('fac_nwrecess')
# NW glass block skylight (f315): pale grey-blue glazing sloping up to the stand, bars every 1.2 m along it and
# every 1.5 m up the slope, a light frame at the low edge.
t = T(6.0, (190, 198, 202))
for u in np.arange(0, 6, 1.2): t.vl(u, 0.09, col=(118, 130, 140))
for z in np.arange(0, 24, 1.5): t.hl(z, 0.06, (150, 160, 168))
t.a[:] *= np.linspace(1.04, 0.9, t.h)[:, None, None]
t.save('skylight')
# Open ground floors under the NE blocks (f045): the back wall in deep shade (dark glazed doors and panels, slim
# mullions every 1.5 m, a door head at z 2.6) and the soffit under the slab.
t = T(6.0, (26, 31, 38))
for u in np.arange(0, 6, 1.5): t.vl(u, 0.08, 0, 2.6, col=(46, 52, 60))
t.hl(2.6, 0.12, (46, 52, 60)); t.rect(0, 6, 2.66, 24, (36, 40, 46))
t.save('uc_back')
t = T(6.0, (52, 58, 66))
for u in np.arange(0, 6, 1.2): t.vl(u, 0.05, col=(42, 48, 56))
t.save('uc_soffit')
t = T(6.0, (96, 100, 104))
for u in np.arange(0, 6, 1.2): t.vl(u, 0.03, col=(86, 90, 94))
t.save('uc_floor')
N = 768; a = np.ones((N, N, 3)) * np.array((168, 174, 174), float) + R.normal(0, 3, (N, N, 1)); p = N / 6.0
for r0 in (0.5, 3.5):
    for c in np.arange(0.05, 5.9, 1.0):
        y0, y1, x0, x1 = int(r0 * p), int((r0 + 2.0) * p), int(c * p), int((c + 0.9) * p)
        a[y0:y1, x0:x1] = np.array((52, 66, 92), float) + R.normal(0, 3, (y1 - y0, x1 - x0, 1))
        a[y0:y1:int(p / 3), x0:x1] = (150, 160, 176); a[y0:y1, x0:x1:int(p / 3)] = (150, 160, 176)
Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(OUT + 'solar.png'); TILE['solar'] = (6.0, 6.0)
# Gate terrace: red-brown paving on the deck behind the balustrade.
a = np.ones((N, N, 3)) * np.array((150, 112, 94), float) + R.normal(0, 4, (N, N, 1))
for k in range(0, N, N // 6): a[k:k + 2] *= 0.85; a[:, k:k + 2] *= 0.85
Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(OUT + 'terrace.png'); TILE['terrace'] = (6.0, 6.0)
json.dump(TILE, open(OUT + 'tiles.json', 'w', newline=''), indent=0); print('ok')
