# Hand-made procedural textures (no photo pixels). Each tile covers a stated real size so detail is crisp close up.
from PIL import Image, ImageDraw, ImageFilter
import numpy as np, os, sys
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
rng = np.random.RandomState(7)
N = 1024
def save(n, a): Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).save(out + '/' + n + '.png')
def base(c, amp=2.0, n=N):
    a = np.ones((n, n, 3)) * np.array(c, float)
    return a + rng.normal(0, amp, (n, n, 1))
def shade(a, y0, y1, x0, x1, c): a[y0:y1, x0:x1] = np.array(c, float)
# brick: tile = 2.0 m wide x 1.0 m high -> 230 mm brick + 10 mm joint, 76 mm course + 10 mm joint
def brick(c, mortar, name):
    a = np.ones((N, N, 3)) * np.array(mortar, float)
    bw = N / (2.0 / 0.24); bh = N / (1.0 / 0.086)
    rows = int(round(N / bh)); bh = N / rows
    for r in range(rows):
        off = 0 if r % 2 == 0 else bw / 2
        x = -off
        while x < N:
            k = rng.uniform(-14, 14)
            col = np.array(c) + k + rng.uniform(-6, 6, 3)
            y0 = int(r * bh + 1); y1 = int((r + 1) * bh - 2)
            x0 = int(max(0, x + 1)); x1 = int(min(N, x + bw - 2))
            if x1 > x0: a[y0:y1, x0:x1] = col
            x += bw
    a += rng.normal(0, 3, (N, N, 1))
    save(name, a)
brick((184, 104, 62), (196, 186, 170), 'brick')
brick((150, 70, 46), (190, 180, 165), 'brickdark')
# seats: tile = 4 m wide x 4 rows (0.8 m deep each). Each row: concrete tread, then a row of moulded seats (0.5 m pitch).
def seats(seat, name, tread=(176, 176, 170), riser=(128, 128, 124)):
    a = base(tread, 2.5)
    rh = N // 4; sw = N / 8
    for r in range(4):
        y = r * rh
        shade(a, y + int(rh * 0.82), y + rh, 0, N, riser)
        for s in range(8):
            x0 = int(s * sw + sw * 0.08); x1 = int((s + 1) * sw - sw * 0.08)
            shade(a, y + int(rh * 0.18), y + int(rh * 0.40), x0, x1, np.array(seat) * 0.78)  # back
            shade(a, y + int(rh * 0.40), y + int(rh * 0.62), x0, x1, seat)  # pan
            shade(a, y + int(rh * 0.62), y + int(rh * 0.66), x0, x1, np.array(seat) * 0.6)  # lip shadow
    a += rng.normal(0, 1.5, (N, N, 1))
    save(name, a)
seats((34, 62, 120), 'seats')          # navy plastic seats (Carlton)
seats((40, 70, 132), 'seatslegends')
# terrace: tile = 4 m x 4 steps of 0.8 m, plain concrete steps with crush rails every 4 m
a = base((168, 168, 162), 3)
for r in range(4):
    y = r * N // 4
    shade(a, y + int(N / 4 * 0.80), y + N // 4, 0, N, (122, 122, 118))
    shade(a, y + int(N / 4 * 0.80) - 4, y + int(N / 4 * 0.80), 0, N, (196, 196, 190))
shade(a, 0, N, 0, 10, (110, 112, 112))
save('terrace', a)
# corrugated roof sheet: tile = 4 m, rib every 0.2 m
def roof(c, name, pitch=0.2):
    a = base(c, 1.5)
    n = int(4 / pitch); w = N / n
    x = np.arange(N); ph = (x % w) / w
    prof = 0.85 + 0.15 * np.cos(ph * 2 * np.pi)
    a *= prof[None, :, None]
    for k in range(1, 4): shade(a, k * N // 4 - 2, k * N // 4 + 1, 0, N, np.array(c) * 0.82)  # sheet laps
    save(name, a)
roof((232, 234, 230), 'roof'); roof((150, 156, 158), 'greyroof'); roof((196, 200, 200), 'sawtooth'); roof((166, 175, 188), 'roofgrey')
save('steeldark', base((70, 76, 82), 2, 256))
# concrete: tile 4 m, formwork panels 1.2 m x 2.4 m with tie holes
a = base((206, 204, 196), 3)
for x in range(0, N, int(N / 4 * 1.2)): shade(a, 0, N, x, x + 3, (178, 176, 168))
for y in range(0, N, int(N / 4 * 2.4)): shade(a, y, y + 3, 0, N, (178, 176, 168))
save('concrete', a)
save('white', base((236, 238, 234), 1.5, 256))
save('under', base((92, 96, 98), 2, 256))
# glass bays: tile = 3 m wide x 3 m high: frame, mullion, transom
def glass(frame, name, tint=(46, 64, 80)):
    a = np.ones((N, N, 3)) * np.array(frame, float)
    m = int(N * 0.04)
    for (x0, x1) in ((m, N // 2 - m // 2), (N // 2 + m // 2, N - m)):
        for (y0, y1) in ((m, int(N * 0.7) - m // 2), (int(N * 0.7) + m // 2, N - int(N * 0.18))):
            g = np.linspace(1.15, 0.85, y1 - y0)[:, None, None]
            a[y0:y1, x0:x1] = np.array(tint) * g
            a[y0:y0 + int((y1 - y0) * 0.3), x0:x0 + int((x1 - x0) * 0.25)] += 18  # sky glint
    shade(a, N - int(N * 0.18), N, 0, N, (196, 108, 66))  # spandrel brick colour band
    save(name, a)
glass((232, 232, 226), 'glass')
glass((70, 72, 74), 'glassdark')
# timber cladding (Heroes facade): tile 2 m, vertical boards 0.15 m
a = base((176, 104, 56), 2)
w = N / (2 / 0.15)
for i in range(int(2 / 0.15) + 1):
    x = int(i * w); shade(a, 0, N, x, x + 4, (128, 74, 40))
    a[:, x + 4:int(x + w)] += rng.uniform(-10, 10)
save('timber', a)
save('wood', a)
# steel: light grey painted
save('steel', base((206, 210, 212), 2, 256))
# grass with mowing stripes: tile 20 m, stripes 5 m
a = base((58, 126, 60), 4)
for k in range(4):
    if k % 2: a[:, k * N // 4:(k + 1) * N // 4] *= 0.9
save('grass', a)
save('park', base((80, 128, 70), 5))
save('asphalt', base((122, 126, 128), 6))
save('pool', base((70, 170, 205), 2, 256))
save('yellow', base((230, 190, 40), 2, 256))
save('red', base((175, 45, 50), 2, 256))
save('orange', base((200, 110, 45), 2, 256))
save('fosterblue', base((30, 70, 140), 2, 256))
save('scoreblue', base((50, 100, 165), 2, 256))
print('ok')
