"""The house street north-east of the ground (the st_house view), traced by eye off two straight-down Google Earth
shots 150 m up (2026-11-23), where the machine footprints (OpenStreetMap, Microsoft) had the townhouses of no. 31,
nos. 2, 4 and 6 and their neighbours in the wrong places and one storey tall (PC check r5).

  python3 houses_traced.py <tiles2 workdir>     # writes houses_traced.json beside this file

Only outlines, storeys and each roof's median colour are kept, never imagery (docs/MCG_STANDARD.md).

The shots: 'c' centred 250 m east, 150 m north of the pitch centre, 'd' 260 east, 200 north, both
https://earth.google.com/web/@<lat>,<lon>,10.0a,150.0d,35y,0h,0t,0r. Each outline below was read off a 2 m grid
drawn with the 800 m shots' scale (ge_trees.py: 25.58 degrees over the 720 px crop). Registered against the 800 m
shot that holds them (tiles2 t09, whose scale the shape audit checked), the 150 m shots come out at 0.84 of that
scale and 0.5 m west, 1.0 m south; both shots agree to 0.5-1 m after that (the dark block east of no. 33 is in
both). A roof stands h metres up, so it sits (H - h)/H as far from the shot's centre as drawn (H = 150/0.84 m).

Storeys and roofs from the oblique Google Earth view (qa/views.json st_house): flat2 two storeys under a flat roof
(the townhouses), flat1 one storey flat (units, garages), hip1/hip2 hipped houses, gable2.

Walls, windows and solar panels from the same oblique (PC check r6: the townhouses were blank white boxes). Its
walls face the camera in shade, so their colour is named by eye (white render, red brick, blue weatherboard ...)
and set as the finish's colour in sun, linear as the game's other walls; never sampled pixels. Each house's
detail flags (GroundModels._add_buildings, SURROUNDS "house_detail"): WINDOWS a window per 3.4 m of wall on each
storey, PARAPET a 0.5 m parapet round a flat roof, SOLAR a rack of panels on the roof (on a pitched roof, the slope
facing most north)."""
import json, math, os, sys
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
SCALE, H = 0.84, 150.0 / 0.84
SHOT = {"c": (250.0, 150.0, -0.5, -1.0), "d": (260.0, 200.0, 0.0, -1.0)}   # centre east, north; registration
KIND = {"flat2": 6.4, "flat1": 3.2, "hip1": -2.7, "hip2": -5.6, "gable2": -105.6}
TOP = {"flat2": 6.4, "flat1": 3.2, "hip1": 4.5, "hip2": 7.5, "gable2": 8.0}  # roof height for the lean

WINDOWS, PARAPET, SOLAR = 1, 2, 4
RENDER, CREAM, BRICK, BROWN = (0.84, 0.85, 0.84), (0.86, 0.82, 0.74), (0.56, 0.33, 0.27), (0.6, 0.44, 0.36)
WALL = {"33": BROWN, "31 dark block": (0.3, 0.33, 0.36), "31 north-west": (0.62, 0.64, 0.66), "4 front": BRICK,
        "4 rear": BRICK, "6 front": BRICK, "6 rear": BRICK, "27": (0.62, 0.7, 0.8), "27 garage": (0.6, 0.62, 0.62),
        "29": CREAM, "29 shed": (0.6, 0.62, 0.62), "25": (0.88, 0.86, 0.8), "8A": (0.78, 0.8, 0.82),
        "53": (0.5, 0.52, 0.54), "61": (0.6, 0.64, 0.7)}                   # the rest white render
SOLAR_ON = {"31 south-west", "31 east, south", "27", "8A"}
NO_WINDOWS = {"27 annex", "27 garage", "29 shed", "31 south annex"}


def detail(name, kind):
    f = 0 if name in NO_WINDOWS else WINDOWS
    if kind == "flat2":
        f |= PARAPET
    if name in SOLAR_ON:
        f |= SOLAR
    return f


# name, shot, kind, outline (east, north as read off the shot's grid)
TRACED = [
    ("33", "c", "hip1", [(220.0, 177.4), (232.9, 176.8), (232.5, 170.1), (219.8, 170.8)]),
    ("31 dark block", "c", "flat2", [(234.4, 178.1), (241.7, 178.1), (241.7, 168.9), (234.4, 168.9)]),
    ("31 west block", "c", "flat2", [(214.2, 168.4), (229.8, 167.6), (229.6, 161.3), (214.0, 162.7)]),
    ("31 middle block", "c", "flat2", [(235.9, 166.1), (251.3, 164.3), (251.2, 158.8), (235.4, 160.3)]),
    ("31 north-west", "d", "flat2", [(244.4, 188.7), (252.3, 188.7), (252.3, 187.6), (256.6, 187.6), (256.6, 181.3),
                                      (252.3, 181.3), (252.3, 179.1), (244.4, 179.1)]),
    ("31 north-east", "d", "flat2", [(274.7, 186.9), (287.5, 186.9), (286.8, 176.8), (279.6, 176.8), (279.6, 180.1),
                                      (274.7, 180.1)]),
    ("31 pair", "c", "flat2", [(256.1, 168.3), (271.1, 166.8), (270.3, 160.0), (255.9, 160.1)]),
    ("31 east, north", "c", "flat2", [(275.2, 168.1), (283.7, 166.9), (282.5, 154.9), (273.8, 156.1)]),
    ("31 east, south", "c", "flat2", [(274.2, 155.0), (283.6, 154.6), (283.6, 142.0), (274.0, 142.2)]),
    ("31 south-west", "c", "flat2", [(239.4, 153.8), (253.5, 153.8), (253.5, 144.2), (239.4, 144.2)]),
    ("31 south", "c", "flat2", [(255.3, 152.4), (265.8, 152.4), (265.8, 143.3), (255.3, 143.3)]),
    ("31 south annex", "c", "flat1", [(265.8, 149.4), (270.4, 149.4), (270.4, 140.7), (265.8, 140.7)]),
    ("2 north", "c", "flat2", [(237.3, 139.3), (247.6, 139.3), (247.6, 130.1), (237.3, 130.1)]),
    ("2 middle", "c", "flat2", [(236.6, 127.5), (245.5, 127.5), (245.5, 117.8), (236.6, 117.8)]),
    ("4 front", "c", "flat1", [(254.3, 136.5), (262.1, 136.5), (262.1, 128.8), (254.3, 128.8)]),
    ("4 rear", "c", "flat1", [(252.5, 128.6), (260.7, 128.6), (260.7, 116.2), (252.5, 116.2)]),
    ("6 front", "c", "flat1", [(268.8, 136.5), (281.3, 136.5), (281.3, 126.3), (268.8, 126.3)]),
    ("6 rear", "c", "flat1", [(267.3, 126.3), (274.2, 126.3), (274.2, 119.5), (267.3, 119.5)]),
    ("27", "c", "gable2", [(209.0, 143.9), (217.7, 143.9), (217.7, 133.4), (209.0, 133.4)]),
    ("27 annex", "c", "flat1", [(217.7, 138.7), (221.9, 138.7), (221.9, 134.7), (217.7, 134.7)]),
    ("27 garage", "c", "flat1", [(227.9, 136.1), (234.5, 136.1), (234.5, 131.8), (227.9, 131.8)]),
    ("29", "c", "hip2", [(209.8, 157.1), (226.0, 157.1), (226.0, 148.2), (209.8, 148.2)]),
    ("29 shed", "c", "flat1", [(234.4, 155.9), (238.7, 155.9), (238.7, 152.2), (234.4, 152.2)]),
    ("25", "c", "hip1", [(205.0, 130.8), (220.8, 130.8), (220.8, 120.4), (205.0, 120.4)]),
    ("8A", "c", "hip2", [(285.0, 133.8), (292.8, 133.8), (292.8, 118.0), (285.0, 118.0)]),
    ("53", "d", "hip2", [(219.4, 212.8), (234.8, 211.6), (232.0, 192.3), (220.0, 192.3)]),
    ("55", "d", "flat2", [(235.0, 210.9), (247.3, 210.9), (247.3, 200.1), (235.0, 200.1)]),
    ("57", "d", "flat2", [(250.1, 209.7), (260.6, 209.7), (260.6, 199.6), (250.1, 199.6)]),
    ("59", "d", "hip1", [(264.1, 209.0), (273.8, 209.0), (273.8, 198.7), (273.1, 198.7), (273.1, 191.6), (266.7, 191.6),
                         (266.7, 198.7), (264.1, 198.7)]),
    ("61", "d", "hip2", [(278.0, 206.7), (292.4, 206.7), (292.4, 193.5), (287.5, 193.5), (287.5, 197.7),
                         (278.0, 197.7)]),
    ("63", "d", "hip2", [(294.0, 199.5), (304.8, 199.5), (304.8, 184.4), (294.0, 184.4)]),
]


def true_outline(shot, kind, pts):
    ce, cn, dx, dy = SHOT[shot]
    lean = (H - TOP[kind]) / H
    out = []
    for e, n in pts:
        e2 = ce + dx + (e - ce) / SCALE
        n2 = cn + dy + (n - cn) / SCALE
        out.append((ce + dx + (e2 - ce - dx) * lean, cn + dy + (n2 - cn - dy) * lean))
    return out


def main(work):
    from PIL import Image, ImageDraw, ImageFilter
    C = json.load(open(os.path.join(work, "centres.json")))
    K = 360.0 / (800.0 * math.tan(math.radians(12.79)))
    out = []
    for name, shot, kind, pts in TRACED:
        en = true_outline(shot, kind, pts)
        c = np.mean(en, axis=0)
        i = int(np.argmin([(a - c[0]) ** 2 + (b - c[1]) ** 2 for a, b in C]))
        im = Image.open(os.path.join(work, "ge", "t%02d.png" % i)).convert("RGB")
        q = [(640 + (e - C[i][0]) * K, 360 - (n - C[i][1]) * K) for e, n in en]
        m = Image.new("L", im.size, 0)
        ImageDraw.Draw(m).polygon(q, fill=255)
        mm = np.asarray(m.filter(ImageFilter.MinFilter(3))) > 0
        col = np.median(np.asarray(im).astype(float)[mm], axis=0)
        col = np.clip((col - 14.0) * 1.08, 8, 255) / 255.0                 # as houses_ge.py: the aerial's haze
        out.append({"name": name, "kind": kind, "h": KIND[kind], "wall": list(WALL.get(name, RENDER)),
                    "flags": detail(name, kind),
                    "rgb": [round(float(v) ** 2.2, 4) for v in col],
                    "pts": [[round(e, 2), round(-n, 2)] for e, n in en]})        # model x (east), z (south)
    json.dump(out, open(os.path.join(HERE, "houses_traced.json"), "w"), indent=0)
    print(len(out), "traced")


if __name__ == "__main__":
    main(sys.argv[1])
