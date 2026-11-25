# South-west corner buildings (photo g49 x 262-700, y 725-1000): hand-painted, no photo pixels.
# Positions in metres were measured on the photo grid (gate_grid / n7_grid / roof_grid) and unprojected through camB.
exec(open('mktex_hand.py').read().split('# ---------------------------------------------------------------- facade bay')[0])
PALE, JOINT = (226, 228, 224), (198, 202, 200)
def tiles(c, w, h, tw=1.2, th=0.6):
    for i in range(int(w / tw) + 1):
        for j in range(int(h / th) + 1):
            c.rect(i * tw, j * th, (i + 1) * tw, (j + 1) * th, tone(PALE, R.integers(-8, 9)))
    for i in range(int(w / tw) + 1): c.vline(i * tw, 0, h, JOINT, 0.03)
    for j in range(int(h / th) + 1): c.hline(j * th, JOINT, 0.03)
def poly(c, pts, col): c.d.polygon([(c.X(u), c.Y(z)) for u, z in pts], fill=col)
def ell(c, u, z, w, h, col): c.d.ellipse([c.X(u - w / 2), c.Y(z + h / 2), c.X(u + w / 2), c.Y(z - h / 2)], fill=col)

# pale tiled wall, repeat 4.8 m (sides and backs of the gate block)
c = Canvas(4.8, 4.8, 64, PALE); tiles(c, 4.8, 4.8); weather(c, mo=3, mc=1.2, streaks=22, sl=(0.6, 2.4), sk=-20, tops=[4.8, 2.4], seed=21); c.save('paletile.png', grain=1.2)

# gate block front: G1 u 0-18.7 (photo x 477-567), G2 18.7-25.9 (567-600), G3 25.9-45.4 (600-690), z 0-24
GW, GH = 46.0, 24.0
c = Canvas(GW, GH, 32, PALE); tiles(c, GW, GH)
TEAL, TEALL = (58, 100, 94), (98, 140, 132)
# v8 (no painted geometry): the glass-block stair, its rail, the round window, the portholes, the signs and the dark
# opening are all modelled in sw.py; this face is the pale tiles only.
c.save('gatefront.png', grain=1.2)
# glass block (the stair's glazing, 0.4 m blocks with pale joints), 4 m tile; the round window's coloured glass; dark glass
c = Canvas(4.0, 4.0, 48, TEAL)
for k in range(11): c.vline(k * 0.4, 0, 4.0, TEALL, 0.03); c.hline(k * 0.4, TEALL, 0.03)
c.save('glassblock.png', grain=0.8)
c = Canvas(4.2, 5.7, 64, (34, 46, 98)); ell(c, 2.1, 2.85, 2.3, 3.1, (234, 170, 42)); ell(c, 1.7, 3.35, 1.1, 1.4, (124, 30, 46))
c.save('roundglass.png', grain=0.5)
c = Canvas(4.0, 4.0, 16, (30, 34, 40)); c.save('darkglass.png', grain=0.5)
c = Canvas(2.0, 2.0, 64, (120, 86, 52))
for k in range(10): c.hline(k * 0.2, (100, 70, 42), 0.015)
c.save('timber.png', grain=2.0)

# navy block walls (repeat 3 m) and its maroon front with the gate "7" (9.7 x 8.5 m)
NAVY, MAR = (30, 40, 78), (112, 26, 40)
c = Canvas(9.0, 9.0, 48, NAVY)
for k in range(3): c.vline(k * 3.0 + 0.02, 0, 9, tone(NAVY, -10), 0.04); c.hline(k * 3.0 + 0.02, tone(NAVY, -10), 0.04)   # 3 m panel joints, 9 m tile
weather(c, mo=1.2, mc=0.8, streaks=420, sl=(0.6, 3.6), sk=-30, tops=[9.0, 6.0, 3.0], seed=22); c.save('navywall.png', grain=1.5)
# director 2026-11-19 gate: "a navy block with a maroon strip only at the bottom" (g49 330,900,450,1000): navy above 3.4 m,
# maroon strip 0-3.4 m holding the white "7" (2.5 m tall, 3.2 m from the east corner; u runs east to west on this face)
SH = 3.4
c = Canvas(8.5, 8.5, 64, NAVY); c.rect(0, 0, 8.5, SH, MAR)
c.hline(SH + 0.02, tone(NAVY, -10), 0.04)
# director 2026-11-18 "C: no lettering": the gate's "7" is left off (plain maroon strip)
weather(c, mo=1.2, mc=0.8, seed=23)   # flat paint, as g49 (330,900,450,1000): no run-off streaks
c.save('n7front.png', grain=1.5)
# NE face of the same block (photo g49 left face): navy with the same maroon strip, 9 m tile
c = Canvas(9.0, 8.5, 48, NAVY); c.rect(0, 0, 9.0, SH, MAR)
c.hline(SH + 0.02, tone(NAVY, -10), 0.04)
weather(c, mo=1.2, mc=0.8, seed=26); c.save('n7strip.png', grain=1.5)   # flat paint, no streaks
c = Canvas(10.0, 10.0, 32, (34, 46, 84))                                        # roof membrane; its upstand and vents are modelled (sw.py)
c.save('n7roof.png', grain=1.0)

# white rendered walls (repeat 3 m), dark roof deck with white tables and timber benches (repeat 6 m), skylight lantern top
WH = (238, 240, 238)
c = Canvas(9.0, 9.0, 48, WH)
for k in range(3): c.vline(k * 3.0 + 0.02, 0, 9, (216, 218, 216), 0.03); c.hline(k * 3.0 + 0.02, (216, 218, 216), 0.03)   # 3 m render joints, 9 m tile
weather(c, mo=3.0, mc=0.8, streaks=150, sl=(0.8, 3.8), sk=-22, tops=[9.0, 6.0, 3.0], seed=24); c.save('whiterender.png', grain=1.0)
c = Canvas(6.0, 6.0, 48, (44, 48, 54))                                         # deck; its tables and benches are modelled (sw.py)
for k in range(5): c.hline(k * 1.2 + 0.01, (36, 40, 46), 0.02)
c.save('deckdots.png', grain=1.5)
c = Canvas(12.0, 12.0, 32, (136, 158, 178))                                     # lantern glass; its white frames are modelled (sw.py)
c.save('skylight.png', grain=1.0)
