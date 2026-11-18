# South-west corner buildings (photo g49 x 262-700, y 725-1000): hand-painted, no photo pixels.
# Positions in metres were measured on the photo grid (gate_grid / n7_grid / roof_grid) and unprojected through camB.
exec(open('mktex_hand.py').read().split('# ---------------------------------------------------------------- facade bay')[0])
PALE, JOINT = (226, 228, 224), (198, 202, 200)
def tiles(c, w, h, tw=1.2, th=0.6):
    for i in range(int(w / tw) + 1):
        for j in range(int(h / th) + 1):
            c.rect(i * tw, j * th, (i + 1) * tw, (j + 1) * th, tone(PALE, R.integers(-4, 5)))
    for i in range(int(w / tw) + 1): c.vline(i * tw, 0, h, JOINT, 0.03)
    for j in range(int(h / th) + 1): c.hline(j * th, JOINT, 0.03)
def poly(c, pts, col): c.d.polygon([(c.X(u), c.Y(z)) for u, z in pts], fill=col)
def ell(c, u, z, w, h, col): c.d.ellipse([c.X(u - w / 2), c.Y(z + h / 2), c.X(u + w / 2), c.Y(z - h / 2)], fill=col)

# pale tiled wall, repeat 4.8 m (sides and backs of the gate block)
c = Canvas(4.8, 4.8, 64, PALE); tiles(c, 4.8, 4.8); c.save('paletile.png', grain=1.2)

# gate block front: G1 u 0-18.7 (photo x 477-567), G2 18.7-25.9 (567-600), G3 25.9-45.4 (600-690), z 0-24
GW, GH = 46.0, 24.0
c = Canvas(GW, GH, 32, PALE); tiles(c, GW, GH)
TEAL, TEALL = (58, 100, 94), (98, 140, 132)
band = [(1.7, 6.2), (25.9, 18.6), (25.9, 12.4), (4.8, 0.0), (1.7, 0.0)]       # glass-block stair, photo (485,977)-(600,942) top, (500,995)-(600,960) bottom
poly(c, band, TEAL)
img = c.im; m = Image.new('L', img.size, 0); ImageDraw.Draw(m).polygon([(c.X(u), c.Y(z)) for u, z in band], fill=255)
g = Image.new('RGB', img.size, TEAL); gd = ImageDraw.Draw(g)
for k in range(int(GW / 0.4) + 1): gd.line([(c.X(k * 0.4), 0), (c.X(k * 0.4), img.size[1])], fill=TEALL, width=2)
for k in range(int(GH / 0.4) + 1): gd.line([(0, c.Y(k * 0.4)), (img.size[0], c.Y(k * 0.4))], fill=TEALL, width=2)
img.paste(g, (0, 0), m)
c.d.line([(c.X(4.8), c.Y(2.4)), (c.X(25.9), c.Y(14.2))], fill=(240, 242, 240), width=c.X(0.25))   # white stair rail, photo (550,972)-(600,956)
ell(c, 8.5, 19.5, 4.2, 5.7, (34, 46, 98))                                       # round window, photo centre (518,940), 20 x 16 px
ell(c, 8.5, 19.5, 2.3, 3.1, (234, 170, 42)); ell(c, 8.1, 20.0, 1.1, 1.4, (124, 30, 46))
for z in (12.0, 4.6): ell(c, 30.7, z, 1.3, 1.4, (44, 48, 54))                   # portholes, photo (622,962) and (622,983)
c.rect(32.9, 4.4, 34.1, 5.6, (44, 48, 54))   # sign at photo (635,982) as a blank panel (director 2026-11-18 "C: no lettering")
c.rect(34.6, 0.0, 43.3, 12.0, (30, 34, 40))                                     # dark opening, photo x 640-680
c.rect(43.6, 4.0, 44.6, 9.0, (244, 246, 246))                                   # white sign board, photo x 680
c.save('gatefront.png', grain=1.2)

# navy block walls (repeat 3 m) and its maroon front with the gate "7" (9.7 x 8.5 m)
NAVY, MAR = (30, 40, 78), (112, 26, 40)
c = Canvas(3.0, 3.0, 64, NAVY); c.vline(0.02, 0, 3, tone(NAVY, -10), 0.04); c.hline(0.02, tone(NAVY, -10), 0.04); c.save('navywall.png', grain=1.5)
c = Canvas(9.7, 8.5, 64, MAR); c.rect(0, 7.3, 9.7, 8.5, NAVY)
# the gate "7" left off: blank maroon panel (director 2026-11-18 "C: no lettering")
c.save('n7front.png', grain=1.5)
c = Canvas(10.0, 10.0, 32, (34, 46, 84))                                        # roof: white upstand line set in from the edge
for a, b in (((0.8, 0.8), (9.2, 0.95)), ((0.8, 9.05), (9.2, 9.2)), ((0.8, 0.8), (0.95, 9.2)), ((9.05, 0.8), (9.2, 9.2))): c.rect(a[0], a[1], b[0], b[1], (230, 232, 232))
for u, z in ((3.0, 6.5), (5.0, 3.2), (6.6, 7.4), (2.2, 2.4)): ell(c, u, z, 0.35, 0.35, (230, 232, 232))
c.save('n7roof.png', grain=1.0)

# white rendered walls (repeat 3 m), dark roof deck with white tables and timber benches (repeat 6 m), skylight lantern top
WH = (238, 240, 238)
c = Canvas(3.0, 3.0, 64, WH); c.vline(0.02, 0, 3, (216, 218, 216), 0.03); c.hline(0.02, (216, 218, 216), 0.03); c.save('whiterender.png', grain=1.0)
c = Canvas(6.0, 6.0, 48, (44, 48, 54))
for u, z in ((1.0, 1.2), (2.6, 4.4), (4.2, 1.8), (5.2, 4.9), (1.6, 3.4), (3.6, 2.9)): ell(c, u, z, 0.55, 0.55, (226, 228, 228))
c.rect(0.6, 5.0, 2.4, 5.35, (120, 86, 52)); c.rect(3.4, 0.4, 5.4, 0.75, (120, 86, 52))
c.save('deckdots.png', grain=1.5)
c = Canvas(12.0, 12.0, 32, (236, 238, 238))
for i in range(3):
    for j in range(2): c.rect(0.7 + i * 3.7, 0.7 + j * 5.4, 0.7 + i * 3.7 + 3.3, 0.7 + j * 5.4 + 5.0, (136, 158, 178))
c.save('skylight.png', grain=1.0)
