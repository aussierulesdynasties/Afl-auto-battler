"""Type 1 bare council oval (ref photo grid/t1_council_grid.jpg). Camera on the field at (0, 46, 1.6) looking +y
(straight out at the fence), horizon row 742, 69.4 deg lens: fence 22 m away, scoreboard 24.9 m on a 0.5 m bank."""
import json, math
HZ, FPX, CY = 742, 1443.0, 750
CAM = (0.0, 46.0)
def X(u, Z): return (u - 1000) * Z / FPX
def part(u0, u1, Z, **kw):
    a, b = X(u0, Z), X(u1, Z)
    d = dict(x=round((a + b) / 2, 3), y=round(CAM[1] + Z, 3), rot=0.0, w=round(b - a, 3)); d.update(kw); return d

ZF, ZSB, ZLED = 22.0, 24.9, 27.4
spec = {"name": "oval_t1_council", "seed": 1,
        "field": {"a": 80.0, "b": 65.0, "turf": "turf", "apron": 3.0},
        "surround": [{"d0": 3.0, "d1": 3.3, "tex": "turf_dry"}, {"d0": 3.3, "d1": 5.2, "z0": 0.0, "z1": 0.5, "tex": "turf_dry"},
                     {"d0": 5.2, "d1": 30.0, "z0": 0.5, "z1": 0.5, "tex": "turf_dry"}],
        "outer": {"d": 400, "tex": "turf_dry"},
        "fence": {"type": "chainlink", "tex": "chainlink_black", "d": 3.0, "h": 0.93, "post_tex": "dark_metal", "rails": [0.9, 0.05]},
        "posts": {"goal_h": 12.0, "behind_h": 7.0, "pad": "pad_red"}}

# shed on the fence line (u 205-435, top v 650), 2.4 m deep, green iron sides
shed = part(205, 435, ZF, dpt=2.4, h=3.0, wall="iron_green", front="iron_green", roof="flat", roof_tex="iron_zinc", parapet="steel_grey")
# scoreboard building on the bank (u 742-1233, base v 805 = 0.5 m, face 6.09 m), brick
sb = part(742, 1233, ZSB, dpt=3.0, h=6.6, wall="brick_red", front="brick_red", roof="flat", roof_tex="iron_zinc", parapet="dark_metal")
spec["buildings"] = [shed, sb]
spec["boxes"] = [dict(part(742, 1233, ZSB, dpt=3.0, wall="brick_red"), z0=0.0, h=0.5)]   # plinth into the bank
for b in spec["buildings"]:
    b.pop("w_", None)
sb_face = dict(part(742, 1233, ZSB), z0=0.5, z1=0.5 + 353 / 58.0, tex="t1_scoreboard")
top = dict(part(775, 1193, ZSB - 0.15), z0=0.5 + (805 - 505) / 58.0, z1=0.5 + (805 - 436) / 58.0, tex="t1_topsign", back="dark_metal")
shed_face = dict(part(205, 435, ZF), z0=0.0, z1=3.0, tex="t1_shed_front")
led = dict(part(1473, 1843, ZLED), z0=1.64, z1=6.25, tex="t1_led", back="dark_metal", off=0.0)
spec["panels"] = [sb_face, top, shed_face, led]
# fence boards hung on the field side of the fence (z 0.03-0.96)
for nm, a, b in (("t1_s1", 25, 187), ("t1_s3", 768, 920), ("t1_s4", 1320, 1462), ("t1_s5", 1465, 1615), ("t1_s6", 1618, 1788),
                 ("t1_s7", 1790, 1838), ("t1_s8", 1838, 1940), ("t1_s9", 1940, 2060)):
    spec["panels"].append(dict(part(a, b, ZF - 0.08), z0=0.03, z1=0.96, tex=nm, back="dark_metal"))
# LED screen legs and frame box, light pole beside the scoreboard
lx0, lx1 = X(1480, ZLED), X(1825, ZLED)
spec["poles"] = [{"x": round(x, 2), "y": CAM[1] + ZLED + 0.1, "h": 1.7, "r": 0.08, "tex": "dark_metal"} for x in (lx0, X(1765, ZLED), lx1)]
spec["boxes"].append(dict(part(1473, 1843, ZLED + 0.02, dpt=0.35, wall="dark_metal"), z0=1.64, h=6.25))
pole = {"x": round(X(1305, ZSB + 0.5), 2), "y": CAM[1] + ZSB + 0.5, "h": 26, "r0": 0.19, "r1": 0.15, "rows": 2, "cols": 3}
# era-appropriate generic towers off camera, matching the one in the photo
spec["lights"] = [pole] + [{"t": math.radians(a), "d": 7.0, "h": 26, "r0": 0.19, "r1": 0.15, "rows": 2, "cols": 3} for a in (30, 150, 210, 266, 330)]
# off camera (generic, type 1): small brick clubrooms opposite, coaches' boxes, interchange benches
spec["buildings"].append({"t": math.radians(270), "d": 9.0, "w": 18.0, "dpt": 10.0, "h": 3.4, "wall": "brick_red", "front": "brick_red_window",
                          "roof": "skillion", "rise": 1.0, "roof_tex": "iron_zinc", "verandah": {"d": 2.5, "h": 2.8}})
spec["coaches"] = [{"t": math.radians(a), "d": 6.0, "w": 3.6, "wall": "iron_cream"} for a in (255, 285)]
spec["benches"] = [{"t": math.radians(a), "d": 4.2, "w": 7.0, "h": 2.0, "wall": "iron_zinc"} for a in (258, 282)]
spec["scoreboards"] = []
# director 2026-11-18: no sponsor boards (bare fence); sponsor panels kept under off_panels, build.py ignores them
spec["off_panels"] = [p for p in spec["panels"] if p["tex"] not in ("t1_scoreboard", "t1_led")]
spec["panels"] = [p for p in spec["panels"] if p["tex"] in ("t1_scoreboard", "t1_led")]
json.dump(spec, open("spec/t1_council.json", "w"), indent=1)

pitch = math.atan((HZ - CY) / FPX)
job = {"out": "../out/t1/r", "res": [2000, 1500], "samples": 32, "sun": {"az": 230, "el": 40, "power": 4.0},
       "views": [{"name": "match", "cam": [CAM[0], CAM[1], 1.6], "look": [CAM[0], CAM[1] + 100, 1.6 + 100 * math.tan(pitch)], "fov_h": 69.4}]}
json.dump(job, open("spec/t1_job_match.json", "w"), indent=1)
print("ok")
