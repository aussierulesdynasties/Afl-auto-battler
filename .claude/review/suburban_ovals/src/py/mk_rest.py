"""Quick generic specs for ovals 2, 3, 5, 6 (director 2026-11-18: "just functional, basic, suburban footy ovals").
Layouts read off the type photos (t3, t6) or the type description (t2, t5); placed by boundary angle t (deg) and
distance d out from the boundary line. t 90 = the main (camera) side."""
import json, math
R = math.radians
def T(**k):
    if "t" in k: k["t"] = R(k["t"])
    for a in ("t0", "t1"):
        if a in k: k[a] = R(k[a])
    return k
FIELD = {"a": 80.0, "b": 65.0, "turf": "turf", "apron": 3.0}
POSTS = lambda pad: {"goal_h": 12.0, "behind_h": 7.0, "pad": pad}
def towers(angs, h=26, d=7.0, led=False):
    return [T(t=a, d=d, h=h, r0=0.19, r1=0.15, rows=2, cols=3, led=led) for a in angs]
def coaches(wall):
    return [T(t=a, d=6.0, w=3.6, wall=wall) for a in (255, 285)]
def benches(wall, h=2.0):
    return [T(t=a, d=4.2, w=7.0, h=h, wall=wall) for a in (259, 281)]
specs = {}

# ---- t3 minor VFL/SANFL ground: brick clubrooms with a glazed upper floor + small covered two-tier stand ----
specs["t3_minor"] = {
    "name": "oval_t3_minor", "seed": 3, "field": FIELD,
    "surround": [{"d0": 3.0, "d1": 9.0, "tex": "concrete"}, {"d0": 9.0, "d1": 40.0, "tex": "turf_dry"}],
    "outer": {"d": 400, "tex": "turf_dry"},
    "fence": {"type": "chainlink", "tex": "chainlink_black", "d": 3.0, "h": 1.1, "post_tex": "dark_metal", "rails": [1.08, 0.05]},
    "posts": POSTS("pad_blue"),
    "buildings": [
        T(t=108.5, d=8.0, w=24.0, dpt=12.0, h=3.4, wall="brick_red", front="brick_red_window", roof="gable", rise=2.0,
          roof_tex="iron_green", overhang=0.6,
          upper={"h": 3.2, "front": "glass_curtain", "wall": "brick_red", "set": 1.5, "rail": True, "roof_tex": "iron_green"},
          doors=[[-6.0, 1.0, 2.1, "door_white"], [5.0, 1.0, 2.1, "door_white"]]),
        T(t=58, d=8.0, w=12.0, dpt=8.0, h=3.0, wall="brick_cream", front="brick_cream_window", roof="gable", rise=1.6,
          roof_tex="iron_red", overhang=0.5),
        T(t=270, d=8.0, w=14.0, dpt=8.0, h=3.0, wall="brick_red", front="brick_red_window", roof="skillion", rise=0.8,
          roof_tex="iron_zinc", verandah={"d": 2.4, "h": 2.6}),
    ],
    "stands": [T(t=84, d=7.0, len=42.0, rows=7, tread=0.8, riser=0.38, base=3.2, seat="seats_white", riser_tex="concrete",
                 front="brick_red", back="iron_green", back_h=1.0, ends="brick_red", roof="skillion", roof_front=11.4,
                 roof_over=2.5, roof_tex="iron_green", bay=7.0, post="dark_metal", rail=True,
                 doors=[[-12.0, 1.0, 2.1, "door_white"], [-4.0, 1.0, 2.1, "door_white"], [6.0, 1.0, 2.1, "door_white"], [14.0, 1.0, 2.1, "door_white"]],
                 stairs=[{"x": -19.5, "top": 3.2, "dir": 1, "run": 5.0, "y": -1.1}])],
    "coaches": [T(t=a, d=4.5, w=3.6, wall="dark_metal") for a in (80, 96)],
    "benches": [T(t=a, d=3.6, w=6.5, h=2.0, wall="dark_metal") for a in (83, 93)],
    "scoreboards": [T(t=270, d=12.0, w=8.0, h=3.6, lift=2.6, tex="scoreboard_manual", back="iron_green", box=True)],
    "lights": towers((30, 150, 210, 250, 290, 330)),
}

# ---- t6 northern ground: long low dark clubhouse with a white skillion roof and verandah, palms, LED towers ----
specs["t6_north"] = {
    "name": "oval_t6_north", "seed": 6, "field": dict(FIELD, turf="turf_tropic"),
    "surround": [{"d0": 3.0, "d1": 7.0, "tex": "red_earth"}, {"d0": 6.0, "d1": 40.0, "tex": "turf_dry"}],
    "outer": {"d": 400, "tex": "turf_dry"},
    "fence": {"type": "chainlink", "tex": "chainlink_black", "d": 3.0, "h": 1.0, "post_tex": "dark_metal", "rails": [0.98, 0.05]},
    "posts": POSTS("pad_red"),
    "buildings": [
        T(t=92, d=7.0, w=46.0, dpt=10.0, h=3.0, wall="clad_charcoal", front="clad_charcoal", roof="skillion", rise=1.4,
          roof_tex="white_paint", overhang=0.6, verandah={"d": 3.2, "h": 2.7, "post": "white_paint", "tex": "white_paint", "bay": 4.6},
          doors=[[-14.0, 1.0, 2.1, "door_white"], [-2.0, 1.8, 2.1, "door_white"], [12.0, 1.0, 2.1, "door_white"]]),
    ],
    "sails": [T(t=270, d=6.0, len=18.0, rows=4, n=3, tex="sail_white", seat="seats_white")],
    "coaches": coaches("white_paint"), "benches": benches("white_paint"),
    "scoreboards": [T(t=0, d=10.0, w=7.0, h=3.6, lift=2.6, tex="scoreboard_led", back="dark_metal")],
    "lights": towers((60, 120, 240, 300), h=30, led=True),
    "trees": [T(kind="palm", t0=70, t1=110, d=17.0, n=9, h=11.0, djit=2.0),
              T(kind="palm", t0=200, t1=230, d=10.0, n=4, h=10.0), T(kind="palm", t0=310, t1=340, d=10.0, n=4, h=10.0)],
}

# ---- t2 grassy banks: low earth bank right round, gum trees on top, cars parked nose-in ----
specs["t2_banks"] = {
    "name": "oval_t2_banks", "seed": 2, "field": FIELD,
    "surround": [{"d0": 3.0, "d1": 4.0, "tex": "turf_dry"}, {"d0": 4.0, "d1": 9.0, "z0": 0.0, "z1": 1.6, "tex": "turf_dry"},
                 {"d0": 9.0, "d1": 40.0, "z0": 1.6, "z1": 1.6, "tex": "turf_dry"}],
    "outer": {"d": 400, "tex": "turf_dry"},
    "fence": {"type": "picket", "d": 3.0, "h": 1.0},
    "posts": POSTS("pad_blue"),
    "buildings": [T(t=90, d=10.0, w=20.0, dpt=10.0, h=3.2, wall="weatherboard_cream", front="weatherboard_window",
                    roof="gable", rise=1.8, roof_tex="iron_red", overhang=0.5, verandah={"d": 2.6, "h": 2.6})],
    "coaches": coaches("iron_cream"), "benches": benches("iron_cream"),
    "scoreboards": [T(t=270, d=10.0, w=8.0, h=3.6, lift=2.4, tex="scoreboard_manual", back="iron_green", box=True)],
    "cars": [T(t0=105, t1=250, d=9.5, gap=2.8, fill=0.75), T(t0=290, t1=435, d=9.5, gap=2.8, fill=0.75)],
    "trees": [T(kind="gum_mix", t0=100, t1=255, d=18.0, n=14, h=16.0), T(kind="gum_mix", t0=285, t1=440, d=18.0, n=14, h=16.0)],
    "lights": towers((30, 150, 210, 330)),
}
for k in ("cars", "trees"):
    for c in specs["t2_banks"][k]:
        c["z"] = 1.6

# ---- t5 modern community hub: glass clubrooms, small seated stand, slim LED poles ----
specs["t5_hub"] = {
    "name": "oval_t5_hub", "seed": 5, "field": FIELD,
    "surround": [{"d0": 3.0, "d1": 10.0, "tex": "concrete"}, {"d0": 10.0, "d1": 40.0, "tex": "turf_dry"}],
    "outer": {"d": 400, "tex": "turf_dry"},
    "fence": {"type": "chainlink", "tex": "chainlink_black", "d": 3.0, "h": 1.1, "post_tex": "dark_metal", "rails": [1.08, 0.05]},
    "posts": POSTS("pad_blue"),
    "buildings": [T(t=90, d=12.0, w=36.0, dpt=14.0, h=4.0, wall="clad_white", front="glass_curtain", roof="flat",
                    roof_tex="iron_zinc", parapet="clad_charcoal",
                    upper={"h": 3.4, "front": "glass_curtain", "wall": "clad_timber", "set": 2.0, "rail": True, "eave": 2.5})],
    "stands": [T(t=90, d=4.0, len=30.0, rows=5, tread=0.8, riser=0.4, base=0.3, seat="seats_blue", riser_tex="concrete",
                 front="concrete", back="clad_charcoal", back_h=0.6, ends="concrete", roof="skillion", roof_front=5.4,
                 roof_over=1.0, roof_tex="clad_white", bay=7.5, post="dark_metal", rail=True)],
    "coaches": coaches("clad_charcoal"), "benches": benches("clad_charcoal"),
    "scoreboards": [T(t=270, d=10.0, w=9.0, h=4.5, lift=2.4, tex="scoreboard_led", back="dark_metal")],
    "lights": towers((20, 70, 110, 160, 200, 250, 290, 340), h=24, d=5.0, led=True),
}
# stadium only (lead ruling 2026-11-18): trees and cars kept under bg_ for the later background pass
for k in ("t2_banks", "t6_north"):
    for g in ("trees", "cars"):
        if g in specs[k]:
            specs[k]["bg_" + g] = specs[k].pop(g)
for k, s in specs.items():
    json.dump(s, open("spec/%s.json" % k, "w"), indent=1)
print("ok", list(specs))
